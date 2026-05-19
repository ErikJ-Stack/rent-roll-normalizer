"""
migrate_to_v028.py — Substrate template v0.2.7 → v0.2.8

Closes UW-BACKLOG **BL-0020** (Dashboard chart-data-link bug fixes).

The v0.2.7 Dashboard shipped with three stale/incorrect cross-sheet
references that were noticed in Excel after the v0.2.7 release:

  1. **C97:C108 "Monthly EGI Trend" series** pointed at `Monthly
     Trending!B21:M21` — which has been the **Housekeeping Income** row
     since substrate v0.1.7 (when EGI moved to row 26 as part of the
     ancillary-revenue Labels expansion / BL-0001). The chart was
     plotting Housekeeping Income labeled as EGI. Corrected to row 26.

  2. **F90:F93 "Payer Mix — Revenue Share" pie chart values** pointed
     at `Rent Roll Recon!B40:B43` — which holds COUNTIFS for unit
     counts per payer type. The pie chart's title says **Revenue
     Share**, so the right source is `Rent Roll Recon!I40:I43` (the
     revenue-ratio formulas computing `H40/H47` etc.). Corrected to
     column I.

  3. **Chart [1] (doughnut) series range + data layout.** In v0.2.7
     the doughnut covered `Dashboard!$O$8:$O$19` with only `O8` and
     `O15:O19` populated — the chart was rendering 6 empty slices
     before the actual data, which looked broken. v0.2.8 moves the
     5 data rows from `O15:O19` up to `O9:O13` (now contiguous with
     the existing `O8` row) and shortens the chart series range to
     `Dashboard!$O$8:$O$14`, so the doughnut now points at populated
     cells.

All three corrections were applied by the user in their local Excel
copy of the v0.2.7 Analyzer. v0.2.8 ports those corrections into the
bundled Analyzer via the same template-asset pattern v0.2.7 used.

OPERATIONS:

  A. Remove the existing v0.2.7 `Dashboard` sheet.
  B. Insert a refreshed `Dashboard` sheet from
     `v028_assets/dashboard_template.xlsx`, copying cells + styles +
     column widths + row heights + merged cells + 6 charts + tab color.
  C. Re-stamp AZ1:AZ5 anchor metadata on the new sheet.
  D. Stamp Cover!B8 → v0.2.8 + AZ4 on all 15 sheets.

Anchor list unchanged from v0.2.7 (15 sheets, "Dashboard" at index 1).

Idempotency: gate checks BOTH `Cover!B8 == "v0.2.8"` AND the corrected
formula at `Dashboard!C97` references row 26 (the canonical "have the
fixes shipped" check). Re-running on already-migrated workbook is a
no-op (just re-saves).

Why a fresh substrate version rather than a hotfix to v0.2.7:
  - Substrate versions are immutable once shipped (Cover!B8 + AZ4
    anchors are content-addressable for downstream tooling). Mutating
    v0.2.7's bundled file in place would break the
    "v0.2.7 == specific known content" invariant.
  - The migration chain stays linear: v0.2.6 → v0.2.7 → v0.2.8. Users
    on v0.2.7 (e.g. anyone who downloaded after PR #33 merged) run
    this migration to pick up the fixes; users still on v0.2.6 should
    run v0.2.7 first, then v0.2.8.

Usage:
    python tools/migration/migrate_to_v028.py input.xlsx output.xlsx
"""
from __future__ import annotations

import sys
from copy import copy, deepcopy
from pathlib import Path

import openpyxl

SUBSTRATE_FROM = "v0.2.7"
SUBSTRATE_TO = "v0.2.8"

DASHBOARD_SHEET = "Dashboard"
DASHBOARD_INDEX = 1  # immediately after Cover

