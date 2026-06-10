# Publishing & automation (free)

How content gets from this repo onto Instagram & Facebook — from "post it by hand" to
"fully automated", all on free tools. Pick the tier you want.

## Step 0 — Render the carousels (on your Mac, free)
The repo holds **specs**; turn them into image slides with one command:
```
python3 .claude/skills/caillte-carousel/render.py social/content/week1/03-missed-call-maths.json --out social/out
```
→ PNGs in `social/out/03-missed-call-maths/slide_01.png …`. Repeat per spec. (Needs Chrome,
already on your Mac.) Reels/demos you make in CapCut (free); statics in Holo.

---

## Tier 1 — Manual (0 setup, most control)
- **Carousel:** IG app → + → select the slide PNGs **in order** → paste caption from
  `week1/captions.md` → share. Cross-post to FB on the last screen.
- **Reel:** upload the video, paste caption, cover frame = your hook frame.
- Best while you're finding your feet; ~3 min/post.

## Tier 2 — Schedule for free (RECOMMENDED to start) ⭐
**Meta Business Suite** (business.facebook.com) — Meta's own free tool. Schedule IG **and**
FB feed posts, **carousels**, **Reels** and **Stories** days/weeks ahead from your desktop.
- **Requires:** IG switched to a **Professional** account, **linked to a Facebook Page**
  (both free — see `PROFILE.md`).
- **Workflow:** render the week's PNGs → upload all 7 posts Sunday → set times → done.
  One sitting covers the week. This is the sweet spot: free, official, no code, reliable.
- Free third-party schedulers exist (Buffer free = 3 channels/limited, Metricool free) but
  Business Suite does more for £0 — start there.

## Tier 3 — Full automation (free, technical) — connect this repo → Instagram
For hands-off posting straight from the repo, use the **Instagram Graph API → Content
Publishing**. Free. Publishes image/carousel/reel to an IG **Business** account
programmatically, and cross-posts to the FB Page.

**What it needs (one-time):**
1. IG **Business** account + linked **Facebook Page**.
2. A **Meta developer app** (free) with `instagram_basic`, `instagram_content_publish`,
   `pages_show_list` permissions.
3. A **long-lived access token** (~60 days — rotate; see `CLAUDE.md` token note) + your IG
   user id.
4. **Public image URLs.** The API pulls images by URL — and you already publish to GitHub
   Pages, so committed carousel PNGs get a public URL it can fetch. Nice fit.

**How it'd run:**
```
render PNGs → commit to repo (public URL via GitHub Pages)
      → publisher script: create media container per slide → carousel container → publish
      → cross-post to FB Page
      → trigger on a GitHub Actions cron (free) = scheduled, hands-off
```

**Caveats:** Business/Creator accounts only (not personal); ~50 API posts / 24h; Reels via
API need a hosted **video** URL (carousels/images are the easy win); token refresh every
~60 days. The vendored Arcads pack has Meta API plumbing, but that's for **paid ads** —
organic posting uses the Content Publishing API above.

### Want this built?
I can scaffold a `caillte-publish` skill + `social/publish/ig_publish.py` that:
- reads rendered PNGs + the caption from `week1/captions.md`,
- publishes the carousel to IG and mirrors to the FB Page,
- runs manually or on a free GitHub Actions schedule.
You'd provide the Meta app token + IG id (kept in env/secrets, never committed). Say the
word and I'll build it.

---

## Recommendation
**Weeks 1–4:** render → schedule the week in **Meta Business Suite** (Tier 2). Zero cost,
zero code, fully reliable while you learn what's hitting. **Once the cadence is a habit**
and you're sick of the Sunday upload, switch on **Tier 3** automation. Don't automate
before you have proof the content works — you'd just be scaling guesses.
