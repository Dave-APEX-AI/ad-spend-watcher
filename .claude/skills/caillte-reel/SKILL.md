---
name: caillte-reel
description: >-
  Generate an on-brand CaillteAI Instagram/Facebook REEL (vertical 1080x1920 MP4) for
  free — no Arcads, no subscription. Chromium renders branded cards, ffmpeg stitches them
  with fades + slow zoom + a silent audio track. Use when the user wants "a reel", "a
  video", "turn this into a reel", a text-reel, hook reel, or number-counter reel. For
  static multi-image posts use caillte-carousel.
---

# caillte-reel — free vertical video/reels

Reels are the IG growth lever. This makes them with the same brand engine as carousels.
£0: Chromium (bundled) renders each card; ffmpeg (free `imageio-ffmpeg`) stitches the MP4.

## When to use
- Text/hook reels, the villain "I'm your missed call" reel, number-counter reels,
  carousel→reel conversions, Office Heroes episodes as video.

## Run
1. Write a spec (see `examples/im-your-missed-call-reel.json`): `name`, `fps` (30),
   `cards: [...]`. Each card = a carousel slide spec (`cover/point/stat/quote/cta`) **+
   `seconds`** (how long it's on screen).
2. `CHROME_BIN=/opt/pw-browsers/.../chrome python3 render_reel.py spec.json --out social/out`
   (locally) — or it auto-finds Chromium/ffmpeg.
3. Output: `social/out/<name>/<name>.mp4` (1080×1920, H.264, silent AAC track so the IG
   Reels API accepts it).

## Card fields
Same as `caillte-carousel` slide types, plus `seconds`. Inline `<span class='hl'>` (green)
/ `<span class='hl-amber'>` (amber) to colour-pop. Keep 4–7 cards, ~2–3s each → 10–18s.

## Brand rules
- 1080×1920, ink/emerald/cream/amber, big type, one idea per card.
- First card = the hook (sound-off readable). Last card = soft audit CTA + soundwave.
- Amber = loss/missed; green = win/answered.

## Publishing
A reel publishes via a queue job: `{ "type":"reel", "caption":"...",
"video_url":"https://raw.githubusercontent.com/Dave-APEX-AI/ad-spend-watcher/main/social/publish/queue/<name>/<name>.mp4" }`.
Commit the MP4 into `social/publish/queue/<name>/`, add the job to `queue/schedule.json`,
push to main — the auto-publisher posts it (IG transcodes; ~1 min). Reels aren't
cross-posted to FB by the script — share those from the app/Business Suite.

## Notes
- Silent by default (IG allows it; the silent AAC track keeps the API happy). Add music
  in-app if wanted, or drop a royalty-free track later.
- Repurpose: any carousel spec can become a reel — reuse its slides as cards with `seconds`.