# Anchor list unchanged from v0.2.7.
ANCHOR_SHEETS = (
    "Cover", "Dashboard",
    "T12 Analytics", "T12 Input", "T12 Raw Data",
    "Rent Roll Input", "Rent Roll Recon", "Monthly Trending", "UW Output",
    "UW Export",
    "Mapping Review", "Description_Map", "RR_Calc", "T12_Calc",
    "Workbook Health",
)

ANCHOR_PURPOSE = "Underwriting at-a-glance KPI dashboard with embedded charts"
ANCHOR_CATEGORY = "Analytical (handoff)"
ANCHOR_VISIBILITY = "visible"
ANCHOR_NOTES = (
    "All value cells are formula references into T12 Analytics, Rent Roll Recon, "
    "Monthly Trending, and Cover. 6 native Excel charts embedded. No source-of-"
    "truth data lives here. v0.2.8 fixes three Dashboard bugs from v0.2.7: "
    "EGI series (Monthly Trending row 21 -> 26), Revenue Share pie "
    "(Rent Roll Recon col B -> I), doughnut layout (data O15:O19 -> O9:O13, "
    "series range O8:O19 -> O8:O14)."
)

TEMPLATE_PATH = (
    Path(__file__).parent / "v028_assets" / "dashboard_template.xlsx"
)


def is_already_v028(wb) -> bool:
    """Gate: version stamp AND the corrected C97 formula already present."""
    if wb["Cover"]["B8"].value != SUBSTRATE_TO:
        return False
    if DASHBOARD_SHEET not in wb.sheetnames:
        return False
    c97 = wb[DASHBOARD_SHEET]["C97"].value
    if not isinstance(c97, str):
        return False
    # Corrected formula references row 26, not row 21.
    return "Monthly Trending'!B26" in c97


def _copy_cell(src_cell, dst_cell) -> None:
    dst_cell.value = src_cell.value
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.border = copy(src_cell.border)
        dst_cell.alignment = copy(src_cell.alignment)
        dst_cell.number_format = src_cell.number_format
        dst_cell.protection = copy(src_cell.protection)


def remove_existing_dashboard(wb) -> bool:
    if DASHBOARD_SHEET in wb.sheetnames:
        del wb[DASHBOARD_SHEET]
        return True
    return False


def insert_dashboard(wb) -> dict:
    """Insert the corrected Dashboard from the v028 template at index 1."""
    n = {"cells": 0, "col_widths": 0, "row_heights": 0, "merges": 0, "charts": 0}

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Template asset missing: {TEMPLATE_PATH}. "
            "This migration cannot proceed without the bundled dashboard template."
        )

    tmpl_wb = openpyxl.load_workbook(TEMPLATE_PATH)
    src_ws = tmpl_wb[DASHBOARD_SHEET]

    dst_ws = wb.create_sheet(DASHBOARD_SHEET)

    for row in src_ws.iter_rows():
        for cell in row:
            new_cell = dst_ws.cell(row=cell.row, column=cell.column)
            _copy_cell(cell, new_cell)
            if cell.value is not None:
                n["cells"] += 1

    for letter, dim in src_ws.column_dimensions.items():
        if dim.width:
            dst_ws.column_dimensions[letter].width = dim.width
            n["col_widths"] += 1
        if dim.hidden:
            dst_ws.column_dimensions[letter].hidden = dim.hidden

    for r, dim in src_ws.row_dimensions.items():
        if dim.height:
            dst_ws.row_dimensions[r].height = dim.height
            n["row_heights"] += 1

    for mr in src_ws.merged_cells.ranges:
        dst_ws.merge_cells(str(mr))
        n["merges"] += 1

    if src_ws.sheet_view.showGridLines is False:
        dst_ws.sheet_view.showGridLines = False

    if src_ws.sheet_properties.tabColor is not None:
        dst_ws.sheet_properties.tabColor = copy(src_ws.sheet_properties.tabColor)

    for chart in src_ws._charts:
        new_chart = deepcopy(chart)
        dst_ws._charts.append(new_chart)
        n["charts"] += 1

    current_index = wb.sheetnames.index(DASHBOARD_SHEET)
    offset = DASHBOARD_INDEX - current_index
    if offset != 0:
        wb.move_sheet(DASHBOARD_SHEET, offset=offset)

    return n


