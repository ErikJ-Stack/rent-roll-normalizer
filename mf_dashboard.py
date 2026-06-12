"""
mf_dashboard.py — MF (multifamily) dashboard: compute + render.

The MF counterpart of Track 5's `dashboard_model.py`/`dashboard_ui.py`, kept
in one module (MF convention: lean single-purpose files). Surfaces the
first-look screen institutional multifamily underwriters run before anything
else:

  - The headline strip: units, physical occupancy, in-place rent/unit, T-12
    NOI + margin, going-in cap at the ask, price/unit, economic occupancy.
  - The income waterfall ledger: GPR → loss-to-lease → physical vacancy →
    concessions → bad debt → employee/down units → other income → EGI →
    OpEx → NOI, each line as % of GPR (income contras) or % of EGI (expense).
  - T-3 vs T-12 trajectory: trailing-3 annualized revenue against the full
    trailing-12 — the standard institutional read on whether income is
    accelerating or rolling over.
  - Unit mix & rents (count / avg sqft / in-place vs market / $/SF) and the
    loss-to-lease gap by floorplan.
  - OpEx table in the two units institutional reviewers sanity-check:
    $/unit/year and % of EGI.
  - Risk flags: occupancy, economic-vacancy drag, concession burn, bad debt,
    expense-ratio too HIGH and too LOW (understated opex is the classic
    broker-pro-forma tell), management fee floor, tax-reassessment reminder,
    delinquency (when AR is joined), and T-3 vs T-12 divergence.

Inputs are the already-parsed MF objects (`MFRRResult`, `MFT12Result`) — no
file I/O here. Rendering reuses the cockpit component classes from
`branding.inject_cockpit_css()` (.t5-tile, .ck-panel/.ck-ledger, .ck-flag) so
the MF dashboard reads identically to the ALF one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
import streamlit as st

# ── Special income buckets (exact _StdCOA names from mf_mappings) ────────────
_B_GPR = "Gross Potential Rent"
_B_VAC = "Vacancy Loss"
_B_CONC = "Concessions"
_B_BD = "Write-offs / Bad Debt"
_B_LTL = "Gain/Loss on Market Rent"
_B_EMP = "Employee Units"
_B_DOWN = "Down Units Loss"
_CONTRA_BUCKETS = (_B_LTL, _B_VAC, _B_CONC, _B_BD, _B_EMP, _B_DOWN)


@dataclass
class MFFlag:
    label: str
    status: str          # "ok" | "warn" | "bad" | "info"
    detail: str


@dataclass
class MFUnitMixRow:
    unit_type: str
    count: int
    avg_sqft: Optional[float]
    avg_market: Optional[float]
    avg_in_place: Optional[float]   # occupied units only
    in_place_psf: Optional[float]
    ltl_pct: Optional[float]        # 1 − in-place/market


@dataclass
class MFOpexRow:
    bucket: str
    annual: float
    per_unit: Optional[float]
    pct_egi: Optional[float]


@dataclass
class MFDashboardModel:
    property_name: str = ""
    period_label: str = ""

    # Rent roll
    units: int = 0
    occupied: int = 0
    vacant: int = 0
    physical_occ: Optional[float] = None
    avg_in_place_rent: Optional[float] = None   # occupied, actual charges /mo
    avg_market_rent: Optional[float] = None     # all units
    loss_to_lease_pct: Optional[float] = None   # 1 − in-place/market (occupied)
    avg_sqft: Optional[float] = None
    in_place_psf: Optional[float] = None
    total_sqft: Optional[float] = None
    unit_mix: List[MFUnitMixRow] = field(default_factory=list)

    # T-12 income waterfall (annual $; contras carry their GL sign — negative)
    gpr: Optional[float] = None
    ltl: Optional[float] = None
    vacancy: Optional[float] = None
    concessions: Optional[float] = None
    bad_debt: Optional[float] = None
    emp_down: Optional[float] = None            # employee + down units
    net_rental: Optional[float] = None
    other_income: Optional[float] = None
    egi: Optional[float] = None                 # total income (computed)
    opex_total: Optional[float] = None
    noi: Optional[float] = None
    noi_reported: Optional[float] = None
    noi_margin: Optional[float] = None
    opex_ratio: Optional[float] = None
    opex_per_unit: Optional[float] = None
    economic_occ: Optional[float] = None        # net rental / GPR
    other_income_per_unit: Optional[float] = None
    opex_rows: List[MFOpexRow] = field(default_factory=list)

    # Trajectory
    month_labels: List[str] = field(default_factory=list)
    monthly_income: List[float] = field(default_factory=list)
    t3_annualized_income: Optional[float] = None
    t3_vs_t12_pct: Optional[float] = None       # (T-3 ann / T-12) − 1

    # Delinquency (RR balance + AR join when present)
    delinquent_units: int = 0
    delinquent_total: Optional[float] = None
    ar_60_plus: Optional[float] = None

    # Valuation (optional ask)
    purchase_price: Optional[float] = None
    going_in_cap: Optional[float] = None
    price_per_unit: Optional[float] = None
    price_per_sf: Optional[float] = None
    grm: Optional[float] = None                 # price / annual GPR

    flags: List[MFFlag] = field(default_factory=list)


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or not b:
        return None
    return a / b


def compute_mf_dashboard(rr=None, t12=None, *, purchase_price: Optional[int] = None,
                         property_name: str = "", period_label: str = "") -> MFDashboardModel:
    """Build the dashboard model from parsed MF objects. Either input may be
    None — the renderer degrades gracefully (RR-only or T-12-only views)."""
    m = MFDashboardModel(property_name=property_name, period_label=period_label)

    # ── Rent roll side ───────────────────────────────────────────────────────
    if rr is not None and rr.units:
        units = rr.units
        m.units = len(units)
        m.occupied = rr.occupied
        m.vacant = rr.vacant
        m.physical_occ = _safe_div(m.occupied, m.units)

        occ_rents = [u.actual_charges for u in units
                     if u.status.startswith("Occupied") and u.actual_charges > 0]
        mkt_rents = [u.market_rent for u in units if u.market_rent > 0]
        m.avg_in_place_rent = (sum(occ_rents) / len(occ_rents)) if occ_rents else None
        m.avg_market_rent = (sum(mkt_rents) / len(mkt_rents)) if mkt_rents else None

        # Loss-to-lease on occupied units with both sides present.
        pairs = [(u.actual_charges, u.market_rent) for u in units
                 if u.status.startswith("Occupied")
                 and u.actual_charges > 0 and u.market_rent > 0]
        if pairs:
            ip = sum(p[0] for p in pairs)
            mk = sum(p[1] for p in pairs)
            m.loss_to_lease_pct = (1 - ip / mk) if mk else None

        sqfts = [u.sqft for u in units if u.sqft]
        m.avg_sqft = (sum(sqfts) / len(sqfts)) if sqfts else None
        m.total_sqft = sum(sqfts) if sqfts else None
        if m.avg_in_place_rent and m.avg_sqft:
            m.in_place_psf = m.avg_in_place_rent / m.avg_sqft

        # Unit mix by floorplan/type.
        by_type: dict[str, list] = {}
        for u in units:
            by_type.setdefault(u.unit_type or "(untyped)", []).append(u)
        for ut, lst in sorted(by_type.items()):
            t_sq = [u.sqft for u in lst if u.sqft]
            t_mkt = [u.market_rent for u in lst if u.market_rent > 0]
            t_ip = [u.actual_charges for u in lst
                    if u.status.startswith("Occupied") and u.actual_charges > 0]
            avg_sq = (sum(t_sq) / len(t_sq)) if t_sq else None
            avg_mk = (sum(t_mkt) / len(t_mkt)) if t_mkt else None
            avg_ip = (sum(t_ip) / len(t_ip)) if t_ip else None
            m.unit_mix.append(MFUnitMixRow(
                unit_type=ut, count=len(lst), avg_sqft=avg_sq,
                avg_market=avg_mk, avg_in_place=avg_ip,
                in_place_psf=(avg_ip / avg_sq) if (avg_ip and avg_sq) else None,
                ltl_pct=(1 - avg_ip / avg_mk) if (avg_ip and avg_mk) else None,
            ))

        # Delinquency snapshot from the RR balance column (+ AR join fields).
        delinq = [u for u in units if (u.balance or 0) > 100]
        m.delinquent_units = len(delinq)
        m.delinquent_total = sum(u.balance for u in delinq) if delinq else 0.0
        ar60 = sum((u.ar_61_90 or 0) + (u.ar_90_plus or 0) for u in units)
        m.ar_60_plus = ar60 if ar60 else None

    # ── T-12 side ───────────────────────────────────────────────────────────
    # Aggregation follows the statement SECTION (income vs expense), matching
    # mf_t12_normalizer's `computed` reconciliation — utility-rebill contras
    # that sit in the expense section reduce opex rather than inflating income,
    # and the OpEx table sums exactly to `computed["expense"]`.
    if t12 is not None and t12.lines:
        sums: dict[str, float] = {}            # income-section bucket sums
        opex_sums: dict[str, float] = {}        # expense-section bucket sums
        n_months = len(t12.month_labels) or 12
        monthly_income = [0.0] * n_months
        for ln in t12.lines:
            if ln.section == "income":
                sums[ln.bucket] = sums.get(ln.bucket, 0.0) + ln.total
                for i, v in enumerate(ln.monthly[:n_months]):
                    monthly_income[i] += v
            elif ln.section == "expense":
                opex_sums[ln.bucket] = opex_sums.get(ln.bucket, 0.0) + ln.total

        m.gpr = sums.get(_B_GPR)
        m.ltl = sums.get(_B_LTL)
        m.vacancy = sums.get(_B_VAC)
        m.concessions = sums.get(_B_CONC)
        m.bad_debt = sums.get(_B_BD)
        m.emp_down = (sums.get(_B_EMP, 0.0) + sums.get(_B_DOWN, 0.0)) or None

        m.egi = t12.computed.get("income")
        m.opex_total = t12.computed.get("expense")
        m.noi = t12.computed.get("noi")
        m.noi_reported = t12.reported.get("noi")

        if m.gpr:
            contra_total = sum(sums.get(b, 0.0) for b in _CONTRA_BUCKETS)
            m.net_rental = m.gpr + contra_total          # contras are negative
            m.economic_occ = m.net_rental / m.gpr
        if m.egi is not None and m.net_rental is not None:
            m.other_income = m.egi - m.net_rental
        m.noi_margin = _safe_div(m.noi, m.egi)
        m.opex_ratio = _safe_div(m.opex_total, m.egi)
        if m.units:
            m.opex_per_unit = _safe_div(m.opex_total, m.units)
            m.other_income_per_unit = _safe_div(m.other_income, m.units)

        # OpEx table, largest first — expense-section buckets, so the rows
        # sum exactly to computed["expense"] (rebill contras included).
        for bucket, total in sorted(opex_sums.items(), key=lambda kv: -abs(kv[1])):
            m.opex_rows.append(MFOpexRow(
                bucket=bucket, annual=total,
                per_unit=_safe_div(total, m.units) if m.units else None,
                pct_egi=_safe_div(total, m.egi),
            ))

        # Trajectory — T-3 annualized vs T-12 (institutional standard read).
        m.month_labels = list(t12.month_labels)
        m.monthly_income = monthly_income
        populated = [v for v in monthly_income if abs(v) > 0.005]
        if len(populated) >= 12 and len(monthly_income) >= 3:
            t3 = sum(monthly_income[-3:]) * 4
            m.t3_annualized_income = t3
            if m.egi:
                m.t3_vs_t12_pct = t3 / m.egi - 1

    # ── Valuation at the ask ─────────────────────────────────────────────────
    if purchase_price:
        m.purchase_price = float(purchase_price)
        m.going_in_cap = _safe_div(m.noi, m.purchase_price)
        m.price_per_unit = _safe_div(m.purchase_price, m.units) if m.units else None
        m.price_per_sf = _safe_div(m.purchase_price, m.total_sqft)
        m.grm = _safe_div(m.purchase_price, m.gpr)

    _build_flags(m)
    return m


def _build_flags(m: MFDashboardModel) -> None:
    f = m.flags

    if m.physical_occ is not None:
        if m.physical_occ < 0.85:
            f.append(MFFlag(f"Physical occupancy {m.physical_occ:.1%}", "bad",
                            "below 85% — lease-up / distress territory"))
        elif m.physical_occ < 0.90:
            f.append(MFFlag(f"Physical occupancy {m.physical_occ:.1%}", "warn",
                            "below the 90% stabilized threshold"))
        else:
            f.append(MFFlag(f"Physical occupancy {m.physical_occ:.1%}", "ok",
                            f"{m.occupied}/{m.units} units"))

    if m.economic_occ is not None and m.physical_occ is not None:
        gap = m.physical_occ - m.economic_occ
        if gap > 0.05:
            f.append(MFFlag(f"Economic occ {m.economic_occ:.1%} vs physical {m.physical_occ:.1%}", "warn",
                            "5%+ economic drag — check concessions/bad debt/LTL"))
        else:
            f.append(MFFlag(f"Economic occupancy {m.economic_occ:.1%}", "ok",
                            "collections track physical occupancy"))

    if m.loss_to_lease_pct is not None:
        if m.loss_to_lease_pct > 0.08:
            f.append(MFFlag(f"Loss-to-lease {m.loss_to_lease_pct:.1%}", "warn",
                            "8%+ gap to market — mark-to-market upside, verify market rents"))
        elif m.loss_to_lease_pct < -0.02:
            f.append(MFFlag(f"Rents {-m.loss_to_lease_pct:.1%} ABOVE market", "warn",
                            "in-place over market — rollover risk on renewal"))
        else:
            f.append(MFFlag(f"Loss-to-lease {m.loss_to_lease_pct:.1%}", "ok",
                            "in-place rents near market"))

    if m.concessions is not None and m.gpr:
        c = abs(m.concessions) / m.gpr
        f.append(MFFlag(f"Concessions {c:.1%} of GPR", "warn" if c > 0.02 else "ok",
                        "above 2% — concession burn" if c > 0.02 else "within the 2% norm"))

    if m.bad_debt is not None and m.gpr:
        b = abs(m.bad_debt) / m.gpr
        status = "bad" if b > 0.02 else ("warn" if b > 0.01 else "ok")
        f.append(MFFlag(f"Bad debt {b:.1%} of GPR", status,
                        "collections problem" if b > 0.02 else
                        ("above the 1% norm" if b > 0.01 else "healthy collections")))

    if m.opex_ratio is not None:
        if m.opex_ratio > 0.55:
            f.append(MFFlag(f"OpEx ratio {m.opex_ratio:.1%} of EGI", "warn",
                            "heavy expense load — utility/payroll/tax drivers?"))
        elif m.opex_ratio < 0.32:
            f.append(MFFlag(f"OpEx ratio {m.opex_ratio:.1%} of EGI", "warn",
                            "suspiciously LOW — owner-managed books often understate "
                            "payroll/R&M; underwrite to market expense loads"))
        else:
            f.append(MFFlag(f"OpEx ratio {m.opex_ratio:.1%} of EGI", "ok",
                            f"${(m.opex_per_unit or 0):,.0f}/unit/yr"))

    mgmt = next((r for r in m.opex_rows if r.bucket == "Management Fee"), None)
    if mgmt is not None and m.egi:
        pct = mgmt.annual / m.egi
        if pct < 0.025:
            f.append(MFFlag(f"Management fee {pct:.1%} of EGI", "warn",
                            "below the 2.5–3% institutional floor — re-underwrite"))

    taxes = next((r for r in m.opex_rows if r.bucket == "Real Estate Taxes"), None)
    if taxes is not None:
        f.append(MFFlag(f"RE taxes ${taxes.annual:,.0f} (${(taxes.per_unit or 0):,.0f}/unit)", "info",
                        "will reassess at sale — model post-acquisition millage on the ask"))

    if m.t3_vs_t12_pct is not None:
        if m.t3_vs_t12_pct > 0.03:
            f.append(MFFlag(f"T-3 revenue +{m.t3_vs_t12_pct:.1%} vs T-12", "ok",
                            "income accelerating — recent leasing gains are real"))
        elif m.t3_vs_t12_pct < -0.03:
            f.append(MFFlag(f"T-3 revenue {m.t3_vs_t12_pct:.1%} vs T-12", "warn",
                            "income rolling over — T-12 overstates run-rate"))
        else:
            f.append(MFFlag("T-3 ≈ T-12 revenue", "ok", "stable run-rate"))

    if m.delinquent_units and m.units:
        share = m.delinquent_units / m.units
        f.append(MFFlag(
            f"{m.delinquent_units} units carry balances (${(m.delinquent_total or 0):,.0f})",
            "warn" if share > 0.05 else "info",
            "5%+ of units delinquent" if share > 0.05 else "rent-roll balance column"))
    if m.ar_60_plus:
        f.append(MFFlag(f"AR 60+ days ${m.ar_60_plus:,.0f}", "warn",
                        "aged receivables — likely write-offs"))

    if m.noi is not None and m.noi_reported is not None and abs(m.noi - m.noi_reported) > 1.0:
        f.append(MFFlag("NOI does not tie to as-reported", "warn",
                        f"computed ${m.noi:,.0f} vs reported ${m.noi_reported:,.0f}"))
    elif m.noi is not None and m.noi_reported is not None:
        f.append(MFFlag(f"NOI ties to statement (${m.noi:,.0f})", "ok", "penny-exact"))


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

def _money(v: Optional[float], digits: int = 0) -> str:
    return "—" if v is None else f"${v:,.{digits}f}"


def _money_compact(v: Optional[float]) -> str:
    if v is None:
        return "—"
    av = abs(v)
    if av >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if av >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def _pct(v: Optional[float], digits: int = 1) -> str:
    return "—" if v is None else f"{v*100:.{digits}f}%"


def _render_headline(m: MFDashboardModel) -> None:
    tiles = [
        ("Units",            f"{m.units:,}" if m.units else "—"),
        ("Physical occ",     _pct(m.physical_occ)),
        ("Economic occ",     _pct(m.economic_occ)),
        ("In-place rent/mo", _money(m.avg_in_place_rent)),
        ("NOI (T-12)",       _money_compact(m.noi)),
        ("NOI margin",       _pct(m.noi_margin)),
        ("Going-in cap",     _pct(m.going_in_cap, digits=2)),
        ("Price / unit",     _money_compact(m.price_per_unit)),
    ]
    tile_html = "".join(
        f'<div class="t5-tile"><div class="t5-tile-label">{label}</div>'
        f'<div class="t5-tile-value">{value}</div></div>'
        for label, value in tiles
    )
    st.markdown(
        f"""
        <div class="t5-headline-grid" style="display:grid;
             grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));
             gap:0.6rem; margin:0.5rem 0 1rem;">
            <div class="t5-headline-eyebrow" style="grid-column:1/-1;
                 font-family:'JetBrains Mono',ui-monospace,Consolas,monospace;
                 font-size:0.66rem; letter-spacing:0.18em; font-weight:600;">HEADLINE</div>
            {tile_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ledger(m: MFDashboardModel) -> None:
    def money(v, paren=False):
        if v is None:
            return "—"
        return f"({abs(v):,.0f})" if paren else f"{v:,.0f}"

    def pct_gpr(v):
        if v is None or not m.gpr:
            return ""
        return f"{abs(v)/m.gpr*100:.1f}%"

    def pct_egi(v):
        if v is None or not m.egi:
            return ""
        return f"{abs(v)/m.egi*100:.1f}%"

    rows = [
        ("", "GPR", money(m.gpr), "100%" if m.gpr else "", "val"),
        ("", "Loss-to-lease", money(m.ltl, paren=(m.ltl or 0) < 0), pct_gpr(m.ltl), "neg"),
        ("", "Physical vacancy", money(m.vacancy, paren=True), pct_gpr(m.vacancy), "neg"),
        ("", "Concessions", money(m.concessions, paren=True), pct_gpr(m.concessions), "neg"),
        ("", "Bad debt", money(m.bad_debt, paren=True), pct_gpr(m.bad_debt), "neg"),
        ("", "Employee / down units", money(m.emp_down, paren=True), pct_gpr(m.emp_down), "neg"),
        ("total", "Net rental income", money(m.net_rental), pct_gpr(m.net_rental), "val"),
        ("", "Other income", money(m.other_income), pct_egi(m.other_income), "val"),
        ("total", "EGI", money(m.egi), "100%" if m.egi else "", "val"),
        ("", "Operating expenses", money(m.opex_total, paren=True), pct_egi(m.opex_total), "val"),
        ("total", "NOI", money(m.noi), pct_egi(m.noi), "pos"),
    ]
    body = "".join(
        f'<tr class="{cls}"><td class="lbl">{lbl}</td>'
        f'<td class="val {vcls}">{val}</td><td class="pct">{p}</td></tr>'
        for cls, lbl, val, p, vcls in rows
    )
    st.markdown(
        f"""
        <div class="ck-panel">
            <div class="ck-eyebrow">Income waterfall — T-12 basis</div>
            <table class="ck-ledger">{body}</table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_flags(m: MFDashboardModel) -> None:
    cards = []
    for fl in m.flags:
        cls = fl.status if fl.status in ("ok", "warn", "bad") else "info"
        cards.append(
            f'<div class="ck-flag {cls}"><div class="t">{fl.label}</div>'
            f'<div class="d">{fl.detail}</div></div>'
        )
    st.markdown("".join(cards), unsafe_allow_html=True)


def render_mf_dashboard(m: MFDashboardModel) -> None:
    """Render the MF dashboard into the current container (cockpit chrome)."""
    st.title(m.property_name or "MF deal")
    st.caption(f"Period: {m.period_label or '—'}  ·  Basis: T-12 actual / current rent roll")

    _render_headline(m)

    col_ledger, col_flags = st.columns([3, 2])
    with col_ledger:
        if m.gpr is not None or m.egi is not None:
            _render_ledger(m)
        else:
            st.info("Upload a T-12 to build the income waterfall.")
        if m.t3_annualized_income is not None:
            d1, d2, d3 = st.columns(3)
            d1.metric("T-12 revenue", _money_compact(m.egi))
            d2.metric("T-3 annualized", _money_compact(m.t3_annualized_income))
            d3.metric("Trajectory", _pct(m.t3_vs_t12_pct, digits=1))
    with col_flags:
        st.markdown('<div class="ck-eyebrow">Risk flags</div>', unsafe_allow_html=True)
        _render_flags(m)

    if m.unit_mix:
        st.divider()
        st.subheader("Unit mix & rents")
        st.dataframe(pd.DataFrame([{
            "Type": r.unit_type,
            "Units": r.count,
            "Avg SF": f"{r.avg_sqft:,.0f}" if r.avg_sqft else "—",
            "Market rent": _money(r.avg_market),
            "In-place rent": _money(r.avg_in_place),
            "In-place $/SF": f"${r.in_place_psf:,.2f}" if r.in_place_psf else "—",
            "LTL %": _pct(r.ltl_pct),
        } for r in m.unit_mix]), hide_index=True, use_container_width=True)

    if m.opex_rows:
        st.divider()
        st.subheader("Operating expenses")
        st.dataframe(pd.DataFrame([{
            "Expense": r.bucket,
            "T-12 $": _money(r.annual),
            "$/unit/yr": _money(r.per_unit),
            "% of EGI": _pct(r.pct_egi),
        } for r in m.opex_rows]), hide_index=True, use_container_width=True)

    if m.monthly_income and any(abs(v) > 0.005 for v in m.monthly_income):
        st.divider()
        st.subheader("Monthly revenue trend (T-12)")
        df = pd.DataFrame({
            "Month": m.month_labels[:len(m.monthly_income)],
            "Revenue": m.monthly_income,
        })
        try:
            import altair as alt
            chart = (
                alt.Chart(df).mark_bar()
                .encode(x=alt.X("Month:N", sort=None, title=None),
                        y=alt.Y("Revenue:Q", title="Revenue ($)"),
                        tooltip=["Month:N", alt.Tooltip("Revenue:Q", format="$,.0f")])
                .properties(height=240)
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.bar_chart(df.set_index("Month"))

    if m.purchase_price:
        st.divider()
        st.subheader("Valuation at the ask")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Purchase price", _money_compact(m.purchase_price))
        v2.metric("Going-in cap (T-12 NOI)", _pct(m.going_in_cap, digits=2))
        v3.metric("Price / SF", _money(m.price_per_sf, digits=0))
        v4.metric("GRM (price / GPR)", f"{m.grm:.2f}x" if m.grm else "—")
