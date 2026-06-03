"""
MF UW Model writer — paste normalized RR / AR / T-12 into MF_UW_Model_v15.xlsx.

Writes only the two intake grids (the diagnostic/analytic layers are formula-
driven and left untouched):
  - T-12 → `T-12 Analysis` Layer 1 (anchor A106): Acct# / Name / 12 months /
    O=SUM formula / P=`_StdCOA` bucket.
  - RR (+joined AR) → `Rent Roll Analysis` grid (anchor A273, cols A–T core).

All formulas, cross-sheet refs, legacy CSE array formulas, and the (zero) charts
survive the round-trip — verified on v15. The model has **no** `xl/metadata.xml`
(no Excel-365 dynamic-array spills), so the defensive `_restore_dynamic_arrays`
call is a harmless no-op kept for forward-compat. openpyxl does drop auxiliary
parts on save — **cell comments + their indicators, the Claude-for-Excel add-in,
and custom doc properties** (no data/formulas/charts) — surfaced in the report
as a warning; open + re-save in Excel only if you need those annotations back.

Public API:
    populate_mf_model(model_bytes, *, t12=None, rr=None, property_name=None,
                      property_units=None) -> (bytes, dict)
"""
from __future__ import annotations

import io

import openpyxl

from uw_template_writer import _restore_dynamic_arrays

# Rent Roll Analysis grid (header row 272, data 273+). 1-based column indices.
_RR = dict(bldg=1, unit=2, unit_type=3, sqft=4, status=5, resident=6, legal=7,
           move_in=8, lease_start=9, lease_end=10, exp_move_out=11,
           market_rent=12, actual_charges=13, scheduled_charges=14, balance=15,
           deposit=16, ar_0_30=17, ar_31_60=18, ar_61_90=19, ar_90_plus=20,
           notes=22)
_RR_ANCHOR = 273
_RR_END = 1772
_RR_COLS = 37  # A–AK

# T-12 Analysis Layer 1 (header row 105, data 106+).
_T12_ANCHOR = 106
_T12_END = 255
_T12_HEADER = 105


class MFModelWriterError(Exception):
    pass


def _set(ws, r, c, v):
    if v is not None and v != "":
        ws.cell(r, c).value = v


def _clear_block(ws, r0, r1, c0, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            cell = ws.cell(r, c)
            if cell.value is not None:
                cell.value = None


def populate_mf_model(model_bytes: bytes, *, t12=None, rr=None,
                      property_name: str | None = None,
                      property_units: int | None = None):
    """Populate the MF UW Model. Returns (xlsx_bytes, report_dict)."""
    wb = openpyxl.load_workbook(io.BytesIO(model_bytes), data_only=False)
    report = {"t12_lines": 0, "t12_cells": 0, "rr_units": 0, "rr_cells": 0,
              "warnings": []}

    # --- T-12 Analysis Layer 1 ---
    if t12 is not None:
        if "T-12 Analysis" not in wb.sheetnames:
            raise MFModelWriterError("Model missing 'T-12 Analysis' sheet.")
        ws = wb["T-12 Analysis"]
        _clear_block(ws, _T12_ANCHOR, _T12_END, 1, 16)  # A–P
        # month headers (C–N) aligned to the operator's actual months
        for i, lab in enumerate(t12.month_labels[:12]):
            _set(ws, _T12_HEADER, 3 + i, lab)
        n = min(len(t12.lines), _T12_END - _T12_ANCHOR + 1)
        if len(t12.lines) > n:
            report["warnings"].append(
                f"T-12 has {len(t12.lines)} lines; Layer 1 holds {n} — extra truncated.")
        for i, ln in enumerate(t12.lines[:n]):
            r = _T12_ANCHOR + i
            _set(ws, r, 1, ln.acct or "")
            _set(ws, r, 2, ln.name)
            for m, val in enumerate(ln.monthly[:12]):
                _set(ws, r, 3 + m, val)
            ws.cell(r, 15).value = f"=SUM(C{r}:N{r})"   # O = T-12 Total
            _set(ws, r, 16, ln.bucket)                   # P = → MAPPING
            report["t12_cells"] += 16
        report["t12_lines"] = n

    # --- Rent Roll Analysis grid ---
    if rr is not None:
        if "Rent Roll Analysis" not in wb.sheetnames:
            raise MFModelWriterError("Model missing 'Rent Roll Analysis' sheet.")
        ws = wb["Rent Roll Analysis"]
        _clear_block(ws, _RR_ANCHOR, _RR_END, 1, _RR_COLS)
        n = min(len(rr.units), _RR_END - _RR_ANCHOR + 1)
        if len(rr.units) > n:
            report["warnings"].append(
                f"RR has {len(rr.units)} units; grid holds {n} — extra truncated.")
        for i, u in enumerate(rr.units[:n]):
            r = _RR_ANCHOR + i
            _set(ws, r, _RR["bldg"], u.bldg)
            _set(ws, r, _RR["unit"], u.unit)
            _set(ws, r, _RR["unit_type"], u.unit_type)
            _set(ws, r, _RR["sqft"], u.sqft)
            _set(ws, r, _RR["status"], u.status)
            _set(ws, r, _RR["resident"], u.resident)
            ws.cell(r, _RR["legal"]).value = bool(u.legal)   # Excel boolean
            _set(ws, r, _RR["move_in"], u.move_in)
            _set(ws, r, _RR["lease_start"], u.lease_start)
            _set(ws, r, _RR["lease_end"], u.lease_end)
            _set(ws, r, _RR["exp_move_out"], u.exp_move_out)
            _set(ws, r, _RR["market_rent"], u.market_rent)
            _set(ws, r, _RR["actual_charges"], u.actual_charges)
            _set(ws, r, _RR["scheduled_charges"], u.scheduled_charges)
            _set(ws, r, _RR["balance"], u.balance)
            _set(ws, r, _RR["deposit"], u.deposit)
            _set(ws, r, _RR["ar_0_30"], u.ar_0_30)
            _set(ws, r, _RR["ar_31_60"], u.ar_31_60)
            _set(ws, r, _RR["ar_61_90"], u.ar_61_90)
            _set(ws, r, _RR["ar_90_plus"], u.ar_90_plus)
            _set(ws, r, _RR["notes"], u.notes)
            report["rr_cells"] += 21
        report["rr_units"] = n

    # --- Prop Info (drives the health-check reconciliations) ---
    if "Prop Info" in wb.sheetnames:
        pi = wb["Prop Info"]
        if property_name:
            _set(pi, 4, 2, property_name)        # B4 Property Name
        units = property_units if property_units is not None else (
            rr.unit_count if rr is not None else None)
        if units is not None:
            pi.cell(6, 2).value = units          # B6 # Units

    buf = io.BytesIO()
    wb.save(buf)
    out = buf.getvalue()
    out = _restore_dynamic_arrays(out, model_bytes)   # no-op on v15 (no metadata.xml)
    report["warnings"].append(
        "Cell comments, the Claude-for-Excel add-in, and custom doc properties "
        "are dropped by the Excel writer (no data/formulas/charts affected) — "
        "open + re-save in Excel if you need those annotations back.")
    return out, report