def stamp_anchor_cells(wb) -> None:
    ws = wb[DASHBOARD_SHEET]
    ws["AZ1"] = ANCHOR_PURPOSE
    ws["AZ2"] = ANCHOR_CATEGORY
    ws["AZ3"] = ANCHOR_VISIBILITY
    ws["AZ4"] = SUBSTRATE_TO
    ws["AZ5"] = ANCHOR_NOTES


def stamp_versions(wb) -> None:
    if "Cover" in wb.sheetnames:
        wb["Cover"]["B8"] = SUBSTRATE_TO
    for s in ANCHOR_SHEETS:
        if s in wb.sheetnames:
            wb[s]["AZ4"] = SUBSTRATE_TO


def verify_migration(wb) -> dict:
    r = {}

    r["cover_b8"] = wb["Cover"]["B8"].value
    r["cover_b8_ok"] = r["cover_b8"] == SUBSTRATE_TO

    r["dashboard_exists"] = DASHBOARD_SHEET in wb.sheetnames
    r["dashboard_position_ok"] = (
        r["dashboard_exists"]
        and wb.sheetnames.index(DASHBOARD_SHEET) == DASHBOARD_INDEX
    )
    r["sheet_count"] = len(wb.sheetnames)
    r["sheet_count_ok"] = r["sheet_count"] == 15

    az4 = {s: wb[s]["AZ4"].value for s in ANCHOR_SHEETS if s in wb.sheetnames}
    r["az4_all"] = all(v == SUBSTRATE_TO for v in az4.values())
    r["az4_count"] = len(az4)

    if r["dashboard_exists"]:
        ws = wb[DASHBOARD_SHEET]
        r["chart_count"] = len(ws._charts)
        r["chart_count_ok"] = r["chart_count"] == 6

        # The three bug-fix checks — confirm each correction is in the migrated file.
        c97 = str(ws["C97"].value or "")
        f90 = str(ws["F90"].value or "")

        # Doughnut chart [1] series range AND data layout.
        # v0.2.7 had range $O$8:$O$19 with data only at O8 + O15:O19 (gaps).
        # v0.2.8 has range $O$8:$O$14 with data at O8 + O9:O13 (contiguous).
        doughnut_range_ok = False
        if len(ws._charts) >= 2:
            ch1 = ws._charts[1]
            for s in (ch1.series or []):
                try:
                    cat_f = s.cat.strRef.f if s.cat and s.cat.strRef else ""
                    val_f = s.val.numRef.f if s.val and s.val.numRef else ""
                    if "$O$8:$O$14" in cat_f and "$P$8:$P$14" in val_f:
                        doughnut_range_ok = True
                except Exception:
                    pass
        # Data layout check: O9-O13 populated, O15-O19 not populated.
        layout_top_populated = all(ws[f"O{i}"].value is not None for i in range(9, 14))
        layout_bottom_empty = all(ws[f"O{i}"].value is None for i in range(15, 20))

        r["c97_fixed"] = "Monthly Trending'!B26" in c97
        r["f90_fixed"] = "Rent Roll Recon'!I40" in f90
        r["doughnut_range_fixed"] = doughnut_range_ok
        r["doughnut_layout_fixed"] = layout_top_populated and layout_bottom_empty

        # AZ anchor block
        r["az1_purpose_ok"] = ws["AZ1"].value == ANCHOR_PURPOSE
        r["az3_visibility_ok"] = ws["AZ3"].value == ANCHOR_VISIBILITY
        r["az4_self_stamp_ok"] = ws["AZ4"].value == SUBSTRATE_TO
    else:
        r["chart_count"] = 0
        r["chart_count_ok"] = False
        r["c97_fixed"] = False
        r["f90_fixed"] = False
        r["doughnut_range_fixed"] = False
        r["doughnut_layout_fixed"] = False
        r["az1_purpose_ok"] = False
        r["az3_visibility_ok"] = False
        r["az4_self_stamp_ok"] = False

    return r


