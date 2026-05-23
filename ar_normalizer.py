"""
ar_normalizer.py — AR aging file parser.

Reads an operator's AR aging report (.xlsx or .csv) and produces a
normalized AROutput dataclass with aging-bucket totals, payer mix, and
roll-forward fields. Mirrors the shape of the RR (normalizer.py) and
T12 (t12_normalizer.py) parsers.

Per-instance MappingSet construction uses payer_fallback="Self-Pay + Other"
so unmapped AR payers route to the explicit Other bucket instead of the
RR module-level "Private Pay" fallback (mappings.py PAYER_FALLBACK).

The parser does NOT join to the Rent Roll — that's the writer's
responsibility (it has access to the Analyzer's RR sheet). The parser
just produces clean, summarized AR data + ingest diagnostics.

LIVE OPERATOR SAMPLE STATUS (2026-05-23):  PENDING.
The fuzzy header rules (HEADER_RULES) were built against the synthetic
fixture at tests/fixtures/ar/ar_synthetic_v01.xlsx — they will need
expansion once real operator files arrive. See the fixtures README for
detail.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from mappings import MappingSet, normalize_payer


# ---------------------------------------------------------------------------
# Header fuzzy-match — first regex match wins, so order specific → generic.
# ---------------------------------------------------------------------------

HEADER_RULES: list[tuple[str, str]] = [
    # --- Identity ---
    (r"^(unit|apt|apartment|room|suite)\b",                 "unit"),
    (r"^(resident|tenant|patient|name)\b",                  "resident_name"),
    (r"^(payer|payor|pay[\s_\-]?type|"
     r"payment[\s_\-]?(source|type)|bill[\s_\-]?type)\b",   "payer_type"),

    # --- Aging buckets (most-specific first to disambiguate "Over 90" etc.) ---
    (r"^(91[\s\-to]+120|over[\s_]?90)\b",                   "days_91_120"),
    (r"^(120\+|121\+|>\s*120|over[\s_]?120)\b",             "over_120"),
    (r"^(61[\s\-to]+90|over[\s_]?60)\b",                    "days_61_90"),
    (r"^(31[\s\-to]+60|over[\s_]?30)\b",                    "days_31_60"),
    (r"^(current|0[\s\-to]+30|1[\s\-to]+30)\b",             "current_0_30"),

    # --- Total / balance check column ---
    (r"^(total[\s_]?balance|total[\s_]?outstanding|"
     r"outstanding|total|balance|amount[\s_]?due)\s*$",     "total_balance"),

    # --- Optional roll-forward fields ---
    (r"^(prior|beginning|opening)([\s_]?(period|balance))?\b", "prior_period_balance"),
    (r"^(charges|billed)\b",                                "charges_period"),
    (r"^(collections?|payments?|received|cash[\s_]?received)\b", "collections_period"),
    (r"^(write[\s_\-]?offs?|writeoffs?|bad[\s_]?debt|wo)\b", "writeoffs_period"),
    (r"^(adjustments?|adj|credits?)\b",                     "adjustments_period"),
]

CANONICAL_BUCKETS = (
    "current_0_30", "days_31_60", "days_61_90", "days_91_120", "over_120",
)
REQUIRED_FIELDS = (
    "unit", "resident_name", "payer_type",
    "current_0_30", "days_31_60", "days_61_90", "total_balance",
)
OPTIONAL_FIELDS = (
    "days_91_120", "over_120",
    "prior_period_balance", "charges_period", "collections_period",
    "writeoffs_period", "adjustments_period",
)


# ---------------------------------------------------------------------------
# Data classes — public contract; ar_writer.py consumes these.
# ---------------------------------------------------------------------------

@dataclass
class ARRow:
    unit: str
    resident_name: str
    payer_raw: str
    payer_normalized: str
    current_0_30: float = 0.0
    days_31_60: float = 0.0
    days_61_90: float = 0.0
    days_91_120: float = 0.0
    over_120: float = 0.0
    total_balance: float = 0.0
    sum_check_ok: bool = True


@dataclass
class AROutput:
    rows: list = field(default_factory=list)

    # Aging Summary totals (Analyzer §1)
    total_current_0_30: float = 0.0
    total_days_31_60: float = 0.0
    total_days_61_90: float = 0.0
    total_days_91_120: float = 0.0
    total_over_120: float = 0.0
    total_ar: float = 0.0
    total_90_plus: float = 0.0
    pct_90_plus: float = 0.0

    # By-Payer Mix (Analyzer §3) — keyed by canonical payer bucket
    payer_outstanding: dict = field(default_factory=dict)
    payer_90_plus: dict = field(default_factory=dict)

    # Roll-Forward inputs (Analyzer §4) — None if optional cols absent
    prior_period_balance: Optional[float] = None
    charges_period: Optional[float] = None
    collections_period: Optional[float] = None
    writeoffs_period: Optional[float] = None
    adjustments_period: Optional[float] = None

    # Period metadata — set by the writer or analyst override
    as_of_date: Optional[str] = None

    # Ingest diagnostics
    sum_check_mismatch_count: int = 0
    unmapped_payer_count: int = 0
    unmatched_to_rr_count: int = 0   # populated by writer's join step

    # Header recognition diagnostics — surfaces during analyst review
    headers_matched: dict = field(default_factory=dict)
    headers_unmatched: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_header(s) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower()).rstrip(":")


def _match_header(cleaned: str) -> Optional[str]:
    for pat, canon in HEADER_RULES:
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            return canon
    return None


def _coerce_number(v) -> float:
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    # Strip $ , parentheses-as-negative
    s = str(v).strip()
    if not s:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace("$", "").replace(",", "").strip()
    try:
        n = float(s)
        return -n if neg else n
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_ar_file(
    path_or_buffer,
    sheet_name: Optional[str] = None,
    mapping_set: Optional[MappingSet] = None,
) -> AROutput:
    """Parse an AR aging file and return an AROutput.

    Args:
        path_or_buffer: file path (str/Path) or a file-like buffer
            (e.g., Streamlit upload).
        sheet_name: explicit sheet name for .xlsx inputs. Defaults to
            "AR Aging" if present, else the first sheet.
        mapping_set: optional pre-built MappingSet. If None, builds a
            default with payer_fallback="Self-Pay + Other" (AR convention).

    Raises:
        ValueError: if required columns are missing.
    """
    if mapping_set is None:
        mapping_set = MappingSet(payer_fallback="Self-Pay + Other")

    df = _load_dataframe(path_or_buffer, sheet_name)

    header_map, unmatched_headers = _build_header_map(df)

    missing = [f for f in REQUIRED_FIELDS if f not in header_map]
    if missing:
        raise ValueError(
            f"AR file missing required field(s): {missing}. "
            f"Headers seen: {list(df.columns)}"
        )

    rows: list[ARRow] = []
    sum_check_mismatch_count = 0
    unmapped_payer_count = 0

    for _, raw in df.iterrows():
        # Skip wholly-empty rows
        unit_v = raw[header_map["unit"]]
        name_v = raw[header_map["resident_name"]]
        if pd.isna(unit_v) and pd.isna(name_v):
            continue

        unit = str(unit_v).strip() if not pd.isna(unit_v) else ""
        resident = str(name_v).strip() if not pd.isna(name_v) else ""

        payer_raw_v = raw[header_map["payer_type"]]
        payer_raw = str(payer_raw_v).strip() if not pd.isna(payer_raw_v) else ""
        payer_norm, matched_pattern = normalize_payer(payer_raw, mapping_set)
        if matched_pattern == "__fallback__":
            unmapped_payer_count += 1

        def _get(canon: str) -> float:
            col = header_map.get(canon)
            return _coerce_number(raw[col]) if col is not None else 0.0

        ar_row = ARRow(
            unit=unit,
            resident_name=resident,
            payer_raw=payer_raw,
            payer_normalized=payer_norm,
            current_0_30=_get("current_0_30"),
            days_31_60=_get("days_31_60"),
            days_61_90=_get("days_61_90"),
            days_91_120=_get("days_91_120"),
            over_120=_get("over_120"),
            total_balance=_get("total_balance"),
        )

        bucket_sum = (ar_row.current_0_30 + ar_row.days_31_60
                      + ar_row.days_61_90 + ar_row.days_91_120
                      + ar_row.over_120)
        if abs(bucket_sum - ar_row.total_balance) > 0.01:
            ar_row.sum_check_ok = False
            sum_check_mismatch_count += 1

        rows.append(ar_row)

    return _aggregate(
        rows=rows,
        df=df,
        header_map=header_map,
        unmatched_headers=unmatched_headers,
        sum_check_mismatch_count=sum_check_mismatch_count,
        unmapped_payer_count=unmapped_payer_count,
    )


# ---------------------------------------------------------------------------
# Internal: load, header-map, aggregate
# ---------------------------------------------------------------------------

def _load_dataframe(path_or_buffer, sheet_name: Optional[str]) -> pd.DataFrame:
    is_path = isinstance(path_or_buffer, (str, Path))
    is_csv = is_path and str(path_or_buffer).lower().endswith(".csv")

    if is_csv:
        return pd.read_csv(path_or_buffer)

    # .xlsx path or file-like buffer
    if sheet_name is None:
        # Prefer "AR Aging" if present; fall back to first sheet.
        try:
            xl = pd.ExcelFile(path_or_buffer)
            sheet_name = "AR Aging" if "AR Aging" in xl.sheet_names else xl.sheet_names[0]
        except Exception:
            sheet_name = 0

    return pd.read_excel(path_or_buffer, sheet_name=sheet_name)


def _build_header_map(df: pd.DataFrame) -> tuple[dict, list]:
    header_map: dict = {}
    unmatched: list = []
    for col in df.columns:
        cleaned = _clean_header(col)
        canon = _match_header(cleaned)
        if canon and canon not in header_map:
            # First-match-wins per canonical field — protects against
            # duplicate-canonical hits (e.g., two columns both matching
            # "total_balance" via different rules).
            header_map[canon] = col
        elif canon is None:
            unmatched.append(col)
    return header_map, unmatched


def _aggregate(
    rows: list[ARRow],
    df: pd.DataFrame,
    header_map: dict,
    unmatched_headers: list,
    sum_check_mismatch_count: int,
    unmapped_payer_count: int,
) -> AROutput:
    out = AROutput(rows=rows)

    for r in rows:
        out.total_current_0_30 += r.current_0_30
        out.total_days_31_60 += r.days_31_60
        out.total_days_61_90 += r.days_61_90
        out.total_days_91_120 += r.days_91_120
        out.total_over_120 += r.over_120
        out.total_ar += r.total_balance

        bucket = r.payer_normalized
        out.payer_outstanding[bucket] = out.payer_outstanding.get(bucket, 0.0) + r.total_balance
        out.payer_90_plus[bucket] = out.payer_90_plus.get(bucket, 0.0) + r.days_91_120 + r.over_120

    out.total_90_plus = out.total_days_91_120 + out.total_over_120
    out.pct_90_plus = (out.total_90_plus / out.total_ar) if out.total_ar > 0 else 0.0

    # Roll-forward (optional — None if column absent)
    for canon in ("prior_period_balance", "charges_period", "collections_period",
                  "writeoffs_period", "adjustments_period"):
        col = header_map.get(canon)
        if col is not None:
            setattr(out, canon, float(df[col].fillna(0).apply(_coerce_number).sum()))

    out.sum_check_mismatch_count = sum_check_mismatch_count
    out.unmapped_payer_count = unmapped_payer_count
    out.headers_matched = dict(header_map)
    out.headers_unmatched = list(unmatched_headers)

    return out
