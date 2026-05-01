"""
Rent roll normalization engine.

Produces a bed-level normalized dataframe from a raw rent roll workbook whose
header is somewhere in the first ~15 rows. Handles the parent-apartment /
child-bed layout and auto-catches unrecognized monthly care columns into
Other LOC $.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from mappings import (
    MappingSet,
    classify_care_bucket,
    normalize_apt,
    normalize_bed_status,
    normalize_care_level,
    normalize_care_type,
    normalize_payer,
)


HEADER_SCAN_ROWS = 20  # search the first 20 rows for the header

# Signature tokens we expect to see in the header row. Weighted scoring.
HEADER_SIGNALS = {
    "unit": 2,
    "apartment": 3,
    "apt": 2,
    "room": 2,
    "bed": 3,
    "resident": 3,
    "status": 1,
    "market": 2,
    "actual": 2,
    "rate": 1,
    "payer": 2,
    "move": 1,
    "move in": 3,
    "move-in": 3,
    "occupancy": 1,
    "type": 1,
    "level": 1,
}

# Column-name patterns for extracting canonical fields from the detected header.
# First match wins. Patterns are matched against a lower-cased, whitespace-
# collapsed version of the header string.
FIELD_PATTERNS: Dict[str, List[str]] = {
    "unit":            [r"^unit(\s*#|\s*number)?$", r"^unit$", r"^building$"],
    "apartment":       [r"^apartment$", r"^apt(\s*#|\s*number)?$",
                        r"^room(\s*#|\s*number)?$", r"^suite$",
                        r"^unit\s*$"],  # trailing-space "Unit " (Briar Glen)
    "apt_type":        [r"^apartment\s*type$", r"^apt\s*type$",
                        r"^unit\s*type$", r"^floor\s*plan$"],
    "bed":             [r"^bed$", r"^bed\s*#$", r"^bed\s*letter$",
                        r"^privacy\s*level$"],   # Briar Glen: PRI/SPA/SPB
    "potential_occ":   [r"^potential\s*occupancy$", r"^max\s*occupancy$",
                        r"^unit\s*capacity$"],   # Briar Glen
    "first_name":      [r"^resident\s*first\s*name$", r"^first\s*name$"],
    "last_name":       [r"^resident\s*last\s*name$", r"^last\s*name$"],
    "resident_full":   [r"^resident(\s*name)?$", r"^resident\s*full\s*name$",
                        r"^tenant$"],
    "payer":           [r"^payer$", r"^payer\s*type$", r"^payor$"],
    "market_rate":     [r"^market\s*rate$", r"^gross\s*rent$",
                        r"^scheduled\s*rent$",
                        r"^unit\s*market\s*rate$"],   # Briar Glen
    "actual_rate":     [r"^actual\s*rate$", r"^net\s*rent$",
                        r"^contract\s*rent$", r"^current\s*rent$",
                        r"^accommodation(\s*service)?$"],   # Briar Glen
    "discount":        [r"^discount$"],
    "move_in":         [r"^move\s*in$", r"^move[\- ]in\s*date$",
                        r"^lease\s*start$",
                        r"^resident\s*move\s*in\s*date$"],   # Briar Glen
    "move_out":        [r"^estimated\s*move\s*out$", r"^move\s*out$",
                        r"^lease\s*end$"],
    "bed_status":      [r"^bed\s*status$"],
    "apt_status":      [r"^apartment\s*status$", r"^unit\s*status$"],
    "sqft":            [r"^sq\s*ft$", r"^square\s*feet$", r"^size$",
                        r"^unit\s*sqft$"],   # Briar Glen
    "al_care_level":   [r"^al\s*care\s*level$",
                        r".*assisted\s*living.*level$",
                        r"^care\s*level$"],   # Briar Glen has 2-letter codes here
    "care_type":       [r"^care\s*type$", r"^level\s*of\s*care$", r"^loc$",
                        r"^wing$", r"^community\s*type$", r"^building$",
                        r"^license\s*type$", r"^care\s*setting$"],
}


# ---------------------------------------------------------------------------
def _clean_header(x) -> str:
    """Lower, collapse whitespace, strip control chars."""
    if x is None:
        return ""
    s = str(x)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _score_row_as_header(row_values: List) -> int:
    """How strongly does this row look like a header row?"""
    score = 0
    cleaned = [_clean_header(v) for v in row_values]
    joined = " | ".join(cleaned)
    for token, weight in HEADER_SIGNALS.items():
        if re.search(rf"\b{re.escape(token)}\b", joined):
            score += weight
    # Penalty for numeric-looking rows (probably data, not header)
    num_like = sum(1 for v in row_values
                   if isinstance(v, (int, float))
                   and not (isinstance(v, bool)))
    score -= num_like
    return score


def detect_header_row(df_raw: pd.DataFrame) -> int:
    """Return the 0-indexed row that looks most like a header."""
    best_row, best_score = 0, -999
    limit = min(HEADER_SCAN_ROWS, len(df_raw))
    for i in range(limit):
        row = df_raw.iloc[i].tolist()
        s = _score_row_as_header(row)
        if s > best_score:
            best_row, best_score = i, s
    return best_row


def _field_for_header(h: str) -> Optional[str]:
    """Classify a cleaned header string into a canonical field name, or None."""
    for field, patterns in FIELD_PATTERNS.items():
        for p in patterns:
            if re.fullmatch(p, h):
                return field
    return None


# ---------------------------------------------------------------------------
@dataclass
class CareColGroup:
    """A detected care/ancillary column group, e.g. 'Med Mgmt' group."""
    bucket: str             # normalized bucket name: 'Med Mgmt $', 'Pharmacy $', 'Care Level $', 'Other LOC $'
    level_col: Optional[str] = None
    amount_col: Optional[str] = None
    discount_col: Optional[str] = None
    monthly_col: Optional[str] = None
    source_prefix: Optional[str] = None  # for the mapping reference audit


def _strip_bucket_suffix(h_clean: str) -> Tuple[str, str]:
    """Split a header like 'foo bar level' into ('foo bar', 'level')."""
    for suffix in ["(month", "month total", "level", "amount", "discount"]:
        if h_clean.endswith(suffix):
            return h_clean[: -len(suffix)].strip(" -:"), suffix
    # Handle '(january 2026)' style
    m = re.search(r"\((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s*\d{4}\)\s*$", h_clean)
    if m:
        return h_clean[: m.start()].strip(" -:"), "(month"
    return h_clean, ""


def detect_care_groups(headers: List[str], mappings: MappingSet) -> Tuple[List[CareColGroup], Dict[str, str]]:
    """Scan headers, group care/ancillary columns by prefix, classify into buckets.

    Returns (groups, audit) where audit maps each care-related header to its bucket.
    """
    # First pass: group headers by prefix.
    by_prefix: Dict[str, CareColGroup] = {}
    audit: Dict[str, str] = {}

    for h in headers:
        hc = _clean_header(h)
        if not hc:
            continue
        # Skip obvious non-care columns
        if hc in {"market rate", "actual rate", "discount"}:
            continue
        # Skip concession-equivalent columns — handled separately by detect_concession_cols
        if any(re.search(p, hc) for p in _CONCESSION_PATTERNS):
            continue
        prefix, suffix = _strip_bucket_suffix(hc)

        # Case A: header has a recognized suffix (e.g., "AL Care (January 2026)")
        # -> the prefix names the bucket
        if suffix:
            # 'discount' as a suffix alone (no prefix) is the base concession discount
            if prefix == "" and suffix == "discount":
                continue
            # Concessions handled separately — skip here
            if "concession" in prefix:
                continue
            # Grand-total / roll-up columns — skip (they'd double-count)
            if prefix in {"", "total", "monthly forecast", "total charges",
                          "total rent", "total monthly", "grand total"}:
                continue
            if prefix.startswith("total ") or prefix.endswith(" total"):
                continue

            bucket = classify_care_bucket(prefix, mappings)
            g = by_prefix.setdefault(prefix, CareColGroup(bucket=bucket, source_prefix=prefix))
            if suffix == "level":
                g.level_col = h
            elif suffix == "amount":
                g.amount_col = h
            elif suffix == "discount":
                g.discount_col = h
            elif suffix in {"(month", "month total"}:
                g.monthly_col = h
            audit[h] = bucket

        # Case B: standalone care/ancillary column (no suffix) — Briar Glen-style
        # "Care Charges", "Med Mgmt", "Other Charges". The full header IS the
        # monthly column. We classify by whether it matches a care-bucket
        # pattern explicitly.
        else:
            # Skip obvious non-care fields and structural columns
            skip_exact = {
                "unit", "apartment", "apt", "room", "bed", "resident", "payer",
                "status", "move in", "move-in", "move out", "move-out",
                "birth date", "rate type", "privacy level", "unit type",
                "unit capacity", "unit count", "unit sqft", "sq ft", "sqft",
                "care level", "level", "first name", "last name",
                "concession", "concession end date", "concession (month",
                "potential occupancy",
            }
            if hc in skip_exact:
                continue
            # Skip columns that already match a non-bucket field pattern
            if _field_for_header(hc):
                continue
            # Only treat as a care bucket if it matches a known care-bucket pattern
            # OR appears care-related (heuristic: contains "charge", "service",
            # "care", "medication", "pharmacy", "incentive", "discount" but
            # we exclude pure "discount"/"incentive" which are typically negative
            # adjustments rather than care revenue).
            looks_care = any(kw in hc for kw in [
                "care charge", "care service", "med mgmt", "medication",
                "pharmacy", "level of care", "ancillary", "service charge",
                "other charge",
            ])
            if not looks_care:
                continue

            bucket = classify_care_bucket(hc, mappings)
            # Use the header itself as the prefix to keep groups distinct
            g = by_prefix.setdefault(hc, CareColGroup(bucket=bucket, source_prefix=hc))
            g.monthly_col = h
            audit[h] = bucket

    # Only keep groups that have at least a monthly column (that's the dollar signal).
    groups = [g for g in by_prefix.values() if g.monthly_col is not None]
    return groups, audit


# Concession-equivalent column patterns. ANY column whose cleaned header matches
# one of these is treated as a concession source. Multiple columns from the same
# row are summed into a single Concession $ in the output.
#
# Sign convention: source values are PRESERVED (typically negative for discounts).
# Total Monthly Revenue uses `actual + LOC + conc_amt`, so a negative concession
# correctly reduces revenue.
_CONCESSION_PATTERNS = [
    r"\bconcession\b",                  # generic — covers "Concession", "Concession (January 2026)"
    r"\brecurring\s+discount",          # Briar Glen
    r"\bone[- ]time\s+incentive",       # Briar Glen
    r"\bdiscount\b.*\(month",           # generic monthly-suffixed discount
]


def detect_concession_cols(headers: List[str]) -> Tuple[List[str], Optional[str]]:
    """Return (list_of_monthly_concession_cols, concession_end_date_col).

    Multiple columns may be detected — Briar Glen has both 'Recurring Discounts'
    and 'One-Time Incentives' alongside the generic 'Concession' pattern other
    operators use. All matched columns are summed into Concession $ in the output.
    """
    monthly_cols: List[str] = []
    end_date: Optional[str] = None
    for h in headers:
        hc = _clean_header(h)
        # End-date column for concessions (singular)
        if "concession" in hc and "end date" in hc:
            end_date = h
            continue
        # Monthly amount column — match against any of the patterns
        for pat in _CONCESSION_PATTERNS:
            if re.search(pat, hc):
                monthly_cols.append(h)
                break
    return monthly_cols, end_date


# ---------------------------------------------------------------------------
def _to_num(x) -> float:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace("$", "").replace(",", "")
    if s in {"", "-", "--", "N/A", "n/a"}:
        return 0.0
    # Parenthesized negatives
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def _blank_if_zero(v):
    """Return None for numeric values within 1e-9 of zero, else pass through.

    Applied to per-bed dollar charge columns (Concession $, Care Level $,
    Med Mgmt $, Pharmacy $, Other LOC $, Total LOC $) so that 'no charge'
    renders as truly blank — not 0 — in Excel and Streamlit. This stops
    zero-fills from inflating COUNT() / COUNTIF() on those columns.

    NOT applied to rates (Market Rate, Actual Rate, Rate Gap) or to
    Total Monthly Revenue — for those, 0 has informational meaning
    (e.g. vacant beds typically have $0 actual rate).
    """
    if v is None:
        return None
    try:
        if abs(float(v)) < 1e-9:
            return None
    except (TypeError, ValueError):
        return v
    return v


def _row_has_apartment(row: pd.Series, field_map: Dict[str, str]) -> bool:
    unit_col = field_map.get("unit")
    apt_col = field_map.get("apartment")
    bed_col = field_map.get("bed")
    has_unit = unit_col and pd.notna(row.get(unit_col)) and str(row.get(unit_col)).strip() != ""
    has_apt = apt_col and pd.notna(row.get(apt_col)) and str(row.get(apt_col)).strip() != ""
    has_bed = bed_col and pd.notna(row.get(bed_col)) and str(row.get(bed_col)).strip() != ""
    return (has_unit or has_apt) and not has_bed


def _row_has_bed(row: pd.Series, field_map: Dict[str, str]) -> bool:
    bed_col = field_map.get("bed")
    if not bed_col:
        return False
    v = row.get(bed_col)
    return pd.notna(v) and str(v).strip() != ""


def _row_is_self_contained_unit(row: pd.Series, field_map: Dict[str, str]) -> bool:
    """A row that contains BOTH apartment-level info (unit/apartment) AND
    a resident-or-bed-status signal on the same row.

    This is the Briar Glen single-bed pattern: one row per unit with everything
    populated, no separate child bed row.

    Strict definition: requires a RESIDENT name (or *Vacant marker) on the same
    row as the unit. Rates alone are NOT enough because Salem-style formats
    legitimately put rates on parent rows above the bed children.
    """
    has_apt_id = (
        (field_map.get("apartment") and
         pd.notna(row.get(field_map.get("apartment"))) and
         str(row.get(field_map.get("apartment"))).strip() != "")
        or
        (field_map.get("unit") and
         pd.notna(row.get(field_map.get("unit"))) and
         str(row.get(field_map.get("unit"))).strip() != "")
    )
    if not has_apt_id:
        return False

    # Self-contained ONLY if resident-identifying data is present.
    # NOT considered: rates (Salem puts rates on parent rows), bed letter
    # (that's the child-bed signal we use elsewhere).
    resident_signals = ["resident_full", "first_name", "last_name"]
    for sig in resident_signals:
        col = field_map.get(sig)
        if col and pd.notna(row.get(col)):
            v = str(row.get(col)).strip()
            if v and v.lower() != "nan":
                return True
    return False


# ---------------------------------------------------------------------------
@dataclass
class NormalizeResult:
    normalized: pd.DataFrame        # full bed-level detail
    condensed: pd.DataFrame         # 18-col analyst view (user-specified order)
    mapping_audit: pd.DataFrame     # rule-by-rule trail of what got mapped
    source_headers: List[str]
    header_row_idx: int
    care_groups: List[CareColGroup]
    unmapped: Dict[str, List[str]]  # per-category list of unmapped source values
    property_care_type_default: str = ""  # what default was applied (if any)
    pre_clean_stats: dict = None    # what the pre-cleaner stripped


CONDENSED_COLUMNS = [
    "Unit #", "Room #", "Sq Ft", "Care Type", "Status", "Apt Type",
    "Market Rate", "Actual Rate", "Concession $", "Concession End Date",
    "Care Level", "Care Level $", "Med Mgmt $", "Pharmacy $",
    "Other LOC $", "Payer Type", "Move-in Date", "Resident Name",
]


def normalize_rent_roll(
    xlsx_bytes_or_path,
    sheet_name: Optional[str] = None,
    mappings: Optional[MappingSet] = None,
    property_care_type_default: Optional[str] = None,
) -> NormalizeResult:
    """
    property_care_type_default: If set to 'IL', 'AL', or 'MC', any bed without
    an explicit source Care Type value falls back to this value. Source values
    always win over the default.
    """
    mappings = mappings or MappingSet()
    # Sanitize the default — only IL/AL/MC are accepted; anything else means "no default"
    valid_defaults = {"IL", "AL", "MC"}
    prop_default = (property_care_type_default or "").strip().upper()
    if prop_default not in valid_defaults:
        prop_default = ""

    # --- Read raw ----------------------------------------------------------
    xl = pd.ExcelFile(xlsx_bytes_or_path)
    if sheet_name is None:
        # Smart sheet selection: prefer "Details" if it exists (Salem format),
        # otherwise score all sheets and pick the one most likely to have
        # rent roll data based on:
        #   - row count (rent rolls are typically 30+ rows)
        #   - column count (rent rolls have many columns)
        #   - presence of header signals (Unit, Resident, Apartment, etc.)
        # Avoids picking tiny "Document map" or legend sheets as the default.
        if "Details" in xl.sheet_names:
            sheet_name = "Details"
        elif len(xl.sheet_names) == 1:
            sheet_name = xl.sheet_names[0]
        else:
            best_sheet, best_score = xl.sheet_names[0], -999
            for sn in xl.sheet_names:
                df_sn = xl.parse(sn, header=None, dtype=object, nrows=20)
                # Score: rows × cols × header-signal hits
                rows = len(df_sn)
                cols = df_sn.shape[1] if not df_sn.empty else 0
                # Header signal scan: check first 20 rows for rent-roll keywords
                signal_hits = 0
                if rows > 0 and cols > 0:
                    sample_text = " ".join(
                        str(v).lower() for row in df_sn.iloc[:20].itertuples(index=False)
                        for v in row if v is not None
                    )
                    for keyword in ["unit", "apartment", "resident", "bed",
                                     "rate", "move in", "care level"]:
                        if keyword in sample_text:
                            signal_hits += 1
                score = rows * cols + signal_hits * 50
                if score > best_score:
                    best_score = score
                    best_sheet = sn
            sheet_name = best_sheet
    df_raw = xl.parse(sheet_name, header=None, dtype=object)

    # --- Pre-clean: strip totals/banners/blank padding rows ---------------
    # This handles broker-style rent rolls (Briar Glen, etc.) that have
    # report headers, page banners, summary totals, and blank padding rows
    # interleaved with the actual data.
    from pre_cleaner import clean_raw_rent_roll
    df_raw, pre_clean_stats = clean_raw_rent_roll(df_raw)

    # --- Detect header -----------------------------------------------------
    header_idx = detect_header_row(df_raw)
    headers = [str(v) if v is not None else "" for v in df_raw.iloc[header_idx].tolist()]
    # Make column names unique (pandas requires unique)
    seen: Dict[str, int] = {}
    unique_headers = []
    for h in headers:
        key = h.strip() or "col"
        if key in seen:
            seen[key] += 1
            unique_headers.append(f"{key}__{seen[key]}")
        else:
            seen[key] = 0
            unique_headers.append(key)

    df = df_raw.iloc[header_idx + 1 :].copy()
    df.columns = unique_headers
    df = df.reset_index(drop=True)
    # Drop completely blank rows
    df = df.dropna(how="all").reset_index(drop=True)

    # --- Build field map ---------------------------------------------------
    field_map: Dict[str, str] = {}
    for col in df.columns:
        hc = _clean_header(col)
        field = _field_for_header(hc)
        if field and field not in field_map:
            field_map[field] = col

    # --- Detect care column groups ----------------------------------------
    care_groups, care_audit = detect_care_groups(list(df.columns), mappings)
    conc_monthly_cols, conc_end_col = detect_concession_cols(list(df.columns))

    # --- Parse parent-child structure -------------------------------------
    current_apt_ctx: Dict[str, object] = {}
    bed_rows: List[Dict[str, object]] = []
    unmapped = {
        "apt_type": [],
        "bed_status": [],
        "payer": [],
        "care_level": [],
        "care_type": [],
        "missing_care_type": [],  # rows where no Care Type column found / value blank
    }

    for _, row in df.iterrows():
        # Three row classifications:
        #   1. Parent-only: has unit/apt info but no bed-level data → set context, skip
        #   2. Self-contained: has unit/apt info AND bed-level data on same row →
        #      refresh context AND emit a bed record from the same row
        #   3. Child bed: has bed-level data only → emit bed record using prior context
        #
        # Salem uses (1) + (3). Briar Glen single-bed uses (2). Briar Glen
        # two-bed uses (1) + (3) where the bed signal is the Privacy Level (SPA/SPB).

        is_self_contained = _row_is_self_contained_unit(row, field_map)
        is_parent_only = _row_has_apartment(row, field_map) and not is_self_contained
        is_child_bed = _row_has_bed(row, field_map) and not is_self_contained

        if is_parent_only:
            # Refresh apartment context
            current_apt_ctx = {
                "unit":       row.get(field_map.get("unit")) if field_map.get("unit") else None,
                "apartment":  row.get(field_map.get("apartment")) if field_map.get("apartment") else None,
                "apt_type":   row.get(field_map.get("apt_type")) if field_map.get("apt_type") else None,
                "market_rate_apt": _to_num(row.get(field_map.get("market_rate"))) if field_map.get("market_rate") else 0.0,
                "actual_rate_apt": _to_num(row.get(field_map.get("actual_rate"))) if field_map.get("actual_rate") else 0.0,
                "apt_status": row.get(field_map.get("apt_status")) if field_map.get("apt_status") else None,
                "potential_occ": row.get(field_map.get("potential_occ")) if field_map.get("potential_occ") else None,
                "sqft":       row.get(field_map.get("sqft")) if field_map.get("sqft") else None,
                "care_type_raw": row.get(field_map.get("care_type")) if field_map.get("care_type") else None,
            }
            continue

        if is_self_contained:
            # Refresh context from this row, then fall through to emit a record
            # using the SAME row's bed-level data.
            current_apt_ctx = {
                "unit":       row.get(field_map.get("unit")) if field_map.get("unit") else None,
                "apartment":  row.get(field_map.get("apartment")) if field_map.get("apartment") else None,
                "apt_type":   row.get(field_map.get("apt_type")) if field_map.get("apt_type") else None,
                "market_rate_apt": _to_num(row.get(field_map.get("market_rate"))) if field_map.get("market_rate") else 0.0,
                "actual_rate_apt": _to_num(row.get(field_map.get("actual_rate"))) if field_map.get("actual_rate") else 0.0,
                "apt_status": row.get(field_map.get("apt_status")) if field_map.get("apt_status") else None,
                "potential_occ": row.get(field_map.get("potential_occ")) if field_map.get("potential_occ") else None,
                "sqft":       row.get(field_map.get("sqft")) if field_map.get("sqft") else None,
                "care_type_raw": row.get(field_map.get("care_type")) if field_map.get("care_type") else None,
            }
            # fall through into the bed-record builder below

        if is_child_bed or is_self_contained:
            # Build a bed-level record
            first = row.get(field_map.get("first_name")) if field_map.get("first_name") else None
            last = row.get(field_map.get("last_name")) if field_map.get("last_name") else None
            full = row.get(field_map.get("resident_full")) if field_map.get("resident_full") else None

            def _safe_str(x):
                if x is None or (isinstance(x, float) and pd.isna(x)):
                    return ""
                s = str(x).strip()
                return "" if s.lower() == "nan" else s

            first_s, last_s, full_s = _safe_str(first), _safe_str(last), _safe_str(full)
            if full_s:
                resident_name = full_s
            else:
                parts = [p for p in (first_s, last_s) if p]
                resident_name = " ".join(parts)

            # Apt Type normalization
            raw_apt_type = current_apt_ctx.get("apt_type")
            apt_type_norm, apt_rule = normalize_apt(raw_apt_type, mappings)
            if raw_apt_type and not apt_rule:
                unmapped["apt_type"].append(str(raw_apt_type))

            # Bed status
            raw_bed_status = row.get(field_map.get("bed_status")) if field_map.get("bed_status") else None
            # Briar Glen pattern: status is encoded in the Resident column
            # ("*Vacant" instead of a name). If we have no bed_status column
            # AND the resident name looks like a vacancy marker, treat that as
            # the bed status.
            if (raw_bed_status is None or str(raw_bed_status).strip() == "") and resident_name:
                rn_lower = resident_name.lower().strip()
                # Common vacancy markers: "*Vacant", "Vacant", "VACANT", "(vacant)"
                if rn_lower.lstrip("*").lstrip("(").startswith("vacant"):
                    raw_bed_status = "Vacant"
                    resident_name = ""  # don't propagate "*Vacant" as a name
            # Default: if still nothing, infer Occupied if we have a real
            # resident name, else Vacant.
            if raw_bed_status is None or str(raw_bed_status).strip() == "":
                raw_bed_status = "Occupied" if resident_name else "Vacant"

            bed_status_norm, bed_rule = normalize_bed_status(raw_bed_status, mappings)
            if raw_bed_status and not bed_rule:
                unmapped["bed_status"].append(str(raw_bed_status))

            # Payer (with fallback to Private Pay for OCCUPIED beds only)
            raw_payer = row.get(field_map.get("payer")) if field_map.get("payer") else None
            if isinstance(raw_payer, float) and pd.isna(raw_payer):
                raw_payer = None
            if bed_status_norm == "Occupied":
                payer_norm, payer_rule = normalize_payer(raw_payer, mappings)
                if raw_payer is not None and str(raw_payer).strip() and str(raw_payer).lower() != "nan" and payer_rule == "__fallback__":
                    unmapped["payer"].append(str(raw_payer))
            else:
                # Vacant / Hold / Notice / Model / Down — no payer
                payer_norm = ""

            # Care Level (source-style raw value, e.g. "Assisted Living Level 6")
            al_care_level_raw = row.get(field_map.get("al_care_level")) if field_map.get("al_care_level") else None
            # Also check inside detected care groups if we don't have a clean field hit
            if (al_care_level_raw is None or str(al_care_level_raw).strip() == "") and care_groups:
                for g in care_groups:
                    if g.bucket == "Care Level $" and g.level_col:
                        al_care_level_raw = row.get(g.level_col)
                        break
            care_level_norm, care_rule = normalize_care_level(al_care_level_raw, mappings)
            if (al_care_level_raw is not None
                and str(al_care_level_raw).strip()
                and str(al_care_level_raw).lower() != "nan"
                and not care_rule):
                unmapped["care_level"].append(str(al_care_level_raw))

            # --- Extract Unit / Room / Building / Bed identity ---------------
            # (Done before Care Type detection because Care Type fallback uses
            # building_str.)
            bed_letter_raw = row.get(field_map.get("bed")) if field_map.get("bed") else ""
            bed_letter = str(bed_letter_raw).strip() if bed_letter_raw is not None else ""
            if bed_letter.lower() == "nan":
                bed_letter = ""

            # Briar Glen-style Privacy Level codes: PRI=single (no letter),
            # SPA/DAS/QAS=A side, SPB/DBS/QBS=B side. Translate to single
            # letters so Unit # composite reads "05-A" instead of "05-SPA".
            bl_upper = bed_letter.upper()
            if bl_upper in {"PRI", "SINGLE"}:
                bed_letter = ""  # solo occupancy — no bed letter needed
            elif bl_upper in {"SPA", "DAS", "QAS"}:
                bed_letter = "A"
            elif bl_upper in {"SPB", "DBS", "QBS"}:
                bed_letter = "B"

            # Determine room# and building. Two cases:
            #   Salem-style: separate Unit + Apartment columns. Unit holds the
            #     building/wing code ("AL"), Apartment holds the room number
            #     ("101").
            #   Briar Glen-style: only Unit column, holds the room number ("01").
            #     There's no separate building.
            apt_field = field_map.get("apartment")
            unit_field = field_map.get("unit")
            has_separate_apt = apt_field is not None and apt_field != unit_field

            if has_separate_apt:
                room_raw = current_apt_ctx.get("apartment")
                building_raw = current_apt_ctx.get("unit")
            else:
                # Single-column format: unit IS the room
                room_raw = current_apt_ctx.get("unit")
                building_raw = None

            room_str = str(room_raw).strip() if room_raw is not None else ""
            if room_str.lower() == "nan":
                room_str = ""
            # Normalize numeric room numbers (Excel often loads "101" as 101.0)
            try:
                if room_str and float(room_str).is_integer():
                    room_str = str(int(float(room_str)))
            except (ValueError, TypeError):
                pass

            building_str = str(building_raw).strip() if building_raw is not None else ""
            if building_str.lower() == "nan":
                building_str = ""

            if room_str and bed_letter:
                unit_id = f"{room_str}-{bed_letter}"
            elif room_str:
                unit_id = room_str
            elif building_str:
                unit_id = building_str
            else:
                unit_id = ""

            # Care Type (IL / AL / MC) — Priority chain:
            #   1. Explicit Care Type column on this row
            #   2. Apartment-context Care Type (parent-level column)
            #   3. Building / Unit code (e.g., Salem's "AL")
            #   4. Care Level raw value (e.g., "Assisted Living Level 6")
            #   5. Property default from app sidebar
            #   6. Blank + flag exception
            care_type_raw = row.get(field_map.get("care_type")) if field_map.get("care_type") else None
            if care_type_raw is None or (isinstance(care_type_raw, float) and pd.isna(care_type_raw)) or str(care_type_raw).strip() == "":
                care_type_raw = current_apt_ctx.get("care_type_raw")

            care_type_norm, care_type_rule = normalize_care_type(care_type_raw, mappings)
            care_type_source_label = "Source" if care_type_norm else None

            # Fallback 3: Building / Unit code
            if not care_type_norm and building_str:
                bldg_norm, _ = normalize_care_type(building_str, mappings)
                if bldg_norm:
                    care_type_norm = bldg_norm
                    care_type_source_label = "Building"

            # Fallback 4: Care Level raw value (often contains "Assisted Living ...")
            if not care_type_norm and al_care_level_raw:
                cl_norm, _ = normalize_care_type(al_care_level_raw, mappings)
                if cl_norm:
                    care_type_norm = cl_norm
                    care_type_source_label = "Care Level"

            # Fallback 5: Property default
            care_type_from_default = False
            if not care_type_norm and prop_default:
                care_type_norm = prop_default
                care_type_from_default = True
                care_type_source_label = "Property Default"

            # Only flag if every fallback came up empty
            care_type_missing = not care_type_norm

            # Rates
            market = _to_num(row.get(field_map.get("market_rate"))) if field_map.get("market_rate") else 0.0
            actual = _to_num(row.get(field_map.get("actual_rate"))) if field_map.get("actual_rate") else 0.0
            # If the bed row has zeros, fall back to apartment-context values (some formats
            # only record rate at the apt row and leave bed blank).
            if market == 0:
                market = current_apt_ctx.get("market_rate_apt", 0.0) or 0.0
            if actual == 0:
                actual = current_apt_ctx.get("actual_rate_apt", 0.0) or 0.0

            # Concessions
            # Concessions — sum ALL detected concession columns (Briar Glen has
            # Recurring Discounts AND One-Time Incentives alongside any generic
            # Concession column). Source signs preserved; values are typically
            # negative for discounts.
            conc_amt = (
                sum(_to_num(row.get(c)) for c in conc_monthly_cols)
                if conc_monthly_cols else 0.0
            )
            conc_end = row.get(conc_end_col) if conc_end_col else None

            # Care bucket totals
            bucket_sums = {"Care Level $": 0.0, "Med Mgmt $": 0.0, "Pharmacy $": 0.0, "Other LOC $": 0.0}
            for g in care_groups:
                if g.monthly_col:
                    bucket_sums[g.bucket] = bucket_sums.get(g.bucket, 0.0) + _to_num(row.get(g.monthly_col))

            # --- Track unmapped Care Type for exceptions ----
            if care_type_missing:
                unmapped["missing_care_type"].append(
                    f"Room {room_str or '?'}, Bed {bed_letter or '?'}"
                )

            rec = {
                # --- Core identity
                "Unit #":           unit_id,
                "Room #":           room_str,
                "Bed":              bed_letter,
                "Building":         building_str,
                "Sq Ft":            current_apt_ctx.get("sqft") or "",   # blank if source lacks it
                "Apt Type (raw)":   raw_apt_type or "",
                "Apt Type":         apt_type_norm,
                "Potential Occupancy": current_apt_ctx.get("potential_occ") or "",

                # --- Status
                "Bed Status (raw)":   raw_bed_status or "",
                "Status":             bed_status_norm,
                "Apartment Status":   current_apt_ctx.get("apt_status") or "",

                # --- Resident
                "Resident Name":      resident_name,
                "Resident First":     first_s,
                "Resident Last":      last_s,
                "Payer (raw)":        raw_payer or "",
                "Payer Type":         payer_norm,
                "Move-in Date":       row.get(field_map.get("move_in")) if field_map.get("move_in") else "",
                "Move-out Date":      row.get(field_map.get("move_out")) if field_map.get("move_out") else "",

                # --- Pricing
                # Rates and TMR are blanked when zero so Excel COUNT() reflects
                # populated rows only. Math is computed on the raw values BEFORE
                # blanking, so Rate Gap and TMR remain correct.
                "Market Rate":        _blank_if_zero(market),
                "Actual Rate":        _blank_if_zero(actual),
                "Rate Gap":           _blank_if_zero(market - actual),
                "Concession $":       _blank_if_zero(conc_amt),
                "Concession End Date": conc_end or "",

                # --- Care
                "Care Type (raw)":    care_type_raw or "",
                "Care Type":          care_type_norm,            # IL / AL / MC
                "Care Type Source":   care_type_source_label or "",
                "Care Level (raw)":   al_care_level_raw or "",
                "Care Level":         care_level_norm,           # Level 1-5 or Level 6+
                "Care Level $":    _blank_if_zero(bucket_sums.get("Care Level $", 0.0)),
                "Med Mgmt $":         _blank_if_zero(bucket_sums.get("Med Mgmt $", 0.0)),
                "Pharmacy $":         _blank_if_zero(bucket_sums.get("Pharmacy $", 0.0)),
                "Other LOC $":        _blank_if_zero(bucket_sums.get("Other LOC $", 0.0)),
                "Total LOC $":        _blank_if_zero(sum(bucket_sums.values())),

                # --- Derived
                # Concessions are stored as negative source values (discounts).
                # Adding them correctly reduces revenue. Previous version used
                # subtraction which inverted the discount on every concession row.
                "Total Monthly Revenue": _blank_if_zero(
                    actual + sum(bucket_sums.values()) + conc_amt
                ),
            }
            bed_rows.append(rec)

    normalized = pd.DataFrame(bed_rows)

    # --- Second pass: mark shared apartments -------------------------------
    # A room is "shared" when it has 2+ bed rows under the same Room # AND
    # under the same Building (so two unrelated buildings using the same room
    # number don't get incorrectly flagged as shared).
    if not normalized.empty:
        # Count beds per (Building, Room #) — only rooms with a non-empty room
        # number get checked, otherwise every blank-room row would group together
        room_key = list(zip(
            normalized["Building"].astype(str),
            normalized["Room #"].astype(str),
        ))
        normalized["_room_key"] = room_key
        # Count beds per room (skip rows with blank room numbers)
        valid_keys = normalized.loc[normalized["Room #"].astype(str).str.strip() != "", "_room_key"]
        bed_counts = valid_keys.value_counts().to_dict()
        # Append ' - Shared' suffix where bed count >= 2
        def _maybe_share(row):
            apt = str(row["Apt Type"] or "").strip()
            if not apt:
                return apt
            count = bed_counts.get(row["_room_key"], 0)
            if count >= 2 and "Shared" not in apt:
                return f"{apt} - Shared"
            return apt
        normalized["Apt Type"] = normalized.apply(_maybe_share, axis=1)
        normalized = normalized.drop(columns=["_room_key"])

    # --- Condensed 18-column view (user-specified order) -------------------
    if not normalized.empty:
        condensed = pd.DataFrame({
            "Unit #":            normalized["Unit #"],
            "Room #":            normalized["Room #"],
            "Sq Ft":             normalized["Sq Ft"],
            "Care Type":         normalized["Care Type"],
            "Status":            normalized["Status"],
            "Apt Type":          normalized["Apt Type"],
            "Market Rate":       normalized["Market Rate"],
            "Actual Rate":       normalized["Actual Rate"],
            "Concession $":      normalized["Concession $"],
            "Concession End Date": normalized["Concession End Date"],
            "Care Level":        normalized["Care Level"],
            "Care Level $":   normalized["Care Level $"],
            "Med Mgmt $":        normalized["Med Mgmt $"],
            "Pharmacy $":        normalized["Pharmacy $"],
            "Other LOC $":       normalized["Other LOC $"],
            "Payer Type":        normalized["Payer Type"],
            "Move-in Date":      normalized["Move-in Date"],
            "Resident Name":     normalized["Resident Name"],
        })
    else:
        condensed = pd.DataFrame(columns=CONDENSED_COLUMNS)

    # --- Mapping audit -----------------------------------------------------
    audit_rows = []
    for col, bucket in care_audit.items():
        audit_rows.append({"Category": "Care Bucket", "Source": col, "Mapped To": bucket})
    for g in care_groups:
        audit_rows.append({"Category": "Care Group", "Source": g.source_prefix or "", "Mapped To": g.bucket})
    mapping_audit = pd.DataFrame(audit_rows) if audit_rows else pd.DataFrame(columns=["Category", "Source", "Mapped To"])

    return NormalizeResult(
        normalized=normalized,
        condensed=condensed,
        mapping_audit=mapping_audit,
        source_headers=list(df.columns),
        header_row_idx=header_idx,
        care_groups=care_groups,
        unmapped={k: sorted(set(v)) for k, v in unmapped.items()},
        property_care_type_default=prop_default,
        pre_clean_stats=pre_clean_stats,
    )
