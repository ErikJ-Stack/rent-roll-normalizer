"""
Report builders: RR_Summary, RR_By_Type, RR_Exceptions.

These sit on top of the Normalized_Beds dataframe produced by normalizer.py.
"""

from __future__ import annotations

from typing import List

import pandas as pd


def build_summary(n: pd.DataFrame) -> pd.DataFrame:
    """KPI table for RR_Summary."""
    if n.empty:
        return pd.DataFrame(columns=["KPI", "Value"])

    total_beds = len(n)
    occupied_beds = int((n["Status"] == "Occupied").sum())
    vacant_beds = int((n["Status"] == "Vacant").sum())
    other_beds = total_beds - occupied_beds - vacant_beds
    total_units = n["Room #"].nunique()

    occ = (n["Status"] == "Occupied")
    occ_df = n[occ]

    # NaN-aware averages.
    # "(all beds)" series treat blanks as $0 — semantically "this bed has no
    # rate, count it at zero in the all-beds average." Use fillna(0).mean().
    # "(occupied)" averages skip blanks naturally with .mean() — that's right
    # because an occupied bed with a blank rate is a data gap, not a $0 rate.
    avg_market_all  = n["Market Rate"].fillna(0).mean() if total_beds else 0
    avg_actual_all  = n["Actual Rate"].fillna(0).mean() if total_beds else 0
    avg_actual_occ  = occ_df["Actual Rate"].mean()      if len(occ_df) else 0

    rows = [
        # Inventory
        ("Total Units",                       total_units),
        ("Total Beds",                        total_beds),
        ("Occupied Beds",                     occupied_beds),
        ("Vacant Beds",                       vacant_beds),
        ("Other Status Beds",                 other_beds),
        # Occupancy
        ("Bed Occupancy %",                   _pct(occupied_beds, total_beds)),
        # Pricing
        ("Avg Market Rate (all beds)",        round(avg_market_all, 2)),
        ("Avg Actual Rate (all beds)",        round(avg_actual_all, 2)),
        ("Avg Actual Rate (occupied)",        round(avg_actual_occ, 2)),
        ("Avg Rate Gap (Market - Actual)",    round(avg_market_all - avg_actual_all, 2)),
        # Revenue (monthly, in-place)
        ("Total Market Rate $ (all beds)",    round(n["Market Rate"].sum(), 2)),
        ("Total Actual Rate $ (occupied)",    round(occ_df["Actual Rate"].sum(), 2)),
        ("Total Concessions $",               round(n["Concession $"].sum(), 2)),
        ("Total Care Level $",             round(n["Care Level $"].sum(), 2)),
        ("Total Med Mgmt $",                  round(n["Med Mgmt $"].sum(), 2)),
        ("Total Pharmacy $",                  round(n["Pharmacy $"].sum(), 2)),
        ("Total Other LOC $",                 round(n["Other LOC $"].sum(), 2)),
        ("Total LOC $ (all care buckets)",    round(n["Total LOC $"].sum(), 2)),
        ("Total In-Place Monthly Revenue $",  round(n["Total Monthly Revenue"].sum(), 2)),
    ]
    return pd.DataFrame(rows, columns=["KPI", "Value"])


def _pct(num, den) -> str:
    if not den:
        return "0.0%"
    return f"{100 * num / den:.1f}%"


