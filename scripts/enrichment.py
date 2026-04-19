"""
Enrichment Script — Companies House (UK) + CRO Ireland + LinkedIn
=================================================================
Takes a list of company names (from scrapers) and enriches each with:
  - Director / decision-maker name and role
  - Employee count band
  - Registered address / region confirmation
  - Company status (active vs dissolved)

UK:  Uses the official Companies House REST API (free, no scraping needed)
IE:  Scrapes CRO Ireland web interface (no public API available)
LI:  Manual LinkedIn lookup — script generates URLs to check, not automated

Usage:
  python enrichment.py --input data/meta_qualified_2024-11-04.json
  python enrichment.py --company "Greenflow Solar Ltd" --country UK

Output:
  data/enriched_{date}.json  — merged company records with contact data

Setup:
  Get a free Companies House API key at:
  https://developer.company-information.service.gov.uk/
  Add to config/credentials.json as: { "COMPANIES_HOUSE_API_KEY": "your_key" }
"""

from __future__ import annotations
import asyncio
import json
import re
import time
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

COMPANIES_HOUSE_BASE = "https://api.company-information.service.gov.uk"
CRO_BASE = "https://core.cro.ie"

EMPLOYEE_BANDS = {
    "1 to 10": "1-10",
    "11 to 20": "10-20",
    "21 to 50": "20-50",
    "51 to 100": "50+",
    "101 to 250": "50+",
    "251 to 500": "50+",
    "500+": "50+",
}


def load_credentials() -> dict:
    creds_path = CONFIG_DIR / "credentials.json"
    if creds_path.exists():
        with open(creds_path) as f:
            return json.load(f)
    return {}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPANIES HOUSE (UK)
# ═══════════════════════════════════════════════════════════════════════════════

async def search_companies_house(company_name: str, api_key: str) -> list[dict]:
    """Search Companies House for a company name. Returns top matches."""
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp not installed. Run: pip install aiohttp --break-system-packages")

    url = f"{COMPANIES_HOUSE_BASE}/search/companies?q={quote(company_name)}&items_per_page=5"
    auth = aiohttp.BasicAuth(api_key, "")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("items", [])
            elif resp.status == 401:
                raise ValueError("Invalid Companies House API key")
            else:
                print(f"    Companies House search failed: {resp.status}")
                return []


async def get_company_officers(company_number: str, api_key: str) -> list[dict]:
    """Fetch officer (director) list for a company from Companies House."""
    url = f"{COMPANIES_HOUSE_BASE}/company/{company_number}/officers"
    auth = aiohttp.BasicAuth(api_key, "")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("items", [])
            else:
                return []


async def get_company_profile(company_number: str, api_key: str) -> dict:
    """Fetch full company profile from Companies House."""
    url = f"{COMPANIES_HOUSE_BASE}/company/{company_number}"
    auth = aiohttp.BasicAuth(api_key, "")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as resp:
            if resp.status == 200:
                return await resp.json()
            return {}


def extract_director(officers: list[dict]) -> dict | None:
    """
    Find the best decision-maker from a list of officers.
    Priority: active > MD/Director/Founder > longest serving.
    """
    if not officers:
        return None

    # Filter to active (not resigned)
    active = [o for o in officers if not o.get("resigned_on")]
    if not active:
        active = officers  # fallback: use all

    # Priority role keywords
    priority_roles = ["managing director", "md", "founder", "owner", "chief executive",
                      "director", "proprietor"]

    for priority in priority_roles:
        for officer in active:
            role = officer.get("officer_role", "").lower()
            if priority in role:
                return _format_officer(officer)

    # Fallback: return first active officer
    return _format_officer(active[0])


def _format_officer(officer: dict) -> dict:
    """Format a Companies House officer record into our contact format."""
    name = officer.get("name", "Unknown")
    # CH returns name as "SURNAME, Firstname" — flip it
    parts = name.split(",")
    if len(parts) == 2:
        name = f"{parts[1].strip()} {parts[0].strip().title()}"

    role = officer.get("officer_role", "Director").replace("-", " ").title()

    # Appointment date
    appointed = officer.get("appointed_on", "")

    return {
        "name": name,
        "role": role,
        "appointed_on": appointed,
        "linkedin_url": None,  # populated separately
        "email": None,         # inferred separately
        "source": "companies_house"
    }


