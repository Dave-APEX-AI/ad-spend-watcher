"""
Collector: WEBSITE-LEAK + ad-budget signals.

A bad/missing website is a public, free-to-detect pain — and it's most valuable
when crossed with "currently advertising", because then they're paying for clicks
that bounce. Free checks (all scriptable on Dave's Mac):
  * no website link on the Google Business Profile -> 'none'
  * only a Facebook page as web presence            -> 'facebook_only'
  * missing <meta viewport> (not mobile-responsive) -> 'not_mobile'
  * no HTTPS / expired certificate                   -> 'no_ssl'
  * Google PageSpeed Insights API (FREE) score < 50  -> 'slow'

Seed mode reads website_status + advertising from the roster; live mode fills
website_status from the checks above and PageSpeed.

Run:  python intent/collectors/collect_web.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

WEB_ISSUE = {
    "none": "No website at all — established firm with zero web presence",
    "facebook_only": "Only a Facebook page — no real website",
    "not_mobile": "Website isn't mobile-friendly — most enquiries bounce on phones",
    "no_ssl": "No HTTPS / 'not secure' warning — Google demotes it, buyers distrust it",
    "slow": "Very slow site (PageSpeed < 50) — losing enquiries to load time",
}


def collect():
    signals = []
    for c in lib.load_roster():
        name = c["name"]
        if config.is_chain(name):
            continue
        v, country = c["vertical"], c.get("country", "UK")
        status = c.get("website_status", "ok")
        advertising = c.get("advertising", False)

        if status in WEB_ISSUE:
            # the leak is worse (and the pitch sharper) if they're paying for traffic
            base = config.SIGNAL_WEIGHTS["website_leak"]
            strength = base * (1.0 if advertising else 0.7)
            head = WEB_ISSUE[status]
            if advertising:
                head += " — and they're paying for ads into it"
            signals.append(lib.signal(
                name, v, "website_leak", strength=round(strength, 1),
                headline=head, evidence_url=c.get("website", ""), country=country,
                raw={"website_status": status, "advertising": advertising}))

        if advertising:
            signals.append(lib.signal(
                name, v, "ads_active", strength=config.SIGNAL_WEIGHTS["ads_active"],
                headline="Currently running paid ads — has budget and is buying inbound",
                evidence_url="https://www.facebook.com/ads/library/", country=country,
                raw={}))
    return signals


if __name__ == "__main__":
    sig = collect()
    n = lib.append_signals(sig)
    print(f"[web] {len(sig)} website/ad signals ({n} new to log)")
