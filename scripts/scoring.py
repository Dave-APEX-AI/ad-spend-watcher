"""
Signal Scoring Engine — UK & Ireland Trades Ad Spend Watcher
============================================================
Applies the 0–100 signal scoring model to enriched company records,
calculates outreach windows (Hot/Warm/Watch), identifies outreach triggers,
and ranks companies per sector.

Scoring model:
  Spend duration    30 pts  (3m=15, 4m=20, 5m=25, 6+m=30)
  Platform diversity 25 pts  (1=8, 2=16, 3+=25)
  Spend momentum    25 pts  (flat=5, rising=12, ramping=25)
  Company size      10 pts  (10-20=5, 20-50=8, 50+=10)
  Creative quality  10 pts  (generic=3, specific/video=7, professional+AB=10)

Thresholds:
  85-100 = Hot   → reach out this week
  65-84  = Warm  → reach out within the month
  <65    = Watch → monitor, reassess in 4 weeks

Usage:
  python scoring.py --input data/enriched_2024-11-04.json
  python scoring.py --input data/enriched_2024-11-04.json --prev data/enriched_2024-10-28.json

Output:
  data/scored_{date}.json   — all companies with scores
  data/companies.json       — dashboard-ready format (top 10 per sector)
"""

from __future__ import annotations
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Sector display names and avatar colours
SECTOR_CONFIG = {
    "plumbing":      {"label": "Plumbing",        "avatarBg": "#EEEDFE", "avatarCol": "#3C3489"},
    "solar":         {"label": "Solar",            "avatarBg": "#E1F5EE", "avatarCol": "#085041"},
    "electrical":    {"label": "Electrical",       "avatarBg": "#E6F1FB", "avatarCol": "#0C447C"},
    "alarms":        {"label": "Alarms",           "avatarBg": "#FAEEDA", "avatarCol": "#633806"},
    "insulation":    {"label": "Insulation",       "avatarBg": "#F1EFE8", "avatarCol": "#444441"},
    "windows_doors": {"label": "Windows & Doors",  "avatarBg": "#FDE8EC", "avatarCol": "#7C0C2A"},
    "drainage":      {"label": "Drainage",         "avatarBg": "#E8F4FD", "avatarCol": "#0A5C84"},
    "pumps":         {"label": "Pumps",            "avatarBg": "#F0E8FD", "avatarCol": "#4A0A84"},
}

