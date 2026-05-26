# UW Template Handoff — `2026-05-25-uwt-v4-to-v5-template-gaps`

---

**Status:** Pending operator
**Template version:** v4 → v5 (proposed)
**Registry version:** 0.2.1 → 0.3.0 (will bump on receipt of v5 file)
**Triggered by:** Track 4 Phase 0 → Phase 2 (UWT v0.1.0 → v0.3.0, 2026-05-23 → 2026-05-25). Backlog of `gap_target` concepts + writer-scope decisions accumulated through three phases; consolidated here.
**Owner (Claude Code side):** Track 4 chat (UWT v0.3.0, 2026-05-25)
**Owner (operator side):** Cowork → Excel

## Summary

The mapping registry currently has **10 concepts at `gap_target` status** — Analyzer produces a value, but template v4 has no row/column to receive it. Phase 1 (registry expansion 72 → 111 concepts, 2026-05-25) and Phase 2 (writer module ship, 2026-05-25) shipped without closing these; the writer currently skips them via the default skip set (`gap_target` is in the skip list).

This handoff requests **template v5** with three structural additions on `Rent Roll Analysis`, plus a handful of smaller additions on `T-12 Analysis` / `Prop Info` / `Cover`, plus four operator decisions on writer-scope questions that depend on template intent (not structure).

After v5 lands, the writer will gain ~10 newly-mapped concepts without code changes (modular-registry pattern — extending `targets.v5 = {...}` is sufficient).

---

## Template-side changes required

### A. `Rent Roll Analysis` — three new columns past AO Pet $

Per the current rent_roll path, paste anchor is `Rent Roll Analysis!A211`, header band at row 210, and the last currently-mapped column is `AO Pet $`. The three additions slot at AP / AQ / AR (or wherever feels right given the template's existing trailing analyst-input columns at AR Conc Source / AS Effective Conc $ — operator's call on exact placement; just keep them contiguous and ahead of the analyst-input block).

#### 1. `Rent Roll Analysis!<col>210` — Care Level (tier label) header

- **Before:** No column for the tier label. Care Level $ at `AF` carries the dollar amount; the qualitative tier (Basic / Level 2-7) is dropped on paste.
- **After:** New column header (e.g. `AP210` if appended) labeled **`Care Level Tier`** — adjacent or near `AF Care Level $`. Plain text column; no formula. Width ~14, same header styling as AF.
- **Styling:** Match `AF210` header (font, fill, alignment, bold).
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `rr_care_level_tier_label`. Substrate captures the tier at `Rent Roll Input!K` since v0.1.10 / RR v1.16.0; the writer is ready to populate as soon as a target cell exists.

#### 2. `Rent Roll Analysis!<col>210` — Total Ancillary $ header

