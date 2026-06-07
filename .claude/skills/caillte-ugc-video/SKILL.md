---
name: caillte-ugc-video
description: >-
  Phase-2 (PAID) engine. Create AI-actor UGC video ads for CaillteAI via the vendored
  Arcads skill pack (Seedance/Sora/Veo/Kling + Nano Banana stills). Use only when the user
  explicitly wants AI-actor talking-head video and has an Arcads or Pletor key. For the
  free core engine use caillte-carousel / caillte-demo-clip instead.
---

# caillte-ugc-video — AI-actor UGC (Arcads, Phase 2, PAID)

A thin CaillteAI wrapper over the vendored **Arcads** pack at
`social/engines/arcads-pack/`. This is **paid** (Arcads API credits, or via Pletor). Do
not reach for it in default GROW mode — carousels + demos are free and carry the channel.
Use it when Dave specifically wants scalable AI-actor talking-head reels (e.g. a faceless
"trade owner" testifying about missed calls).

## Before doing anything
1. Confirm a key exists: `social/engines/arcads-pack/.env` with `ARCADS_BASIC_AUTH` (or
   `ARCADS_API_KEY`). If missing, **stop** and point the user to `social/engines/SETUP.md`
   — do not ask them to paste a key in chat unless they insist.
2. Read `social/engines/arcads-pack/MASTER_CONTEXT.md` (CaillteAI brand voice/defaults).

## How to use the underlying pack
The real skills live under the vendored pack — read and follow them:
- **Video / UGC:** `social/engines/arcads-pack/skills/arcads-external-api/SKILL.md`
  (decision tree → Seedance 2.0 UGC for selfie-style testimonials).
- **Static image ads:** `…/skills/nano-banana-image-ad/` and `…/chatgpt-image-ad/`.
- **Shared pipelines:** `…/shared/skills/` (caption-video, meta-ad-builder, etc.).

Drive those skills, but enforce the CaillteAI layer:

## CaillteAI overrides (apply on top of the pack)
- **Brief:** trade owner / missed-call scenario, UK/Irish idiom, the missed-call number,
  payoff to "never go caillte". Pull the script from `social/series/office-heroes.md`
  (formats 1, 2, 5) and the hook from `social/content/hooks.md`.
- **Look:** brand tokens from `social/BRAND.md`; burned-in captions; end card with green
  soundwave + audit CTA. Faceless brand, AI actor as the "everyman trade owner".
- **Honesty:** any AI-actor "testimonial" is a dramatisation, not a real customer — label
  it. Never imply a real person endorsed us.
- **Publishing:** the pack's `meta-ad-builder` creates **paused** Meta ads only. Keep it
  that way; Dave launches manually.

## Cost discipline
The pack logs costs to `arcads-pack/logs/arcads-api.jsonl` and estimates before each
generation — surface the estimate to Dave and get a yes before spending.
