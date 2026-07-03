# MF UW Model Handoff — `2026-06-29-mf-uwt-v25-absorption`

---

**Status:** Verified (absorbed same session — operator authored externally, no
follow-up operator action required for the mapping; one optional cosmetic note)
**Model version:** v20 → **v25**
**Registry version:** 0.3.0 → **0.4.0**
**Triggered by:** 2026-06-29 — operator dropped `MF_UW_Model_v25.xlsx` with
"update the template for the mf side" (supersedes the v20 absorption from
2026-06-21, PR #63, still open at the time).
**Owner (Claude Code side):** MF Track 4 chat (this one)
**Owner (operator side):** Excel — already authored

## Summary

The operator authored a v25 MF UW Model, superseding v20. I copied it to
`assets/MF_UW_Model_v25.xlsx`, repointed the writer + app, and absorbed it
registry-side. **Net mapping impact is zero: every one of the writer's four
target sheets is anchor-identical to v20 (and v15), so no concept target moved.**
v25's deltas are confined to non-target sheets (rename / removal / reorder) and
formula-display layers the writer never touches — plus one new cosmetic drop
(extended data-validation dropdowns) handled the same way as comments.

## Model-side changes (operator already authored — recorded for traceability)

Verified cell-by-cell against the binary:

1. **Sheet count 24 → 23.** `Dashboard` renamed **`Dash`**; **`Data Refresh`
   removed**; several sheets reordered (P&L / Exit Strategy moved up). None are
   writer targets — the writer keys off sheet names and all four targets
   (T-12 Analysis / Rent Roll Analysis / Prop Info / Rental Comps) remain.
2. **`Rent Roll Analysis` helper columns trimmed.** v20's blank AM–AP (cols
   39–42) dropped; only **AL** (col 38, the recent-lease chart-helper formula)
   remains. Header row 272, anchor A273, data 273–1772, cols **A–AK identical**;
   diagnostic anchors G5/I5/N5/Q5/T5 still reference `273:1772`; footer "W. OTHER
   CHARGES" still at row 1775. AL is outside the writer's A–AK (1–37) clear band
   → preserved.
3. **`Prop Info`** col-A labels rows 4–47 + col-B values **identical**; trailing
   cols E/F dropped (max col 6 → 4) — irrelevant to the writer (uses A + B).
4. **`T-12 Analysis` Layer 1** (header 105 / anchor 106 / data 106–255 / cols
   A–P) and **`Rental Comps`** (SUBJECT row 7, comp anchor 8) **identical** to v20.
5. **`xl/metadata.xml`** present (7 `cm`-marked cells), preserved on round-trip
   (7 → 7), same as v20.
6. **NEW — 2 extended (x14) data-validation dropdowns on `Rent Roll Analysis`.**
   openpyxl drops these on save (it can't model the x14 DV extension). **Cosmetic
   only** — the writer fills those cells (Status/Type) with real values
   regardless; the dropdowns are an analyst data-entry aid. Surfaced in the
   writer's report warning alongside comments/add-in/doc-props. Recover via an
   Excel open + re-save if the analyst wants the dropdowns back. Not a mapping
   concern; no DV-restore repair built (proportionate to a 2-dropdown cosmetic
   loss — flag for a future repair only if the operator asks).

## Mapping updates

- **All 90 concepts:** `targets.v25` added as a verbatim inherit of `targets.v20`
  (which itself inherited v15). Status distribution unchanged: 63 mapped /
  21 gap_source / 5 proposed / 1 derived.
- **Registry-level:**
  - `registry_version`: `0.3.0` → `0.4.0`
  - `primary_template`: set to `"v25"` (the generator honors this explicit key;
    falls back to highest numeric version otherwise).
  - `templates.v25`: new block mirroring v20 with `sheet_count: 23`, a
    `structural_deltas_vs_v20` list, and an AL-only `helper_formula_columns` note.
- Absorber: `tools/mf_uw_template/_absorb_v25.py` (idempotent). Artifacts
  regenerated via `build_mapping_artifacts.py` (v25 now primary).

## Writer-scope decisions

None affecting paste behavior. The two intake paste paths are unchanged;
`template_version` remains informational (same anchors drive v15/v20/v25).

## Verification (done this session)

- [x] Cell-by-cell structural diff v20 vs v25 on all four write-target sheets — identical anchors.
- [x] Zip-part inventory: v25 retains `xl/metadata.xml`; writer output retains it; `cm` 7 → 7.
- [x] Located the new x14 DV (Rent Roll Analysis, 2 dropdowns); writer warning updated to surface the drop.
- [x] `assets/MF_UW_Model_v25.xlsx` committed; `BUNDLED_MF_MODEL_PATH` + `_VERSION` repointed.
- [x] `registry.json` `templates.v25` + `targets.v25` (×90) + `primary_template`; artifacts regenerated.
- [x] Writer test repointed to v25; all MF suites green (writer + RR/AR 10/10).
- [x] End-to-end populate against v25: 23-sheet output, `Dash` present, valid + reloadable.

## Cross-references

- **Spec:** [`SPEC-MF.md`](../../SPEC-MF.md)
- **Changelog:** [`CHANGELOG-MF.md`](../../CHANGELOG-MF.md)
- **Prior handoff:** [`2026-06-21-mf-uwt-v20-absorption.md`](2026-06-21-mf-uwt-v20-absorption.md)
- **Registry entries affected:** all 90 (verbatim `targets.v25` inherit)
- **Source docs:** `MF Docs/` *(gitignored)*

## Notes for the operator / Cowork

v15 + v20 retained at `assets/` for override / history. Do not round-trip the
blank v25 model through openpyxl to author structural changes — it drops
`xl/metadata.xml`, the Claude-for-Excel add-in, **and now the x14 DV dropdowns**
(quirk #6). The writer's auto-repair covers `metadata.xml` + `cm` markers on the
**populate output** only. If the populated model's Status/Type dropdowns matter
to the downstream analyst, open + re-save the output once in Excel (or ask for a
`_restore_data_validations` repair to be built). Author v26+ in Excel and drop
it back at `assets/`.
