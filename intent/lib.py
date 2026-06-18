"""
Intent Engine — shared helpers: paths, slugify, the Signal record, and
append-only signal-log IO. Kept dependency-free (stdlib only) so it runs on
Dave's Mac with a bare Python 3.
"""
import json
import os
import re
import datetime as _dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SIGNALS_LOG = os.path.join(DATA, "signals.jsonl")
COMPANIES_OUT = os.path.join(DATA, "intent_companies.json")
ACTION_QUEUE = os.path.join(DATA, "action_queue.json")
ROSTER = os.path.join(DATA, "roster.json")


def load_roster():
    data = load_json(ROSTER, {"companies": []})
    return data.get("companies", [])

os.makedirs(DATA, exist_ok=True)


def today() -> str:
    return _dt.date.today().isoformat()


def days_since(iso_date: str) -> int:
    try:
        d = _dt.date.fromisoformat(iso_date[:10])
    except (ValueError, TypeError):
        return 0
    return (_dt.date.today() - d).days


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "unknown"


def signal(company, vertical, signal_type, *, strength, headline,
           evidence_url="", country="UK", detected_at=None, raw=None):
    """Build one normalized signal record."""
    return {
        "company": company,
        "company_id": slugify(company),
        "vertical": vertical,
        "country": country,
        "signal_type": signal_type,
        "strength": strength,
        "headline": headline,
        "evidence_url": evidence_url,
        "detected_at": detected_at or today(),
        "raw": raw or {},
    }


def load_signals():
    out = []
    if not os.path.exists(SIGNALS_LOG):
        return out
    with open(SIGNALS_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _dedupe_key(s):
    # One company can't log the "same" signal twice on the same day from the
    # same source headline — keeps weekly re-runs idempotent.
    return (s["company_id"], s["signal_type"], s["headline"], s["detected_at"])


def append_signals(new_signals):
    """Append signals, skipping exact duplicates already in the log."""
    existing = {_dedupe_key(s) for s in load_signals()}
    added = 0
    with open(SIGNALS_LOG, "a") as f:
        for s in new_signals:
            if _dedupe_key(s) in existing:
                continue
            f.write(json.dumps(s) + "\n")
            existing.add(_dedupe_key(s))
            added += 1
    return added


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
