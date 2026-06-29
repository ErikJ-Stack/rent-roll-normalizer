"""
Absorb operator-authored MF_UW_Model_v25.xlsx into the MF mapping registry.

Operator dropped MF_UW_Model_v25.xlsx (2026-06-29) at
  Deals/.../Ai Underwriting/Templates/MF_UW_Model_v25.xlsx
copied to assets/MF_UW_Model_v25.xlsx (the committed binding reference).

Cell-by-cell structural diff vs v20 (verified against the binary):
  - Sheet count 24 -> 23. `Dashboard` renamed `Dash`; `Data Refresh` removed;
    several sheets reordered (P&L / Exit Strategy moved up). None are writer
    targets, so the renames/removal/reorder are harmless to the writer (it keys
    off sheet names: T-12 Analysis / Rent Roll Analysis / Prop Info / Rental
    Comps — all still present).
  - Rent Roll Analysis: header 272, anchor A273, data 273-1772, cols A-AK ALL
    IDENTICAL (diagnostic anchors G5/I5/N5/Q5/T5 still reference 273:1772;
    footer "W. OTHER CHARGES" still at row 1775). v20's blank helper cols
    AM-AP (39-42) were dropped; only AL (38, the recent-lease chart helper
    formula) remains — outside the writer's A-AK (1-37) clear band -> preserved.
  - T-12 Analysis Layer 1 (105/106/255, A-P), Prop Info col-A labels rows 4-47
    (col B values; trailing cols E/F dropped -> max col 4, irrelevant to the
    writer), and Rental Comps (SUBJECT row 7, anchor 8) all IDENTICAL to v20.
  - xl/metadata.xml present (7 cm cells), preserved on round-trip (7->7), same
    as v20.
  - NEW: 2 extended (x14) data-validation dropdowns on Rent Roll Analysis that
    openpyxl drops on save (cosmetic; writer fills those cells with real values
    regardless). Surfaced in the writer's report warning; recover via an Excel
    re-save if needed. Not a mapping concern.

Net mapping impact: ZERO concept target moved. v25 absorption = add a
`templates.v25` block recording the structural deltas + set targets.v25 = v20
(verbatim inherit; v20 itself inherited v15) for every concept.
registry_version 0.3.0 -> 0.4.0.

Idempotent: re-running is a no-op once templates.v25 exists.
"""
import json
from pathlib import Path

REG = Path(__file__).parent / "registry.json"


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))

    if "v25" in reg["templates"]:
        print("templates.v25 already present — no-op.")
        return

    base = reg["templates"].get("v20") or reg["templates"]["v15"]
    v25 = json.loads(json.dumps(base))  # deep copy of the geometry
    v25["file"] = "assets/MF_UW_Model_v25.xlsx"
    v25["external_source"] = (
        "Deals/Acquisition/_Template/MF Templates/MF_UW_Model_v25.xlsx "
        "(operator-authored in Excel; dropped 2026-06-29)")
    v25["released"] = "2026-06-29 (absorbed 2026-06-29)"
    v25["sheet_count"] = 23
    v25["structural_deltas_vs_v20"] = [
        "Sheet count 24 -> 23: `Dashboard` renamed `Dash`; `Data Refresh` "
        "removed; some sheets reordered. None are writer targets (writer keys "
        "off names; all four target sheets present).",
        "Rent Roll Analysis: header 272 / anchor A273 / data 273-1772 / cols "
        "A-AK identical to v20. v20's blank helper cols AM-AP dropped; only AL "
        "(recent-lease chart helper formula) remains, outside the writer's A-AK "
        "clear band -> preserved.",
        "T-12 Analysis Layer 1 (105/106/255, A-P), Prop Info (col A labels / "
        "col B values, rows 4-47; trailing cols E/F dropped), and Rental Comps "
        "(SUBJECT row 7, anchor 8) all identical to v20.",
        "xl/metadata.xml present (7 cm cells), preserved on round-trip (7->7).",
        "NEW: 2 extended (x14) data-validation dropdowns on Rent Roll Analysis "
        "are dropped by openpyxl on save (cosmetic — writer fills those cells "
        "with real values; recover via Excel re-save). Not a mapping concern.",
    ]
    # the v20 AL-AP helper-columns note narrows to AL-only in v25
    if "rent_roll_grid" in v25 and isinstance(v25["rent_roll_grid"], dict):
        v25["rent_roll_grid"]["helper_formula_columns"] = {
            "AL": "Template-owned per-row recent-lease chart-helper formula "
                  "(v20's blank AM-AP dropped). Formula-derived; the writer must "
                  "not overwrite (it clears only A-AK / cols 1-37)."
        }
    reg["templates"]["v25"] = v25

    inherited = 0
    for c in reg["concepts"]:
        t = c.get("targets", {})
        src = t.get("v20") or t.get("v15")
        if src is not None and "v25" not in t:
            t["v25"] = json.loads(json.dumps(src))
            inherited += 1

    reg["registry_version"] = "0.4.0"
    reg["primary_template"] = "v25"
    reg["generated_phase"] = reg["generated_phase"].replace(
        "MF_UW_Model_v20.xlsx", "MF_UW_Model_v25.xlsx")

    REG.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Absorbed v25. targets.v25 inherited on {inherited} concepts. "
          f"registry_version -> {reg['registry_version']}. "
          f"templates: {sorted(reg['templates'].keys())}")


if __name__ == "__main__":
    main()
