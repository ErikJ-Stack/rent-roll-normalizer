"""
MF (multifamily) closed vocabularies + COA classification.

The MF counterpart of `mappings.py`. The centerpiece is the COA -> `_StdCOA`
classifier, promoted from the validated seed at
`tools/mf_uw_template/coa_seed.csv` (built + 100%-coverage-validated across 5
operator T-12 formats — see `tools/mf_uw_template/COA-SEED.md`).

Public API:
    classify_t12_account(acct, name) -> str            # _StdCOA bucket
    bucket_side(bucket) -> "income" | "expense" | "excluded" | "control"
    INCOME_BUCKETS / EXPENSE_BUCKETS / CONTROL_BUCKETS  (frozensets)
    normalize_status(raw) -> str                        # RR status taxonomy
    STD_BUCKETS                                         # ordered _StdCOA list

This module is import-time cheap (loads one small CSV) and has no Excel/openpyxl
dependency, so parsers and tests can use it freely.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

_SEED_PATH = Path(__file__).resolve().parent / "tools" / "mf_uw_template" / "coa_seed.csv"

# ---------------------------------------------------------------------------
# _StdCOA bucket inventory + income/expense side (from the model's _StdCOA tab)
# ---------------------------------------------------------------------------
INCOME_BUCKETS = frozenset({
    "Gross Potential Rent", "Gain/Loss on Market Rent", "Vacancy Loss",
    "Down Units Loss", "Employee Units", "Concessions", "Delinquency Change",
    "Write-offs / Bad Debt", "Prepaid Rent Change", "MTM Fees",
    "Application Fees", "Late Fees", "Utility Reimbursement", "Pet Fees",
    "Parking Income", "Amenity Fees", "Admin Fees", "Insurance Pass-Thru",
    "Misc Other Income", "Renter's Insurance", "Reimbursement — Internet",
    "Storage / Common Bins", "Package Service / Lockers", "Lease Lock Fee",
    "Valet Trash", "Lease Break Fee",
})
EXPENSE_BUCKETS = frozenset({
    "Repairs & Maintenance", "Contract Services", "Landscaping", "Pest Control",
    "Pool / Amenity Maintenance", "Make-Ready / Turnover", "Payroll — On-Site",
    "Leasing & Marketing", "General & Administrative", "Legal / Eviction",
    "Insurance", "Real Estate Taxes", "Utilities — Electric", "Utilities — Gas",
    "Utilities — Water/Sewer", "Utilities — Trash", "Utilities — Internet/Cable",
    "Management Fee",
})
UNMAPPED = "— UNMAPPED —"
EXCLUDED = "— EXCLUDED (non-OpEx) —"
CONTROL_BUCKETS = frozenset({UNMAPPED, EXCLUDED})

STD_BUCKETS = tuple(INCOME_BUCKETS) + tuple(EXPENSE_BUCKETS) + (UNMAPPED, EXCLUDED)


def bucket_side(bucket: str) -> str:
    if bucket in INCOME_BUCKETS:
        return "income"
    if bucket in EXPENSE_BUCKETS:
        return "expense"
    if bucket == EXCLUDED:
        return "excluded"
    return "control"


# ---------------------------------------------------------------------------
# COA seed loader (single source of truth = coa_seed.csv)
# ---------------------------------------------------------------------------
def _load_seed(path: Path = _SEED_PATH):
    acct_root: dict[int, str] = {}
    excluded_lo = excluded_hi = None
    name_rules: list[tuple[re.Pattern, str]] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tier, key, bucket = row["tier"], row["key"], row["std_bucket"]
            if tier == "acct_root":
                acct_root[int(key)] = bucket
            elif tier == "acct_range":
                lo, hi = key.split("-")
                excluded_lo, excluded_hi = int(lo), int(hi)
            elif tier == "name_regex":
                name_rules.append((re.compile(key, re.IGNORECASE), bucket))
    return acct_root, (excluded_lo, excluded_hi), name_rules


_ACCT_ROOT, (_EXCL_LO, _EXCL_HI), _NAME_RULES = _load_seed()


def _acct_root(acct) -> int | None:
    m = re.match(r"(\d{4,5})", str(acct) if acct is not None else "")
    return int(m.group(1)) if m else None


def classify_t12_account(acct=None, name: str | None = None) -> str:
    """Classify one raw T-12 GL line into a `_StdCOA` bucket.

    Tiers (first hit wins): exact Yardi 5-digit account root -> 70000-89999
    EXCLUDED range -> ordered name-regex fallback -> UNMAPPED.
    """
    root = _acct_root(acct)
    if root is not None:
        if _EXCL_LO is not None and _EXCL_LO <= root <= _EXCL_HI:
            return EXCLUDED
        if root in _ACCT_ROOT:
            return _ACCT_ROOT[root]
    s = name or ""
    for pat, bucket in _NAME_RULES:
        if pat.search(s):
            return bucket
    return UNMAPPED


# ---------------------------------------------------------------------------
# RR status taxonomy — operator status string -> model COUNTIF vocabulary.
# Near-identity (decision SPEC-MF §2.7.4); normalize + map the few that differ,
# unknowns flagged by the caller.
# ---------------------------------------------------------------------------
_STATUS_RULES = [
    (r"occupied.*no notice|occupied.*current", "Occupied No Notice"),
    (r"occupied.*notice|notice", "Occupied On Notice"),
    (r"occupied", "Occupied No Notice"),
    (r"vacant.*not ready|vacant.*unrented.*not", "Vacant Unrented Not Ready"),
    (r"vacant.*ready|vacant.*unrented", "Vacant Unrented Ready"),
    (r"vacant.*(lease|rent)", "Vacant Leased"),
    (r"\bdown\b|off.?line", "Down"),
    (r"model", "Model"),
    (r"employee", "Employee"),
    (r"office", "Office"),
    (r"vacant", "Vacant Unrented Ready"),
]
UNMAPPED_STATUS = "— UNMAPPED status —"


# ---------------------------------------------------------------------------
# RR charge-code -> per-unit ancillary bucket (model Rent Roll Analysis cols
# W–AK). Recognized non-rent charge codes break out into their own column;
# Base Rent / Subsidy Rent (core contractual rent) stay folded in the scheduled
# total only (return None). Unrecognized codes also return None (kept in the
# scheduled total, never force-bucketed).
# ---------------------------------------------------------------------------
ANCILLARY_BUCKETS = (
    "mtm", "application", "late", "utility_reimb", "pet", "parking", "amenity",
    "admin", "insurance_passthru", "misc", "storage", "package", "lease_lock",
    "valet", "lease_break",
)
_CHARGE_RULES = [
    (r"amenity", "amenity"),
    (r"\bpet\b", "pet"),
    (r"parking|carport|garage", "parking"),
    (r"storage", "storage"),
    (r"valet", "valet"),
    (r"trash|rubbish", "utility_reimb"),
    (r"util|rubs|water|sewer|electric|\bgas\b|reimburse", "utility_reimb"),
    (r"\bnsf\b|late", "late"),
    (r"applicat", "application"),
    (r"month.?to.?month|\bmtm\b", "mtm"),
    (r"admin", "admin"),
    (r"renter.?s insurance|insurance", "insurance_passthru"),
    (r"lease lock", "lease_lock"),
    (r"package|locker", "package"),
    (r"lease (break|cancel|termin)|early term", "lease_break"),
    (r"base rent|subsidy", "__core__"),   # rent — stays in scheduled total
]


def classify_charge_code(code) -> str | None:
    """Map an RR charge-code string to a W–AK ancillary bucket, or None for
    core rent (base/subsidy) and unrecognized codes (kept in the scheduled total)."""
    s = str(code).strip().lower() if code not in (None, "") else ""
    if not s:
        return None
    for pat, bucket in _CHARGE_RULES:
        if re.search(pat, s):
            return None if bucket == "__core__" else bucket
    return None


def normalize_status(raw) -> str:
    s = str(raw).strip().lower() if raw not in (None, "") else ""
    if not s:
        return ""
    for pat, val in _STATUS_RULES:
        if re.search(pat, s):
            return val
    return UNMAPPED_STATUS
