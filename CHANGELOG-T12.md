# Changelog — T12 Normalizer

All notable changes to the T12 Normalizer (Track 2). Independent version stream from the Rent Roll Normalizer (Track 1, currently v1.17.0). This changelog covers T12 work only — see `CHANGELOG-RR.md` for RR releases.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a T12-related chat, add an entry here in the same commit.

---

## [Substrate template v0.1.14] — 2026-05-14

### Summary

Three small Track 3 patches surfaced in v0.1.10 carry-forwards, bundled into a single substrate increment per UW-BACKLOG prioritization. Pure substrate change — no RR/T12 code changes.

**Closes [UW-BACKLOG BL-0004, BL-0005, BL-0006](UW-BACKLOG.md).**

### What changed (migrate_to_v0114.py)

- **A. BL-0004 — T12 Analytics: 2P revenue reconciliation row** at rows 168-170:
  - Row 168: subsection title (merged A:G) — `RR ↔ T12 — 2nd Person Revenue Reconciliation`
  - Row 169: column headers (Metric / RR projection / T12 actual / Variance % / Note)
  - Row 170: data row — `=SUM('Rent Roll Input'!$V$7:$V$606)*12` (RR annual projection) vs. `=IFERROR('T12 Raw Data'!$R$15,0)` (T12 actual annual). Variance % + conditional note: ⚠ fires at \|variance\| > 10%; ✓ "reconciles within 10% of T12" otherwise.

  Placement: chose rows 168-170 (after the existing KPI Dashboard color key at row 166) instead of slotting into rows 42-44 because of pre-existing `A43:H43` and `A45:H45` horizontal merges in the GPR Waterfall area. Appending past row 166 is cleaner than disrupting merge ranges; the new block stands alone as an addendum and doesn't risk breaking adjacent formulas.

- **B. BL-0005 — Workbook Health: total AR / Balance aggregation** at rows 43-45:
  - Row 43: `G9 · Total outstanding AR (Σ Rent Roll Input!X)` — `=SUM('Rent Roll Input'!$X$7:$X$606)`
  - Row 44: `G10 · AR ÷ monthly EGI (collection-velocity indicator)` — `=IFERROR(B43/('Monthly Trending'!$N$21/12),0)`
  - Row 45: conditional note (merged A:D) — ⚠ fires when `AR > 5% of monthly EGI`; ✓ "within 5% of monthly EGI" otherwise.

  Placement: directly after the existing `G8 · Last opened (volatile)` row at 42. The new rows extend the Diagnostics section without disturbing it.

- **C. BL-0006 — Rent Roll Recon Section K: Avg Actual PSF column** at col I rows 87-93:
  - I87: header — `Avg Actual\nPSF`
  - I88-I92: per-unit-type AVERAGEIFS on `Rent Roll Input!$AA$7:$AA$606` (Actual PSF, captured at v1.16.0). Same filter pattern as col D (Avg Rate) — period selector + occupied + IL care type + unit type.
  - I93: Total IL row — same formula without the unit-type filter.

  Placement: extends the existing IL unit-type table (cols A-H) with a new col I. Doesn't touch the dispersion rows below (rows 95-100). Source data already exists at `Rent Roll Input!AA` per substrate v0.1.10.

- **D. Stamp** `Cover!B8` and 13 `AZ4` anchors to `v0.1.14`.

### Idempotency

Gate (`is_already_v0114()`) checks BOTH the version stamp AND three sentinel cells (one per BL): T12 Analytics!A168 contains "Reconciliation", Workbook Health!A43 contains "G9", Rent Roll Recon!I87 contains "Actual" and "PSF". Re-runs on partial-state files safely re-apply.

### Verification

13-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, BL-0004 title row + RR projection formula + T12 actual formula, BL-0005 G9 label + AR sum formula + G10 label, BL-0006 I87 header + I88 Studio formula + I93 Total IL formula, plus Section K unit-type table intact + Section L MC structure intact (regression guards).

Migration verified end-to-end on:
- **Bundled v0.1.13 Analyzer** → v0.1.14 cleanly. File size 193,915 → 194,732 bytes (+817 bytes — small, consistent with ~13 new functional cells + 14 stamps).
- **User's populated Homestead workbook** chained v0.1.10 → v0.1.12 → v0.1.13 → v0.1.14 — all 13 checks green at each step.
- **Idempotency**: re-running on a v0.1.14 file exits cleanly with `"Workbook is already at v0.1.14. No-op (will re-save)."`

### What's left in UW-BACKLOG.md after this release

- `BL-0001` (substrate v0.2.0): finer ancillary T12 Labels (`Meal Income`, `Housekeeping Income`, etc.)
- `BL-0002` (substrate v0.2.0): V5 chart fallback for broker-format rent rolls with no acuity
- `BL-0008` (RR, whenever bundled): substrate version detection in `app.py`
- `BL-0009` (substrate v0.2.0 flagship): Branch 2 Handoff readiness (UW Export, pre-export gate, metadata header)
- `BL-0010` (refactor, whenever): `t12_translator.py` → `analyzer_rr_translator.py` rename

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.14
- `tools/migration/migrate_to_v0114.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — substrate version reference
- `UW-BACKLOG.md` — `BL-0004` / `BL-0005` / `BL-0006` moved from Pending to Shipped
- `CHANGELOG-T12.md` — this entry

---

## [Substrate template v0.1.13] — 2026-05-13

### Summary

Track 3 companion to RR v1.17.0 (UW-BACKLOG BL-0003 — RR Input expansion). Two coordinated changes:

1. **Rent Roll Input gets 5 new columns at AC-AG** to receive the per-fee ancillary breakdown produced by the v1.17.0 parser: `Meal Plan $` / `Scooter Fee $` / `Housekeeping $` / `Laundry $` / `Pet $`. Other LOC $ (col O) remains as the catchall. Total LOC $ formula at T7:T606 extended to include AC-AG so the per-resident total is unchanged — only the distribution across columns changes.

2. **Section M (Rent Roll Recon rows 121-167) gets a 5th M1 column "RR Input Col"** plus a complete M2 / M4 rewrite using universal `INDIRECT` formulas off that column. Previously only Second Person Fee had real per-fee capture-rate / implied-rate formulas; now Meal Delivery / Motorized Scooter / Housekeeping / Laundry compute too because they have direct RR Input column matches. M2 eligibility unified to all-occupied beds in the selected period (was: occupied IL only for SP — per user spec, couples can occur in any care type).

### What changed (migrate_to_v0113.py)

- **A. RRI new column headers** at row 4 cols AC-AG (5 cells styled to match the existing navy header).
- **B. Total LOC $ formula extension** at T7:T606:
  ```
  Old: =IFERROR(L{r}+M{r}+N{r}+O{r},0)
  New: =IFERROR(L{r}+M{r}+N{r}+O{r}+IFERROR(AC{r},0)+IFERROR(AD{r},0)+
                 IFERROR(AE{r},0)+IFERROR(AF{r},0)+IFERROR(AG{r},0),0)
  ```
  Pattern-matched on the exact prior shape so customized formulas (if any) are left intact.
- **C1. Section M1 "RR Input Col" header** at E122 + pre-populated default mappings for the 7 default fees:
  - Community Fee → `""` (event-based; no per-fee RR col)
  - Elective Transfer Fee → `""` (rare event; no per-fee RR col)
  - Meal Delivery → `AC`
  - Motorized Scooter Fee → `AD`
  - Second Person Fee → `V` (existing v0.1.10 column)
  - Housekeeping → `AE`
  - Laundry → `AF`
- **C2. Section M2 universal formulas** (rows 135-143):
  - Eligible #: `COUNTIFS(occupied across all care types, period selector)` — same for all 9 rows
  - Capturing #: `IF(E{m1_row}="", "—", COUNTIF(INDIRECT("'Rent Roll Input'!"&E{m1_row}&"7:606"), ">0"))`
  - Capture %: `IFERROR(C/B, "")`
  - Note: dynamic — `"✓ Direct RR match (col X)"` when E set, `"No per-fee RR column"` otherwise
- **C3. Section M4 universal formulas** (rows 159-167):
  - T12 $/mo from M3 (unchanged behavior)
  - RR # capturing pulled from M2
  - Implied $/resident: only when E set AND counts numeric
  - Variance % vs. M1 schedule
  - Conditional note: `"✓ Implied rate within 5% of schedule"` / `"⚠ Implied rate differs by X%"` / `"Falls into M5 Misc."` based on E-col + variance threshold
- **D. Stamp** `Cover!B8` and 13 `AZ4` anchors to `v0.1.13`.

Section M3 / M5 unchanged — the v0.1.12 formulas were already forward-compatible. M5's SUMPRODUCT for "fees attributed to OCR via M2 capture" begins producing real deductions automatically once Meal/Scooter/HK/Laundry rows have populated M2 capture #'s.

### Idempotency

Gate (`is_already_v0113()`) checks BOTH the version stamp AND that `Rent Roll Input!AC4` reads `Meal Plan` (verifying the new headers landed). Re-runs on a partial-state file safely re-apply.

### Verification

11-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, 5 new RRI headers present, Total LOC formula extended in 600 rows, M1 col E header / 5 default mappings, M2 INDIRECT formula present, M2 eligibility unified (no IL filter), M4 implied-rate formula generic, Sections K and L intact.

End-to-end migration verified on:
- **Bundled v0.1.12 Analyzer** → v0.1.13 cleanly. File size 183,103 → 193,915 bytes (+10,812 bytes consistent with 5 new header cells + 600 row × 1 col formula extension + 9 × 4 cells of M1/M2/M4 rewrites).
- **User's populated Homestead workbook** chained through v0.1.10 → v0.1.12 → v0.1.13 — all 11 checks green at each step.
- **Idempotency**: re-running on a v0.1.13 file exits cleanly with `"Workbook is already at v0.1.13. No-op (will re-save)."`

### Migration path for users

Workbooks at substrates older than v0.1.12 must chain through prior migrations in order. Each script handles one substrate version step:

```
python tools/migration/migrate_to_v0111.py file.xlsx file_v0111.xlsx
python tools/migration/migrate_to_v0112.py file_v0111.xlsx file_v0112.xlsx
python tools/migration/migrate_to_v0113.py file_v0112.xlsx file_v0113.xlsx
```

Or skip the chaining: re-run the live app to get a fresh download with v0.1.13 substrate.

### Out of scope (logged in UW-BACKLOG.md)

- **`BL-0001`** still pending: finer ancillary T12 Labels (`Meal Income`, `Housekeeping Income`, etc.) so Section M3 stops returning `(shared bucket)` notes. Substrate v0.2.0 vocabulary expansion.
- **`BL-0004` / `BL-0005` / `BL-0006`** still pending: small Track 3 patches surfaced by v0.1.10 (T12 Analytics 2P reconciliation row, Workbook Health AR aggregation, Section K PSF dispersion stats). Substrate v0.1.14 candidates.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.13
- `tools/migration/migrate_to_v0113.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — substrate version reference
- `UW-BACKLOG.md` — `BL-0003` moved to Shipped
- `CHANGELOG-T12.md` — this entry

