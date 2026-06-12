"""
dashboard_ui.py — Track 5 Streamlit renderer.

Single function `render_dashboard(model)` draws the Dashboard data into the
current Streamlit container. Mobile-first single-scroll layout: st.metric
tiles in 2-col grids (Streamlit narrows them gracefully on small viewports),
tables via st.dataframe(use_container_width=True), charts via st.altair_chart
(Altair auto-reflows).

No business logic here. The model is the contract.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from dashboard_model import DashboardModel


# ---------------------------------------------------------------------------
# Formatters — safe wrappers that return "—" for None
# ---------------------------------------------------------------------------

def _fmt_pct(v: Optional[float], digits: int = 1) -> str:
    if v is None:
        return "—"
    return f"{v * 100:.{digits}f}%"


def _fmt_money(v: Optional[float], digits: int = 0) -> str:
    if v is None:
        return "—"
    return f"${v:,.{digits}f}"


def _fmt_money_compact(v: Optional[float]) -> str:
    if v is None:
        return "—"
    av = abs(v)
    if av >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if av >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def _fmt_int(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{int(v):,}"


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------

def _render_headline(m: DashboardModel) -> None:
    # CSS-grid hero panel (Track 5 v0.1.5) — replaces st.metric tiles in
    # st.columns(2) with a native HTML grid that uses
    # `grid-template-columns: repeat(auto-fit, minmax(140px, 1fr))` so the
    # browser packs as many tiles as the viewport allows: 8 across on a
    # wide desktop, reflowing to 4 → 2 → 1 as the viewport narrows. Native
    # st.columns doesn't reflow; CSS grid is the only way to get true
    # responsive behavior in Streamlit without a custom component.
    tiles = [
        ("Occupancy",         _fmt_pct(m.occupancy_pct)),
        ("EBITDARM margin",   _fmt_pct(m.ebitdarm_margin)),
        ("Going-in cap rate", _fmt_pct(m.going_in_cap, digits=2)),
        ("RevPOR",            _fmt_money(m.revpor)),
        ("EGI (annual)",      _fmt_money_compact(m.egi)),
        ("EBITDAR",           _fmt_money_compact(m.ebitdar)),
        ("EBITDARM",          _fmt_money_compact(m.ebitdarm)),
        ("Price / bed",       _fmt_money(m.price_per_bed)),
    ]
    tile_html = "".join(
        f'<div class="t5-tile">'
        f'<div class="t5-tile-label">{label}</div>'
        f'<div class="t5-tile-value">{value}</div>'
        f'</div>'
        for label, value in tiles
    )
    st.markdown(
        f"""
        <style>
        .t5-headline-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.6rem;
            margin: 0.5rem 0 1rem;
        }}
        .t5-headline-eyebrow {{
            grid-column: 1 / -1;
            font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace;
            font-size: 0.66rem;
            letter-spacing: 0.18em;
            color: #5E6B7A;
            font-weight: 600;
        }}
        .t5-tile {{
            background: #1A2027;
            border: 1px solid #232A33;
            border-radius: 8px;
            padding: 0.6rem 0.8rem;
            min-width: 0;
        }}
        .t5-tile-label {{
            font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace;
            font-size: 0.66rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #5E6B7A;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 0.2rem;
        }}
        .t5-tile-value {{
            font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace;
            font-size: 1.45rem;
            font-weight: 600;
            color: #E6EDF5;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        @media (max-width: 480px) {{
            .t5-tile-value {{ font-size: 1.2rem; }}
            .t5-headline-grid {{ gap: 0.5rem; }}
        }}
        </style>
        <div class="t5-headline-grid">
            <div class="t5-headline-eyebrow">HEADLINE</div>
            {tile_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ledger(m: DashboardModel) -> None:
    """Cockpit live ledger — the GPR → EBITDAR waterfall in monospace with a
    % of EGI column. All inputs derive from fields the model already carries;
    rows whose inputs are missing render as "—"."""
    egi = m.egi
    gpr = m.gpr
    vac = (gpr - egi) if (gpr is not None and egi is not None) else None
    labor = (m.total_labor_pct * egi) if (m.total_labor_pct is not None and egi) else None
    opex_excl_mgmt = (egi - m.ebitdarm) if (egi is not None and m.ebitdarm is not None) else None
    nonlabor = (opex_excl_mgmt - labor) if (opex_excl_mgmt is not None and labor is not None) else None
    mgmt = (m.ebitdarm - m.ebitdar) if (m.ebitdarm is not None and m.ebitdar is not None) else None

    def money(v: Optional[float], paren: bool = False) -> str:
        if v is None:
            return "—"
        return f"({v:,.0f})" if paren else f"{v:,.0f}"

    def pct(v: Optional[float]) -> str:
        if v is None or not egi:
            return ""
        return f"{v / egi * 100:.1f}%"

    rows = [
        ("", "GPR", money(gpr), "", "val"),
        ("", "Vacancy / LTL / contras", money(vac, paren=True), pct(vac), "neg"),
        ("total", "EGI", money(egi), "100%" if egi else "", "val"),
        ("", "Labor", money(labor, paren=True), pct(labor), "val"),
        ("", "Non-labor opex", money(nonlabor, paren=True), pct(nonlabor), "val"),
        ("total", "EBITDARM", money(m.ebitdarm), pct(m.ebitdarm), "pos"),
        ("", "Mgmt fee", money(mgmt, paren=True), pct(mgmt), "val"),
        ("total", "EBITDAR", money(m.ebitdar), pct(m.ebitdar), "pos"),
    ]
    body = "".join(
        f'<tr class="{cls}"><td class="lbl">{lbl}</td>'
        f'<td class="val {vcls}">{val}</td><td class="pct">{p}</td></tr>'
        for cls, lbl, val, p, vcls in rows
    )
    st.markdown(
        f"""
        <div class="ck-panel">
            <div class="ck-eyebrow">Live ledger — T12 basis</div>
            <table class="ck-ledger">{body}</table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_capacity(m: DashboardModel) -> None:
    st.subheader("Capacity & occupancy")
    rows = []
    for row in m.care_types:
        rows.append({
            "Care type": row.care_type,
            "Licensed": row.licensed,
            "Occupied": row.occupied,
            "Occupancy": _fmt_pct(row.occupancy_pct),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_revenue(m: DashboardModel) -> None:
    st.subheader("Revenue & rate")
    rows = [
        ("Gross potential rent",     _fmt_money_compact(m.gpr)),
        ("Effective gross income",   _fmt_money_compact(m.egi)),
        ("Blended ADR / bed / mo",   _fmt_money(m.blended_adr)),
        ("RevPOR (base + LOC)",      _fmt_money(m.revpor)),
        ("RevPAB (EGI / avail bed)", _fmt_money(m.revpab)),
        ("LOC as % of base rent",    _fmt_pct(m.loc_pct)),
        ("Vacancy loss %",           _fmt_pct(m.vacancy_pct)),
        ("Loss to lease %",          _fmt_pct(m.loss_to_lease_pct)),
        ("Bad debt %",               _fmt_pct(m.bad_debt_pct, digits=2)),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Metric", "Value"]),
                 hide_index=True, use_container_width=True)


def _render_profitability(m: DashboardModel) -> None:
    st.subheader("Profitability")
    c1, c2 = st.columns(2)
    c1.metric("EBITDARM", _fmt_money_compact(m.ebitdarm))
    c2.metric("EBITDARM margin", _fmt_pct(m.ebitdarm_margin))
    c1.metric("EBITDAR (post-mgmt fee)", _fmt_money_compact(m.ebitdar))
    c2.metric("EBITDAR margin", _fmt_pct(m.ebitdar_margin))
    c1.metric("EGI / occupied bed / mo", _fmt_money(m.egi_per_occupied_bed))
    c2.metric("Opex / occupied bed / mo", _fmt_money(m.opex_per_occupied_bed))
    c1.metric("Total opex (annual)", _fmt_money_compact(m.total_opex))


def _render_cost_structure(m: DashboardModel) -> None:
    st.subheader("Cost structure & labor")
    rows = [
        ("Total labor + burden % EGI", _fmt_pct(m.total_labor_pct)),
        ("Direct labor % EGI",         _fmt_pct(m.direct_labor_pct)),
        ("Overtime % direct labor",    _fmt_pct(m.overtime_pct)),
        ("Agency % direct labor",      _fmt_pct(m.agency_pct)),
        ("Food cost / patient day",    _fmt_money(m.food_ppd)),
        ("Management fee % EGI",       _fmt_pct(m.mgmt_fee_pct)),
        ("P&C insurance % EGI",        _fmt_pct(m.insurance_pct, digits=2)),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Metric", "Value"]),
                 hide_index=True, use_container_width=True)


def _render_valuation(m: DashboardModel) -> None:
    st.subheader("Valuation")
    if m.purchase_price is None:
        st.info("Purchase price not yet entered — open the downloaded Analyzer, set `T12 Analytics!E117`, "
                "and reload to populate cap rates and per-bed pricing.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Purchase price", _fmt_money_compact(m.purchase_price))
    c2.metric("Price / licensed bed", _fmt_money(m.price_per_bed))
    c1.metric("Going-in cap (EBITDARM)", _fmt_pct(m.going_in_cap, digits=2))
    c2.metric("Going-in cap (EBITDAR)", _fmt_pct(m.ebitdar_cap, digits=2))


def _render_payer_mix(m: DashboardModel) -> None:
    st.subheader("Payer mix")
    if not any(r.resident_count for r in m.payer_mix):
        st.caption("No payer data — Rent Roll has no Payer Type column or all are blank.")
        return
    rows = []
    for row in m.payer_mix:
        rows.append({
            "Payer":      row.payer,
            "Residents":  row.resident_count,
            "% Census":   _fmt_pct(row.census_pct),
            "Revenue":    _fmt_money_compact(row.revenue) if row.revenue else "—",
            "% Revenue":  _fmt_pct(row.revenue_pct),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    chart_df = pd.DataFrame([
        {"Payer": r.payer, "Revenue Share": r.revenue_pct or 0.0}
        for r in m.payer_mix if (r.revenue_pct or 0) > 0
    ])
    if not chart_df.empty:
        try:
            import altair as alt
            chart = (
                alt.Chart(chart_df)
                .mark_arc(innerRadius=60)
                .encode(
                    theta=alt.Theta("Revenue Share:Q"),
                    color=alt.Color("Payer:N", legend=alt.Legend(orient="bottom")),
                    tooltip=["Payer:N", alt.Tooltip("Revenue Share:Q", format=".1%")],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.bar_chart(chart_df.set_index("Payer"))


def _render_care_type_table(m: DashboardModel) -> None:
    st.subheader("Care type breakdown")
    rows = []
    for row in m.care_types:
        rows.append({
            "Care type": row.care_type,
            "Licensed":  row.licensed,
            "Occupied":  row.occupied,
            "Occ %":     _fmt_pct(row.occupancy_pct),
            "ADR":       _fmt_money(row.adr),
            "RevPOR":    _fmt_money(row.revpor),
            "LOC %":     _fmt_pct(row.loc_pct),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_monthly_trend(m: DashboardModel) -> None:
    if not m.monthly_egi:
        return
    st.subheader("Monthly EGI trend (T12)")
    df = pd.DataFrame([
        {"Month": s.month_label, "EGI": s.egi} for s in m.monthly_egi
    ])
    try:
        import altair as alt
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Month:N", sort=None, title=None),
                y=alt.Y("EGI:Q", title="EGI ($)"),
                tooltip=["Month:N", alt.Tooltip("EGI:Q", format="$,.0f")],
            )
            .properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        st.bar_chart(df.set_index("Month"))


def _render_care_level_dist(m: DashboardModel) -> None:
    if not m.al_care_level_dist:
        return
    st.subheader("AL care level distribution")
    df = pd.DataFrame(m.al_care_level_dist, columns=["Care Level", "Residents"])
    try:
        import altair as alt
        chart = (
            alt.Chart(df)
            .mark_arc(innerRadius=50)
            .encode(
                theta="Residents:Q",
                color=alt.Color("Care Level:N", legend=alt.Legend(orient="bottom")),
                tooltip=["Care Level:N", "Residents:Q"],
            )
            .properties(height=260)
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        st.bar_chart(df.set_index("Care Level"))


def _render_risk_flags(m: DashboardModel, heading: bool = True) -> None:
    # Cockpit flag cards — color-coded left border, monospace, compact.
    if heading:
        st.subheader("Risk flags & underwriting checks")
    cards = []
    for flag in m.risk_flags:
        val_text = ""
        if flag.value is not None:
            # Use $ for $-shaped metrics, % for everything else (all current flags are %)
            val_text = f" — {_fmt_pct(flag.value, digits=2)} (vs {flag.threshold_text})"
        cls = flag.status if flag.status in ("ok", "warn", "bad") else "info"
        cards.append(
            f'<div class="ck-flag {cls}">'
            f'<div class="t">{flag.label}{val_text}</div>'
            f'<div class="d">{flag.read_text}</div>'
            f'</div>'
        )
    st.markdown("".join(cards), unsafe_allow_html=True)


def _render_ar(m: DashboardModel) -> None:
    if not m.ar_bad_debt_variance:
        return
    st.subheader("AR & bad debt variance")
    st.info(m.ar_bad_debt_variance)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_dashboard(m: DashboardModel) -> None:
    """Render the full Dashboard tab content into the current Streamlit container.

    Mobile-friendly single-scroll layout. Caller decides the container (tab,
    expander, dialog, etc.) — this function only writes Streamlit elements.
    """
    st.title(m.property_name)
    st.caption(f"Period: {m.period_label}  ·  Basis: T12 actual")

    _render_headline(m)

    # Cockpit center stage — live ledger beside the risk-flag column.
    col_ledger, col_flags = st.columns([3, 2])
    with col_ledger:
        _render_ledger(m)
    with col_flags:
        st.markdown('<div class="ck-eyebrow">Risk flags</div>', unsafe_allow_html=True)
        _render_risk_flags(m, heading=False)

    st.divider()
    _render_capacity(m)
    st.divider()
    _render_revenue(m)
    st.divider()
    _render_profitability(m)
    st.divider()
    _render_cost_structure(m)
    st.divider()
    _render_valuation(m)
    st.divider()
    _render_payer_mix(m)
    st.divider()
    _render_care_type_table(m)
    st.divider()
    _render_monthly_trend(m)
    st.divider()
    _render_care_level_dist(m)
    if m.ar_bad_debt_variance:
        st.divider()
        _render_ar(m)
