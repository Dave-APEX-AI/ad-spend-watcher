# CaillteAI Social — MEMORY (read first, append as we learn)

Durable memory for the CaillteAI social growth system. **Read this before working on
social.** Append a dated entry to the Learnings log after any significant change or lesson.

System lives under `social/` + `.claude/skills/caillte-*`. Index: `social/README.md`.
Strategy: `social/STRATEGY.md`. The weekly engine: `.claude/skills/caillte-weekly-drop`.

---

## Hard decisions & preferences (the always/never list)

- **Free engines only for the core:** carousels (`caillte-carousel`), reels (`caillte-reel`),
  statics (`caillte-static`) — all render via bundled Chromium + ffmpeg, £0. Proven live.
- **Arcads = PARKED.** Installed (`social/engines/arcads-pack/`, skills synced) but idle —
  it's PAID, Phase-2. Don't reach for it unless Dave explicitly wants AI-actor UGC and has a key.
- **No Web3Forms / no third-party email senders.** Notifications go through **GitHub Issues**:
  the Actions **bot** opens an issue + **assigns @Dave-APEX-AI** → GitHub emails him.
  - ⚠️ GitHub delivers to his **GitHub account email = dave@apexemeraldai.com**, NOT
    hello@caillteai.com (unless he adds+verifies it and sets it as default notifications email).
  - Issues opened by Dave's own token do NOT email him (no self-notifications) — must be bot-opened.
- **Customer stories:** anonymise by default ("a plumber we work with"); **qualitative only**
  — never invent £/%/quotes as a real result (UK DMCCA 2024 / ASA compliance). Add real numbers
  only when Dave confirms. Bank + 10-trade rotation in `social/content/customer-stories.md`.
- **Cadence:** 2 posts/day (cron 09:00 + 18:00 UTC). ~3 stories/week woven among other types.
- **Operating model = scan-driven weekly** (`caillte-weekly-drop`): scan → pivot → produce →
  queue. **Triggered, not autonomous** — needs Dave to say "weekly drop" (scan needs live web
  research; can't self-run here). Keep ~1 week buffered. Don't over-batch a static month.
- **Mode = GROW + ship-now.** Reach/saves/follows first; soft CTA only (the missed-call audit).
- **Branch model:** develop on `claude/caillteai-social-growth-xXKt5`, then merge to **`main`**
  (Actions + Pages + raw image URLs all serve `main`). Verify `.posted` before re-ordering queue.
- **Image/video hosting:** committed under `social/publish/queue/` → public via
  `raw.githubusercontent.com/.../main/...` (repo is public). No CDN needed.

## How publishing works (so we don't relearn it)
- GitHub Actions `caillte-publish.yml` posts the next pending queue item (2×/day) to IG +
  cross-posts images/carousels to the FB Page; reels are IG-only. Marks `.posted`, commits back.
- Meta token: **~60-day expiry** (refresh ~early Aug 2026) — `social/publish/ACTIVATE.md`.
  Secrets in repo: IG_USER_ID, IG_ACCESS_TOKEN, FB_PAGE_ID, FB_PAGE_TOKEN.
- IDs (not secret): IG_USER_ID `17841478247755553`, FB_PAGE_ID `921434057715457` (Cailliteai).
- One-off publish of a specific job: `caillte-publish.yml` `job` input. Notify: `caillte-notify.yml`.

## State snapshot (keep current)
- Live & posting: carousel + reel confirmed on @caillte_ai; ~6+ posts auto-published.
- Queue: ~10–12 days buffered (stories + others), 2/day.
- Audit funnel: `social/audit/index.html` (capture-enabled) — uses Web3Forms for the AUDIT
  lead capture (separate from notifications; Dave's call whether to wire its key).
- Notifications: GitHub-issue based → dave@apexemeraldai.com. Working (confirmed 2026-06-20).

## Open / next
- **Proof reel** — "listen to it book a job at 9pm": needs a consented real call recording.
  Highest-trust post in the niche; nobody does it. Build when Dave sends audio.
- **More "other" content** — story bank is deep (~month at 3/week) but non-story posts need
  topping up to sustain 2/day for a full month. Produce weekly via the drop.
- Optional: move GitHub notifications to hello@caillteai.com (settings).
- Remaining trades all covered (10/10). Strengthen any story with a confirmed real result.

---

## Learnings log (append dated entries)

### 2026-06-20
- **GitHub notification gotcha:** GitHub never emails you about your own actions, and it
  delivers to the **GitHub-account email (dave@apexemeraldai.com)**, not hello@caillteai.com.
  Fix = bot-authored issues + assign Dave; he found the test email in dave@apexemeraldai.com.
- Confirmed the free video pipeline (Chromium frames → ffmpeg, via free imageio-ffmpeg) posts
  to IG as a Reel end-to-end. Statics = single-slide carousel render. All £0.
- Dave wants: anonymised, qualitative customer stories across 10 trades, 3/week; weekly
  scan-driven content; no Web3Forms; Arcads parked; email confirmations on each step/problem.
- Verified UK stat to lean on: trades lose ~£24k/yr to 60%+ unanswered calls (digitalx, 2026).
- Trend data: carousels win saves, reels win reach → mix ~4 reels / ~7 carousels / ~3 statics.
