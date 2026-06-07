# caillte-leads — missed-call audit lead capture

Free Cloudflare Worker (same free tier + pattern as `asw-status`) that catches leads from
the missed-call calculator (`social/audit/index.html`) and stores them in KV. Token-
protected CSV export so you (or the VA) can pull leads anytime.

## Deploy (5 minutes, free)

```bash
cd worker/caillte-leads
npx wrangler login                                  # one-time
npx wrangler kv namespace create LEADS_KV           # copy the printed id...
#   ...paste it into wrangler.toml -> id = "..."
npx wrangler secret put ADMIN_TOKEN                 # type a long random string; keep it safe
npx wrangler deploy                                 # prints your worker URL
```

You'll get a URL like `https://caillte-leads.<you>.workers.dev`.

## Wire it to the calculator
In `social/audit/index.html`, set:
```js
const LEAD_ENDPOINT = "https://caillte-leads.<you>.workers.dev/lead";
```
(If left blank, the form falls back to a pre-filled `mailto:` so leads still reach you.)

## Get your leads
```
https://caillte-leads.<you>.workers.dev/leads?token=YOUR_ADMIN_TOKEN
```
Downloads a CSV: timestamp, name, email, phone, trade, £ lost/yr & /mo, inputs, UTM source.
Open in Sheets/Excel. (Keep the token private — anyone with it can read the list.)

## Endpoints
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/lead` | Origin allowlist | capture a lead |
| GET | `/leads?token=` | `ADMIN_TOKEN` | CSV export |
| OPTIONS | `*` | — | CORS preflight |

## Security
- POST only from the allowlisted origins in `index.js` (`ALLOWED_ORIGINS`) — add your real
  calculator host there if it isn't `caillteai.com` / `dave-apex-ai.github.io`.
- Email/phone validated; all fields length-capped; array hard-capped at 50k.
- Export gated by a secret token (never committed).
- No secrets in this repo — the token lives only in Wrangler.
