"""
dashboard_model.py — Track 5 Dashboard data model.

Pure-Python compute layer that mirrors the bundled Analyzer's `Dashboard`
sheet. Consumes the same in-memory artifacts the writers already produce
(NormalizeResult from RR, T12ParseResult from T12, optional AROutput from
AR) and returns a `DashboardModel` dataclass that `dashboard_ui.render_dashboard`
can drop straight into Streamlit.

Source of truth — design intent
-------------------------------
The xlsx Dashboard is a formula-reference layer over `T12 Analytics`. Those
formulas in turn aggregate `T12 Raw Data` (per-Description_Map-label sums)
and read `Rent Roll Recon` (per-care-type bed counts + payer mix). This
module re-implements that aggregation in Python so the dashboard tab can
render *before* the user opens the downloaded xlsx in Excel — openpyxl
can't evaluate formulas, so reading `data_only=True` on a Python-written
file returns None for every formula cell.

Re-implementing in Python rather than calling a formula engine
(`formulas`, `pycel`) keeps the dependency footprint flat (Streamlit Cloud
constraint) and the math testable. The drift guard is the regression test
that compares `compute_dashboard()` outputs against a populated Analyzer's
cached `data_only=True` values (Homestead fixture).

What this module does NOT compute
---------------------------------
- Bench thresholds (renderer concern — UI decides what's ✓/⚠/✗).
- AR roll-forward details (only the headline AR variance metric the
  Dashboard surfaces is included; the full AR module has its own sheet).
- Purchase-price-dependent metrics fall back to None when price not set
  (the xlsx Dashboard shows "—" in the same case via IFERROR).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import openpyxl
import pandas as pd

from ar_normalizer import AROutput
from normalizer import NormalizeResult
from t12_normalizer import T12ParseResult


# ---------------------------------------------------------------------------
# Description_Map cache — loaded once from the bundled Analyzer
# ---------------------------------------------------------------------------

_DESCMAP_CACHE: Optional[Dict[str, str]] = None


def load_description_map(analyzer_path: Path) -> Dict[str, str]:
    """Return a {Description → Label} dict from the Analyzer's Description_Map.

    Cached per-process — the bundled map is constant across runs.
    """
    global _DESCMAP_CACHE
    if _DESCMAP_CACHE is not None:
        return _DESCMAP_CACHE

    wb = openpyxl.load_workbook(analyzer_path, data_only=False, read_only=True)
    ws = wb["Description_Map"]
    out: Dict[str, str] = {}
    for row in ws.iter_rows(min_row=5, max_col=2, values_only=True):
        desc, label = row[0], row[1]
        if desc and label:
            out[str(desc).strip()] = str(label).strip()
    wb.close()
    _DESCMAP_CACHE = out
    return out


# ---------------------------------------------------------------------------
# Dashboard model
# ---------------------------------------------------------------------------

@dataclass
class PayerRow:
    payer: str
    resident_count: int
    census_pct: Optional[float]
    revenue: Optional[float]
    revenue_pct: Optional[float]


@dataclass
class CareTypeRow:
    care_type: str          # "Independent Living" / "Assisted Living" / "Memory Care" / "Blended"
    code: str               # "IL" / "AL" / "MC" / "ALL"
    licensed: int
    occupied: int
    occupancy_pct: Optional[float]
    adr: Optional[float]            # base rent / (occ*12)
    revpor: Optional[float]         # (base + LOC) / (occ*12)
    loc_pct: Optional[float]        # LOC / base


@dataclass
class MonthlySeries:
    month_label: str
    egi: float


@dataclass
class RiskFlag:
    label: str
    value: Optional[float]
    threshold_text: str
    status: str  # "ok" / "warn" / "bad" / "no_data"
    read_text: str


@dataclass
class DashboardModel:
    # Header
    property_name: str
    period_label: str

    # ── Headline tiles
    occupancy_pct: Optional[float]
    ebitdarm_margin: Optional[float]
    going_in_cap: Optional[float]
    revpor: Optional[float]
    egi: Optional[float]
    ebitdar: Optional[float]
    ebitdarm: Optional[float]
    price_per_bed: Optional[float]

    # ── Capacity & Occupancy
    licensed_total: int
    licensed_il: int
    licensed_al: int
    licensed_mc: int
    occupied_total: int
    occupied_il: int
    occupied_al: int
    occupied_mc: int

    # ── Revenue & rate
    gpr: Optional[float]
    blended_adr: Optional[float]   # T12 Analytics F140 -> we use the Blended back-calc
    revpab: Optional[float]
    loc_pct: Optional[float]
    bad_debt_pct: Optional[float]
    loss_to_lease_pct: Optional[float]
    vacancy_pct: Optional[float]

    # ── Profitability
    egi_per_occupied_bed: Optional[float]
    opex_per_occupied_bed: Optional[float]
    total_opex: Optional[float]
    ebitdar_margin: Optional[float]

    # ── Cost structure & labor
    total_labor_pct: Optional[float]
    direct_labor_pct: Optional[float]
    overtime_pct: Optional[float]
    agency_pct: Optional[float]
    food_ppd: Optional[float]
    mgmt_fee_pct: Optional[float]
    insurance_pct: Optional[float]

    # ── Valuation
    purchase_price: Optional[float]
    ebitdar_cap: Optional[float]

    # ── Payer mix (≤ 7 rows)
    payer_mix: List[PayerRow]

    # ── Care type breakdown (IL/AL/MC + Blended)
    care_types: List[CareTypeRow]

    # ── Monthly EGI trend (12 months)
    monthly_egi: List[MonthlySeries]

    # ── Risk flags
    risk_flags: List[RiskFlag]

    # ── AR variance tile (only if AR uploaded)
    ar_bad_debt_variance: Optional[str] = None   # text reading from AR module C56 (✓/⚪/⚠ + text)

    # ── Care level distribution (AL)
    al_care_level_dist: List[Tuple[str, int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den == 0:
        return None
    return num / den


def _safe_sum(*vals: Optional[float]) -> Optional[float]:
    """Sum non-None values. Returns None if all inputs are None."""
    nz = [v for v in vals if v is not None]
    if not nz:
        return None
    return sum(nz)


def _classify(value: Optional[float], ok: bool, warn: bool) -> str:
    if value is None:
        return "no_data"
    if ok:
        return "ok"
    if warn:
        return "warn"
    return "bad"


# Label-set constants — mirror T12 Analytics col E aggregation groups.
# Keys here must match Description_Map's Label column exactly (case-sensitive).
_LABELS_BASE_RENT = ("Base rent — IL", "Base rent — AL", "Base rent — MC")
_LABELS_LOC = ("LOC revenue — IL", "LOC revenue — AL", "LOC revenue — MC")
_LABELS_OTHER_REV = (
    "Community / move-in fees",
    "Concessions & specials",
    "Respite care",
    "Other community revenue",
)
_LABELS_DIRECT_LABOR = (
    "Care staff labor",
    "Wellness / care coordinators",
    "Contract / agency labor",
    "Activities labor",
    "Dining / food service labor",
    "Maint. & housekeeping labor",
    "Administrative labor",
    "Bonus wages",
)
_LABELS_PAYROLL_BURDEN = (
    "Overtime wages",
    "PTO wages",
    "Payroll taxes",
    "Employee benefits",
    "Workers' comp insurance",
    "Employee 401(k)",
)
_LABELS_NON_LABOR = (
    "Food cost", "Dining & kitchen supplies", "Nursing & care supplies",
    "Recreation & activity suppl.", "R&M fixed", "R&M variable",
    "HK & laundry supplies", "Sales, adv. & marketing", "Referral fees",
    "Utilities", "Telephone / IT", "P&C insurance (bundled)",
    "Auto insurance", "Fire / security monitoring", "Pest elimination",
    "Real estate taxes", "Personal property taxes", "Legal expenses",
    "Professional services", "Bad debt expense", "Permits, licenses & dues",
    "Office, admin & G&A", "Other / miscellaneous", "Lease / ground lease",
)


def _aggregate_t12(
    t12: Optional[T12ParseResult],
    descmap: Dict[str, str],
) -> Tuple[Dict[str, float], Dict[str, List[float]], List[str]]:
    """Group GL rows by Label. Returns (totals_by_label, monthly_by_label, month_labels)."""
    totals: Dict[str, float] = defaultdict(float)
    monthly: Dict[str, List[float]] = defaultdict(lambda: [0.0] * 12)
    month_labels: List[str] = [""] * 12

    if t12 is None:
        return totals, monthly, month_labels

    month_labels = list(t12.month_labels)
    while len(month_labels) < 12:
        month_labels.append("")

    for row in t12.gl_rows:
        label = descmap.get(row.description.strip())
        if not label:
            continue
        totals[label] += row.total
        for i, v in enumerate(row.monthly):
            monthly[label][i] += v
    return totals, monthly, month_labels


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_dashboard(
    rr_result: NormalizeResult,
    t12_result: Optional[T12ParseResult] = None,
    ar_result: Optional[AROutput] = None,
    *,
    property_name: str = "",
    period_label: str = "",
    purchase_price: Optional[float] = None,
    analyzer_path: Optional[Path] = None,
) -> DashboardModel:
    """Build a DashboardModel from parsed inputs.

    `analyzer_path` defaults to the bundled `ALF_Financial_Analyzer_Only.xlsx`
    in the repo root and is used only to load Description_Map.
    """
    if analyzer_path is None:
        analyzer_path = Path(__file__).parent / "ALF_Financial_Analyzer_Only.xlsx"
    descmap = load_description_map(analyzer_path)

    cond = rr_result.condensed

    # ── Capacity (bed counts by care type) ──────────────────────────────────
    # Matches Rent Roll Recon B7/C7/D7 which COUNTIFS all rows by Care Type
    # (no status filter) on the current period.
    care_col = cond["Care Type"] if "Care Type" in cond.columns else pd.Series(dtype=str)
    status_col = cond["Status"] if "Status" in cond.columns else pd.Series(dtype=str)

    licensed_il = int((care_col == "IL").sum())
    licensed_al = int((care_col == "AL").sum())
    licensed_mc = int((care_col == "MC").sum())
    licensed_total = licensed_il + licensed_al + licensed_mc

    occupied_il = int(((care_col == "IL") & (status_col == "Occupied")).sum())
    occupied_al = int(((care_col == "AL") & (status_col == "Occupied")).sum())
    occupied_mc = int(((care_col == "MC") & (status_col == "Occupied")).sum())
    occupied_total = occupied_il + occupied_al + occupied_mc

    occupancy_pct = _safe_div(occupied_total, licensed_total)

    # ── T12 aggregation ────────────────────────────────────────────────────
    totals, monthly, month_labels = _aggregate_t12(t12_result, descmap)

    base_rent_il = totals.get("Base rent — IL", 0.0)
    base_rent_al = totals.get("Base rent — AL", 0.0)
    base_rent_mc = totals.get("Base rent — MC", 0.0)
    base_rent_total = base_rent_il + base_rent_al + base_rent_mc  # T12 Analytics E16

    loc_il = totals.get("LOC revenue — IL", 0.0)
    loc_al = totals.get("LOC revenue — AL", 0.0)
    loc_mc = totals.get("LOC revenue — MC", 0.0)
    loc_total = loc_il + loc_al + loc_mc  # E23

    other_rev = sum(totals.get(l, 0.0) for l in _LABELS_OTHER_REV)
    egi = base_rent_total + loc_total + other_rev if t12_result else None  # F52

    direct_labor = sum(totals.get(l, 0.0) for l in _LABELS_DIRECT_LABOR)
    payroll_burden = sum(totals.get(l, 0.0) for l in _LABELS_PAYROLL_BURDEN)
    total_labor = direct_labor + payroll_burden  # F76

    non_labor = sum(totals.get(l, 0.0) for l in _LABELS_NON_LABOR)  # F103
    total_opex = total_labor + non_labor if t12_result else None  # F105
    mgmt_fee = totals.get("Management fee", 0.0)

    ebitdarm = (egi - total_opex) if (egi is not None and total_opex is not None) else None
    ebitdar = (ebitdarm - mgmt_fee) if (ebitdarm is not None) else None

    overtime = totals.get("Overtime wages", 0.0)
    agency = totals.get("Contract / agency labor", 0.0)
    bad_debt = totals.get("Bad debt expense", 0.0)
    food_cost = totals.get("Food cost", 0.0)
    insurance = totals.get("P&C insurance (bundled)", 0.0)

    occ_bed_months = occupied_total * 12 if occupied_total else 0
    total_bed_months = licensed_total * 12 if licensed_total else 0

    revpor = _safe_div(base_rent_total + loc_total, occ_bed_months) if t12_result else None  # ~F143
    revpab = _safe_div(egi, total_bed_months)
    egi_per_occupied_bed = _safe_div(egi, occ_bed_months)
    opex_per_occupied_bed = _safe_div(total_opex, occ_bed_months)
    blended_adr = _safe_div(base_rent_total, occ_bed_months) if t12_result else None  # E17 analogue

    loc_pct = _safe_div(loc_total, base_rent_total) if t12_result else None  # F146 ≈ E23/E16

    ebitdarm_margin = _safe_div(ebitdarm, egi)
    ebitdar_margin = _safe_div(ebitdar, egi)

    total_labor_pct = _safe_div(total_labor, egi) if t12_result else None
    direct_labor_pct = _safe_div(direct_labor, egi) if t12_result else None
    overtime_pct = _safe_div(overtime, direct_labor) if t12_result and direct_labor else None
    agency_pct = _safe_div(agency, direct_labor) if t12_result and direct_labor else None
    bad_debt_pct = _safe_div(bad_debt, egi) if t12_result else None
    mgmt_fee_pct = _safe_div(mgmt_fee, egi) if t12_result else None
    insurance_pct = _safe_div(insurance, egi) if t12_result else None
    food_ppd = _safe_div(food_cost, occupied_total * 365) if t12_result and occupied_total else None

    # GPR + vacancy + loss-to-lease use RR market rates × bed counts
    # E37 = SUM(B37:D37) where B37 = B6 * B36 * 12 (beds × avg market rate × 12)
    market_rate_col = cond["Market Rate"] if "Market Rate" in cond.columns else None
    avg_market_il = avg_market_al = avg_market_mc = 0.0
    if market_rate_col is not None:
        ml = pd.to_numeric(market_rate_col, errors="coerce")
        m_il = ml[care_col == "IL"].mean()
        m_al = ml[care_col == "AL"].mean()
        m_mc = ml[care_col == "MC"].mean()
        avg_market_il = float(m_il) if pd.notna(m_il) else 0.0
        avg_market_al = float(m_al) if pd.notna(m_al) else 0.0
        avg_market_mc = float(m_mc) if pd.notna(m_mc) else 0.0
    # Prefer T12 "Gross Rent Revenue" label when present (matches xlsx T12
    # Analytics F37 logic); fall back to RR-derived (beds × avg market × 12).
    gpr_t12 = totals.get("Gross Rent Revenue", 0.0)
    gpr_il = licensed_il * avg_market_il * 12
    gpr_al = licensed_al * avg_market_al * 12
    gpr_mc = licensed_mc * avg_market_mc * 12
    gpr_rr = gpr_il + gpr_al + gpr_mc
    if gpr_t12:
        gpr: Optional[float] = gpr_t12
    elif gpr_rr > 0:
        gpr = gpr_rr
    else:
        gpr = None

    vac_il = (licensed_il - occupied_il) * avg_market_il * 12
    vac_al = (licensed_al - occupied_al) * avg_market_al * 12
    vac_mc = (licensed_mc - occupied_mc) * avg_market_mc * 12
    vacancy_loss = vac_il + vac_al + vac_mc
    vacancy_pct = _safe_div(vacancy_loss, gpr)

    loss_to_lease = (gpr - vacancy_loss - base_rent_total) if (gpr and t12_result) else None
    if loss_to_lease is not None and loss_to_lease < 0:
        loss_to_lease = 0.0
    loss_to_lease_pct = _safe_div(loss_to_lease, gpr) if loss_to_lease is not None else None

    # ── Valuation ──────────────────────────────────────────────────────────
    going_in_cap = _safe_div(ebitdarm, purchase_price)
    ebitdar_cap = _safe_div(ebitdar, purchase_price)
    price_per_bed = _safe_div(purchase_price, licensed_total)

    # ── Payer mix ──────────────────────────────────────────────────────────
    # Mirror Rent Roll Recon B40-46 / D40-46 / F40-46 layout.
    # Census = count of all units by payer; Revenue = SUMIFS of cols H (actual)
    # and T (which is a formula column in Rent Roll Input; for the Python
    # model we use Actual Rate × 12 as the comparable revenue figure).
    PAYER_ORDER = ["Private Pay", "Medicaid", "LTC Insurance", "VA",
                   "Managed Care", "Self-Pay", "Other"]
    payer_col = cond["Payer Type"] if "Payer Type" in cond.columns else pd.Series([""] * len(cond))
    actual_rate_col = cond["Actual Rate"] if "Actual Rate" in cond.columns else pd.Series([0] * len(cond))

    payer_mix: List[PayerRow] = []
    total_payer_census = 0
    total_payer_revenue = 0.0
    rev_by_payer: Dict[str, float] = {}
    cnt_by_payer: Dict[str, int] = {}
    for payer in PAYER_ORDER:
        sel = (payer_col == payer)
        cnt = int(sel.sum())
        rev = float(pd.to_numeric(actual_rate_col[sel], errors="coerce").fillna(0).sum()) * 12
        rev_by_payer[payer] = rev
        cnt_by_payer[payer] = cnt
        total_payer_census += cnt
        total_payer_revenue += rev
    for payer in PAYER_ORDER:
        cnt = cnt_by_payer[payer]
        rev = rev_by_payer[payer]
        payer_mix.append(PayerRow(
            payer=payer,
            resident_count=cnt,
            census_pct=_safe_div(cnt, total_payer_census),
            revenue=rev if rev else None,
            revenue_pct=_safe_div(rev, total_payer_revenue),
        ))

    # ── Care type table ────────────────────────────────────────────────────
    def _care_row(name: str, code: str, lic: int, occ: int, base_rent: float, loc: float) -> CareTypeRow:
        occ_months = occ * 12 if occ else 0
        return CareTypeRow(
            care_type=name, code=code,
            licensed=lic, occupied=occ,
            occupancy_pct=_safe_div(occ, lic),
            adr=_safe_div(base_rent, occ_months) if t12_result else None,
            revpor=_safe_div(base_rent + loc, occ_months) if t12_result else None,
            loc_pct=_safe_div(loc, base_rent) if t12_result and base_rent else None,
        )
    care_types = [
        _care_row("Independent Living", "IL", licensed_il, occupied_il, base_rent_il, loc_il),
        _care_row("Assisted Living",    "AL", licensed_al, occupied_al, base_rent_al, loc_al),
        _care_row("Memory Care",        "MC", licensed_mc, occupied_mc, base_rent_mc, loc_mc),
        _care_row("Blended",            "ALL", licensed_total, occupied_total, base_rent_total, loc_total),
    ]

    # ── Monthly EGI series ─────────────────────────────────────────────────
    monthly_egi: List[MonthlySeries] = []
    if t12_result:
        for i in range(12):
            mlbl = month_labels[i] or f"M{i+1:02d}"
            # Per-month EGI mirrors the annual formula label-by-label
            m_base = sum(monthly.get(l, [0.0]*12)[i] for l in _LABELS_BASE_RENT)
            m_loc = sum(monthly.get(l, [0.0]*12)[i] for l in _LABELS_LOC)
            m_other = sum(monthly.get(l, [0.0]*12)[i] for l in _LABELS_OTHER_REV)
            m_egi = m_base + m_loc + m_other
            monthly_egi.append(MonthlySeries(month_label=mlbl, egi=m_egi))

    # ── Risk flags ─────────────────────────────────────────────────────────
    def _rf_occupancy(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="Occupancy gap to market (89.5%)",
            value=v,
            threshold_text="≥ 89.5% target",
            status=_classify(v, ok=v is not None and v >= 0.895, warn=v is not None and v >= 0.85),
            read_text="At or above NIC MAP" if (v and v >= 0.895)
                      else "Lease-up risk" if v else "No data",
        )

    def _rf_agency(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="Agency labor reliance",
            value=v,
            threshold_text="< 3% of direct labor",
            status=_classify(v, ok=v is not None and v < 0.03, warn=v is not None and v < 0.06),
            read_text="Healthy in-house staffing" if (v is not None and v < 0.03)
                      else "Elevated agency reliance" if v is not None else "No data",
        )

    def _rf_overtime(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="Overtime burden",
            value=v,
            threshold_text="< 5% of direct labor",
            status=_classify(v, ok=v is not None and v < 0.05, warn=v is not None and v < 0.10),
            read_text="Schedule well-managed" if (v is not None and v < 0.05)
                      else "Scheduling pressure" if v is not None else "No data",
        )

    def _rf_medicaid(payer_mix: List[PayerRow]) -> RiskFlag:
        for row in payer_mix:
            if row.payer == "Medicaid":
                v = row.revenue_pct
                return RiskFlag(
                    label="Medicaid concentration",
                    value=v,
                    threshold_text="< 20% of revenue",
                    status=_classify(v, ok=v is not None and v < 0.20, warn=v is not None and v < 0.35),
                    read_text="Private-pay dominant" if (v is not None and v < 0.20)
                              else "Reimbursement-rate exposure" if v is not None else "No data",
                )
        return RiskFlag(label="Medicaid concentration", value=None, threshold_text="< 20% of revenue",
                        status="no_data", read_text="No data")

    def _rf_bad_debt(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="Bad debt expense",
            value=v,
            threshold_text="< 1% of revenue",
            status=_classify(v, ok=v is not None and v < 0.01, warn=v is not None and v < 0.03),
            read_text="Strong collections" if (v is not None and v < 0.01)
                      else "Collections risk" if v is not None else "No data",
        )

    def _rf_ebitdarm(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="EBITDARM margin",
            value=v,
            threshold_text="≥ 25%",
            status=_classify(v, ok=v is not None and v >= 0.25, warn=v is not None and v >= 0.20),
            read_text="Institutional-quality margin" if (v is not None and v >= 0.25)
                      else "Sub-institutional" if v is not None else "No data",
        )

    def _rf_cap(v: Optional[float]) -> RiskFlag:
        return RiskFlag(
            label="Going-in cap rate vs market (6.2%)",
            value=v,
            threshold_text="≥ 6.5%",
            status=_classify(v, ok=v is not None and v >= 0.065, warn=v is not None and v >= 0.055),
            read_text="Wide of 6.2% market avg" if (v is not None and v >= 0.065)
                      else "Tight pricing" if v is not None else "No data",
        )

    risk_flags = [
        _rf_occupancy(occupancy_pct),
        _rf_agency(agency_pct),
        _rf_overtime(overtime_pct),
        _rf_medicaid(payer_mix),
        _rf_bad_debt(bad_debt_pct),
        _rf_ebitdarm(ebitdarm_margin),
        _rf_cap(going_in_cap),
    ]

    # ── AL care level distribution ─────────────────────────────────────────
    al_care_level_dist: List[Tuple[str, int]] = []
    if "Care Level" in cond.columns:
        al_rows = cond[care_col == "AL"]
        if len(al_rows) > 0:
            counts = al_rows["Care Level"].fillna("(none)").value_counts()
            al_care_level_dist = [(str(k), int(v)) for k, v in counts.items()]

    # ── AR variance ────────────────────────────────────────────────────────
    ar_bad_debt_variance: Optional[str] = None
    if ar_result is not None:
        # Mirror Dashboard!K11 = AR & Collections!C56 (✓/⚪/⚠ + text)
        # AR module computes this; for the dashboard we just show the AR total
        # vs T12 bad debt comparison narrative.
        ar_writeoff = ar_result.writeoffs_period or 0.0
        annualized_writeoff = ar_writeoff  # AR writer annualizes already if period-aware
        if t12_result and bad_debt:
            diff = bad_debt - annualized_writeoff
            pct = abs(diff) / bad_debt if bad_debt else 0
            sym = "✓" if pct < 0.10 else "⚠" if pct < 0.25 else "⚪"
            ar_bad_debt_variance = (
                f"{sym} T12 bad debt ${bad_debt:,.0f} vs AR writeoffs ${annualized_writeoff:,.0f} "
                f"({pct*100:.1f}% variance)"
            )
        else:
            ar_bad_debt_variance = f"AR aging total ${ar_result.total_ar:,.0f}"

    return DashboardModel(
        property_name=property_name or "(unnamed property)",
        period_label=period_label or (month_labels[-1] if any(month_labels) else "T12"),
        occupancy_pct=occupancy_pct,
        ebitdarm_margin=ebitdarm_margin,
        going_in_cap=going_in_cap,
        revpor=revpor,
        egi=egi,
        ebitdar=ebitdar,
        ebitdarm=ebitdarm,
        price_per_bed=price_per_bed,
        licensed_total=licensed_total,
        licensed_il=licensed_il,
        licensed_al=licensed_al,
        licensed_mc=licensed_mc,
        occupied_total=occupied_total,
        occupied_il=occupied_il,
        occupied_al=occupied_al,
        occupied_mc=occupied_mc,
        gpr=gpr,
        blended_adr=blended_adr,
        revpab=revpab,
        loc_pct=loc_pct,
        bad_debt_pct=bad_debt_pct,
        loss_to_lease_pct=loss_to_lease_pct,
        vacancy_pct=vacancy_pct,
        egi_per_occupied_bed=egi_per_occupied_bed,
        opex_per_occupied_bed=opex_per_occupied_bed,
        total_opex=total_opex,
        ebitdar_margin=ebitdar_margin,
        total_labor_pct=total_labor_pct,
        direct_labor_pct=direct_labor_pct,
        overtime_pct=overtime_pct,
        agency_pct=agency_pct,
        food_ppd=food_ppd,
        mgmt_fee_pct=mgmt_fee_pct,
        insurance_pct=insurance_pct,
        purchase_price=purchase_price,
        ebitdar_cap=ebitdar_cap,
        payer_mix=payer_mix,
        care_types=care_types,
        monthly_egi=monthly_egi,
        risk_flags=risk_flags,
        ar_bad_debt_variance=ar_bad_debt_variance,
        al_care_level_dist=al_care_level_dist,
    )
