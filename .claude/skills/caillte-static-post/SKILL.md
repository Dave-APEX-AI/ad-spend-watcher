---
name: caillte-static-post
description: >-
  Produce a single on-brand CaillteAI static image post (hero graphic / quote / banter)
  plus caption + hashtags, designed for Holo (free, single-image) or any image tool. Use
  when the user wants "a static post", "a quote graphic", "a single image", or a pillar-4
  banter post. For multi-slide carousels use caillte-carousel instead.
---

# caillte-static-post — single hero static (Holo-ready)

Holo (free tier) makes one static image at a time. This skill produces the **brief +
copy** so Holo (or any tool) outputs an on-brand 1080×1350 / 1080×1920 graphic, plus the
caption and hashtags. It does not call an API — it specs the asset.

## When to use
- A quote graphic, a single stat, a banter line, an "Office Hero of the Week" card.
- Anything that's one image, not a swipe (→ that's `caillte-carousel`).

## Output (always produce all four)
1. **Design brief for Holo** — exact layout using the brand tokens:
   - Background `--ink` (#0A0F0D) or `--cream`; headline in heavy geometric sans;
     one green call-dot or amber missed-dot; soundwave motif; `@caillte_ai` bottom-left.
   - Big number/word as the focal point. Captions/contrast mobile-first.
2. **Headline text** (the on-image words) — pulled/adapted from `social/content/hooks.md`.
3. **Caption** — hook first line (before the fold), 1–3 short value lines, 1 soft CTA
   ("Free missed-call audit — link in bio"), in CaillteAI voice (see `social/BRAND.md`).
4. **Hashtags** — 3–5 specific (niche + geo + pain), rotated.

## Holo prompt pattern
> "1080×1350 poster. Near-black (#0A0F0D) background. Bold white geometric sans headline:
> '<HEADLINE>'. One glowing emerald (#0FB97E) dot top-left as a call signal. Small
> '@caillte_ai' bottom-left in muted grey. Minimal, high-contrast, no stock photos."

Swap `#0FB97E`→`#FFC247` and "call signal"→"missed-call alert" for pain/banter posts.

## Brand guardrails
Trade-native or bin it. One emoji max. Number > adjective. Never generic-AI-agency. Keep
the green-dot / amber-dot / soundwave visual system consistent across every static.
