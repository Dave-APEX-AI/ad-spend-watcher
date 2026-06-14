---
name: caillte-competitor-watch
description: >-
  Run CaillteAI's weekly competitor & trends scan — who in the trades / AI-receptionist
  niche is posting what, which formats/hooks are working, and 3 reactive content ideas to
  ride the trend this week. Use when the user says "competitor watch", "what are
  competitors doing", "weekly scan", "what's trending", or on a weekly (Friday) cadence.
---

# caillte-competitor-watch — weekly scan

A repeatable Friday ritual: scan the niche, spot what's working, and turn it into 3
reactive posts for next week. Free (web search + public profiles). Output is logged to
`social/content/competitor-reports/YYYY-MM-DD.md`.

## Honest scope
- We CAN track: what competitors publicly post (formats, hooks, cadence), visible signals
  (public like/comment/view counts where shown), and broad format trends via web search.
- We CANNOT (without paid scrapers / against ToS): pull competitors' private analytics or
  exact "traffic". So "what's doing well" = best-effort from public engagement + trend
  research, clearly labelled as observed vs inferred. Don't fabricate numbers.

## Watchlist
Read `social/content/competitors-watchlist.md` for the accounts + what to look for.

## Steps
1. **Scan** each watchlist account/tool (WebSearch + WebFetch their recent posts/reels).
   Note: formats used, hook styles, posting cadence, any visibly high-engagement post.
2. **Trends:** search current IG format/hook trends for trades/SMB/B2B (reels vs carousels,
   length, audio, new features being rewarded).
3. **Gaps:** angles nobody's covering that fit our missed-call / AI-receptionist wedge.
4. **React:** 3 content ideas for next week — each with format (carousel/reel/static), a
   one-line hook, and why it'll hit. Map each to a skill (caillte-carousel/reel/static).
5. **Log:** write the report to `social/content/competitor-reports/<date>.md`; offer to
   build the 3 ideas and queue them.

## Cadence / automation
- Run weekly (Fridays) — pair with `caillte-daily-snapshot`'s Friday review.
- To recur hands-off, the user can trigger via `/loop 7d caillte-competitor-watch` or a
  calendar reminder; this skill can't poll on its own (it needs to be invoked).
- The 3 reactive ideas should feed straight into the next week's queue.

## Output shape
```
# Competitor & trends — <date>
## Who's doing what  (account → formats/hooks → what's working)
## Format & hook trends this week
## Gaps & opportunities for CaillteAI
## 3 reactive ideas (format · hook · why) → next week's queue
```
