# UW Template Handoff — `2026-06-05-uwt-v6-rev2-b56-monthly-header-repoint`

---

**Status:** Pending operator
**Template version:** v6 rev2 in place (formula-only — no version bump)
**Registry version:** 0.6.0 (unchanged — no concept targets affected)
**Triggered by:** chat 2026-06-05 (state-review verification of the committed `assets/ALF_UW_Template_v6.xlsx`)
**Owner (Claude Code side):** Track 4 chat
**Owner (operator side):** Cowork → Excel

## Summary

The Layer-3 monthly header row `T-12 Analysis!B56:M56` is mis-pointed in the
current committed v6 binary. These 12 cells are supposed to mirror the Layer-1
raw-T-12 month-label row (`Apr-25 … Mar-26`) so the Layer-3 trending grid shows
month names above its columns. They currently read `=C125 .. =N125`, but **row
125 is an expense line ("Permits, Licenses & Dues", value 0)** — so the header
band renders zeros/blanks instead of month labels.

This is the **same openpyxl-quirk-#4 partial-repoint class** that bit v0.7.1
(`=C122` → fixed to `=C137`) and v0.8.1 / the rev2 Section-D fix. The v0.7.1 fix
repointed B56:M56 to row 137 for v6 **rev1**. The operator's v6 **rev2** ("Other
Care") restructure shifted the Layer-1 raw grid down to row **140** (its header
row is now `T-12 Analysis!C140:N140 = Apr-25 … Mar-26`), and the rev2 repoint
pass missed the B56:M56 chain — leaving it pointing at row 125. **Cosmetic only:
no total/subtotal/diagnostic math depends on B56:M56** (it is a display header,
not a SUMIFS driver), so populated outputs are numerically correct; only the
month-label header reads wrong.

## Template-side changes required

### 1. `T-12 Analysis!B56:M56` — repoint monthly headers to the rev2 raw row

- **Before:** `B56=C125`, `C56=D125`, `D56=E125`, … `M56=N125` (12 cells; row
  125 = "Permits, Licenses & Dues", an expense line → renders 0).
- **After:** `B56=C140`, `C56=D140`, `D56=E140`, … `M56=N140` (mirror the
  Layer-1 raw month-header row, which in rev2 is row 140: `C140:N140 = Apr-25 …
  Mar-26`).
- **Styling:** none — leave the existing cell formatting untouched; only the
  formula reference row number changes (125 → 140).
- **Data validation / named ranges:** none affected.
- **Why:** the rev2 income restructure shifted the Layer-1 raw grid +15 rows
  (rev1 row 125-area → rev2 row 140); the B56:M56 display-header chain was not
  re-pointed. `N56 = "T-12 Total"` (a literal label) is already correct and does
  not change.

## Mapping updates

None. No registry concept targets B56:M56 (it is a within-sheet display header,
not a writer paste target or a `uw_output` concept). `registry.json` stays at
0.6.0; no `build_mapping_artifacts.py` re-run needed.

## Verification checklist

**Operator side (in Excel after authoring):**
- [ ] `T-12 Analysis!B56` shows `Apr-25` (or the first actual T-12 month), not 0.
- [ ] `M56` shows the 12th month (`Mar-26`); `N56` still reads `T-12 Total`.
- [ ] The repointed cells reference row **140** (`=C140 … =N140`), matching the
      raw month-header row `C140:N140`.
- [ ] Save through Excel so `xl/metadata.xml` (dynamic-array Section R/S spills)
      is preserved — do **not** round-trip through Google Sheets / LibreOffice
      (openpyxl quirk #6 / BL-0018 lesson).
- [ ] Re-drop the corrected file as the canonical `assets/ALF_UW_Template_v6.xlsx`
      and into the Deals-folder template.

**Claude Code side (next chat, on receipt of the corrected template):**
- [ ] Confirm `B56:M56 = =C140..=N140` on the committed asset.
- [ ] Smoke-test `populate_uw_template(..., template_version='v6')` — B56:M56 now
      renders month labels on a populated Homestead output.
- [ ] Mark this handoff **Verified** in HANDOFF_TRACKER.md.

## Interim programmatic patch (optional, mirrors v0.7.1 / v0.8.1)

Precedent (v0.7.1 `_fix_v6_headers_and_metadata.py`, v0.8.1 Section-D,
rev2 Section-D fix) is that Claude Code may apply this formula-only repoint
programmatically **with `xl/metadata.xml` + `cm`-marker restore** as an interim
patch, then this handoff drives the durable Excel re-author so the Deals-folder
source doesn't drift again. The fix is a 12-cell reference bump (125 → 140); the
metadata restore re-injects the dynamic-array part openpyxl drops on save (see
`uw_template_writer._restore_dynamic_arrays`). Not yet applied as of this brief.

## Cross-references

- **Backlog:** not a BL ticket (cosmetic; tracked via this handoff).
- **Spec:** [`SPEC-UWT.md`](../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../CHANGELOG-UWT.md)
- **Prior instances:** 2026-05-28 handoff (v0.7.1 rev1 fix `=C122`→`=C137`);
  2026-05-30 + 2026-06-03 handoffs (Section-D `B22/B23/B24` same partial-repoint
  class).
- **Substrate version mapped against:** n/a (template-only).

## Notes for Cowork

Single formula-row bump on 12 cells. Preserve all existing cell styling. Save
through Excel (not Google Sheets / LibreOffice) to keep the dynamic-array
metadata intact. While in the file, worth a quick sanity-sweep for any *other*
`=C125`-class display references that should track the rev2 raw grid at row 140.
