# CaillteAI — Social Growth System

A self-contained, **portable** module for growing CaillteAI's Instagram & Facebook
presence as the category-leading AI voice receptionist for UK & Irish trades.

> **Caillte** (Irish, "lost") — the whole brand is built on one promise:
> *you never lose another call, lead, or job.* That word does a lot of work in
> our content. Lean on it.

Nothing in here touches the lead-gen pipeline (`scripts/`, `data/`, `dashboard.html`).
Everything lives under `social/` and `.claude/skills/caillte-*` so it can be lifted
into its own `caillte-social` repo at any time (see `engines/SETUP.md` → "Extracting").

## What's here

| Path | What it is |
|------|------------|
| `BRAND.md` | Positioning, tone of voice, the faceless-channel doctrine, visual tokens |
| `STRATEGY.md` | The IG + FB growth plan — pillars, cadence, algorithm tactics, KPIs |
| `PROFILE.md` | Copy-paste bio, name, handle, highlights, link-in-bio |
| `competitors.md` | Joe Doyle / Tradify / the AI-receptionist newcomers — how we differ |
| `series/office-heroes.md` | The flagship faceless content franchise + episode formats + scripts |
| `content/hooks.md` | Hook swipe file (missed-call pain → product) |
| `content/launch-sprint.md` | ⚡ **72-hour go-live sprint — start here** |
| `content/calendar-30day.md` | Day-by-day launch calendar |
| `content/lead-magnet-missed-call-audit.md` | The free "what are missed calls costing you" audit |
| `audit/index.html` | The **owned, capture-enabled** missed-call calculator (our CTA) |
| `../worker/caillte-leads/` | Free Cloudflare Worker that catches the audit's leads |
| `PUBLISHING.md` | How to publish to IG/FB + free scheduling & automation |
| `engines/SETUP.md` | How to wire the engines + what's free vs paid |
| `engines/arcads-pack/` | Vendored Arcads UGC-video skill pack (MIT, Phase-2, **paid**) |

## The engines (what actually makes the posts)

| Engine | Cost | Makes | Skill |
|--------|------|-------|-------|
| **Free carousel generator** | £0 | Multi-slide IG/FB carousels (PNG) | `caillte-carousel` |
| **Demo screen-recordings** | £0 | Reels of the AI answering calls | `caillte-demo-clip` |
| **Holo** | free tier | Single hero static images | `caillte-static-post` |
| **Arcads (Pletor)** | **paid** | AI-actor UGC video | `caillte-ugc-video` (Phase 2) |

Your **core engine costs nothing** — carousels + demos + Holo statics. Arcads/Pletor
are optional, only when you want AI-actor video.

## Daily driver

Run the `caillte-daily-snapshot` skill each morning for a "what to post today" brief,
or ask: *"plan this week's CaillteAI posts"* (→ `caillte-content-calendar`).

## Action mode: GROW — and SHIP NOW ⚡

**Bias to ship.** Aggressive timelines: live in hours not weeks, 8/10-today beats
10/10-next-week. New here? Open `content/launch-sprint.md` and go.

Every decision in this module optimises for **reach → saves → follows** first.
Soft CTA only (free missed-call audit). Monetise the audience once it's built.
