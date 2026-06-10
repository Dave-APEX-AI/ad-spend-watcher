---
name: caillte-daily-snapshot
description: >-
  Produce CaillteAI's daily social brief — what to post today, plus a place to log
  yesterday's numbers (reach, saves, follows, audit completions) so we steer on data. Use
  when the user says "daily snapshot", "what's today's post", "log yesterday", or wants a
  morning social check-in. Good for a scheduled/recurring task.
---

# caillte-daily-snapshot — the morning driver

A 5-minute daily ritual: confirm today's post, capture yesterday's signal, flag what to
double down on. Designed to be run on a schedule (e.g. each morning).

## What it does
1. **Today's post** — read the active calendar (`social/content/calendar-30day.md` or the
   latest from `caillte-content-calendar`); state today's pillar, title, format, engine,
   and the hook. If the asset isn't made yet, offer to make it now (carousel/static/demo).
2. **Yesterday's numbers** — prompt for / append to a simple log (create
   `social/content/metrics.csv` if absent) with columns:
   `date,post,pillar,format,reach,saves,shares,profile_visits,follows,comments,audit_completions`.
3. **Steer** — compare to the leading indicators in `social/STRATEGY.md` (hold rate,
   saves, shares, profile→follow). Call out the best performer and recommend a
   double-down (recut the winner, make a sibling post) for tomorrow.
4. **Engagement reminder** — reply to comments in the first 60 min; pin the audit CTA.

## Output (keep it tight)
```
📅 TODAY  — <pillar> · <title> · <format> · <engine>
   Hook: "<hook>"   | asset: ready / make now?
📊 YESTERDAY — reach X · saves Y · follows +Z · audits N
   🔥 winner: <post> (why)  → double-down: <suggestion>
✅ do now: post today's reel · reply to comments · log numbers
```

## Notes
- GROW mode: celebrate reach/saves/follows, not vanity likes.
- Weekly (Fridays): summarise the week, prune losing formats, set next week's emphasis.
