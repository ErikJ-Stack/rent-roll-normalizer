# Changelog — Rent Roll Normalizer

All notable changes to the Rent Roll Normalizer.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a chat, add an entry here in the same commit.

---

## [1.12.0] — 2026-05-06

### Summary

UI rearrangement, bundled-Analyzer default, override expander, T12 status panel bug fix. **No behavioral changes** to RR parsing, T12 parsing, or any writer module — `app.py` is the only file touched (plus a `git mv` rename of `CHANGELOG.md` / `SPEC.md` for symmetry with the T12 docs).

### Added

- **Bundled Analyzer by default.** The repo's `ALF_Financial_Analyzer_Only.xlsx` is loaded silently as the destination workbook on every run. Users no longer need to upload an Analyzer for the standard flow — single-click rent roll → populated Analyzer download. The bundled file is the canonical source of `Description_Map` for UNMATCHED matching during T12 parsing.
- **Override path.** New "Advanced — override Analyzer template" expander at the bottom of the sidebar (collapsed by default). Uploading a custom Analyzer here overrides the bundled file for the session only — uploads do not modify the bundled file. Use cases: adding new data to a populated Analyzer from a prior deal, working with a v0.1.4 (or earlier) substrate Analyzer that hasn't been migrated yet, or testing a candidate substrate edit before promoting it.
- **Substrate version detection.** New `_detect_substrate_version()` helper reads the loaded Analyzer's `Description_Map` and reports `v0.1.5`, `v0.1.4`, or `pre-v0.1.4` based on canonical Label markers (`2nd Person Revenue` for v0.1.5; `Auto Expense` + `Lease / ground lease` for v0.1.4). Surfaced in the empty-state info banner, in the post-process header caption, and in `Run_Info` metadata. Display-only — never gates functionality.
- **Analyzer source label** in run metadata: `bundled (repo)` or `uploaded: <filename>`, alongside the detected substrate version. Helps audit which Analyzer was used after the fact.

### Changed

- **Sidebar reorganization.** Sections in order: `Inputs` (Rent Roll → Period Date → Raw T12), `Property Defaults` (Care Type), `Optional` (Mapping workbook), `Output` (Sheet name), and the Advanced expander at the bottom. The previous "Analyzer integration (optional)" section header is removed; Raw T12 sits alongside the rent roll and period-date as a peer optional input.
- **T12 parsing no longer requires uploaded Analyzer.** Previous logic gated T12 parsing on having both a Raw T12 AND an uploaded Analyzer in the sidebar, because `Description_Map` was needed for UNMATCHED detection. Now that the bundled Analyzer is always available, the gate is just "Raw T12 uploaded." Removed the explanatory "Raw T12 uploaded, but no Analyzer uploaded" branch from the T12 status panel.
- **Combined download flow.** Now produces a populated Analyzer from rent roll alone (no T12 required). When T12 is also uploaded and resolved, both data sets are baked in. Output filename adapts: `Analyzer with <rr_stem> <date>.xlsx` for RR-only, `Analyzer with <rr_stem> + <t12_stem> <date>.xlsx` for combined.

### Fixed

- **T12 status panel: dead-display bug.** Previous layout was 4 columns (`ta`, `tb`, `tc`, `td`) but had two `tc.metric()` calls — "Period (first month)" and "Period (last month)" — the second overwrote the first, so first-month never displayed. Layout is now 5 columns with each metric in its own column. All five display.

### Versions

- `APP_VERSION` / `RR_VERSION`: `1.11.0` → `1.12.0`
- `T12_VERSION`: `0.1.1` (unchanged)
- Bundled Analyzer substrate: v0.1.5 (unchanged from prior commit `18f55bc`)

### Files changed

- `app.py` — UI rearrangement, bundled-default loading, override expander, version bump, bug fix
- `CHANGELOG.md` → `CHANGELOG-RR.md` (rename via `git mv` for symmetry with `CHANGELOG-T12.md`)
- `SPEC.md` → `SPEC-RR.md` (rename via `git mv` for symmetry with `SPEC-T12.md`)
- `SPEC-RR.md` — current-version line, file inventory, Analyzer-source section, T12-cross-reference, doc-rename history note, versioning convention guidance
- This entry added

