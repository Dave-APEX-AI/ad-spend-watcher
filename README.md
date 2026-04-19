# UK & Ireland Trades — Ad Spend Watcher

Automated weekly intelligence on UK & Ireland trade companies advertising on
Meta (Facebook/Instagram) and ranking on Google. Surfaces sustained-spend
advertisers as outreach targets.

## Live dashboard

**For the VA:** https://dave-apex-ai.github.io/ad-spend-watcher/

Updated every Sunday after the weekly run. Past weeks live in
[/archive/](archive/).

## Coverage

- **8 sectors:** Solar, Plumbing, Electrical, Alarms, Insulation,
  Windows & Doors, Drainage, Pumps
- **2 countries:** UK, Ireland
- **Minimum qualifying tenure:** 3 months active advertising
- **Scoring tiers:** Hot (70+), Warm (55–69), Watch (<55)

## How it runs

Every Sunday, the scheduled task on Dave's Mac runs:

```
cd ~/ad-spend-watcher && git pull && python scripts/weekly_run.py
```

That script:

1. Scrapes the Meta Ad Library (via Chrome MCP) for all 8 sectors × 2 countries
2. Filters to companies active for 3+ months
3. Verifies Tier-1 candidates on Google (page-1 presence)
4. Scores and tiers each company
5. Writes `data/companies.json` (live dashboard data)
6. Writes `data/scored_YYYY-MM-DD.json` (historical record)
7. Builds the Word report in `reports/`
8. Freezes a snapshot to `archive/YYYY-MM-DD.html`
9. Commits and pushes — GitHub Pages rebuilds automatically within ~1 minute

## Repo layout

```
/
  index.html          # Live dashboard (copy of dashboard.html, for GH Pages root)
  dashboard.html      # Live dashboard source
  archive/            # Frozen past snapshots
    index.html        # Listing page
    2026-04-19.html
    ...
  data/
    companies.json    # Latest 55 enriched companies (dashboard reads this)
    scored_*.json     # Historical per-week scored data
    meta_qualified_*.json  # Historical per-week qualified data
    run_log.jsonl     # One line per weekly run
  reports/
    Weekly Report *.docx   # Word exports
  scripts/
    weekly_run.py     # Sunday entry point
    scraper_meta.py
    scraper_google.py
    scraper_google_verify.py
    scoring.py
    convert_browser_data.py
    enrichment.py
    publish.py        # git add/commit/push helper
  config/
    credentials.json  # API keys — NEVER committed (.gitignored)
  onepagers/          # Sample outreach assets
```

## Setup (one-time)

On the Mac that runs the automation:

```bash
git clone https://github.com/Dave-APEX-AI/ad-spend-watcher.git
cd ad-spend-watcher
cp config/credentials.json.example config/credentials.json
# fill in META_USER_ACCESS_TOKEN and GITHUB_TOKEN
pip3 install aiohttp --break-system-packages
```

Schedule `scripts/weekly_run.py` to run every Sunday (existing task just needs
`cd ~/ad-spend-watcher && git pull && python scripts/weekly_run.py`).

## For future Claude sessions

See [CLAUDE.md](CLAUDE.md) for project context, architecture, and common
operations.