(See [CHANGELOG-RR.md](CHANGELOG-RR.md) `[1.17.0]` for the Track 1 parser / writer / mapping changes that this substrate companions.)

---

## [Substrate template v0.1.12] — 2026-05-13

### Summary

Adds **Section M** (Operator Fee Schedule & Ancillary Revenue Reconciliation) to `Rent Roll Recon` rows 119-172. Captures the operator's published fee schedule as a structural part of the underwriting analysis and reconciles published rates against T12 actuals through the chain: schedule → RR-side capture (count + %) → T12 12-month actuals → implied per-resident rate → schedule fidelity %.

Five sub-sections:

- **M1 — Published schedule (analyst paste-in)**: 7 default fee rows (Community Fee / Elective Transfer / Meal Delivery / Motorized Scooter / Second Person / Housekeeping / Laundry) plus 2 blank rows for property-specific additions. Column D = T12 Label, validated against `DescMap_Label` named range.
- **M2 — RR-side capture (auto)**: for fees with a direct per-resident column on `Rent Roll Input`, count eligible vs. capturing residents and compute capture %. Today only Second Person Fee has a direct match (`Rent Roll Input!V`, added v0.1.10). Other 6 fees show `n/a (one-time)` or `falls into M5 (see UW-BACKLOG BL-0003)`.
- **M3 — T12 actuals (auto)**: VLOOKUP from the M1 T12 Label into `T12 Raw Data!R` (annual total). Shared-bucket detection: when multiple M1 fees map to the same Label (typical for `Other community revenue`), the 2nd+ occurrences display `(shared — see row N)` instead of duplicating the value.
- **M4 — Implied per-resident rate (T12 ÷ RR count vs. schedule)**: per user spec, divides T12 monthly $ by RR # capturing → implied per-resident rate → variance % vs. M1 schedule. Conditional note fires when |variance| > 5%. Only computable today for SP; others fall into M5.
- **M5 — Misc. Income (residual)**: T12 `Other community revenue` annual + monthly + per-fee attribution + residual + % of EGI. Conditional note fires when residual > 15% of EGI, pointing the analyst to UW-BACKLOG BL-0003.

### What changed (migrate_to_v0112.py)

- **A. Section M installation** on `Rent Roll Recon` at rows 119-172:
  - Section title (row 119), 5 subsection titles (M1 row 121, M2 row 133, M3 row 143, M4 row 153, M5 row 163)
  - M1: 9 paste-in rows × 4 cols (Fee Name / Published $ / Basis / T12 Label) with data validation on the Label column
  - M2: 9 auto-computed rows × 5 cols
  - M3: 9 auto-computed rows × 5 cols (VLOOKUP + shared-bucket detection)
  - M4: 9 auto-computed rows × 7 cols (implied rate + variance + conditional note)
  - M5: 5 metric rows + 1 conditional note row, anchored to `'Monthly Trending'!$N$21` (EGI annual)
- **B. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.12`.

### Idempotency

Gate (`is_already_v0112()`) checks BOTH the version stamp AND that `Rent Roll Recon!A119` already starts with `"M "` (the Section M title prefix). Re-runs on a partial-state file safely re-apply.

### Verification

10-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, Section M title in place, M1 subsection title, 7 default fees installed, M2 SP COUNTIF formula references `Rent Roll Input!V`, M3 first row VLOOKUP formula references `T12 Raw Data`, M4 SP variance formula references D column (implied rate), M5 residual formula references B column (computed delta), Sections K and L (rows 86-117) intact.

Migration verified end-to-end on:
- **Bundled v0.1.11 Analyzer** → migrates cleanly to v0.1.12, file size 180,003 → 183,103 bytes (+3,100 bytes, consistent with ~50 new rows of content)
- **User's populated Homestead workbook** (RR + T12 baked in) → same verification result; Section M installs cleanly alongside existing data

### Idempotency proven

Re-running the migration on an already-v0.1.12 file exits cleanly: `"Workbook is already at v0.1.12. No-op (will re-save)."` No double-installation, no formula corruption.

### Companion: UW-BACKLOG.md

This release introduces `UW-BACKLOG.md` at the repo root as the authoritative forward-looking list of underwriting workbook changes. Prior "Out of scope" / "Carry-forward" notes scattered across CHANGELOG-T12 and CHANGELOG-RR have been swept into 10 `BL-NNNN` entries. New items are added there; closed items move to the `Shipped` section but keep their IDs so cross-references remain stable.

The Section M work itself opens 4 new backlog items (BL-0001, BL-0003, BL-0004, BL-0007) — finer T12 Labels, RR Input expansion, T12 Analytics 2P reconciliation row, and the meal/scooter RR keyword widening. All are wired into Section M's conditional notes so the analyst sees them in-workbook when relevant.

### Out of scope (logged in UW-BACKLOG.md)

- **BL-0001**: Finer ancillary Labels in `Description_Map` (Meal Income, HK Income, Laundry Income, Scooter Fee Revenue, Transfer Fee Revenue). Substrate v0.2.0 territory — vocabulary expansion, not a patch.
- **BL-0003**: RR Input expansion for per-fee ancillary columns. Cross-cutting Track 1 + Track 3; ships as its own scoped PR.
- **BL-0004**: T12 Analytics 2P reconciliation row. Substrate v0.1.13 candidate.
- **BL-0007**: Meal / scooter / mobility / transport keyword additions in `_looks_care`. RR v1.16.2 patch candidate.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.12
- `tools/migration/migrate_to_v0112.py` — idempotent migration script
- `UW-BACKLOG.md` — **new file** at repo root; 10 initial entries swept from prior changelogs + this release
- `SPEC-T12.md` — current-version line bumped to v0.1.12; file inventory adds `migrate_to_v0112.py` row
- `SPEC-RR.md` — Track-versions inline line bumped (v0.1.11 → v0.1.12); Section M referenced in the Analyzer-source section
- `README.md` — versions table + migration script listing updated
- `CLAUDE.md` — substrate version bumped to v0.1.12; carry-forwards section condensed to point at UW-BACKLOG.md
- `CHANGELOG-T12.md` — this entry

---

## [Substrate template v0.1.11] — 2026-05-13

### Summary

Patch fix for a chart category-axis positioning bug introduced when the five `T12 Analytics` charts were added at substrate v0.1.8 (Branch 3 analytical coverage). All three axis-bearing charts (V1, V2, V4) had their category axis incorrectly positioned at `axPos="l"` (left) when it should be `axPos="b"` (bottom) for vertical column and line charts.

The bug visibly manifests on the V4 LineChart (T12 Revenue Trend): Excel can't reconcile two axes both claiming the left position and falls back to rendering the categories (month labels) as legend entries with no plot area. V1 (Occupancy stacked column) and V2 (Rate Dispersion clustered column) had the same bug technically but Excel tolerates BarChart axis ambiguity — they rendered correctly to the eye. This fix brings them to spec-compliance and removes the risk of stricter future Excel versions silently breaking them.

### What changed (migrate_to_v0111.py)

- **A. Chart category-axis position fix.** For each chart on `T12 Analytics` whose title matches V1 / V2 / V4, flip `x_axis.axPos` from `"l"` to `"b"`. The value axis (`y_axis.axPos`) is left at `"l"` — correct for vertical charts. V3 (Payer Mix doughnut) and V5 (AL Acuity Mix doughnut) have no axes and are skipped.
- **B. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.11`.

No new sheets, no new named ranges, no new formulas, no header changes. Three byte-level edits inside three chart XML files (l → b in `<catAx><axPos val="l"/>`) plus 14 cell stamps.

### Idempotency

Gate (`is_already_v0111()`) checks BOTH the version stamp AND that V4's `x_axis.axPos` already reads `"b"`. Re-runs on a partial-state file safely re-apply.

### Verification

6-check verification block: `Cover!B8` stamped, all 13 `AZ4` stamped, three target charts have catAx `"b"` (was `"l"`), valAx unmoved at `"l"`, V3 and V5 doughnuts still present (sanity).

Round-trip test against the v0.1.10 bundled Analyzer + the user-reported populated Homestead workbook: in both cases, all three target charts flip cleanly to `"b"`, the value axis stays at `"l"`, and the doughnut charts are untouched. File size delta on the bundled Analyzer: +10 bytes (3 axPos edits + 14 stamps) — confirms no other content was dropped or rewritten during the openpyxl save.

End-to-end smoke after applying the migration: parser pipeline produces a populated Analyzer whose `Description_Map` and formula sheets are unchanged from pre-migration. Re-opening the populated file in Excel renders V4 as a 12-point line chart with months on the X axis (was: empty plot + months as a vertical legend list).

### How this bug got introduced

When `migrate_to_v018.py` created the five charts at substrate v0.1.8, the chart construction code likely copied axis configuration from another chart type without adjusting `axPos`. The bug only surfaced when V4 (the LineChart) was actually populated with monthly trend data — V1 and V2 happened to render fine despite being equally wrong, so the issue stayed latent until a Homestead-with-T12 run hit V4 with real data.

### Out of scope (logged for v0.1.12+)

