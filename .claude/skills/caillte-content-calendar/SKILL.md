---
name: caillte-content-calendar
description: >-
  Plan a week or month of CaillteAI Instagram/Facebook posts across the 6 content pillars
  with hooks, formats, and which engine to use. Use when the user says "plan this week",
  "what should I post", "build a content calendar", "fill the calendar", or wants a
  posting schedule.
---

# caillte-content-calendar — plan the week/month

Turns the strategy into a concrete, balanced schedule the user can execute in ~20 min/day.

## When to use
- "Plan this week's posts", "what do I post Mon–Fri", "give me next month's calendar".

## Method
1. Read `social/STRATEGY.md` (pillars, cadence, 70/20/10) and `social/content/
   calendar-30day.md` (the reference structure). Don't repeat what shipped recently —
   check the grid / last calendar.
2. Produce a table: **Day · Pillar · Working title · Format · Engine · Hook**.
   - Hold **1 reel/day**; 3–4 carousels/week; daily stories; mirror to FB.
   - Rotate all 6 pillars; keep 70 entertain/educate · 20 proof · 10 audit CTA.
   - Slot one **Office Heroes** episode + one "Watch it work" demo per week minimum.
3. For each row, draft the hook via the `caillte-hook-writer` patterns and name the
   engine: `caillte-carousel`, `caillte-demo-clip`, `caillte-static-post`, or (Phase 2)
   `caillte-ugc-video`.
4. End with the **repurposing map**: which 1 idea becomes a reel + 3 stories + an FB post.

## Defaults
- GROW mode: optimise for reach/saves; only soft audit CTA.
- If the user gives a theme/promo, weight the week toward it but keep pillar balance.
- Always leave Friday's slot flexible to ride whatever hit that week.

## Output
A clean Markdown table + a one-line "production order" (what to batch-make Sunday).
Offer to immediately generate the week's carousels (`caillte-carousel`) and hooks.
