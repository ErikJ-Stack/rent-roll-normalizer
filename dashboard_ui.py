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
    # Box the headline so it reads as the hero panel — st.container(border=True)
    # paints a subtle outlined card; metrics inside stay native st.metric tiles.
    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center; font-size:0.85rem; "
            "letter-spacing:0.12em; color:#7a8696; font-weight:600; "
            "margin-bottom:0.5rem;'>HEADLINE</div>",
            unsafe_allow_html=True,
        )
        # Row 1 — the four "must-see" tiles
        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Occupancy", _fmt_pct(m.occupancy_pct))
        r1c2.metric("EBITDARM margin", _fmt_pct(m.ebitdarm_margin))
        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Going-in cap rate", _fmt_pct(m.going_in_cap, digits=2))
        r2c2.metric("RevPOR", _fmt_money(m.revpor))
        st.divider()
        # Row 3-4 — supporting financial scale tiles
        r3c1, r3c2 = st.columns(2)
        r3c1.metric("EGI (annual)", _fmt_money_compact(m.egi))
        r3c2.metric("EBITDAR", _fmt_money_compact(m.ebitdar))
        r4c1, r4c2 = st.columns(2)
        r4c1.metric("EBITDARM", _fmt_money_compact(m.ebitdarm))
        r4c2.metric("Price / bed", _fmt_money(m.price_per_bed))


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


def _render_risk_flags(m: DashboardModel) -> None:
    st.subheader("Risk flags & underwriting checks")
    for flag in m.risk_flags:
        val_text = ""
        if flag.value is not None:
            # Use $ for $-shaped metrics, % for everything else (all current flags are %)
            val_text = f" — {_fmt_pct(flag.value, digits=2)} (threshold: {flag.threshold_text})"
        line = f"**{flag.label}**{val_text} — {flag.read_text}"
        if flag.status == "ok":
            st.success(line, icon="✅")
        elif flag.status == "warn":
            st.warning(line, icon="⚠️")
        elif flag.status == "bad":
            st.error(line, icon="❌")
        else:
            st.info(line, icon="⚪")


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
    st.title(f"📊 {m.property_name}")
    st.caption(f"Period: {m.period_label}  ·  Basis: T12 actual")
    st.divider()

    _render_headline(m)
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
    st.divider()
    _render_risk_flags(m)
    if m.ar_bad_debt_variance:
        st.divider()
        _render_ar(m)
