"""
Intent scoring engine (leak model).

Joins firmographics (data/roster.json) with observed signals (signals.jsonl),
applies the qualification gate (10+ staff or multi-site; no chains, no 1–3
person shops), then scores each qualifying company on how much inbound revenue
it's leaking — and routes it to the right offer (led by AI receptionist +
speed-to-lead).

Output: data/intent_companies.json (dashboard-ready, ranked).

Run:  python intent/intent_score.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import lib  # noqa: E402

TIER_COLORS = {
    "Hot":   ("#FDECEC", "#C0392B"),   # red — bleeding money now
    "Warm":  ("#FBF1DF", "#BA7517"),
    "Watch": ("#EEEDE9", "#696860"),
}

LEAK_LABEL = {
    "missed_call_review": "Missing calls",
    "slow_response": "Slow on DMs/forms",
    "out_of_hours_gap": "No out-of-hours cover",
    "hiring_receptionist": "Hiring to answer phones",
    "website_leak": "Broken/no website",
    "new_location": "Opening a new site",
    "expansion_hiring": "Scaling up",
    "ads_active": "Paying for ads",
    "review_velocity": "High throughput",
}


def _effective(s):
    return s["strength"] * config.recency_multiplier(lib.days_since(s["detected_at"]))


def _initials(name):
    parts = [p for p in name.split() if p[:1].isalnum()]
    if not parts:
        return "??"
    return (parts[0][:2] if len(parts) == 1 else parts[0][:1] + parts[1][:1]).upper()


def _signals_by_company():
    out = {}
    for s in lib.load_signals():
        out.setdefault(s["company_id"], {})
        t = s["signal_type"]
        cur = out[s["company_id"]].get(t)
        if cur is None or _effective(s) > _effective(cur):
            out[s["company_id"]][t] = s   # keep strongest of each type
    return out


def _suggested_action(c, kept):
    meta = config.vertical_meta(c["vertical"])
    leaks = [LEAK_LABEL[s["signal_type"]] for s in kept
             if s["signal_type"] in config.INBOUND_SIGNALS or s["signal_type"] == "website_leak"]
    leaks = list(dict.fromkeys(leaks))[:3]
    leak_str = ", ".join(leaks).lower() if leaks else "leaking inbound enquiries"
    offer = c["primary_offer"]
    return (f"{c['name']} ({c.get('employees','?')} staff"
            + (f", {c['locations']} sites" if c.get("locations", 1) > 1 else "")
            + f") is {leak_str}. Lead with {offer}. Angle: {meta['hook']}.")


def build():
    roster = lib.load_roster()
    sigs = _signals_by_company()

    companies, disqualified = [], 0
    for c in roster:
        if not config.qualifies(c):
            disqualified += 1
            continue
        cid = lib.slugify(c["name"])
        kept = list(sigs.get(cid, {}).values())
        if not kept:
            continue
        kept.sort(key=_effective, reverse=True)

        # Diminishing returns: the single biggest leak dominates, each extra leak
        # adds less. Keeps the strongest signal meaningful and spreads the ranking
        # instead of pinning every multi-leak firm at 100.
        DIMINISH = [1.0, 0.7, 0.5, 0.35]
        score = sum((DIMINISH[i] if i < len(DIMINISH) else 0.2) * _effective(s)
                    for i, s in enumerate(kept))
        score = int(round(min(score, 100)))
        tier = config.tier_for(score)
        signal_types = [s["signal_type"] for s in kept]
        offer = config.primary_offer(signal_types)
        meta = config.vertical_meta(c["vertical"])
        bg, col = TIER_COLORS[tier]

        offers = []
        if set(signal_types) & config.INBOUND_SIGNALS:
            offers.append(config.OFFER_RECEPTIONIST)
        if "website_leak" in signal_types:
            offers.append(config.OFFER_WEBSITE)
        if "new_location" in signal_types:
            offers.append(config.OFFER_LAUNCH)

        rec = {
            "id": cid,
            "name": c["name"],
            "vertical": c["vertical"],
            "vertical_label": meta["label"],
            "country": c.get("country", "UK"),
            "region": c.get("region", ""),
            "employees": c.get("employees"),
            "locations": c.get("locations", 1),
            "website": c.get("website"),
            "website_status": c.get("website_status"),
            "facebook": c.get("facebook"),
            "phone": c.get("phone"),
            "advertising": c.get("advertising", False),
            "rating": c.get("rating"),
            "reviews_now": c.get("reviews_now"),
            "intent_score": score,
            "tier": tier,
            "primary_offer": offer,
            "offers": offers or [offer],
            "leak_tags": list(dict.fromkeys(LEAK_LABEL[t] for t in signal_types)),
            "signal_types": signal_types,
            "top_triggers": [s["headline"] for s in kept[:3]],
            "signals": [{"type": s["signal_type"], "headline": s["headline"],
                         "detected_at": s["detected_at"], "evidence": s.get("evidence_url", ""),
                         "weight": round(_effective(s), 1),
                         "quote": s.get("raw", {}).get("quote", "")} for s in kept],
            "hook": meta["hook"],
            "avatar": _initials(c["name"]), "avatarBg": bg, "avatarCol": col,
        }
        rec["suggested_action"] = _suggested_action(rec, kept)
        companies.append(rec)

    companies.sort(key=lambda x: x["intent_score"], reverse=True)
    summary = {
        "generated": lib.today(),
        "qualified": len(companies),
        "disqualified": disqualified,
        "hot": sum(1 for c in companies if c["tier"] == "Hot"),
        "warm": sum(1 for c in companies if c["tier"] == "Warm"),
        "watch": sum(1 for c in companies if c["tier"] == "Watch"),
        "by_offer": {o: sum(1 for c in companies if c["primary_offer"] == o)
                     for o in [config.OFFER_RECEPTIONIST, config.OFFER_WEBSITE, config.OFFER_LAUNCH]},
        "verticals": sorted({c["vertical"] for c in companies}),
    }
    out = {"summary": summary, "companies": companies}
    lib.save_json(lib.COMPANIES_OUT, out)
    return out


if __name__ == "__main__":
    out = build()
    s = out["summary"]
    print(f"[score] {s['qualified']} qualified ({s['disqualified']} disqualified) — "
          f"{s['hot']} Hot / {s['warm']} Warm / {s['watch']} Watch")
    for c in out["companies"][:10]:
        print(f"  {c['intent_score']:>3} {c['tier']:<5} {c['name']:<32} "
              f"{c['primary_offer']:<28} [{', '.join(c['leak_tags'][:3])}]")
