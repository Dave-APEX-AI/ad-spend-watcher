"""
Convert Browser-Scraped Ad Library Data to Pipeline JSON
=========================================================
Parses pipe-delimited text extracted from the Meta Ad Library via Chrome browser
and converts it to the pipeline JSON format used by scoring.py.

Why this exists:
  The Meta Ad Library blocks plain HTTP requests (HTTP 403 / JS challenge).
  Data is collected by navigating in a real Chrome browser (via Chrome MCP),
  injecting a JavaScript extractor, and reading back the results in 900-char
  chunks (to work within MCP tool output limits).

Input format (one record per line):
  Company Name|DD Mon YYYY|sector|UK_or_IE

Usage:
  python3 scripts/convert_browser_data.py \\
    --input  data/meta_raw_browser_2026-04-14.txt \\
    --output data/meta_qualified_2026-04-14.json \\
    --date   2026-04-14
"""

from __future__ import annotations
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def parse_date(date_str: str) -> str | None:
    """Parse UK-format date string to ISO 8601, stripping Meta noise like '· Total active time'."""
    if not date_str:
        return None
    # Strip "· Total active time X hrs" suffix that appears on very-new ads
    if "·" in date_str:
        date_str = date_str.split("·")[0].strip()
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%dT00:00:00+0000")
        except ValueError:
            continue
    return None


def calculate_tenure_months(iso_date: str | None) -> int:
    if not iso_date:
        return 0
    try:
        start = datetime.strptime(iso_date[:10], "%Y-%m-%d")
        delta = datetime.utcnow() - start
        return max(0, int(delta.days / 30.44))
    except Exception:
        return 0


def convert(input_path: Path, output_path: Path, date_str: str) -> list:
    """Parse pipe-delimited browser export and return qualified records."""
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    raw_lines = input_path.read_text(encoding="utf-8").strip().splitlines()
    scraped_at = datetime.utcnow().isoformat()
    records = []
    skipped = 0

    for line in raw_lines:
        parts = line.split("|")
        if len(parts) < 4:
            skipped += 1
            continue

        name      = parts[0].strip()
        date_raw  = parts[1].strip() if len(parts) > 1 else ""
        sector    = parts[2].strip() if len(parts) > 2 else ""
        country   = parts[3].strip() if len(parts) > 3 else ""

        # Skip noise rows
        if not name or not sector or not country:
            skipped += 1
            continue
        if len(name) > 80 or name in ("Sponsored", "See ad details"):
            skipped += 1
            continue

        iso_date = parse_date(date_raw)
        tenure   = calculate_tenure_months(iso_date)

        records.append({
            "advertiser_name":    name,
            "page_id":            None,
            "keyword_found_under": sector,
            "ad_start_date":      iso_date,
            "tenure_months":      tenure,
            "platforms":          ["facebook"],
            "ad_count":           1,
            "ad_copy_samples":    [],
            "ad_snapshot_url":    None,
            "country":            country,
            "sector":             sector,
            "source":             "meta_ad_library_browser",
            "scraped_at":         scraped_at,
            # Google verification fields — populated by Step 5 of the weekly pipeline
            "google_page1":       False,
            "google_page1_rank":  None,
            "google_rank_band":   "not_found",
            "google_ads_verified": False,
            "google_visible":     False,
        })

    qualified = [r for r in records if r["tenure_months"] >= 3]

    # Summary
    from collections import Counter
    sector_counts  = Counter(r["sector"]  for r in qualified)
    country_counts = Counter(r["country"] for r in qualified)

    print(f"Parsed   : {len(records)} records ({skipped} skipped)")
    print(f"Qualified: {len(qualified)} companies (3+ months tenure)")
    print(f"By sector:")
    for s, c in sorted(sector_counts.items()):
        print(f"  {s:<20} {c}")
    print(f"By country: {dict(country_counts)}")

    # Guard: never write an empty file over a good one
    if len(qualified) == 0:
        existing = []
        if output_path.exists():
            try:
                existing = json.loads(output_path.read_text())
            except Exception:
                pass
        if existing:
            print(f"WARNING: 0 qualified companies parsed — keeping existing file ({len(existing)} records)")
            return existing
        else:
            print("WARNING: 0 qualified companies and no existing file to fall back on.")

    output_path.write_text(json.dumps(qualified, indent=2))
    print(f"\nSaved {len(qualified)} qualified records → {output_path.name}")
    return qualified


def main():
    parser = argparse.ArgumentParser(description="Convert browser-scraped Ad Library data")
    parser.add_argument("--input",  required=True, help="Path to pipe-delimited .txt file")
    parser.add_argument("--output", help="Output JSON path (default: data/meta_qualified_DATE.json)")
    parser.add_argument("--date",   help="Date string for default output filename (YYYY-MM-DD)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")
        output_path = DATA_DIR / f"meta_qualified_{date_str}.json"

    convert(input_path, output_path, args.date or datetime.utcnow().strftime("%Y-%m-%d"))


if __name__ == "__main__":
    main()
