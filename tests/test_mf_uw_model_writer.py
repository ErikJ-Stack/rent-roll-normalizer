"""
Tests for `mf_uw_model_writer.populate_mf_model`.

The MF UW Model is committed at `assets/MF_UW_Model_v25.xlsx`, so these run in
CI with synthetic in-memory RR/T-12 inputs (no gitignored deps). They assert the
writer pastes into the right cells, leaves the model's formulas intact, and
produces a valid, reloadable workbook.
"""
import io
import os
import re
import zipfile

import openpyxl
import pytest

from mf_normalizer import MFRRResult, MFUnit
from mf_t12_normalizer import MFT12Line, MFT12Result
from mf_uw_model_writer import populate_mf_model

MODEL = "assets/MF_UW_Model_v25.xlsx"
pytestmark = pytest.mark.skipif(not os.path.exists(MODEL), reason="committed MF model absent")


def _synthetic():
    units = [
        MFUnit(bldg_unit="A1", bldg="A", unit="1", unit_type="1x1", sqft=890,
               status="Occupied No Notice", resident="Tester, A", legal=False,
               market_rent=800, actual_charges=885, scheduled_charges=870,
               balance=28.1, deposit=0, ar_0_30=28.1),
        MFUnit(bldg_unit="A2", bldg="A", unit="2", unit_type="2x2", sqft=1230,
               status="Vacant Unrented Not Ready", resident="", legal=False,
               market_rent=925),
        MFUnit(bldg_unit="B3", bldg="B", unit="3", unit_type="2x2",
               status="Occupied No Notice", resident="Smith, Z", legal=True,
               market_rent=950, scheduled_charges=980, balance=15000, ar_90_plus=15000),
    ]
    rr = MFRRResult(units=units)
    lines = [
        MFT12Line("41000-000", "Market Rent", [1000] * 12, 12000,
                  "Gross Potential Rent", "income", "income"),
        MFT12Line("61030-000", "Management Fees", [100] * 12, 1200,
                  "Management Fee", "expense", "expense"),
    ]
    t12 = MFT12Result(format_guess="yardi_numbered",
                      month_labels=["Apr 2025", "May 2025", "Jun 2025", "Jul 2025",
                                    "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025",
                                    "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026"],
                      period="Apr 2025 – Mar 2026", lines=lines)
    return rr, t12


def test_populate_counts_and_cells():
    rr, t12 = _synthetic()
    model = open(MODEL, "rb").read()
    out, report = populate_mf_model(model, t12=t12, rr=rr,
                                    property_name="Unit Test Property",
                                    property_units=rr.unit_count)
    assert report["rr_units"] == 3
    assert report["t12_lines"] == 2

    wb = openpyxl.load_workbook(io.BytesIO(out), data_only=False)
    g, t, pi = wb["Rent Roll Analysis"], wb["T-12 Analysis"], wb["Prop Info"]

    # RR grid (anchor A273)
    assert g["A273"].value == "A" and g["B273"].value == "1"
    assert g["E273"].value == "Occupied No Notice"
    assert g["G275"].value is True            # legal flag as a real Excel boolean
    assert abs(g["O273"].value - 28.1) < 0.01  # balance
    assert abs(g["Q273"].value - 28.1) < 0.01  # AR 0–30

    # T-12 Layer 1 (anchor A106): inputs written, O is a SUM formula, P is the bucket
    assert t["A106"].value == "41000-000"
    assert t["O106"].value == "=SUM(C106:N106)"
    assert t["P106"].value == "Gross Potential Rent"
    assert t["C105"].value == "Apr 2025"       # month header aligned

    # Prop Info
    assert pi["B4"].value == "Unit Test Property"
    assert pi["B6"].value == 3


def test_model_formulas_survive():
    rr, t12 = _synthetic()
    out, _ = populate_mf_model(open(MODEL, "rb").read(), t12=t12, rr=rr)
    wb = openpyxl.load_workbook(io.BytesIO(out), data_only=False)
    # key diagnostic formulas untouched by the writer
    assert wb["T-12 Analysis"]["N80"].value == "=N67+N79"           # EGI
    assert wb["Rent Roll Analysis"]["I5"].value == "=COUNTA(B273:B1772)"
    assert wb["T-12 Analysis"]["B58"].value.startswith("=SUMIFS")    # bucket aggregation
    # v20 per-row chart-helper formula columns AL–AP sit outside the writer's
    # A–AK clear band and must survive intact.
    assert str(wb["Rent Roll Analysis"]["AL273"].value or "").startswith("=IF(")


def _cm_count(data: bytes) -> int:
    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for nm in z.namelist():
            if nm.startswith("xl/worksheets/sheet") and nm.endswith(".xml"):
                n += len(re.findall(r'cm="\d+"', z.read(nm).decode("utf-8", "ignore")))
    return n


def test_dynamic_arrays_preserved():
    """v20 ships xl/metadata.xml (Excel-365 dynamic arrays); the writer's
    _restore_dynamic_arrays repair must re-inject it + the cm markers after the
    openpyxl save (openpyxl quirk #6)."""
    rr, t12 = _synthetic()
    model = open(MODEL, "rb").read()
    out, _ = populate_mf_model(model, t12=t12, rr=rr)
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        assert "xl/metadata.xml" in z.namelist()       # restored, not dropped
    assert _cm_count(out) == _cm_count(model)           # every cm marker preserved
