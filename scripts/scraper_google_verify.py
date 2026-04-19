"""
Google Page Ranking Verification — UK & Ireland Trades Ad Spend Watcher
=======================================================================
Takes companies already discovered on Meta Ad Library and checks whether
each one appears on page 1 of Google search results for their sector keyword.

WHY PAGE RANKING INSTEAD OF SPONSORED DETECTION:
  Google renders "Sponsored" labels via JavaScript, so they are invisible
  to plain HTTP requests. Instead we check whether the company name appears
  anywhere on page 1 (positions 1–10). Page 1 presence — whether from paid
  ads or strong organic SEO — is a reliable indicator of serious digital
  marketing investment. Ranking in positions 1–3 is treated as a stronger
  signal than positions 4–10.

Why this matters for scoring:
  A company that appears on page 1 of Google AND runs Meta ads has confirmed
  multi-platform spend. Platform diversity is worth 25 pts in the scoring
  model (vs 8 for single-platform), pushing 6+ month advertisers into
  Warm/Hot territory.

Output fields added to each company record:
  "google_page1":        true/false  — appeared on page 1
  "google_page1_rank":   1–10 or None — estimated rank position
  "google_rank_band":    "top3" / "mid" / "lower" / "not_found"
  "platforms":           [..., "google"]  — appended if page 1 found

Usage:
  python scraper_google_verify.py --input data/meta_qualified_2026-04-01.json
  python scraper_google_verify.py --input data/meta_qualified_2026-04-01.json --output data/verified.json
"""

from __future__ import annotations
import asyncio
import json
import random
import argparse
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Realistic browser headers — rotated to reduce blocking
HEADER_SETS = [
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    },
]

# Sector-specific search terms to pair with company name
SECTOR_SEARCH_TERMS = {
    "solar":         "solar panels",
    "plumbing":      "plumber",
    "electrical":    "electrician",
    "alarms":        "alarm installation",
    "insulation":    "insulation",
    "windows_doors": "windows doors",
    "drainage":      "drainage",
    "pumps":         "pump installation",
}


def build_search_url(company_name: str, sector: str, country: str) -> str:
    """Build a Google search URL for the company + sector term."""
    sector_term = SECTOR_SEARCH_TERMS.get(sector.lower(), "")
    gl = "ie" if country == "IE" else "gb"
    query = f"{company_name} {sector_term}".strip()
    return f"https://www.google.com/search?q={quote_plus(query)}&gl={gl}&hl=en&num=10"


def get_core_name_words(company_name: str) -> list[str]:
    """
    Strip legal suffixes and return meaningful words for matching.
    e.g. "Octopus Energy Ltd" -> ["Octopus", "Energy"]
    """
    suffixes = r'\b(ltd|limited|llc|inc|plc|group|uk|ireland|ie|co|solar|energy|services|solutions)\b'
    clean = re.sub(suffixes, '', company_name, flags=re.IGNORECASE)
    return [w for w in clean.split() if len(w) >= 3]


def estimate_page1_rank(html: str, company_name: str) -> int | None:
    """
    Estimate where in the Google page 1 results the company appears.
    Returns an integer 1–10 (approximate position) or None if not found.

    Method:
    - Split HTML into result-block chunks using <h3> tags as result boundaries
      (each organic result in Google's HTML has an <h3> headline)
    - Find which chunk first contains the company name
    - Return that chunk index as the approximate rank
    """
    words = get_core_name_words(company_name)
    if not words:
        return None

    primary = words[0].lower()

    if primary not in html.lower():
        return None  # Not on page at all

    # Split by <h3> result headlines — each organic result has one
    blocks = re.split(r'<h3[\s>]', html, flags=re.IGNORECASE)

    if len(blocks) <= 1:
        # Fallback: split by result link anchors
        blocks = re.split(r'<a\s+href="https?://', html, flags=re.IGNORECASE)

    for i, block in enumerate(blocks[1:], start=1):  # skip preamble before first result
        if primary in block.lower():
            return min(i, 10)  # cap at 10

    # Name appeared in HTML but not in a result block — treat as lower page 1
    return 8


def rank_band(rank: int | None) -> str:
    """Convert rank position to a human-readable band."""
    if rank is None:
        return "not_found"
    elif rank <= 3:
        return "top3"
    elif rank <= 6:
        return "mid"
    else:
        return "lower"


