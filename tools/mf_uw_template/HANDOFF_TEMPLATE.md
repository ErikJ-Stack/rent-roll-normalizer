# MF UW Model Handoff — `<YYYY-MM-DD-slug>`

> Copy this file to `handoffs/YYYY-MM-DD-<slug>.md` and fill it in. Add a row
> to [`HANDOFF_TRACKER.md`](HANDOFF_TRACKER.md) at the top of the index table.

---

**Status:** Pending operator
**Model version:** vN → vM *(or "v15 in place" if no version bump)*
**Registry version:** before → after
**Triggered by:** *(chat date, user request, or BL ticket)*
**Owner (Claude Code side):** MF Track 4 chat
**Owner (operator side):** Excel (optionally Cowork)

## Summary

*One paragraph. What changed on the Claude Code side, and what does the operator
need to do in the model to keep both sides consistent? Lead with the why.*

## Model-side changes required

> Each numbered item is one discrete Excel edit. Include the sheet, cell or
> range, and the operation. Be precise enough that a Cowork session can
> re-author without re-reading the repo.

### 1. `<Sheet>!<cell or range>` — `<one-line operation>`

- **Before:** *(current state — value, formula, or empty)*
- **After:** *(desired state)*
- **Styling:** *(font, fill, alignment, width, number format — match neighbors unless noted)*
- **Why:** *(short — link to the intake/registry change that surfaced the need)*

### 2. ...

## Mapping updates

> Registry edits coupled to the model changes above. Show before/after pairs
> against `tools/mf_uw_template/registry.json`. Run
> `python tools/mf_uw_template/build_mapping_artifacts.py` after applying.

- **Concept `<key>`:**
  - Before: `targets.v15 = {...}`
  - After: `targets.v16 = {...}`
  - Status change: *(e.g. `gap_source` → `mapped`)*
  - Why: *(short)*

- **Registry-level changes:**
  - `registry_version`: `0.X.Y` → `0.X.Z`
  - `templates.v16`: *(new block, mirroring `templates.v15` structure)*
  - `open_questions`: *(remove answered; add new)*

## Writer-scope decisions

> Pure prose. Things the operator needs to *decide* (vs. *do in Excel*) that
> shape future parser/writer behavior. Skip if all the work is structural.

- **Decision needed:** ...
  - Options: ...
  - Recommendation: ...
  - Implication: ...

## Verification checklist

**Operator side (in Excel after authoring):**
- [ ] *(e.g. New column header renders correctly; grid rows still drive the diagnostic dashboards.)*

**Claude Code side (next chat, on receipt of the updated model):**
- [ ] Drop file at `assets/MF_UW_Model_v16.xlsx` (or overwrite `v15` if minor, per policy).
- [ ] Extend `registry.json` `templates.v16 = {...}` block.
- [ ] Update affected concept entries with `targets.v16` keys.
- [ ] Re-run `python tools/mf_uw_template/build_mapping_artifacts.py`.
- [ ] Verify the zip-part inventory of the new model (metadata.xml / webextensions present — openpyxl quirk #6).
- [ ] Mark this handoff **Verified** in HANDOFF_TRACKER.md.

## Cross-references

- **Spec:** [`SPEC-MF.md`](../../SPEC-MF.md)
- **Changelog:** [`CHANGELOG-MF.md`](../../CHANGELOG-MF.md)
- **Registry entries affected:** *(list keys)*
- **Source docs:** `MF Docs/` *(gitignored — Hidden Lakes RR / Sortable-RR / AR / T-12)*

## Notes for the operator / Cowork

*Optional. e.g. don't roundtrip through Google Sheets / LibreOffice (corrupts
dynamic-array / `minifs` formulas); preserve chart objects and `_StdCOA`; keep
the `xl/metadata.xml` part on save (openpyxl quirk #6 — author in Excel, not via
a Python round-trip).*