- The carry-forwards from v0.1.10 still stand: `Rent Roll Recon` section K PSF stats, T12 Analytics 2P reconciliation row, `Workbook Health` AR aggregation.
- V5's empty rendering on broker-format rent rolls (Homestead has no per-bed acuity tiers, so SUMIFS for Basic/Level 2-7 all return $0). Either accept that V5 is meaningful only when source has acuity, or rework V5 to fall back to "Care Level $ grouped by Care Type" for sources without acuity. Design decision, not a bug.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.11
- `tools/migration/migrate_to_v0111.py` — idempotent migration script
- `SPEC-T12.md` — current-version line bumped, file inventory updated
- `SPEC-RR.md` — Track-versions inline line bumped (substrate v0.1.10 → v0.1.11)
- `CHANGELOG-T12.md` — this entry; also corrected header line's stale Track 1 reference (was v1.11.0; now v1.16.1)

---

## [Substrate template v0.1.10] — 2026-05-11

### Summary

Track 3 companion to RR v1.16.0 (Track 1 data-capture expansion). Adds 7 new column headers to `Rent Roll Input` row 4 at columns V-AB, after the existing T-U formula columns. Extends the `Total Monthly Rev` formula at `U7:U606` to include the new 2nd Person Rent column. No new sheets, no new named ranges, no rewiring of existing aggregators — purely a column-extension of the existing Rent Roll Input schema.

### What changed (migrate_to_v0110.py)

- **A. New headers at Rent Roll Input row 4 cols V-AB**, styled to match the existing navy `FF1F3864` header row:
  - V: `2nd Person Rent $` (Tier 1.2 — RR ↔ T12 2P reconciliation enabler)
  - W: `Move-out Date` (Tier 2.1 — vacate forecasting)
  - X: `Balance` (Tier 2.2 — bad-debt indicator)
  - Y: `Notes` (Tier 2.3 — free-form context)
  - Z: `Market PSF` (Tier 3.1)
  - AA: `Actual PSF` (Tier 3.1)
  - AB: `ACH` (Tier 3.2 — collection-velocity flag)
- **B. Total Monthly Rev formula extension at U7:U606:**
  ```
  =IFERROR(H{r}+IFERROR(I{r},0)+T{r},0)
    -> =IFERROR(H{r}+IFERROR(I{r},0)+T{r}+IFERROR(V{r},0),0)
  ```
  Adds `+V{r}` (2nd Person Rent) to the per-resident total. 2P is incremental housing revenue and was previously excluded — without this fix, V would be populated but never flow into TMR or downstream aggregators that read U.
- **C. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.10`.

### Idempotency

Gate (`is_already_v0110()`) checks BOTH the version stamp AND that the row-4 V header is present. The formula-update step gates on the exact old-pattern match per row, so cells with customized formulas are left untouched on re-run.

### Verification

5-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, 7 new headers present at V-AB, TMR formula extended in sample rows (DATA_START / mid / DATA_END), existing A4 header (`Unit #`) intact.

End-to-end smoke against the Homestead fixture: RR v1.16.0 → translate → populate v0.1.10 Analyzer → Sandra & Darryl Owens row 19 has V=$650 (2P) + O=$100 (H/K) = $750 total, Notes captured ("HK $100 eff 3/1- sec occ $650"), Move-in Date 2026-02-23, Market PSF 8.12, ACH "X", and U19 formula correctly references V19.

### Out of scope (logged for v0.1.11+)

- `Rent Roll Recon` section K (IL deep-dive at rows 86-100) could surface PSF stats now that the substrate has those columns. Small addition (2-3 cells).
- `T12 Analytics` could add a new row that reconciles `SUM('Rent Roll Input'!V) × 12` (RR-projected 2P annualized) against `T12 Raw Data!2nd Person Revenue` (T12 actual). Same shape as Section B revenue reconciliation. Useful enhancement.
- `Workbook Health` could aggregate `Balance` column as a total-AR validation. Useful but not blocking.

### Carry-forwards opened

None blocking. The three items above are nice-to-haves that don't gate any downstream UW work.

---

## [Substrate template v0.1.9] — 2026-05-11

### Summary

Bug fix on top of v0.1.8. Two issues surfaced when a user opened the substrate-v0.1.8 populated Analyzer in Excel: (a) the period-selector dropdown on `Rent Roll Recon!B2` rendered empty, and (b) the cell didn't auto-populate the latest period. Same root cause behind both: `RR_Calc!A2:A13` (the dropdown source + the v0.1.8 LOOKUP target) was pre-populated with `_xludf.minifs(...)` formulas. The `_xludf.` prefix is a Google Sheets / LibreOffice user-defined-function marker that Excel does not recognize as a function name — every cell resolved to `#NAME?`, the `IFERROR(..., "")` wrapper returned `""`, and my v0.1.8 LOOKUP-against-RR_Calc found no numeric value to return.

### What changed

**Migration script — `tools/migration/migrate_to_v019.py`:**

- **A. Drop `_xludf.` prefix from 12 cells in `RR_Calc!A2:A13`** — `_xludf.minifs(...)` → `MINIFS(...)`. Excel-native MINIFS evaluates these correctly; the dropdown now populates with the sorted unique period dates and the chain feeds downstream cells as designed.
- **B. Rewrite `Rent Roll Recon!B2` formula** to read directly from `Rent Roll Input!$S$7:$S$606` via `MAX`, dropping the transitive dependency on RR_Calc. Belt-and-suspenders — if RR_Calc ever drifts again, B2 still works:
  ```excel
  =IF(MAX('Rent Roll Input'!$S$7:$S$606)>0,MAX('Rent Roll Input'!$S$7:$S$606),"")
  ```
  Data validation on B2 (the dropdown sourced from RR_Calc) is left in place — now that RR_Calc evaluates correctly, the dropdown lets analysts override to an earlier period.
- **C. Stamp `Cover!B8` and all 13 anchor `AZ4` cells to v0.1.9.**

Idempotent — `is_already_v019()` gate checks both the version stamp AND that no `_xludf` prefix remains in RR_Calc, so the migration safely re-applies on partial-state files. 6-check verification block confirms: Cover B8 stamped, all 13 AZ4 stamped, zero `_xludf` remaining workbook-wide, RR_Calc!A2 uses native MINIFS, B2 references direct MAX on Rent Roll Input!S, B2 data validation intact.

### Why this is in scope

Analogous to the v0.1.6 H20 `_xlfn._LONGTEXT` chunked-literal repair (Cluster A correctness fix). The architectural constraint of "additive only" is preserved — these are formula-text repairs on broken formulas, not a rewrite of an aggregator's logic. RR_Calc's intent (produce sorted unique period dates) is unchanged; only the Excel-incompatible function-name prefix is removed.

### Files

- `tools/migration/migrate_to_v019.py` — new migration script.
- `ALF_Financial_Analyzer_Only.xlsx` — bundled regenerated at v0.1.9.
- `SPEC-T12.md`, `CLAUDE.md`, `OPTIMIZATION-DECISIONS.md`, `journal.md` — current-version refs + new design entry / decision / session note.

### Verification

