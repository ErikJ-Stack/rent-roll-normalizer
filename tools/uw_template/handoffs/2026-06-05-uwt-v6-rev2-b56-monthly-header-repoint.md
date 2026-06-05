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

## Interim programmatic patch — APPLIED 2026-06-05

Mirrors v0.7.1 `_fix_v6_headers_and_metadata.py` / the rev2 Section-D fix:
`tools/uw_template/_fix_v6_rev2_b56_monthly_headers.py` repoints the 12 cells
`B56:M56` from `=C125..=N125` to `=C140..=N140` on the committed canonical asset
`assets/ALF_UW_Template_v6.xlsx`, with `xl/metadata.xml` restored from the file's
own pre-edit bytes (faithful — only B56:M56 edited, never a dynamic-array anchor;
`N56="T-12 Total"` untouched). Idempotent; pre-flight aborts unless row 140
carries the raw month-header (`A140="Acct #"`, `C140="Apr-25"`). Verified:
B56=`=C140`, M56=`=N140`, sheet count 16, metadata.xml present; UWT writer suite
green (v6 rev2 default — 195 concepts, `dynamic_arrays_restored: 1`).

**Still Pending operator:** the committed asset is now correct, but the
operator's **Deals-folder** v6 copy is unchanged. The durable fix is the operator
re-authoring `B56:M56 = =C140..=N140` in Excel and re-dropping, so the canonical
source doesn't drift back on the next rev. This handoff flips to **Verified**
once that lands. (The Windows session here couldn't reach the macOS Deals path;
the script intentionally patches the committed asset only.)

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
