---
name: caillte-publish
description: >-
  Publish a CaillteAI carousel/image/reel to Instagram (and cross-post to the Facebook
  Page) via the Meta Graph API — free organic posting. Use when the user wants to "post
  this to Instagram", "publish the carousel", "push to IG/FB", "schedule the post", or
  automate publishing. Requires an IG Business account + token (social/publish/.env).
---

# caillte-publish — post to Instagram + Facebook (free)

Drives `social/publish/ig_publish.py` (Graph API Content Publishing). Free; no third-party
tools. For *making* the assets use `caillte-carousel` / `caillte-demo-clip` first.

## Before anything
1. Confirm `social/publish/.env` exists with `IG_USER_ID` + `IG_ACCESS_TOKEN`. If missing,
   **stop** and point the user to `social/publish/README.md` setup — do not ask for tokens
   in chat unless they insist; they belong in `.env` (gitignored).
2. The media must be at **public URLs**. Render with `caillte-carousel`, then copy the
   slides into `social/publish/queue/<name>/` and commit so GitHub Pages serves them.

## Steps
1. Build/locate the assets and the caption (caption from `social/content/week1/captions.md`
   or `caillte-hook-writer`).
2. **Always dry-run first** and show the user the asset URLs + caption:
   ```
   set -a; source social/publish/.env; set +a
   python3 social/publish/ig_publish.py <job>.json --dry-run
   ```
3. On the user's go-ahead, publish (remove `--dry-run`). Report the returned media id and
   confirm the FB cross-post.

## Job file
`{ "type":"carousel"|"image"|"reel", "caption":"...", "image_urls":[...],
   "video_url":"...", "cross_post_facebook":true }` — or use
`--from-dir <dir> --caption-file ... --caption-section "Day N"`.

## Guardrails
- Confirm with the user before the live (non-dry-run) post — publishing is outward-facing.
- IG Business accounts only; carousels 2–10 images; ~50 posts/24h; token ~60-day expiry
  (surface the auth error and tell them to refresh if it's stale).
- Never echo tokens; never commit `.env`.
- Scheduling: `.github/workflows/caillte-publish.yml.example` (cron, repo secrets).
