---
name: caillte-carousel
description: >-
  Generate on-brand CaillteAI Instagram/Facebook carousels (multi-slide 1080x1350
  PNGs) for free, with no subscription, using local headless Chrome. Use when the
  user wants to "make a carousel", "create slides", "the missed-call maths post", a
  "swipe post", or any multi-image CaillteAI social graphic. The free alternative to
  Holo (which only does single images) and to paid tools like Canva/Pletor.
---

# caillte-carousel — free multi-slide carousel generator

Renders branded carousels to PNG with whatever Chromium/Chrome is installed. £0, no
account, no credits. Brand tokens live in `templates/carousel.html` (`:root` block) —
the single source of truth for colours/type; edit once, every slide updates.

## When to use
- "Make a carousel about the missed-call maths"
- "Turn these 5 points into slides"
- Any pillar-2 (maths) or pillar-5 (how-to) post, or an Office Heroes static episode.

## How to run
1. Write a spec JSON (see `examples/maths.json`). Pick slide types per slide.
2. `python3 render.py spec.json --out OUTDIR`
3. PNGs land in `OUTDIR/<name>/slide_01.png …` — post in order.

Needs Chrome/Chromium on PATH (or set `CHROME_BIN`). On Dave's Mac that's already
present. If missing: `brew install chromium` (mac) / `apt-get install -y chromium` (Linux).

## Slide types (set `"type"`)
| type | fields | use |
|------|--------|-----|
| `cover` | `kicker`, `headline`, `body`, `theme` | slide 1, the hook |
| `point` | `index`, `headline`, `body` | a numbered point |
| `stat` | `value`, `label`, `body`, `win`(bool), `amberDot`(bool) | one big number |
| `quote` | `headline` | a punchy line |
| `cta` | `headline`, `body`, `save` | last slide — the audit CTA |

Common fields: `theme` ("dark" default / "light"), `page` (auto-numbered if omitted).
Inline HTML allowed in text: wrap key words in `<span class='hl'>…</span>` (green) or
`<span class='hl-amber'>…</span>` (amber) to colour-pop the number that hurts.

## Brand rules baked in
- 1080×1350 (4:5), ink/emerald/cream/amber palette, big numbers as design.
- Slide 1 must be screenshot-worthy on its own. Last slide = soft audit CTA + "save this".
- Amber = loss/missed; green = win/answered. Keep one idea per slide.

## Recipe: the workhorse "maths" carousel
Use `examples/maths.json` as a template — cover hook → stat → point → big amber stat →
quote → CTA. Swap the numbers, keep the structure. Then caption with a pillar-2 hook
from `social/content/hooks.md` and 3–5 specific hashtags.

## After rendering
Hand the PNG paths back to the user, plus: a caption (hook first line + value + 1 CTA),
3–5 hashtags, and a reminder to also recut the slides as a reel (repurposing rule).
