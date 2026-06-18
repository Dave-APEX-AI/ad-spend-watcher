# Intent Radar — inbound-leak signal engine

A free, signal-driven lead engine for Apex Emerald AI / CaillteAI. It does the
opposite of chasing new businesses: it finds **established UK & Ireland firms
(10+ staff) that are leaking inbound revenue right now** — missing calls, slow to
reply on any channel, sending paid ad clicks to a broken/no website, or opening a
new location blind — and routes each to the right offer, led by the **AI voice
receptionist + speed-to-lead**.

It is the inverse of a Clay/Apollo: those sell firmographic exhaust; we mine
**free public pain signals** (review text, Facebook reply-speed badges, Google
listings, PageSpeed, planning/expansion) that paid tools don't index.

## Who we target (ICP)

| ✅ In | ❌ Out |
|---|---|
| 10+ employees, or multi-location | 1–3 person sole traders |
| Established, has a budget | Brand-new registrations (no money, over-sold) |
| Independent / regional groups / franchisees | National corporate chains (in-house marketing) |

Sectors: aesthetic clinics, vets, MOT centres, tyre & fast-fit, independent car
dealers, heat-pump / solar / EV-charger installers, recruitment agencies.
(Dentists explicitly excluded.)

## The signals (all free)

| Signal | Means | Free source |
|---|---|---|
| `missed_call_review` | reviews say "no one answered / never called back" | Google / Trustpilot / FB review text |
| `slow_response` | slow on DMs/forms | Facebook "typically replies in…" badge |
| `out_of_hours_gap` | urgent calls after hours go unanswered | Google Business Profile hours |
| `hiring_receptionist` | already paying to answer phones | Indeed / careers page |
| `website_leak` | no/broken/slow site (worse if advertising) | GBP website field, viewport/SSL check, PageSpeed API |
| `ads_active` | has budget, buying inbound | Meta Ad Library / Google Ads Transparency |
| `new_location` | expanding — jackpot | new Google listing, "now open in…" |
| `expansion_hiring` | scaling capacity | job-ad volume |

Signals **stack** (with recency decay) into a 0–100 intent score, with
diminishing returns so the single biggest leak dominates. Tiers: Hot ≥ 60,
Warm 35–59, Watch < 35.

## Pipeline

```
intent/run.py
├── collectors/collect_inbound.py   # missed-call reviews, slow reply, out-of-hours, receptionist hiring
├── collectors/collect_web.py       # website leak + ad-budget
├── collectors/collect_growth.py    # new location + expansion hiring
├── intent_score.py                 # qualify (gate) → stack signals → score → route to offer
│      → data/intent_companies.json (dashboard)
├── action_agent/draft_outreach.py  # leak-referencing outreach drafts
│      → data/action_queue.json
└── (Claude sub-agent) action_agent/AGENT.md  # finds contact, personalises, → Gmail draft for VA
```

Run it:

```bash
python intent/run.py --include-warm      # collect → score → draft
python -m http.server -d intent 8000     # then open http://localhost:8000  (dashboard)
```

## Live vs seed data

Every collector tries the live free source first and **falls back to the bundled
sample** (`data/roster.json`) when a source 403s or an API key is missing, so the
pipeline always produces a dashboard. On Dave's Mac:

- **Reviews / Facebook reply-speed** are JS-driven and 429 bare HTTP clients —
  use the Chrome MCP override (see root `CLAUDE.md` "Chrome verification").
- **Jobs**: add `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` (free at developer.adzuna.com)
  to `config/credentials.json`.
- **Website leak**: Google PageSpeed Insights API is free, no key needed for low
  volume.
- **Registers** (MCS / OZEV / DVSA active-station CSV / REC) are the free source
  lists used to enumerate the established firms in `roster.json`.

`data/roster.json` is **sample data** for demonstration — replace with live
roster pulls per vertical.

## The actioning sub-agent

`action_agent/` is the second half of the system: the engine *finds* leaks, the
sub-agent *acts* on them. `draft_outreach.py` always produces a safe templated
draft; the Claude agent in `AGENT.md` then finds the contact email for free,
personalises it, and stages a **Gmail draft** for the VA — nothing auto-sends.
