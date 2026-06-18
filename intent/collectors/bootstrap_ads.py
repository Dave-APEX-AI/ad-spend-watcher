"""
Collector: ADVERTISING signals.

Two free sources, no new scraping required for the bootstrap:
  1. The existing ad-spend-watcher output (../data/companies.json) — 78 firms
     already verified as active Meta advertisers. Each becomes an `advertising`
     signal, so the new engine inherits all of that work for free.
  2. Optional per-vertical sample (sample_ads_<vertical>.json) for the seed
     vertical, representing a fresh Meta Ad Library / Google Ads Transparency
     sweep (reuse scripts/scraper_meta.py for the live version).

Run:  python intent/collectors/bootstrap_ads.py [vertical]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

ROOT_COMPANIES = os.path.join(os.path.dirname(lib.HERE), "data", "companies.json")


def _from_existing_pipeline():
    companies = lib.load_json(ROOT_COMPANIES, [])
    signals = []
    for c in companies or []:
        name = c.get("name", "").strip()
        if not name or config.is_chain(name):
            continue
        vertical = (c.get("sector") or "other").lower().replace(" ", "_")
        tenure = c.get("tenure_months", 0)
        # longer sustained spend = a touch more weight (caps at the base weight)
        strength = min(config.SIGNAL_WEIGHTS["advertising"],
                       config.SIGNAL_WEIGHTS["advertising"] * (0.6 + min(tenure, 24) / 60))
        signals.append(lib.signal(
            name, vertical, "advertising",
            strength=round(strength, 1),
            headline=f"Active Meta advertiser — {tenure} months sustained spend",
            evidence_url=c.get("page_url", ""),
            country=c.get("country", "UK"),
            detected_at=c.get("first_seen") or lib.today(),
            raw={"tenure_months": tenure, "website": (c.get("contact") or {}).get("website"),
                 "page_url": c.get("page_url"), "source": "ad-spend-watcher"},
        ))
    return signals


def _from_sample(vertical):
    raw = lib.load_json(os.path.join(lib.DATA, f"sample_ads_{vertical}.json"))
    if not raw:
        return []
    signals = []
    for r in raw.get("advertisers", []):
        if config.is_chain(r["company"]):
            continue
        signals.append(lib.signal(
            r["company"], vertical, "advertising",
            strength=config.SIGNAL_WEIGHTS["advertising"],
            headline=r.get("headline", "Active on Meta Ad Library"),
            evidence_url=r.get("url", ""),
            country=r.get("country", "UK"),
            raw={"platform": r.get("platform", "meta")},
        ))
    return signals


def collect(vertical=config.DEFAULT_VERTICAL):
    return _from_existing_pipeline() + _from_sample(vertical)


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_VERTICAL
    sig = collect(v)
    n = lib.append_signals(sig)
    print(f"[ads] {len(sig)} advertising signals ({n} new to log)")
