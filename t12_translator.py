"""
T12 Vocabulary Translator
=========================

Converts a Condensed_RR DataFrame's normalized values into the vocabulary the
T12 intake workbook expects (its data validation lists).

The Condensed_RR's normalization is preserved in the standalone RR output;
only the T12-bound copy is translated. This keeps the analyst's standalone
view clean while satisfying the T12's validation rules.

T12 expected values per column (from Rent Roll Input data validations):
  D Care Type:    AL / MC / IL
  E Status:       Occupied / Vacant / Notice / Eviction
  F Apt Type:     Studio / 1 Bedroom / 1 Bedroom Deluxe / 2 Bedroom /
                  2 Bedroom Deluxe / Semi-Private / Other
  K Care Level:   Basic / Level 2 / Level 3 / Level 4 / Level 5 /
                  Level 6 / Level 7 / Other
  P Payer:        Private Pay / Medicaid / LTC Insurance / VA /
                  Managed Care / Self-Pay / Other
"""

from __future__ import annotations

import pandas as pd


# Translation tables. Anything not listed passes through unchanged.
STATUS_MAP = {
    "Hold":   "Other",
    "Model":  "Other",
    "Down":   "Other",
    # Occupied, Vacant, Notice pass through; "Eviction" not in our normalized
    # vocabulary so will never appear; "Other" passes through.
}

APT_TYPE_MAP = {
    "1BR":             "1 Bedroom",
    "2BR":             "2 Bedroom",
    "Companion":       "Other",
    # Studio, Semi-Private, Other pass through
}

CARE_LEVEL_MAP = {
    "Level 1":  "Basic",
    "Level 6+": "Level 7",   # T12's highest discrete bucket
    # Level 2-5 pass through; blank → blank
}

PAYER_MAP = {
    "VA Benefit": "VA",
    "Medicare":   "Other",   # T12 has no Medicare option
    # Private Pay, Medicaid, LTC Insurance, Self-Pay, Managed Care, Other pass through
}


def _strip_shared_suffix(apt_type: str) -> str:
    """Remove the ' - Shared' suffix used in standalone RR output.
    T12's Apt Type list doesn't include shared variants, so we strip it.
    The shared/companion data is preserved in the standalone RR output."""
    if not apt_type:
        return apt_type
    s = str(apt_type).strip()
    if s.endswith(" - Shared"):
        return s[:-len(" - Shared")].strip()
    return s


def translate_for_t12(condensed: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the Condensed_RR DataFrame with values translated
    into the T12's expected vocabulary. The column order is preserved.

    Source DataFrame is not mutated.
    """
    if condensed is None or condensed.empty:
        return condensed.copy() if condensed is not None else pd.DataFrame()

    df = condensed.copy()

    # Status (col E in T12 — index 4 in our 18-col layout)
    if "Status" in df.columns:
        df["Status"] = df["Status"].apply(
            lambda v: STATUS_MAP.get(str(v).strip(), str(v).strip()) if pd.notna(v) else ""
        )

    # Apt Type — strip " - Shared" suffix first, then translate
    if "Apt Type" in df.columns:
        df["Apt Type"] = df["Apt Type"].apply(
            lambda v: APT_TYPE_MAP.get(_strip_shared_suffix(v), _strip_shared_suffix(v)) if pd.notna(v) else ""
        )

    # Care Level
    if "Care Level" in df.columns:
        df["Care Level"] = df["Care Level"].apply(
            lambda v: CARE_LEVEL_MAP.get(str(v).strip(), str(v).strip()) if pd.notna(v) else ""
        )

    # Payer Type
    if "Payer Type" in df.columns:
        df["Payer Type"] = df["Payer Type"].apply(
            lambda v: PAYER_MAP.get(str(v).strip(), str(v).strip()) if pd.notna(v) else ""
        )

    return df
