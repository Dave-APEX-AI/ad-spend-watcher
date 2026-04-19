"""
Google Ads Transparency Centre Scraper — UK & Ireland Trades
=============================================================
Uses aiohttp to query Google's Transparency Centre — no browser required.

Google Transparency is a JavaScript SPA with no official public API.
This scraper hits the internal search endpoint the SPA uses and parses
the JSON response. If Google changes their internal API format, the
scraper fails gracefully with 0 results (Meta data still flows through).

No credentials needed — this endpoint is publicly accessible.
"""

from __future__ import annotations
import asyncio
import json
import random
import re
import argparse
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
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR.mkdir(exist_ok=True)

COUNTRY_REGION_MAP = {
    "UK": "GB",
    "IE": "IE",
}

SECTOR_KEYWORDS = {
    "plumbing":      ["emergency plumber", "boiler installation", "drain unblocking"],
    "solar":         ["solar panel installation", "solar panels", "EV charger"],
    "electrical":    ["electrician EICR", "house rewire", "smart home electrician"],
    "alarms":        ["intruder alarm", "CCTV installation", "home security system"],
    "insulation":    ["cavity wall insulation", "loft insulation", "insulation grant"],
    "windows_doors": ["double glazing", "composite doors", "bifold doors"],
    "drainage":      ["CCTV drain survey", "drain jetting", "septic tank"],
    "pumps":         ["borehole pump", "sewage pump installation", "flood pump"],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://adstransparency.google.com/",
}


async def scrape_google_transparency(sector: str, country: str, max_results: int = 30) -> list[dict]:
    """
    Attempt to scrape Google Ads Transparency Centre for a sector/country.
    Returns list of advertiser dicts, or empty list if unreachable.
    """
    if not AIOHTTP_AVAILABLE:
        print(f"  [Google] aiohttp not available — skipping")
        return []

    region_code = COUNTRY_REGION_MAP.get(country, "GB")
    keywords = SECTOR_KEYWORDS.get(sector, [])
    results = []
    seen: set = set()

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for keyword in keywords[:2]:
            print(f"  Searching Google Transparency: '{keyword}' | {country}")
            entries = await _fetch_google_keyword(session, keyword, region_code)

            for entry in entries:
                name = entry.get("advertiser_name", "")
                if name and name not in seen:
                    seen.add(name)
                    entry.update({
                        "keyword_found_under": keyword,
                        "sector": sector,
                        "country": country,
                        "source": "google_transparency",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                    results.append(entry)
                    if len(results) >= max_results:
                        break

            await asyncio.sleep(random.uniform(3, 6))

    return results


async def _fetch_google_keyword(session, keyword: str, region_code: str) -> list[dict]:
    """
    Try to get results for one keyword from Google Transparency.
    Attempts the internal API endpoint first; falls back to HTML parsing.
    """
    results = []

    # Attempt 1: Internal API endpoint (JSON response)
    try:
        api_url = (
            f"https://adstransparency.google.com/anji/_/AdTransparencyUi/data/batchexecute"
        )
        # Build the RPC payload Google's SPA uses
        encoded_kw = quote_plus(keyword)
        search_url = (
            f"https://adstransparency.google.com/?region={region_code}"
            f"&topic=&text={encoded_kw}"
        )
        async with session.get(
            search_url,
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True,
        ) as resp:
            if resp.status == 200:
                html = await resp.text()
                extracted = _parse_html_for_advertisers(html, region_code)
                if extracted:
                    results.extend(extracted)
                    print(f"    → {len(extracted)} advertisers parsed from HTML")
                    return results

    except asyncio.TimeoutError:
        print(f"    Timeout on '{keyword}' — skipping")
    except Exception as e:
        print(f"    Google fetch error: {e}")

    return results


def _parse_html_for_advertisers(html: str, region_code: str) -> list[dict]:
    """
    Extract advertiser data from Google Transparency HTML/JSON blobs.
    Looks for JSON-LD, embedded data arrays, and advertiser name patterns.
    """
    results = []
    seen_names: set = set()

    # Pattern 1: JSON-LD schema data
    json_ld_pattern = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.DOTALL)
    for match in json_ld_pattern.finditer(html):
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict) and data.get("name"):
                name = data["name"]
                if name not in seen_names:
                    seen_names.add(name)
                    results.append({
                        "advertiser_name": name,
                        "platforms": ["google"],
                        "regions_targeted": [region_code],
                        "ad_copy_samples": [],
                    })
        except Exception:
            continue

    # Pattern 2: Embedded data arrays in page JS
    # Google sometimes embeds advertiser data as JS arrays
    name_pattern = re.compile(r'"advertiserName"\s*:\s*"([^"]{3,80})"')
    for match in name_pattern.finditer(html):
        name = match.group(1).strip()
        if name and name not in seen_names and not name.startswith("\\"):
            seen_names.add(name)
            results.append({
                "advertiser_name": name,
                "platforms": ["google"],
                "regions_targeted": [region_code],
                "ad_copy_samples": [],
            })

    # Pattern 3: advertiser profile links
    link_pattern = re.compile(r'/advertiser/([A-Z0-9]{10,})')
    advertiser_ids = set(link_pattern.findall(html))

    # Only use link pattern if we found no names yet
    if not results and advertiser_ids:
        for adv_id in list(advertiser_ids)[:10]:
            results.append({
                "advertiser_name": f"Advertiser_{adv_id}",
                "advertiser_id": adv_id,
                "google_profile_url": f"https://adstransparency.google.com/advertiser/{adv_id}",
                "platforms": ["google"],
                "regions_targeted": [region_code],
                "ad_copy_samples": [],
            })

    return results


def save_results(results: list, sector: str, country: str) -> Path:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = DATA_DIR / f"google_raw_{sector}_{country}_{date_str}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Saved {len(results)} results to {filename.name}")
    return filename


async def run_all_sectors(countries: list | None = None) -> list:
    if countries is None:
        countries = ["UK", "IE"]

    all_results = []

    for sector in SECTOR_KEYWORDS:
        for country in countries:
            print(f"\n[Google] Scraping: {sector.upper()} | {country}")
            try:
                results = await scrape_google_transparency(sector, country)
                save_results(results, sector, country)
                all_results.extend(results)
                print(f"  → {len(results)} advertisers found")
            except Exception as e:
                print(f"  ERROR: {e}")

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    combined_path = DATA_DIR / f"google_qualified_{date_str}.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Google combined: {len(all_results)} companies → {combined_path}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Transparency Scraper (HTTP, no browser)")
    parser.add_argument("--sector", choices=list(SECTOR_KEYWORDS.keys()))
    parser.add_argument("--country", choices=["UK", "IE"], default="UK")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        asyncio.run(run_all_sectors())
    elif args.sector:
        async def _single():
            results = await scrape_google_transparency(args.sector, args.country)
            save_results(results, args.sector, args.country)
        asyncio.run(_single())
    else:
        parser.print_help()
