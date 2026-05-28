"""
Regression tests for `uw_output_model.compute_uw_output_values` — the
in-Python UW Output evaluator that kills the cache caveat.

Run without pytest:
    python tests/test_uw_output_model.py

Two layers, both gated on the gitignored Homestead fixtures:

  1. **Engine vs cached** — parse the Homestead RR + T12 (as the app does),
     compute the UW Output values in Python, and assert they match the
     populated Analyzer fixture's cached `UW Output` values to the penny.
     This is the drift guard: if the Analyzer's T12 Analytics formulas
     change, this test catches the engine going stale.

  2. **Writer fallback end-to-end** — build a FRESH in-memory Analyzer
     (openpyxl, no cached formula values — exactly the cache-caveat state),
     run `populate_uw_template(..., computed_values=...)`, and assert the
     previously-blank `T-12 Analysis` cells now carry the right numbers and
     the report counts the in-Python fallbacks.

All inputs are property-specific data and intentionally gitignored. Skip
cleanly when absent so cold checkouts / CI don't fail.
"""
from __future__ import annotations

import datetime
import io
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
BUNDLED_ANALYZER = ROOT / "ALF_Financial_Analyzer_Only.xlsx"
TEMPLATE_V5 = ROOT / "assets" / "ALF_UW_Template_v5.xlsx"
RR_FIXTURE = ROOT / "Sample Files" / "2026-04-24 Homestead Village Rent Roll v2.xlsx"
T12_FIXTURE = ROOT / "Sample Files" / "Homestead - March 2026 T12.xlsx"
POPULATED_ANALYZER = (
    ROOT / "Sample Files"
    / "Analyzer with 2026-04-24 Homestead Village Rent Roll v2 + March 2026 T12 2026-04-24.xlsx"
)
PERIOD = datetime.date(2026, 4, 24)


class TestFailure(AssertionError):
    pass


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise TestFailure(msg)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# Concept key → (UW Output column, row) on the populated fixture (col F =
# normalized scenario, the writer default).
_UW_OUTPUT_REF = {
    "licensed_beds_il": ("B", 70), "licensed_beds_al": ("C", 70), "licensed_beds_mc": ("D", 70),
    "occupied_beds_il": ("B", 71), "occupied_beds_al": ("C", 71), "occupied_beds_mc": ("D", 71),
    "base_rent_normalized": ("F", 6), "loc_revenue": ("F", 7),
    "community_movein_fees": ("F", 8), "concessions_specials": ("F", 9),
    "respite_care": ("F", 10), "other_community_revenue": ("F", 11),
    "egi": ("F", 12), "gpr_base": ("F", 15), "physical_vacancy_loss": ("F", 16),
    "loss_to_lease": ("F", 18),
    "labor_care_staff": ("F", 22), "labor_wellness": ("F", 23), "labor_agency": ("F", 24),
    "labor_activities": ("F", 25), "labor_dining": ("F", 26), "labor_maint_hk": ("F", 27),
    "labor_admin": ("F", 28), "labor_bonus": ("F", 29), "labor_overtime": ("F", 30),
    "labor_pto": ("F", 31), "labor_payroll_taxes": ("F", 32), "labor_benefits": ("F", 33),
    "labor_workers_comp": ("F", 34), "labor_401k": ("F", 35), "labor_total": ("F", 36),
    "opex_food_cost": ("F", 38), "opex_utilities": ("F", 47), "opex_re_taxes": ("F", 53),
    "opex_bad_debt_expense": ("F", 57), "opex_nonlabor_total": ("F", 62),
    "opex_total_excl_mgmt": ("F", 63), "mgmt_fee": ("F", 64),
    "ebitdarm": ("F", 66), "ebitdar": ("F", 67), "ebitda": ("F", 68),
    "bad_debt_writeoffs_revenue": ("F", 57),
}


