"""
Property Name — filename-to-property-name derivation.

Shared utility used by both writers (Track 1 + Track 2):
  - `analyzer_rr_writer.py` derives from the uploaded RR filename and stamps
    `Rent Roll Input!A3`.
  - `t12_normalizer_writer.py` derives from the uploaded T12 filename and
    stamps `T12 Input!A10`.

Cross-track shared module — analogous to `period_date.py`. Treat as a
read-only utility from both tracks; bumping its behavior should consider
both writers.

The heuristic strips date stamps, version suffixes, and common report-type
boilerplate ("T-12", "Rent Roll", "P&L Statement", "Financial Summary",
etc.) from the filename stem. Best-effort — falls back to the raw stem if
cleaning removes everything.

If the source file actually carries a property name in its content (e.g.
Yardi puts it in row 1, broker formats put it on a Cover sheet), a future
parser-side enhancement could surface that and override the filename
derivation. Not staffed today; filename is the contract.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

# Patterns are deliberately ordered: date patterns first (so e.g. "P&L
# 2025.12" leaves "P&L" for the boilerplate pass to handle), then
# boilerplate. Each pattern is case-insensitive at substitution time.
_DATE_PATTERNS = (
    # Run AFTER `_` / `-` are normalized to spaces, so all separators here
    # are space, slash, or dot.
    r"\b\d{4}[./]\d{1,2}[./]\d{1,2}\b",              # 2026.04.24
    r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b",            # 1.31.26, 04/24/2026
    r"\b\d{4}\s+\d{1,2}\s+\d{1,2}\b",                # 2026 04 24 (after sep-normalize)
    r"\b\d{1,2}\s+\d{1,2}\s+\d{2,4}\b",              # 04 24 2026
    r"\b\d{4}\.\d{1,2}\b",                           # 2025.12
    r"\b\d{4}\s+\d{1,2}\b",                          # 2026 03 (was 2026-03)
    r"\b\d{1,2}\s+\d{4}\b",                          # 03 2026 (was 03-2026)
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{2,4}\b",                   # March 2026, Mar 26
    r"\bmo\s*\d{2,4}\b",                             # Mo 2026
    r"\bq[1-4]\s*\d{2,4}\b",                         # Q1 2026
    r"\b20\d{2}\b",                                  # bare year 2026
)

_BOILERPLATE_PATTERNS = (
    r"\bt-?\s*12\b",                                 # T-12, T12, T 12
    r"\bt-?\s*twelve\b",
    r"\bcondensed\s+rr\b",                           # Condensed_RR (after sep-normalize)
    r"\brent\s*roll\b",                              # Rent Roll, RentRoll
    r"\brr\b",                                       # bare "RR" abbreviation
    r"\bp\s*&\s*l\b",                                # P&L, P & L
    r"\bp\s*and\s*l\b",                              # P and L
    r"\bpnl\b",                                      # PnL
    r"\bprofit\s*(?:\s+and\s+|\s*&\s*)?\s*loss\b",
    r"\bincome\s+statement\b",
    r"\bfinancial\s+summary\b",
    r"\bfinancial\s+statement\b",
    r"\bstatement\b",
    r"\bnormalized\b",
    r"\bsummary\b",
    r"\breport\b",
    r"\banalyzer\b",
    r"\bv\d+\b",                                     # v2, v10
    r"\(\s*\d+\s*\)",                                # (1), (2) — common dupe markers
)


def _strip_extension(stem: str) -> str:
    """Strip a trailing .xlsx / .xlsm / .xls / .csv extension if present."""
    for ext in (".xlsx", ".xlsm", ".xls", ".csv", ".tsv"):
        if stem.lower().endswith(ext):
            return stem[: -len(ext)]
    return stem


def derive_property_name(filename: str) -> str:
    """Best-effort property-name extraction from a filename.

    Examples (verified against the four reference fixtures + Homestead RR):
      "Salem Road T-12 1.31.26.xlsx"                          -> "Salem Road"
      "Briar Glen T12 P&L Statement_2025.12.xlsx"             -> "Briar Glen"
      "2026-04-24 Homestead Village Rent Roll v2.xlsx"        -> "Homestead Village"
      "2026-03 Homestead Village Pensacola Financial Summary" -> "Homestead Village Pensacola"
      "Homestead - March 2026 T12.xlsx"                       -> "Homestead"
      "Oaks at Beaufort RR 03-2026.xlsx"                      -> "Oaks at Beaufort"

    Empty / whitespace-only input returns empty string. If cleaning removes
    every character, falls back to the raw stem so the caller always gets
    something meaningful.
    """
    if not filename or not str(filename).strip():
        return ""

    # Drop directory components (handle both POSIX and Windows separators)
    raw = str(filename)
    name = PureWindowsPath(raw).name if "\\" in raw else PurePosixPath(raw).name

    stem = _strip_extension(name)
    if not stem:
        return ""

    # Normalize separators (_, -) to spaces FIRST so word-boundary \b in
    # the date/boilerplate patterns works (underscore is a \w character).
    cleaned = re.sub(r"[_\-]+", " ", stem)
    for pat in _DATE_PATTERNS + _BOILERPLATE_PATTERNS:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -._,()[]")

    # If cleaning removed everything meaningful, fall back to the raw stem
    return cleaned or stem
