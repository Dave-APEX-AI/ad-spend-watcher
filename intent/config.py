"""
Intent Engine — configuration.

Central place for: which verticals we track, where their FREE public registers
live, how each signal type is weighted into the intent score, the tier cutoffs,
the grant/regulatory "why now" hooks per vertical, and the corporate-chain
blocklist that keeps us pointed at sellable independent owner-operators.

No paid tools. Every source below is a free public register, a free job API/board,
a free ad library, or a free reviews surface.
"""

# ──────────────────────────────────────────────────────────────────────────
# Signal weights — how many points a *fresh* signal of each type contributes
# to a company's intent score (0–100 scale, before recency decay + grant boost).
# ──────────────────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "new_register":    35,   # just qualified / just opened — peak intent
    "planning":        30,   # new-site application — earliest signal, 6–18mo out
    "hiring":          25,   # per active job ad (capped) — capacity expansion
    "advertising":     20,   # active on Meta/Google ad library — warm to marketing
    "review_velocity": 15,   # sudden review ramp — active demand / push
}

# A single company can stack at most this many job ads toward its score, so a
# huge recruiter doesn't drown out a sharper multi-signal lead.
HIRING_CAP = 2

# Signals older than this (days) stop counting toward "live" intent.
SIGNAL_TTL_DAYS = 120

# Recency decay: a signal at age 0 counts full; at SIGNAL_TTL_DAYS it counts ~0.
def recency_multiplier(age_days: int) -> float:
    if age_days <= 7:
        return 1.0
    if age_days >= SIGNAL_TTL_DAYS:
        return 0.0
    return max(0.0, 1.0 - (age_days - 7) / (SIGNAL_TTL_DAYS - 7))

# ──────────────────────────────────────────────────────────────────────────
# Tiers — same Hot/Warm/Watch language as ad-spend-watcher so the VA workflow
# is identical across both dashboards.
# ──────────────────────────────────────────────────────────────────────────
TIER_HOT = 65
TIER_WARM = 40

def tier_for(score: int) -> str:
    if score >= TIER_HOT:
        return "Hot"
    if score >= TIER_WARM:
        return "Warm"
    return "Watch"

# ──────────────────────────────────────────────────────────────────────────
# Verticals — the public register(s) that act as our free, qualified prospect
# list, plus the live grant/regulatory "why now" hook the actioning agent uses
# in outreach. Seed vertical is heat_pump; the rest are wired and ready.
# ──────────────────────────────────────────────────────────────────────────
VERTICALS = {
    "heat_pump": {
        "label": "Heat-pump installers",
        "job_roles": ["heat pump engineer", "ASHP installer", "renewables engineer"],
        "registers": [
            {"name": "MCS", "url": "https://mcscertified.com/find-an-installer/",
             "tech": "Air/Ground Source Heat Pump"},
        ],
        "grant_hook": "Boiler Upgrade Scheme £7,500 (new £9,000 off-grid uplift from 21 Jul 2026); Ireland SEAI up to €12,500",
        "sell_angle": "turn the grant-driven enquiry surge into booked installs before the BUS deadline",
    },
    "ev_charger": {
        "label": "EV-charger installers",
        "job_roles": ["EV charger installer", "EVSE electrician"],
        "registers": [
            {"name": "OZEV authorised installers",
             "url": "https://www.gov.uk/guidance/electric-vehicle-chargepoint-and-infrastructure-grant-installer-guidance",
             "tech": "EV chargepoint"},
        ],
        "grant_hook": "OZEV grant £500/socket (raised Apr 2026); Part S mandates chargers on new builds",
        "sell_angle": "win the grant-funded home/workplace charger work nobody is selling them",
    },
    "insulation": {
        "label": "Insulation / retrofit",
        "job_roles": ["insulation installer", "retrofit coordinator", "EWI installer"],
        "registers": [
            {"name": "TrustMark", "url": "https://www.trustmark.org.uk/find-a-tradesman",
             "tech": "Insulation / PAS 2035 retrofit"},
        ],
        "grant_hook": "GBIS closes Mar 2026 (deadline scramble); ECO4 to Dec 2026; Warm Homes up to £15k/home",
        "sell_angle": "capture private-pay retrofit demand that bypasses scheme-manager margins",
    },
    "hvac": {
        "label": "HVAC / air-conditioning",
        "job_roles": ["air conditioning engineer", "HVAC installer", "F-gas engineer"],
        "registers": [
            {"name": "REFCOM / F-Gas", "url": "https://www.refcom.org.uk/refcom-register/",
             "tech": "F-Gas refrigeration & AC"},
        ],
        "grant_hook": "New air-to-air BUS grant £2,500 (from Apr 2026); F-gas R410A phase-down forces a replacement cycle",
        "sell_angle": "ride the summer AC demand spike and the new air-to-air grant",
    },
}

DEFAULT_VERTICAL = "heat_pump"

# Fallback metadata for any vertical not explicitly configured above (e.g. the
# Solar/Plumbing/Alarms sectors inherited from ad-spend-watcher).
GENERIC_VERTICAL = {
    "label": "Local trades",
    "job_roles": [],
    "registers": [],
    "grant_hook": "",
    "sell_angle": "turn local demand into booked jobs",
}


def vertical_meta(vertical):
    """Vertical config, tolerant of unknown verticals."""
    if vertical in VERTICALS:
        return VERTICALS[vertical]
    meta = dict(GENERIC_VERTICAL)
    meta["label"] = (vertical or "other").replace("_", " ").title()
    return meta

# ──────────────────────────────────────────────────────────────────────────
# Corporate-chain blocklist. The whole strategy is selling to INDEPENDENT
# owner-operators; chains have in-house marketing and are not sellable leads.
# Matched case-insensitively as a substring of the company name. Extend freely.
# (Healthcare/childcare chains included so the engine is safe to point at those
# verticals later without re-pitching corporates.)
# ──────────────────────────────────────────────────────────────────────────
CHAIN_BLOCKLIST = [
    # vets
    "ivc", "evidensia", "cvs ", "vets4pets", "vetpartners", "medivet", "linnaeus",
    # dental
    "mydentist", "{my}dentist", "bupa dental", "portmandentex", "rodericks", "colosseum dental",
    # childcare
    "busy bees", "bright horizons", "kids planet", "monkey puzzle", "n family",
    # national trade franchises (in-house marketing)
    "british gas", "octopus energy", "eon ", "e.on", "ovo ",
]


def is_chain(name: str) -> bool:
    n = (name or "").lower()
    return any(token in n for token in CHAIN_BLOCKLIST)