def _parse_inputs():
    """Mirror the app pipeline: NormalizeResult + T12ParseResult from fixtures."""
    from normalizer import normalize_rent_roll
    from t12_normalizer import parse_t12, read_descmap_descriptions

    rr = normalize_rent_roll(str(RR_FIXTURE))
    descmap = read_descmap_descriptions(
        openpyxl.load_workbook(BUNDLED_ANALYZER, data_only=True)
    )
    t12 = parse_t12(
        T12_FIXTURE.read_bytes(), descmap, annualize_partial_year=False
    )
    return rr, t12


def test_engine_matches_cached() -> None:
    """compute_uw_output_values reproduces the fixture's cached UW Output."""
    if not (RR_FIXTURE.exists() and T12_FIXTURE.exists() and POPULATED_ANALYZER.exists()):
        print("  ⊘ SKIP test_engine_matches_cached — Homestead fixtures absent")
        return

    from uw_output_model import compute_uw_output_values

    rr, t12 = _parse_inputs()
    vals = compute_uw_output_values(rr, t12)

    uo = openpyxl.load_workbook(POPULATED_ANALYZER, data_only=True)["UW Output"]

    mismatches = []
    for key, (col, row) in _UW_OUTPUT_REF.items():
        engine = _num(vals.get(key))
        cached = _num(uo[f"{col}{row}"].value)
        if engine is None or cached is None:
            ok = engine is None and cached is None
        else:
            ok = abs(engine - cached) < 0.5  # penny-level; allow float noise
        if not ok:
            mismatches.append(f"{key}: engine={vals.get(key)!r} cached={uo[f'{col}{row}'].value!r}")

    _check(not mismatches, "engine diverged from cached UW Output:\n  " + "\n  ".join(mismatches))
    print(f"  ✓ engine matches cached UW Output on {len(_UW_OUTPUT_REF)} concepts (to the penny)")
    # Headline spot-print
    print(f"      EGI={vals['egi']:,.2f}  EBITDARM={vals['ebitdarm']:,.2f}  EBITDA={vals['ebitda']:,.2f}")


def test_writer_fallback_populates() -> None:
    """A fresh (no-cache) Analyzer + computed_values fills T-12 Analysis."""
    if not (RR_FIXTURE.exists() and T12_FIXTURE.exists() and TEMPLATE_V5.exists()):
        print("  ⊘ SKIP test_writer_fallback_populates — fixtures absent")
        return

    from analyzer_rr_translator import translate_for_t12
    from analyzer_rr_writer import populate_rr_input
    from t12_normalizer_writer import populate_t12_input
    from uw_output_model import compute_uw_output_values
    from uw_template_writer import populate_uw_template

    rr, t12 = _parse_inputs()

    # Build a FRESH in-memory Analyzer exactly like the app — never saved
    # through Excel, so every formula cell has no cached value.
    after_rr = populate_rr_input(
        BUNDLED_ANALYZER.read_bytes(), translate_for_t12(rr.condensed),
        PERIOD, source_filename="homestead.xlsx",
    )
    fresh = populate_t12_input(
        after_rr, t12, new_descmap_entries=[], source_filename="t12.xlsx"
    )
    tpl = TEMPLATE_V5.read_bytes()

    # Baseline (no fallback) — the cache caveat: T-12 path comes through blank.
    _, rep_base = populate_uw_template(fresh, tpl, template_version="v5")
    base_t12_blank = sum(
        1 for r in rep_base.results if r.outcome == "no_source" and r.path == "t12"
    )

    # With the in-Python fallback.
    vals = compute_uw_output_values(rr, t12)
    out_bytes, rep = populate_uw_template(
        fresh, tpl, template_version="v5", computed_values=vals
    )
    fix_t12_blank = sum(
        1 for r in rep.results if r.outcome == "no_source" and r.path == "t12"
    )
    n_computed = rep.summary.get("computed_in_python", 0)

    _check(base_t12_blank > 50, f"expected baseline cache caveat (>50 blank), got {base_t12_blank}")
    _check(n_computed >= 60, f"expected >=60 in-Python fallbacks, got {n_computed}")
    _check(fix_t12_blank <= 2, f"expected <=2 residual t12 blanks, got {fix_t12_blank}")

    # The populated template's T-12 Analysis chain carries the right numbers.
    ta = openpyxl.load_workbook(io.BytesIO(out_bytes), data_only=False)["T-12 Analysis"]
    _check(abs(_num(ta["N69"].value) - 7001956.79) < 1.0, f"N69 EGI wrong: {ta['N69'].value}")
    _check(abs(_num(ta["N116"].value) - 1767482.75) < 1.0, f"N116 EBITDARM wrong: {ta['N116'].value}")
    _check(abs(_num(ta["N118"].value) - 1417384.90) < 1.0, f"N118 EBITDA wrong: {ta['N118'].value}")
    _check(abs(_num(ta["N115"].value) - 5234474.04) < 1.0, f"N115 Total OpEx wrong: {ta['N115'].value}")

    print(
        f"  ✓ fallback: baseline {base_t12_blank} blank → {fix_t12_blank} "
        f"({n_computed} computed in-Python); N69/N116/N118/N115 all correct"
    )