### Maintenance note

Editing the bundled `ALF_Financial_Analyzer_Only.xlsx` (cosmetic formatting, column widths, conditional formatting) is now a normal git workflow:

1. Edit the file in Excel
2. `git add ALF_Financial_Analyzer_Only.xlsx`
3. `git commit -m "Analyzer: <describe edit>"`
4. `git push`

Streamlit Cloud auto-redeploys; users pick up the new bundled file on next session. **Do not edit cell formulas, named ranges, helper col `T12_Calc!N`, sheet structure, or `Description_Map` rows 5-315 (canonical 55-Label vocabulary) without bumping the substrate version and shipping a migration script** — see `CHANGELOG-T12.md` `[Substrate template v0.1.5]` for the pattern.

---

## [T12 Normalizer cross-reference] — 2026-05-01 to 2026-05-04

The T12 Normalizer (Track 2) is an independent version stream with its own changelog at `CHANGELOG-T12.md`. The following T12-stream releases landed in this repo during the v1.10.0–v1.12.0 timeframe and affected `app.py` integration but are NOT logged in detail here:

- **T12 v0.1.0** (2026-05-01, commit `ae03d61`) — Parser (`t12_normalizer.py`), writer (`t12_normalizer_writer.py`), and `app.py` integration (Raw T12 uploader, UNMATCHED matcher form, combined Analyzer download). See `CHANGELOG-T12.md` `[0.1.0]`.
- **T12 v0.1.1** (2026-05-02, commit `f92717a`) — Yardi extractor patch: capture banner-style expenses (notably Salem's $131,579.65 Management Fees row that v0.1.0 silently dropped). See `CHANGELOG-T12.md` `[0.1.1]`.
- **Substrate template v0.1.4** (2026-05-02, commits `272e876`, `13c9736`, `612c2ac`) — Master Analyzer migrated to v0.1.4 substrate. See `CHANGELOG-T12.md` `[Substrate template v0.1.4]` and `[Master Analyzer migration — applied 2026-05-02]`.
- **Substrate template v0.1.5** (2026-05-04, commit `18f55bc`) — Added `2nd Person Revenue` Label. Per-bed base rate calculations now stay clean. See `CHANGELOG-T12.md` `[Substrate template v0.1.5]`.

### Why this cross-reference exists

`CHANGELOG-RR.md` is the source of truth for `app.py` releases (RR parsing, RR writer, RR-side UI). `CHANGELOG-T12.md` is the source of truth for T12 parser/writer/substrate changes. The two streams are independent (per `SPEC-T12.md` "How the version stream relates to Track 1"). However, T12 work that touches `app.py` shows up in both `git log app.py` and `CHANGELOG-T12.md` — this can be confusing when reading the RR changelog and seeing a gap between v1.11.0 and v1.12.0. This cross-reference closes the gap by acknowledging the parallel T12 work without duplicating its detail.

---

## [1.11.0] — 2026-05-01

### Summary
Analyzer rename. UI label and SPEC updates only. No behavioral change. Confirmed end-to-end working on prior release: Salem RR + `ALF_Financial_Analyzer_Only.xlsx` produced identical output to the prior T12-named workflow (writer is target-agnostic).

### Changed
- `app.py` — Sidebar section header renamed `T12 integration (optional)` → `Analyzer integration (optional)`.
- `app.py` — Uploader label renamed `T12 Intake Template (.xlsx)` → `ALF Financial Analyzer (.xlsx)`. Help tooltip updated to reference Analyzer terminology and call out that the legacy `ALF_T12_Intake_Final.xlsx` template is still compatible (same `Rent Roll Input!A7+` schema).
- `app.py` — Period Date label `Rent Roll Period Date (for T12 col S)` → `Rent Roll Period Date (for Analyzer col S)` and corresponding help text.
- `app.py` — Download button section header `T12 with Rent Roll` → `Analyzer with Rent Roll`. Disabled-state caption / button text and the three error-message strings (`T12 capacity exceeded`, `T12 error`, `Could not populate T12`) all retitled to `Analyzer ...`.
- `SPEC-RR.md` — Section "T12 file expected structure" retitled to "Analyzer / T12 destination workbook structure". Calls out `ALF_Financial_Analyzer_Only.xlsx` as the canonical destination and notes legacy `ALF_T12_Intake_Final.xlsx` compatibility / deprecation.
- `SPEC-RR.md` — Added "Module naming history" note under File inventory: `t12_writer.py` / `t12_translator.py` are named historically; they now write into the Analyzer's `Rent Roll Input` sheet. A future cross-cutting commit may rename to `rr_to_analyzer_*.py`. Same note already exists in `SPEC-T12.md`.
- `SPEC-RR.md` — User-facing language throughout updated: "T12" → "Analyzer" in Stage 3, vocabulary translation table title, output filename pattern, "How the analyst uses the app", and known issues. The literal string "T12" is preserved in the T12 Normalizer roadmap section (that work still concerns actual T12 GL data) and in module filenames.
- `app.py` — `APP_VERSION` 1.9.0 → 1.11.0; `APP_LAST_UPDATED` → 2026-05-01.

### Unchanged (intentional)
- `t12_translator.py`, `t12_writer.py` — module filenames retained per "future cross-cutting rename" note. No code changes.
- `key="t12_uploader"`, `key="dl_t12"`, `key="dl_t12_disabled"` — Streamlit widget keys preserved to avoid invalidating any in-flight session state. Internal identifiers; not user-visible.
- All writer logic. The destination-workbook contract (`Rent Roll Input!A7+`, cols T-U formulas, max 600 rows) is identical between `ALF_Financial_Analyzer_Only.xlsx` and the legacy `ALF_T12_Intake_Final.xlsx`, so the same writer produces the same output for both.
- Output filename pattern (`<destination_stem> with <rr_stem> YYYY-MM-DD.xlsx`) — works correctly with either Analyzer or legacy T12 stems.
- README.md — out of scope per task boundaries. Will be refreshed in a later sweep.

### Verified
- User confirmed end-to-end on prior release: `ALF_Financial_Analyzer_Only.xlsx` uploaded into the (then-named) "T12 Intake Template" slot against the Salem rent roll, all 50 beds populated correctly into `Rent Roll Input`, `Rent Roll Recon` tab numbers spot-checked. This commit is purely cosmetic — same inputs should yield byte-identical output.
- Post-deploy verification (analyst): screenshot the live app sidebar showing the new label, then re-run Salem RR + Analyzer template and confirm output matches.

### Note on prior release state
- The deployed `app.py` was running `APP_VERSION = "1.9.0"` despite v1.10.0 docs being published — the v1.10.0 code/version-bump push didn't fully land. This commit jumps the deployed version pill from 1.9.0 to 1.11.0. The v1.10.0 zero-vs-blank behavior in `normalizer.py` should be re-verified separately on prod after this deploy; if the live app still shows `0` instead of blanks for empty charge cells, that's a v1.10.0 regression to address in a follow-up commit.

---

## [1.10.0] — 2026-04-30

### Summary
**All numeric output columns** (rates AND per-bed dollar charges) now output **blank** instead of `0` when there's no value. Stops zero-fills from inflating `COUNT()` / `COUNTIF()` in Excel. Sums and KPIs all unchanged.

### Changed
- `normalizer.py` — new `_blank_if_zero(v)` helper returns `None` for numeric values within 1e-9 of zero, else passes through. Applied to all numeric output fields at record-build time.
- `reports.py` — `build_summary` updated: `Avg Market Rate (all beds)` and `Avg Actual Rate (all beds)` now use `fillna(0).mean()` to preserve "average across the full denominator" semantics. `Avg Rate Gap` derived from those two so it's also denominator-correct. `(occupied)` averages still use plain `.mean()` (skip blanks) — that's the right behavior because an occupied bed with a blank rate is a data gap, not a $0 rate.
- `reports.py` — `build_exceptions` now coerces NaN to 0 via a local `_num()` helper before threshold checks. Without this, `NaN <= 0` is False and would silently mask occupied-with-blank-rate data gaps.

### Affected output columns (zero → blank)
**Pricing:**
- `Market Rate`
- `Actual Rate`
- `Rate Gap`
- `Total Monthly Revenue`

**Charges (per-bed):**
- `Concession $`
- `Care Level $`
- `Med Mgmt $`
- `Pharmacy $`
- `Other LOC $`
- `Total LOC $`

### Unchanged
- All categorical fields (Status, Apt Type, Care Type, Care Level, Payer Type, etc.)
- `Potential Occupancy` — integer count where 0 would be a real data error worth surfacing
- `Sq Ft` — already blank when source lacks it (string `""`)
- All RR_Summary totals (sum operations treat NaN as 0)
- All RR_By_Type aggregations (per-group `.mean()` correctly skips blanks)

### Verified
- **Salem (round-trip)**: 50 rows, totals identical to v1.9.0. Excel COUNT() now: Concession=7, Care Level=44 (was always 50/50). Avg Market (all beds) = $4,050.82, Avg Actual (all beds) = $4,000.28, Avg Rate Gap = $50.54 — preserves prior denominator semantics.
- **Briar Glen (raw)**: 79 rows. Sums unchanged: $234,360 Care Level $, $-14,132 Concession $, $250,978 TMR. Excel COUNT() now: Actual Rate=34 (was 79), Concession=16 (was 79), Care Level=44 (was 79), Med Mgmt=0 (was 79), Pharmacy=0 (was 79).
- **Briar Glen Avg Actual (occupied) = $864.71** is correct, not a regression — Briar Glen's billing structure puts ~$880 in Accommodation Service and ~$5K in Care Charges per resident. Total monthly bill (Actual + Care Level) averages ~$5,800/occ which matches MC market rates.
- Vacant beds now visually distinct: all dollar columns blank instead of `0` / `-`.

### Note for downstream consumers
- Analyzer paste: blank Condensed_RR cells write as truly empty into Analyzer cols D-S. Analyzer SUM() formulas continue to total correctly (empty = 0). Analyzer COUNT() now returns accurate populated-cell counts.
- Filtering: to find "occupied beds" use `Status == "Occupied"` (categorical), not `Actual Rate > 0` (which would now exclude legitimate zero-rate edge cases).

---

## [1.9.0] — 2026-04-30

### Summary
Concession detection extended to broker-format columns + fixed a sign bug in Total Monthly Revenue. Briar Glen `Recurring Discounts` and `One-Time Incentives` now flow into `Concession $` instead of being silently dropped. Salem TMR was previously inflated by 2× the concession amount on rows with concessions; now correct.

### Changed
- `normalizer.py` — `detect_concession_cols` now returns a **list** of monthly columns (was Optional[str]). Multiple concession-equivalent columns on a single rent roll are summed into `Concession $`.
- `normalizer.py` — new `_CONCESSION_PATTERNS` regex set recognizes `Concession`, `Recurring Discount(s)`, `One-Time Incentive(s)`, and generic `Discount (month)` headers as concession sources.
- `normalizer.py` — care-group detector now explicitly skips columns matching `_CONCESSION_PATTERNS` so concessions can never be double-counted as a care bucket.
- `app.py` — `conc_monthly_col` → `conc_monthly_cols` rename.

### Fixed
- **Total Monthly Revenue sign bug.** Concessions are stored as negative source values (e.g. −500). Previous formula `actual + LOC - conc_amt` subtracted a negative, inflating revenue by 2× the concession on those rows. Changed to `actual + LOC + conc_amt`. Affected 7 rows on Salem (TMR was overstated by ~$2,841 across those rows).

### Sign convention (decision recorded)
- `Concession $` is stored **negative** in output (preserves source convention; Analyzer column I sees the value as-is). The math now correctly applies a discount as a reduction.

### Verified
- Salem regression (raw): 50 rows, $28,125.81 Care Level $, $36,675 Total LOC $ — unchanged from v1.8.0
- Salem TMR fix: all 7 concession rows now have TMR = actual + LOC + concession (math validated row-by-row)
- Briar Glen (raw): **79 rows, $234,360.00 Care Level $ — unchanged**. **NEW: $-14,132.00 Concessions across 16 rows** (15 from Recurring Discounts at $-13,732, 1 from One-Time Incentives at $-400)
- Briar Glen status mix unchanged: 44 Occupied / 35 Vacant; 79 Care Type=MC

### Known limitation (updated)
- v1.8.0 listed `Recurring Discounts` and `One-Time Incentives` as out-of-scope. **This is no longer true** — both are now mapped. `Medicaid Charges` and `Other Charges` remain unmapped (still flow into `Other LOC $` via auto-catch).

### Migration note
- Any prior outputs with concession rows had inflated `Total Monthly Revenue` by 2× the concession amount on those specific rows. Re-run those files for accurate TMR. Concession $, Actual Rate, and Care Level $ values were all correct in prior runs — only TMR was affected.

---

## [1.8.0] — 2026-04-30

### Summary
Broker rent roll support: pre-cleaner module + smart sheet selection + self-contained-row parsing + standalone care bucket detection. Verified end-to-end on Briar Glen (Vitality Senior Living format) without breaking Salem (Oaks format). Also: column rename `AL Care Level $` → `Care Level $` for consistency.

### Added
- `pre_cleaner.py` — strips totals/banners/legend/blank padding from raw DataFrame before header detection. Drops 92 of 181 rows on Briar Glen, 0 on Salem (no false positives).
- Smart multi-sheet selection: when no sheet name given, scores all sheets by row × col + header signal hits and picks the best. Handles Briar Glen's `Document map` + data sheet + legend structure.
- Self-contained row classification (`_row_is_self_contained_unit`): a row with apartment ID AND resident name on same row is treated as both parent context refresh AND bed record emission. Handles Briar Glen single-bed unit format.
- Standalone care bucket detection in `detect_care_groups`: columns whose name itself is the bucket (e.g., "Care Charges") with no monthly suffix are now recognized as monthly care columns. Heuristic: must contain care-related keyword to qualify.
- Bed status fallback: if no Bed Status column exists, infer from resident name. `*Vacant` / `Vacant` / `(vacant)` markers are detected and the marker is stripped from resident name.
- Privacy Level → Bed letter translation: PRI/Single → no letter; SPA/DAS/QAS → A; SPB/DBS/QBS → B.
- Single-Unit-column format support: when there's no separate Apartment column, Unit is treated as the room number directly. Salem's two-column format still works.

### Changed
- **Renamed `AL Care Level $` column → `Care Level $`** throughout codebase: app.py, mappings.py, normalizer.py, reports.py, t12_writer.py, writer.py, README.md. Analyzer paste is positional so this rename is purely cosmetic on rent roll output.
- `mappings.py` `DEFAULT_CARE_TYPE`: added entries for Briar Glen-style codes (DM, DU7, LTC, Special Care, Long-Term Care, Alzheimer's). Memory Care patterns ordered before AL to ensure correct precedence.
- `mappings.py` `DEFAULT_APT_TYPE`: added Briar Glen-style codes (DLXSTD, STD, 1BED, 2BED, S SUI, D SUI).
- `mappings.py` `DEFAULT_CARE_BUCKETS`: added "Care Charges" / "Care Services" patterns.
- Field patterns (`FIELD_PATTERNS`) loosened to accept Briar Glen-style headers: trailing-space "Unit ", multi-word "Resident Move In Date", "Privacy Level", "Unit Capacity", "Unit Sqft", etc.

### Verified
- Salem regression: 50 rows, $28,125.81 Care Level $, $36,675 Total LOC $ — identical to v1.7.0
- Briar Glen: 79 rows (71 units × bed multiplicity for 8 shared apts), $234,360.00 Care Level $ matching Briar Glen's own reported totals row exactly. 44 Occupied / 35 Vacant. All 79 rows correctly tagged Care Type=MC via the Care Level raw fallback (DM code). All shared 2-bed units correctly labeled `1BR - Shared`.

### Known limitation
- Briar Glen's `Recurring Discounts`, `Medicaid Charges`, `One-Time Incentives`, `Other Charges` columns are currently NOT mapped — only `Care Charges` flows into `Care Level $`. Per user decision: those negative/special line items are out of scope for now.

---

## [1.7.0] — 2026-04-29

### Summary
Analyzer integration shipped. The app now optionally produces a second output: the user's Analyzer template populated with the rent roll data on the `Rent Roll Input` sheet starting at row 7. (Originally shipped with the legacy T12 Intake template as the destination; same writer code now also accepts `ALF_Financial_Analyzer_Only.xlsx` per v1.11.0 rename.)

### Added
- `t12_translator.py` — converts Condensed_RR vocabulary to the Analyzer's data validation vocabulary
- `t12_writer.py` — loads user's Analyzer, writes A:S row 7+, preserves cols T-U formulas and all other tabs/formatting/validations
- `period_date.py` — extracts period date from rent roll filename across 6 patterns

### Changed
- `app.py` — added Analyzer upload slot, period date picker (auto-fills from filename), two-button download section

### Verified
- Salem: 50 rows written to Analyzer rows 7-56, period date `2026-01-31` on every row, zero data validation violations, formulas in cols T-U intact at rows 7/100/606, all 11 sheets preserved.

---

## [1.6.0] — 2026-04-29

### Summary
Added version badge and last-updated date to top-right of UI so users can verify which build is running.

### Added
- Version pill (charcoal `v1.x.x`) and "Updated YYYY-MM-DD" text in title row
- `APP_LAST_UPDATED` constant alongside `APP_VERSION`
- Both surface in Run_Info tab of every output workbook

---

## [1.5.0] — 2026-04-29

### Summary
Care Type fallback chain and Shared apartment detection.

### Changed
- Care Type detection now falls back through Building code → Care Level raw text → Property Default before flagging as missing
- Second pass after row parsing: rooms with 2+ beds get ` - Shared` appended to Apt Type on every row
- `Care Type Source` column added to full Normalized_Beds tab showing provenance

### Verified
- Salem: 50 × Care Type = AL (sourced from Building), shared rooms correctly show `Studio - Shared` / `1BR - Shared` / `2BR - Shared`

---

## [1.4.0] — 2026-04-28

### Summary
Care Level "Level 6+" bucket replaces the cap-at-Level-5 with exception-flag pattern.

### Changed
- Level 6, 7, 8+ now all map to `Level 6+` instead of being capped at `Level 5`
- Removed cap-and-flag exception infrastructure
- Added 6th color to gradient: Level 6+ darkest navy with bold white text

---

## [1.3.0] — 2026-04-27

### Summary
Full Excel formatting polish on output workbook. Charcoal + white theme.

### Added
- Comprehensive formatting: charcoal headers, alternating row banding, color-coded Status/Care Level/Care Type, currency formatting, autofilters, frozen panes, print-ready setup

---

## [1.2.0] — 2026-04-26

### Summary
Property Care Type default option for single-care-setting buildings.

### Added
- Sidebar dropdown for property-level default
- Banner in UI confirms when default is active

---

## [1.1.0] — 2026-04-26

### Summary
Care Type (IL/AL/MC) and Care Level (Level 1-5) become two distinct fields.

### Changed
- `Care Type` now means setting (IL/AL/MC); `Care Level` means acuity (Level 1-5)
- Output column `AL Care Level` renamed to `Care Level`

### Added
- Unit # composite (`{Room}-{Bed}`)

---

## [1.0.0] — 2026-04-24

### Summary
Initial deploy. Streamlit app reads any senior-housing rent roll, normalizes to one row per bed, produces 6-tab Excel output.

### Initial decisions
- Normalize to bed-level (one row per bed, vacant beds preserved)
- Header auto-detection via signal scoring of first 20 rows
- Parent-apartment / child-bed parsing
- Care bucket auto-grouping with Other LOC $ catch-all
- Sq Ft left blank when not in source (no fabrication)
- Output filename: `<source_stem> Normalized YYYY-MM-DD.xlsx`
