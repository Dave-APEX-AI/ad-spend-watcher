# Real photo backgrounds (free, via Pexels)

Put real trade imagery (plumbers, vans, jobsites) *behind* the text in reels and statics —
free, commercial-use, no attribution. The engine darkens the photo automatically so the
copy stays readable and on-brand.

## One-time: get a free key (30 sec)
1. https://www.pexels.com/api/ → sign up → copy your API key (instant, free).
2. For local use: `export PEXELS_API_KEY=...`
   For the automated pipeline: add it as a repo secret **`PEXELS_API_KEY`** (Settings →
   Secrets and variables → Actions) so the auto-refill can fetch photos too.

## Use it
Fetch a photo, then reference it in a reel spec via `"photo"`:
```
PEXELS_API_KEY=... python3 social/publish/fetch_photo.py "plumber van uk" /tmp/bg.jpg
```
Reel spec:
```json
{ "name":"...", "fps":30, "photo":"/tmp/bg.jpg", "cards":[ ... ] }
```
The renderer inlines the image (so the headless browser can load it) and lays the animated
text + mascot over a darkened version. Carousels/statics get the same `photo` support next.

## Good search terms for our niche
`plumber van`, `electrician working`, `tradesman phone`, `roofer ladder`, `tools workshop`,
`van night street`, `phone ringing desk`, `solar panel installer`.

## Licensing
Pexels photos are free for commercial use, no attribution required. (Same for Pixabay if we
add it as a fallback.)
