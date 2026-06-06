# UW Template Handoff — `2026-06-05-uwt-v6-rev2-b56-monthly-header-repoint`

---

**Status:** Verified (durable fix landed on the Deals-folder canonical copy 2026-06-05)
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

**Deals canonical copy (durable fix, 2026-06-05):**
- [x] The repointed cells reference row **140** (`=C140 … =N140`), matching the
      raw month-header row `C140:N140` — so `B56` evaluates to `Apr-25` and `M56`
      to `Mar-26` on open; `N56` still reads `T-12 Total`.
- [x] `xl/metadata.xml` preserved (37-part inventory identical pre/post; restored
      via `_restore_dynamic_arrays` from the file's own bytes — no Google Sheets /
      LibreOffice round-trip). Neither file carries `xl/webextensions/`, so nothing
      to restore there.
- [x] Corrected file is the canonical Deals-folder template; committed
      `assets/ALF_UW_Template_v6.xlsx` already carried the interim fix.

**Claude Code side:**
- [x] Confirmed `B56:M56 = =C140..=N140` on the committed asset (interim patch) and
      on the Deals canonical copy (durable fix).
- [x] Writer suite green on the committed asset (v6 rev2 default, prior session).
- [x] Marked this handoff **Verified** in HANDOFF_TRACKER.md.

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

## Durable fix — APPLIED to the Deals canonical copy 2026-06-05 (macOS session)

The macOS session **could** reach the Deals path, so the durable fix landed
directly on the operator's canonical source:

- **File:** `…/Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v6.xlsx`
  (pre-fix backup preserved at
  `…/Old Versions/ALF_UW_Template_v6_pre-B56fix_2026-06-05.xlsx`).
- **Method:** the same proven `fix_one()` from
  `_fix_v6_rev2_b56_monthly_headers.py`, applied to the Deals path. This is
  faithful here with **zero fidelity loss** — a zip-part inventory diff confirmed
  both the Deals copy and the committed asset carry an **identical 37-part
  inventory** (only special part is `xl/metadata.xml`; **neither file has
  `xl/webextensions/`**), and `_restore_dynamic_arrays` restores `xl/metadata.xml`
  from the file's own pre-edit bytes. Only B56:M56 edited; no dynamic-array anchor
  touched; `N56="T-12 Total"` untouched.
- **Result (verified on the Deals copy):** `B56=C140 … M56=N140`, `N56="T-12 Total"`,
  sheet count 16, 37 parts, `xl/metadata.xml` present. The canonical source now
  matches the committed asset, so the next rev inherits the corrected header chain
  rather than drifting back.

Both the committed asset (interim patch, 2026-06-05) and the Deals canonical copy
(durable fix, 2026-06-05) now carry `B56:M56 = =C140..=N140`. Handoff **Verified**.

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
