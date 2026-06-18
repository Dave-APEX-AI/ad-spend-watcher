"""
Intent scoring engine.

Reads the append-only signal log, groups signals by company, and fuses them into
a single Intent Score (0–100) + Hot/Warm/Watch tier. The thesis the score
encodes: a company emitting MULTIPLE fresh signals (just hit a register AND
hiring AND ramping reviews) is far hotter than one emitting a single signal —
so signals STACK, with recency decay so stale signals fade.

Output: data/intent_companies.json — the dashboard-ready, ranked lead list.

Run:  python intent/intent_score.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
import lib  # noqa: E402

# Avatar palette per tier (matches the ad-spend-watcher dashboard look).
TIER_COLORS = {
    "Hot":   ("#E1F5EE", "#1D9E75"),
    "Warm":  ("#FBF1DF", "#BA7517"),
    "Watch": ("#EEEDE9", "#696860"),
}

TRIGGER_VERB = {
    "new_register": "Just hit the register",
    "planning": "New-site planning filed",
    "hiring": "Hiring",
    "advertising": "Already advertising",
    "review_velocity": "Reviews ramping",
}


def _effective(signal):
    age = lib.days_since(signal["detected_at"])
    return signal["strength"] * config.recency_multiplier(age)


def _initials(name):
    parts = [p for p in name.split() if p[:1].isalnum()]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][:1] + parts[1][:1]).upper()


def _suggested_action(name, vertical, top_signals):
    meta = config.vertical_meta(vertical)
    triggers = []
    for s in top_signals[:2]:
        triggers.append(s["headline"].lower())
    why = " and ".join(triggers) if triggers else "showing growth signals"
    hook = meta.get("grant_hook")
    angle = meta.get("sell_angle", "win more local enquiries")
    action = f"Reach out now: {name} is {why}. Lead with helping them {angle}."
    if hook:
        action += f" Tie it to: {hook}."
    return action


def build():
    signals = lib.load_signals()
    by_company = {}
    for s in signals:
        if config.is_chain(s["company"]):
            continue
        by_company.setdefault(s["company_id"], []).append(s)

    companies = []
    for cid, sigs in by_company.items():
        # one signal per (type) — keep the strongest/freshest of each type
        best_by_type = {}
        for s in sigs:
            t = s["signal_type"]
            if t not in best_by_type or _effective(s) > _effective(best_by_type[t]):
                best_by_type[t] = s
        kept = list(best_by_type.values())
        kept.sort(key=_effective, reverse=True)

        score = sum(_effective(s) for s in kept)
        vertical = kept[0]["vertical"]
        meta = config.vertical_meta(vertical)

        # grant-urgency boost: a grant-driven vertical with a freshly-qualified
        # firm is the most actionable lead there is.
        if vertical in config.VERTICALS and any(s["signal_type"] in ("new_register", "planning") for s in kept):
            score *= 1.12

        score = int(round(min(score, 100)))
        tier = config.tier_for(score)
        name = kept[0]["company"]

        # pull contact/location crumbs out of whichever signal carries them
        website = region = page_url = None
        for s in sigs:
            raw = s.get("raw", {})
            website = website or raw.get("website")
            region = region or raw.get("region")
            page_url = page_url or raw.get("page_url")

        bg, col = TIER_COLORS[tier]
        companies.append({
            "id": cid,
            "name": name,
            "vertical": vertical,
            "vertical_label": meta["label"],
            "country": kept[0].get("country", "UK"),
            "region_label": region or kept[0].get("country", "UK"),
            "website": website,
            "page_url": page_url,
            "intent_score": score,
            "tier": tier,
            "signal_types": sorted(best_by_type.keys()),
            "signal_count": len(kept),
            "top_triggers": [s["headline"] for s in kept[:3]],
            "signals": sorted(
                ({"type": s["signal_type"], "headline": s["headline"],
                  "detected_at": s["detected_at"], "evidence_url": s["evidence_url"],
                  "strength": round(_effective(s), 1)} for s in kept),
                key=lambda x: x["detected_at"], reverse=True),
            "grant_hook": meta.get("grant_hook", ""),
            "sell_angle": meta.get("sell_angle", ""),
            "suggested_action": _suggested_action(name, vertical, kept),
            "first_seen": min(s["detected_at"] for s in sigs),
            "last_signal": max(s["detected_at"] for s in sigs),
            "avatar": _initials(name),
            "avatarBg": bg,
            "avatarCol": col,
        })

    companies.sort(key=lambda c: c["intent_score"], reverse=True)

    summary = {
        "generated": lib.today(),
        "total": len(companies),
        "hot": sum(1 for c in companies if c["tier"] == "Hot"),
        "warm": sum(1 for c in companies if c["tier"] == "Warm"),
        "watch": sum(1 for c in companies if c["tier"] == "Watch"),
        "verticals": sorted({c["vertical"] for c in companies}),
    }
    out = {"summary": summary, "companies": companies}
    lib.save_json(lib.COMPANIES_OUT, out)
    return out


if __name__ == "__main__":
    out = build()
    s = out["summary"]
    print(f"[score] {s['total']} companies — {s['hot']} Hot / {s['warm']} Warm / {s['watch']} Watch")
    for c in out["companies"][:8]:
        print(f"  {c['intent_score']:>3} {c['tier']:<5} {c['name']}  [{', '.join(c['signal_types'])}]")
