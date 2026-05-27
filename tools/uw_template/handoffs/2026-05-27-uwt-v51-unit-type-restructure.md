# UW Template Handoff — `2026-05-27-uwt-v51-unit-type-restructure`

---

**Status:** Pending operator
**Template version:** v5 → v5.1 (binding when shipped — overwrite `assets/ALF_UW_Template_v5.xlsx` in place)
**Registry version:** 0.3.0 → 0.4.0 *(substantial structural restructure, not just point-release)*
**Triggered by:** Operator request 2026-05-27 — "Unit Type should be before Status; reflect this completely upstream to downstream."
**Owner (Claude Code side):** Track 4 chat (UWT v0.4.4 → v0.5.1)
**Owner (operator side):** Cowork → Excel

## Summary

Restructure Rent Roll Analysis so **Unit Type** sits as a primary identifier (new col **D**, immediately before Status). The old "Unit Type (base)" helper at W and "Apt Type" at AC are both **dropped** — Section R's formula chain rewires to use the new D directly. Everything from current D–V shifts right by 1; the AC gap closes by shifting current AD–AV left by 1. Net column count: 48 → 47 (−2 dropped, +1 new).

**Why now:** Unit Type is a primary classification key (a sort/group dimension, like Care Level). Burying it at W (col 23) or AC (col 29) forces the reader to scroll right 25+ columns before seeing a fundamental unit attribute. Moving it before Status gives the user a clean left-to-right read: identity → classification → state → detail.

**Operator decisions locked in this chat:**
- W and AC both **dropped** (option 1 — cleanest data model, one Unit Type col).
- Writer source unchanged: **Analyzer col F (Apt Type)** → new template col D.
- Operator authors the Excel restructure directly (not via Cowork-with-openpyxl), labels it v5.1, overwrites `assets/ALF_UW_Template_v5.xlsx` in place.

## Template-side changes required

### 1. `Rent Roll Analysis!D` — **NEW column: "Unit Type"**

- **Before:** Column D is `Status`. Status will move to E.
- **After:** Insert a new column at position D. Header at `D210` = `"Unit Type"`. Data rows D211:D610 receive the canonical Unit Type from Analyzer col F (Apt Type) — closed vocab values: `Studio` / `1 Bedroom` / `2 Bedroom` / `3 Bedroom` / `Suite` / `Cottage`.
- **Styling:** Match the header style of the existing C210 ("Care Level") column. Data cells left unstyled (or matching neighbors C/E) — they'll be writer-paste-populated.
- **Data validation / named ranges:** None initially. If you want a closed-vocab dropdown on D211:D610, set it to `Studio,1 Bedroom,2 Bedroom,3 Bedroom,Suite,Cottage` matching the Analyzer's apt-type vocab.
- **Why:** Primary classification key. Section R's unique-key chain reads from this col directly going forward.

### 2. `Rent Roll Analysis!W` — **DROP "Unit Type (base)" column**

