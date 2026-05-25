"""
Default mappings + mapping loader.

Every rule is (pattern, target). Patterns are matched case-insensitively after
light cleanup. The *first* matching rule wins, so order matters — put the more
specific rules before the generic ones. A mapping workbook uploaded by the
analyst OVERRIDES these defaults for the rule sheets it contains; unspecified
sheets fall back to the defaults below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


# -- Apartment type ----------------------------------------------------------
# Normalized targets: Studio, 1BR, 2BR, Companion, Semi-Private, Other
DEFAULT_APT_TYPE = [
    (r"\bstudio\b",                 "Studio"),
    (r"\bcompanion\b",              "Companion"),
    (r"\bsemi[\- ]?private\b",      "Semi-Private"),
    (r"\b1\s*b(ed)?r(oom)?\b",      "1BR"),
    (r"\bone\s*bedroom\b",          "1BR"),
    (r"\b2\s*b(ed)?r(oom)?\b",      "2BR"),
    (r"\btwo\s*bedroom\b",          "2BR"),
    (r"\bdeluxe\b",                 "Studio"),   # Oaks-style
    (r"\balcove\b",                 "Studio"),
    (r"\bsuite\b",                  "1BR"),
    # Briar Glen-style codes
    (r"\bdlxstd\b",                 "Studio"),   # Deluxe Studio
    (r"\bstd\b",                    "Studio"),
    (r"\bstu\b",                    "Studio"),   # Homestead-style: "STU"
    (r"\b1bed\b",                   "1BR"),
    (r"\b2bed\b",                   "2BR"),
    (r"\bs\s*sui\b",                "1BR"),     # Single Suite
    (r"\bd\s*sui\b",                "2BR"),     # Double Suite
]

# -- Bed status --------------------------------------------------------------
# Normalized targets: Occupied, Vacant, Preleased, Hold, Notice, Model, Down
DEFAULT_BED_STATUS = [
    # NTV (Notice To Vacate) must come before "occupied" — Homestead reports
    # "Occ w/ NTV" for residents on notice and we want that flagged as Notice,
    # not silently rolled into Occupied.
    (r"\bntv\b",                    "Notice"),
    (r"\boccupied\b",               "Occupied"),
    # "Prelease" must come before "vacant" — Homestead reports "Vacant w/ Prelease"
    # for empty units with a signed lease awaiting move-in. Preleased units offset
    # exposure (Section N on Rent Roll Recon) since they're already on the way to
    # being filled; collapsing them into plain Vacant would overstate risk.
    (r"\bprelease",                 "Preleased"),
    (r"\bvacant\b",                 "Vacant"),
    (r"\bempty\b",                  "Vacant"),
    (r"\bavailable\b",              "Vacant"),
    (r"\bhold\b",                   "Hold"),
    (r"\breserved\b",               "Hold"),
    (r"\bnotice\b",                 "Notice"),
    (r"\bmodel\b",                  "Model"),
    (r"\bdown\b",                   "Down"),
    (r"\bout of service\b",         "Down"),
]

# -- Payer type --------------------------------------------------------------
# Normalized targets: Private Pay, Medicaid, Medicare, Managed Care, VA Benefit,
#                     LTC Insurance, Self-Pay + Other
# Module-level fallback: Private Pay (RR — avoids false VA classifications).
# AR ingest constructs MappingSet(payer_fallback="Self-Pay + Other") at
# instantiation; RR behavior unchanged.
DEFAULT_PAYER = [
    (r"\bmedicaid\b",               "Medicaid"),
    (r"\bwaiver\b",                 "Medicaid"),
    # Medicare Advantage / MA plans are managed care — must come before bare medicare.
    (r"\bmedicare\s*advantage\b",   "Managed Care"),
    (r"\bma\s*plan\b",              "Managed Care"),
    (r"\bmedicare\b",               "Medicare"),
    (r"\bmanaged\s*care\b",         "Managed Care"),
    (r"\bmco\b",                    "Managed Care"),
    (r"\bva\b",                     "VA Benefit"),
    (r"\bveteran",                  "VA Benefit"),
    (r"\bltc\b",                    "LTC Insurance"),
    (r"\blong[\- ]?term\s*care\b",  "LTC Insurance"),
    (r"\binsurance\b",              "LTC Insurance"),
    (r"\bprimary resident\b",       "Private Pay"),
    (r"\bprivate\b",                "Private Pay"),
    (r"\bresident\b",               "Private Pay"),
    (r"\bself[\- ]?pay\b",          "Private Pay"),
]
PAYER_FALLBACK = "Private Pay"

# -- Care level --------------------------------------------------------------
# Normalized targets: Level 1, Level 2, Level 3, Level 4, Level 5, Level 6+
# Source levels 6+ map to the 'Level 6+' bucket (their own analytical group;
# typically premium-rate residents). 'Basic' maps to Level 1 (lowest tier).
# Independent / Level 0 / Base have no care level and map to "" (blank).
DEFAULT_CARE_LEVEL = [
    (r"\blevel\s*1\b",              "Level 1"),
    (r"\blevel\s*2\b",              "Level 2"),
    (r"\blevel\s*3\b",              "Level 3"),
    (r"\blevel\s*4\b",              "Level 4"),
    (r"\blevel\s*5\b",              "Level 5"),
    # Level 6 and above all flow into the Level 6+ bucket
    (r"\blevel\s*6\b",              "Level 6+"),
    (r"\blevel\s*7\b",              "Level 6+"),
    (r"\blevel\s*[89]\b",           "Level 6+"),
    (r"\blevel\s*1[0-9]\b",         "Level 6+"),
    # Oaks Memory Care acuity tiers — "Comfort Care 1/2/3/4" parallels Level 1-4
    (r"\bcomfort\s*care\s*1\b",     "Level 1"),
    (r"\bcomfort\s*care\s*2\b",     "Level 2"),
    (r"\bcomfort\s*care\s*3\b",     "Level 3"),
    (r"\bcomfort\s*care\s*4\b",     "Level 4"),
    (r"\bcomfort\s*care\s*5\b",     "Level 5"),
    (r"\bcomfort\s*care\s*[6-9]\b", "Level 6+"),
    # Word-based tiers
    (r"\bbasic\b",                  "Level 1"),
    (r"\blow\b",                    "Level 2"),
    (r"\bmoderate\b",               "Level 3"),
    (r"\bmedium\b",                 "Level 3"),
    (r"\bhigh\b",                   "Level 4"),
    (r"\bextensive\b",              "Level 5"),
    (r"\btotal\b",                  "Level 6+"),
    # No care
    (r"\blevel\s*0\b",              ""),
    (r"\bbase\b",                   ""),
    (r"\bindependent\b",            ""),
]

# -- Care Type (setting) -----------------------------------------------------
# Normalized targets: IL, AL, MC
# Requires an explicit Care Type / Unit / Building / Wing column in source.
# If not found or no rule matches, value is left blank and flagged in exceptions.
#
# IMPORTANT: Order matters — first match wins. Memory Care patterns must come
# before Assisted Living patterns because "Assisted Living Memory Care" should
# resolve to MC, not AL.
DEFAULT_CARE_TYPE = [
    # Memory Care variants (must come first — most specific)
    (r"\bmemory\s*care\b",          "MC"),
    (r"\bmc\b",                     "MC"),
    (r"\bdementia\b",               "MC"),
    (r"\balzheimer",                "MC"),
    (r"\bdm\b",                     "MC"),    # Briar Glen code: Alzheimer's Care
    (r"\bdu7?\b",                   "MC"),    # Briar Glen code: Special Care
    (r"\bspecial\s*care\b",         "MC"),
    (r"\bhorizons\b",               "MC"),    # Oaks at Beaufort: Memory Care wing
    (r"\bcomfort\s*care\b",         "MC"),    # Oaks Memory Care acuity vocabulary
    # Assisted Living variants
    (r"\bassisted\s*living\b",      "AL"),
    (r"\bal\b",                     "AL"),
    (r"\bltc\b",                    "AL"),    # Long-Term Care typically = AL setting
    (r"\blong[\- ]?term\s*care\b",  "AL"),
    # Independent Living variants
    (r"\bindependent\s*living\b",   "IL"),
    (r"\bil\b",                     "IL"),
    (r"\bindependent\b",            "IL"),
]

# -- Care bucket detection (for Other LOC $ auto-catch) ----------------------
# Maps column-header substrings to normalized care buckets.
# Any monthly-total column not matched here flows into "Other LOC $".
#
# v1.17.0 (UW-BACKLOG BL-0003) — Other LOC $ split into named per-fee buckets:
# Meal Plan $ / Scooter Fee $ / Housekeeping $ / Laundry $ / Pet $. Each gets
# its own column on Rent Roll Input (substrate v0.1.13: AC-AG). Section M's
# RR-side capture (M2/M4) uses these to compute per-fee capture rates and
# implied rates vs. the published schedule. Diabetes / Misc / anything else
# care-related but not in the named buckets stays in Other LOC $ (the
# fallback). The 4 named-bucket rules use word boundaries (\b) to avoid
# spurious matches in column names like "Misc. (no laundry charge)".
DEFAULT_CARE_BUCKETS = [
    # Care-revenue buckets (acuity / nursing) ---------------------------
    (r"assisted\s*living",          "Care Level $"),
    (r"memory\s*care",              "Care Level $"),  # Oaks: MC level $ is care revenue, not ancillary
    (r"\bal\s*care\b",              "Care Level $"),
    (r"^care\s*charges?\b",         "Care Level $"),  # Briar Glen-style
    (r"^care\s*services?\b",        "Care Level $"),
    (r"med\s*mgmt",                 "Med Mgmt $"),
    (r"medication",                 "Med Mgmt $"),
    (r"pharmacy",                   "Pharmacy $"),
    (r"\brx\b",                     "Pharmacy $"),
    # Per-fee ancillary buckets (v1.17.0 — UW-BACKLOG BL-0003) ----------
    (r"\bmeal\b",                   "Meal Plan $"),
    (r"\bscooter\b",                "Scooter Fee $"),
    (r"\bmobility\b",               "Scooter Fee $"),   # mobility-aid bundles with scooter
    (r"\btransport\b",              "Scooter Fee $"),   # resident-transport bundles with scooter
    (r"\bhousekeeping\b",           "Housekeeping $"),
    (r"\bh\s*/\s*k\b",              "Housekeeping $"),  # Homestead-style "H/K"
    (r"\blaundry\b",                "Laundry $"),
    (r"\bpet\b",                    "Pet $"),
    # Diabetes / Misc / unmatched care headers fall through to "Other LOC $"
    # (the classify_care_bucket fallback in this same module).
]


# ---------------------------------------------------------------------------
@dataclass
class MappingSet:
    """Container for active mapping rules (defaults merged with user overrides)."""
    apt_type: list = field(default_factory=lambda: list(DEFAULT_APT_TYPE))
    bed_status: list = field(default_factory=lambda: list(DEFAULT_BED_STATUS))
    payer: list = field(default_factory=lambda: list(DEFAULT_PAYER))
    care_level: list = field(default_factory=lambda: list(DEFAULT_CARE_LEVEL))
    care_type: list = field(default_factory=lambda: list(DEFAULT_CARE_TYPE))
    care_buckets: list = field(default_factory=lambda: list(DEFAULT_CARE_BUCKETS))
    payer_fallback: str = PAYER_FALLBACK


def _apply_rules(value, rules, default=None):
    """Return (normalized_value, matched_pattern). First match wins."""
    if value is None:
        return default, None
    s = str(value).strip()
    if not s:
        return default, None
    for pat, target in rules:
        if re.search(pat, s, flags=re.IGNORECASE):
            return target, pat
    return None, None  # explicit no-match so the caller can flag "unmapped"


def normalize_apt(v, m: MappingSet):
    out, rule = _apply_rules(v, m.apt_type)
    return (out if out is not None else (str(v).strip() if v is not None else "")), rule


def normalize_bed_status(v, m: MappingSet):
    out, rule = _apply_rules(v, m.bed_status)
    return (out if out is not None else (str(v).strip() if v is not None else "")), rule


def normalize_payer(v, m: MappingSet):
    out, rule = _apply_rules(v, m.payer)
    if out is None:
        return m.payer_fallback, "__fallback__"
    return out, rule


def normalize_care_level(v, m: MappingSet):
    """Returns (normalized_level, matched_rule). Blank if no match or no care."""
    out, rule = _apply_rules(v, m.care_level)
    return (out if out is not None else ""), rule


def normalize_care_type(v, m: MappingSet):
    """Returns (normalized_type, matched_rule). Blank if no match — caller should flag."""
    out, rule = _apply_rules(v, m.care_type)
    return (out if out is not None else ""), rule


def classify_care_bucket(col_header: str, m: MappingSet) -> str:
    """Return the normalized bucket name for a care/ancillary column header.
    Unmapped columns return 'Other LOC $' (auto-catch)."""
    out, _ = _apply_rules(col_header, m.care_buckets)
    return out or "Other LOC $"


# ---------------------------------------------------------------------------
def load_mapping_workbook(path_or_buffer) -> MappingSet:
    """Load mapping overrides from an uploaded .xlsx.

    Expected sheets (all optional):
      Apartment_Type_Rules  [Source, Normalized]
      Bed_Status_Rules      [Source, Normalized]
      Payer_Type_Rules      [Source, Normalized]
      Care_Level_Rules      [Source, Normalized]
      Care_Bucket_Rules     [Source_Contains, Maps_To]

    Any missing sheet falls back to defaults.
    """
    m = MappingSet()
    try:
        xl = pd.ExcelFile(path_or_buffer)
    except Exception:
        return m

    def _load(sheet_name, target_attr):
        if sheet_name not in xl.sheet_names:
            return
        df = xl.parse(sheet_name).dropna(how="all")
        if df.shape[1] < 2:
            return
        # Treat user rules as literal substrings (case-insensitive) — analysts
        # shouldn't have to write regex. We escape and wrap in \b where sensible.
        rules = []
        for _, row in df.iterrows():
            src = row.iloc[0]
            tgt = row.iloc[1]
            if pd.isna(src) or pd.isna(tgt):
                continue
            pat = re.escape(str(src).strip())
            rules.append((pat, str(tgt).strip()))
        if rules:
            # User rules take precedence; defaults remain as fallback.
            setattr(m, target_attr, rules + getattr(m, target_attr))

    _load("Apartment_Type_Rules", "apt_type")
    _load("Bed_Status_Rules",     "bed_status")
    _load("Payer_Type_Rules",     "payer")
    _load("Care_Level_Rules",     "care_level")
    _load("Care_Type_Rules",      "care_type")
    _load("Care_Bucket_Rules",    "care_buckets")
    return m
