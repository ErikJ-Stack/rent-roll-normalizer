"""
Tests for the MF rent-roll parser (`mf_normalizer`) + AR parser/join
(`mf_ar_parser`). The operator files are gitignored — tests SKIP when absent.

Pure unit tests (CI-runnable) cover the Bldg-Unit split + join key. The
end-to-end cases assert the Hidden Lakes figures: 143 units (66 occupied /
77 vacant / 9 legal-flagged) and a 62-row AR report joining 61/62 to units.
"""
import os

import pytest

RR = "MF Docs/RR-Hidden-Lakes-4-16-26-xlsx.xlsx"
AR = "MF Docs/AR-Hidden-Lakes-3-31-26-xlsx.xlsx"
# Itemized "charge codes" RR format (multi-row per unit) — gitignored deal file.
RR_ITEMIZED = os.path.expanduser(
    "~/Dropbox/Erik Javellana - Deal Review/Deals under review/"
    "MF_VA_Woodbridge_AvanaStoneyRidge/Rent Roll/"
    "Rent Roll (Operations) - Avana Stoney Ridge 05.12.26.xlsx")


# --- pure unit tests (no file deps) ---
def test_unit_key():
    from mf_normalizer import unit_key
    assert unit_key("A1") == "A1"
    assert unit_key("a-1") == "A1"
    assert unit_key(" A 1 ") == "A1"
    assert unit_key("01-101") == "01101"


def test_bldg_unit_split():
    from mf_normalizer import _split_bldg_unit
    assert _split_bldg_unit("A1") == ("A", "1")
    assert _split_bldg_unit("01-101") == ("01", "101")
    assert _split_bldg_unit("B12") == ("B", "12")


# --- end-to-end (skip if gitignored files absent) ---
@pytest.mark.skipif(not os.path.exists(RR), reason="gitignored RR sample absent")
def test_rr_hidden_lakes():
    from mf_normalizer import parse_mf_rr
    r = parse_mf_rr(RR)
    assert r.unit_count == 143
    assert r.occupied == 66
    assert r.vacant == 77
    assert r.legal_count == 9


@pytest.mark.skipif(not os.path.exists(RR_ITEMIZED), reason="gitignored itemized RR absent")
def test_rr_itemized_charge_codes():
    """Multi-row-per-unit 'charge codes' format: identity on the header row,
    charges itemized across continuation rows and summed into the unit."""
    from mf_normalizer import parse_mf_rr
    r = parse_mf_rr(RR_ITEMIZED)
    assert r.unit_count == 263
    assert r.occupied == 244
    u = next(x for x in r.units if x.bldg_unit == "384-11")
    assert abs(u.market_rent - 1902) < 0.01
    assert abs(u.scheduled_charges - 1929) < 0.01   # Amenity 145 + Base 1784


@pytest.mark.skipif(not (os.path.exists(RR) and os.path.exists(AR)),
                    reason="gitignored RR/AR samples absent")
def test_ar_join_hidden_lakes():
    from mf_ar_parser import join_ar_to_units, parse_mf_ar
    from mf_normalizer import parse_mf_rr
    ar = parse_mf_ar(AR)
    assert len(ar.rows) == 62
    assert abs(ar.total_ar - 237542.14) < 1.0
    rr = parse_mf_rr(RR)
    rep = join_ar_to_units(rr.units, ar)
    assert rep.matched == 61
    assert len(rep.unmatched_ar) == 1            # 'L3' — not in the RR grid
    # an AR row's aging buckets sum to its own balance (gross, modulo prepayments)
    row = next(r for r in ar.rows if r.bldg_unit == "S2")
    assert abs((row.ar_0_30 + row.ar_31_60 + row.ar_61_90 + row.ar_90_plus) - row.balance) < 0.05
