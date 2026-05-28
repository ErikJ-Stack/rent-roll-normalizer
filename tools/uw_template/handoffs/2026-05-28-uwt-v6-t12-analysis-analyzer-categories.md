# UW Template Handoff — `2026-05-28-uwt-v6-t12-analysis-analyzer-categories`

---

**Status:** Pending operator
**Template version:** v5 → **v6** (major — T-12 Analysis income restructure)
**Registry version:** 0.4.2 → 0.5.0 (proposed, on absorption)
**Triggered by:** Operator review 2026-05-28 — "The ALF UW Template T-12 Analysis tab doesn't match the categories coming from the T12 Input and T12 Raw Data tab from the Analyzer. I need these specific categories coming from the Analyzer."
**Owner (Claude Code side):** Track 4 chat (registry + writer + engine + Description_Map)
**Owner (operator side):** Cowork → Excel (author the new T-12 Analysis rows)

## Summary

The T-12 Analysis **Layer 3 (Standardized Aggregation)** income section uses a
GPR→Net-Rent **market-projection waterfall** that collapses the Analyzer's
actual revenue categories: Base Rent IL/AL/MC become one "Net Rent Revenue",
LOC IL/AL/MC become one "LOC / Care Services Revenue", and the ancillary income
lines have no rows. Two concrete consequences surfaced in review:

1. **"Auto Expense" ($6,061) has no Layer-3 row** — it's dropped from the
   standardized aggregation, which is the *entire* reason Layer-3 EBITDAR
   ($1,417,385) overstates the as-reported NOI ($1,411,324) by exactly $6,061.
2. The by-care-type and ancillary revenue detail the Analyzer produces only
   appears in **Section I (Layer 1 — Raw T-12)**, not in the headline Layer-3
   view.

Operator decisions (confirmed 2026-05-28):
- **Restructure Layer 3 income to the Analyzer's actual categories** (build EGI
  bottom-up from real T-12 lines).
- **Add a dedicated "Auto Expense" non-labor row.**
- **Re-map "Second Persons Revenue | IL/AL/MC"** out of Base Rent into its own
  "2nd Person Revenue" line (Description_Map / substrate change — Claude Code).