- **Before:** Per-fee ancillary columns exist at `AK Meal Plan $ / AL Scooter $ / AM Housekeeping $ / AN Laundry $ / AO Pet $`. No rollup column.
- **After:** New column header (e.g. `AQ210`) labeled **`Total Ancillary $`**, with a formula in `AQ211:AQ710` (or whatever the template's analysis range is) of the form `=SUM(AK211:AO211)`. Plain `$#,##0.00` number format.
- **Styling:** Match the existing AK-AO ancillary header band (green derived-column fill — substrate convention is `FF1F6B52` for green / derived columns; match whatever the template currently uses for AS Effective Conc $).
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `rr_total_ancillary`. The substrate has this rollup at `Rent Roll Input!AH` since v0.2.2; **no upstream change needed** — the template can derive it inline from the per-fee columns. (Optionally, the writer can paste-value from `AH` instead of letting the template recompute — operator's call. Inline formula is preferred since it stays valid if an analyst overrides a per-fee cell.)

#### 3. `Rent Roll Analysis!<col>210` — Preleased Date header

- **Before:** No template column for the Preleased Date — a per-row date captured by the RR parser (RR v1.18.0) and routed by `analyzer_rr_writer.py` to `Rent Roll Input!AJ` as of substrate v0.2.14.
- **After:** New column header (e.g. `AR210`) labeled **`Preleased Date`**, near the existing move-in / move-out date columns. Plain date number format (`mm/dd/yyyy` to match neighboring date cols). No formula.
- **Styling:** Match the `Move-out Date` column header at its current position in the template (operator to identify — likely in the H–M date band).
- **Data validation / named ranges:** None (date cells; let Excel parse).
- **Why:** Closes `gap_target` concept `rr_preleased_date`. Substrate v0.2.13 added the Preleased status to the RR Input DV list and the Section N exposure rollup on `Rent Roll Recon`; v0.2.14 relocated the date column from `AI` to `AJ` to free `AI` for Deposit per the 2026-05-25 handoff contract. Section N matches on `Status="Preleased"`, not on the date, so the substrate exposure surface stands today even without a per-row template column — but underwriting analysts reviewing the populated template rent roll need to see when each preleased unit was signed.

### B. `T-12 Analysis` — two new rows in the OpEx → NOI block

The current Layer 3 paste lands annual totals in col N at rows 56-116 (Concessions → EBITDAR = NOI). Two rows are missing.

#### 4. `T-12 Analysis!A117` (insert before existing row 117) — Total OpEx (excl. mgmt) row

- **Before:** Row 114 is `TOTAL OPERATING EXPENSES` and is inclusive of management fee. No row for opex-excluding-mgmt.
- **After:** New row inserted such that `A<row>` reads `Total Operating Expenses (excl. mgmt)` and `N<row>` accepts an annual scalar. Either (a) leave `N<row>` empty for writer to populate from UW Output row 63, or (b) make `N<row>` a formula `=N111+N85` (opex subtotal + non-mgmt-fee subtotal — adjust to existing template row numbers).
- **Styling:** Match the adjacent OpEx / NOI subtotal rows (existing row 114 is a good reference — bold, single-line border above).
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `opex_total_excl_mgmt`. Useful for underwriters running a mgmt-fee swap (replace operator's contracted rate with a market rate); having opex-excl-mgmt as an explicit line avoids re-derivation. Could also be deferred — operator's call. Defer-decision recorded below if you'd rather drop this from scope.

#### 5. `T-12 Analysis!A117` (insert after row 116 EBITDAR / NOI) — EBITDA row

- **Before:** Row 116 is `EBITDAR  (= NOI)` (label A116). No EBITDA row.
- **After:** New row inserted at `A<row>` reading `EBITDA` with `N<row>` accepting an annual scalar. The Analyzer's UW Output row 68 has EBITDA as a distinct line (= EBITDAR − rent reserve or similar — see `UW Output!A68`).
- **Styling:** Match row 116.
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `ebitda`. The Analyzer surfaces EBITDA distinctly from EBITDAR; the template currently equates EBITDAR with NOI and stops there. **Alternative:** drop EBITDA from writer scope (most UW templates do). Operator's call — see Decision D1 below.

### C. `Prop Info` — three new rows for occupied-bed split (optional)

#### 6. `Prop Info!A<rows>` — Stabilized occupied beds × {IL, AL, MC}

- **Before:** `Prop Info!B15:B18` carries licensed bed counts (total / IL / AL / MC). No occupied-bed split.
- **After:** Three new rows in the same block. Suggested placement: `A19/B19 = "Occupied beds — Total"`, `A20/B20 = "Occupied beds — IL"`, etc. The writer would populate `B19:B22` from UW Output row 71.
- **Styling:** Match `A15:B18`.
- **Data validation / named ranges:** None — but if operator wants `Occupied_Beds` named ranges for downstream use, add them.
- **Why:** Closes `gap_target` concepts `occupied_beds_il`, `occupied_beds_al`, `occupied_beds_mc`. **This is the lowest-priority structural change** — Rent Roll Analysis already computes occupancy internally from the pasted block; adding metadata cells on Prop Info is duplicative. Recommend deferring unless the downstream consumer specifically wants metadata-cell access to occupied counts (e.g. for a cover-page summary). Operator's call.

### D. `Cover` (or wherever a header band sits) — substrate version stamp cell

#### 7. `Cover!F1` (or operator's preferred location) — substrate version stamp

- **Before:** No version-stamp cell anywhere on the template. Each populated copy carries no provenance — analyst reading the file can't tell which Analyzer substrate version produced it.
- **After:** Single cell (e.g. `Cover!F1` or `Prop Info!H1`) labeled `Substrate:` in the adjacent cell and the version string in the target cell. The writer would populate it from the Analyzer's `Cover!B8` value (currently `v0.2.14`).
- **Styling:** Small (e.g. Calibri 9pt italic gray `FF595959`), right-aligned, similar to the v0.2.7 `Dashboard!N1` "Last updated" stamp pattern (BL-0021).
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `substrate_version`. Provenance — when a populated UW Template lands on someone's desk three months later, the substrate version is the single most useful piece of context for debugging discrepancies.

### E. `T-12 Analysis` — Layer 3 monthly header decision (no Excel work yet)

#### 8. Monthly header cells `B56:M56`

The cells currently hold hardcoded text values `Apr-25..Mar-26`. The writer's current default is to NOT overwrite them (writer ships annual-only in N; B-M left blank). The operator decision is whether template v5 should:

- **Option A (status quo):** Keep `Apr-25..Mar-26` hardcoded; the writer ignores them and the analyst manually relabels per deal.
- **Option B (header-only update):** Switch `B56:M56` to formula refs that read from a single template metadata cell (`Prop Info!B6` = T-12 period end), with `=EDATE(B6,-11)` / `EDATE(B6,-10)` / ... / `B6` so the headers always reflect the period.
- **Option C (writer overwrites):** Writer stamps `B56:M56` with the 12 month labels derived from the Analyzer's `T12_Period_Date` named range.

**Recommend Option B.** Single source of truth (T-12 period date on Prop Info), zero writer surface change, headers auto-adjust if analyst tweaks the period. See Decision D4 below.

---

## Mapping updates

Coupled registry edits to apply on receipt of `Sample Files/ALF_UW_Template_v5.xlsx`. Bump `registry_version` 0.2.1 → 0.3.0.

### New `templates.v5` block

Mirror `templates.v4`'s shape. New keys to confirm with operator before authoring:

```json
"templates": {
  "v4": { ... existing ... },
  "v5": {
    "file": "Sample Files/ALF_UW_Template_v5.xlsx",
    "intake_sheets": ["Prop Info", "T-12 Analysis", "Rent Roll Analysis"],
    "annual_total_column": "N",
    "monthly_columns": ["B","C","D","E","F","G","H","I","J","K","L","M"],
    "monthly_header_row": 56,
    "rent_roll_paste_anchor": "Rent Roll Analysis!A211",
    "rent_roll_header_row": 210
  }
}
```

### Per-concept `targets.v5` additions

| Concept key | v4 status | v5 target (proposed) | New status |
| --- | --- | --- | --- |
| `rr_care_level_tier_label` | `gap_target` | `'Rent Roll Analysis'!<col>211+`, `label_at: <col>210` | `mapped` |
| `rr_total_ancillary` | `gap_target` | `'Rent Roll Analysis'!<col>211+`, `label_at: <col>210` (or `derived_in_template` flag if template formula handles it) | `mapped` or `derived_in_template` |
| `rr_preleased_date` | `gap_target` | `'Rent Roll Analysis'!<col>211+`, `label_at: <col>210` | `mapped` |
| `opex_total_excl_mgmt` | `gap_target` | `'T-12 Analysis'!N<row>`, `label_at: A<row>` | `mapped` (or deferred — see D2) |
| `ebitda` | `gap_target` | `'T-12 Analysis'!N<row>`, `label_at: A<row>` | `mapped` (or deferred — see D1) |
| `occupied_beds_il` | `gap_target` | `'Prop Info'!B<row>`, `label_at: A<row>` | `mapped` (or deferred — see D5) |
| `occupied_beds_al` | `gap_target` | `'Prop Info'!B<row>`, `label_at: A<row>` | `mapped` (or deferred) |
| `occupied_beds_mc` | `gap_target` | `'Prop Info'!B<row>`, `label_at: A<row>` | `mapped` (or deferred) |
| `substrate_version` | `gap_target` | `'Cover'!F1` (or operator-chosen), `label_at: E1` | `mapped` |
| `t12_period_date` | `gap_target` | `'Prop Info'!B6` (single source for monthly header formulas) | `mapped` if Option B chosen, else stays `gap_target` |

### `open_questions` cleanup

Of the 11 currently in `registry.json`, the following will close on receipt of v5:

- ✓ Bad Debt placement (D3 below resolves)
- ✓ EBITDA row (D1 below resolves)
- ✓ Occupied beds target (D5 below resolves)
- ✓ Date header at A5 format (operator confirms `mm/dd/yyyy` in v5 file)
- ✓ Monthly header overwrite policy (D4 below resolves)
- ✓ Preleased Date in template v5 (the two duplicate entries — close both)

Remaining open after v5:

- 2nd Person Revenue — extend UW Output to expose, or pull directly from `Rent Roll Input!V`? (D6 below — not blocking v5)
- Monthly grid B-M — accept blank, or widen UW Export contract? (D7 below — not blocking v5)
- AR aging row-level routing — needs upstream substrate change (resident-key join) before AR concepts move off `gap_source`. Not v5 work.
- Rent Roll Analysis rows 1-209 (already confirmed `derived` in v4; no change).

### Re-run after registry edits

```
python tools/uw_template/build_mapping_artifacts.py
```

Regenerates `MAPPING_TRACKER.md`, `mapping_tracker.csv`, and `mapping_mindmap.html` from the updated registry.

---

## Writer-scope decisions

Operator decisions that shape writer behavior in subsequent Claude Code work. None of these require Excel edits — they're prose answers that get recorded in `registry.json` notes and `SPEC-UWT.md`.

### D1. EBITDA — add a template row, or drop from writer scope?

- **Context:** Analyzer UW Output row 68 exposes EBITDA distinctly from EBITDAR. Template currently equates EBITDAR with NOI and stops there.
- **Options:** (a) Add a template row at `T-12 Analysis!A117` for EBITDA; writer populates from `UW Output!E68` / `F68`. (b) Drop EBITDA from writer scope; analysts read it off the Analyzer if they need it.
- **Recommendation:** (a) Add the row. The structural change is one row; downstream consumers that care about EBITDA (debt-service-coverage sizing) avoid re-deriving from EBITDAR.

### D2. Total OpEx (excl. mgmt) — add a template row, or derive inline?

- **Context:** Template row 114 is opex *inclusive* of mgmt fee. Analyzer UW Output row 63 exposes opex *excluding* mgmt fee distinctly.
- **Options:** (a) Add a template row at `T-12 Analysis!A<117 or wherever>` for opex-excl-mgmt; writer populates from `UW Output!E63` / `F63`. (b) Don't add a row — the value is derivable as `N114 − N113` on the template side, and the few use cases (mgmt-fee swap analysis) can derive it inline. (c) Make `N<new row>` a formula `=N114-N113` and label it; no writer involvement.
- **Recommendation:** (c) — formula-derived row with label. Same template-side surface as (a) but zero writer dependency.

### D3. Bad Debt placement — revenue contra (template row 62) vs opex (template row 106)?

- **Context:** Analyzer UW Output row 57 is "Bad debt expense." Template has it in *both* places — A62 in the GPR waterfall band (revenue contra) and A106 in the OpEx block. Writer currently writes to N62 only (registry entry `bad_debt_writeoffs_revenue` → `'T-12 Analysis'!N62`); registry's `opex_bad_debt_expense` is in `_SPECIAL_SKIP_KEYS` to avoid double-counting.
- **Options:** (a) Confirm N62 only (current writer default). (b) Switch to N106 only. (c) Write to both and the template handles deduplication.
- **Recommendation:** (a) — confirm N62 only. The 2026-05-25 handoff contract puts bad debt as a revenue contra-line; ALF UW convention treats write-offs as revenue contra (not opex) because the GL never recognizes the revenue. The N106 cell in the template is a vestigial slot; either delete it from v5 or leave it labeled but blank.

### D4. Monthly header `T-12 Analysis!B56:M56` — overwrite policy?

See Change E.8 above. Three options. **Recommend Option B** (formula refs to a single Prop Info period cell) — zero writer surface change, single source of truth.

### D5. Occupied beds metadata cells on Prop Info — add or defer?

- **Context:** Rent Roll Analysis already computes occupied bed counts from the pasted block. Adding metadata cells on Prop Info is duplicative but gives downstream-consumer cover pages direct access.
- **Options:** (a) Add rows; writer populates. (b) Defer indefinitely.
- **Recommendation:** (b) Defer. Three template-side rows of pure duplication is low-value. Revisit only if a specific downstream report needs them.

### D6. 2nd Person Revenue — UW Output extension, or RR direct? (NOT blocking v5)

- **Context:** Template has a dedicated 2P Revenue row (`T-12 Analysis!N67`). UW Output does not break 2P out separately — 2P amounts are captured per-bed at `Rent Roll Input!V` and folded into Total Monthly Rev. Concept `second_person_revenue` is currently `gap_source` (= source side missing the breakout, not target side missing the slot).
- **Options:** (a) Extend UW Output with a new row exposing the 2P annual rollup; writer populates N67 from there. (b) Writer reads `RR_Input_Data!V` directly and rolls up at populate time. (c) Leave N67 blank for analyst entry.
- **Recommendation:** (b) — writer rollup from RR_Input_Data. Lowest-friction; substrate change avoided. Defer to next writer iteration; not blocking v5.

### D7. Monthly grid `B-M` on T-12 Analysis — leave blank, or widen UW Export contract? (NOT blocking v5)

- **Context:** Template Layer 3 expects 12 months of bucket-level data in cols B-M; UW Output only exposes annual totals (col N target). Writer ships v0.1 with B-M left blank.
- **Options:** (a) Accept blank B-M for now. (b) Widen UW Export to expose monthly bucket data; writer fills B-M.
- **Recommendation:** (a) — defer. Monthly trending is already on the Analyzer's `Monthly Trending` sheet; analysts who need the grid can copy-paste manually for v0.1. Revisit if multiple deals show analysts spending real time on this step.

---

## Verification checklist

### Operator side (in Excel after authoring v5)

- [ ] Three new columns on `Rent Roll Analysis` (Care Level Tier / Total Ancillary $ / Preleased Date) — headers at row 210, formatted to match neighbors.
- [ ] Total Ancillary $ column has a working `=SUM(...)` formula in row 211+ that picks up the per-fee ancillary cols.
- [ ] EBITDA row added on `T-12 Analysis` (if chose D1 = add).
- [ ] Total OpEx (excl. mgmt) row added on `T-12 Analysis` with `=N114-N113` formula (if chose D2 = formula option).
- [ ] Substrate version stamp cell on `Cover` styled subtly (italic gray small font).
- [ ] Monthly header cells `T-12 Analysis!B56:M56` either kept as hardcoded text, or switched to formula refs from a single period-date cell — per D4.
- [ ] No round-trip through Google Sheets / LibreOffice (BL-0018 lesson: avoids `_xludf.minifs` / lowercase formula prefix corruption).
- [ ] All existing v4 chart objects preserved (Rent Roll Analysis diagnostic charts, T-12 Analysis layered analysis charts).
- [ ] All existing v4 formula-derived columns preserved (Rent Roll Analysis cols V, X, Y, Z, AA, AB, AS).
- [ ] Existing v4 manual analyst-input columns preserved (Rent Roll Analysis cols AR Conc Source, AS Effective Conc $).
- [ ] File dropped at `Sample Files/ALF_UW_Template_v5.xlsx` (gitignored — same location convention as v4).

### Claude Code side (next chat, on receipt of v5)

- [ ] Verify file presence at `Sample Files/ALF_UW_Template_v5.xlsx` and bind reader to it.
- [ ] Inspect v5 to capture exact column letters / row numbers for each new addition.
- [ ] Extend `registry.json`:
  - [ ] Add `templates.v5 = {...}` block.
  - [ ] Update each affected concept entry with `targets.v5 = {...}` per the table above.
  - [ ] Bump `registry_version` 0.2.1 → 0.3.0.
  - [ ] Close the 6 listed `open_questions`; surface any new ones.
- [ ] Re-run `python tools/uw_template/build_mapping_artifacts.py`.
- [ ] Add a `'v5'` branch to the writer's `template_version` dispatch in `uw_template_writer.py` (likely zero code — registry-driven dispatch already handles it; just confirm).
- [ ] Smoke-test `populate_uw_template(analyzer_bytes, v5_bytes, template_version='v5')` against both fixtures:
  - [ ] Empty Analyzer (bundled v0.2.14).
  - [ ] Homestead populated (gitignored).
- [ ] Verify the 10 previously-skipped concepts now report `written` in `PopulateReport`.
- [ ] Mark this handoff **Verified** in [HANDOFF_TRACKER.md](../HANDOFF_TRACKER.md).
- [ ] Add a `CHANGELOG-UWT.md` entry for UWT v0.4.0 (registry 0.3.0 + template v5 binding).

---

## Cross-references

- **Backlog:** No BL ticket — this handoff covers Track 4 forward work, distinct from the closed-and-shipped backlog items.
- **Spec:** [`SPEC-UWT.md`](../../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../../CHANGELOG-UWT.md) (v0.3.0 entry is the immediate predecessor of the v0.4.0 work this handoff enables)
- **Writer module:** [`uw_template_writer.py`](../../../uw_template_writer.py)
- **Writer tests:** [`tests/test_uw_template_writer.py`](../../../tests/test_uw_template_writer.py)
- **Authoritative handoff contract (Analyzer side):** `Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md` (external — maintained outside repo)
- **Registry entries affected:** `rr_care_level_tier_label`, `rr_total_ancillary`, `rr_preleased_date`, `opex_total_excl_mgmt`, `ebitda`, `occupied_beds_il`, `occupied_beds_al`, `occupied_beds_mc`, `substrate_version`, `t12_period_date`
- **Substrate version mapped against:** v0.2.14 (no substrate change required by this handoff)

## Notes for Cowork

- **Do not roundtrip the template through Google Sheets or LibreOffice.** BL-0018 lesson: those round-trips introduce `_xludf.minifs` UDF prefixes (and other lowercase function-name normalizations) that Excel can't evaluate as native MINIFS, breaking dependent dashboards on import. Author directly in Excel.
- **Preserve all existing v4 charts and formula-derived columns.** v4 Rent Roll Analysis has diagnostic chart objects and 7+ formula-derived columns that must not be wiped on re-author. The v0.2.7 Dashboard redesign (BL-0018, 2026-05-19) shipped with a 14-check verify that explicitly confirms chart counts — apply the same discipline here.
- **Column placement is operator's call.** This handoff prescribes the *concepts* (what columns/rows exist) and styling-by-reference (match neighbor X), not exact letters/rows. Pick what reads cleanest given the template's existing visual rhythm; Claude Code will adapt the registry to whatever you author.
- **Date format:** the existing `Rent Roll Analysis!A5/B5` Date cell is an open question (registry `rr_period_date` notes "Confirm format expectations"). If you switch B5 to formula-fed from a Prop Info period cell (D4 Option B), confirm whether it should display as `mm/dd/yyyy` or a custom format like `mmm-yy`.