- **Before:** Column W (after the 1-position right-shift, that's the *old* W which would have been at X post-shift) is "Unit Type (base)" with the v0.4.4 gated-AC formula `=IF(AND($D="Occupied", $AC<>""), $AC, "")`.
- **After:** Column entirely removed from the sheet. Everything from old W onward shifts left by 1 to fill the gap.
- **Why:** Now redundant — its sole purpose was to mirror AC (which is itself being dropped). Section R's X formula will read from new D directly.

### 3. `Rent Roll Analysis!AC` — **DROP "Apt Type" column**

- **Before:** Column AC (after right-shift would be AD pre-this-drop) holds "Apt Type" — currently writer-populated from Analyzer col F.
- **After:** Column entirely removed. Everything from AC onward shifts left by 1.
- **Why:** Redundant with new col D. Writer re-targets Analyzer col F → new D instead of AC.

### 4. Update Section R formulas to use new D instead of old W

`Rent Roll Analysis` rows 173+ Section R is driven by spilled formulas at Z173 (or its new position post-shift) that reference X column for the unique-key spill. X currently concatenates `C & "|" & W` (Care|UnitType). Replace W with the new D:

- **X formula** (current): `=IF(AND(D{r}="Occupied", C{r}<>"", W{r}<>""), C{r}&"|"&W{r}, "")` — note D here is the OLD D (Status).
- **After restructure**, since cols have shifted, this lives at the new equivalent position. Rewrite to: `=IF(AND(E{r}="Occupied", C{r}<>"", D{r}<>""), C{r}&"|"&D{r}, "")` — uses **new E** (Status, was D) and **new D** (Unit Type, was W or AC).
- **Y formula** (Care|Unit all rows): `=IF(AND(C{r}<>"", D{r}<>""), C{r}&"|"&D{r}, "")` — uses new D not old W.
- **D173 AVERAGEIFS** (v0.4.4 swap): adjust col references for the shift. `$T$211:$T$610` (Sq Ft) becomes `$U$211:$U$610` (shifts right by 1 because Sq Ft was at T, now at U). `$AC$211:$AC$610` (the criteria col for the bucket Unit Type) — but AC is dropped, so this needs to point at the NEW D: `$D$211:$D$610`.

### 5. Re-verify all diagnostic-section formulas (rows 1-209)

Many formulas in the upper diagnostic sections reference specific columns:
- Care Level reference (col C — unchanged)
- Status reference (was D, becomes E)
- Sq Ft reference (was T, becomes U)
- AR Balance / Deposit / aging cols (shift right by 1)
- Apt Type lookups (was AC, becomes new D)

**Recommendation:** Open the diagnostic sections (A through R headers on rows 1-209) and audit every cell that has a formula. Use Find & Replace within Rent Roll Analysis ONLY (not workbook-wide) to bulk-update references. Critical patterns to update:

| Find | Replace with | Sheet scope |
|---|---|---|
| `$D$211:$D$610` (when ref Status) | `$E$211:$E$610` | Rent Roll Analysis only |
| `$T$211:$T$610` (when ref Sq Ft) | `$U$211:$U$610` | Rent Roll Analysis only |
| `$W$211:$W$610` (when ref old Unit Type) | `$D$211:$D$610` | Rent Roll Analysis only |
| `$AC$211:$AC$610` (when ref old Apt Type) | `$D$211:$D$610` | Rent Roll Analysis only |

⚠️ **Take care with bulk Find & Replace** — col-letter substrings can appear inside other cell refs and tokens. Manually review every match before accepting. Tools like the Name Manager and Trace Dependents can help spot reference cascades.

### 6. Re-verify chart data ranges and PivotTable sources (if any)

If Rent Roll Analysis has any chart objects or PivotTables (none currently per v5 inspection), their data-range references will need updating for the shift. Verify after the restructure.

## Mapping updates (registry — Claude Code side)

The pre-wired absorber script handles these automatically when run on the v5.1 file: `tools/uw_template/_absorb_v51_column_restructure.py`. Manual reference for what changes:

### Per-concept target shifts (v5 → v5.1)

| Concept key | v5 target | v5.1 target | Reason |
|---|---|---|---|
| `rr_unit_#` | A211+ | A211+ | unchanged (left of insert) |
| `rr_room_#` | B211+ | B211+ | unchanged |
| `rr_care_type` | C211+ | C211+ | unchanged |
| **`rr_apt_type`** | **AC211+** | **D211+** | **re-targeted to new Unit Type col; AC dropped** |
| `rr_status` | D211+ | E211+ | right-shift by 1 |
| `rr_resident_name` | E211+ | F211+ | right-shift |
| `rr_move_in_date` | F211+ | G211+ | right-shift |
| `rr_move_out_date` | G211+ | H211+ | right-shift |
| `rr_market_rate` | H211+ | I211+ | right-shift |
| `rr_actual_rate` | I211+ | J211+ | right-shift |
| `rr_total_loc` | J211+ | K211+ | right-shift (template formula col — writer skips anyway) |
| `rr_total_monthly_rev` | K211+ | L211+ | right-shift (template formula) |
| `rr_balance` (AR Balance) | L211+ | M211+ | right-shift |
| `rr_deposit` | M211+ | N211+ | right-shift |
| `ar_aging_0_30` | N211+ | O211+ | right-shift |
| `ar_aging_31_60` | O211+ | P211+ | right-shift |
| `ar_aging_61_90` | P211+ | Q211+ | right-shift |
| `ar_aging_90_plus` | Q211+ | R211+ | right-shift |
| `rr_payer_type` | R211+ | S211+ | right-shift |
| `rr_notes` | S211+ | T211+ | right-shift |
| `rr_sq_ft` | T211+ | U211+ | right-shift |
| `rr_actual_psf` | U211+ | V211+ | right-shift |
| `rr_concession` | AD211+ | AC211+ | left-shift by 1 (AC dropped, AD→AC) |
| `rr_concession_end_date` | AE211+ | AD211+ | left-shift |
| `rr_care_level_amt` | AF211+ | AE211+ | left-shift |
| `rr_med_mgmt` | AG211+ | AF211+ | left-shift |
| `rr_pharmacy` | AH211+ | AG211+ | left-shift |
| `rr_other_loc` | AI211+ | AH211+ | left-shift |
| `rr_2nd_person_rent` | AJ211+ | AI211+ | left-shift |
| `rr_meal_plan` | AK211+ | AJ211+ | left-shift |
| `rr_scooter_fee` | AL211+ | AK211+ | left-shift |
| `rr_housekeeping` | AM211+ | AL211+ | left-shift |
| `rr_laundry` | AN211+ | AM211+ | left-shift |
| `rr_pet` | AO211+ | AN211+ | left-shift |
| `rr_care_level_tier_label` | AP211+ | AO211+ | left-shift |
| `rr_total_ancillary` | AQ211+ | AP211+ | left-shift (template formula — derived) |
| `rr_preleased_date` | AR211+ | AQ211+ | left-shift |
| `rr_ach` | AS211+ | AR211+ | left-shift |
| `rr_market_psf` | AT211+ | AS211+ | left-shift |

### Registry-level changes

- `registry_version`: `0.3.0` → `0.4.0` *(major bump — structural restructure)*
- `templates.v5`: replaced in place (v5 is overwritten — not a new template_version key, just a content update)
- `templates.v5.intake_sheets`: unchanged
- `templates.v5.rent_roll_data_end_row`: unchanged at 610
- `open_questions`: any references to W or AC closed implicitly

## Writer-scope decisions

None new — writer source for the new D column was decided earlier in this chat (Analyzer col F, same as the dropped AC). The writer change is purely the registry retarget; no writer code change needed.

## Verification checklist

### Operator side (in Excel after authoring v5.1)

- [ ] `Rent Roll Analysis!D210` = `"Unit Type"` with correct styling.
- [ ] Old column W ("Unit Type (base)") completely removed from the sheet.
- [ ] Old column AC ("Apt Type") completely removed from the sheet.
- [ ] Old D210 ("Status") now at E210.
- [ ] Old V210 ("$/SqFt/Yr") now at W210.
- [ ] Old AV210 ("Effective Conc $") now at AU210 (last column).
- [ ] Section R diagnostic at rows 170-181 still shows the same headers (`R. UNIT TYPE PRICING BY CARE LEVEL` etc).
- [ ] Z173 dynamic-array formula updated to reference X (Care|UnitType) which now uses new D not W.
- [ ] A spot-check formula audit: scan rows 1-209 for any formulas still referencing `$W$` or `$AC$` — replace with `$D$`. Scan for `$D$` referring to Status — replace with `$E$`. Scan for `$T$` referring to Sq Ft — replace with `$U$`.
- [ ] All v5 chart objects (if any) preserved with updated data ranges.
- [ ] NO round-trip through Google Sheets / LibreOffice (BL-0018 lesson — `_xludf.minifs` prefix corruption).
- [ ] File overwritten at `assets/ALF_UW_Template_v5.xlsx` in the repo (since v5 → v5.1 keeps the same filename).
- [ ] Optionally also re-save at `Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v5.xlsx` to keep both copies in sync.

### Claude Code side (next chat, on receipt of v5.1)

- [ ] Verify file presence + structural fingerprint (16 sheets, RR Analysis max_col = 47 — was 48).
- [ ] Run `python tools/uw_template/_absorb_v51_column_restructure.py` to apply all registry target shifts atomically.
- [ ] Re-run `python tools/uw_template/build_mapping_artifacts.py`.
- [ ] Run writer regression: `PYTHONPATH=. python tests/test_uw_template_writer.py` — expect cell counts to be near-identical to v5 (column count drop doesn't reduce data volume) but with `rr_apt_type` now writing to D211+ instead of AC211+, and all right-shifted concepts writing to their new positions.
- [ ] Manually inspect the populated Homestead output: D211 = `"1 Bedroom"` (or whatever Janet Pierson's unit type is), E211 = `"Occupied"` (was D), AU211 (last col) populated where AV was previously.
- [ ] Bump UWT_VERSION 0.4.4 → 0.5.1 (skip 0.5.0 — used by rolled-back attempt).
- [ ] Add CHANGELOG-UWT.md v0.5.1 entry.
- [ ] Update SPEC-UWT.md current code version + phase plan row.
- [ ] Update CLAUDE.md last-updated stamp + Track 4 row.
- [ ] Mark this handoff **Verified** in HANDOFF_TRACKER.md.
- [ ] Commit + push.

## Cross-references

- **Prior handoff (also pending operator):** [`2026-05-26-uwt-v5-to-v51-residual-gaps.md`](2026-05-26-uwt-v5-to-v51-residual-gaps.md) — Cover stamp + RR Period Date metadata cells. **Recommend authoring both this handoff's restructure AND the metadata cells in the same Excel pass** (one v5.1 release covering both).
- **Spec:** [`SPEC-UWT.md`](../../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../../CHANGELOG-UWT.md) — most recent v0.4.4 (Section R re-fix) immediate predecessor
- **Writer module:** [`uw_template_writer.py`](../../../uw_template_writer.py)
- **Authoritative handoff contract:** `Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md` *(external — will need updating to reflect new col positions when v5.1 ships; §10 column crosswalk + §12 column reference both affected)*
- **Substrate version mapped against:** v0.2.14 (no substrate change required — this is purely template-side)

## Notes for Cowork

- **Combine with the prior v5.1 metadata-cells handoff in one Excel pass** if possible — both target v5.1, both overwrite `assets/ALF_UW_Template_v5.xlsx`. Doing them separately means two absorption runs.
- Take a snapshot of the v5 file before starting — column inserts and deletes can cascade unexpectedly, and being able to roll back is critical. Suggest: save `assets/ALF_UW_Template_v5_pre_v51_snapshot.xlsx` before any edits.
- The biggest risk in this restructure is broken formulas after the column shifts. Excel's automatic formula-adjustment handles MOST cases when you Insert/Delete columns natively (Excel's `Insert Column` command updates all formulas in the worksheet). But **absolute references like `$T$211` won't update** — you must hunt those down manually. The Find & Replace table in §5 above lists the critical ones; recommend scanning every formula in rows 1-209 with the formula bar visible.
- Section R, S, and the diagnostic blocks A-R in rows 1-172 reference many specific cell positions. Audit each section header's underlying formulas.
- Do NOT roundtrip through Google Sheets / LibreOffice (BL-0018 lesson — `_xludf.minifs` prefix corruption, dynamic-array semantics loss).
- The v5 → v5.1 file keeps the same name (`ALF_UW_Template_v5.xlsx`) — overwrite in place. v5.1 is a minor revision; we don't bump to v6 because the registry still treats it as `template_version='v5'`.