- **Keep** the GPR / Loss-to-Lease / Vacancy waterfall, demoted to a labeled
  **diagnostic sub-section** (it's a rent-roll *projection*, not a T-12 actual).

This brief covers the **template-authoring** work (yours, in Excel). The
registry / writer / engine / Description_Map work is Claude Code's and lands on
either side of your authoring (see "Mapping updates" + sequencing below).

## Template-side changes required

> All edits are on the **`T-12 Analysis`** sheet, **Layer 3** (currently rows
> 55–118) and the Non-Labor block. Work in Excel so row inserts auto-update the
> downstream formula references (Section I/J at rows 121+, and any Scenarios /
> P&L pulls into this tab). Do **not** round-trip through openpyxl / Google
> Sheets / LibreOffice — it breaks the Rent Roll Analysis dynamic-array spills
> (openpyxl quirk #6) and re-introduces `_xludf.`/lowercase-`minifs` prefixes.

### 1. `T-12 Analysis` INCOME section (rows 57–69) — rebuild to actual T-12 categories

Replace the current income block (GPR → … → EGI) with an **actual-T-12 build**
followed by a **diagnostic waterfall**. Recommended layout (exact row numbers
are yours — keep them contiguous; the col-N total + B–M monthly grid pattern is
unchanged, and the writer mirrors col-N formulas across B–M automatically):

```
INCOME  (Actual — per T-12)
  Base Rent — IL
  Base Rent — AL
  Base Rent — MC
    Total Base Rent                    = SUM(IL:MC)            [subtotal row]
  LOC / Care Services — IL
  LOC / Care Services — AL
  LOC / Care Services — MC
    Total LOC / Care Services          = SUM(IL:MC)            [subtotal row]
  2nd Person Revenue
  Community / Move-in Fees
  Respite Care Revenue
  Meal Income
  Housekeeping Income
  Laundry Income
  Scooter Fee Revenue
  Transfer Fee Revenue
  Other Community Revenue
  Concessions & Specials               (contra — negative)
  Bad Debt / Write-offs                (contra — negative)
  EFFECTIVE GROSS INCOME (EGI)         = SUM of all the lines above   [bold total]

GPR WATERFALL — DIAGNOSTIC  (Rent Roll market projection; NOT T-12 actual)
  Gross Potential Rent (GPR)
  Less: Loss to Lease
  Less: Vacancy Loss
  Net Rent (projected)                 = GPR + Loss to Lease + Vacancy Loss
```

- **EGI formula:** sum every actual-income line **including** the two contra
  rows (Concessions and Bad Debt are stored negative, so a plain `=SUM(...)` of
  the block is correct). This preserves the v0.6.3 decision that bad debt
  reduces EGI.
- **Subtotal rows** (Total Base Rent, Total LOC) are optional but recommended —
  if you add them, make them `=SUM()` of the three care-type rows and the
  writer will leave them alone (it only writes the line items).
- **Diagnostic waterfall:** label the sub-section header clearly (e.g.
  "DIAGNOSTIC — RR market projection") so it reads as informational. Its
  Net Rent line does **not** feed EGI.
- **Styling:** match the existing Layer-3 row styling (indented line items,
  bold section headers / totals, the col-N number format, the B–M monthly grid,
  and cols O/P/Q untouched).

### 2. `T-12 Analysis` NON-LABOR — add an "Auto Expense" row

- **Before:** Non-labor has "Auto Insurance" (currently row 99); no
  "Auto Expense".
- **After:** Insert a new **"Auto Expense"** row immediately after
  "Auto Insurance". The Total Non-Labor `=SUM(...)` must expand to include it
  (it will automatically if you insert *inside* the existing SUM range).
- **Why:** the Analyzer reports "Auto Expense" ($6,061 on Homestead) distinct
  from "Auto Insurance"; today it has no row and is silently dropped from the
  standardized NOI.

### 3. Section I / Section J (rows 121+) — no manual edits

The writer rebuilds Section I (Layer 1 raw lines) and Section J (raw totals)
programmatically. Just confirm they still sit below the restructured Layer 3
after your inserts (Excel will shift them down — fine).

## Mapping updates

> Claude Code applies these on absorption, once v6 row numbers are final.

- **New concepts** (source `uw_output` or `derived`, T12-by-label):
  `base_rent_il`, `base_rent_al`, `base_rent_mc`, `loc_il`, `loc_al`, `loc_mc`,
  `rev_meal_income`, `rev_housekeeping_income`, `rev_laundry_income`,
  `rev_scooter_fee`, `rev_transfer_fee`, `opex_auto_expense` — each with a
  `targets.v6 = {sheet: 'T-12 Analysis', address: 'N<row>'}` once rows exist.
- **Re-targeted to v6 rows:** all existing T-12 Analysis concepts (the row
  numbers shift after the income restructure). `egi`, `labor_total`,
  `opex_nonlabor_total`, `opex_total_*`, `ebitdarm/ebitdar/ebitda` stay
  formula-preserved totals at their new rows; `_finalize_t12_layer3` row
  constants update to v6.
- **`second_person_revenue`** flips `derived/gap` → `mapped` (now fed by the
  re-mapped Description_Map labels).
- **Registry-level:** `registry_version` 0.4.2 → 0.5.0; new `templates.v6`
  block; `templates.v6.income_model = "actual_t12"` (vs v5 `gpr_waterfall`).

## Writer-scope decisions

- **2nd Person Revenue re-map (Description_Map / substrate — Claude Code, independent of this template):**
  - Change Description_Map so `Second Persons Revenue | Independent Living` (and
    AL / MC) map to label **`2nd Person Revenue`** instead of **`Base rent — IL/AL/MC`**.
  - **Implication:** Base Rent IL/AL/MC totals drop by the 2nd-person amount;
    "2nd Person Revenue" (currently $0 on Homestead) gets it. EGI is unchanged
    (pure reallocation). This works against the **current** template too — the
    existing N67 "2nd Person Revenue" row will populate immediately.
  - This is a **substrate migration** (bundled Analyzer Description_Map +
    `read_descmap_descriptions`), versioned separately on the Track-2 stream.

## Verification checklist

**Operator side (in Excel after authoring):**
- [ ] INCOME block lists Base Rent IL/AL/MC, LOC IL/AL/MC, 2nd Person, Community, Respite, Meal/HK/Laundry/Scooter/Transfer, Other, Concessions, Bad Debt → EGI.
- [ ] EGI = `=SUM()` of the whole actual-income block (contras negative).
- [ ] "Auto Expense" row present in Non-Labor, inside the Total Non-Labor SUM.
- [ ] GPR / Loss-to-Lease / Vacancy live under a clearly-labeled DIAGNOSTIC sub-header and do **not** feed EGI.
- [ ] Section R/S on Rent Roll Analysis still spills (open once in Excel, accept any repair, save — confirms dynamic arrays intact).
- [ ] Save as `assets/ALF_UW_Template_v6.xlsx` (or drop for filename consolidation per policy).

**Claude Code side (on receipt of v6):**
- [ ] Add `templates.v6` block + `targets.v6` for every T-12 Analysis concept; new revenue/auto concepts.
- [ ] Engine: expose by-care base rent + LOC, the 5 ancillary income lines, `opex_auto_expense` (label sums already computed by `_aggregate_t12`).
- [ ] Writer: populate new rows; update `_finalize_t12_layer3` row map + EGI/Net-Rent formula handling for v6; default `template_version='v6'`.
- [ ] Description_Map 2nd-Person re-map migration (substrate).
- [ ] Re-run `build_mapping_artifacts.py`; smoke-test on empty + Homestead.
- [ ] Reconcile: EGI ties to the actual-income sum; NOI ties to as-reported $1,411,324 (Auto Expense now captured).
- [ ] Mark this handoff **Verified**.

## Cross-references

- **Backlog:** related to BL-0026 (Layer 1 raw — shipped UWT v0.6.4).
- **Spec:** [`SPEC-UWT.md`](../../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../../CHANGELOG-UWT.md)
- **Registry entries affected:** all `path=t12` concepts targeting `T-12 Analysis`.
- **Substrate version mapped against:** v0.2.14 (Description_Map re-map will bump the substrate stream).

## Notes for Cowork

- This is a **major** income restructure — inserting ~16 rows shifts the labor /
  non-labor / Section I/J blocks down. Do it in Excel so formula refs follow.
- Preserve the col-N total + B–M monthly grid pattern and cols O/P/Q on every
  new income row (the writer mirrors col-N formulas across B–M and pastes line
  items; it expects the same column geometry as v5).
- Do **not** round-trip through openpyxl / Sheets / LibreOffice (dynamic-array +
  `_xludf` prefix hazards).

## Pre-work verified 2026-05-28 (parallel chat — turnkey facts for the absorption)

A parallel session verified the two Claude-Code engine/substrate checklist
items against the Homestead fixture so the absorption applies them with no
re-investigation. Neither was executed in parallel (both touch files the v6
absorption rewrites — `uw_output_model.py` / `dashboard_model.py` / `registry.json`
— so they land atomically with v6 to avoid an engine-vs-template mismatch).

### `opex_auto_expense` — the $6,061 NOI gap is exactly Auto Expense

- **Confirmed:** on Homestead the `Auto Expense` Description_Map label sums to
  **$6,061.32** — penny-exact to the standardized-vs-as-reported NOI gap
  ($1,417,385 − $1,411,324). The v0.6.4 changelog's "bad-debt-as-revenue-contra"
  attribution was imprecise; the gap is **Auto Expense dropped from the opex total**.
- **Root cause:** `Auto Expense` is **absent from `_LABELS_NON_LABOR`** in
  `dashboard_model.py` (only `Auto insurance` is present). The label aggregates
  correctly but never reaches `opex_nonlabor_total` → falls out of EBITDARM.
- **Fix (lands with v6 — changes NOI by $6,061, re-baseline tests):** add
  `"Auto Expense"` to `_LABELS_NON_LABOR`. Drops EBITDARM/EBITDAR/EBITDA by
  $6,061 on every property; standardized NOI then ties to as-reported
  $1,411,324. **Test impact:** `tests/test_uw_output_model.py` + writer tests
  assert the old EBITDA $1,417,385 / EBITDARM $1,767,483 — bump down $6,061 each.
- The engine already computes `Base rent — IL/AL/MC` and `LOC revenue — IL/AL/MC`
  as intermediates (summed for EGI in `compute_uw_output_values`) — exposing
  `base_rent_il/al/mc`, `loc_il/al/mc` + the 5 ancillary income keys is purely
  additive re-exposure of existing label sums.

### 2nd Person Revenue Description_Map re-map — exact rows + zero Homestead impact

- **Exact rows** in `ALF_Financial_Analyzer_Only.xlsx` → `Description_Map`
  (col A = description, col B = label):
  - **r400** `Second Persons Revenue | Assisted Living` — currently `Base rent — AL` → `2nd Person Revenue`
  - **r401** `Second Persons Revenue | Independent Living` — currently `Base rent — IL` → `2nd Person Revenue`
  - **r402** `Second Persons Revenue | Memory Care` — currently `Base rent — MC` → `2nd Person Revenue`
- **Open question (r127):** `Second Person Fee` — currently `Base rent — IL`. A
  *fee* description, distinct from the three "...Revenue | care" rows the brief
  names. Recommend leaving it unless the operator confirms it's recurring
  2nd-person revenue. **Decision needed.**
- **Zero Homestead impact confirmed:** all three `Second Persons Revenue | care`
  descriptions sum to **$0** on Homestead (no GL lines), so Base Rent totals
  don't move and `2nd Person Revenue` stays $0. EGI unchanged (pure
  reallocation). The current template's N67 row populates immediately for any
  property that *does* carry 2nd-person GL lines.
- Substrate migration (Description_Map content change) → bump the substrate
  stream (v0.2.14 → v0.2.15) via `migrate_to_v0215.py` + verify + idempotency,
  applied to the bundled Analyzer.
