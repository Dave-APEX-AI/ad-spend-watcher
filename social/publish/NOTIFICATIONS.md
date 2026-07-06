# Notifications — via GitHub (no third-party, no extra account)

You wanted email on **problems**, **steps done/good**, and **needs-your-input** — without
Web3Forms. So we use **GitHub Issues** as the channel: when an issue is opened, **GitHub
emails you** through its own notification system. No external service, no key.

## The three notifications
| Trigger | How | You're emailed because |
|---------|-----|------------------------|
| 🚨 **Problem** — a scheduled post fails | `caillte-publish.yml` opens a `🚨 ...FAILED` issue | you're @mentioned + own the repo |
| 🚨 **Problem** (backstop) — any workflow fails | GitHub's built-in failed-run email | repo notifications |
| ✅ **Done & good** — weekly drop / a step finished | I open a `✅ ...` issue (cc you) | @mention emails you |
| ❓ **Needs your input** — blocked on you | I open a `❓ ...` issue (cc you) | @mention emails you |

Each issue is opened **by the GitHub Actions bot** (not by you) and **assigns + @mentions
@Dave-APEX-AI** — both trigger a GitHub email. (Important: GitHub never emails you about
issues *you* open yourself, so notifications must be bot-opened — that's why the
`caillte-notify` workflow exists rather than me opening them directly.) Close the issue
once you've read it.

## One-time check (≈1 min, no account, no key)
Make sure GitHub emails you:
1. github.com → your avatar → **Settings → Notifications**.
2. Under **Email**, confirm your notification email — set it to **hello@caillteai.com** if
   you want them there (add+verify it under Settings → Emails first), or keep your usual one.
3. Ensure **Participating** notifications (mentions) are emailed — on by default.

That's it. No Web3Forms, no secrets, no SMTP.

## Volume
Notifications are **per step/problem**, not per post — a few a week, not 60. The 2-a-day
auto-posts don't each email you; only failures and the work-steps (weekly drops, input
requests) do.
