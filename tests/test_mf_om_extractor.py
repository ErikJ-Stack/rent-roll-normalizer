"""
Tests for `mf_om_extractor` (MF Offering-Memorandum intake, Track 4-MF P3).

Three layers, only the first two need no gitignored deps:
  - number coercers + the LLM JSON -> dataclass mapping (`_result_from_json`),
    driven by a synthetic payload — always runs in CI.
  - writer integration (`populate_mf_model(om=...)`) against the committed
    `assets/MF_UW_Model_v15.xlsx` — always runs.
  - the basic deterministic engine on the three real OM PDFs in `MF Docs/OM/`
    (gitignored) — skipped when the fixtures are absent.

The LLM engine itself is NOT exercised here (needs an API key); its output shape
is covered via `_result_from_json` on a recorded-shape payload.
"""
import io
import os

import openpyxl
import pytest

from mf_om_extractor import (
    MFOMExtractorError, MFRentComp, _int, _num, _result_from_json, _year,
    parse_mf_om,
)
from mf_uw_model_writer import _occ_fraction, populate_mf_model

MODEL = "assets/MF_UW_Model_v15.xlsx"
OM_DIR = "MF Docs/OM"


# --------------------------------------------------------------------------- #
# coercers
# --------------------------------------------------------------------------- #
def test_num_strips_symbols():
    assert _num("$1,330") == 1330.0
    assert _num("32.18 Acres") == 32.18
    assert _num("") is None and _num(None) is None
    assert _num(376) == 376.0


def test_int_and_year():
    assert _int("376 units") == 376
    assert _int(None) is None
    assert _year("1975/2005") == 1975        # built year, not renovation
    assert _year("Built 2024") == 2024
    assert _year("n/a") is None


def test_occ_fraction():
    assert _occ_fraction("96%") == 0.96
    assert _occ_fraction(0.91) == 0.91
    assert _occ_fraction(88) == 0.88
    assert _occ_fraction("") is None


# --------------------------------------------------------------------------- #
# LLM JSON -> dataclass mapping
# --------------------------------------------------------------------------- #
def _payload():
    """Mirrors the shape Claude returns for the Ascend OM."""
    return {
        "prop_info": {
            "property_name": "Ascend Brunswick Village", "city": "Leland",
            "state": "NC", "county": "Brunswick", "units_total": 334,
            "year_built": 2024, "building_class": "A", "amenity_tier": "Luxury",
            "lot_acres": "30 acres", "parking_spaces": "600",
            "value_add_thesis": "New-build lease-up with 6% trade-outs.",
            "unit_mix": [
                {"unit_type": "1BR", "count": 120, "avg_sf": 749, "market_rent": 1345},
                {"unit_type": "1BR Casita", "count": 63, "avg_sf": 795, "market_rent": 1603},
                {"unit_type": "2BR", "count": 110, "avg_sf": 1098, "market_rent": 1601},
                {"unit_type": "3BR", "count": 41, "avg_sf": 1382, "market_rent": 1900},
            ],
        },
        "market": {"city_market": "Wilmington, NC", "avg_household_income": "$112,000",
                   "population_growth_rate": "57% / 10yr"},
        "comps": [
            {"name": "Hawthorne Cottages At Leland", "year_built": "2023",
             "occupancy": "98%", "units": 160, "avg_sf": 1131, "asking_rent": 2030},
            {"name": "Westgate Townes", "year_built": "2025", "occupancy": "64%",
             "units": 240, "avg_sf": 1459, "asking_rent": 1868},
            {"name": "", "asking_rent": 999},   # blank name -> dropped
        ],
        "proforma": {"asking_price": "$80,000,000", "noi": None},
    }


def test_result_from_json_maps_and_coerces():
    om = _result_from_json(_payload(), engine="llm", page_count=35, warnings=[])
    pi = om.prop_info
    assert pi.units_total == 334 and pi.year_built == 2024
    assert pi.lot_acres == 30.0 and pi.parking_spaces == 600   # coerced from strings
    assert len(pi.unit_mix) == 4
    assert om.market.avg_household_income == 112000.0
    assert len(om.comps) == 2                  # blank-name comp dropped
    assert om.comps[0].name == "Hawthorne Cottages At Leland"
    assert om.proforma is not None and om.proforma.asking_price == 80000000.0


# --------------------------------------------------------------------------- #
# writer integration (committed model)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.path.exists(MODEL), reason="committed MF model absent")
def test_writer_writes_prop_info_and_comps_preserving_formulas():
    om = _result_from_json(_payload(), engine="llm", page_count=35, warnings=[])
    out, report = populate_mf_model(open(MODEL, "rb").read(), om=om)
    assert report["om_prop_cells"] >= 10
    assert report["om_comps"] == 2

    wb = openpyxl.load_workbook(io.BytesIO(out))
    pi, rc = wb["Prop Info"], wb["Rental Comps"]
    assert pi["B4"].value == "Ascend Brunswick Village"
    assert pi["B6"].value == 334
    assert pi["B9"].value == 2024
    assert pi["B13"].value == "A"
    assert pi["B17"].value == 183            # 1BR 120 + Casita 63 both -> 1BR bucket
    assert pi["B18"].value == 110            # 2BR
    assert pi["B31"].value == 41             # 3BR
    # comps
    assert rc["R8"].value == "Hawthorne Cottages At Leland"
    assert rc["T8"].value == 2023 and rc["U8"].value == 160
    assert rc["X8"].value == 2030 and rc["AB8"].value == 0.98
    # formulas survive (subject row + eff-rent / $-per-SF)
    assert str(rc["Z8"].value).startswith("=IFERROR(")
    assert str(rc["R7"].value).startswith("='Prop Info'")


@pytest.mark.skipif(not os.path.exists(MODEL), reason="committed MF model absent")
def test_rr_units_override_om_units():
    """RR is authoritative: property_units wins over the OM's unit count for B6."""
    om = _result_from_json(_payload(), engine="llm", page_count=35, warnings=[])
    out, _ = populate_mf_model(open(MODEL, "rb").read(), om=om, property_units=999)
    wb = openpyxl.load_workbook(io.BytesIO(out))
    assert wb["Prop Info"]["B6"].value == 999


# --------------------------------------------------------------------------- #
# basic engine on the real OM PDFs (gitignored fixtures)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not os.path.exists(f"{OM_DIR}/Blairstone_OM.pdf"),
                    reason="OM fixtures absent (MF Docs/ gitignored)")
def test_basic_engine_blairstone():
    om = parse_mf_om(f"{OM_DIR}/Blairstone_OM.pdf", engine="basic")
    pi = om.prop_info
    assert pi.units_total == 376
    assert pi.year_built == 1988
    assert pi.lot_acres == 32.18
    assert pi.num_buildings == 42
    assert pi.parking_spaces == 692
    assert pi.county == "Leon"
    assert om.engine == "basic" and om.comps == []   # basic = no comps


@pytest.mark.skipif(not os.path.exists(f"{OM_DIR}/Avana_OM.pdf"),
                    reason="OM fixtures absent (MF Docs/ gitignored)")
def test_basic_engine_avana():
    pi = parse_mf_om(f"{OM_DIR}/Avana_OM.pdf", engine="basic").prop_info
    assert pi.units_total == 264
    assert pi.year_built == 1985
    assert pi.county == "Prince William"


def test_unknown_engine_raises():
    with pytest.raises(MFOMExtractorError):
        parse_mf_om(b"%PDF-1.4 fake", engine="bogus")
