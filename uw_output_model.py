"""
uw_output_model.py — Track 4 / in-Python UW Output evaluator.

Pure-Python compute layer that reproduces the Analyzer's `UW Output` values
*without* requiring Excel to evaluate the workbook's formulas. It exists to
kill the **cache caveat**: the UW Template writer reads cached formula values
from the Analyzer (`data_only=True`), but an Analyzer the app just built
in-memory via openpyxl has formula *text* with no cached values — so every
`uw_output`-system concept came through `no_source`, leaving the populated
UW Template's `T-12 Analysis` tab blank unless the operator round-tripped
the Analyzer through Excel first.

This module computes those values directly from the same parsed artifacts
the writers already consume (`NormalizeResult` from RR, `T12ParseResult`
from T12) and returns a `{concept_key: value}` dict the writer accepts as a
**fallback** (used only when the Analyzer cell is blank — an analyst-saved
Analyzer with real cached values still wins).

Why this is correct
-------------------
`UW Output` is a thin reference layer over `T12 Analytics`, which in turn:
  - sums `T12 Raw Data` per Description_Map Label (every opex / labor /
    other-revenue line item), and
  - reads `Rent Roll Recon` per-care-type bed counts.

The **normalized** scenario (UW Output col F, the default) reads T12 Analytics
col F for opex — and `F{r} = =E{r}` for every line item, so normalized == the
T12 actual by default. For base rent / LOC the normalized figure is the
"stabilized" value (`E20`/`E27`), but the stabilized formula
`B20 = B6·B10·B19·12` collapses algebraically to the T12 actual base rent
when the target-occupancy assumption `B10 = B8` (its default — `B10` literally
references `B8`). Verified empirically on the Homestead fixture:
`E16 == E20`, `E23 == E27`, `E52 == F52`, `E108 == F108`.

So computing T12 actuals (sum by Label) + RR bed counts reproduces both
scenarios for a freshly-built Analyzer. Analyst normalization overrides happen
*later* in Excel; once the analyst saves and re-uploads, the cached values
exist and the writer prefers them over this fallback.

This re-uses `dashboard_model`'s aggregation primitives (Track 5) rather than
re-implementing them — same pure-Python pattern, same Description_Map labels,
same drift-guard philosophy.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from normalizer import NormalizeResult
from t12_normalizer import T12ParseResult

# Re-use Track 5's aggregation + label constants — single source of truth for
# the Description_Map label vocabulary and the GL-by-label grouping.
from dashboard_model import (
    load_description_map,
    _aggregate_t12,
    _LABELS_OTHER_REV,
    _LABELS_DIRECT_LABOR,
    _LABELS_PAYROLL_BURDEN,
    _LABELS_NON_LABOR,
)

# Bundled Analyzer is used only to load Description_Map (constant across runs).
_BUNDLED_ANALYZER = Path(__file__).parent / "ALF_Financial_Analyzer_Only.xlsx"


# ---------------------------------------------------------------------------
# Per-concept → Description_Map label mapping
# ---------------------------------------------------------------------------
# Each key here is a registry concept whose source.system == 'uw_output' and
# whose value is a single GL line item (1:1 with a T12 Analytics MATCH(...)).
# Subtotals (EGI / labor total / EBITDARM / ...) are computed below, not here.
_CONCEPT_LABEL: Dict[str, str] = {
    # ── Other revenue (UW Output 8-11 → T12 Analytics 47-50) ──
    "community_movein_fees":      "Community / move-in fees",
    "concessions_specials":       "Concessions & specials",
    "respite_care":               "Respite care",
    "other_community_revenue":    "Other community revenue",
    # ── Direct labor (UW Output 22-29 → T12 Analytics 57-64) ──
    "labor_care_staff":           "Care staff labor",
    "labor_wellness":             "Wellness / care coordinators",
    "labor_agency":               "Contract / agency labor",
    "labor_activities":           "Activities labor",
    "labor_dining":               "Dining / food service labor",
    "labor_maint_hk":             "Maint. & housekeeping labor",
    "labor_admin":                "Administrative labor",
    "labor_bonus":                "Bonus wages",
    # ── Payroll burden (UW Output 30-35 → T12 Analytics 68-73) ──
    "labor_overtime":             "Overtime wages",
    "labor_pto":                  "PTO wages",
    "labor_payroll_taxes":        "Payroll taxes",
    "labor_benefits":             "Employee benefits",
    "labor_workers_comp":         "Workers' comp insurance",
    "labor_401k":                 "Employee 401(k)",
    # ── Non-labor opex (UW Output 38-61 → T12 Analytics 79-102) ──
    "opex_food_cost":             "Food cost",
    "opex_dining_supplies":       "Dining & kitchen supplies",
    "opex_nursing_supplies":      "Nursing & care supplies",
    "opex_recreation_supplies":   "Recreation & activity suppl.",
    "opex_rm_fixed":              "R&M fixed",
    "opex_rm_variable":           "R&M variable",
    "opex_hk_laundry":            "HK & laundry supplies",
    "opex_marketing":             "Sales, adv. & marketing",
    "opex_referral_fees":         "Referral fees",
    "opex_utilities":             "Utilities",
    "opex_telephone_it":          "Telephone / IT",
    "opex_pc_insurance":          "P&C insurance (bundled)",
    "opex_auto_insurance":        "Auto insurance",
    "opex_fire_security":         "Fire / security monitoring",
    "opex_pest":                  "Pest elimination",
    "opex_re_taxes":              "Real estate taxes",
    "opex_personal_prop_taxes":   "Personal property taxes",
    "opex_legal":                 "Legal expenses",
    "opex_professional_services": "Professional services",
    "opex_bad_debt_expense":      "Bad debt expense",
    "opex_permits_licenses":      "Permits, licenses & dues",
    "opex_office_ga":             "Office, admin & G&A",
    "opex_misc":                  "Other / miscellaneous",
    "opex_lease_ground":          "Lease / ground lease",
}


def _bed_counts(cond: pd.DataFrame) -> Dict[str, int]:
    """Licensed + occupied bed counts by care type, mirroring Rent Roll Recon
    B7/C7/D7 (licensed = all rows by Care Type) and the occupied COUNTIFS
    (Status == 'Occupied')."""
    care = cond["Care Type"] if "Care Type" in cond.columns else pd.Series(dtype=str)
    status = cond["Status"] if "Status" in cond.columns else pd.Series(dtype=str)
    out: Dict[str, int] = {}
    for code in ("IL", "AL", "MC"):
        out[f"licensed_{code.lower()}"] = int((care == code).sum())
        out[f"occupied_{code.lower()}"] = int(((care == code) & (status == "Occupied")).sum())
    return out


def _avg_market_by_care(cond: pd.DataFrame) -> Dict[str, float]:
    """Avg Market Rate over *occupied* beds by care type — mirrors T12
    Analytics B36/C36/D36 AVERAGEIFS(...,Status='Occupied',CareType=...)."""
    out = {"IL": 0.0, "AL": 0.0, "MC": 0.0}
    if "Market Rate" not in cond.columns or "Care Type" not in cond.columns:
        return out
    care = cond["Care Type"]
    status = cond["Status"] if "Status" in cond.columns else pd.Series([""] * len(cond))
    mkt = pd.to_numeric(cond["Market Rate"], errors="coerce")
    for code in ("IL", "AL", "MC"):
        sel = (care == code) & (status == "Occupied")
        m = mkt[sel].mean()
        out[code] = float(m) if pd.notna(m) else 0.0
    return out


def compute_uw_output_values(
    rr_result: NormalizeResult,
    t12_result: Optional[T12ParseResult] = None,
    *,
    analyzer_path: Optional[Path] = None,
    scenario: str = "normalized",
) -> Dict[str, Any]:
    """Return ``{concept_key: value}`` for the UW-Output-derived registry
    concepts, computed in pure Python.

    Intended to be passed to ``populate_uw_template(..., computed_values=...)``
    as a fallback for the cache caveat. Only includes T12-derived keys when a
    ``T12ParseResult`` is present (so a missing T12 stays ``no_source`` rather
    than writing a spurious 0). Bed counts and RR-derived GPR are always
    included.

    ``scenario`` is accepted for symmetry with the writer but does not change
    the output: normalized == T12 actual at the Analyzer's default assumptions
    (see module docstring). Kept as a parameter so a future analyst-override
    path can branch on it if needed.
    """
    descmap = load_description_map(analyzer_path or _BUNDLED_ANALYZER)
    totals, _monthly, _months = _aggregate_t12(t12_result, descmap)
    has_t12 = t12_result is not None

    cond = rr_result.condensed
    beds = _bed_counts(cond)
    mkt = _avg_market_by_care(cond)

    out: Dict[str, Any] = {}

    # ── Bed counts (always available — RR-driven) ───────────────────────────
    out["licensed_beds_il"] = beds["licensed_il"]
    out["licensed_beds_al"] = beds["licensed_al"]
    out["licensed_beds_mc"] = beds["licensed_mc"]
    out["licensed_beds_total"] = (
        beds["licensed_il"] + beds["licensed_al"] + beds["licensed_mc"]
    )
    out["occupied_beds_il"] = beds["occupied_il"]
    out["occupied_beds_al"] = beds["occupied_al"]
    out["occupied_beds_mc"] = beds["occupied_mc"]

    # ── GPR waterfall (RR-driven; mirrors T12 Analytics F37/F38/F40) ─────────
    # B37 = beds × market × 12 ; B38 = (lic − occ) × market × 12
    gpr = 0.0
    vac = 0.0
    for code in ("IL", "AL", "MC"):
        lic = beds[f"licensed_{code.lower()}"]
        occ = beds[f"occupied_{code.lower()}"]
        rate = mkt[code]
        gpr += lic * rate * 12
        vac += (lic - occ) * rate * 12
    if gpr > 0:
        out["gpr_base"] = gpr
        out["physical_vacancy_loss"] = vac

    # ── T12-derived line items, subtotals, and the P&L chain ─────────────────
    if has_t12:
        def L(label: str) -> float:
            # IFERROR(INDEX/MATCH, 0) → missing labels resolve to 0, matching
            # the Analyzer's T12 Analytics formulas.
            return float(totals.get(label, 0.0))

        # 1:1 line items
        for key, label in _CONCEPT_LABEL.items():
            out[key] = L(label)

        # Revenue: base rent / LOC (normalized == actual at default assumptions)
        base_rent = L("Base rent — IL") + L("Base rent — AL") + L("Base rent — MC")
        loc = L("LOC revenue — IL") + L("LOC revenue — AL") + L("LOC revenue — MC")
        other_rev = sum(L(x) for x in _LABELS_OTHER_REV)
        out["base_rent_normalized"] = base_rent
        out["loc_revenue"] = loc
        out["egi"] = base_rent + loc + other_rev

        # Bad debt is written to N62 (revenue contra) via this concept; the
        # opex_bad_debt_expense → N106 copy is special-skipped by the writer.
        out["bad_debt_writeoffs_revenue"] = L("Bad debt expense")

        # Loss to lease (needs T12 base rent): F40 = SUM(B37−B38−B16) by care.
        if gpr > 0:
            ltl = 0.0
            for code in ("IL", "AL", "MC"):
                lic = beds[f"licensed_{code.lower()}"]
                occ = beds[f"occupied_{code.lower()}"]
                rate = mkt[code]
                gpr_c = lic * rate * 12
                vac_c = (lic - occ) * rate * 12
                base_c = L(f"Base rent — {code}")
                ltl += gpr_c - vac_c - base_c
            out["loss_to_lease"] = ltl

        # Subtotals
        direct_labor = sum(L(x) for x in _LABELS_DIRECT_LABOR)
        payroll_burden = sum(L(x) for x in _LABELS_PAYROLL_BURDEN)
        total_labor = direct_labor + payroll_burden
        non_labor = sum(L(x) for x in _LABELS_NON_LABOR)
        total_opex_excl_mgmt = total_labor + non_labor
        mgmt_fee = L("Management fee")

        out["labor_total"] = total_labor
        out["opex_nonlabor_total"] = non_labor
        out["opex_total_excl_mgmt"] = total_opex_excl_mgmt
        out["opex_total_incl_mgmt"] = total_opex_excl_mgmt + mgmt_fee
        out["mgmt_fee"] = mgmt_fee

        # P&L chain (depreciation excluded from EBITDA → 0)
        egi = out["egi"]
        ebitdarm = egi - total_opex_excl_mgmt
        ebitdar = ebitdarm - mgmt_fee
        out["ebitdarm"] = ebitdarm
        out["ebitdar"] = ebitdar
        out["ebitda"] = ebitdar  # less depreciation (0)

    return out


# Canonical Layer-1 raw-line order (P&L sequence) + revenue classification.
_T12_RAW_LINE_ORDER: tuple = (
    "Base rent — IL", "Base rent — AL", "Base rent — MC",
    "Gross Rent Revenue",
    "LOC revenue — IL", "LOC revenue — AL", "LOC revenue — MC",
    "2nd Person Revenue",
    *_LABELS_OTHER_REV,
    *_LABELS_DIRECT_LABOR,
    *_LABELS_PAYROLL_BURDEN,
    *_LABELS_NON_LABOR,
    "Management fee",
)
_T12_RAW_REVENUE_LABELS: frozenset = frozenset({
    "Base rent — IL", "Base rent — AL", "Base rent — MC", "Gross Rent Revenue",
    "LOC revenue — IL", "LOC revenue — AL", "LOC revenue — MC",
    "2nd Person Revenue", *_LABELS_OTHER_REV,
})


def compute_t12_raw_lines(
    t12_result: Optional[T12ParseResult] = None,
    *,
    analyzer_path: Optional[Path] = None,
) -> list:
    """Return the summarized raw T-12, grouped by Description_Map label.

    One entry per label that has GL data, each a dict::

        {"label": str, "section": "Revenue"|"Expense",
         "descriptions": [raw GL account names], "monthly": [12 floats],
         "total": float}

    Feeds the UW Template writer's Section I (Layer 1 — Raw T-12) population.
    Computed from the parsed T12 (not read from the Analyzer's `T12 Raw Data`
    sheet, whose monthly cells are formulas and would be blank on a freshly
    built Analyzer — same cache caveat as the rest of the engine). Ordered in
    P&L sequence; any label outside the canonical order is appended.
    """
    if t12_result is None:
        return []
    descmap = load_description_map(analyzer_path or _BUNDLED_ANALYZER)

    by_label: Dict[str, dict] = {}
    for row in t12_result.gl_rows:
        desc = (row.description or "").strip()
        label = descmap.get(desc)
        if not label:
            continue  # unmapped lines are excluded (mirrors T12 Raw Data)
        d = by_label.get(label)
        if d is None:
            d = {
                "label": label,
                "section": "Revenue" if label in _T12_RAW_REVENUE_LABELS else "Expense",
                "descriptions": [],
                "monthly": [0.0] * 12,
                "total": 0.0,
            }
            by_label[label] = d
        if desc and desc not in d["descriptions"]:
            d["descriptions"].append(desc)
        d["total"] += float(row.total or 0.0)
        for i, v in enumerate(row.monthly or []):
            if i < 12:
                d["monthly"][i] += float(v or 0.0)

    order = {lbl: i for i, lbl in enumerate(_T12_RAW_LINE_ORDER)}
    return sorted(by_label.values(), key=lambda d: order.get(d["label"], 9999))


def compute_uw_output_monthly(
    rr_result: NormalizeResult,
    t12_result: Optional[T12ParseResult] = None,
    *,
    analyzer_path: Optional[Path] = None,
) -> Dict[str, list]:
    """Return ``{concept_key: [12 monthly floats]}`` for the T12-derived UW
    Output concepts that have a monthly breakdown.

    Feeds the writer's `computed_monthly=` parameter, which pastes the 12
    values into the UW Template's `T-12 Analysis` Layer-3 monthly grid (cols
    B–M; col N is the T-12 Total). Mirrors `_aggregate_t12`'s month-by-month
    GL bucketing — the same primitive `compute_dashboard` / the annual
    evaluator use — so monthly sums reconcile to the annual values to the
    penny.

    Returns ``{}`` when no T12 is present. GPR / physical_vacancy_loss /
    loss_to_lease are intentionally omitted — they're rent-roll *projections*
    with no monthly source (their rows stay blank in the monthly grid, same as
    the Analyzer's own T12 Analytics).
    """
    if t12_result is None:
        return {}
    descmap = load_description_map(analyzer_path or _BUNDLED_ANALYZER)
    _totals, monthly, _months = _aggregate_t12(t12_result, descmap)

    def M(label: str) -> list:
        arr = monthly.get(label)
        return list(arr) if arr else [0.0] * 12

    def Msum(labels) -> list:
        out = [0.0] * 12
        for lb in labels:
            arr = monthly.get(lb)
            if arr:
                for i in range(12):
                    out[i] += arr[i]
        return out

    res: Dict[str, list] = {}

    # 1:1 line items (labor + non-labor opex + other revenue)
    for key, label in _CONCEPT_LABEL.items():
        res[key] = M(label)

    # Revenue aggregates
    base = Msum(["Base rent — IL", "Base rent — AL", "Base rent — MC"])
    loc = Msum(["LOC revenue — IL", "LOC revenue — AL", "LOC revenue — MC"])
    other = Msum(_LABELS_OTHER_REV)
    res["base_rent_normalized"] = base
    res["loc_revenue"] = loc
    res["bad_debt_writeoffs_revenue"] = M("Bad debt expense")
    egi = [base[i] + loc[i] + other[i] for i in range(12)]
    res["egi"] = egi

    # Subtotals + P&L chain
    direct = Msum(_LABELS_DIRECT_LABOR)
    burden = Msum(_LABELS_PAYROLL_BURDEN)
    labor = [direct[i] + burden[i] for i in range(12)]
    nonlabor = Msum(_LABELS_NON_LABOR)
    total_opex = [labor[i] + nonlabor[i] for i in range(12)]
    mgmt = M("Management fee")
    res["labor_total"] = labor
    res["opex_nonlabor_total"] = nonlabor
    res["opex_total_excl_mgmt"] = total_opex
    res["opex_total_incl_mgmt"] = [total_opex[i] + mgmt[i] for i in range(12)]
    res["mgmt_fee"] = mgmt
    ebitdarm = [egi[i] - total_opex[i] for i in range(12)]
    ebitdar = [ebitdarm[i] - mgmt[i] for i in range(12)]
    res["ebitdarm"] = ebitdarm
    res["ebitdar"] = ebitdar
    res["ebitda"] = ebitdar  # less depreciation (0)

    return res
