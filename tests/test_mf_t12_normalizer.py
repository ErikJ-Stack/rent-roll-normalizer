"""
Tests for the MF T-12 normalizer + COA classifier.

Two layers:
  1. Pure unit tests of `mf_mappings.classify_t12_account` — CI-runnable, no
     file dependencies.
  2. End-to-end reconciliation against the 5 real operator T-12 formats. Those
     files are gitignored (real financials) — the test SKIPS any that are
     absent, mirroring the ALF populated-fixture convention. When present, each
     must classify 100% of leaf lines and reconcile income/expense/NOI to the
     as-reported totals (penny tolerance), with the one documented exception:
     Blairstone's QuickBooks export carries a ~$22,128.62 total-vs-detail gap in
     its own subtotal rows (no matching detail line) — our detail sum is the
     correct figure, so that delta is whitelisted.
"""
import os

import pytest

from mf_mappings import EXCLUDED, UNMAPPED, classify_t12_account
from mf_t12_normalizer import parse_mf_t12


# --------------------------------------------------------------------------
# 1. Pure classifier unit tests (no file deps)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("acct,name,expected", [
    ("41000-000", "Market Rent", "Gross Potential Rent"),
    ("41100-000", "Vacancy Loss", "Vacancy Loss"),
    ("41150-000", "Bad Debt - Rent", "Write-offs / Bad Debt"),
    ("61030-000", "Management Fees", "Management Fee"),
    ("62010-000", "Ad Valorem Property Taxes", "Real Estate Taxes"),
    ("63010-000", "Property Insurance", "Insurance"),
    ("71020-000", "Carpet", EXCLUDED),          # 70000-89999 below-the-line
    ("80410-000", "Lease Up - Advertising", EXCLUDED),
    (None, "Base Rent", "Gross Potential Rent"),
    (None, "Application Fee", "Application Fees"),
    (None, "Late Fee", "Late Fees"),
    (None, "Trash Removal", "Utilities — Trash"),
    (None, "Water Reimbursement", "Utility Reimbursement"),
    (None, "Painting", "Make-Ready / Turnover"),
    (None, "Some Totally Novel Line", UNMAPPED),
    # MF v0.5.2 — COA seed additions surfaced by Verona at Silver Hill (Yardi).
    ("41094-000", "Preferred Employer Discount", "Concessions"),
    ("43082-000", "Damage Fees-Carpet Replace", "Misc Other Income"),
    ("43130-000", "Interest Paid - Security Deposits", "Misc Other Income"),
    ("52025-000", "Backflow Inspections", "Contract Services"),
    ("54045-000", "Call Center Service", "Leasing & Marketing"),
    ("54070-000", "Lease-Up Expenses", "Leasing & Marketing"),
    ("54080-000", "Locator Fees", "Leasing & Marketing"),
    ("54130-000", "Signage", "Leasing & Marketing"),
])
def test_classify_account(acct, name, expected):
    assert classify_t12_account(acct, name) == expected


# --------------------------------------------------------------------------
# 2. End-to-end reconciliation against the 5 real T-12 formats
# --------------------------------------------------------------------------
_DEALS = os.path.expanduser(
    r"~/Dropbox/Erik Javellana - Deal Review/Deals under review"
)

# file, format, {income, expense, noi}, expense_artifact_tolerance
_CASES = [
    ("MF Docs/T12-NOI-Hidden-Lakes-3-31-26-xlsx.xlsx", "psi_flat",
     {"noi": 98969.0}, 0),
    (rf"{_DEALS}/MF_FL_Tallahassee_Blairstone/Broker Docs/2026 Update/Blairstone-at-Governors-Square-T12-March-2026-xlsx.xlsx",
     "quickbooks_nested", {"income": 5805382.10}, 22129),  # QB total-vs-detail artifact on exp/NOI
    (rf"{_DEALS}/MF_VA_Woodbridge_AvanaStoneyRidge/Operating Statement/Avana Stoney Ridge_April_T-12.xlsx",
     "yardi_numbered", {"income": 5346349.92, "expense": 1807466.31, "noi": 3538883.61}, 0),
    (rf"{_DEALS}/MF_NC_Leland_AscendBrunswickVillage/Income Statements/Ascend Brunswick Village - T12 (2026.04).xlsx",
     "yardi_numbered", {"income": 3572817.47, "expense": 1520302.39, "noi": 2052515.08}, 0),
    (rf"{_DEALS}/MF_FL_Tampa_CopelandVillage/Broker Docs/Financials/Copeland Village - P&L - 2026-04 T12.xlsx",
     "tzadik_nameonly", {"income": 5016396.68, "expense": 1577564.00, "noi": 3438832.68}, 0),
    # MF v0.5.2 — Yardi "Trailing Twelve Months - Detail" with numeric date-string
    # headers ("MM/DD/YYYY") + combined "ACCT - Name" col-A cells. $1 rounding
    # artifacts in the source's integer-rounded cells on expense/NOI.
    (rf"{_DEALS}/MF_MD_Suitland_VeronaAtSilverHill/2026.2 - VSH T12 - Feb26 - 3.18.26.xlsx",
     "psi_flat", {"income": 4186936.0, "expense": 2119059.0, "noi": 2067877.0}, 1),
]


@pytest.mark.parametrize("path,fmt,expected,artifact", _CASES)
def test_t12_reconciliation(path, fmt, expected, artifact):
    if not os.path.exists(path):
        pytest.skip(f"gitignored deal file absent: {path}")
    res = parse_mf_t12(path)
    assert res.format_guess == fmt, f"format misdetected: {res.format_guess}"
    assert res.coverage == 1.0, f"coverage {res.coverage:.0%}; unmapped={[l.name for l in res.unmapped]}"
    for key, want in expected.items():
        got = res.computed[key]
        tol = max(2.0, artifact + 1) if key in ("expense", "noi") else 2.0
        assert abs(got - want) <= tol, f"{key}: got {got:,.2f} want {want:,.2f}"


# --------------------------------------------------------------------------
# 3. Synthetic Yardi numeric-date / combined-acct fixture (committed, always-run)
#    Guards the MF v0.5.2 parser fix without shipping real financials. See
#    tests/fixtures/mf/_build_yardi_numdate_synthetic.py.
# --------------------------------------------------------------------------
_SYNTH = os.path.join(
    os.path.dirname(__file__), "fixtures", "mf", "yardi_numdate_synthetic.xlsx"
)


def test_yardi_numdate_synthetic():
    res = parse_mf_t12(_SYNTH)
    # numeric "MM/DD/YYYY" text headers must be recognized + labeled
    assert len(res.month_labels) == 12
    assert res.month_labels[0] == "Mar 2025"
    assert res.month_labels[-1] == "Feb 2026"
    # combined "ACCT - Name" cells must split the leading account number
    assert {"41000", "52025", "54130", "71020"} <= {ln.acct for ln in res.lines}
    # full coverage + reconciliation
    assert res.coverage == 1.0, [l.name for l in res.unmapped]
    assert abs(res.computed["income"] - 1_101_600.0) <= 2.0
    assert abs(res.computed["expense"] - 64_200.0) <= 2.0
    assert abs(res.computed["noi"] - 1_037_400.0) <= 2.0
    # the 7xxxx line stays below the NOI line
    assert abs(res.computed["excluded"] - 12_000.0) <= 2.0
