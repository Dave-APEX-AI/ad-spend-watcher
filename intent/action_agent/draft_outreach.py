"""
Actioning sub-agent — deterministic draft builder.

Reads the scored lead list and, for every Hot (and optionally Warm) company,
writes a personalised outreach draft that NAMES THE SIGNAL that triggered it —
the whole point of intent-based outreach is that the first line proves you
noticed something real ("saw you just hit the MCS register and you're hiring
two engineers"), not a generic blast.

Output: data/action_queue.json — each item ready for the VA to review and send,
or for the Claude sub-agent (see AGENT.md) to push into Gmail as a draft via the
Gmail MCP. Nothing is auto-sent.

Run:  python intent/action_agent/draft_outreach.py [--include-warm]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib  # noqa: E402

SIGNAL_PHRASE = {
    "new_register": "I saw you've just come onto the {reg} register",
    "hiring": "I noticed you're hiring",
    "advertising": "I can see you're already running ads",
    "review_velocity": "your Google reviews have been climbing fast",
    "planning": "I spotted your new-site planning application",
}


def _opening_line(company):
    bits = []
    for s in company["signals"][:2]:
        t = s["type"]
        if t == "new_register":
            reg = "MCS" if company["vertical"] == "heat_pump" else "your trade"
            bits.append(SIGNAL_PHRASE[t].format(reg=reg))
        elif t in SIGNAL_PHRASE:
            bits.append(SIGNAL_PHRASE[t])
    if not bits:
        return f"I've been following {company['name']} locally"
    if len(bits) == 1:
        return bits[0].capitalize()
    return (bits[0] + ", and " + bits[1]).capitalize()


def _body(company):
    opener = _opening_line(company)
    angle = company.get("sell_angle") or "win more local enquiries"
    hook = company.get("grant_hook")
    hook_line = f"\n\nWith {hook}, the firms moving first are the ones filling their pipeline — that's exactly what we help with." if hook else ""
    return (
        f"Hi {{first_name}},\n\n"
        f"{opener} — usually a sign a business is growing.\n\n"
        f"I run a small UK & Ireland agency that helps {company['vertical_label'].lower()} "
        f"{angle}. We work on results, not retainers, and everything's set up so you "
        f"get the enquiries without lifting a finger.{hook_line}\n\n"
        f"Worth a quick 10-minute call this week? Happy to share exactly how we'd do it "
        f"for {company['name']}.\n\n"
        f"Best,\nDave\nApex Emerald AI"
    )


def _subject(company):
    top = company["signals"][0]["type"] if company["signals"] else ""
    if top == "new_register":
        return f"Congrats on the listing — quick idea for {company['name']}"
    if top == "hiring":
        return f"Saw you're hiring — quick idea for {company['name']}"
    return f"Quick idea for {company['name']}"


def build(include_warm=False):
    data = lib.load_json(lib.COMPANIES_OUT, {"companies": []})
    tiers = {"Hot", "Warm"} if include_warm else {"Hot"}
    queue = []
    for c in data["companies"]:
        if c["tier"] not in tiers:
            continue
        queue.append({
            "company_id": c["id"],
            "name": c["name"],
            "tier": c["tier"],
            "intent_score": c["intent_score"],
            "vertical": c["vertical_label"],
            "country": c["country"],
            "why_now": "; ".join(c["top_triggers"]),
            "evidence": [s["evidence_url"] for s in c["signals"] if s["evidence_url"]],
            "channel": "email",
            "to": "",  # VA / sub-agent fills from website contact page or FB About
            "website": c.get("website"),
            "subject": _subject(c),
            "body": _body(c),
            "suggested_action": c["suggested_action"],
            "status": "draft_pending",
        })
    out = {"generated": lib.today(), "count": len(queue), "items": queue}
    lib.save_json(lib.ACTION_QUEUE, out)
    return out


if __name__ == "__main__":
    include_warm = "--include-warm" in sys.argv
    out = build(include_warm)
    print(f"[action] {out['count']} outreach drafts queued -> {lib.ACTION_QUEUE}")
    for it in out["items"][:6]:
        print(f"  {it['tier']:<4} {it['name']} — {it['why_now'][:70]}")
