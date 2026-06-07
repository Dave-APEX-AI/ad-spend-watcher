# caillte-publish — auto-post to Instagram + Facebook (free)

Publishes carousels / images / Reels to an Instagram **Business** account via the Meta
Graph API Content Publishing API, and cross-posts images to your Facebook Page. Organic
publishing is free. Zero third-party deps (Python stdlib only).

## One-time setup

1. **Accounts:** IG switched to a **Business** account, linked to a **Facebook Page** (both
   free — see `../PROFILE.md`).
2. **Meta app + token:** create a free app at developers.facebook.com → use the Graph API
   Explorer to grant `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement` (+ `pages_manage_posts` for FB cross-post) → generate a
   **long-lived** token (~60 days; rotate before it expires — see `CLAUDE.md`).
3. **IDs:** get your IG user id (`GET /me/accounts` → page → `instagram_business_account`).
4. **Config:** `cp .env.example .env` and fill it in. The `.env` is gitignored — never commit it.

## Publish flow

```
render carousel (caillte-carousel) → PNGs
  → commit PNGs to a Pages-served folder (so they have PUBLIC URLs)
  → load env:  set -a; source social/publish/.env; set +a
  → dry-run:   python3 social/publish/ig_publish.py <job>.json --dry-run
  → go live:   python3 social/publish/ig_publish.py <job>.json
```

### Two ways to specify a post
- **A job file** (see `example-job.json`): set `type`, `caption`, `image_urls` (public),
  `cross_post_facebook`.
- **From a folder** (auto-builds slide URLs from `PUBLIC_BASE_URL`):
  ```
  python3 social/publish/ig_publish.py \
     --from-dir social/publish/queue/03-missed-call-maths \
     --caption-file social/content/week1/captions.md --caption-section "Day 3"
  ```

> **Why a `queue/` folder?** The API fetches media by **public URL**, so the PNGs must be
> committed somewhere GitHub Pages serves. `social/out/` is gitignored (working output);
> copy the slides you're ready to post into `social/publish/queue/<name>/` and commit them.

## Limits & notes
- IG **Business/Creator** accounts only (not personal). ~50 API-published posts / 24h.
- Carousels: 2–10 images. Reels need a public **video** URL; transcoding adds a wait.
- Reels aren't auto-cross-posted to FB here — share those from the IG app / Business Suite.
- Token expires ~60 days → refresh it; the script will report a clear auth error if stale.

## Scheduling (hands-off, free)
Use the GitHub Actions template `.github/workflows/caillte-publish.yml.example`:
rename to `.yml`, add `IG_USER_ID`, `IG_ACCESS_TOKEN`, `FB_PAGE_ID`, `FB_PAGE_TOKEN` as
repo **Secrets**, and it runs on a cron (or manual dispatch) to publish a queued job.
Start manual; switch the schedule on once you trust the content.
