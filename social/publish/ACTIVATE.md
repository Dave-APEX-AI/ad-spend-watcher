# ⚡ Activate the auto-publisher — your one-time checklist

Everything on the build side is **done**: 3 posts rendered, queued with public image URLs +
captions, the scheduler + GitHub Actions workflow are wired. To switch it on, three things
need YOU (they require logging in as you — I can't do these):

> 🔒 **Never paste a token in chat or commit it.** Tokens go into GitHub **Secrets** only.

---

## 1. Instagram must be a Business account (5 min — phone)
- IG app → Settings → Account type → **switch to Business**.
- Link it to your **Facebook Page** (Business Suite prompts this). Both free.

## 2. Get a Meta token + IG id (10 min — laptop)
The simplest path uses a **Page access token** (effectively non-expiring), so you avoid the
60-day refresh dance.

1. developers.facebook.com → **Create App** → type **Business**.
2. Tools → **Graph API Explorer** → pick your app → **Add permissions**:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `pages_manage_posts`, `business_management`.
3. **Generate Access Token** → approve. (This is short-lived — next step makes it durable.)
4. In the Explorer, run `GET /me/accounts` → find your Page → copy its **`id`** (= `FB_PAGE_ID`)
   and its **`access_token`** (this Page token is long-lived → use for `IG_ACCESS_TOKEN` and
   `FB_PAGE_TOKEN`).
5. Run `GET /{FB_PAGE_ID}?fields=instagram_business_account` → copy the returned
   **`id`** (= `IG_USER_ID`).

## 3. Add the secrets to GitHub (2 min — laptop)
Repo → **Settings → Secrets and variables → Actions → New repository secret**. Add:

| Secret | Value |
|--------|-------|
| `IG_USER_ID` | from step 2.5 |
| `IG_ACCESS_TOKEN` | the Page token from step 2.4 |
| `FB_PAGE_ID` | from step 2.4 *(optional — for FB cross-post)* |
| `FB_PAGE_TOKEN` | the Page token from step 2.4 *(optional)* |

---

## 4. Go live
1. Make sure this branch is **merged to `main`** (the workflow only runs from the default
   branch). Ask me and I'll merge it, or merge it yourself.
2. Repo → **Actions → caillte-publish → Run workflow** with **dry run = true** → check the
   log shows the right post + URLs.
3. Run again with **dry run = false** → **Post 1 publishes to Instagram + Facebook.** 🎉
4. Repeat to push Post 2 and Post 3 today, or just let the **daily 18:00 UTC schedule** drain
   the queue one post a day. The workflow records progress in `queue/.posted`.

## Adding more posts later
Render → `python3 social/publish/stage.py --name <spec> --caption-section "Day N"` → add the
job filename to `queue/schedule.json` → commit. The scheduler picks it up automatically.

## If a run fails
- **auth error** → token wrong/expired → regenerate (step 2) and update the secret.
- **media url not reachable** → the PNG isn't on `main` yet (merge first), or the repo path
  changed.
- A failed post is **not** marked done — it retries on the next run.