def build_by_type(n: pd.DataFrame) -> pd.DataFrame:
    """Aggregated counts and revenue by Apt Type / Care Type / Payer / Status.

    Returns a long-format dataframe with a Category column naming the dimension.
    """
    if n.empty:
        return pd.DataFrame(columns=["Category", "Value", "Beds", "Occupied", "Avg Actual Rate", "Total Actual $", "Total LOC $"])

    dfs: List[pd.DataFrame] = []
    for dim, label in [
        ("Apt Type", "Apt Type"),
        ("Care Type", "Care Type (IL/AL/MC)"),
        ("Care Level", "Care Level"),
        ("Payer Type", "Payer Type"),
        ("Status", "Bed Status"),
    ]:
        g = n.groupby(dim, dropna=False).agg(
            Beds=("Status", "size"),
            Occupied=("Status", lambda s: (s == "Occupied").sum()),
            Avg_Actual_Rate=("Actual Rate", "mean"),
            Total_Actual=("Actual Rate", "sum"),
            Total_LOC=("Total LOC $", "sum"),
        ).reset_index()
        g.insert(0, "Category", label)
        g = g.rename(columns={
            dim: "Value",
            "Avg_Actual_Rate": "Avg Actual Rate",
            "Total_Actual":    "Total Actual $",
            "Total_LOC":       "Total LOC $",
        })
        g["Avg Actual Rate"] = g["Avg Actual Rate"].round(2)
        g["Total Actual $"]  = g["Total Actual $"].round(2)
        g["Total LOC $"]     = g["Total LOC $"].round(2)
        dfs.append(g)

    return pd.concat(dfs, ignore_index=True)


def build_exceptions(n: pd.DataFrame, unmapped: dict) -> pd.DataFrame:
    """Rows needing manual review, per the handoff rules."""
    if n.empty:
        return pd.DataFrame(columns=["Row", "Unit #", "Room #", "Bed", "Resident Name", "Issue"])

    issues: List[dict] = []

    def _flag(idx, row, issue):
        issues.append({
            "Row":            idx + 2,  # 1-indexed + header
            "Unit #":         row.get("Unit #", ""),
            "Room #":         row.get("Room #", ""),
            "Bed":            row.get("Bed", ""),
            "Resident Name":  row.get("Resident Name", ""),
            "Issue":          issue,
        })

    def _num(v):
        """Coerce NaN/None/non-numeric to 0 for threshold checks.
        Plain `or 0` doesn't work because `NaN or 0` returns NaN, and
        `NaN <= 0` is False — would silently mask real data gaps."""
        if v is None:
            return 0
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0
        if f != f:  # NaN check
            return 0
        return f

    for idx, row in n.iterrows():
        status = row.get("Status", "")
        name = str(row.get("Resident Name", "")).strip()
        actual = _num(row.get("Actual Rate"))
        market = _num(row.get("Market Rate"))
        move_in = str(row.get("Move-in Date", "")).strip()
        care_level = str(row.get("Care Level", "")).strip()
        care_type = str(row.get("Care Type", "")).strip()
        al_care_dollar = _num(row.get("Care Level $"))

        if status == "Vacant" and name:
            _flag(idx, row, "Vacant bed has resident name")
        if status == "Occupied" and not name:
            _flag(idx, row, "Occupied bed missing resident name")
        if status == "Occupied" and actual <= 0:
            _flag(idx, row, "Occupied bed with zero/blank actual rate")
        if status == "Occupied" and not move_in:
            _flag(idx, row, "Occupied bed missing move-in date")
        if status == "Occupied" and not care_type:
            _flag(idx, row, "Occupied bed missing Care Type (IL/AL/MC) — add Care Type column to source or map building/wing code")
        if care_level and al_care_dollar <= 0:
            _flag(idx, row, f"Care Level '{care_level}' populated but no care charge")
        if market > 0 and actual > 0 and (market - actual) / market > 0.25:
            _flag(idx, row, f"Large market-to-actual gap ({(market-actual)/market:.0%})")

    # Unmapped values as their own block at the bottom.
    # Skip 'missing_care_type' — that's flagged per-row above.
    skip_keys = {"missing_care_type"}
    for cat, vals in (unmapped or {}).items():
        if cat in skip_keys:
            continue
        for v in vals:
            issues.append({
                "Row": "", "Unit #": "", "Room #": "", "Bed": "",
                "Resident Name": "",
                "Issue": f"Unmapped {cat.replace('_', ' ')}: '{v}' — add to mapping workbook",
            })

    return pd.DataFrame(issues) if issues else pd.DataFrame(
        columns=["Row", "Unit #", "Room #", "Bed", "Resident Name", "Issue"]
    )