- 6-check migration verifier: all green on first clean run, idempotent re-run is a no-op.
- Functional smoke: load v0.1.9 bundled Analyzer, populate via `analyzer_rr_writer.populate_t12()` with 4 rows at period 04/24/2026, confirm the saved file has `Rent Roll Recon!B2` formula referencing `MAX('Rent Roll Input'!$S$7:$S$606)` and zero `_xludf` anywhere. (Excel-side calculation of the formula confirmed manually against the user's reported repro.)

### Carry-forwards opened by this round

- **None.** This is a pure bug fix that closes the user-reported issue. Branch 2 (Handoff readiness) remains the next open Analyzer-optimization workstream.

---

## [0.2.1] — 2026-05-11

### Summary

Track 2 follow-up to substrate v0.1.8 Branch 3 analytical coverage: the T12 Analyzer writer (`t12_normalizer_writer.populate_t12_input`) now stamps the property name into `T12 Input!A10`, derived from the uploaded T12 filename. Closes the Track 2 carry-forward opened by substrate v0.1.8. T12 Analytics!B2 (3-priority RR → T12 → Cover) now sees A10 populated when a T12 is uploaded — so if no RR is uploaded for the same property, B2 falls through to the T12-derived name instead of the Cover!B5 default.

### What changed

**Writer — `t12_normalizer_writer.py`:**
- New `from property_name import derive_property_name` import (shared cross-track utility introduced in RR v1.15.0).
- `populate_t12_input()` already received `source_filename` — that path is now extended: when non-empty, the derived property name is written to `T12 Input!A10` after the GL detail rows. Empty filename or empty derivation leaves A10 untouched.
- Step numbering in the function body shifted: prior Step 4 (Description_Map append) and Step 5 (Run_Info upsert) become Steps 5 and 6; new Step 4 is the property-name stamp.
- Idempotent: each call rewrites A10 from the new T12 file's derived name. Matches the existing "writer manages the T12 Input sheet" contract.

**App — `app.py`:**
- `T12_VERSION = "0.2.1"` (was 0.2.0); `T12_LAST_UPDATED = "2026-05-11"`.
- No call-site change needed — `populate_t12_input()` already received `source_filename`; the new behavior consumes it.

**Docs:**
- `SPEC-T12.md` — Current version line bumped to v0.2.1; brief note in the parser/writer section about the A10 stamp.
- `CHANGELOG-T12.md` — this entry.
- `CLAUDE.md` — Track 2 follow-up carry-forward marked closed; current T12 version bumped to v0.2.1.

### Verification

In-process smoke test (`_smoke_t2.py`, not committed) covers the end-to-end pipeline through both writers:
1. RR + T12 uploaded with same filename property prefix → A3 and A10 both populated with the derived name.
2. RR + T12 from different uploads → A3 from RR-derived, A10 from T12-derived (RR wins in B2 by 3-priority order).
3. T12 only (no RR) → A3 empty, A10 populated.
4. Empty `source_filename` → A10 untouched.
5. T12 Analytics B2 formula still resolves cleanly through the 3-priority chain.

### Why this is Track 2 (not Track 3)

Same logic as the RR v1.15.0 commit: substrate cell reservation was Track 3 work (substrate v0.1.8); stamping content into that cell from a parser-side filename is application logic — Track 2 territory. Bundled into the same chat as Track 1 per user authorization on 2026-05-11.

---

## [Substrate template v0.1.8] — 2026-05-11

Branch 3 of the Analyzer optimization roadmap (analytical coverage). All edits additive — new formulas in currently-empty cells (`T12 Analytics!B2`/`E2`), new chart objects on currently-empty `T12 Analytics!K1:V44`, and two new sections appended at the bottom of `Rent Roll Recon` (rows 86-117). No existing aggregators rewired. Workbook-only — no code changes to `t12_normalizer.py` / `t12_normalizer_writer.py` / `analyzer_rr_writer.py` / `app.py`. Design captured in `OPTIMIZATION-DECISIONS.md` decisions D-15 through D-22.

### What changed (Track 3 — workbook substrate)

**Property name + period plumbing** (closes F-9, F-10, F-11 from the 2026-05-11 grounding inspection):
- Reserved single-cell property-name value targets: `Rent Roll Input!A3` and `T12 Input!A10`. No separate labels — the cell location itself is the documented contract. Until Track 1/2 writer follow-ups land, these cells are analyst-paste; the analyst types once and T12 Analytics!B2 picks it up.
- Rewired `T12 Analytics!B2` from `=Property_Name` to a 3-priority formula: `Rent Roll Input!A3` → `T12 Input!A10` → `Property_Name` (Cover!B5). Until writer follow-ups land, behavior identical to before — `Property_Name` is the only populated source.
- Installed `T12 Analytics!E2` rightmost-populated-month formula: `=IFERROR(LOOKUP(2,1/('T12 Input'!$C$11:$N$11<>""),'T12 Input'!$C$11:$N$11),"")`. Partial-year safe. Named range `T12_Period_Date` now resolves; Workbook Health row 26 auto-validates.

**Property snapshot visuals on T12 Analytics** (closes F-13):
- 5 chart objects at `K1:V44` (industry-standard senior-housing UW visual set per CBRE / NIC MAP research):
  - V1 — Occupancy by Care Type (stacked column, IL/AL/MC × Occupied/Vacant/Notice/Eviction)
  - V2 — Rate Dispersion (clustered column, 5 rate bands × IL/AL/MC three-series)
  - V3 — Payer Mix (doughnut, 7 payer types as % of total monthly revenue)
  - V4 — T12 Revenue Trend (line, 12 months of total operating revenue)
  - V5 — AL Acuity Mix (doughnut, Basic/Level 2-7 distribution)
- 5 conditional formula-driven note cells at `K15`/`K30`/`P15`/`P30`/`K45` — context messages that update with the underlying data (e.g. "⚠ Medicaid revenue share 35% — reimbursement rate risk" only fires when Medicaid > 30%).
- Hidden helper block at `K46:V52` for rate-bucket counts (V2 source) and at `K53:V54` for monthly revenue totals (V4 source). Bucket boundaries: $0-1,999 / $2,000-3,999 / $4,000-5,999 / $6,000-7,999 / $8,000+. Revenue source: `SUMIFS('T12 Raw Data'!F:F..Q:Q, A:A, "Revenue")` — sums all Revenue-section rows per month.

**Rent Roll Recon period default + dropdown** (closes F-11):
- `Rent Roll Recon!B2` set to `=IFERROR(LOOKUP(9.99E+307,'RR_Calc'!$A$2:$A$13),"")` — returns the latest date from the ascending-sorted period list.
- Data validation list on B2 sourced from `RR_Calc!$A$2:$A$13`. Analyst can override via dropdown; once overridden, the formula is replaced by the static date (standard Excel behavior). Re-running the migration restores the formula default — flagged as expected idempotency side effect.

**Rent Roll Recon section K — IL Unit-Type Mix, Size & Rate Dispersion** (closes F-14):
- New section at rows 86-100 (append, not insert — avoids openpyxl `insert_rows()` formula-text quirk).
- Columns: Unit Type / Count / % of IL / Avg Rate / Min Rate / Max Rate / Avg Sq Ft / $/Sq Ft.
- Apt-type breakouts: Studio / 1 Bedroom / 2 Bedroom / Cottage / Villa / Other (filter on `Rent Roll Input!F`).
- Summary rows: rate spread (max − min), CV proxy ((max − min) ÷ avg ÷ √12), avg sq ft, sq ft range, $/sq ft.
- Conditional note at A100: flags wide IL rate dispersion (CV > 25%) as possible legacy in-place rates.

**Rent Roll Recon section L — MC Care Structure auto-detect** (closes F-15):
- New section at rows 102-117.
- B103 pattern detector: counts distinct populated K-column values among occupied MC residents and classifies as Flat-rate / Tiered / Fee-for-service.
- Tier mapping (rows 106-108): substring match on K values — Basic/Tier 1/Level 1 → Tier 1, Moderate/Tier 2/Level 2-3 → Tier 2, Advanced/Tier 3/Level 4-7 → Tier 3. Row 109 (Other / unmapped) catches FFS.
- Summary rows: avg base rent / resident, avg care charge / resident, care charge ÷ base rent ratio (flag if > 30%), total MC monthly revenue.
- Conditional note at A117: pattern-specific guidance — "Flat-rate MC detected.", "Tiered MC detected. Verify per-tier staffing model.", or "Fee-for-service MC detected. Review individual care plans for sustainability."

**Substrate version stamp** `v0.1.7 → v0.1.8` (`Cover!B8`, all 13 anchor `AZ4` cells).

### Files

- `tools/migration/migrate_to_v018.py` — new migration script. 10 operations, 17-check verification block. Re-run on a v0.1.8 file is a no-op via the `is_already_v018` guard.
- `ALF_Financial_Analyzer_Only.xlsx` — bundled regenerated at v0.1.8.
- `OPTIMIZATION-DECISIONS.md` — added Branch 3 design (Clusters B3.1-B3.5), discovered facts F-9 through F-15, decisions D-15 through D-22.
- `SPEC-T12.md` — Current Template substrate version line bumped; v0.1.8 entry appended to substrate history.
- `CHANGELOG-T12.md` — this entry.
- `CLAUDE.md` — version line, last-updated, carry-forward updates.
- `journal.md` — session entry.

### Carry-forwards opened by this round

- **Track 1 follow-up — RR writer stamp.** Modify `writer.py` to write the parsed property name into `Rent Roll Input!A3`. Until this lands, A3 is analyst-paste only and T12 Analytics B2 continues to fall back to Cover!B5.
- **Track 2 follow-up — T12 writer stamp.** Same idea for `t12_normalizer_writer.py` → `T12 Input!A10`.
- **Branch 2 — Handoff readiness** remains open per the Track 3 roadmap (UW Export mirror, pre-export gate, metadata header).

### Verification

`tools/migration/migrate_to_v018.py` 17-check block: Cover!B8 = v0.1.8, all 13 AZ4 stamped, B2 3-priority formula references RR Input A3 + T12 Input A10, E2 LOOKUP formula present, 5 chart objects on T12 Analytics, helper rate-bucket block populated, helper V4 monthly revenue row populated, 5 conditional note cells present, Rent Roll Recon B2 formula + DV present, IL section K header at A86, IL total row at B93, MC section L header at A102, MC pattern detector at B103, RR Input A3 reserved (no leftover label), T12 Input A2 cleared (A10 is the writer target), all named ranges intact. Idempotent — re-run on v0.1.8 file is a no-op via gate that checks both `Cover!B8` and the corrected B2 formula text.

Cell scan over all 13 sheets confirms zero formula error strings (`#NAME?` / `#REF!` / `#VALUE!` / `#DIV/0!` / `#N/A` / `#NUM!` / `#NULL!`) introduced.

---

## [0.2.0] — 2026-05-08

Adds `BrokerFinancialSummaryFormat` (third T12 format) and Cluster B robustness hooks (sign-convention guards + partial-year T12 detection). Closes the v0.1.6 carry-forward documented in OPTIMIZATION-DECISIONS.md D-12 and the BrokerFinancialSummaryFormat carry-forward from journal 2026-05-06.

### Added

- **`BrokerFinancialSummaryFormat`** — third T12 format alongside Yardi and MRI.
  - **Detection:** A4 contains `Historical Performance` (case-insensitive). When multiple sheets match, picks the first (matches Homestead's `Summary` over `P&L-Dumps`).
  - **Column selection:** broker files may have 12 to 54+ datetime cells in row 4 (Homestead has 39 across CY / T12 / T6M / T2M / T1M sections). Parser walks row 4 right-to-left and returns the **rightmost contiguous monotonic monthly run** (≤12 cells). For Homestead Summary that picks cols AB:AM (Apr 2025 → Mar 2026, the T12 block); for March_2026 single-sheet it picks B:M.
  - **Banner-prefix disambiguation.** Each section banner (col A text + all 12 monthly cells truly None) becomes the prefix for the next GL rows: `Direct Care | Payroll - Wages` vs `Marketing | Payroll - Wages`. Subtotal rows pop the sub-banner back to the top-level "Revenues" so siblings (`Concessions`, `Respite Revenue`, `Move-In Fees`, `Other Income`) emit unprefixed.
  - **Pre-financial preamble drop.** Drops everything before the first banner matching `Revenue` / `Revenues` (filters Census / ADC / Room Rates summaries).
  - **Post-P&L cutoff.** Stops on banners matching `Non-Operating` / `Wages Analysis` / `Payroll Summary` (drops below-NOI items + broker analytical sections).
  - **Standard signs.** No per-format sign override; revenue +, expense +, concessions − (matches Yardi/MRI).
  - **Total computed locally.** Broker "Totals" column (when present at col 14 of March_2026 or col 40 of Homestead) is ignored; parser sums the 12 monthly values.
- **`_check_sign_convention(gl_rows)`** — Cluster B B-1. Returns warnings for descriptions containing `CONCESSION` (suffix-only match — banner-name keyword false-positives suppressed) with positive totals. Defensive; doesn't fire on any of the four verified fixtures.
- **`_count_populated_months(gl_rows)`** — Cluster B B-2. Counts how many of the 12 month columns have at least one non-zero GL value across all rows. Drives partial-year detection downstream.
- **`_annualize_rows(gl_rows, populated_months)`** — pure-Python annualizer. Multiplies monthly + total by 12/N.
- **`parse_t12(..., annualize_partial_year: bool = False)`** — new optional kwarg. Controlled by the app's sidebar checkbox; when `True` and `populated_months < 12`, parser scales values before returning.
- **`T12ParseResult` fields** — `sign_warnings: List[str]`, `populated_months: int`, `was_annualized: bool`. Backwards-compatible (positional args unchanged).
- **`tools/verify_t12_v020.py`** — parser-side end-to-end harness covering all four reference fixtures with deterministic checks (format detection, GL row count, source $, populated months, implied NOI for broker, sign-warning + UNMATCHED counts). Substrate-level EGI / EBITDARM unchanged from v0.1.6 — workbook formulas are untouched, so v0.1.1's verified $2,201,865 (Salem) / $3,763,229 (Briar Glen) continue to hold.

### Changed

- **`GRAND_TOTAL_PREFIXES`** extended with `SUBTOTAL,` and `SUBTOTAL ` (broker convention catches `Subtotal, Room & Board`, `Subtotal, Care Level`, etc.).
- **`EXPLICIT_DROP_LIST`** extended with `NOI on Statement` and `Check` (broker-specific summary lines that aren't GL detail).
- **`app.py`** — sidebar gets an "Annualize partial-year T12" checkbox (disabled until a T12 is uploaded). T12 status panel surfaces partial-year warning when `populated_months < 12`, and lists every `sign_warning`. Period-label display tolerates partial-year padded-empty labels. Version pill shows `T12 v0.2.0`.

### Verified end-to-end (2026-05-08)

All four fixtures parse against the v0.1.7 Description_Map (after Phase 4 substrate appends):

| Fixture | Format | GL rows | UNMATCHED | Months | Implied NOI / Source $ |
| --- | --- | ---: | ---: | ---: | ---: |
| Salem | Yardi (Income to Budget) | 73 | 0 | 12 | source = $4,249,047.98 |
| Briar Glen | MRI R12MINCS | 91 | 0 | 12 | source = $8,306,657.64 |
| Homestead Pensacola | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 (broker NOI to the penny) |
| March 2026 | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 |

Both broker fixtures share identical T12 data (101 unique parser-produced descriptions, $12,592,590 source); they differ only in workbook layout (Homestead is multi-section dashboard, March_2026 is single-sheet T12).

### Notes

- **Banner-prefix is always-on for broker files.** The parser does not consult Description_Map to decide whether to prefix. Phase 4 substrate v0.1.7 ships 99 prefixed Description_Map entries to make Homestead/March_2026 zero-UNMATCHED end-to-end. Future operators may need similar substrate vocabulary additions.
- **Salem's source $ now includes Management Fees** ($131,579.65 — fixed in v0.1.1) — unchanged at v0.2.0.
- **Cluster B partial-year detection counts MONTH columns with any non-zero GL value.** A row of zeros in March doesn't count March as populated, but a row of -$1 in March does.

---

## [Substrate template v0.1.7] — 2026-05-08

Workbook-side companion to T12 code v0.2.0. Closes the substrate carry-forwards from v0.1.6 (R102 lease formula, N501→N500 cosmetic, Cluster B partial-year row) and ships the Description_Map vocabulary needed to make Homestead / March_2026 broker fixtures zero-UNMATCHED end-to-end.

### Fixed

- **`T12 Analytics!E102` (Lease / ground lease)** — was `=0` placeholder per v0.1.4 plan that never landed. Replaced with `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`. Sibling `F102` set to `=E102`. UW Output R61 (Lease) now displays real values when source has lease data, instead of $0.
- **`T12 Raw Data` SUMIFS range mismatch** — 636 formula cells had `T12_Calc!$X$1:$X$501` (legacy from v0.1.5 row insert). Swept to `$X$1:$X$500` to match T12_Calc's actual 500-row data area. Cosmetic; T12_Calc row 501 reads empty either way, so no $ effect.

### Added

- **`Workbook Health!A30` — V8 partial-year T12 validation row.** Formula: `=COUNTA('T12 Input'!C11:N11)` paired with `=IF(B30=12,"✓","⚠")`. Surfaces partial-year T12s alongside V1-V7 in the existing Validation section (replaces the formerly-blank gutter row 30 between Validation and Diagnostics).
- **99 Description_Map entries (Homestead vocabulary).** Mechanically derived from the populated_analyzer's v0.1.5 Option-C work: for each parser-produced unique broker description, its suffix-Label mapping is inherited (e.g., `Direct Care | Payroll - Overtime → Overtime wages`, `Utilities | Electric → Utilities`, `Marketing | Payroll - Wages → Administrative labor`). All 99 map cleanly to the existing 54-Label closed vocabulary. After this addition, both Homestead Pensacola and March_2026 broker fixtures parse with **zero UNMATCHED descriptions**.

### Changed

- **Substrate version stamp** `v0.1.6 → v0.1.7` (Cover!B8, all 13 anchor `AZ4` cells).

### Migration script

- **`tools/migration/migrate_to_v017.py`** — idempotent. Operations: apply lease formula at E102/F102 → sweep $501→$500 across T12 Raw Data → add V8 partial-year validation row → append 99 Description_Map entries (skipping any already-present keys) → stamp version cells → run 7 verification checks.

### Verified end-to-end (2026-05-08)

- Migration ran clean against v0.1.6 bundled `ALF_Financial_Analyzer_Only.xlsx`. All 7 verification checks pass.
- Re-run (v0.1.7 → v0.1.7) is a no-op via the `is_already_v017` guard.
- Description_Map row count grows from 311 → 410 (311 existing + 99 new).
- All four reference fixtures (Salem, Briar Glen, Homestead, March_2026) produce 0 UNMATCHED when parsed against the v0.1.7 substrate.

---

## [Substrate template v0.1.6] — 2026-05-07

Workbook-side optimization round per OPTIMIZATION-DECISIONS.md (Branches 1 + 4 of the optimization mind map). Cluster B (sign-convention guards, partial-year T12 handling) is code-side and ships separately on Track 2.

### Added

- **Cover sheet** at first tab position. Carries property name, substrate version, RR / T12 normalizer version pills, repo + app links, and a short About block. Property name lives canonically at `Cover!B5` and propagates via the new `Property_Name` named range.
- **Workbook Health sheet** at last position, hidden by default. Three sections: Workbook Map (formula-driven from per-sheet anchor cells), Validation (7 live $ checks), Diagnostics (capacity utilization, version pills, last-open timestamp).
- **Per-sheet anchor cells** at `AZ1:AZ5` on all 13 sheets — purpose / category / visibility / version / notes. Drives the Workbook Map section. AZ5 (notes) left empty by default.
- **5 named ranges**: `RR_Period_Date` (`Rent Roll Recon!B2`), `T12_Period_Date` (`T12 Analytics!E2`), `RR_Input_Data` (`Rent Roll Input!A7:S606`), `T12_Input_Data` (`T12 Input!A12:O511`), `Property_Name` (`Cover!B5`). Joins the existing two (`DescMap_Description`, `DescMap_Label`).
- **Light cell comments** on 5 hardest-to-decode formula cells: `Monthly Trending!B5` (T12 rollup INDEX/MATCH pattern), `T12 Analytics!E37` (GPR), `T12 Analytics!E52` (EGI), `T12 Analytics!E110` (EBITDAR after mgmt fee), `Rent Roll Recon!H20` (RR↔T12 gap diagnostic).

### Fixed

- **`Rent Roll Recon!H20` `#NAME?` error** — the diagnostic message cell that interprets the RR-vs-T12 base rent gap was broken in every populated workbook because its 5-item investigation lists exceeded Excel's 255-char-per-literal cap and got serialized as `_xlfn._LONGTEXT(...)` calls Excel doesn't recognize. Rewritten with chunked literals (each ≤255 chars, joined with `&`). Same four-case logic, same message content, parses clean. Cell now displays its intended diagnostic instead of `#NAME?`.
- **UW Output R29 (Bonus wages)** — formula gap. `B29:D29` set to `"-"`, `E29` and `F29` now point at `T12 Analytics!E64`/`F64` (sibling-pattern fill).
- **UW Output R57 (Bad debt expense)** — same gap pattern. Filled to point at `T12 Analytics!E98`/`F98`.
- **UW Output R61 (Lease / ground lease)** — was fully empty including `G61` variance. Filled to point at `T12 Analytics!E102`/`F102` (currently `=0` placeholder; see deferred bug below). Indent fixed (0.0 → 1.0) to match siblings R60 / R62.
- **`T12 Analytics!B2` (Property name)** — wired to `=Property_Name`. Was empty; now propagates from Cover sheet input.

### Changed

- **Substrate version** stamp `v0.1.5 → v0.1.6` (Cover!B8, all 13 anchor AZ4 cells).

### Deferred

- **`T12 Analytics!R102`** still `=0` placeholder. Replacing with the planned INDEX/MATCH against `T12 Raw Data!B:B` for "Lease / ground lease" requires rewiring an existing aggregator, which was out of scope for this round per the architectural constraint. Result: `UW Output!R61 Lease` displays `$0` until v0.1.7 picks this up. Tracked in OPTIMIZATION-DECISIONS.md A-5.
- **`T12 Raw Data` SUMIFS range cosmetic mismatch** — some shifted rows still reference `$N$1:$N$501` instead of `$N$1:$N$500` (artifact of the v0.1.5 migration). Harmless; same-as-before. Logged for next migration that touches the range.

### Migration script

- **`tools/migration/migrate_to_v016.py`** — idempotent. Operates in order: add Cover sheet → apply Cluster A formula fixes → add Workbook Health sheet → populate AZ anchor cells on all 13 sheets → add 5 named ranges → wire `T12 Analytics!B2` → add cell comments → verify (11 checks).

### Verified end-to-end (2026-05-07)

- Migration runs clean on `ALF_Financial_Analyzer_Only.xlsx` (empty v0.1.5 template).
- Re-running on a v0.1.6 file is a no-op (idempotency works).
- LibreOffice recalc of the migrated empty template produces **0 formula errors** across all 13 sheets.
- `Rent Roll Recon!H20` resolves to `"Gap = $0 — RR and T12 are perfectly aligned."` (case 1 of 4) on the empty template — was `#NAME?` before.
- Workbook Health Map section pulls correctly from all 13 anchor cells via formula refs.
- Validation section fires `⚠` on missing RR/T12 period dates and Property name (correct behavior on an empty template).

### Notes

- Three openpyxl quirks worth flagging for future migrations on this workbook:
  1. `wb.defined_names[name] = DefinedName(...)` is the v3.x assignment form — `defined_names.append()` was removed.
  2. Empty-string cell values render as `0` in Excel/Calc when read back. Preferred: leave the cell truly unset (skip the assignment) rather than write `""`. Workaround in formula context: wrap with `=IF(ref="","",ref)`.
  3. `Cell.alignment` is read-only; to mutate one attribute (e.g. indent) re-assign the whole `Alignment(...)` object preserving the others.

---

## [Substrate template v0.1.5] — 2026-05-04

Substrate-only change (no code release). Adds one new Label, `2nd Person Revenue`, to the closed vocabulary (54 → 55 Labels). Migration script `migrate_to_v015.py` applies idempotently to any v0.1.4 Analyzer.

### Why

Surfaced on Homestead Pensacola broker file (2026-05-04). Broker reported second-occupant revenue as three separate line items by care type (`Second Persons Revenue | Independent Living`, `... | Assisted Living`, `... | Memory Care`). v0.1.4 substrate had no Label for this — collapsing into `Base rent — IL/AL/MC` would inflate the per-bed base rate (Base rent ÷ ADC). At Homestead the inflation was modest ($43/bed/mo on AL is the largest), but the principle is right: a second occupant generates additional revenue at a fixed rate, separate from base rent. Per-bed base rate calculations now stay clean.

### Changed

- **T12 Raw Data**: new row at R15 `2nd Person Revenue` (was Other community revenue). Helper SUMIF formulas across F:Q reference T12_Calc!N matching the new Label string. Col R `=SUM(F15:Q15)`. Old R15+ shifted down by 1.
- **Monthly Trending**: new row at R19 `2nd Person Revenue` (was Other community revenue). Col B uses standard `=IFERROR(INDEX('T12 Raw Data'!F:F,MATCH("2nd Person Revenue",'T12 Raw Data'!B:B,0)),0)` pattern with month-equivalent formulas across C:M. Col N `=SUM(B19:M19)`. EGI formula at (post-shift) R21 rewritten from `=B8+B10+B11+B15+B16+B17+B18+B19` to `=B8+B10+B11+B15+B16+B17+B18+B19+B20` — adds the new R19 (2nd Person) to the sum while preserving Total base rent (R8) clean. Old R19+ shifted down by 1.
- **T12 Analytics**: 4 cells (E38, H38, E39, E40) patched to follow Physical Vacancy and Loss to Lease references as they shifted from `T12 Raw Data!$R$55/$R$56` → `$R$56/$R$57`.
- **Description_Map**: no schema changes. New Label becomes referenceable when descriptions map to it; vocabulary lookup unaffected.

### Migration mechanics

Three openpyxl quirks discovered and worked around in `migrate_to_v015.py`. Documenting here because the same patterns will apply to any future Label-insert substrate change:

1. **`insert_rows()` shifts cell positions but does not update formula text.** 684 cells in T12 Raw Data and 145 cells in Monthly Trending have formulas referencing rows >= insert point that all need explicit row-ref updates. Plus 4 external refs in T12 Analytics. Solution: full-workbook formula sweep with regex-based row shifting, handling both qualified (`'Sheet'!A19`) and unqualified (`B19`) refs, including range endpoints (`F15:Q15`).
2. **Range-endpoint refs need the lookbehind regex to allow colons.** Initial pattern `(?<![A-Za-z_!:])` excluded the second endpoint of a range like `F15:Q15` because `:` was in the lookbehind. Fix: `(?<![A-Za-z_!])` — drop the colon — so both endpoints get shifted.
3. **`insert_rows()` does not shift merged-cell range definitions.** The original substrate has `A21:N21` (LABOR section header) merged. After insert at R19, the LABOR text moves to R22 but the merge range still says A21:N21 — and the row that shifted into R21 (the EGI subtotal) ends up *inside* the stale merge range, causing Excel to silently drop its non-A column values on save (merged cells only keep the top-left value). **Critical: don't fix this with `unmerge_cells()` then `merge_cells()` with new addresses.** That triggers openpyxl's unmerge logic which clears the non-top-left cells of the merge — but those cells now hold real shifted content, which gets wiped. Fix: use the merge range's `shift(row_shift=delta)` method to mutate bounds in-place without unmerge.

### Verified end-to-end (2026-05-04)

Homestead Pensacola repopulated against v0.1.5 substrate:

| Metric | Result | Target | OK |
| --- | ---: | ---: | --- |
| GL rows written | 101 | 101 | ✓ |
| UNMATCHED descriptions | 0 | 0 | ✓ |
| Source $ → Operating $ leakage | $0.00 | $0.00 | ✓ |
| R8 Total base rent (CLEAN, no 2nd person) | $6,951,136.46 | $6,951,136.46 | ✓ |
| R19 2nd Person Revenue (NEW, isolated) | $32,220.49 | $32,220.49 | ✓ |
| R21 EFFECTIVE GROSS INCOME | $7,001,956.79 | $7,001,956.79 | ✓ |
| R69 EBITDARM | $1,761,421.43 | $1,761,421.43 | ✓ |
| R70 EBITDAR (= broker NOI on Statement) | $1,411,323.58 | $1,411,323.58 | ✓ |

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — migrated to v0.1.5 substrate
- `migrate_to_v015.py` — migration script (idempotent; detects `2nd Person Revenue` in T12 Raw Data and exits if already applied)
- `SPEC-T12.md` — updated current-version line and Template substrate section
- `CHANGELOG-T12.md` — this entry

Pre-existing `Rent Roll Recon!H20` `#NAME?` is **not** introduced by this migration; it's a substrate-level issue documented in [0.1.0]. Migration verified against an empty v0.1.4 substrate (recalc: 0 errors, 10,953 formulas all evaluate clean).

---

## [0.1.1] — 2026-05-02

Patch release. Fixes a Yardi-extractor bug that silently dropped Salem's $131,579.65 Management Fees line. Briar Glen and the rest of the v0.1.0 verification numbers are unaffected.

### Fixed

- **`t12_normalizer.py` — Yardi extractor no longer requires a numeric account #.** v0.1.0's `YardiIncomeToBudgetFormat.extract()` required col A to contain a numeric account number on every GL row, applied *before* the three drop-rules. This was a defensive guard against picking up section headers and subtotals, but it was too strict: Yardi sometimes reports single-line expenses (notably property-management fees) as section-banner-style rows with no account number, and v0.1.0 silently dropped them. The check is removed; the three drop-rules (no $, grand-total pattern, explicit drop-list) are sufficient on their own. Account # is still preserved when present (most rows) and stored as `""` when absent. Format **detection** in `YardiIncomeToBudgetFormat.detect()` still uses the "≥3 numeric account #s in body" heuristic — that's about identifying which file is a Yardi T12, not which rows to keep.
- **`t12_normalizer.py` — added `Non-Operating Expenses` to the explicit drop-list.** Yardi's "Non-Operating Expenses" appears twice in Salem's source: once at row 134 as a section header (col O blank, caught by drop-rule 1) and once at row 137 as a subtotal of the preceding GL rows (col O = $45,161.67, but no `TOTAL` prefix so drop-rule 2 misses it). Without this fix, removing the account-# filter would have caused row 137 to double-count rows 135 (`Depreciation Expense`) and 136 (`Other Non Operating Revenue & Expense`). Added per the spec's documented pattern: "New non-operating descriptions added to this list when encountered."

### Verified end-to-end (2026-05-02)

Salem now reconciles to source on every line. Briar Glen unchanged.

| Metric | Salem (Yardi) | Briar Glen (MRI) |
| --- | ---: | ---: |
| GL rows written | 73 (was 72 at v0.1.0) | 91 (unchanged) |
| UNMATCHED at parse | 0 ✓ | 0 ✓ |
| Source $ | $4,249,047.98 (v0.1.0: $4,117,468.33; +$131,579.65 management fee) | $8,306,657.64 (unchanged) |
| Operating $ (T12 Raw Data total) | $4,205,759.14 (v0.1.0: $4,074,179.49; +$131,579.65) | $8,310,006.39 (unchanged) |
| Depreciation — EXCLUDED $ | $43,288.84 (unchanged) | -$3,348.75 (unchanged) |
| Leakage | $0.00 ✓ ZERO | $0.00 ✓ ZERO |
| EGI (`Monthly Trending!N20`) | $2,201,864.71 ✓ (unchanged — management fee doesn't affect revenue) | $3,763,228.77 ✓ (unchanged) |
| TOTAL OPEX excl. mgmt (`Monthly Trending!N66`) | $1,872,314.78 ✓ (unchanged — substrate's R66 already excludes mgmt) | $4,358,616.18 ✓ (unchanged) |
| Management fee (`Monthly Trending!N67`) | $131,579.65 ✓ (was $0.00 at v0.1.0 — bug fixed) | $188,161.44 ✓ (already correct in v0.1.0) |
| EBITDARM (`Monthly Trending!N68`) | $329,549.93 ✓ (unchanged — substrate excludes mgmt by accounting standard) | -$595,387.41 ✓ (unchanged) |
| EBITDAR (`Monthly Trending!N69`) | $197,970.28 ✓ (was $329,549.93 at v0.1.0 — now correctly subtracts management fee) | -$783,548.85 ✓ (unchanged) |

**Salem source-side cross-check.** Source row 126 EBITDARM = $329,549.93 → matches Salem R68 ✓. Source row 128 Management Fees = $131,579.65 → matches Salem R67 ✓. Source row 130 EBITDAR = $197,970.28 → matches Salem R69 ✓. Salem now ties to source on all four rows.

**Why EBITDARM didn't change.** The substrate's R66 (`TOTAL OPEX (excl. mgmt)`) deliberately excludes the management-fee line, and R68 EBITDARM = EGI − R66. So Management fee not appearing at all (v0.1.0 bug) versus appearing in R67 separately (v0.1.1 fix) makes no difference to EBITDARM by design — that's the accounting-standard definition. The bug surfaced at R69 EBITDAR, which is EBITDARM − R67. v0.1.0's R69 was wrong by exactly the missing management fee.

### How this was caught

Reported by user during post-v0.1.0 testing: "There was an omitted expense item in the Salem Road T12. Management fee was not included." User pointed to Description_Map row 122 (`Management Fees → Management fee`, ready and waiting) and Salem source row 128 (the actual line in the raw T12). Diagnosis traced to the Yardi extractor's strict account-# pre-filter dropping Salem's row 128 before drop-rules ran.

### Notes

- v0.1.0's verification table (72 GL rows, all-zero leakage already) was internally consistent — the missing management fee was getting dropped at parse time, so neither the source-side total nor the aggregated total counted it. The bug was a *missing line item*, not a *miscalculated line item*. This is why the v0.1.0 leakage check passed despite the bug.
- No app.py UI behavior changes. T12_VERSION constant bumped to `"0.1.1"`.
- No template substrate changes. Description_Map already had the mappings; the bug was upstream of the workbook.

---

## [0.1.0] — 2026-05-02

First T12 code release. Substantial template substrate work landed in the kickoff chat before any Python code was written — those iterations are documented below as part of the v0.1.0 ship scope. The code release on 2026-05-02 adds parser, writer, and `app.py` integration on top of that substrate.

### Added

- **`t12_normalizer.py`** — Format-registry parser. `T12Format` ABC with `detect(wb)` / `extract(wb, sheet)` methods. `YardiIncomeToBudgetFormat` (detects sheet named `Income to Budget` first, falls back to scanning for ≥3 numeric account-# rows) and `MriR12mincsFormat` (sheet name match) registered. Three drop-rules applied in order during extraction: no-$-value, grand-total pattern (TOTAL/NET prefixes, EBITDA/EBITDAR/EBITDARM keywords, exact NET INCOME / NET OPERATING INCOME), explicit drop-list (initially `Other Non Operating Revenue & Expense`). Returns `T12ParseResult` (gl_rows, month_labels normalized to `MMM YYYY`, unmatched, format_name, sheet_name). Raises `UnknownT12FormatError` if no format matches. UNMATCHED detection runs against the destination workbook's `Description_Map` set.
- **`t12_normalizer_writer.py`** — Idempotent destination writer. Loads the user's Analyzer / standalone Normalizer template (v0.1.4 substrate). Clears `T12 Input!A12:O511` + `T12 Input!C11:N11` before writing (prevents ghost rows on re-upload). Writes 12 month labels to C11:N11 with text format, then GL detail rows to A:O. Col P (Coverage Check formula), `T12_Calc!N` helper col, named ranges (`DescMap_Description`, `DescMap_Label`), and all other tabs untouched. Capacity 500 GL rows; raises `T12NormalizerCapacityError` if exceeded. Optionally appends UNMATCHED-resolution mappings to `Description_Map` after the last data row — the dynamic named ranges pick them up via COUNTA without formula edits. Upserts a `Run_Info` tab with T12 version, run timestamp, source filename, format detected, GL rows written, and Description_Map appends.
- T12-side version constants in `app.py`: `T12_VERSION = "0.1.0"`, `T12_LAST_UPDATED = "2026-05-02"`, alongside the existing `RR_VERSION` / `RR_LAST_UPDATED`.

### Changed

- **`app.py`** — Raw T12 uploader added to sidebar (optional). Interactive UNMATCHED matcher form appears when the parser returns unresolved descriptions: per-row Label combobox (sourced from the Analyzer's existing 54-entry vocabulary), Section dropdown (Revenue / Labor / Non-Labor / Excluded), CareType dropdown (`-` / IL / AL / MC), Flag dropdown (8 substrate values + blank). Resolutions persist in `st.session_state.t12_resolutions` and survive Streamlit reruns; submission validates that Label and Section are filled. Single combined download "Analyzer with both data" replaces v1.7.0's RR-only Analyzer paste; disabled until rent roll AND Analyzer AND raw T12 are uploaded AND all UNMATCHED are resolved. Combined flow writes RR data to `Rent Roll Input!A7+` first via the existing `t12_writer.populate_t12()` (historical name; see SPEC-T12 §"Module naming history"), then layers T12 data on top via the new `t12_normalizer_writer.populate_t12_input()`. Standalone Normalized RR download stays available whenever a rent roll is uploaded. Version pill renders both versions: `RR v1.11.0 · T12 v0.1.0`. Page title updated to "Rent Roll & T12 Normalizer".
- **Behavior change worth flagging.** v1.11.0's "Analyzer with Rent Roll" download (RR data only into Analyzer) is **retired** in this release per SPEC-T12 §"How the analyst uses the app". The single Analyzer download now always carries both RR and T12 data. Existing users who upload only an RR + Analyzer (no T12) will see the combined download stay disabled and only get the standalone Normalized Rent Roll. This is deliberate — the Analyzer is now defined as a both-data deliverable.

### Verified end-to-end (2026-05-02)

Numbers reconcile to the penny on both reference samples. Tested via parser → writer → LibreOffice recalc (`scripts/recalc.py`) → read post-recalc cell values.

| Metric | Salem (Yardi) | Briar Glen (MRI) |
| --- | ---: | ---: |
| GL rows written | 72 / 72 ✓ | 91 / 91 ✓ |
| UNMATCHED at parse | 0 ✓ | 0 ✓ |
| Source $ (`T12 Input!O` sum) | $4,117,468.33 | $8,306,657.64 |
| Operating $ (`T12 Raw Data` total) | $4,074,179.49 | $8,310,006.39 |
| Depreciation — EXCLUDED $ (`T12 Input` col P filter) | $43,288.84 | -$3,348.75 |
| Leakage = source − operating − excluded | $0.00 ✓ ZERO | $0.00 ✓ ZERO |
| EGI (`Monthly Trending!N20`) | $2,201,864.71 ✓ | $3,763,228.77 ✓ |
| EBITDARM (`Monthly Trending!N68`) | $329,549.93 ✓ | -$595,387.41 ✓ |

Additional verifications:

- **Idempotent re-run** — Wrote Salem (72 rows), then Briar Glen (91 rows) on top of the same workbook. Result: exactly 91 rows in `T12 Input`, no ghost Salem rows, month labels swapped to Briar Glen's Jan–Dec 2025.
- **Capacity guard** — `T12NormalizerCapacityError` fires correctly on 501 synthetic rows; exactly 500 rows accepted (boundary OK).
- **UNMATCHED resolution loop** — Synthetic test injected a fake description (`Pickleball League Sponsorship Income`) with mapping {Other community revenue / Revenue / `-` / blank}. Mapping appended to `Description_Map` row 316. Post-recalc, T12 Input col P resolved the fake description to its label correctly via the dynamic named range — confirming `DescMap_Description` / `DescMap_Label` auto-extension works as designed.
- **Substrate preservation** — All 11 sheets, both named ranges, the hidden `T12_Calc!N` helper col, the 612 SUMIF formulas in `T12 Raw Data`, and rows 1-10 of `T12 Input` (title, instructions, layout note) confirmed intact post-write.
- **Run_Info tab** — Created with all 10 T12-side keys present (version, last-updated, run timestamp, source filename, format detected, source sheet, GL rows written, months detected, UNMATCHED at parse, Description_Map appends).

**Pre-existing substrate issue, not introduced by v0.1.0.** Recalc reports a single `#NAME?` error at `Rent Roll Recon!H20` on every output. Identical pre-write and post-write across both Salem and Briar Glen runs, so this is a substrate-level issue in the migrated master Analyzer (introduced during the master Analyzer migration on 2026-05-02), not anything this release added. Worth a separate substrate-cleanup pass; outside v0.1.0 scope.

### Template iterations (all ship with v0.1.0)

#### Master Analyzer migration — applied 2026-05-02

The five template iterations below were originally landed on the standalone T12 Normalizer template (`ALF_T12-_Normalizer.xlsx`). The user's master Analyzer (`ALF_Financial_Analyzer_Only.xlsx`) was at the pre-v0.1.0 substrate state and needed the same edits applied so that v0.1.0's parser/writer code can target either workbook.

Migration applied via `migrate_analyzer.py` (one-shot script, archived under `tools/migration/`). All five batches landed cleanly, end-to-end verification matched targets to the penny:

| Format | GL rows | UNMATCHED | EGI | EBITDARM |
| --- | ---: | ---: | ---: | ---: |
| Yardi (Salem) | 72 | 0 | $2,201,864.71 | $329,549.93 |
| MRI (Briar Glen) | 91 | 0 | $3,763,228.77 | -$595,387.41 |

Both dollar values reconcile exactly against the standalone T12 template's verification numbers, confirming the migrated master is structurally identical to the standalone v0.1.4 substrate.

**Salem GL-row count correction:** the standalone-template verification table reads "73 GL rows" for Salem. The accurate count after applying parser drop-rule #3 (`Other Non Operating Revenue & Expense` on the explicit drop-list) is 72. The "73" figure was the count before the drop-list filter ran. Corrected in the verification tables in SPEC-T12.md. Total dollars and EGI/EBITDARM unaffected — that one row was already routed to `Depreciation — EXCLUDED` either way.

**openpyxl side effects on save** (known limitations, no formula impact): conditional formatting rules dropped, data validation rules dropped. Both are visual/structural only. Mentioned here for traceability; same limitation as RR's existing T12 paste flow.

**RR-side sheets untouched.** `Rent Roll Input`, `Rent Roll Recon`, `T12 Analytics`, `UW Output`, `RR_Calc` were not modified by the migration. RR v1.11.0 functionality preserved.

**Re-running the migration is safe with caveats** — script checks pre-state and warns rather than blindly applying edits. If run on an already-migrated workbook, it would emit warnings on every batch. Idempotent on Description_Map duplicate removal, named ranges, helper col, and label-row inserts; the row-shift in Monthly Trending is the one batch that would not be idempotent, so don't re-run on already-migrated workbooks without checking.

#### Template v0.1.4 — Monthly Trending fixes

The architectural Path B fix (template v0.1.3) made T12 Raw Data work correctly, but Monthly Trending had pre-existing bugs that were exposed once aggregation started flowing real numbers. Five fixes:

- **R10 (Physical Vacancy)** and **R11 (Loss to Lease)** — dropped `ABS()` wrapper. These rows now flow through with their original signs (negative when reported by source). Returns 0 when source value is missing instead of `""`, so downstream addition in EGI works without errors.
- **R20 (EGI)** — extended formula from `=B8+B15+B16+B17+B18+B19` to `=B8+B10+B11+B15+B16+B17+B18+B19`. Self-applying rule per user direction: when Vacancy/L2L lines are present in source, base rent is treated as gross and these get subtracted (via negative signs); when absent, they evaluate to 0 and contribute nothing (base rent is treated as net). Verified: Salem (no V/L2L) EGI = $2,201,865; Briar Glen (L2L = -$139K) EGI = $3,763,229.
- **New row R53 (`Auto Expense`)** — inserted between Auto insurance (R52) and Fire / security monitoring (now R54). All rows R53-R68 shifted to R54-R69. Done via manual read-row → write-row pattern after openpyxl's `insert_rows()` proved unreliable (it shifted col A labels but didn't update formula references in shifted rows; first attempt corrupted the workbook).
- **R64 (Lease / ground lease)** — replaced `=0` placeholder with proper INDEX/MATCH lookup against `T12 Raw Data!Lease / ground lease` row.
- **R65 (Total non-labor opex)** — both B and N columns rebuilt to sum full range R40:R64 (25 rows). Pre-existing N-column bug (was stopping at N59) is now fixed; this had been understating Salem's Total non-labor opex by ~$100K and Briar Glen's by ~$261K.
- **R66, R68, R69** — references shifted to point at correct rows post-Auto-Expense insert. R66 (TOTAL OPEX) now `=B38+B65`. R68 (EBITDARM) now `=B20-B66`. R69 (EBITDAR) now `=B68-B67`.
- **N-column self-references R54-R63 and R67** — fixed off-by-1 bug introduced during the row shift. Each row's T12 total now correctly sums its own row's monthly values.

End-to-end verification: every row passes audit. All self-sum N-column formulas reference their own row. All cross-row formulas (Total base rent, EGI, Total direct labor, etc.) have matching B-column and N-column references.

#### Template v0.1.3 — Path B architectural fix

The original `T12 Raw Data` SUMIF formulas hardcoded raw description strings (e.g., `SUMIF(..., "ALZ Base Rate Income", ...) + SUMIF(..., "Memory Care Base Rate Income", ...) + SUMIF(..., "MC Base Rate Income", ...)`). Adding new operator vocabulary to `Description_Map` made T12 Input col P resolve correctly but did NOT make T12 Raw Data aggregate the new descriptions — Raw Data's hardcoded list didn't include them. Path B replaces this with a label-based aggregation that picks up new vocabulary automatically:

- **New helper column `T12_Calc!N`** (500 rows) — formula `=IFERROR(INDEX(DescMap_Label, MATCH(A{r}, DescMap_Description, 0)), "")` per row. Pre-computes the Label for every row's description.
- **Rewrote 612 SUMIFs in T12 Raw Data** (51 label rows × 12 monthly cols) from chained-against-raw-descriptions to single `SUMIF(T12_Calc!$N$1:$N$500, "<label>", T12_Calc!$<month>$1:$<month>$500)`. Result: any new operator vocabulary added to `Description_Map` flows through aggregation automatically — no formula maintenance ever.
- **Removed duplicate `Auto Expenses` entry** from `Description_Map` (kept R125 → `Auto Expense`, deleted R152 → `Office, admin & G&A`). The MATCH function returns first hit so R125 was already winning; deletion just cleaned up dead-code data.
- **Added `Auto Expense` row to T12 Raw Data** (at R57). Salem's `Auto Expenses` and Briar Glen's `Auto and Mileage Expense` and `Bus/Shuttle Service` now have an aggregation home.
- **Added `Lease / ground lease` row to T12 Raw Data** (at R58). Future-proofs against ground-leased-property T12s; no current operator uses this label, but the orphan-label leakage is gone.

End-to-end verification confirms zero dollar leakage on either format. Salem: $4,117,468 in source = $4,074,180 to operating + $43,289 to Depreciation EXCLUDED. Briar Glen: $8,306,658 in source = $8,310,006 to operating + $-3,349 to Depreciation EXCLUDED.

#### Template v0.1.2 — Briar Glen vocabulary mapping

Added 82 new entries to `Description_Map` (rows 235-316) covering MRI/Briar Glen vocabulary. Hard constraint enforced throughout: only the existing 54 Labels used, no new categories created. 8 entries auto-skipped because the descriptions already exist in `Description_Map` with the correct labels (`Late Charges`, `Referral Fees`, `Payroll Taxes`, `Workers Comp Insurance`, `Maintenance Supplies`, `Gas`, `Water`, `Real Estate Taxes`).

Mapping decisions made across 6 batches (Revenue, Administration, Property Mgmt + Marketing, Labor & Benefits, Maintenance + Food + Operating + Resident Services, Common Area + Turn + Utilities + Insurance + Taxes). Notable judgment calls:

- **Holiday Pay → `Overtime wages`** (per user direction; flagged that PTO would be more conventional).
- **Marketing labor → `Administrative labor`** (keeps Labor/Non-Labor section split clean; alternative `Sales, adv. & marketing` would have crossed sections).
- **Corporate Taxes → `Depreciation — EXCLUDED`** (treats this as non-operating; excluded from NOI calculation).
- **Approach C for Labor section:** department-first for Salaries (G&A → Admin labor, Nursing → Care staff, etc.), pay-type for Overtime/PTO/Holiday/Bonus (collapsed across departments).

Description_Map went from 229 entries to 311 entries (82 new + 229 existing - 0 removed). The duplicate `Auto Expenses` removal in v0.1.3 brought it to 310 effective entries.

#### Template v0.1.1 — GL-detect formula change + row 11 headers + instruction rewrite

Three changes preparing the template for both Yardi and MRI formats:

- **Col P GL-detect formula** changed from `IF(ISNUMBER(VALUE(TRIM(A12))),...)` to `IF(TRIM(B12)<>"",...)`. Account number column becomes optional (Yardi populates it, MRI doesn't). All 500 col P formulas (P12:P511) rewritten with the new test.
- **Row 11 unmerged** (was a single banner cell `↓ Paste your T12 starting at A12`) and populated with column headers: A=`Account #`, B=`Description`, O=`T12 Total`, P=`Coverage Check`. Cols C-N intentionally blank — writer fills these per upload with detected month labels.
- **Row 4-7 instructions rewritten** to reflect the new app-driven workflow (upload to Streamlit, use in-app matcher, download). Replaces the old "Ctrl+C, Ctrl+V into A12, manually fix UNMATCHED" workflow.
- **Row 9 layout note updated** to describe the new column structure with optional Account #.

#### Template v0.1.0 — Dynamic named ranges

First template substrate work. Added two workbook-scoped defined names:

- `DescMap_Description` = `Description_Map!$A$5:INDEX(Description_Map!$A:$A, MAX(5, COUNTA(Description_Map!$A:$A)+4))`
- `DescMap_Label` = `Description_Map!$B$5:INDEX(Description_Map!$B:$B, MAX(5, COUNTA(Description_Map!$A:$A)+4))`

Rewrote 500 col P formulas in `T12 Input` from hardcoded `Description_Map!$A$5:$A$284` references to the named ranges. Result: `Description_Map` can grow indefinitely without needing formula maintenance. Replaces the original "50-row headroom" approach with proper dynamic ranges.

The `MAX(5, ...)` floor prevents Excel from rejecting an empty-data-area range (`A5:A4` is invalid; `MAX(5,0+4)=5` keeps it valid even pathologically).

### Architectural decisions (implemented in v0.1.0 code)

These pin down the implementation scope before code is written:

- **Format-registry pattern.** Each supported T12 format is a class with `detect()` and `extract()` methods. Adding a format is a small change. v0.1.0 ships with `YardiIncomeToBudgetFormat` and `MriR12mincsFormat`.
- **Three parser drop-rules**, applied in order: drop rows with no $ value; drop rows whose description matches a grand-total pattern (`TOTAL `, `NET `, `EBITDA`, `EBITDAR`, `EBITDARM`, exact match `NET INCOME` / `NET OPERATING INCOME`); drop rows in an explicit drop-list (initially: `Other Non Operating Revenue & Expense`).
- **UNMATCHED in-app matching with write-to-Description_Map.** Interactive Streamlit form lets user map unmatched descriptions (Label / Section / CareType / Flag) and writes them to the destination workbook's `Description_Map` on download. Mappings persist for re-uploads. Approach A from Interpretation A vs. B decision earlier in the chat.
- **Single combined download button.** "Analyzer with both data" — replaces v1.7.0's RR-only Analyzer paste. Disabled until rent roll AND Analyzer AND raw T12 are uploaded, AND all UNMATCHED are mapped. The standalone Normalized Rent Roll download (existing) stays.
- **Separate writer module** (`t12_normalizer_writer.py`) — does not extend the existing `t12_writer.py` (which writes RR data). Keeps boundaries clean. Naming-history note in SPEC.
- **Parser writes month labels to row 11.** C11:N11 of `T12 Input` get filled with normalized `MMM YYYY` labels detected from each format's source row (Yardi row 9, MRI row 11). Format-specific extraction, uniform output.
- **Description_Map ships pre-populated.** v0.1.0 baseline is 310 effective entries (Yardi-aware + MRI-aware vocabulary). Future operators add their delta via the in-app matcher.

### Sequencing note (resolved)

Track 1's Path B (Analyzer-as-paste-target rename) shipped as RR v1.11.0 in commit `9cb4edd`. The T12 chat resumed after that, with template work landing in subsequent commits during the kickoff chat. Code work is the next deliverable.

### Documentation discipline

- This changelog and `SPEC-T12.md` join `SPEC-RR.md` and `CHANGELOG-RR.md`.
- `T12_NORMALIZER_KICKOFF.md` is superseded by `SPEC-T12.md`. Move to `docs/archive/` once v0.1.0 ships, or earlier if root tidiness matters.
- `README.md` to be updated when v0.1.0 ships: top-level "Repo contents" section explaining the two tracks + the Analyzer destination.

---

## How the version stream relates to Track 1

RR and T12 evolve independently. A change to RR (e.g., adding a third operator format) bumps RR only. A change to T12 (e.g., adding RealPage support) bumps T12 only. A change to shared infrastructure (`app.py` UI, `period_date.py`, `requirements.txt`) bumps whichever track the change primarily serves; if it serves both equally, bump both.

Each track's version surfaces in the UI pill and in the `Run_Info` tab of any output that track touched.

The "one track at a time" principle means a chat is RR-only OR T12-only OR explicitly cross-cutting — never accidentally cross-cutting. If a chat finds itself editing both `SPEC-RR.md` and `SPEC-T12.md`, stop and confirm whether that's intentional cross-cutting work or scope creep.
