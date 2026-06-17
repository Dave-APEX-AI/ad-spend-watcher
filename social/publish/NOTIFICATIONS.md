# Email notifications — what you get, and the one-time setup

You wanted: email me on **problems**, **when steps are done/good**, and **when I need your
input**. Here's how each is delivered.

## The three emails
| Trigger | How | To |
|---------|-----|----|
| 🚨 **Problem** — a scheduled post fails | `caillte-publish.yml` failure step → email | hello@caillteai.com |
| 🚨 **Problem** (backstop) — any workflow fails | GitHub's built-in failed-run email (free) | your GitHub account email |
| ✅ **Done & good** — weekly drop / a step finished | `caillte-notify.yml` (I trigger it) | hello@caillteai.com |
| ❓ **Needs your input** — something's blocked on you | `caillte-notify.yml` (I trigger it) | hello@caillteai.com |

## Why an email sender is needed
GitHub Actions (the robot that posts) has no mailbox. GitHub will email you *only when a
job fails* — it can't send "all good ✅" or "need your input ❓" emails. So those require a
sender. **Web3Forms** is the simplest free one (no SMTP, no password — one HTTP request).

## One-time setup (~2 min, free)
1. Go to **web3forms.com**, enter **hello@caillteai.com**, copy the access key they email you.
2. Repo → Settings → Secrets and variables → Actions → **New repository secret**:
   name `WEB3FORMS_KEY`, value = the key.
That's it. All three emails above now send to hello@caillteai.com.

> Already made a Web3Forms key for the audit page? Reuse the same one.

## Free backstop (no setup)
Even without the key, GitHub emails you when a workflow **fails** — make sure repo
notifications are on (Settings → Notifications → Actions) and your GitHub email is one you
check. This covers "alert me on problems" at zero cost; the key adds the ✅ and ❓ emails.
