"""
Collector: REVIEW VELOCITY.

A sudden ramp in Google/Trustpilot reviews is a free proxy for throughput and an
active growth push (often a marketing campaign already running — i.e. they value
marketing). We track review COUNT week-over-week and fire a `review_velocity`
signal when the jump clears a threshold.

Live path on Dave's Mac: the Chrome MCP reads the Google Business Profile review
count per company (cookie-bearing, DOM-aware — Google 429s bare HTTP clients,
per the CLAUDE.md 'Chrome verification' override). Counts persist to
data/review_counts_<vertical>.json; this collector diffs them. With no live
counts it falls back to the bundled sample.

Run:  python intent/collectors/collect_reviews.py [vertical]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

VELOCITY_THRESHOLD = 5  # new reviews since last check to count as a signal


def collect(vertical=config.DEFAULT_VERTICAL):
    counts = lib.load_json(os.path.join(lib.DATA, f"review_counts_{vertical}.json"))
    if not counts:
        counts = lib.load_json(os.path.join(lib.DATA, f"sample_reviews_{vertical}.json"))
    if not counts:
        return []

    signals = []
    for row in counts.get("companies", []):
        name = row["company"]
        if config.is_chain(name):
            continue
        delta = row.get("reviews_now", 0) - row.get("reviews_prev", 0)
        if delta >= VELOCITY_THRESHOLD:
            # scale strength with the size of the jump, capped at the base weight
            strength = min(config.SIGNAL_WEIGHTS["review_velocity"],
                           config.SIGNAL_WEIGHTS["review_velocity"] * delta / 10)
            signals.append(lib.signal(
                name, vertical, "review_velocity",
                strength=round(strength, 1),
                headline=f"+{delta} Google reviews in the last 30 days (now {row.get('reviews_now')})",
                evidence_url=row.get("url", ""),
                country=row.get("country", "UK"),
                raw={"reviews_now": row.get("reviews_now"), "delta": delta,
                     "rating": row.get("rating")},
            ))
    return signals


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_VERTICAL
    sig = collect(v)
    n = lib.append_signals(sig)
    print(f"[reviews/{v}] {len(sig)} review-velocity signals ({n} new to log)")
    for s in sig:
        print(f"  + {s['company']} — {s['headline']}")
