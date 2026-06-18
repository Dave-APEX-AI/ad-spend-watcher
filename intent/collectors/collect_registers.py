"""
Collector: public competency/accreditation REGISTERS.

This is the engine's sharpest edge. Paid tools (Clay, Apollo, ZoomInfo) index
SaaS/firmographic exhaust; they do NOT index MCS / OZEV / TrustMark / REFCOM /
Ofsted / CQC / DVSA registers. Those are free, postcode-searchable, list every
*qualified* firm — and crucially they can be DIFFED week-over-week to catch a
business at its highest-intent moment: just qualified / just opened.

How it works:
  1. fetch_register(vertical) returns the current installer list. It tries a
     live fetch; if the source 403s or there's no network (common on gov/MCS
     pages), it falls back to the bundled SAMPLE snapshot so the pipeline always
     produces output.
  2. We diff the current list against the stored snapshot of installer_ids.
  3. Companies present now but absent last time => a `new_register` signal.
  4. We persist the current list as the new snapshot for next week's diff.

Run:  python intent/collectors/collect_registers.py [vertical]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

REG_DIR = os.path.join(lib.DATA, "registers")


def _live_fetch(vertical, reg):
    """Attempt a live register pull. Returns list of installer dicts or None.

    Intentionally conservative: MCS/gov registers are JS-driven or 403 plain
    HTTP clients, so on Dave's Mac the recommended path is the Chrome-MCP
    override (see CLAUDE.md 'Chrome verification' pattern). Here we just try a
    bare GET and fall back cleanly — we never fabricate live data.
    """
    try:
        import urllib.request
        req = urllib.request.Request(reg["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()  # reached it, but these pages need a real browser to parse
        return None  # signal: reachable but not parseable without Chrome MCP
    except Exception:
        return None


def fetch_register(vertical):
    cur_path = os.path.join(REG_DIR, f"{vertical}_current.json")
    for reg in config.VERTICALS[vertical]["registers"]:
        live = _live_fetch(vertical, reg)
        if live:
            data = {"vertical": vertical, "source": reg["name"],
                    "fetched": lib.today(), "installers": live}
            lib.save_json(cur_path, data)
            return data
    # fallback to bundled sample / last live capture
    data = lib.load_json(cur_path)
    if not data:
        return {"vertical": vertical, "source": "none", "installers": []}
    return data


def collect(vertical=config.DEFAULT_VERTICAL):
    os.makedirs(REG_DIR, exist_ok=True)
    data = fetch_register(vertical)
    installers = data.get("installers", [])
    source = data.get("source", "register")

    snap_path = os.path.join(REG_DIR, f"{vertical}_snapshot.json")
    snap = lib.load_json(snap_path, {}) or {}
    seen_ids = set(snap.get("installer_ids", []))

    signals = []
    current_ids = []
    for inst in installers:
        cid = lib.slugify(inst["name"])
        current_ids.append(cid)
        if config.is_chain(inst["name"]):
            continue  # never pitch corporate chains
        if cid not in seen_ids:
            reg = config.VERTICALS[vertical]["registers"][0]
            signals.append(lib.signal(
                inst["name"], vertical, "new_register",
                strength=config.SIGNAL_WEIGHTS["new_register"],
                headline=f"Newly listed on {source} register ({inst.get('tech','')})".strip(),
                evidence_url=reg["url"],
                country=inst.get("country", "UK"),
                raw={"town": inst.get("town"), "region": inst.get("region"),
                     "website": inst.get("website"), "tech": inst.get("tech")},
            ))

    # persist current as the snapshot for next week's diff
    lib.save_json(snap_path, {
        "_note": "Last-seen register snapshot, auto-updated each run.",
        "vertical": vertical, "source": source, "fetched": lib.today(),
        "installer_ids": current_ids,
    })
    return signals


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_VERTICAL
    sig = collect(v)
    n = lib.append_signals(sig)
    print(f"[registers/{v}] {len(sig)} new-registration signals ({n} new to log)")
    for s in sig:
        print(f"  + {s['company']} — {s['headline']}")
