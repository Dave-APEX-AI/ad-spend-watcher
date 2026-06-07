# Lead Magnet — The Missed-Call Audit

The **only** offer we push in GROW mode, and gently. It captures intent without breaking
the no-hard-sell rule, and gives every post a natural soft CTA.

## The promise

> "Find out what missed calls are *actually* costing your trade business — in 60 seconds,
> free, no call required."

## The asset

### v1 — The Calculator (BUILT & OWNED — `social/audit/index.html`) ✅
The existing page at `caillteai.com/challenges` shows a number but **captures nothing** —
every lead leaks. So we built our own capture-enabled version: `social/audit/index.html`,
backed by the free `worker/caillte-leads` Cloudflare Worker. Deploy steps in that worker's
README; once hosted, set `<AUDIT_URL>` to its address (bio link + every CTA below), and
point the old `/challenges` page's button at it (or replace it).

What it does:

**Inputs (4 sliders/fields):**
1. Average job value (£)
2. Calls you miss per day (honest guess)
3. Days worked per week
4. % of missed callers who'd have booked (default 30%)

**Output (instant, no email needed to *see* it):**
- "You're losing approx **£X,XXX/month** — about **£XX,XXX/year** — to missed calls."
- A breakdown bar (answered vs caillte/lost).
- Then the soft capture: *"Want the full breakdown + how to plug it? Drop your email / WhatsApp."*

> Maths: `lost_per_year = avg_job × missed_per_day × days_per_week × 50 × convert_%`.
> Show the working — trades owners trust numbers they can follow.

### v2 — The "Mystery Call" Audit (higher intent)
We ring their business line a few times (incl. after hours), record what happens, and
send a short report: how many rang out, time-to-answer, what a caller experiences.
Brutal, personal, converts. Manual now; semi-automate later.

## The capture mechanic (IG/FB native)

- **DM keyword:** "Comment or DM **CAILLTE** and I'll send your missed-call number."
  (Auto-DM tools exist; manual is fine at first — replies also boost the post.)
- **Link in bio:** → the calculator page.
- **Story:** the calculator as a sticker/poll ("How many calls do you reckon you miss a
  day?") → swipe up to the real number.

## Where it appears (soft, every time)

- Last slide of every carousel: *"Curious what it's costing you? Free audit in bio."*
- Pinned comment on every reel.
- End card of every Office Heroes episode.
- Bio link.

## Why this and not "book a demo"

In GROW mode a demo ask is too heavy for a cold trades audience. The audit is *valuable
on its own*, ungated to view, and self-qualifies: anyone who finishes it and sees a scary
number is pre-sold for the demo later. It feeds the list without feeling like selling.

## Going live (one-time setup)

1. **Deploy the lead Worker** — `worker/caillte-leads/README.md` (free, ~5 min). Get its
   URL, set `LEAD_ENDPOINT` in `social/audit/index.html`. (If skipped, the form falls back
   to a pre-filled email so leads still reach you.)
2. **Host the page** — either:
   - drop `social/audit/` onto caillteai.com (replace/redirect `/challenges`), or
   - serve it from this repo's GitHub Pages.
   Then set `<AUDIT_URL>` (in this file + `PROFILE.md`) to its address.
3. **Use it as the bio link** with tracking: `<AUDIT_URL>?utm_source=instagram`
   (`=facebook` on FB) so you see which posts drive audits.
4. **Built-in extras** (already supported by the page):
   - per-trade warm open: `?trade=plumber` tags the lead with their trade.
   - the DM keyword "CAILLTE" feeds the same list (manual send, or auto-DM later).