REGION_MAP = {
    "london": ["london", "greater london", "sw", "se", "n", "e", "w", "ec", "wc"],
    "midlands": ["midlands", "birmingham", "coventry", "leicester", "nottingham", "derby"],
    "northwest": ["manchester", "liverpool", "cheshire", "lancashire", "merseyside", "salford"],
    "scotland": ["scotland", "edinburgh", "glasgow", "aberdeen", "dundee"],
    "southeast": ["kent", "essex", "surrey", "sussex", "hampshire", "berkshire", "oxfordshire"],
    "ireland": ["ireland", "dublin", "cork", "limerick", "galway", "waterford", ".ie"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def score_spend_duration(tenure_months: int) -> int:
    """30 points max for spend duration."""
    if tenure_months >= 6:
        return 30
    elif tenure_months == 5:
        return 25
    elif tenure_months == 4:
        return 20
    elif tenure_months == 3:
        return 15
    else:
        return 0  # Doesn't qualify at all


def score_platform_diversity(platforms: list[str], google_rank_band: str | None = None) -> int:
    """
    25 points max for multi-platform presence.

    Platform detection uses Google page 1 ranking (not sponsored-label detection,
    which requires JS rendering). Any page 1 presence counts as a confirmed second
    platform. A top-3 rank earns a small bonus (+3 pts) — it signals either paid
    ads or dominant organic investment, both strong buying-intent indicators.
    """
    # Normalise: treat google_seo as google for counting purposes
    normalised = set()
    for p in platforms:
        pl = p.lower()
        if pl in ("google", "google_seo"):
            normalised.add("google")
        else:
            normalised.add(pl)

    unique = len(normalised)
    if unique >= 3:
        base = 25
    elif unique == 2:
        base = 16
    elif unique == 1:
        base = 8
    else:
        base = 0

    # Top-3 Google rank bonus: stronger signal of paid/dominant presence
    rank_bonus = 3 if (google_rank_band == "top3" and unique >= 2) else 0

    return min(25, base + rank_bonus)


def score_spend_momentum(spend_history: list[float]) -> tuple[int, str]:
    """
    25 points max for spend momentum.
    Returns (score, momentum_label).

    Momentum is calculated from the spend trend:
      - Flat/declining:    last 3 values have ≤5% growth  → 5 pts
      - Slowly rising:     consistent upward trend        → 12 pts
      - Ramping hard:      3+ consecutive weeks of growth → 25 pts
    """
    if not spend_history or len(spend_history) < 2:
        # No spend history available (browser-scraped data).
        # A business actively running Meta ads for 3+ months is not flat —
        # award steady-growth score rather than the floor penalty.
        return 12, "steady"

    recent = spend_history[-4:] if len(spend_history) >= 4 else spend_history

    # Check for 3 consecutive weeks of growth
    consecutive_growth = 0
    for i in range(1, len(recent)):
        if recent[i] > recent[i - 1]:
            consecutive_growth += 1
        else:
            consecutive_growth = 0

    # Overall trend
    start_val = recent[0]
    end_val = recent[-1]
    overall_pct = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0

    if consecutive_growth >= 3:
        return 25, "ramping hard"
    elif overall_pct > 20:
        return 12, "rising slowly"
    elif overall_pct >= 0:
        return 5, "flat"
    else:
        return 5, "flat"  # Declining still gets floor score


def score_company_size(staff_str: str) -> int:
    """10 points max for company size."""
    if not staff_str:
        # No Companies House data yet. UK/IE trade businesses running
        # sustained ad campaigns typically have 10–50 staff.
        return 7  # conservative mid-band default

    try:
        staff = int(str(staff_str).replace("+", "").split("-")[0].strip())
    except (ValueError, AttributeError):
        return 5

    if staff >= 50:
        return 10
    elif staff >= 20:
        return 8
    elif staff >= 10:
        return 5
    else:
        return 0  # too small


def score_creative_sophistication(ad_copies: list[str], ad_count: int) -> int:
    """
    10 points max for creative quality.
    Infers sophistication from ad copy text and volume.
    """
    if not ad_copies:
        # No ad copy available from browser scraping.
        # A company running multi-month Meta campaigns has at minimum
        # put effort into their creative — don't penalise for unknown data.
        return 5  # conservative baseline (not floor)

    combined = " ".join(ad_copies).lower()

    # Professional production signals
    pro_signals = ["a/b test", "testimonial", "case study", "accredited",
                   "award", "guaranteed", "video", "before and after",
                   "rated", "reviews", "google guaranteed"]

    # Specific offer signals (better than generic)
    specific_signals = ["% off", "£", "free quote", "same day", "24 hour",
                        "next day", "from £", "grant", "0% finance",
                        "trusted", "approved installer"]

    pro_count = sum(1 for s in pro_signals if s in combined)
    specific_count = sum(1 for s in specific_signals if s in combined)

    # Multiple active ads = A/B testing signal
    if ad_count >= 5 and (pro_count >= 1 or specific_count >= 2):
        return 10
    elif specific_count >= 2 or pro_count >= 1:
        return 7
    else:
        return 3


def _tenure_from_start_date(ad_start_date: str) -> int:
    """Calculate tenure months from an ISO date string."""
    if not ad_start_date:
        return 0
    try:
        start_str = str(ad_start_date)[:10]  # take YYYY-MM-DD
        start = datetime.strptime(start_str, "%Y-%m-%d")
        delta = datetime.utcnow() - start
        return max(0, int(delta.days / 30.44))
    except Exception:
        return 0


def calculate_signal_score(company: dict) -> tuple[int, str, str]:
    """
    Calculate the 0–100 signal score for a company.
    Returns (score, label, momentum_label).
    """
    # Calculate tenure from ad_start_date if tenure_months not explicitly set
    tenure_months = company.get("tenure_months") or _tenure_from_start_date(
        company.get("ad_start_date") or company.get("ad_delivery_start_time", "")
    )
    platforms = company.get("platforms", [])
    spend_history = company.get("spend_history", company.get("spend", []))
    ad_copies = company.get("ad_copy_samples", [])
    ad_count = company.get("ad_count", 1)
    staff_str = str(company.get("staff", company.get("employee_count", "15")))

    google_rank_band = company.get("google_rank_band")

    s_duration = score_spend_duration(tenure_months)
    s_platform = score_platform_diversity(platforms, google_rank_band)
    s_momentum, momentum_label = score_spend_momentum(spend_history)
    s_size = score_company_size(staff_str)
    s_creative = score_creative_sophistication(ad_copies, ad_count)

    total = s_duration + s_platform + s_momentum + s_size + s_creative
    total = min(100, total)

    # Thresholds calibrated for browser-scraped data (no enrichment):
    #   6mo + Facebook + Google page1 = ~70 → Hot
    #   6mo + Facebook only           = ~62 → Warm
    #   3-5mo + Facebook only         = ~47 → Watch
    label = "Hot" if total >= 70 else "Warm" if total >= 55 else "Watch"

    return total, label, momentum_label


# ═══════════════════════════════════════════════════════════════════════════════
# OUTREACH TRIGGER DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def detect_hot_trigger(company: dict, prev_company: dict | None = None) -> str | None:
    """
    Detect if a company qualifies for immediate Hot trigger.
    Returns trigger description string or None.
    """
    spend = company.get("spend_history", company.get("spend", []))
    tenure = company.get("tenure_months", 0)

    # 1. 3+ consecutive weeks of spend increase
    if spend and len(spend) >= 4:
        recent = spend[-4:]
        if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
            return "Ramping 4 weeks straight"
        elif all(recent[i] > recent[i-1] for i in range(1, 3)):
            return "Ramping 3 weeks straight"

    # 2. New platform in last 30 days
    if company.get("new_platform_added"):
        platform = company.get("new_platform_added", "platform")
        return f"Expanded to {platform.title()} this month"

    # 3. Score jumped 10+ points since last week
    if prev_company:
        prev_score = prev_company.get("score", 0)
        curr_score = company.get("score", 0)
        if curr_score - prev_score >= 10:
            return f"Score up {curr_score - prev_score}pts this week"

    # 4. Just crossed 3-month threshold for first time
    if tenure == 3 and prev_company and prev_company.get("tenure_months", 0) < 3:
        return "Just crossed 3-month threshold"

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# REGION NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def normalise_region(region_text: str, country: str) -> tuple[str, str]:
    """
    Map a freeform region string to a dashboard region key.
    Returns (region_key, region_label).
    """
    text = (region_text or "").lower()

    if country == "IE" or "ireland" in text or ".ie" in text:
        return "ireland", "Dublin & Ireland"

    for key, signals in REGION_MAP.items():
        if any(s in text for s in signals):
            labels = {
                "london": "London",
                "midlands": "Midlands",
                "northwest": "North West",
                "scotland": "Scotland",
                "southeast": "South East",
                "ireland": "Ireland"
            }
            return key, labels.get(key, region_text)

    # Default: use the raw text
    return "other", region_text.title() if region_text else "UK"


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE SPEND SPARKLINE DATA
# ═══════════════════════════════════════════════════════════════════════════════

def generate_spend_history(tenure_months: int, momentum: str) -> list[int]:
    """
    Generate a synthetic 7-point spend trend for the sparkline.
    Used when real week-by-week data isn't available.
    """
    import random
    base = random.randint(2, 5)
    points = [base]

    if momentum == "ramping hard":
        for _ in range(6):
            points.append(round(points[-1] * random.uniform(1.08, 1.25)))
    elif momentum == "rising slowly":
        for _ in range(6):
            points.append(round(points[-1] * random.uniform(1.02, 1.10)))
    else:  # flat
        for _ in range(6):
            points.append(round(points[-1] * random.uniform(0.95, 1.05)))

    return points


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD FORMAT CONVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def to_dashboard_format(company: dict, company_id: int) -> dict:
    """Convert an enriched+scored company record to the dashboard JS format."""
    sector_raw = company.get("sector", "").lower().replace(" ", "_")
    sector_cfg = SECTOR_CONFIG.get(sector_raw, SECTOR_CONFIG["plumbing"])

    region_raw = company.get("region_label") or company.get("region", "")
    country = company.get("country", "UK")
    region_key, region_label = normalise_region(region_raw, country)

    score = company.get("score", 0)
    momentum = company.get("momentum", "flat")
    spend_history = company.get("spend_history", company.get("spend", []))

    if not spend_history:
        effective_tenure = company.get("tenure_months") or _tenure_from_start_date(
            company.get("ad_start_date") or company.get("ad_delivery_start_time", "")
        )
        spend_history = generate_spend_history(effective_tenure or 3, momentum)

    # Contact / director
    director = company.get("director") or {}
    contact_name = director.get("name", "Unknown")
    contact_role = director.get("role", "Director")
    contact_email = None

    email_candidates = company.get("email_candidates", [])
    if email_candidates:
        contact_email = email_candidates[0]["email"]  # first (most likely) candidate
    elif director.get("email"):
        contact_email = director["email"]

    li_url = director.get("linkedin_url") or company.get("linkedin_search_url", "")

    # Company name initials for avatar
    words = company.get("advertiser_name", company.get("company_name", "??")).split()
    initials = "".join(w[0].upper() for w in words[:2])

    return {
        "id": company_id,
        "name": company.get("advertiser_name") or company.get("company_name", "Unknown"),
        "sector": sector_cfg["label"],
        "country": country,
        "region": region_key,
        "region_label": region_label,
        "staff": str(company.get("staff", company.get("employee_count", "15"))),
        "tenure_months": company.get("tenure_months") or _tenure_from_start_date(
            company.get("ad_start_date") or company.get("ad_delivery_start_time", "")
        ),
        "tenure_label": f"{company.get('tenure_months') or _tenure_from_start_date(company.get('ad_start_date') or company.get('ad_delivery_start_time', ''))} months",
        "score": score,
        "hot_trigger": company.get("hot_trigger"),
        "platforms": company.get("platforms", ["google"]),
        "audience": company.get("audience", "Homeowners"),
        "keywords": company.get("keywords", ""),
        "spend": spend_history,
        "contact": {
            "name": contact_name,
            "role": contact_role,
            "email": contact_email,
            "li": li_url
        },
        "avatar": initials,
        "avatarBg": sector_cfg["avatarBg"],
        "avatarCol": sector_cfg["avatarCol"]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCORING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def score_and_rank(companies: list[dict], prev_companies: list[dict] | None = None) -> list[dict]:
    """
    Score all companies, detect triggers, rank per sector.
    Returns full list sorted by score descending.
    """
    # Build prev lookup by name
    prev_lookup = {}
    if prev_companies:
        for c in prev_companies:
            key = (c.get("advertiser_name") or c.get("company_name", "")).lower()
            prev_lookup[key] = c

    scored = []
    for company in companies:
        name_key = (company.get("advertiser_name") or company.get("company_name", "")).lower()
        prev = prev_lookup.get(name_key)

        score, label, momentum = calculate_signal_score(company)
        company["score"] = score
        company["score_label"] = label
        company["momentum"] = momentum

        # Detect outreach trigger
        trigger = detect_hot_trigger(company, prev)
        if score >= 85 and not trigger:
            trigger = "High signal score"
        company["hot_trigger"] = trigger

        scored.append(company)

    # Sort by score descending
    scored.sort(key=lambda c: c.get("score", 0), reverse=True)
    return scored


def get_top_per_sector(scored: list[dict], top_n: int = 10) -> list[dict]:
    """Get top N companies per sector (7-8 UK, 2-3 IE where possible)."""
    by_sector = defaultdict(list)
    for c in scored:
        by_sector[c.get("sector", "").lower()].append(c)

    result = []
    for sector, companies in by_sector.items():
        # Split UK and IE
        uk = [c for c in companies if c.get("country") == "UK"]
        ie = [c for c in companies if c.get("country") == "IE"]

        # Target: 7-8 UK + 2-3 IE = 10
        uk_count = min(8, max(7, top_n - min(3, len(ie))))
        ie_count = min(3, len(ie), top_n - uk_count)

        selected = uk[:uk_count] + ie[:ie_count]
        selected.sort(key=lambda c: c.get("score", 0), reverse=True)
        result.extend(selected[:top_n])

    return result


def save_scored(records: list[dict]) -> Path:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = DATA_DIR / f"scored_{date_str}.json"
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"✓ Saved {len(records)} scored records to {path}")
    return path


def save_dashboard_data(records: list[dict]) -> Path:
    """Convert to dashboard format and save as companies.json."""
    dashboard_records = []
    for i, company in enumerate(records, start=1):
        dashboard_records.append(to_dashboard_format(company, i))

    path = DATA_DIR / "companies.json"
    with open(path, "w") as f:
        json.dump(dashboard_records, f, indent=2)
    print(f"✓ Dashboard data saved: {len(dashboard_records)} companies → {path}")
    return path


def print_summary(scored: list[dict]):
    """Print weekly summary to stdout."""
    hot = [c for c in scored if c.get("score", 0) >= 85]
    warm = [c for c in scored if 65 <= c.get("score", 0) < 85]
    sectors_covered = len(set(c.get("sector", "") for c in scored))

    print("\n" + "═" * 60)
    print("WEEKLY SUMMARY — UK & Ireland Trades Ad Spend Watcher")
    print("═" * 60)
    print(f"  Companies tracked:  {len(scored)}")
    print(f"  Hot leads (85+):    {len(hot)}")
    print(f"  Warm leads (65–84): {len(warm)}")
    print(f"  Sectors covered:    {sectors_covered}/8")
    print()

    if hot:
        print("  HOT LEADS THIS WEEK:")
        for c in hot:
            name = c.get("advertiser_name") or c.get("company_name", "Unknown")
            trigger = c.get("hot_trigger", "")
            print(f"    • {name} [{c.get('sector','')}] — Score {c.get('score')} — {trigger}")

    print()
    by_sector = defaultdict(list)
    for c in scored:
        by_sector[c.get("sector", "")].append(c)
    print("  SECTOR ACTIVITY:")
    for sector, companies in sorted(by_sector.items()):
        hot_count = len([c for c in companies if c.get("score", 0) >= 85])
        print(f"    {sector:<20} {len(companies)} tracked  |  {hot_count} hot")
    print("═" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal scoring engine")
    parser.add_argument("--input", required=True, help="Enriched companies JSON")
    parser.add_argument("--prev", help="Previous week's scored JSON for delta scoring")
    args = parser.parse_args()

    with open(args.input) as f:
        companies = json.load(f)

    prev_companies = None
    if args.prev:
        with open(args.prev) as f:
            prev_companies = json.load(f)

    print(f"Scoring {len(companies)} companies...")
    scored = score_and_rank(companies, prev_companies)
    top_per_sector = get_top_per_sector(scored)

    save_scored(top_per_sector)
    save_dashboard_data(top_per_sector)
    print_summary(scored)
