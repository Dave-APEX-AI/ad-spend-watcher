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

## Autonomous vs triggered (IMPORTANT — set 2026-06-22)
- **Fully autonomous (no human):** (1) posting 2/day via `caillte-publish.yml`; (2) **queue
  auto-refill** via `caillte-refill.yml` (daily 06:00 UTC) — `refill.py` renders unused
  `social/content/library/` specs on the runner (setup-chrome + imageio-ffmpeg) and tops the
  queue to TARGET_BUFFER (14). **The channel will not go dark.** Proven on the runner 2026-06-22.
- **Still triggered (needs a human/agent):** scan-driven *freshness* (reacting to this week's
  trends) + new customer stories. GitHub Actions can't run live web research / LLM reasoning
  without an API key (cost). So: the library rotates evergreen content autonomously; refresh
  it periodically (weekly drop / new stories) so it never repeats for long.
- **To keep it hands-off for months:** keep `social/content/library/` well stocked. When it
  empties, refill no-ops and (eventually) the queue drains — so top the library up.

## Open / next
- **Proof reel** — "listen to it book a job at 9pm": needs a consented real call recording.
  Highest-trust post in the niche; nobody does it. Build when Dave sends audio.
- **More "other" content** — story bank is deep (~month at 3/week) but non-story posts need
  topping up to sustain 2/day for a full month. Produce weekly via the drop.
- Optional: move GitHub notifications to hello@caillteai.com (settings).
- Remaining trades all covered (10/10). Strengthen any story with a confirmed real result.

---

## Learnings log (append dated entries)

### 2026-06-22 (analytics — REAL view data after adding instagram_manage_insights)
- **Analytics:** `caillte-analytics.yml` + `analytics.py` (ranks all posts by views/reach).
- **#1 post on the whole account = OUR £280→£24k counter REEL (`w3-counter-reel`) — 228 views**
  in ~1 day. Other top reels: villain "I'm your missed call" (161 views/130 reach),
  "under a sink" (89/79), plus older "Pat lost €4,200" reel (169/149).
- **REELS win decisively on REACH:** reels reach 79–149 non-followers; feed posts only 8–57.
  High-view feed posts are mostly Nov–Dec 2025 (months to accumulate). Normalised for age,
  reels dominate. **→ Weight the content mix HARD toward reels.**
- **Saves ≈ 0 everywhere** (audience too small yet). Likes still ≤8. Followers/reach is the lever.
- Account has ~108 posts back to Nov 2025 (Dave/prior tool posted before our system).
- **Autonomous refill** proven on the runner (caillte-refill.yml) — queue tops itself up.

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
- **Meta's own AI content tools (Meta AI / Vibes / Movie Gen) have NO official API** — they're
  human-facing apps; an agent can't drive them hands-off (only a risky unofficial cookie-based
  wrapper, which we won't use — ToS/account risk). Agent-driven generation = our free
  Chromium+ffmpeg engine (default) or Arcads/Pletor APIs (paid, for photoreal/AI-actor). Don't
  re-litigate "just use Meta AI".
