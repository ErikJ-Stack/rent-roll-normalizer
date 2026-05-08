"""
verify_t12_v020.py — End-to-end parser verification for T12 v0.2.0.

Runs all four reference fixtures through `parse_t12()` and asserts the
parser-side facts that gate the v0.2.0 release:

  Regression (must NOT break)
    Salem (Yardi):    73 GL rows, 0 UNMATCHED, source = $4,249,047.98
    Briar Glen (MRI): 91 GL rows, 0 UNMATCHED, source = $8,306,657.64

  New (BrokerFinancialSummaryFormat)
    Homestead Pensacola Financial Summary:  101 GL rows, implied NOI = $1,411,323.58
    March 2026 T12:                          101 GL rows, implied NOI = $1,411,323.58

Cluster B (sign warnings, partial-year detection): all four fixtures are
full-year and standard-sign; verification asserts no warnings fire.

The substrate-level EGI / EBITDARM verification is unchanged from v0.1.6
(Salem $2,201,865 / Briar Glen $3,763,229) and depends only on workbook
formulas, not parser code. With identical source $ totals as the v0.1.1
verification, those figures continue to hold. Run the Streamlit app on each
fixture to confirm interactively, or recalc with LibreOffice.

Usage:
    python tools/verify_t12_v020.py

Exits 0 on full pass, 1 on any check failure. Prints a per-fixture report.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import openpyxl

# Make t12_normalizer importable when run from repo root or anywhere else.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from t12_normalizer import parse_t12, read_descmap_descriptions  # noqa: E402

ANALYZER_PATH = REPO_ROOT / "ALF_Financial_Analyzer_Only.xlsx"

DROPBOX = Path(
    r"C:\Users\erikj\Dropbox\Erik Javellana - Deal Review\Deals under review"
)
FIXTURES = {
    "Salem": DROPBOX
        / "ALF - SC_West Columbia - Beaufort"
        / "Broker Docs"
        / "The Retreat at Beaufort - Salem"
        / "Salem Road T-12 1.31.26.xlsx",
    "Briar Glen": DROPBOX
        / "ALF - AL_Hoover - 71 Senior Housing"
        / "Broker Docs"
        / "Property Information"
        / "Financials"
        / "2025"
        / "Briar Glen T12 P&L Statement_2025.12.xlsx",
    "Homestead": DROPBOX
        / "ALF - Pensacola_Fl - Homestead Village"
        / "Broker Docs"
        / "Financials and Census"
        / "2026-03 Homestead Village Pensacola Financial Summary.xlsx",
    "March_2026": DROPBOX
        / "ALF - Pensacola_Fl - Homestead Village"
        / "Broker Docs"
        / "Financials and Census"
        / "March 2026 T12.xlsx",
}


@dataclass
class Expect:
    """Per-fixture assertions."""
    fixture: str
    format_name: str
    gl_rows: int
    unmatched_max: int                 # caller may allow non-zero (Phase 4 substrate)
    source_total: Optional[float]      # exact (±$0.01) source $ check; None = informational
    populated_months: int = 12
    sign_warnings_max: int = 0
    implied_noi: Optional[float] = None  # broker-only — revenue subset minus expense subset


# Targets sourced from spec / journal:
#   Salem source $    : CHANGELOG-T12 [0.1.1] verification table
#   Briar Glen source : CHANGELOG-T12 [0.1.1] (unchanged from v0.1.0)
#   Homestead NOI     : CHANGELOG-T12 [Substrate template v0.1.5] EBITDAR row
EXPECTATIONS = [
    Expect(
        fixture="Salem",
        format_name="Yardi (Income to Budget)",
        gl_rows=73,
        unmatched_max=0,
        source_total=4_249_047.98,
    ),
    Expect(
        fixture="Briar Glen",
        format_name="MRI R12MINCS",
        gl_rows=91,
        unmatched_max=0,
        source_total=8_306_657.64,
    ),
    Expect(
        fixture="Homestead",
        format_name="Broker Financial Summary",
        gl_rows=101,
        # The v0.1.5 vocabulary additions for Homestead were applied to a
        # personal copy via "Option C" but were never committed to the canonical
        # Description_Map. Phase 4 substrate v0.1.7 lifts those into the bundle;
        # until then we expect ~99 UNMATCHED. Verification accepts that.
        unmatched_max=120,
        source_total=None,                 # multi-section file — sum-of-all is meaningful only via NOI
        implied_noi=1_411_323.58,
    ),
    Expect(
        fixture="March_2026",
        format_name="Broker Financial Summary",
        gl_rows=101,
        unmatched_max=120,
        source_total=None,
        implied_noi=1_411_323.58,
    ),
]


REVENUE_DESC_KEYWORDS = (
    "Room & Board", "Second Persons", "Care Level Revenue",
    "Concessions", "Respite Revenue", "Move-In Fees", "Other Income",
)


def implied_noi_from_rows(gl_rows) -> float:
    """For broker-format outputs, partition GL rows into revenue vs expense by
    description keywords (matches the substrate's intuition without recalcing
    the workbook) and return revenue - expense as the implied NOI.

    Used as a parser-side sanity check that ties to the broker-published NOI.
    """
    revenue = 0.0
    expense = 0.0
    for row in gl_rows:
        if any(kw in row.description for kw in REVENUE_DESC_KEYWORDS):
            revenue += row.total
        else:
            expense += row.total
    return revenue - expense


def run_fixture(expect: Expect, descmap) -> List[str]:
    """Returns a list of failure messages; empty list = pass."""
    path = FIXTURES[expect.fixture]
    failures: List[str] = []

    if not path.exists():
        return [f"fixture file not found: {path}"]

    with open(path, "rb") as f:
        result = parse_t12(f.read(), descmap)

    print(f"=== {expect.fixture} ({expect.format_name}) ===")
    print(f"  format detected:  {result.format_name}")
    print(f"  sheet:            {result.sheet_name}")
    print(f"  GL rows:          {len(result.gl_rows)}")
    print(f"  populated months: {result.populated_months}")
    print(f"  was annualized:   {result.was_annualized}")
    print(f"  UNMATCHED:        {len(result.unmatched)}")
    print(f"  sign warnings:    {len(result.sign_warnings)}")
    source_total = sum(r.total for r in result.gl_rows)
    print(f"  source $:         ${source_total:,.2f}")
    if expect.implied_noi is not None:
        print(f"  implied NOI:      ${implied_noi_from_rows(result.gl_rows):,.2f}")

    # --- Assertions ---
    if result.format_name != expect.format_name:
        failures.append(
            f"format detected={result.format_name!r}, expected={expect.format_name!r}"
        )
    if len(result.gl_rows) != expect.gl_rows:
        failures.append(
            f"GL rows={len(result.gl_rows)}, expected={expect.gl_rows}"
        )
    if len(result.unmatched) > expect.unmatched_max:
        failures.append(
            f"UNMATCHED={len(result.unmatched)}, expected ≤{expect.unmatched_max}"
        )
    if result.populated_months != expect.populated_months:
        failures.append(
            f"populated_months={result.populated_months}, expected={expect.populated_months}"
        )
    if len(result.sign_warnings) > expect.sign_warnings_max:
        failures.append(
            "sign warnings exceed allowed: "
            + "; ".join(result.sign_warnings)
        )
    if expect.source_total is not None:
        delta = abs(source_total - expect.source_total)
        if delta > 0.01:
            failures.append(
                f"source $={source_total:,.2f}, expected={expect.source_total:,.2f} "
                f"(delta ${delta:,.2f})"
            )
    if expect.implied_noi is not None:
        actual_noi = implied_noi_from_rows(result.gl_rows)
        delta = abs(actual_noi - expect.implied_noi)
        if delta > 1.00:
            failures.append(
                f"implied NOI=${actual_noi:,.2f}, expected=${expect.implied_noi:,.2f} "
                f"(delta ${delta:,.2f})"
            )

    if failures:
        for f in failures:
            print(f"  [FAIL] {f}")
    else:
        print("  [OK] PASS")
    print()
    return failures


def main() -> int:
    if not ANALYZER_PATH.exists():
        print(f"Analyzer not found at {ANALYZER_PATH}", file=sys.stderr)
        return 1
    analyzer_wb = openpyxl.load_workbook(ANALYZER_PATH, data_only=False)
    descmap = read_descmap_descriptions(analyzer_wb)
    print(f"Loaded Description_Map ({len(descmap)} entries) from {ANALYZER_PATH.name}")
    print()

    all_failures: List[str] = []
    for expect in EXPECTATIONS:
        failures = run_fixture(expect, descmap)
        all_failures.extend(f"{expect.fixture}: {f}" for f in failures)

    print("=" * 60)
    if all_failures:
        print(f"[FAIL] {len(all_failures)} check(s) failed:")
        for f in all_failures:
            print(f"   - {f}")
        return 1
    print("[OK] All v0.2.0 parser checks passed.")
    print()
    print("NOTE: Substrate-level EGI / EBITDARM ($2.20M Salem, $3.76M Briar")
    print("Glen) depend on workbook formulas which are unchanged from v0.1.6.")
    print("Source $ totals matching the v0.1.1 verified figures imply those")
    print("downstream values still hold. Confirm interactively in the Streamlit")
    print("app or via LibreOffice recalc.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
