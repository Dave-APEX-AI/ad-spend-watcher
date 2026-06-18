"""
Collector: HIRING signals from free job APIs.

A live job ad is the most universally-available growth signal: a firm staffing
up is winning bigger contracts / opening capacity, and almost always about to
need more lead-gen. We use Adzuna's FREE API (register an app at
https://developer.adzuna.com/ — free tier, generous limits) with Reed as an
alt. Credentials live in config/credentials.json (gitignored), shape:

    {"ADZUNA_APP_ID": "...", "ADZUNA_APP_KEY": "...", "REED_API_KEY": "..."}

No key / no network => falls back to the bundled sample so the demo still runs.

Run:  python intent/collectors/collect_jobs.py [vertical]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

CREDS = os.path.join(os.path.dirname(lib.HERE), "config", "credentials.json")


def _creds():
    return lib.load_json(CREDS, {}) or {}


def _adzuna_search(role, app_id, app_key, country="gb"):
    q = urllib.parse.urlencode({
        "app_id": app_id, "app_key": app_key,
        "what_phrase": role, "results_per_page": 20, "max_days_old": 30,
        "content-type": "application/json",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "intent-engine"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _live(vertical):
    c = _creds()
    app_id, app_key = c.get("ADZUNA_APP_ID"), c.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return None
    by_company = {}
    for role in config.VERTICALS[vertical]["job_roles"]:
        for country in ("gb", "ie"):
            try:
                res = _adzuna_search(role, app_id, app_key, country)
            except Exception:
                continue
            for job in res.get("results", []):
                name = (job.get("company", {}) or {}).get("display_name", "").strip()
                if not name:
                    continue
                rec = by_company.setdefault(name, {"count": 0, "roles": set(),
                                                   "country": "IE" if country == "ie" else "UK",
                                                   "url": job.get("redirect_url", "")})
                rec["count"] += 1
                rec["roles"].add(job.get("title", role))
    return by_company or None


def _sample(vertical):
    path = os.path.join(lib.DATA, f"sample_jobs_{vertical}.json")
    raw = lib.load_json(path)
    if not raw:
        return {}
    out = {}
    for r in raw.get("postings", []):
        out[r["company"]] = {"count": r["count"], "roles": set(r["roles"]),
                             "country": r.get("country", "UK"), "url": r.get("url", "")}
    return out


def collect(vertical=config.DEFAULT_VERTICAL):
    by_company = _live(vertical)
    if by_company is None:
        by_company = _sample(vertical)

    signals = []
    for name, rec in by_company.items():
        if config.is_chain(name):
            continue
        n = min(rec["count"], config.HIRING_CAP)
        roles = ", ".join(sorted(rec["roles"])[:3])
        plural = "roles" if rec["count"] != 1 else "role"
        signals.append(lib.signal(
            name, vertical, "hiring",
            strength=config.SIGNAL_WEIGHTS["hiring"] * n / config.HIRING_CAP,
            headline=f"Hiring {rec['count']} {plural} — {roles}",
            evidence_url=rec.get("url", ""),
            country=rec.get("country", "UK"),
            raw={"open_roles": rec["count"], "titles": sorted(rec["roles"])},
        ))
    return signals


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_VERTICAL
    sig = collect(v)
    n = lib.append_signals(sig)
    print(f"[jobs/{v}] {len(sig)} hiring signals ({n} new to log)")
    for s in sig:
        print(f"  + {s['company']} — {s['headline']}")
