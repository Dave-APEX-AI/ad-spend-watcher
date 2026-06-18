"""
Intent Engine — weekly entry point.

Runs every collector, rescoring, and the draft builder in order, then prints a
summary. Designed to slot next to scripts/weekly_runner.py on Dave's Mac (or run
from Claude Code on the web). Collectors degrade gracefully to the seed roster
when a live source 403s / a key is missing, so this always produces a dashboard.

    python intent/run.py [--include-warm]
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "collectors"))
import lib  # noqa: E402
import intent_score  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "action_agent"))
import draft_outreach  # noqa: E402

COLLECTORS = ["collect_inbound", "collect_web", "collect_growth"]


def main(include_warm=False):
    print("── Intent Engine weekly run ───────────────────────────────")
    total = 0
    for modname in COLLECTORS:
        mod = importlib.import_module(modname)
        sigs = mod.collect()
        added = lib.append_signals(sigs)
        total += added
        print(f"  {modname:<18} {len(sigs):>3} signals ({added} new)")
    print(f"  → {total} new signals logged\n")

    out = intent_score.build()
    s = out["summary"]
    print(f"  Scored: {s['qualified']} qualified, {s['disqualified']} disqualified")
    print(f"  Tiers : {s['hot']} Hot / {s['warm']} Warm / {s['watch']} Watch")
    print(f"  Offers: {s['by_offer']}\n")

    q = draft_outreach.build(include_warm)
    print(f"  Drafted {q['count']} outreach messages for {'Hot+Warm' if include_warm else 'Hot'} leads")
    print("───────────────────────────────────────────────────────────")
    print("  Dashboard data: intent/data/intent_companies.json")
    print("  Action queue  : intent/data/action_queue.json")
    return out


if __name__ == "__main__":
    main("--include-warm" in sys.argv)
