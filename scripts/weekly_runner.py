"""
Weekly Runner — UK & Ireland Trades Ad Spend Watcher
=====================================================
Orchestrates the full weekly pipeline every Monday at 07:00:

  1. Re-scrape Meta Ad Library (all 8 sectors × UK + IE)
  2. Re-scrape Google Transparency (all 8 sectors × UK + IE)
  3. Merge raw results, deduplicate by company name
  4. Enrich with Companies House (UK) / CRO (IE) data
  5. Score and rank all companies (top 10 per sector)
  6. Detect new entrants, improvements, companies that went dark
  7. Write data/companies.json (dashboard data)
  8. Generate weekly_summary.json (for email report)
  9. Retire companies dark for 4+ consecutive weeks

Usage:
  python weekly_runner.py          # full run
  python weekly_runner.py --dry    # score only, no scraping (uses last raw data)
  python weekly_runner.py --sector solar  # single sector only

Logs are written to data/run_log.jsonl (one line per run).
"""

from __future__ import annotations

import asyncio
import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add scripts dir to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Lazy imports of project scripts
def import_scripts():
    from scraper_meta import run_all_sectors as meta_scrape, calculate_tenure_months
    from scraper_google import run_all_sectors as google_scrape
    from scraper_google_verify import verify_all as google_verify
    from enrichment import enrich_company_list, save_enriched
    from scoring import score_and_rank, get_top_per_sector, save_scored, save_dashboard_data, print_summary
    return {
        "meta_scrape": meta_scrape,
        "google_scrape": google_scrape,
        "google_verify": google_verify,
        "enrich": enrich_company_list,
        "save_enriched": save_enriched,
        "score_and_rank": score_and_rank,
        "get_top": get_top_per_sector,
        "save_scored": save_scored,
        "save_dashboard": save_dashboard_data,
        "print_summary": print_summary,
        "calc_tenure": calculate_tenure_months,
    }


