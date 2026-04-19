"""
Meta Ad Library Scraper — UK & Ireland Trades
==============================================
Scrapes the PUBLIC Meta Ad Library website (facebook.com/ads/library).
No API credentials, no tokens, no developer account required.

The public Ad Library is the same data Meta exposes at:
  https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=GB&q=solar+panels

This scraper uses the internal JSON endpoint that powers that page.
"""

from __future__ import annotations
import asyncio
import json
import random
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR.mkdir(exist_ok=True)

# Public Ad Library search endpoint — no auth required
AD_LIBRARY_URL = "https://www.facebook.com/ads/library/async/search_ads/"

COUNTRY_CODES = {
    "UK": "GB",
    "IE": "IE",
}

SECTOR_KEYWORDS = {
    "plumbing": [
        "emergency plumber", "boiler repair", "boiler installation",
        "drain unblocking", "heating engineer",
    ],
    "solar": [
        "solar panel installation", "solar panels", "EV charger installation",
        "battery storage home", "SEAI solar grant",
    ],
    "electrical": [
        "electrician", "EICR certificate", "rewiring house",
        "smart home installation",
    ],
    "alarms": [
        "intruder alarm installation", "CCTV installation",
        "home security system",
    ],
    "insulation": [
        "cavity wall insulation", "loft insulation",
        "external wall insulation", "ECO4 scheme",
    ],
    "windows_doors": [
        "double glazing", "composite doors", "bifold doors",
        "window replacement",
    ],
    "drainage": [
        "CCTV drain survey", "drain jetting", "drain unblocking",
        "septic tank emptying",
    ],
    "pumps": [
        "borehole pump", "sewage pump installation",
        "submersible pump", "pump repair",
    ],
}

# Rotate realistic browser headers to avoid blocks
HEADER_SETS = [
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.facebook.com/ads/library/",
        "Origin": "https://www.facebook.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.facebook.com/ads/library/",
        "Connection": "keep-alive",
    },
]


def load_credentials() -> dict:
    creds_path = CONFIG_DIR / "credentials.json"
    if creds_path.exists():
        with open(creds_path) as f:
            return json.load(f)
    return {}


def calculate_tenure_months(ad_start_date: str | None) -> int:
    if not ad_start_date:
        return 0
    try:
        start_str = ad_start_date.replace("+0000", "+00:00")
        start = datetime.fromisoformat(start_str).replace(tzinfo=None)
        delta = datetime.utcnow() - start
        return max(0, int(delta.days / 30.44))
    except Exception:
        return 0


def parse_ad_record(ad: dict, keyword: str, sector: str, country: str) -> dict:
    """Parse a raw ad record from the public Ad Library into our standard format."""
    page_name = (
        ad.get("page_name")
        or ad.get("pageName")
        or ad.get("snapshot", {}).get("page_name")
        or "Unknown"
    )
    page_id = (
        ad.get("page_id")
        or ad.get("pageID")
        or ad.get("snapshot", {}).get("page_id")
    )
    start_date = (
        ad.get("ad_delivery_start_time")
        or ad.get("startDate")
        or ad.get("start_date")
    )
    platforms = ad.get("publisher_platforms") or ad.get("publisherPlatforms") or ["facebook"]
    bodies = ad.get("ad_creative_bodies") or []
    titles = ad.get("ad_creative_link_titles") or []

    # Pull from snapshot if top-level fields are absent
    snapshot = ad.get("snapshot") or {}
    if not bodies:
        bodies = snapshot.get("bodies") or snapshot.get("ad_creative_bodies") or []
        if bodies and isinstance(bodies[0], dict):
            bodies = [b.get("text", "") for b in bodies]
    if not titles:
        titles = snapshot.get("title") or []
        if isinstance(titles, str):
            titles = [titles]

    return {
        "advertiser_name": page_name,
        "page_id": str(page_id) if page_id else None,
        "keyword_found_under": keyword,
        "ad_start_date": start_date,
        "platforms": platforms if isinstance(platforms, list) else [platforms],
        "ad_count": 1,
        "ad_copy_samples": (bodies + titles)[:3],
        "ad_snapshot_url": ad.get("ad_snapshot_url") or snapshot.get("ad_snapshot_url"),
        "country": country,
        "sector": sector,
        "source": "meta_ad_library_public",
        "scraped_at": datetime.utcnow().isoformat(),
    }