def test_dynamic_array_metadata_restored() -> None:
    """The populated output restores xl/metadata.xml + the cm= markers that
    openpyxl drops, so Section R / S dynamic-array spills survive (openpyxl
    quirk #6)."""
    if not (RR_FIXTURE.exists() and T12_FIXTURE.exists() and TEMPLATE_V5.exists()):
        print("  ⊘ SKIP test_dynamic_array_metadata_restored — fixtures absent")
        return

    import zipfile
    import re as _re
    from analyzer_rr_translator import translate_for_t12
    from analyzer_rr_writer import populate_rr_input
    from t12_normalizer_writer import populate_t12_input
    from uw_output_model import compute_uw_output_values
    from uw_template_writer import populate_uw_template

    rr, t12 = _parse_inputs()
    after_rr = populate_rr_input(
        BUNDLED_ANALYZER.read_bytes(), translate_for_t12(rr.condensed),
        PERIOD, source_filename="h.xlsx",
    )
    fresh = populate_t12_input(after_rr, t12, new_descmap_entries=[], source_filename="t.xlsx")
    vals = compute_uw_output_values(rr, t12)
    out_bytes, rep = populate_uw_template(
        fresh, TEMPLATE_V5.read_bytes(), template_version="v5", computed_values=vals
    )

    _check(rep.summary.get("dynamic_arrays_restored") == 1, "repair flag not set")
    z = zipfile.ZipFile(io.BytesIO(out_bytes))
    _check("xl/metadata.xml" in z.namelist(), "metadata.xml not restored")
    _check(z.testzip() is None, "output zip is corrupt")
    cm_total = sum(
        len(_re.findall(r'cm="', z.read(n).decode("utf-8")))
        for n in z.namelist() if _re.match(r"xl/worksheets/sheet\d+\.xml$", n)
    )
    _check(cm_total >= 500, f"expected ~557 cm markers restored, got {cm_total}")

    # Section R driver Z173 must carry the cm marker (dynamic array, not CSE).
    for n in z.namelist():
        if _re.match(r"xl/worksheets/sheet\d+\.xml$", n):
            xml = z.read(n).decode("utf-8")
            if "UNIQUE" in xml and "FILTER" in xml:
                m = _re.search(r'<c r="Z173"[^>]*>', xml)
                _check(m is not None and 'cm="' in m.group(0),
                       f"Z173 missing cm marker: {m.group(0) if m else None}")
                break

    print(f"  ✓ dynamic-array repair: metadata.xml restored, {cm_total} cm markers, Z173 marked dynamic")


def main() -> int:
    print("=== test_uw_output_model ===")
    failures = 0
    for fn in (
        test_engine_matches_cached,
        test_writer_fallback_populates,
        test_dynamic_array_metadata_restored,
    ):
        print(f"\n--- {fn.__name__} ---")
        try:
            fn()
        except TestFailure as e:
            failures += 1
            print(f"  ✗ FAIL: {e}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
    print()
    if failures:
        print(f"=== {failures} test(s) FAILED ===")
        return 1
    print("=== all tests passed ===")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