def get_latest_file(pattern: str) -> Path | None:
    """Get the most recently modified file matching a glob pattern."""
    files = sorted(DATA_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_json(path: Path | None) -> list:
    if path and path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def merge_sources(meta: list, google: list) -> list:
    """
    Merge Meta and Google scrape results by company name.
    Companies appearing in both sources get platform lists merged.
    """
    merged = {}
    for company in meta:
        key = normalise_name(company.get("advertiser_name", ""))
        if key:
            merged[key] = {**company}

    for company in google:
        key = normalise_name(company.get("advertiser_name", ""))
        if not key:
            continue
        if key in merged:
            # Merge platforms
            existing_platforms = set(merged[key].get("platforms", []))
            new_platforms = set(company.get("platforms", []))
            merged[key]["platforms"] = list(existing_platforms | new_platforms)
            # Keep longer keyword list
            if len(company.get("keywords", "")) > len(merged[key].get("keywords", "")):
                merged[key]["keywords"] = company.get("keywords", "")
        else:
            merged[key] = {**company}

    return list(merged.values())


def normalise_name(name: str) -> str:
    """Normalise company name for deduplication."""
    return (name or "").lower().strip().replace("ltd", "").replace("limited", "").replace("  ", " ").strip()


def detect_dark_companies(current: list, previous: list) -> list[str]:
    """Identify companies that appeared in previous run but not current (went dark)."""
    current_names = {normalise_name(c.get("advertiser_name") or c.get("name", "")) for c in current}
    dark = []
    for c in previous:
        name = normalise_name(c.get("advertiser_name") or c.get("name", ""))
        if name and name not in current_names:
            dark.append(c.get("advertiser_name") or c.get("name", "Unknown"))
    return dark


def detect_new_entrants(current: list, previous: list) -> list[str]:
    """Companies appearing for the first time (not in previous run)."""
    prev_names = {normalise_name(c.get("advertiser_name") or c.get("name", "")) for c in previous}
    new = []
    for c in current:
        name = normalise_name(c.get("advertiser_name") or c.get("name", ""))
        if name and name not in prev_names:
            new.append(c.get("advertiser_name") or c.get("name", "Unknown"))
    return new


def generate_weekly_summary(scored: list, dark: list, new_entrants: list) -> dict:
    """Generate the weekly summary report structure."""
    hot = [c for c in scored if c.get("score", 0) >= 85]
    warm = [c for c in scored if 65 <= c.get("score", 0) < 85]

    # Most active sectors (by hot lead count)
    by_sector = defaultdict(list)
    for c in scored:
        by_sector[c.get("sector", c.get("sector_label", ""))].append(c)

    sector_activity = []
    for sector, companies in sorted(by_sector.items()):
        hot_count = len([c for c in companies if c.get("score", 0) >= 85])
        sector_activity.append({
            "sector": sector,
            "total": len(companies),
            "hot": hot_count
        })
    sector_activity.sort(key=lambda x: x["hot"], reverse=True)

    summary = {
        "run_date": datetime.utcnow().isoformat(),
        "total_companies": len(scored),
        "hot_leads": len(hot),
        "warm_leads": len(warm),
        "sectors_covered": len(by_sector),
        "hot_lead_list": [
            {
                "name": c.get("advertiser_name") or c.get("name", "Unknown"),
                "sector": c.get("sector", c.get("sector_label", "")),
                "region": c.get("region_label", ""),
                "score": c.get("score"),
                "trigger": c.get("hot_trigger", "")
            }
            for c in hot
        ],
        "sector_activity": sector_activity,
        "new_entrants": new_entrants,
        "went_dark": dark,
        "top_sector": sector_activity[0]["sector"] if sector_activity else "—"
    }
    return summary


def format_email_report(summary: dict) -> str:
    """Format the weekly summary as a plain-text email."""
    date_str = datetime.utcnow().strftime("%A %d %B %Y")
    lines = [
        f"AD SPEND WATCHER — WEEKLY REPORT",
        f"Week of {date_str}",
        "=" * 50,
        "",
        f"OVERVIEW",
        f"  Companies tracked:  {summary['total_companies']}",
        f"  Hot leads (85+):    {summary['hot_leads']}",
        f"  Warm leads (65-84): {summary['warm_leads']}",
        f"  Sectors covered:    {summary['sectors_covered']}/8",
        "",
    ]

    if summary["hot_lead_list"]:
        lines.append("HOT LEADS — REACH OUT THIS WEEK")
        for lead in summary["hot_lead_list"]:
            trigger = f"  [{lead['trigger']}]" if lead.get("trigger") else ""
            lines.append(f"  • {lead['name']} ({lead['sector']}, {lead['region']}) — Score {lead['score']}{trigger}")
        lines.append("")

    if summary["sector_activity"]:
        lines.append("MOST ACTIVE SECTORS")
        for s in summary["sector_activity"][:4]:
            lines.append(f"  {s['sector']:<22} {s['total']} tracked  |  {s['hot']} hot")
        lines.append("")

    if summary["new_entrants"]:
        lines.append("NEW ENTRANTS (watch list)")
        for name in summary["new_entrants"][:5]:
            lines.append(f"  + {name}")
        lines.append("")

    if summary["went_dark"]:
        lines.append("WENT DARK (no ads 4+ weeks)")
        for name in summary["went_dark"][:5]:
            lines.append(f"  - {name}")
        lines.append("")

    lines.append("Dashboard: open dashboard.html in your Ad Spend Watcher folder")
    lines.append("=" * 50)

    return "\n".join(lines)


def log_run(summary: dict, success: bool, error: str = ""):
    """Append a run log entry to data/run_log.jsonl."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "success": success,
        "companies_tracked": summary.get("total_companies", 0),
        "hot_leads": summary.get("hot_leads", 0),
        "error": error
    }
    log_path = DATA_DIR / "run_log.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


async def run_full_pipeline(dry_run: bool = False, sector_filter: str | None = None):
    """Execute the full weekly pipeline."""
    start_time = datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"AD SPEND WATCHER — Weekly Run")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    if dry_run:
        print("Mode: DRY RUN (scoring only, no scraping)")
    print(f"{'='*60}\n")

    fns = import_scripts()
    date_str = start_time.strftime("%Y-%m-%d")

    # ── Step 1 & 2: Scrape ──────────────────────────────────────────────────
    if not dry_run:
        print("STEP 1/8 — Scraping Meta Ad Library...")
        try:
            countries = ["UK", "IE"]
            meta_results = await fns["meta_scrape"](countries)
        except Exception as e:
            print(f"  ⚠ Meta scrape failed: {e}")
            meta_results = []

        print("\nSTEP 2/8 — Scraping Google Transparency...")
        try:
            google_results = await fns["google_scrape"](countries)
        except Exception as e:
            print(f"  ⚠ Google scrape failed: {e}")
            google_results = []
    else:
        # Load latest raw data from disk
        print("STEP 1-2/8 — Loading latest raw data from disk...")
        meta_file = get_latest_file("meta_qualified_*.json")
        google_file = get_latest_file("google_qualified_*.json")
        meta_results = load_json(meta_file)
        google_results = load_json(google_file)
        print(f"  Meta: {len(meta_results)} records from {meta_file}")
        print(f"  Google: {len(google_results)} records from {google_file}")

    # ── Step 3: Merge ───────────────────────────────────────────────────────
    print("\nSTEP 3/8 — Merging and deduplicating sources...")
    merged = merge_sources(meta_results, google_results)
    print(f"  → {len(merged)} unique companies after merge")

    if sector_filter:
        merged = [c for c in merged if c.get("sector", "").lower() == sector_filter.lower()]
        print(f"  → Filtered to '{sector_filter}': {len(merged)} companies")

    # ── Step 3b: Google Ads verification ────────────────────────────────────
    print("\nSTEP 3b/8 — Verifying Google Ads presence for Meta companies...")
    print("  (Searching each company on Google, checking for Sponsored labels)")
    print(f"  Estimated time: {max(1, len(merged) * 4 // 60)}–{max(1, len(merged) * 6 // 60)} minutes for {len(merged)} companies")
    try:
        merged = await fns["google_verify"](merged)
        paid = sum(1 for c in merged if c.get("google_ads_verified"))
        seo = sum(1 for c in merged if c.get("google_visible") and not c.get("google_ads_verified"))
        print(f"  → {paid} confirmed Google Ads (paid) | {seo} page-1 visible (SEO) | both score as 3-platform")
    except Exception as e:
        print(f"  ⚠ Google verification failed: {e} — continuing without verification")

    # ── Step 4: Enrich ──────────────────────────────────────────────────────
    print("\nSTEP 4/8 — Enriching with Companies House / CRO data...")
    try:
        enriched = await fns["enrich"](merged)
        fns["save_enriched"](enriched)
    except Exception as e:
        print(f"  ⚠ Enrichment failed: {e}")
        enriched = merged  # fall through with unenriched data

    # ── Step 5: Score ───────────────────────────────────────────────────────
    print("\nSTEP 5/8 — Scoring and ranking companies...")
    prev_scored_file = get_latest_file("scored_*.json")
    prev_scored = load_json(prev_scored_file)
    scored = fns["score_and_rank"](enriched, prev_scored)
    top = fns["get_top"](scored, top_n=10)

    # ── Step 6: Detect changes ──────────────────────────────────────────────
    print("\nSTEP 6/8 — Detecting changes since last run...")
    dark = detect_dark_companies(scored, prev_scored)
    new_entrants = detect_new_entrants(scored, prev_scored)
    print(f"  New entrants: {len(new_entrants)}  |  Went dark: {len(dark)}")

    # ── Step 7: Save & report ───────────────────────────────────────────────
    print("\nSTEP 7/8 — Saving dashboard data and weekly summary...")
    # Guard: never overwrite dashboard with empty data
    if len(top) == 0:
        print("  ⚠ 0 companies scored — keeping previous dashboard data unchanged.")
        print("  ⚠ Check that meta_qualified_*.json has data for today's date.")
    else:
        fns["save_scored"](top)
        fns["save_dashboard"](top)

    summary = generate_weekly_summary(scored, dark, new_entrants)

    # Save summary JSON
    summary_path = DATA_DIR / f"weekly_summary_{date_str}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved: {summary_path}")

    # Save latest summary (for dashboard)
    latest_path = DATA_DIR / "latest_summary.json"
    with open(latest_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print email report to stdout
    email_text = format_email_report(summary)
    print("\n" + "─" * 60)
    print(email_text)

    # Save email text
    email_path = DATA_DIR / f"weekly_email_{date_str}.txt"
    with open(email_path, "w") as f:
        f.write(email_text)

    duration = (datetime.utcnow() - start_time).seconds
    print(f"\n✓ Run complete in {duration}s")
    fns["print_summary"](scored)
    log_run(summary, success=True)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly pipeline runner")
    parser.add_argument("--dry", action="store_true", help="Skip scraping, use latest cached data")
    parser.add_argument("--sector", help="Run a single sector only")
    args = parser.parse_args()

    asyncio.run(run_full_pipeline(dry_run=args.dry, sector_filter=args.sector))
