---
name: caillte-weekly-drop
description: >-
  The weekly content engine — run the competitor/trend scan, pivot to what's relevant THIS
  week, then create and queue the week's posts (2/day) from those findings. Use when the
  user says "weekly drop", "make this week's content", "do the weekly", or on a Friday
  cadence. This is the operating loop: scan → plan → produce → queue.
---

# caillte-weekly-drop — scan-driven weekly content

The whole point: content is **freshest and most relevant** because each week's posts are
built FROM that week's scan, not from a stale batch. One closed loop, triggered weekly.

## The loop (run in order)

### 1. SCAN — what's relevant this week
Run `caillte-competitor-watch` (watchlist in `social/content/competitors-watchlist.md`).
Output: who's doing what, format/hook trends, gaps, and **3 reactive ideas**. Save the
report to `social/content/competitor-reports/<date>.md`.

### 2. PIVOT — turn findings into this week's plan
From the scan, decide the week (14 posts at 2/day):
- **Format mix** weighted by what's winning that week (e.g. scan says reels for reach +
  carousels for saves → ~4 reels, ~7 carousels, ~3 statics).
- **Hooks/angles**: adopt the hooks/trends the scan surfaced; drop anything that's gone
  stale. Localise (UK/IE £/€) and react to specific competitor gaps.
- **3 trade stories** (the social-proof pillar): rotate trades NOT used recently
  (`social/content/customer-stories.md` bank), anonymised + qualitative.
- **The other ~11**: the 3 reactive ideas + fresh pattern-breakers (`pattern-breakers.md`)
  shaped by the findings.
Write the plan to `social/content/weekly-plans/<date>.md` (Day · slot · type · hook · engine).

### 3. PRODUCE — build the assets
Render with `caillte-carousel` / `caillte-reel` / `caillte-static`; caption in brand voice
(`caillte-hook-writer`) using this week's hooks. Stories via `caillte-customer-story`.

### 4. QUEUE — stage + weave + ship
`stage.py` each asset (build job + public URL); weave so each day = 1 story-ish + 1 other,
interleave against the live `.posted`; append to `queue/schedule.json`; commit + push to
`main`. The auto-publisher posts 2/day (09:00 + 18:00 UTC).

### 5. REVIEW — steer next week
Glance at `caillte-daily-snapshot` numbers from last week; double down on what hit, cut what
didn't. Feed that into next week's pivot.

### 6. EMAIL Dave — confirm / flag
At the end of every drop (and any significant step), email hello@caillteai.com via the
`caillte-notify` workflow:
- ✅ **Done & good** — "Weekly Drop done", the 3 findings that shaped it, what was queued.
- ❓ **Needs input** — anything blocked on Dave (e.g. confirm a customer result, a decision).
- 🚨 **Problem** — failures from the publisher are emailed automatically (caillte-publish.yml
  failure step); flag anything else here.
Dispatch: Actions → caillte-notify → subject + message (or trigger via MCP). Requires the
`WEB3FORMS_KEY` secret (one-time). GitHub's native failed-workflow email is a free backstop.

## Cadence & honesty
- **Triggered, not autonomous** — the scan needs live web research, so this runs when
  invoked (say "weekly drop"). It can't self-run unattended in this environment.
- **Keep ~1 week buffered** so a missed trigger never goes dark. Check queue depth first
  (`schedule.json` minus `.posted`); only produce what's needed to refill to ~1 week ahead.
- Don't over-batch a static month — that defeats "freshest". Produce a week, ship, re-scan.

## Output to the user
A short summary: this week's 3 findings that shaped it, the 14 posts (type + hook), and the
new queue depth. Then end.
