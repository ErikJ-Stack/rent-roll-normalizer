"""
Pre-Cleaner
===========

Removes structural noise from a raw rent roll DataFrame BEFORE the header
detector and parent-child parser run. Targets:

  - Totals / Grand Total / Summary blocks at the bottom
  - Page banners ("Page 1", "Rent Roll", "Community: ...", "As of Date: ...")
  - Legend / instruction rows ("x: Excluded Units", "w: Waitlisted ...")
  - Community-name banners (single-cell rows that just label a section)
  - Blank padding rows (every cell empty/whitespace)

Conservative by default: only drops rows we're confident are noise. Rows that
might be data are kept. The downstream parser is robust to extra rows.

The cleaner operates on the raw 0-indexed DataFrame (header detection has not
yet run), so we work with column positions, not column names.
"""

from __future__ import annotations

import re
from typing import List, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Patterns that mark a row as "definitely noise"
# ---------------------------------------------------------------------------

# Row text → drop if cell A starts with any of these (anchored prefix match)
_BANNER_PREFIXES = (
    "rent roll",
    "page ",
    "community:",
    "occupancy type:",
    "as of date:",
    "show exclude",
    "summary for community",
    "x: excluded",
    "w: waitlist",
    "au: additional",
    "legend",
    "report date:",
    "report period:",
    "property:",
    "portfolio:",
)

# Row text → drop if any cell contains a totals signal
_TOTALS_SIGNALS = (
    "totals for ",
    "grand total",
    "total for property",
    "total occupancy",
    "total units",
    "report total",
    "property total",
)

# Care code legend rows specifically (Briar Glen has these on its 2nd sheet,
# but if they slip into the main sheet, drop)
_LEGEND_PREFIXES = (
    "care level codes",
    "privacy level codes",
    "resident status codes",
    "unit type codes",
    "rate type codes",
)


# ---------------------------------------------------------------------------
def _row_text(row: pd.Series) -> str:
    """Concatenate all non-null cells in the row into a lowercase string."""
    parts = []
    for v in row:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            parts.append(s)
    return " | ".join(parts).lower()


def _row_first_cell(row: pd.Series) -> str:
    """First non-null cell as a stripped lowercase string."""
    for v in row:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            return s.lower()
    return ""


def _is_blank_row(row: pd.Series) -> bool:
    """True if every cell is None/blank/whitespace."""
    for v in row:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            return False
    return True


def _is_banner_row(row: pd.Series) -> bool:
    """Row is a page header / community banner / instruction line."""
    first = _row_first_cell(row)
    if not first:
        return False
    for prefix in _BANNER_PREFIXES + _LEGEND_PREFIXES:
        if first.startswith(prefix):
            return True
    return False


def _is_totals_row(row: pd.Series) -> bool:
    """Row contains a totals/summary signal anywhere."""
    text = _row_text(row)
    if not text:
        return False
    for signal in _TOTALS_SIGNALS:
        if signal in text:
            return True
    return False


def _count_non_blank_cells(row: pd.Series) -> int:
    n = 0
    for v in row:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            n += 1
    return n


def _is_section_label_row(row: pd.Series, total_cols: int) -> bool:
    """A row with only 1 cell populated and it's a longish text label that
    looks like a section header (e.g. 'Briar Glen Alzheimer's Special Care
    Center (853)').

    Conservative: requires >= 4 columns total in the sheet to avoid flagging
    legitimate single-column data, AND the populated cell must be in col A
    (or B if A is blank), AND must be >20 chars to look label-like."""
    if total_cols < 4:
        return False
    populated = _count_non_blank_cells(row)
    if populated != 1:
        return False
    # Find the populated cell
    for i, v in enumerate(row):
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() != "nan":
            # Must be in first 2 columns and longish
            if i <= 1 and len(s) >= 20:
                # Don't flag if it's already caught by banner or totals
                lower = s.lower()
                for prefix in _BANNER_PREFIXES + _LEGEND_PREFIXES:
                    if lower.startswith(prefix):
                        return True  # caught here too — drop
                # Heuristic: a section label has no numbers in it (data rows
                # almost always have at least one number)
                if not re.search(r"\d", s):
                    return True
                # Has a property-name-like pattern: words with capitals
                # followed by parenthetical code (e.g. "(853)")
                if re.search(r"\(\d+\)", s):
                    return True
            return False
    return False


# ---------------------------------------------------------------------------
def clean_raw_rent_roll(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Strip noise from a raw rent roll DataFrame.

    Returns:
        (cleaned_df, stats) where stats describes what was removed.

    The returned DataFrame keeps original column count but rows are filtered.
    Index is reset.
    """
    if df_raw is None or df_raw.empty:
        return df_raw, {"input_rows": 0, "output_rows": 0, "dropped": {}}

    n_in = len(df_raw)
    total_cols = df_raw.shape[1]

    dropped = {
        "blank":         0,
        "banner":        0,
        "totals":        0,
        "section_label": 0,
        "after_totals":  0,
    }

    # First pass: find the index of the first totals row. Everything from
    # there to the end is dropped (totals/summary block).
    totals_cutoff = None
    for idx, (_, row) in enumerate(df_raw.iterrows()):
        if _is_totals_row(row):
            totals_cutoff = idx
            break

    rows_to_keep = []
    for idx, (_, row) in enumerate(df_raw.iterrows()):
        # Drop everything from totals row onward
        if totals_cutoff is not None and idx >= totals_cutoff:
            if idx == totals_cutoff:
                dropped["totals"] += 1
            else:
                dropped["after_totals"] += 1
            continue

        if _is_blank_row(row):
            dropped["blank"] += 1
            continue

        if _is_banner_row(row):
            dropped["banner"] += 1
            continue

        if _is_section_label_row(row, total_cols):
            dropped["section_label"] += 1
            continue

        rows_to_keep.append(idx)

    cleaned = df_raw.iloc[rows_to_keep].reset_index(drop=True)
    n_out = len(cleaned)

    stats = {
        "input_rows":  n_in,
        "output_rows": n_out,
        "dropped":     dropped,
        "totals_cutoff_at_input_row": totals_cutoff,
    }
    return cleaned, stats
