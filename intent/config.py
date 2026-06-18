"""
Intent Engine — configuration.

Thesis (locked with Dave, June 2026): we do NOT chase new/growing businesses.
We find ESTABLISHED businesses (10+ staff, real budget) that are LEAKING inbound
revenue right now — missing calls, slow to reply on any channel, sending paid
clicks to a broken/no website, or launching a new location blind. Then we route
each to the right offer, led by the AI voice receptionist + speed-to-lead.

Everything here is detectable from FREE public sources. No paid tools.
"""

# ──────────────────────────────────────────────────────────────────────────
# Qualification gate — "has money, big enough to have the problem"
# ──────────────────────────────────────────────────────────────────────────
SIZE_MIN_EMPLOYEES = 10          # hard floor — no 1–3 person sole traders
# A business qualifies if it clears the staff floor OR runs multiple locations
# (multi-site = budget + the jackpot expansion signal). For trades, multi-site
# is NOT required — 10+ staff single-site trades still qualify.
def qualifies(company) -> bool:
    if is_chain(company.get("name", "")):
        return False
    emp = company.get("employees")
    locs = company.get("locations", 1) or 1
    if locs >= 2:
        return True
    if emp is not None and emp >= SIZE_MIN_EMPLOYEES:
        return True
    # unknown size + single site + currently advertising = give benefit of doubt
    if emp is None and company.get("advertising"):
        return True
    return False

# ──────────────────────────────────────────────────────────────────────────
# Signal weights — the score measures "how much revenue are they leaking, and
# can we plug it". Inbound-leak signals dominate; expansion is the bonus.
# ──────────────────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    # ── inbound leak (→ AI receptionist + speed-to-lead) ──
    "missed_call_review": 38,   # public reviews complaining nobody answered / called back
    "slow_response":      25,   # FB "typically replies in a day", no fast channel
    "out_of_hours_gap":   16,   # urgent/emergency service but closed evenings/weekends
    "hiring_receptionist":20,   # advertising a receptionist/call-handler = feels the pain
    # ── paid-but-leaking (amplifier + budget proof) ──
    "ads_active":         15,   # paying for inbound = every dropped lead is wasted spend
    # ── website leak (→ website rebuild + speed-to-lead) ──
    "website_leak":       24,   # no site / not mobile / no SSL / slow, while advertising
    # ── expansion (→ new-location launch / jackpot) ──
    "new_location":       30,   # established operator opening another site
    "expansion_hiring":   14,   # hiring across multiple roles/sites
    # ── activity / throughput proxy ──
    "review_velocity":     8,
}

SIGNAL_TTL_DAYS = 150

def recency_multiplier(age_days: int) -> float:
    if age_days <= 14:
        return 1.0
    if age_days >= SIGNAL_TTL_DAYS:
        return 0.0
    return max(0.0, 1.0 - (age_days - 14) / (SIGNAL_TTL_DAYS - 14))

# ──────────────────────────────────────────────────────────────────────────
# Tiers
# ──────────────────────────────────────────────────────────────────────────
TIER_HOT, TIER_WARM = 60, 35

def tier_for(score: int) -> str:
    return "Hot" if score >= TIER_HOT else "Warm" if score >= TIER_WARM else "Watch"

# ──────────────────────────────────────────────────────────────────────────
# Offers — what we sell against each detected leak. Led by the AI receptionist.
# ──────────────────────────────────────────────────────────────────────────
OFFER_RECEPTIONIST = "AI Receptionist + Speed-to-Lead"
OFFER_WEBSITE = "Website rebuild + Speed-to-Lead"
OFFER_LAUNCH = "New-location launch"

INBOUND_SIGNALS = {"missed_call_review", "slow_response", "out_of_hours_gap", "hiring_receptionist"}

def primary_offer(signal_types) -> str:
    st = set(signal_types)
    if st & INBOUND_SIGNALS:
        return OFFER_RECEPTIONIST          # the lead offer, always wins if pain present
    if "website_leak" in st:
        return OFFER_WEBSITE
    if "new_location" in st:
        return OFFER_LAUNCH
    return OFFER_RECEPTIONIST               # default pitch