async def verify_single(
    session: "aiohttp.ClientSession",
    company: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Check one company for Google page 1 presence and estimate rank."""
    async with semaphore:
        name = company.get("advertiser_name", "")
        sector = company.get("sector", "solar")
        country = company.get("country", "UK")
        search_url = build_search_url(name, sector, country)

        headers = random.choice(HEADER_SETS)
        page1_rank: int | None = None

        try:
            async with session.get(
                search_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    page1_rank = estimate_page1_rank(html, name)
                elif resp.status == 429:
                    print(f"    ⚠ Rate limited on '{name}' — skipping")
                else:
                    print(f"    ⚠ HTTP {resp.status} for '{name}'")

        except asyncio.TimeoutError:
            print(f"    Timeout: '{name}'")
        except Exception as e:
            print(f"    Error on '{name}': {e}")

        on_page1 = page1_rank is not None
        band = rank_band(page1_rank)

        company["google_page1"] = on_page1
        company["google_page1_rank"] = page1_rank
        company["google_rank_band"] = band
        company["google_search_url"] = search_url

        # Backward-compat fields used by scoring
        company["google_ads_verified"] = False   # can't detect paid ads via HTTP
        company["google_visible"] = on_page1     # page 1 presence is the signal

        platforms = list(company.get("platforms", []))
        if on_page1 and "google" not in platforms:
            platforms.append("google")
        company["platforms"] = platforms

        if band == "top3":
            status = f"★ Page 1 rank ~{page1_rank} (top 3)"
        elif band == "mid":
            status = f"◆ Page 1 rank ~{page1_rank} (mid)"
        elif band == "lower":
            status = f"· Page 1 rank ~{page1_rank} (lower)"
        else:
            status = "✗ Not found on page 1"

        print(f"  [{status}] {name} ({country})")

        # Polite delay: 3–6 seconds between requests
        await asyncio.sleep(random.uniform(3, 6))

        return company


async def verify_all(companies: list[dict], max_concurrent: int = 1) -> list[dict]:
    """
    Check Google page 1 ranking for all companies.
    max_concurrent=1 keeps requests well within Google's tolerance.
    """
    if not AIOHTTP_AVAILABLE:
        print("  ⚠ aiohttp not installed — Google page ranking check skipped.")
        print("    Run: pip3 install aiohttp")
        return companies

    semaphore = asyncio.Semaphore(max_concurrent)

    async with aiohttp.ClientSession() as session:
        tasks = [verify_single(session, company, semaphore) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    top3    = sum(1 for c in results if c.get("google_rank_band") == "top3")
    mid     = sum(1 for c in results if c.get("google_rank_band") == "mid")
    lower   = sum(1 for c in results if c.get("google_rank_band") == "lower")
    missing = sum(1 for c in results if not c.get("google_page1"))

    print(f"\n✓ Google page ranking complete:")
    print(f"    Top 3  : {top3} companies")
    print(f"    Mid    : {mid} companies")
    print(f"    Lower  : {lower} companies")
    print(f"    Not found: {missing} companies")

    return list(results)


def load_companies(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def save_companies(companies: list[dict], path: str):
    with open(path, "w") as f:
        json.dump(companies, f, indent=2)
    print(f"✓ Saved {len(companies)} verified records to {path}")


async def run_verification(input_path: str, output_path: str | None = None):
    """Full verification run."""
    companies = load_companies(input_path)
    print(f"\nLoaded {len(companies)} companies from {input_path}")
    print(f"Checking each for Google page 1 presence (3–6s delay between searches)...\n")

    verified = await verify_all(companies)

    top3_list  = [c for c in verified if c.get("google_rank_band") == "top3"]
    mid_list   = [c for c in verified if c.get("google_rank_band") == "mid"]
    lower_list = [c for c in verified if c.get("google_rank_band") == "lower"]
    not_found  = [c for c in verified if not c.get("google_page1")]

    print(f"\n{'='*60}")
    print(f"PAGE 1 RANK RESULTS")
    print(f"\nTOP 3 ({len(top3_list)} companies):")
    for c in top3_list:
        print(f"  ★ {c['advertiser_name']} ({c.get('country','?')}) — rank ~{c.get('google_page1_rank')}")
    print(f"\nMID 4–6 ({len(mid_list)} companies):")
    for c in mid_list:
        print(f"  ◆ {c['advertiser_name']} ({c.get('country','?')}) — rank ~{c.get('google_page1_rank')}")
    print(f"\nLOWER 7–10 ({len(lower_list)} companies):")
    for c in lower_list:
        print(f"  · {c['advertiser_name']} ({c.get('country','?')}) — rank ~{c.get('google_page1_rank')}")
    print(f"\nNOT FOUND ({len(not_found)} companies):")
    for c in not_found:
        print(f"  ✗ {c['advertiser_name']} ({c.get('country','?')})")
    print(f"{'='*60}")

    out = output_path or input_path
    save_companies(verified, out)
    return verified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google page ranking check for Meta-discovered companies")
    parser.add_argument("--input", required=True, help="Path to meta_qualified_*.json")
    parser.add_argument("--output", help="Output path (defaults to overwriting input)")
    args = parser.parse_args()

    asyncio.run(run_verification(args.input, args.output))
