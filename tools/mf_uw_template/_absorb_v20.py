"""
Absorb operator-authored MF_UW_Model_v20.xlsx into the MF mapping registry.

Operator dropped MF_UW_Model_v20.xlsx (2026-06-20) at
  Deals/.../Ai Underwriting/Templates/MF_UW_Model_v20.xlsx
copied to assets/MF_UW_Model_v20.xlsx (the committed binding reference).

Cell-by-cell structural diff vs v15 (verified, not trusted from a handoff):
  - +1 sheet: `Dashboard` inserted at index 1 (sheet_count 23 -> 24). Purely
    formula-derived first-look screen; not a writer target, no new intake
    concept.
  - Rent Roll Analysis: header row 272, paste anchor A273, data 273-1772, cols
    A-AK ALL IDENTICAL to v15 (diagnostic anchors G5/I5/N5/Q5/T5 still
    reference 273:1772). New per-row chart-helper formula columns AL-AP appended
    (AL = recent-lease selection helper); these sit OUTSIDE the writer's A-AK
    (1-37) clear band, so they are preserved on round-trip. Below-grid recapture
    tie-out section "W. OTHER CHARGES" unchanged at row 1775.
  - T-12 Analysis Layer 1: header 105, anchor 106, data 106-255, cols A-P
    IDENTICAL to v15.
  - Prop Info col-B label rows IDENTICAL to v15 (rows 4-47, incl. Renter-Age
    rows 25/26). Rental Comps SUBJECT row 7 + comp anchor 8 IDENTICAL.
  - NEW xl/metadata.xml (Excel-365 dynamic-array properties; 7 cm-marked
    cells). v15 had none. The writer's _restore_dynamic_arrays call — a no-op on
    v15 — now actively preserves these on save (verified 7->7 cm markers).

Net mapping impact: ZERO concept target moved. v20 absorption = add a
`templates.v20` block recording the structural deltas + set targets.v20 = v15
(verbatim inherit) for every concept. registry_version 0.2.0 -> 0.3.0.

Idempotent: re-running is a no-op once templates.v20 exists.
"""
import json
from pathlib import Path

REG = Path(__file__).parent / "registry.json"


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))

    if "v20" in reg["templates"]:
        print("templates.v20 already present — no-op.")
        return

    v15 = reg["templates"]["v15"]
    # v20 inherits v15's grid/layer1 geometry verbatim (nothing moved), with the
    # structural deltas recorded.
    v20 = json.loads(json.dumps(v15))  # deep copy
    v20["file"] = "assets/MF_UW_Model_v20.xlsx"
    v20["external_source"] = (
        "Deals/Acquisition/_Template/MF Templates/MF_UW_Model_v20.xlsx "
        "(operator-authored in Excel; dropped 2026-06-20)")
    v20["released"] = "2026-06-20 (absorbed 2026-06-21)"
    v20["sheet_count"] = 24
    v20["structural_deltas_vs_v15"] = [
        "+1 sheet: Dashboard inserted at index 1 (formula-derived first-look "
        "screen; not a writer target).",
        "Rent Roll Analysis: header 272 / anchor A273 / data 273-1772 / cols "
        "A-AK all identical to v15. New per-row chart-helper formula columns "
        "AL-AP appended (outside the writer's A-AK clear band -> preserved).",
        "T-12 Analysis Layer 1 (105/106/255, A-P), Prop Info (col B rows 4-47), "
        "and Rental Comps (SUBJECT row 7, anchor 8) all identical to v15.",
        "NEW xl/metadata.xml (Excel-365 dynamic arrays, 7 cm-marked cells). "
        "The writer's _restore_dynamic_arrays call is now active (no-op on v15) "
        "and preserves them on save (verified 7->7 cm markers).",
    ]
    # annotate the RR grid with the new helper columns (informational; not paste
    # targets — the writer only touches A-AK).
    v20["rent_roll_grid"]["helper_formula_columns"] = {
        "AL-AP": "Template-owned per-row chart/recapture helper formulas "
                 "(e.g. AL = recent-lease selection key). Formula-derived; the "
                 "writer must not overwrite (it clears only A-AK / cols 1-37)."
    }
    reg["templates"]["v20"] = v20

    # targets.v20 = verbatim inherit of targets.v15 for every concept that has one
    inherited = 0
    for c in reg["concepts"]:
        t = c.get("targets", {})
        if "v15" in t and "v20" not in t:
            t["v20"] = json.loads(json.dumps(t["v15"]))
            inherited += 1

    reg["registry_version"] = "0.3.0"
    reg["generated_phase"] = reg["generated_phase"].replace(
        "MF_UW_Model_v15.xlsx", "MF_UW_Model_v20.xlsx")

    REG.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Absorbed v20. targets.v20 inherited on {inherited} concepts. "
          f"registry_version -> {reg['registry_version']}. "
          f"templates: {sorted(reg['templates'].keys())}")


if __name__ == "__main__":
    main()