async def enrich_uk_company(company_name: str, api_key: str) -> dict:
    """
    Full enrichment for a UK company:
    1. Search Companies House
    2. Get company profile (status, address, employee count)
    3. Get officers (directors)
    4. Return structured enrichment record
    """
    print(f"    [CH] Enriching: {company_name}")

    # Step 1: Search
    matches = await search_companies_house(company_name, api_key)
    if not matches:
        return {"enrichment_status": "not_found", "company_name": company_name}

    # Take best match (first result, typically best name match)
    match = matches[0]
    company_number = match.get("company_number")
    registered_name = match.get("title", company_name)
    status = match.get("company_status", "unknown")

    if status not in ["active", "open"]:
        return {
            "enrichment_status": "not_active",
            "company_name": company_name,
            "registered_name": registered_name,
            "company_status": status
        }

    # Step 2: Full profile
    profile = await get_company_profile(company_number, api_key)
    address = profile.get("registered_office_address", {})
    sic_codes = profile.get("sic_codes", [])

    # Employee count (from accounts if available)
    accounts = profile.get("accounts", {})
    employee_band = profile.get("accounts", {}).get("last_accounts", {}).get("type", "")

    # Step 3: Officers
    await asyncio.sleep(0.3)  # rate limit: 600 req/5min
    officers = await get_company_officers(company_number, api_key)
    director = extract_director(officers)

    return {
        "enrichment_status": "found",
        "company_name": company_name,
        "registered_name": registered_name,
        "company_number": company_number,
        "company_status": status,
        "registered_address": {
            "line1": address.get("address_line_1", ""),
            "city": address.get("locality", ""),
            "postcode": address.get("postal_code", ""),
            "country": address.get("country", "United Kingdom")
        },
        "sic_codes": sic_codes,
        "director": director,
        "source": "companies_house",
        "enriched_at": datetime.utcnow().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CRO IRELAND
# ═══════════════════════════════════════════════════════════════════════════════

async def enrich_ie_company(company_name: str) -> dict:
    """
    Enrich an Irish company via CRO (Companies Registration Office).
    Uses aiohttp HTTP requests against core.cro.ie — no browser required.
    """
    if not AIOHTTP_AVAILABLE:
        return {"enrichment_status": "aiohttp_not_available", "company_name": company_name}

    print(f"    [CRO] Enriching: {company_name}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-IE,en;q=0.9",
        "Referer": "https://core.cro.ie/",
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Step 1: Search CRO for the company name
            search_url = f"https://core.cro.ie/api/company-search?q={quote(company_name)}&start=0&count=5"
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    # Fallback: try the HTML search page
                    return await _enrich_ie_html_fallback(session, company_name)

                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type:
                    data = await resp.json()
                    companies = data.get("companies") or data.get("results") or data.get("items") or []
                    if not companies:
                        return {"enrichment_status": "not_found", "company_name": company_name}

                    # Take first result
                    match = companies[0]
                    company_number = str(match.get("companyNumber") or match.get("company_number") or "")
                    status = (match.get("companyStatus") or match.get("status") or "unknown").lower()
                    registered_name = match.get("companyName") or match.get("name") or company_name

                    return {
                        "enrichment_status": "found",
                        "company_name": company_name,
                        "registered_name": registered_name,
                        "company_number": company_number,
                        "company_status": "active" if "normal" in status or "active" in status else status,
                        "director": None,
                        "source": "cro_ireland",
                        "enriched_at": datetime.utcnow().isoformat(),
                    }
                else:
                    # Response was HTML — parse it
                    html = await resp.text()
                    return _parse_cro_html(html, company_name)

    except asyncio.TimeoutError:
        print(f"    CRO timeout for '{company_name}'")
        return {"enrichment_status": "timeout", "company_name": company_name}
    except Exception as e:
        print(f"    CRO enrichment error: {e}")
        return {"enrichment_status": "error", "company_name": company_name, "error": str(e)}


async def _enrich_ie_html_fallback(session, company_name: str) -> dict:
    """Fallback: scrape the CRO HTML search page."""
    try:
        url = f"https://core.cro.ie/company-search?q={quote(company_name)}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return {"enrichment_status": "not_found", "company_name": company_name}
            html = await resp.text()
            return _parse_cro_html(html, company_name)
    except Exception as e:
        return {"enrichment_status": "error", "company_name": company_name, "error": str(e)}


def _parse_cro_html(html: str, company_name: str) -> dict:
    """Parse CRO HTML search results to extract company info."""
    # Extract company number
    num_match = re.search(r'Company No[.:\s]+(\d{4,7})', html)
    company_number = num_match.group(1) if num_match else None

    # Extract status
    status = "unknown"
    if re.search(r'\bNormal\b|\bActive\b', html, re.IGNORECASE):
        status = "active"
    elif re.search(r'\bDissolved\b|\bStruck Off\b', html, re.IGNORECASE):
        status = "dissolved"

    # Extract registered name from first result link text
    name_match = re.search(r'<a[^>]+href=["\'][^"\']*company[^"\']*["\'][^>]*>([^<]{5,80})</a>', html)
    registered_name = name_match.group(1).strip() if name_match else company_name

    if not company_number and "not_found" not in registered_name.lower():
        return {"enrichment_status": "not_found", "company_name": company_name}

    return {
        "enrichment_status": "found" if company_number else "partial",
        "company_name": company_name,
        "registered_name": registered_name,
        "company_number": company_number,
        "company_status": status,
        "director": None,
        "source": "cro_ireland",
        "enriched_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

def infer_email(first_name: str, last_name: str, domain: str) -> list[dict]:
    """
    Generate probable email patterns from a name and domain.
    Returns list of candidates, labelled as inferred.
    """
    first = first_name.lower().strip()
    last = last_name.lower().strip()
    f_initial = first[0] if first else ""

    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{f_initial}.{last}@{domain}",
        f"{f_initial}{last}@{domain}",
        f"info@{domain}",
    ]

    return [{"email": p, "confidence": "inferred — verify before sending"} for p in patterns]


def extract_domain_from_website(url: str) -> str | None:
    """Extract bare domain from a website URL."""
    if not url:
        return None
    match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', url)
    return match.group(1) if match else None


def generate_linkedin_url(name: str) -> str:
    """Generate a probable LinkedIn search URL for manual verification."""
    slug = name.lower().replace(" ", "-")
    return f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}&origin=GLOBAL_SEARCH_HEADER"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENRICHMENT PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

async def enrich_company_list(companies: list[dict]) -> list[dict]:
    """
    Enrich a list of companies with contact data.
    Processes UK companies via Companies House API,
    IE companies via CRO Ireland scrape.
    """
    creds = load_credentials()
    api_key = creds.get("COMPANIES_HOUSE_API_KEY")

    if not api_key:
        print("  ⚠ No COMPANIES_HOUSE_API_KEY in credentials.json")
        print("    Get a free key: https://developer.company-information.service.gov.uk/")
        print("    UK enrichment will be skipped.\n")

    enriched = []
    for company in companies:
        name = company.get("advertiser_name") or company.get("company_name", "")
        country = company.get("country", "UK")

        try:
            if country == "UK" and api_key:
                enrichment = await enrich_uk_company(name, api_key)
            elif country == "IE":
                enrichment = await enrich_ie_company(name)
            else:
                enrichment = {"enrichment_status": "skipped", "company_name": name}

            # Merge enrichment into company record
            merged = {**company, **enrichment}

            # Add email inference if we have a director name and company website
            director = enrichment.get("director") or {}
            director_name = director.get("name", "")
            website = company.get("website", "")
            domain = extract_domain_from_website(website)

            if director_name and domain:
                name_parts = director_name.split()
                if len(name_parts) >= 2:
                    merged["email_candidates"] = infer_email(name_parts[0], name_parts[-1], domain)

            # Add LinkedIn search URL
            if director_name:
                merged["linkedin_search_url"] = generate_linkedin_url(director_name)

            enriched.append(merged)

        except Exception as e:
            print(f"  Enrichment failed for {name}: {e}")
            enriched.append({**company, "enrichment_status": "error", "error": str(e)})

        # Rate limit: be gentle with APIs
        await asyncio.sleep(0.5)

    return enriched


def save_enriched(records: list[dict]):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = DATA_DIR / f"enriched_{date_str}.json"
    with open(path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"✓ Saved {len(records)} enriched records to {path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Company enrichment (Companies House + CRO)")
    parser.add_argument("--input", help="JSON file of scraped companies")
    parser.add_argument("--company", help="Single company name to look up")
    parser.add_argument("--country", choices=["UK", "IE"], default="UK")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            companies = json.load(f)
        enriched = asyncio.run(enrich_company_list(companies))
        save_enriched(enriched)
    elif args.company:
        async def _single():
            creds = load_credentials()
            api_key = creds.get("COMPANIES_HOUSE_API_KEY")
            if args.country == "UK" and api_key:
                result = await enrich_uk_company(args.company, api_key)
            else:
                result = await enrich_ie_company(args.company)
            print(json.dumps(result, indent=2))
        asyncio.run(_single())
    else:
        parser.print_help()
