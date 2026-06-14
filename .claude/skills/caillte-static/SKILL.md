---
name: caillte-static
description: >-
  Generate a single on-brand CaillteAI static image (1080x1350 or 1080x1080 PNG) for free
  via the Chromium render engine — ready to post, no Holo/Canva needed. Use when the user
  wants "a static", "a single image", "a quote/banter graphic", or "one image post". For
  multi-slide use caillte-carousel; for video use caillte-reel.
---

# caillte-static — free single-image posts

A static is a one-card render. It reuses the carousel engine + brand template, so it's the
same £0 pipeline that already publishes your carousels — just one slide.

## Run
Write a 1-slide spec (see `examples/down-the-ladder.json`) and render with the carousel
renderer:
```
CHROME_BIN=/opt/pw-browsers/.../chrome \
  python3 .claude/skills/caillte-carousel/render.py <spec>.json --out social/out
```
→ `social/out/<name>/slide_01.png` is your static.

## Slide types (pick one)
`cover` (kicker + big headline + body — the workhorse), `stat` (one huge number),
`quote` (punchy line), `point` (numbered). Inline `<span class='hl'>`/`<span class='hl-amber'>`
to colour-pop. Amber = loss/missed, green = win/answered.

## Best static formats for CaillteAI
- **Banter/POV** (pillar 4): "POV: down the ladder — 3 missed calls and a voicemail."
- **One big stat**: "£35k a year — gone to missed calls."
- **Brand line**: "Caillte means lost. We make sure you're not."
- **Office Hero of the Week** card (recurring ritual).

## Publish
Queue as an **image** job: `{ "type":"image", "caption":"...", "image_urls":["<raw url>"],
"cross_post_facebook":true }`. Use `social/publish/stage.py --name <name>` to copy the PNG
into the queue and build the job, add to `schedule.json`, push to main → auto-posts to
IG + FB.

## Square option
For a 1:1 (1080x1080) static, render then center-crop, or add a square template variant on
request. 4:5 (1080x1350) is the default — it takes more feed real estate.
