---
name: caillte-hook-writer
description: >-
  Generate and grade scroll-stopping CaillteAI hooks / captions / first-lines in brand
  voice (trades, UK & Ireland, missed-call pain). Use when the user wants "hooks", "a
  caption", "openers", "first lines", "make this post hit", or needs to improve a reel's
  opening 1.5 seconds.
---

# caillte-hook-writer — hooks & captions in CaillteAI voice

The hook is 90% of the post. This skill writes openers that make a stressed trade owner
stop scrolling, and grades them before they ship.

## Inputs to ask for (or infer)
- Pillar (1 horror / 2 maths / 3 demo / 4 banter / 5 how-to / 6 Office Heroes).
- The specific scenario or number (trade, job value, time of day, what was lost).
- Format (reel opener / carousel slide-1 / caption first-line).

## Method
1. Pull the matching pattern from `social/content/hooks.md` ("Hook formulas").
2. Generate **5–8 variants**. Each must contain a pattern interrupt **and** a number or a
   visceral pain, in <12 words where possible, sound-off-readable.
3. Grade each /10 on: **Stop power** (would a plumber freeze mid-scroll?), **Specificity**
   (real trade detail/number?), **Brand fit** (voice, no guru/hype, ≤1 emoji), **CTA-able**
   (does it set up the audit?). Ship only 8+/10.
4. Return the winner + 2 alternates, plus the full caption (hook → value → 1 soft CTA) and
   3–5 hashtags.

## Voice rules (from social/BRAND.md)
- Plain, confident, a bit cheeky. Site-foreman, not SaaS.
- Numbers over adjectives. Trade idiom welcome ("up a ladder", "ringing round").
- Never: hype ("🚀 game-changer"), fake urgency, guru platitudes, jargon (LLM/agentic).
- The word *caillte* ("lost") is a recurring weapon — use it.

## Quick grader (paste any hook)
> Score Stop/Specificity/Brand/CTA each 0–10, total /40, verdict SHIP (≥32) or REWRITE,
> then give the fixed version.
