# MF UW Model Handoff — `2026-06-21-mf-uwt-v20-absorption`

---

**Status:** Verified (absorbed same session — operator authored externally, no
follow-up operator action required)
**Model version:** v15 → **v20**
**Registry version:** 0.2.0 → **0.3.0**
**Triggered by:** 2026-06-21 — operator dropped `MF_UW_Model_v20.xlsx` at
`Deals/.../Ai Underwriting/Templates/` with "Update the MF template use. review
the mapping also."
**Owner (Claude Code side):** MF Track 4 chat (this one)
**Owner (operator side):** Excel — already authored

## Summary

The operator authored a new MF UW Model (`v20`) in Excel, jumping from `v15`. I
copied it to `assets/MF_UW_Model_v20.xlsx` (the binding committed reference),
repointed the writer + app at it, and absorbed it registry-side. **The net
mapping impact is zero: every one of the writer's four target sheets is
layout-identical to v15, so no concept target moved.** v20's deltas are all in
formula-derived / display layers the writer never touches, plus a new
`xl/metadata.xml` part (Excel-365 dynamic arrays) that the writer's existing
`_restore_dynamic_arrays` repair — a no-op on v15 — now actively preserves.

## Model-side changes (operator already authored — recorded for traceability)

Verified cell-by-cell against `assets/MF_UW_Model_v20.xlsx` (not trusted from a
note):

1. **+1 sheet: `Dashboard`** inserted at index 1 (sheet_count 23 → 24). Purely
   formula-derived institutional first-look screen; not a writer target, no new
   intake concept. No dynamic-array spills on it.
2. **`Rent Roll Analysis` — new helper columns AL–AP.** Per-row template
   formulas (AL = recent-lease selection key `=IF(($C273=$AG$245)*($N273>0)*…`).
   These sit **outside** the writer's A–AK (cols 1–37) clear/write band, so the
   writer preserves them on round-trip. Header row 272, paste anchor A273, data
   273–1772, cols A–AK, and the below-grid recapture tie-out section at row 1775
   are **identical** to v15. Diagnostic summary anchors G5/I5/N5/Q5/T5 still
   reference `273:1772`.
3. **`T-12 Analysis` Layer 1** (header 105 / anchor 106 / data 106–255 / cols
   A–P), **`Prop Info`** (col-B label rows 4–47, incl. Renter-Age rows 25/26),
   and **`Rental Comps`** (SUBJECT row 7, comp anchor 8) — all **identical** to
   v15.
4. **New `xl/metadata.xml`** (7 `cm`-marked cells; v15 had none). The writer's
   `_restore_dynamic_arrays(out, model_bytes)` call now fires for real and
   re-injects it + the `cm` markers after openpyxl's save (openpyxl quirk #6).
   Verified **7 → 7** `cm` markers preserved on round-trip; `metadata.xml`
   present in output.

## Mapping updates

- **All 90 concepts:** `targets.v20` added as a verbatim inherit of `targets.v15`
  (nothing moved). Status distribution unchanged: 63 mapped / 21 gap_source /
  5 proposed / 1 derived.
- **Registry-level:**
  - `registry_version`: `0.2.0` → `0.3.0`
  - `templates.v20`: new block mirroring `templates.v15`, with
    `sheet_count: 24`, a `structural_deltas_vs_v15` list, and a
    `rent_roll_grid.helper_formula_columns` note for AL–AP. v20 is now the
    primary template (last sorted key) the artifacts render against.
  - `generated_phase`: `MF_UW_Model_v15.xlsx` → `MF_UW_Model_v20.xlsx`.
- Absorber: `tools/mf_uw_template/_absorb_v20.py` (idempotent). Artifacts
  regenerated via `build_mapping_artifacts.py`.

## Writer-scope decisions

None. The two intake paste paths are unchanged. `template_version` remains
informational — the same anchors drive v15 and v20.

## Verification (done this session)

- [x] Cell-by-cell structural diff v15 vs v20 on all four write-target sheets — identical anchors.
- [x] Zip-part inventory diff: v20 has `xl/metadata.xml` (v15 did not); writer output retains it.
- [x] `cm` marker count preserved 7 → 7 on round-trip.
- [x] `assets/MF_UW_Model_v20.xlsx` committed; `BUNDLED_MF_MODEL_PATH` + `BUNDLED_MF_MODEL_VERSION` repointed.
- [x] `registry.json` `templates.v20` + `targets.v20` (×90); artifacts regenerated.
- [x] Writer test suite repointed to v20 + new `test_dynamic_arrays_preserved`; all MF suites green (10/10 writer+RR/AR with xlrd present).
- [x] End-to-end populate against v20: 24-sheet output, Dashboard present, valid + reloadable.

## Cross-references

- **Spec:** [`SPEC-MF.md`](../../SPEC-MF.md)
- **Changelog:** [`CHANGELOG-MF.md`](../../CHANGELOG-MF.md)
- **Registry entries affected:** all 90 (verbatim `targets.v20` inherit)
- **Source docs:** `MF Docs/` *(gitignored)*

## Notes for the operator / Cowork

v15 is retained at `assets/MF_UW_Model_v15.xlsx` for the override path / history.
Do not round-trip the blank v20 model through openpyxl to author structural
changes — it would drop `xl/metadata.xml` + the Claude-for-Excel add-in
(quirk #6). The writer's auto-repair only covers the **populate output**, not
template authoring. Author v21+ in Excel and drop it back at `assets/`.
