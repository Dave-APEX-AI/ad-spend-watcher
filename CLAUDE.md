# CLAUDE.md — Project context for future Claude sessions

This file is loaded by Claude Code / Cowork mode when working in this repo.
Read it first before making any changes.

## What this project is

Weekly lead-gen automation for Dave's digital-marketing agency. Scans the Meta
Ad Library for UK & Ireland trade companies (8 sectors), qualifies companies
with 3+ months of sustained Meta spend, verifies them on Google, scores them
(Hot / Warm / Watch), and writes the results to a live dashboard hosted on
GitHub Pages for a VA to work from.

## Core principles

1. **No paid tools, ever.** The stack is free: Chrome MCP scraping,
   free Meta Ad Library, free Google search verification, GitHub Pages (free),
   Cloudflare Workers free tier for status sync. No Apollo, Clay, Cognism,
   Clearbit, Apify, or LinkedIn scrapers.

2. **No Companies House / CRO lookups.** Tried before — not a strong enough
   signal for this use case and adds friction. Skip them.

3. **VA must be able to work from the dashboard alone.** The VA follows very
   direct instructions — every action a lead needs (call, email, copy a
   template) should be one click from the dashboard.

4. **The working folder on Dave's Mac IS the repo.** Don't re-design around a
   separate data folder.

## Scoring methodology

- **Tenure:** 0–50 points based on months of continuous Meta spend
- **Google page-1 verification:** +20 points, with +5 bonus for top-3 rank
- **Minimum qualifying tenure:** 3 months (enforced in `convert_browser_data.py`)
- **Tier cutoffs:** Hot ≥ 70, Warm 55–69, Watch < 55
- **Tier 1:** 12+ months (flagship candidates, always Google-verified)
- **Tier 2:** 6–11 months
- **Tier 3:** 3–5 months

## Weekly run pipeline

```
scripts/weekly_run.py
├── scraper_meta.py        # Chrome-based Meta Ad Library scrape → data/meta_raw_browser_*.txt
├── convert_browser_data.py # Parse pipe-delimited raw into data/meta_qualified_*.json
├── scraper_google_verify.py # Python aiohttp Google page-1 check
├── scoring.py              # Score, tier, write data/scored_*.json
├── build companies.json    # Dashboard-ready format (55 records)
├── build_report.js         # Node/docx Word report → reports/Weekly Report *.docx
├── freeze snapshot         # Dashboard HTML with embedded data → archive/YYYY-MM-DD.html
└── publish.py              # git add/commit/push
```

## The "Chrome verification" override

For the Tier-1 Google check, when running from Cowork / Claude Code
interactively, use the Chrome MCP (DOM-aware, cookie-bearing) instead of the
bare `scraper_google_verify.py` aiohttp path — Google will 429 a plain HTTP
client but not a logged-in browser. The verified rank still goes into
`scored_*.json` via a small inline Python block. See run log 2026-04-19 for
the pattern.

## FB URL capture (next weekly run)

**During the Chrome-based Meta Ad Library scrape, capture the advertiser's
Facebook page URL as a 5th pipe field:**

```
Company Name|DD Mon YYYY|sector|UK_or_IE|https://www.facebook.com/<slug>/
```

Why: the VA dashboard renders `contact.socials.facebook` as a clickable chip
on each card — one click takes the VA to the company's FB page, which
already has website, bio, phone, and IG link in one place. Pulling this during
the scrape (when we're already on the search-results page for each
advertiser) costs almost nothing and eliminates a 55-company manual backfill.

A one-off backfill of 32/55 was done 2026-04-19 (see
`data/companies.json`). The remaining 25 are flagged with
`contact.needs_fb_url: true`; next week's scrape should populate them
automatically.

In the JS extractor running inside the Ad Library search results page, the
pattern is:

```js
Array.from(document.querySelectorAll('a[href*="facebook.com"]'))
  .map(a => { const u = new URL(a.href); return (u.pathname.match(/^\/([^\/]+)/)||[,''])[1]; })
  .filter(s => s && /^[a-zA-Z0-9.\-_]+$/.test(s))
```

then fuzzy-match the slug against the advertiser's normalized name. Numeric
page IDs (e.g. `61569350681767`) are also valid — FB serves the page at
`facebook.com/<page_id>`.

## Dashboard data contract

`data/companies.json` is an array of objects with these fields:

```
{
  "id": "uuid-or-stable-string",
  "name": "Company Name",
  "sector": "solar|plumbing|electrical|alarms|insulation|windows_doors|drainage|pumps",
  "country": "UK" | "IE",
  "region_label": "UK — Solar" etc.,
  "staff": "1–10" | "11–50" | ...,
  "tenure_months": 14,
  "tenure_label": "14 months",
  "score": 78,
  "score_label": "Hot" | "Warm" | "Watch",
  "hot_trigger": "..." (optional — e.g. "Google top-3 + 12mo+"),
  "platforms": ["meta", "google"],
  "audience": "homeowners" (optional),
  "spend": [<sparkline ints>],
  "contact": {
    "name": "Owner Name",
    "role": "Owner" | "Director" | ...,
    "email": "owner@company.com",
    "phone": "+44 ...",
    "website": "https://...",
    "socials": {"facebook": "...", "instagram": "...", "linkedin": "..."}
  },
  "avatar": "OW", "avatarBg": "#...", "avatarCol": "#..."
}
```

The dashboard renders Hot / Warm / Watch / All tabs, 8 sector filters, and
(once the status layer ships) a Not-contacted / Contacted / Replied / Booked /
Passed CRM state with notes stored in localStorage, synced to a Cloudflare
Worker-backed `status.json`.

## Security

- **Never commit `config/credentials.json`.** It's in `.gitignore` — verify on
  every commit with `git status` before pushing.
- The GitHub PAT is fine-grained, scoped to this repo only, Contents:Read/write
  + Metadata:Read-only. Rotate via GitHub settings if exposed.
- Meta user access tokens last ~60 days; regenerate at
  https://developers.facebook.com/tools/explorer/

## Common ops

- **Fresh run for a specific date:**
  ```
  python scripts/weekly_run.py --date 2026-04-19
  ```
- **Re-score without re-scraping:**
  ```
  python scripts/scoring.py --input data/meta_qualified_2026-04-19.json --prev data/meta_qualified_2026-04-12.json
  ```
- **Rebuild a Word report from existing scored JSON:**
  ```
  node scripts/build_report.js reports/Weekly\ Report\ 19\ April\ 2026.docx
  ```
- **Freeze a snapshot from the live dashboard:**
  ```
  python scripts/freeze_snapshot.py --date 2026-04-19
  ```

## What's in flight

- Enrichment pass: adding `contact` (owner name, email, phone, socials) to
  all 55 companies via Chrome scraping of each company's Facebook page About +
  website contact/about pages. No paid tools.
- CRM status layer: localStorage v1 now, Cloudflare Worker backed status.json
  for cross-device sync in v2.
- VA idiot-proofing: tel:/mailto: chips, sector-specific Copy-template buttons,
  "today" view filter, Sunday morning email summary, tooltips.
