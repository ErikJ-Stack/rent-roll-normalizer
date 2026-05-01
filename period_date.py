"""
Period Date Detector
====================

Extracts a period date from a rent roll's filename. Used to auto-fill the
T12 intake's Period Date column (col S of Rent Roll Input).

Patterns checked, in priority order. First successful match wins.
Returns a `datetime.date` or None if no pattern matches.
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
from pathlib import Path
from typing import Optional


_MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_FULL = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _eom(year: int, month: int) -> int:
    """End-of-month day for a given year/month."""
    return calendar.monthrange(year, month)[1]


def _expand_year(yy: int) -> int:
    """Expand a 2-digit year to 4 digits using the standard pivot at 50.
    yy<50 → 20yy; yy>=50 → 19yy."""
    return 2000 + yy if yy < 50 else 1900 + yy


def detect_period_date(filename: str) -> Optional[dt.date]:
    """Inspect a filename and try to extract a period date.

    Patterns matched (first match wins):
      1. YYYY-MM-DD or YYYY/MM/DD          → exact date
      2. MM-DD-YYYY or MM/DD/YYYY          → exact date
      3. M_D_YY or M.D.YY (e.g. 1_31_26)   → exact date (2-digit year expanded)
      4. YYYY-MM or YYYY_MM                → end of that month
      5. Mon_YYYY / MonYYYY (e.g. Jan_2026)→ end of that month
      6. MonDDYYYY (e.g. Jan312026)        → exact date

    The filename's path and extension are ignored.
    """
    if not filename:
        return None
    stem = Path(filename).stem  # drop extension and directories

    # We can't rely on \b because '_' is treated as a word character — so
    # "_1_31_26" has no \b between '_' and '1'. Instead we wrap the stem in
    # delimiters and use explicit non-digit boundaries.
    s = "_" + stem + "_"  # pad so first/last tokens have neighbors

    # Pattern 1: YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r"(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?!\d)", s)
    if m:
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return dt.date(y, mo, d)
        except ValueError:
            pass

    # Pattern 2: MM-DD-YYYY or MM/DD/YYYY
    m = re.search(r"(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?!\d)", s)
    if m:
        try:
            mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return dt.date(y, mo, d)
        except ValueError:
            pass

    # Pattern 3: M_D_YY or M.D.YY (Salem's "1_31_26" format)
    m = re.search(r"(?<!\d)(\d{1,2})[_.](\d{1,2})[_.](\d{2})(?!\d)", s)
    if m:
        try:
            mo, d, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y = _expand_year(yy)
            return dt.date(y, mo, d)
        except ValueError:
            pass

    # Pattern 4a: YYYY_MM or YYYY-MM (no day) → end of month
    m = re.search(r"(?<!\d)(\d{4})[-_](\d{1,2})(?!\d)", s)
    if m:
        try:
            y, mo = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                return dt.date(y, mo, _eom(y, mo))
        except ValueError:
            pass

    # Pattern 4b: MM_YYYY (e.g. "01_2026") → end of month
    m = re.search(r"(?<!\d)(\d{1,2})[-_](\d{4})(?!\d)", s)
    if m:
        try:
            mo, y = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                return dt.date(y, mo, _eom(y, mo))
        except ValueError:
            pass

    # Pattern 5: Month name + 4-digit year (e.g. "Jan_2026", "January 2026")
    for month_dict in (_MONTH_FULL, _MONTH_ABBR):
        for name, num in month_dict.items():
            pat = rf"{name}[\W_]*(\d{{4}})"
            m = re.search(pat, s, flags=re.IGNORECASE)
            if m:
                y = int(m.group(1))
                return dt.date(y, num, _eom(y, num))

    # Pattern 6: MonDDYYYY (e.g. "Jan312026")
    for month_dict in (_MONTH_FULL, _MONTH_ABBR):
        for name, num in month_dict.items():
            pat = rf"{name}(\d{{1,2}})(\d{{4}})"
            m = re.search(pat, s, flags=re.IGNORECASE)
            if m:
                try:
                    d, y = int(m.group(1)), int(m.group(2))
                    return dt.date(y, num, d)
                except ValueError:
                    pass

    return None