def main(input_path: str, output_path: str) -> int:
    src = Path(input_path)
    dst = Path(output_path)
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    print(f"Loading {src}...")
    wb = openpyxl.load_workbook(src)

    if is_already_v028(wb):
        print(f"Workbook is already at {SUBSTRATE_TO}. No-op (will re-save).")
        wb.save(dst)
        return 0

    print(f"Migrating {SUBSTRATE_FROM} -> {SUBSTRATE_TO}...")

    removed = remove_existing_dashboard(wb)
    print(f"  A: removed existing Dashboard sheet: {removed}")

    n = insert_dashboard(wb)
    print(f"  B: inserted corrected Dashboard at index {DASHBOARD_INDEX} — "
          f"{n['cells']} cells, {n['col_widths']} col widths, "
          f"{n['row_heights']} row heights, {n['merges']} merges, "
          f"{n['charts']} charts")

    stamp_anchor_cells(wb)
    print(f"  C: stamped AZ1:AZ5 on Dashboard")

    stamp_versions(wb)
    print(f"  D: stamped substrate version -> {SUBSTRATE_TO} on "
          f"Cover!B8 + {len(ANCHOR_SHEETS)} AZ4 anchors")

    print(f"Saving to {dst}...")
    wb.save(dst)

    print(f"Verifying {dst}...")
    wb2 = openpyxl.load_workbook(dst)
    r = verify_migration(wb2)

    print()
    print("=== Verification ===")
    print(f"  Cover!B8 = {r['cover_b8']!r:24s}     : {r['cover_b8_ok']}")
    print(f"  Dashboard sheet exists                  : {r['dashboard_exists']}")
    print(f"  Dashboard at position 1 (after Cover)   : {r['dashboard_position_ok']}")
    print(f"  Sheet count = {r['sheet_count']} (expected 15)         : {r['sheet_count_ok']}")
    print(f"  Chart count = {r['chart_count']} (expected 6)           : {r['chart_count_ok']}")
    print()
    print(f"  Fix 1 — C97 refs Monthly Trending B26   : {r['c97_fixed']}")
    print(f"  Fix 2 — F90 refs Rent Roll Recon I40    : {r['f90_fixed']}")
    print(f"  Fix 3a — doughnut series range O8:O14   : {r['doughnut_range_fixed']}")
    print(f"  Fix 3b — doughnut data layout (O9:O13)  : {r['doughnut_layout_fixed']}")
    print()
    print(f"  AZ1 purpose stamped                     : {r['az1_purpose_ok']}")
    print(f"  AZ3 visibility stamped                  : {r['az3_visibility_ok']}")
    print(f"  AZ4 self-stamp = {SUBSTRATE_TO}                : {r['az4_self_stamp_ok']}")
    print(f"  All 15 AZ4 = {SUBSTRATE_TO}                    : {r['az4_all']} ({r['az4_count']} sheets)")

    all_ok = (
        r["cover_b8_ok"]
        and r["dashboard_exists"] and r["dashboard_position_ok"]
        and r["sheet_count_ok"]
        and r["chart_count_ok"]
        and r["c97_fixed"] and r["f90_fixed"]
        and r["doughnut_range_fixed"] and r["doughnut_layout_fixed"]
        and r["az1_purpose_ok"] and r["az3_visibility_ok"]
        and r["az4_self_stamp_ok"] and r["az4_all"]
    )
    print()
    print("=== " + ("[OK] Migration complete" if all_ok else "[FAIL] Migration incomplete") + " ===")
    return 0 if all_ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python migrate_to_v028.py input.xlsx output.xlsx")
        sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