async def fetch_ads_public(
    session: "aiohttp.ClientSession",
    keyword: str,
    country_code: str,
    forward_cursor: str | None = None,
) -> dict:
    """
    Call the public Meta Ad Library async search endpoint.
    Returns parsed JSON with 'payload' containing ad results.
    """
    params = {
        "active_status": "active",
        "ad_type": "all",
        "country": country_code,
        "q": keyword,
        "search_type": "keyword_unordered",
        "media_type": "all",
        "content_languages[0]": "en",
    }
    if forward_cursor:
        params["forward_cursor"] = forward_cursor

    headers = random.choice(HEADER_SETS)

    async with session.get(
        AD_LIBRARY_URL,
        params=params,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=30),
    ) as resp:
        if resp.status != 200:
            body = await resp.text()
            raise RuntimeError(f"HTTP {resp.status}: {body[:200]}")
        text = await resp.text()
        # The endpoint returns a for(;;); prefix — strip it
        if text.startswith("for (;;);"):
            text = text[9:]
        elif text.startswith("for(;;);"):
            text = text[8:]
        return json.loads(text)


def extract_ads_from_payload(payload: dict) -> tuple[list, str | None]:
    """
    Pull the list of ad objects and next cursor from the API response.
    Meta's response structure varies — try multiple known shapes.
    """
    ads = []
    next_cursor = None

    # Shape 1: payload.results
    results = payload.get("payload", {}).get("results") or payload.get("results") or []
    if results:
        ads = results
        next_cursor = (
            payload.get("payload", {}).get("forwardCursor")
            or payload.get("forwardCursor")
        )
        return ads, next_cursor

    # Shape 2: payload.data
    data = payload.get("payload", {}).get("data") or payload.get("data") or []
    if data:
        ads = data
        paging = payload.get("payload", {}).get("paging") or payload.get("paging") or {}
        next_cursor = paging.get("cursors", {}).get("after") or paging.get("after")
        return ads, next_cursor

    return [], None


async def scrape_meta_library(sector: str, country: str, max_results: int = 200) -> list[dict]:
    """Scrape the public Meta Ad Library for a given sector and country."""
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp not installed. Run: pip3 install aiohttp")

    country_code = COUNTRY_CODES.get(country, "GB")
    keywords = SECTOR_KEYWORDS.get(sector, [])
    results = []
    seen_pages: set = set()

    async with aiohttp.ClientSession() as session:
        for keyword in keywords[:3]:
            print(f"  Searching Meta Ad Library: '{keyword}' | {country}")
            forward_cursor = None
            collected = 0
            pages_fetched = 0

            try:
                while collected < max_results and pages_fetched < 5:
                    raw = await fetch_ads_public(session, keyword, country_code, forward_cursor)
                    ads, forward_cursor = extract_ads_from_payload(raw)

                    if not ads:
                        break

                    for ad in ads:
                        page_name = (
                            ad.get("page_name")
                            or ad.get("pageName")
                            or ad.get("snapshot", {}).get("page_name", "")
                        )
                        if page_name and page_name not in seen_pages:
                            seen_pages.add(page_name)
                            results.append(parse_ad_record(ad, keyword, sector, country))
                            collected += 1

                    pages_fetched += 1
                    if not forward_cursor:
                        break
                    await asyncio.sleep(random.uniform(2, 4))

                print(f"    → {collected} unique advertisers for '{keyword}'")

            except Exception as e:
                print(f"    Error on '{keyword}': {e}")
                continue

            await asyncio.sleep(random.uniform(2, 4))

    return results


def save_results(results: list, sector: str, country: str) -> Path:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = DATA_DIR / f"meta_raw_{sector}_{country}_{date_str}.json"
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
            print(f"\n[Meta] Scraping: {sector.upper()} | {country}")
            try:
                results = await scrape_meta_library(sector, country)
                save_results(results, sector, country)
                qualified = [r for r in results if calculate_tenure_months(r.get("ad_start_date")) >= 3]
                all_results.extend(qualified)
                print(f"  → {len(qualified)}/{len(results)} qualify (3+ months tenure)")
            except Exception as e:
                print(f"  ERROR on {sector}/{country}: {e}")

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    combined_path = DATA_DIR / f"meta_qualified_{date_str}.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Meta combined: {len(all_results)} qualified companies → {combined_path.name}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta Ad Library public scraper")
    parser.add_argument("--sector", choices=list(SECTOR_KEYWORDS.keys()), help="Single sector only")
    parser.add_argument("--country", default="UK", choices=["UK", "IE"])
    args = parser.parse_args()

    async def main():
        if args.sector:
            results = await scrape_meta_library(args.sector, args.country)
            save_results(results, args.sector, args.country)
            print(f"\n{len(results)} results saved.")
        else:
            await run_all_sectors()

    asyncio.run(main())
