"""
migrate_to_v024.py — Substrate template v0.2.3 → v0.2.4

Adds a new top-of-workbook "Investment Dashboard" sheet that surfaces the
KPIs already computed elsewhere in the Analyzer (T12 Analytics, Rent Roll
Recon) in a single at-a-glance underwriting view.

Why this is additive, not destructive:
  - Every dashboard cell is either a label or a formula REFERENCE into an
    existing sheet (T12 Analytics, Rent Roll Recon). No existing data is
    mutated, no formula on any other sheet changes.
  - Sheet count goes from 14 → 15 (Investment Dashboard inserted at index
    1, immediately after Cover).

Why a template asset rather than programmatic cell-by-cell construction:
  - The dashboard has 335 styled cells with bold section headers, banded
    backgrounds, borders, number formats. Encoding all of that as Python
    style objects would balloon this script by 5-10×. Instead, the source
    sheet is captured once into `v024_assets/investment_dashboard_template.xlsx`
    (committed to the repo) and copied cell-by-cell with styles preserved
    at migration time.

OPERATIONS:

  A. Insert "Investment Dashboard" worksheet at index 1, copying cells +
     styles + column widths + row heights from the bundled template.
  B. Stamp AZ1:AZ5 anchor metadata on the new sheet.
  C. Stamp Cover!B8 → v0.2.4 + AZ4 on all 15 sheets.
  D. Verification: confirm sheet exists, position is 1, dimensions B2:H98,
     key formula refs intact, Cover!B8 + 15 AZ4 anchors stamped.

Idempotent: if "Investment Dashboard" already exists AND Cover!B8 is
already v0.2.4, the script re-saves without modification. If the sheet
exists but the version stamp is older, anchors + version are refreshed
without re-copying the sheet (so post-migration cell edits aren't blown
away on re-run).

Usage:
    python tools/migration/migrate_to_v024.py input.xlsx output.xlsx
"""
from __future__ import annotations

import sys
from copy import copy
from pathlib import Path

import openpyxl

SUBSTRATE_FROM = "v0.2.3"
SUBSTRATE_TO = "v0.2.4"

NEW_SHEET = "Investment Dashboard"
NEW_SHEET_INDEX = 1  # immediately after Cover

# 15-sheet anchor list (v0.2.4 adds "Investment Dashboard" between Cover
# and T12 Analytics; prior 14-sheet list is in migrate_to_v023.py).
ANCHOR_SHEETS = (
    "Cover", "Investment Dashboard",
    "T12 Analytics", "T12 Input", "T12 Raw Data",
    "Rent Roll Input", "Rent Roll Recon", "Monthly Trending", "UW Output",
    "UW Export",
    "Mapping Review", "Description_Map", "RR_Calc", "T12_Calc",
    "Workbook Health",
)

ANCHOR_PURPOSE = "Investment-grade KPI roll-up of T12 Analytics + Rent Roll Recon"
ANCHOR_CATEGORY = "Analytical (handoff)"
ANCHOR_VISIBILITY = "visible"
ANCHOR_NOTES = (
    "All cells are formula references into T12 Analytics and Rent Roll Recon. "
    "No source-of-truth data lives here."
)

TEMPLATE_PATH = (
    Path(__file__).parent / "v024_assets" / "investment_dashboard_template.xlsx"
)


def is_already_v024(wb) -> bool:
    """Gate: version stamp AND new sheet exists at expected position."""
    if wb["Cover"]["B8"].value != SUBSTRATE_TO:
        return False
    if NEW_SHEET not in wb.sheetnames:
        return False
    return wb.sheetnames.index(NEW_SHEET) == NEW_SHEET_INDEX


def has_dashboard_sheet(wb) -> bool:
    return NEW_SHEET in wb.sheetnames


def _copy_cell(src_cell, dst_cell) -> None:
    dst_cell.value = src_cell.value
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.border = copy(src_cell.border)
        dst_cell.alignment = copy(src_cell.alignment)
        dst_cell.number_format = src_cell.number_format
        dst_cell.protection = copy(src_cell.protection)


def insert_dashboard(wb) -> dict:
    """Insert the Investment Dashboard sheet from the template at index 1."""
    n = {"cells": 0, "col_widths": 0, "row_heights": 0}

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Template asset missing: {TEMPLATE_PATH}. "
            "This migration cannot proceed without the bundled dashboard template."
        )

    tmpl_wb = openpyxl.load_workbook(TEMPLATE_PATH)
    src_ws = tmpl_wb[NEW_SHEET]

    # Create at the end first, then re-order. openpyxl create_sheet's `index`
    # param is best-effort — explicit move is more reliable.
    dst_ws = wb.create_sheet(NEW_SHEET)

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

    if src_ws.sheet_view.showGridLines is False:
        dst_ws.sheet_view.showGridLines = False

    for mr in src_ws.merged_cells.ranges:
        dst_ws.merge_cells(str(mr))

    # Move the new sheet to position 1 (right after Cover).
    current_index = wb.sheetnames.index(NEW_SHEET)
    offset = NEW_SHEET_INDEX - current_index
    if offset != 0:
        wb.move_sheet(NEW_SHEET, offset=offset)

    return n


