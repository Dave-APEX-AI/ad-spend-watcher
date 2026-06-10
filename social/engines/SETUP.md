# Engines — Setup & Costs

The honest breakdown of what's free and what costs money, plus how to wire the paid
engines if/when you want them.

## TL;DR — your core engine is £0

| Engine | Skill | Cost | Status |
|--------|-------|------|--------|
| Free carousel generator | `caillte-carousel` | **£0** — local headless Chrome | ✅ ready |
| Demo screen-recordings | `caillte-demo-clip` | **£0** — you record your product | ✅ ready |
| Holo single statics | `caillte-static-post` | **free tier** (single images) | ✅ ready (your account) |
| Hooks / captions / calendar | `caillte-hook-writer`, `caillte-content-calendar`, `caillte-daily-snapshot` | **£0** | ✅ ready |
| AI-actor UGC video | `caillte-ugc-video` → Arcads pack | **PAID** | ⏸ Phase 2, optional |

You can run the entire GROW plan indefinitely without paying for anything. The paid
engines below are purely for *scaling AI-actor video later*.

---

## Free carousel engine (no setup)
Just needs Chrome/Chromium (already on your Mac). Test:
```
python3 .claude/skills/caillte-carousel/render.py \
  .claude/skills/caillte-carousel/examples/maths.json --out social/out
```
PNGs appear in `social/out/missed-call-maths/`. If Chrome isn't found, set `CHROME_BIN`
to its path, or `brew install chromium`.

---

## Arcads (Phase 2, PAID) — AI-actor UGC video
Vendored at `social/engines/arcads-pack/` (MIT, by Kruse Media LLC). Needs an Arcads
account + API credits.

1. `cd social/engines/arcads-pack && ./scripts/setup.sh` — it asks for your key and writes
   `.env` (gitignored). Get the key at **app.arcads.ai/settings/api**.
2. Or manually: `cp .env.example .env` and fill `ARCADS_BASIC_AUTH='Basic …'`.
3. Verify: `./scripts/check-arcads-env.sh`.
4. Use via the `caillte-ugc-video` skill (it applies the CaillteAI brand layer).

**Cost control:** the pack estimates cost before each generation and logs to
`logs/arcads-api.jsonl`. Always approve the estimate first. Every Meta ad it builds is
created **paused**.

> ⚠️ Never commit `social/engines/arcads-pack/.env`. Confirm `.gitignore` excludes it
> before every push (the repo root `.gitignore` already ignores `**/.env`).

---

## Pletor.ai — custom connector (free trial, then PAID)
Pletor ships a Claude-compatible **MCP server** that exposes every Pletor workflow
(static/UGC/video across Nano Banana, Veo, Sora, Kling, etc.) to this agent. Free trial =
200 credits, then paid. It's an *alternative* to wiring Arcads directly, and can power
both statics and video from one connector.

### Wire it (when you want it)
1. Sign up at **pletor.ai**, generate an API key in your account settings.
2. Follow **docs.pletor.ai/automate/pletor-mcp** for the exact server URL + auth header
   (it's a remote MCP server, API-key/bearer auth).
3. Add it as a project MCP server. Copy `pletor-connector.example.json` → wire into your
   Claude config (or `claude mcp add`), filling the real URL + key:
   ```
   cp social/engines/pletor-connector.example.json .mcp.json
   # then edit: paste the URL from the docs and your key
   ```
4. Restart the session; Pletor's tools appear as `mcp__pletor__*`.

> The exact endpoint URL is on the Pletor docs page (Cloudflare-blocked to our fetcher, so
> it's left as a placeholder you paste in). Everything else is ready.
> ⚠️ Put the key in `.mcp.json` / env only — never commit a real key.

---

## What I recommend
Run free-only for the first 30–60 days (carousels + demos + statics). Once you know which
formats convert, add **one** paid video engine — Pletor if you want a single connector for
everything, Arcads if you want the deeper UGC-ad tooling. Not both.

---

## Extracting into its own repo (later)
This whole module is portable. To graduate it to a `caillte-social` repo:
```
git subtree split --prefix=social -b caillte-social    # or just copy social/ + .claude/skills/caillte-*
```
Move `social/` and the `.claude/skills/caillte-*` skills across; nothing depends on the
lead-gen pipeline.
