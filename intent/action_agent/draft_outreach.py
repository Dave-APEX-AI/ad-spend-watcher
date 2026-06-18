"""
Actioning sub-agent — deterministic draft builder (leak model).

For every Hot (and optionally Warm) company, writes an outreach draft whose first
line names the EXACT leak we detected — missed-call reviews, slow DM replies, a
broken site they're paying ads into. Proof you noticed something real beats any
generic pitch. The lead offer is the AI voice receptionist + speed-to-lead.

Output: data/action_queue.json — ready for the VA to send or for the Claude
sub-agent (AGENT.md) to push into Gmail as a draft. Never auto-sends.

Run:  python intent/action_agent/draft_outreach.py [--include-warm]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
import lib  # noqa: E402

OPENER = {
    "missed_call_review": "a few of your Google reviews mention people couldn't get through on the phone",
    "slow_response": "I noticed enquiries on your Facebook/website can take a while to get a reply",
    "out_of_hours_gap": "I noticed calls that come in out-of-hours don't seem to get picked up",
    "hiring_receptionist": "I saw you're hiring front-desk staff to handle the phones",
    "website_leak": "I spotted your website isn't doing your ads justice (it's hard to use on mobile)",
    "new_location": "congratulations on the new location",
}


def _opener(c):
    for s in c["signals"]:
        if s["type"] in OPENER:
            return OPENER[s["type"]]
    return f"I've been following {c['name']}"


def _body(c):
    opener = _opener(c)
    offer = c["primary_offer"]
    if offer == config.OFFER_WEBSITE:
        pitch = ("We rebuild trade/clinic sites that actually convert mobile enquiries, "
                 "with instant speed-to-lead follow-up so no form sits unanswered.")
    elif offer == config.OFFER_LAUNCH:
        pitch = ("We get a new location booked up fast — local lead-gen plus an AI "
                 "receptionist so every call to the new site gets answered from day one.")
    else:
        pitch = ("We put an AI voice receptionist on your line — it answers every call "
                 "24/7, books jobs, and instantly follows up web/SMS/DM enquiries, so "
                 "you stop losing work to a missed call.")
    est = ("For a business your size that's typically several lost jobs a week — "
           "real money walking to whoever picks up first.\n\n")
    return (f"Hi {{first_name}},\n\n"
            f"I run a UK & Ireland agency that works with {c['vertical_label'].lower()}, "
            f"and {opener} — usually a sign good enquiries are slipping through.\n\n"
            f"{pitch}\n\n{est}"
            f"Worth a quick 10 minutes this week? Happy to show you exactly what "
            f"{c['name']} is missing and how we'd fix it.\n\nBest,\nDave\nApex Emerald AI / CaillteAI")


def _subject(c):
    if "missed_call_review" in c["signal_types"]:
        return f"You're losing calls, {c['name']} — quick fix"
    if "website_leak" in c["signal_types"] and c["primary_offer"] == config.OFFER_WEBSITE:
        return f"Your ads deserve a better website, {c['name']}"
    if "new_location" in c["signal_types"]:
        return f"Congrats on the new site — quick idea for {c['name']}"
    return f"Quick idea for {c['name']}"


def build(include_warm=False):
    data = lib.load_json(lib.COMPANIES_OUT, {"companies": []})
    tiers = {"Hot", "Warm"} if include_warm else {"Hot"}
    queue = []
    for c in data["companies"]:
        if c["tier"] not in tiers:
            continue
        queue.append({
            "company_id": c["id"], "name": c["name"], "tier": c["tier"],
            "intent_score": c["intent_score"], "vertical": c["vertical_label"],
            "country": c["country"], "employees": c.get("employees"),
            "locations": c.get("locations"), "offer": c["primary_offer"],
            "why_now": "; ".join(c["top_triggers"]),
            "leak_tags": c["leak_tags"],
            "website": c.get("website"), "phone": c.get("phone"),
            "facebook": c.get("facebook"),
            "to": "", "channel": "email",
            "subject": _subject(c), "body": _body(c),
            "suggested_action": c["suggested_action"], "status": "draft_pending",
        })
    out = {"generated": lib.today(), "count": len(queue), "items": queue}
    lib.save_json(lib.ACTION_QUEUE, out)
    return out


if __name__ == "__main__":
    out = build("--include-warm" in sys.argv)
    print(f"[action] {out['count']} outreach drafts queued -> {lib.ACTION_QUEUE}")
    for it in out["items"][:8]:
        print(f"  {it['tier']:<4} {it['name']:<30} {it['offer']:<28} | {it['why_now'][:55]}")
