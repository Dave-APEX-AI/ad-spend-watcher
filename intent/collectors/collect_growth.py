"""
Collector: EXPANSION signals — the multi-location "jackpot".

An established operator opening another site is launching blind: new number,
new web traffic, new reviews to seed — and they have budget. Free to detect:
  * a new Google Business Profile listing under the same brand
  * "now open in <town>" / "new branch" posts on their site or Facebook
  * job ads at a new postcode, or multiple simultaneous roles across sites

Seed mode reads new_location + open_roles from the roster. Live mode diffs the
brand's Google-listing count week-over-week and scans careers pages.

Run:  python intent/collectors/collect_growth.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402


def collect():
    signals = []
    for c in lib.load_roster():
        name = c["name"]
        if config.is_chain(name):
            continue
        v, country = c["vertical"], c.get("country", "UK")

        if c.get("new_location"):
            signals.append(lib.signal(
                name, v, "new_location", strength=config.SIGNAL_WEIGHTS["new_location"],
                headline=f"Expanding — {c['new_location']}", country=country,
                raw={"detail": c["new_location"], "locations": c.get("locations")}))

        # broad multi-role hiring (excluding the receptionist signal handled in
        # collect_inbound) = scaling capacity
        roles = c.get("open_roles", 0)
        if roles >= 3:
            signals.append(lib.signal(
                name, v, "expansion_hiring", strength=config.SIGNAL_WEIGHTS["expansion_hiring"],
                headline=f"{roles} open roles — actively scaling", country=country,
                raw={"open_roles": roles}))
    return signals


if __name__ == "__main__":
    sig = collect()
    n = lib.append_signals(sig)
    print(f"[growth] {len(sig)} expansion signals ({n} new to log)")