# ──────────────────────────────────────────────────────────────────────────
# Verticals — the sectors Dave sells to, the free source list to enumerate
# established firms, the channels customers flood them on (so we know where the
# leak is), and a sector-specific "why now" the actioning agent can use.
# ──────────────────────────────────────────────────────────────────────────
VERTICALS = {
    "aesthetic_clinic": {
        "label": "Aesthetic clinics",
        "channels": ["phone", "dm", "web_form"],
        "source": "Save Face / JCCP registers + Google Maps",
        "hook": "high-ticket bookings lost to slow DM/phone replies; consultations no-show without instant follow-up",
        "receptionist_roles": ["clinic receptionist", "patient coordinator", "front of house"],
    },
    "vet": {
        "label": "Veterinary practices",
        "channels": ["phone", "web_form"],
        "source": "RCVS (UK) / VCI (IE) registers + Google Maps; exclude IVC/CVS/VetPartners/Medivet",
        "hook": "emergency + booking calls overflow the front desk; out-of-hours calls go to a competitor",
        "receptionist_roles": ["veterinary receptionist", "client care", "front of house"],
    },
    "mot_centre": {
        "label": "MOT centres",
        "channels": ["phone"],
        "source": "DVSA active test-station CSV (free) + Google Maps",
        "hook": "booking + MOT-reminder calls missed while techs are on the ramp; March/Sept surges overwhelm the phone",
        "receptionist_roles": ["service advisor", "garage receptionist", "booking coordinator"],
    },
    "tyre": {
        "label": "Tyre & fast-fit",
        "channels": ["phone"],
        "source": "NTDA members + Google Maps",
        "hook": "puncture/urgent calls go to whoever answers first; seasonal changeover spikes flood the line",
        "receptionist_roles": ["service advisor", "depot receptionist"],
    },
    "car_dealer": {
        "label": "Independent car dealers",
        "channels": ["phone", "web_form", "sms"],
        "source": "AutoTrader/Motors dealer listings + Google Maps (independents, not franchised main dealers)",
        "hook": "web enquiries on stock decay in minutes; after-hours buyer interest never gets a reply",
        "receptionist_roles": ["sales executive", "showroom host", "business development"],
    },
    "heat_pump": {
        "label": "Heat-pump installers",
        "channels": ["phone", "web_form"],
        "source": "MCS Find-an-Installer (filter to 10+ staff, established)",
        "hook": "grant-driven enquiry surge swamps a field-based team; quotes requested faster than they can answer",
        "receptionist_roles": ["office manager", "scheduler", "customer coordinator"],
    },
    "solar": {
        "label": "Solar installers",
        "channels": ["phone", "web_form"],
        "source": "MCS / RECC registers (filter to 10+ staff)",
        "hook": "paying for solar leads (brutal CPCs) then dropping the call while on a roof",
        "receptionist_roles": ["office manager", "scheduler", "customer coordinator"],
    },
    "ev_charger": {
        "label": "EV-charger installers",
        "channels": ["phone", "web_form"],
        "source": "OZEV authorised-installer list + NICEIC (filter to 10+ staff)",
        "hook": "grant-funded install enquiries arrive by form and sit unanswered",
        "receptionist_roles": ["office manager", "scheduler"],
    },
    "recruitment": {
        "label": "Recruitment agencies",
        "channels": ["phone", "email", "web_form"],
        "source": "REC member directory + live-vacancy / consultant-hiring signals",
        "hook": "speed-to-candidate wins placements — first agency to call the applicant fills the role; slow reply = lost fee",
        "receptionist_roles": ["resourcer", "delivery consultant", "candidate manager"],
    },
}

DEFAULT_VERTICAL = "aesthetic_clinic"

def vertical_meta(vertical):
    if vertical in VERTICALS:
        return VERTICALS[vertical]
    return {"label": (vertical or "other").replace("_", " ").title(),
            "channels": ["phone"], "source": "", "hook": "win and keep more inbound enquiries",
            "receptionist_roles": ["receptionist"]}

# ──────────────────────────────────────────────────────────────────────────
# Corporate-chain blocklist — centralised marketing, not sellable. The franchised
# main dealers / national fast-fit chains are here so "car_dealer"/"tyre"/"mot"
# stay on independents and regional multi-site groups.
# ──────────────────────────────────────────────────────────────────────────
CHAIN_BLOCKLIST = [
    # vet
    "ivc", "evidensia", "cvs ", "vets4pets", "vetpartners", "medivet", "linnaeus",
    # tyre / fast-fit / MOT national
    "kwik fit", "kwik-fit", "halfords", "ats euromaster", "national tyres", "formula one autocentres",
    "f1 autocentres", "protyre", "hometyre",
    # car franchised / supermarkets
    "arnold clark", "evans halshaw", "sytner", "lookers", "marshall motor", "cazoo", "motorpoint", "cinch",
    # aesthetic chains
    "sk:n", "sk-n", "the harley medical", "transform hospital",
    # energy nationals
    "british gas", "octopus energy", "eon", "e.on", "ovo",
    # recruitment nationals (in-house marketing)
    "hays", "reed.co.uk", "adecco", "randstad", "pagegroup", "michael page", "robert walters",
]

def is_chain(name: str) -> bool:
    n = (name or "").lower()
    return any(tok in n for tok in CHAIN_BLOCKLIST)
