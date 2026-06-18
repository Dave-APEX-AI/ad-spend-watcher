"""
Collector: INBOUND-LEAK signals — the core of the speed-to-lead / AI-receptionist
play. Detects established firms losing enquiries because nobody answers fast.

Free sources (live, on Dave's Mac):
  * Google / Trustpilot / Facebook REVIEW TEXT — mined for "no one answered",
    "never called back", "couldn't get through", "left a voicemail" etc. This is
    the single most qualified missed-call signal that exists, and it's public.
  * Facebook page RESPONSIVENESS badge ("Typically replies within a day") — a
    free, per-business read on how slow they are on DMs.
  * Google Business Profile HOURS vs an urgent/emergency service = out-of-hours gap.
  * A live "receptionist / call handler / service advisor" job ad = they already
    feel the pain (warm for an AI receptionist as the cheaper, 24/7 alternative).

Seed mode reads the observed fields from data/roster.json. Live mode replaces
those via the Chrome MCP (reviews/FB are JS-driven and 429 bare HTTP clients —
see CLAUDE.md 'Chrome verification' override).

Run:  python intent/collectors/collect_inbound.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

# phrases we scan review text for (the live miner uses these; the seed roster
# pre-counts them into missed_call_reviews)
MISSED_CALL_PHRASES = [
    "no one answered", "no answer", "never called back", "no callback",
    "couldn't get through", "could not get through", "phone rang out",
    "left a voicemail", "rings out", "impossible to get through",
    "never got back", "went to voicemail", "no response", "phone always busy",
]
SLOW_FB = {"within a day", "days", "within a few days"}


def collect():
    signals = []
    for c in lib.load_roster():
        name = c["name"]
        if config.is_chain(name):
            continue
        v = c["vertical"]
        country = c.get("country", "UK")

        # 1) missed-call review mining
        mcr = c.get("missed_call_reviews", 0)
        if mcr >= 2:
            quotes = c.get("review_quotes", [])
            strength = min(config.SIGNAL_WEIGHTS["missed_call_review"],
                           config.SIGNAL_WEIGHTS["missed_call_review"] * (0.5 + mcr / 12))
            evid = quotes[0] if quotes else ""
            signals.append(lib.signal(
                name, v, "missed_call_review", strength=round(strength, 1),
                headline=f"{mcr} reviews mention unanswered calls / no callback",
                evidence_url=c.get("website", ""), country=country,
                raw={"count": mcr, "quote": evid}))

        # 2) slow channel response (FB reply speed)
        if (c.get("fb_reply_speed") or "").lower() in SLOW_FB:
            signals.append(lib.signal(
                name, v, "slow_response",
                strength=config.SIGNAL_WEIGHTS["slow_response"],
                headline=f"Facebook shows a slow DM reply time ('{c['fb_reply_speed']}')",
                evidence_url=f"https://facebook.com/{c.get('facebook','')}", country=country,
                raw={"fb_reply_speed": c["fb_reply_speed"]}))

        # 3) out-of-hours gap on an urgent service
        if c.get("out_of_hours_gap"):
            signals.append(lib.signal(
                name, v, "out_of_hours_gap",
                strength=config.SIGNAL_WEIGHTS["out_of_hours_gap"],
                headline="Urgent enquiries arrive out-of-hours but the line isn't covered",
                country=country, raw={}))

        # 4) hiring a receptionist / call handler = feels the pain
        if c.get("hiring_receptionist"):
            roles = ", ".join(config.vertical_meta(v).get("receptionist_roles", [])[:2])
            signals.append(lib.signal(
                name, v, "hiring_receptionist",
                strength=config.SIGNAL_WEIGHTS["hiring_receptionist"],
                headline=f"Advertising for front-desk staff ({roles}) — paying to answer the phone",
                country=country, raw={"roles": roles}))

        # 5) review velocity (activity/throughput proxy)
        delta = c.get("reviews_now", 0) - c.get("reviews_prev", 0)
        if delta >= 8:
            signals.append(lib.signal(
                name, v, "review_velocity",
                strength=min(config.SIGNAL_WEIGHTS["review_velocity"],
                             config.SIGNAL_WEIGHTS["review_velocity"] * delta / 20),
                headline=f"+{delta} reviews in 30 days — high throughput", country=country,
                raw={"delta": delta, "reviews_now": c.get("reviews_now")}))
    return signals


if __name__ == "__main__":
    sig = collect()
    n = lib.append_signals(sig)
    print(f"[inbound] {len(sig)} inbound-leak signals ({n} new to log)")
