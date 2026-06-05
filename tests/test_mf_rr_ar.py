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
# RealPage OneSite "RENT ROLL DETAIL" legacy-.xls export — gitignored deal file.
RR_ONESITE = os.path.expanduser(
    "~/Dropbox/Erik Javellana - Deal Review/Deals under review/"
    "MF_NC_Leland_AscendBrunswickVillage/Rent Rolls/"
    "Ascend Brunswick Village - Rent Roll (2026.05.28).xls")
# Committed synthetic OneSite .xls fixture (CI-runnable).
ONESITE_FIXTURE = os.path.join(os.path.dirname(__file__),
                               "fixtures", "mf", "onesite_synthetic.xls")


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


# --- RealPage OneSite format + legacy .xls (committed synthetic fixture) ---
def test_onesite_synthetic_xls():
    """OneSite 'RENT ROLL DETAIL' .xls: units repeat across lease rows (deduped
    to one record), horizontal per-code charges broken out to W–AK, pre-leased
    vacant units carry the committed applicant rent, and the legacy .xls reader
    converts date cells. Trailing 'Future Residents' block stops the walk."""
    from mf_normalizer import parse_mf_rr
    import datetime as dt
    r = parse_mf_rr(ONESITE_FIXTURE)
    assert r.unit_count == 6          # 6 physical units from 8 lease rows
    assert r.occupied == 3            # A-101, A-102, A-106 (NTV still Occupied*)
    assert r.vacant == 2              # A-103 (leased), A-104
    assert r.period_hint == "04/30/2026"
    by = {u.bldg_unit: u for u in r.units}
    assert "999-999" not in by        # trailing summary row not parsed

    a101 = by["A-101"]
    assert a101.status == "Occupied No Notice"
    assert a101.market_rent == 1500 and a101.scheduled_charges == 1400
    assert a101.actual_charges == 1400 and a101.deposit == 500
    assert a101.ancillary == {"utility_reimb": 70.0, "pet": 30.0}  # internet+trash, petrent
    assert a101.move_in == dt.datetime(2025, 4, 25)               # .xls date round-trip

    a102 = by["A-102"]                # Pending-renewal secondary deduped away
    assert a102.scheduled_charges == 1500 and a102.actual_charges == 1500
    assert a102.ancillary == {"parking": 75.0, "storage": 25.0}

    a103 = by["A-103"]               # Vacant-Leased -> committed rent from applicant
    assert a103.status == "Vacant Leased"
    assert a103.actual_charges == 0 and a103.scheduled_charges == 1650
    assert a103.ancillary == {}      # no realized fee income while vacant

    assert by["A-105"].status == "Down"
    assert by["A-106"].status == "Occupied On Notice"


@pytest.mark.skipif(not os.path.exists(RR_ONESITE), reason="gitignored OneSite .xls absent")
def test_rr_onesite_ascend():
    """Live RealPage OneSite .xls (Ascend Brunswick): 334 physical units deduped
    from 396 lease rows."""
    from mf_normalizer import parse_mf_rr
    r = parse_mf_rr(RR_ONESITE)
    assert r.unit_count == 334
    assert r.occupied == 251         # 221 no-notice + 30 NTV(L)
    assert r.vacant == 81            # 54 unrented + 27 pre-leased
    u = next(x for x in r.units if x.bldg_unit == "101-101")
    assert abs(u.market_rent - 2125) < 0.01
    assert abs(u.scheduled_charges - 1865) < 0.01
    assert abs(u.ancillary.get("utility_reimb", 0) - 85) < 0.01  # internet+trash+pest


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
    assert abs(u.scheduled_charges - 1929) < 0.01      # total = Amenity 145 + Base 1784
    assert abs(u.ancillary.get("amenity", 0) - 145) < 0.01  # Amenity broken out
    # property-wide: amenity breakout < scheduled total (base rent dominates)
    amenity_total = sum(x.ancillary.get("amenity", 0) for x in r.units)
    assert 10000 < amenity_total < 15000   # ~$11,120 amenity across the property


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