def stamp_anchor_cells(wb) -> None:
    """Fill AZ1:AZ5 on the new sheet per Workbook Health convention."""
    ws = wb[NEW_SHEET]
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

    r["sheet_exists"] = NEW_SHEET in wb.sheetnames
    r["sheet_position_ok"] = (
        r["sheet_exists"]
        and wb.sheetnames.index(NEW_SHEET) == NEW_SHEET_INDEX
    )

    az4 = {s: wb[s]["AZ4"].value for s in ANCHOR_SHEETS if s in wb.sheetnames}
    r["az4_all"] = all(v == SUBSTRATE_TO for v in az4.values())
    r["az4_count"] = len(az4)

    if r["sheet_exists"]:
        ws = wb[NEW_SHEET]
        r["sheet_dimensions"] = ws.dimensions
        r["sheet_dimensions_ok"] = ws.max_row >= 90 and ws.max_column >= 7

        # Spot-check the key headline cells that should hold formula references.
        b2 = str(ws["B2"].value or "")
        b8 = str(ws["B8"].value or "")
        b15 = str(ws["B15"].value or "")
        r["b2_title_ok"] = "INVESTMENT DASHBOARD" in b2.upper()
        r["b8_kpi_formula_ok"] = b8.startswith("=") and "T12 Analytics" in b8
        r["b15_label_ok"] = "occupancy" in b15.lower()

        # AZ1:AZ5 anchor metadata
        r["az1_purpose_ok"] = ws["AZ1"].value == ANCHOR_PURPOSE
        r["az3_visibility_ok"] = ws["AZ3"].value == ANCHOR_VISIBILITY
        r["az4_self_stamp_ok"] = ws["AZ4"].value == SUBSTRATE_TO
    else:
        r["sheet_dimensions"] = None
        r["sheet_dimensions_ok"] = False
        r["b2_title_ok"] = False
        r["b8_kpi_formula_ok"] = False
        r["b15_label_ok"] = False
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

    if is_already_v024(wb):
        print(f"Workbook is already at {SUBSTRATE_TO}. No-op (will re-save).")
        wb.save(dst)
        return 0

    print(f"Migrating {SUBSTRATE_FROM} -> {SUBSTRATE_TO}...")

    if not has_dashboard_sheet(wb):
        n = insert_dashboard(wb)
        print(f"  A: inserted '{NEW_SHEET}' at index {NEW_SHEET_INDEX} — "
              f"{n['cells']} cells, {n['col_widths']} col widths, "
              f"{n['row_heights']} row heights")
    else:
        # Sheet already present but version older than v0.2.4 — refresh
        # anchors only, don't re-copy.
        print(f"  A: '{NEW_SHEET}' already present, skipping sheet copy")
        # Ensure it's in the right position even if pre-existing.
        if wb.sheetnames.index(NEW_SHEET) != NEW_SHEET_INDEX:
            current_index = wb.sheetnames.index(NEW_SHEET)
            wb.move_sheet(NEW_SHEET, offset=NEW_SHEET_INDEX - current_index)
            print(f"     repositioned to index {NEW_SHEET_INDEX}")

    stamp_anchor_cells(wb)
    print(f"  B: stamped AZ1:AZ5 on '{NEW_SHEET}'")

    stamp_versions(wb)
    print(f"  C: stamped substrate version -> {SUBSTRATE_TO} on "
          f"Cover!B8 + {len(ANCHOR_SHEETS)} AZ4 anchors")

    print(f"Saving to {dst}...")
    wb.save(dst)

    print(f"Verifying {dst}...")
    wb2 = openpyxl.load_workbook(dst)
    r = verify_migration(wb2)

    print()
    print("=== Verification ===")
    print(f"  Cover!B8 = {r['cover_b8']!r:24s}    : {r['cover_b8_ok']}")
    print(f"  '{NEW_SHEET}' sheet exists           : {r['sheet_exists']}")
    print(f"  Sheet at position {NEW_SHEET_INDEX} (after Cover)     : {r['sheet_position_ok']}")
    print(f"  Sheet dimensions = {r['sheet_dimensions']!s:10s}      : {r['sheet_dimensions_ok']}")
    print(f"  B2 holds title                         : {r['b2_title_ok']}")
    print(f"  B8 KPI cell is formula into T12 Analytics : {r['b8_kpi_formula_ok']}")
    print(f"  B15 'occupancy' label present          : {r['b15_label_ok']}")
    print(f"  AZ1 purpose stamped                    : {r['az1_purpose_ok']}")
    print(f"  AZ3 visibility stamped                 : {r['az3_visibility_ok']}")
    print(f"  AZ4 self-stamp = {SUBSTRATE_TO}              : {r['az4_self_stamp_ok']}")
    print(f"  All 15 AZ4 = {SUBSTRATE_TO}                 : {r['az4_all']} ({r['az4_count']} sheets)")

    all_ok = (
        r["cover_b8_ok"]
        and r["sheet_exists"] and r["sheet_position_ok"]
        and r["sheet_dimensions_ok"]
        and r["b2_title_ok"] and r["b8_kpi_formula_ok"] and r["b15_label_ok"]
        and r["az1_purpose_ok"] and r["az3_visibility_ok"]
        and r["az4_self_stamp_ok"] and r["az4_all"]
    )
    print()
    print("=== " + ("[OK] Migration complete" if all_ok else "[FAIL] Migration incomplete") + " ===")
    return 0 if all_ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python migrate_to_v024.py input.xlsx output.xlsx")
        sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
