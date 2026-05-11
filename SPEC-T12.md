# T12 Normalizer — Specification

> **For future chats:** This document is the source of truth for the T12 Normalizer (Track 2). Read it before making changes to any T12-related code or templates. Update it in the same commit as any change.

**Live app:** https://rrnormalizer.streamlit.app/ (shared with RR Normalizer)
**Repo:** https://github.com/ErikJ-Stack/rent-roll-normalizer (shared, public)
**Owner:** Erik J (`Erikjayj@gmail.com`, GitHub: `ErikJ-Stack`)
**Stack:** Python · Streamlit · pandas · openpyxl · Streamlit Community Cloud (free tier)
**Current version:** v0.2.1 (2026-05-11) — Track 2 follow-up to substrate v0.1.8: `t12_normalizer_writer.populate_t12_input()` now stamps the property name (derived from the uploaded T12 filename via the shared `property_name.derive_property_name()` helper) into `T12 Input!A10`. Prior v0.2.0 (2026-05-08): `BrokerFinancialSummaryFormat` + Cluster B (sign-convention guards, partial-year T12 detection + optional annualization). Template substrate at v0.1.8 (Branch 3 analytical coverage — T12 Analytics B2/E2 plumbing, 5 chart objects + conditional notes on T12 Analytics K1:V44, Rent Roll Recon B2 latest-date default + DV, IL deep-dive section K, MC auto-detect section L; 2026-05-11).
**Status:** Released. `t12_normalizer.py` + `t12_normalizer_writer.py` shipped. End-to-end verified against Yardi (Salem, 73 GL), MRI (Briar Glen, 91 GL), and Broker (Homestead Pensacola + March_2026, 101 GL each) — **0 UNMATCHED on all four fixtures** at v0.1.7 substrate. Homestead reconciles to broker-published NOI of $1,411,323.58 to the penny. Salem / Briar Glen substrate-side EGI / EBITDARM unchanged from v0.1.1 verified figures (workbook formulas untouched).

---

## What this project does

A senior-housing T12 normalization tool. Companion to the Rent Roll Normalizer in the same repo. Analysts upload a raw T12 export from any property management system; the app cleans it and writes GL detail rows into the user's analysis workbook.

The T12 Normalizer never writes a standalone T12 workbook of its own. The user's analysis workbook (the Analyzer or the standalone T12 Normalizer template) already contains the analyst views (Raw Data, Monthly Trending, Description_Map, etc.) — our job is to feed it clean rows.

---

## Relationship to other modules in this repo

This repo houses two normalizer modules and one combined output:

- **Rent Roll Normalizer** (Track 1) — see `SPEC-RR.md` / `CHANGELOG-RR.md`. Currently v1.11.0.
- **T12 Normalizer** (Track 2) — this document. Currently v0.1.0 (first code release).
- **Combined Analyzer output** — both modules write into the user-provided `ALF_Financial_Analyzer_Only.xlsx` workbook. RR data → `Rent Roll Input!A7+`. T12 data → `T12 Input!A12+`. The reconciliation, monthly trending, and UW Output staging all live in the workbook's formulas, not in our Python.

`app.py` orchestrates both. A single run can produce: standalone Normalized RR workbook + populated Analyzer (RR + T12 data both written) when both required uploads are present.

"Track 2" / "Track 1" is project-management vocabulary, not anything in the codebase.

### Module naming history (read this before grepping)

There are two writer modules in this repo. They handle different inputs and write to different sheets of the same destination Analyzer workbook:

- **`analyzer_rr_writer.py`** — Track 1 module. Writes **rent roll** data (Condensed_RR) into the `Rent Roll Input` sheet of the Analyzer. Was named `t12_writer.py` until 2026-05-10 (when the destination workbook was a standalone T12 intake template — predates the bundled-Analyzer-by-default flow that shipped in RR v1.12.0).
- **`t12_normalizer_writer.py`** — Track 2 module (shipped in v0.1.0). Writes **T12 GL detail** data into the `T12 Input` sheet of the Analyzer.

The exception class `T12CapacityError` exported by `analyzer_rr_writer.py` retains its old name to keep the rename surgical; could be renamed to `AnalyzerRRCapacityError` in a follow-up. The companion `t12_translator.py` (Track 1; translates Condensed_RR vocabulary into the Analyzer's data-validation vocabulary) is the natural next rename target — `analyzer_rr_translator.py` — if the symmetry becomes important. See `CLAUDE.md` "Module naming gotcha" for the full file-by-file disambiguation.

---

## Architecture

Inherits the deploy loop from `SPEC-RR.md`:

```
Local Windows machine (C:\Users\erikj\Downloads\rent_roll_app)
        │  git push
        ▼
GitHub: ErikJ-Stack/rent-roll-normalizer
        │  auto-rebuild
        ▼
Streamlit Cloud (free tier)
        │
        ▼
User browser at https://rrnormalizer.streamlit.app/
```

Same auto-rebuild on push (~30-60 sec). Same Ctrl+Shift+R hard refresh. Same Streamlit caching gotcha — when behavior diverges between local verified runs and live, reboot the app from share.streamlit.io before debugging.

---

## File inventory

| File | Status | Purpose |
| --- | --- | --- |
| `t12_normalizer.py` | shipped in v0.1.0 | T12 parser. Reads raw T12, returns clean GL detail DataFrame plus detected month labels, plus a list of unmatched descriptions (looked up against the destination workbook's `Description_Map`). Format-registry pattern (Yardi + MRI extractors at v0.1.0). |
| `t12_normalizer_writer.py` | shipped in v0.1.0 | Loads user's Analyzer / T12 Normalizer template. Writes A:O at row 12+ of `T12 Input` sheet, plus detected month labels at C11:N11. Preserves col P formula (P12:P511), helper col N in `T12_Calc`, named ranges, and all other tabs. Idempotent re-run. Capacity 500 GL rows; raises `T12NormalizerCapacityError` if exceeded. Optionally appends UNMATCHED-resolution mappings to `Description_Map` (row 317+ on a fresh v0.1.4 substrate). Adds a `Run_Info` tab with T12 version + run timestamp + source filename + format detected. |
| `app.py` | shared (v0.1.0 adds T12 hooks) | Gained optional Raw T12 uploader, an UNMATCHED interactive matcher (Streamlit form with Label / Section / CareType / Flag dropdowns), and a single combined download button "Analyzer with both data". Version pill shows `RR v1.11.0 · T12 v0.1.0`. |
| `period_date.py` | shared (existing, reused as-is) | Filename → period date extraction. Same six patterns work for T12 filenames. |
| `ALF_Financial_Analyzer_Only.xlsx` | template at v0.1.4 (verified) | Master Analyzer. Migrated to v0.1.4 substrate on 2026-05-02 (commits 612c2ac and 13c9736). |
| `tools/migration/migrate_analyzer.py` | one-shot, archived | Applies the five template iterations to a pre-v0.1.0 Analyzer. Used for the master Analyzer migration; runs warnings rather than blind re-applies if executed against an already-migrated workbook. |
| `tools/migration/verify_e2e.py` | one-shot, archived | Pre-v0.1.0 verification harness with throwaway extractors that established the 72 / 91 GL targets. Superseded by the format-registry in `t12_normalizer.py`; retained as a sanity-check reference. |

Filenames are conventions; rename in code if the implementation calls for it, then update this table.

---

## Template substrate (what v0.1.0 ships with)

The destination workbook is a critical part of the v0.1.0 release. The template went through five iterations of substrate-level fixes during the kickoff chat before any code was written. **All template fixes are part of the v0.1.0 ship scope**, not separate releases. The template iterations:

- **Template v0.1.0** — Added two dynamic named ranges (`DescMap_Description`, `DescMap_Label`) so `Description_Map` can grow without needing to edit the col P formula. Rewrote 500 col P formulas to use the named ranges.
- **Template v0.1.1** — Changed col P GL-detect formula from `ISNUMBER(VALUE(TRIM(A12)))` to `TRIM(B12)<>""`. This makes account-number column optional (Yardi populates it, MRI doesn't). Unmerged row 11 to add column headers (`Account #`, `Description`, `T12 Total`, `Coverage Check`). Rewrote rows 4-7 instructions to reflect the new app-driven workflow. Updated row 9 layout note.
- **Template v0.1.2** — Appended 82 new MRI-vocabulary entries to `Description_Map` (rows 235-316). Briar Glen GL descriptions now resolve to existing labels. Hard constraint: no new Labels invented, only existing ones used.
- **Template v0.1.3** — Architectural Path B fix. Added helper col N to `T12_Calc` (`=IFERROR(INDEX(DescMap_Label, MATCH(A{r}, DescMap_Description, 0)), "")` per row). Rewrote 612 SUMIF formulas in `T12 Raw Data` (51 label rows × 12 month columns) from chained `SUMIF + SUMIF + SUMIF` against hardcoded raw descriptions to single `SUMIF(T12_Calc!N, label, T12_Calc!<month>)`. Result: any new operator vocabulary added to `Description_Map` flows through aggregation automatically. Also: removed duplicate `Auto Expenses` entry from `Description_Map` (kept R125, deleted R152). Added `Auto Expense` and `Lease / ground lease` rows to `T12 Raw Data` to fix orphan-label leakage.
- **Template v0.1.4** — Monthly Trending fixes. R10/R11 (Vacancy, L2L) drop ABS and return 0 when source is empty. R20 (EGI) extended to `=B8+B10+B11+B15+B16+B17+B18+B19` — self-applying rule: if Vacancy/L2L lines are present in source, they're subtracted (treating base rent as gross); if absent, they evaluate to 0 (treating base rent as net). New row R53 (`Auto Expense`) inserted with full INDEX/MATCH formula, all rows R53-R68 shifted to R54-R69, all section-totaling formulas updated to point at the new row positions. R64 (Lease) replaces `=0` placeholder with proper INDEX/MATCH. R65 sum range rebuilt to span B40:B64 (covers all 25 non-labor rows including new Auto and now-functional Lease). N-column formulas all corrected to self-reference correctly post-shift.
- **Template v0.1.6** — Workbook-side optimization round per `OPTIMIZATION-DECISIONS.md`. Added `Cover` sheet (first tab, visible — property name, version pills, links, About) and `Workbook Health` sheet (last tab, hidden — Map / Validation / Diagnostics sections). Per-sheet anchor cells at `AZ1:AZ5` on all 13 sheets (purpose / category / visibility / version / notes) feed the Map section. 5 named ranges added (`RR_Period_Date`, `T12_Period_Date`, `RR_Input_Data`, `T12_Input_Data`, `Property_Name`); `T12 Analytics!B2` now `=Property_Name`. Cluster A correctness fixes: `Rent Roll Recon!H20` `#NAME?` rewritten with chunked literals (was `_xlfn._LONGTEXT` from over-255-char string literals); `UW Output!R29` (Bonus wages), `R57` (Bad debt), `R61` (Lease) sibling-pattern fills + R61 indent. Light cell comments on 5 hardest formulas. Migration via `migrate_to_v016.py` (idempotent). **Deferred to v0.1.7+:** `T12 Analytics!R102` lease formula (still `=0` placeholder; would rewire an existing aggregator); `T12 Raw Data` N501 vs N500 SUMIFS cosmetic mismatch. Cluster B (sign guards + partial-year T12 — code-side) deferred to a separate Track 2 chat per the one-track-at-a-time principle.
- **Template v0.1.7** — Workbook-side companion to T12 code v0.2.0 (`BrokerFinancialSummaryFormat` + Cluster B). Fixed `T12 Analytics!E102` (Lease / ground lease) by replacing `=0` placeholder with `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`; sibling `F102` set to `=E102`. Swept 636 SUMIFS cells in `T12 Raw Data` from `T12_Calc!$X$1:$X$501` to `$X$1:$X$500` (cosmetic; T12_Calc data area is 500 rows). Added `Workbook Health!A30` V8 row "T12 month coverage" — counts populated month labels in T12 Input C11:N11; ✓ when 12, ⚠ otherwise. Appended **99 prefixed Description_Map entries** (Homestead vocabulary): mechanically derived from the v0.1.5 populated_analyzer's per-banner mappings, all routing to the existing 54-Label closed vocabulary. Substrate version stamp v0.1.6 → v0.1.7 across `Cover!B8` and all 13 anchor `AZ4` cells. Migration via `migrate_to_v017.py` (idempotent). **End-to-end verified:** all four reference fixtures parse with **0 UNMATCHED** at v0.1.7. Description_Map row count grows 311 → 410.
- **Template v0.1.8** — Branch 3 (analytical coverage) per `OPTIMIZATION-DECISIONS.md` decisions D-15 through D-22. Workbook-only — no Track 1/2 code changes. (a) **Property name + period plumbing:** reserved single-cell property-name value targets at `Rent Roll Input!A3` and `T12 Input!A10` (writer-populated; analyst-paste OK until writer follow-ups land — no separate labels); rewired `T12 Analytics!B2` to 3-priority formula (`Rent Roll Input!A3` → `T12 Input!A10` → `Property_Name` Cover!B5); installed `T12 Analytics!E2` rightmost-populated-month formula over `T12 Input!C11:N11` (named `T12_Period_Date` now resolves). (b) **5 chart objects** on `T12 Analytics!K1:V44`: V1 occupancy stacked column (IL/AL/MC × status), V2 rate-band histogram (3-series clustered), V3 payer-mix doughnut, V4 12-month revenue trend line, V5 AL acuity doughnut. Hidden helper at `K46:V52` (rate buckets) and `K53:V54` (monthly revenue from `SUMIFS('T12 Raw Data'!F:Q, A:A, "Revenue")`). (c) **5 conditional notes** at `K15`/`K30`/`P15`/`P30`/`K45` — formula-driven context that updates with data. (d) **Rent Roll Recon!B2** set to `=LOOKUP(9.99E+307,RR_Calc!A2:A13)` for latest-period default + data validation list dropdown sourced from same range. (e) **Section K** appended at Rent Roll Recon rows 86-100 — IL Unit-Type Mix, Size & Rate Dispersion (Studio / 1BR / 2BR / Cottage / Other × Count / % / Avg-Min-Max rate / Avg sqft / $-per-sqft) plus rate-CV proxy and conditional dispersion note. (f) **Section L** appended at rows 102-117 — MC Care Structure auto-detect (Flat-rate / Tiered / FFS pattern detection from distinct K-column values; substring-mapped tier rows; care-charge-to-base-rent ratio; pattern-specific conditional note). Substrate version stamp v0.1.7 → v0.1.8 across `Cover!B8` and all 13 anchor `AZ4` cells. Migration via `migrate_to_v018.py` (10 ops, 17-check verify, idempotent — gate checks both `Cover!B8` AND that T12 Analytics!B2 references A3/A10, so the migration safely re-applies on a v0.1.8 first-pass file). **Opens carry-forwards:** Track 1 follow-up (RR `writer.py` stamp `Rent Roll Input!A3`) and Track 2 follow-up (`t12_normalizer_writer.py` stamp `T12 Input!A10`) to populate the new property-name source cells programmatically.
- **Template v0.1.5** — Added new revenue Label `2nd Person Revenue`. Inserted as new row in `T12 Raw Data` at R15 (before "Other community revenue") with `=SUMIF(T12_Calc!$N$1:$N$501,"2nd Person Revenue",T12_Calc!$B$1:$B$501)` formulas across F:Q and `=SUM(F15:Q15)` at R. Inserted as new row in `Monthly Trending` at R19 (before "Other community revenue") with `=IFERROR(INDEX('T12 Raw Data'!F:F,MATCH("2nd Person Revenue",'T12 Raw Data'!B:B,0)),0)` formulas across B:M and `=SUM(B19:M19)` at N. Existing rows R19+ shifted down by 1 (Other community revenue → R20, EFFECTIVE GROSS INCOME → R21, all downstream subtotals shift accordingly). EGI formula at new R21 rewritten to `=B8+B10+B11+B15+B16+B17+B18+B19+B20` — adds the new R19 (2nd Person Revenue) to the sum without disturbing R8 (Total base rent) which stays clean. T12 Analytics formulas at E38/H38/E39/E40 patched to follow Physical Vacancy and Loss to Lease as they shifted from R55/R56 → R56/R57. Migration applied via `migrate_to_v015.py`. Closed Label vocabulary grows from 54 → 55. Surfaced as a need on the Homestead Pensacola broker file (2026-05-04) where second-person revenue was reported as separate line items by care type, but the substrate had no Label to receive it without inflating Base rent. **Per-bed base rate calculations (Base rent ÷ ADC) now stay clean.** Three Homestead `Second Persons Revenue` description entries (one each for IL/AL/MC) all map to the single `2nd Person Revenue` Label — preserving source-text fidelity in T12 Input while collapsing to one Label in T12 Raw Data and Monthly Trending.

### Verified end-to-end at template v0.1.4

Numbers reflect parser v0.1.1 (Salem Management Fees fix). v0.1.0 numbers are preserved in CHANGELOG-T12 [0.1.0] for historical reference.

| Format | GL detail rows | Mapped | UNMATCHED | EGI | EBITDARM | EBITDAR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Yardi (Salem) | 73 | 73 | 0 | $2,201,865 | $329,550 | $197,970 |
| MRI (Briar Glen) | 91 | 91 | 0 | $3,763,229 | -$595,387 | -$783,549 |

Both formats reconcile to the penny: total $ in source GL = total $ aggregated to operating P&L + total $ routed to `Depreciation — EXCLUDED`. No silent leakage.

---

## Parser data flow

### Stage 1 — Raw T12 → Format detection

The parser uses a **format-registry pattern**: each supported format is a class with a `detect(workbook)` method (returns True/False) and an `extract(workbook)` method (returns clean GL DataFrame + month labels). Adding a new format is a one-class-plus-one-list-entry change.

**Registered formats (v0.1.0):**

- **YardiIncomeToBudgetFormat** — Detects sheet whose name doesn't match other formats and where col A row 11+ contains numeric account numbers (≥3 hits — heuristic for format detection only, not row-level filtering). Body starts at row 11. Months in cols C-N (12 of them), T12 total in col O. Reads month labels from row 9 (e.g., `02/28/2025`) and normalizes to `MMM YYYY` format. Account # is preserved when present in col A (most GL rows) but **not** required for inclusion — Yardi reports some single-line expenses as banner-style rows with no account number; the three drop-rules below filter section headers and subtotals on their own. (v0.1.0 had a strict account-# pre-filter that silently dropped Salem's $131,579.65 Management Fees line — fixed in v0.1.1.)
- **MriR12mincsFormat** — Detects a sheet named `MRI_R12MINCS`. Body starts at row 14. No account numbers. Description in col A, months in cols B-M, T12 total in col N. Reads month labels from row 11 (e.g., `01/25`) and normalizes to `MMM YYYY` format.
- **BrokerFinancialSummaryFormat** (v0.2.0) — Detects sheets whose A4 cell matches `Historical Perform[ance]` (case-insensitive); when multiple sheets match, parser picks the first. Body starts at row 5. Walks row 4 right-to-left to find the **rightmost contiguous monotonic monthly run** (≤12 cells where each cell is exactly 1 column AND 1 calendar month after the previous). For Homestead's multi-section Summary sheet that picks cols AB:AM (the T12 block); for March_2026 single-sheet it picks B:M. Pads on the left with empty labels for partial-year (<12) runs. **Banner-prefix disambiguation**: a row is a "banner" when col A has text and **all 12 monthly cells are truly None** (not zero); banners track the most-recent section name. The first banner matching `Revenue` / `Revenues` establishes top-level — earlier preamble banners (Census / ADC / Room Rates) are dropped along with their GL rows. **Subtotal-pop**: when a `Subtotal,` row drops via Rule 2, the current sub-banner pops back to the top-level Revenues banner so siblings (`Concessions`, `Respite Revenue`) emit unprefixed. **Post-P&L cutoff**: parser stops on banners matching `Non-Operating` / `Wages Analysis` / `Payroll Summary` (drops below-NOI items + broker analytical sections). T12 total is computed as `sum(monthly)`; any "Totals" column in the source is ignored. Standard signs.

If no format detector matches, the parser raises `UnknownT12FormatError` with the sheet name and a hint that this format isn't yet supported.

### Cluster B (v0.2.0) — sign-convention guards + partial-year detection

After format-specific extraction, two passes run before UNMATCHED detection:

1. **Partial-year detection** (`_count_populated_months`). Counts how many of the 12 month columns have at least one non-zero value across all GL rows. `T12ParseResult.populated_months` carries the count. A full-year T12 is `12`; a 6-month T12 reports `6`.
2. **Optional annualization** (`parse_t12(..., annualize_partial_year=True)`). Default `False` — the app surfaces a partial-year warning instead. When the caller opts in via the sidebar checkbox **and** `populated_months < 12`, the parser scales every row's monthly + total by `12 / populated_months`. `T12ParseResult.was_annualized` is set so the UI can label the result. Annualization assumes flat seasonality.
3. **Sign-convention guards** (`_check_sign_convention`). Returns warnings for descriptions whose **suffix** (after the most-recent `" | "` separator) contains `CONCESSION` and whose total > 0. Suffix-only matching avoids false positives when a banner contains a relevant keyword (broker banner `Management Fee & Bad Debt` no longer fires on its child rows). Vacancy / L2L / Bad Debt are intentionally NOT in the guard set: those are operator-discretionary signs (contra-revenue vs. expense), and the substrate handles either polarity at the Monthly Trending level.

### Stage 2 — GL detail extraction (per format)

Each format's `extract()` walks the body rows and produces clean GL detail. Three filter rules, applied in order:

1. **Drop rows with no $ value.** A row passes only if at least one of the 12 monthly columns or the T12 total column is non-zero numeric. Filters out blank spacer rows and section-banner rows that have a description but no values.
2. **Drop rows whose description matches a grand-total pattern.** Patterns: descriptions starting with `TOTAL ` (case-insensitive), `NET `, `EBITDA`, `EBITDAR`, `EBITDARM`, or matching `NET INCOME`, `NET OPERATING INCOME` exactly. Filters out subtotals embedded in the source like `Total Effective Gross Rents` and `NET OPERATING INCOME`.
3. **Drop rows whose description appears in the explicit drop-list.** Currently: `Other Non Operating Revenue & Expense` (a Yardi non-operating line that's small enough not to need its own Label, and clearly excluded from operating analysis), `Non-Operating Expenses` (the Yardi banner-style subtotal that repeats the section header text and would double-count rows already captured as GL detail — added in v0.1.1). New non-operating descriptions added to this list when encountered.

After filtering, each remaining row is cleaned: TRIM applied to account # (col A) and description (col B); values passed through unchanged; sign convention preserved (revenue +, expense +, concessions -).

**Note on the Yardi extractor (v0.1.1).** Yardi GL rows usually carry a numeric account # in col A, but Yardi sometimes reports single-line expenses (e.g., Salem's `Management Fees` of $131,579.65 between EBITDARM and EBITDAR) as section-banner-style rows with no account number. The Yardi extractor does not pre-filter on account # presence; instead, the three drop-rules above are sufficient on their own. Account # is preserved when present and stored as `""` when absent. v0.1.0 had a strict "must have numeric account #" pre-filter that silently dropped Salem's management fee — fixed in v0.1.1.

### Stage 3 — UNMATCHED detection (Python-side)

The parser reads the destination workbook's `Description_Map` sheet (col A = raw description, ~312 entries at v0.1.0). Each cleaned GL row's description is looked up against that list. Descriptions not present produce an UNMATCHED entry in the parser's return value.

The Python-side lookup avoids the openpyxl-can't-evaluate-formulas constraint and is deterministic. The destination workbook's col P formula remains the runtime source of truth (analyst sees `UNMATCHED` directly in the workbook).

### Stage 4 — Clean DataFrame → Analyzer paste

The writer loads the user's analysis workbook with openpyxl. Writes:

- A:O at row 12+ of `T12 Input` (15 columns: account #, description, 12 months, T12 total)
- C11:N11 with detected month labels (e.g., `Feb 2025` through `Jan 2026`)

Preserves col P formula on rows 12-511. All other sheets, formulas, named ranges, and the `T12_Calc` helper col N are untouched.

Idempotent re-run: clears any prior data in `T12 Input!A12:O511` and `T12 Input!C11:N11` before writing. Same pattern as `analyzer_rr_writer.py` for `Rent Roll Input!A7:S606`.

### Stage 5 — UNMATCHED interactive matching (in-app)

If any descriptions came back UNMATCHED, the UI surfaces a Streamlit form with one row per unmatched description. The user fills in:

- **Label** — combobox of the existing 54 Labels (free-text override allowed but discouraged)
- **Section** — dropdown: Revenue / Labor / Non-Labor / Excluded
- **CareType** — dropdown: `-` / IL / AL / MC (defaults to `-`)
- **Flag** — optional dropdown of existing 8 flag values, or blank

When the user clicks "Apply mappings & enable download," the new mappings are appended to the destination workbook's `Description_Map` sheet (rows 317+, since v0.1.0 ships with 316 entries). The Coverage Check formula picks them up via the dynamic named range. The "Analyzer with both data" download button enables.

On re-upload of the same operator format, those mappings persist in the user's downloaded Analyzer — no UNMATCHED on second run.

### What this module explicitly does NOT do (v0.1.0)

These are deliberate non-features. Each is documented here so the boundary is visible.

- **No vocabulary mapping in code.** The destination workbook's `Description_Map` sheet (~312 entries at v0.1.0) owns raw → Label mapping. Parser passes descriptions through after TRIM and reads `Description_Map` only for UNMATCHED detection. Two sources of truth would drift.
- **No standalone T12 analyst workbook.** The destination workbook already contains all analyst views.
- **No sign-flipping.** Both verified operators use the same convention (revenue +, expense +, concessions -). If a future T12 reverses, we'll handle it with a per-format rule.
- **No annualization.** Both verified samples are full T12s. Partial-year handling deferred until encountered.
- **No multi-property splitting.** Both samples are single-property. Multi-property exports out of scope.
- **No automatic mapping outside the in-app matcher.** UNMATCHED descriptions get mapped only when the user explicitly applies them in the matcher UI. No fuzzy matching, no "guess based on similar descriptions," no LLM-driven suggestions.
- **No code-side reconciliation.** RR-implied GPR vs. T12 collected revenue variance lives in the Analyzer's formulas (`Rent Roll Recon` tab), not in our Python. When variance flagging is needed in code, spin out Track 3 (`SPEC-Analyzer.md`).

---

## T12 file expected structure (destination)

The user's analysis workbook (`ALF_Financial_Analyzer_Only.xlsx` or the standalone `ALF_T12-_Normalizer.xlsx`) at template v0.1.4 contains a `T12 Input` sheet with this structure:

- Rows 1-9: title, instruction block (rows 4-7), layout note (row 9). Untouched by writer.
- Row 10: blank.
- Row 11: column headers. A=Account #, B=Description, C-N=blank (writer fills with month labels), O=T12 Total, P=Coverage Check.
- **Rows 12-511: data area** — A:O written by app, col P has the pre-filled Coverage Check formula on every row in this range (untouched).
- Rows 512+: empty. Beyond v0.1.0 capacity; would require workbook-side formula extension.

The col P formula at v0.1.4 is:
```
=IF(TRIM(B{r})<>"",IFERROR(INDEX(DescMap_Label,MATCH(TRIM(B{r}),DescMap_Description,0)),"UNMATCHED"),"")
```

The named ranges resolve dynamically:
- `DescMap_Description` = `Description_Map!$A$5:INDEX(Description_Map!$A:$A, MAX(5, COUNTA(Description_Map!$A:$A)+4))`
- `DescMap_Label` = `Description_Map!$B$5:INDEX(Description_Map!$B:$B, MAX(5, COUNTA(Description_Map!$A:$A)+4))`

Other sheets in the workbook (do not touch):
- `T12_Calc` (hidden helper) — col A trims `T12 Input!B`, cols B-M mirror monthly values from `T12 Input!C-N`, col M mirrors T12 total, **col N** is the Path B helper that looks up Label per row.
- `T12 Raw Data` (visible aggregator) — 51 Label rows, each with SUMIF formulas against `T12_Calc!N` (the helper col).
- `Monthly Trending` (visible aggregator) — pulls from T12 Raw Data via INDEX/MATCH on Label.
- `Mapping Review`, `Description_Map` (visible).
- The Analyzer additionally has `T12 Analytics`, `Rent Roll Recon`, `UW Output`, `Rent Roll Input`, `RR_Calc`.

Capacity: 500 GL rows max per run. Salem produces 73, Briar Glen 91. Plenty of headroom.

App raises `T12NormalizerCapacityError` with a clear message if exceeded.

---

## Verified formats

| Format | GL detail rows (after filters) | Period | UNMATCHED at v0.2.0 ship | Notes |
| --- | ---: | --- | ---: | --- |
| Yardi "Income to Budget" — Salem (Oaks at Salem Road) | 73 | T12 ending 1/31/2026 | 0 | AL-only. Indented hierarchy. Standard signs. Account numbers in col A on most GL rows but **not all** — Yardi reports some single-line expenses (e.g., Management Fees) as section-banner-style rows with no account number. The parser handles both via the three drop-rules. |
| MRI "R12MINCS" — Briar Glen | 91 | T12 ending 12/31/2025 | 0 | MC-focused. Flat structure. Standard signs. No account numbers (col A blank). 82 vocabulary entries added to Description_Map at v0.1.2. |
| Broker "Financial Summary" — Homestead Pensacola | 101 | T12 ending 3/31/2026 | 0 (at v0.1.7 substrate) | IL/AL/MC. Multi-section dashboard (CY totals + T12 + T6M + T2M + T1M). Parser detects via `Historical Performance` at A4, picks rightmost contiguous monthly run from row 4 (cols AB:AM here). Standard signs. Banner-prefixed descriptions for ambiguous lines (`Direct Care \| Payroll - Wages`). Reconciles to broker NOI $1,411,323.58. 99 vocabulary entries added at v0.1.7. |
| Broker "Financial Summary" — March 2026 (single-sheet) | 101 | T12 ending 3/31/2026 | 0 (at v0.1.7 substrate) | Same data as Homestead reference, single-sheet layout (`Sheet1`, monthly cols B:M). Confirms the parser's contiguous-monthly-run algorithm works on both multi-section and single-sheet variants of the broker format. |

More formats added as encountered. Each format earns a verification line plus any quirks documented under "Key decisions."

### Test fixtures — `Sample Files/` (local-only)

The four reference T12s above live in a repo-root directory `Sample Files/`. The directory is **gitignored** (the .xlsx files contain real property financials and must not be committed to a public repo). Canonical filenames consumed by `tools/verify_t12_v020.py`:

- `Salem Road T-12 1.31.26.xlsx`
- `Briar Glen T12 P&L Statement_2025.12.xlsx`
- `2026-03 Homestead Village Pensacola Financial Summary.xlsx`
- `Homestead - March 2026 T12.xlsx`

A new developer needs to populate `Sample Files/` from their own copy before running the verify harness. The Streamlit app accepts the same files as uploads; no hard dependency on the directory.

Run from repo root: `python tools/verify_t12_v020.py` — exits 0 with four `[OK] PASS` blocks when all fixtures are present and the parser is healthy.

---

## Key decisions captured during template work

These shaped the v0.1.0 ship and should not be relitigated without explicit reason.

- **Account number column is optional.** Col A populated for Yardi, blank for MRI. Description (col B) is the matching key, not account number.
- **Concessions stay negative as in source.** Pass-through. Adding the negative number to EGI = subtraction, which is correct for the two verified operators. If a future operator ships positive concessions, that becomes a v0.2.0 sign-normalization rule in the parser.
- **EGI = base + LOC + fees + concessions + respite + other + vacancy + L2L.** Self-applying rule: if Vacancy/L2L are 0 (Salem-style), they contribute nothing; if Vacancy/L2L are negative (operator-reported), they reduce EGI. Base rent is treated as gross when vacancy/L2L lines are reported, net when they're absent.
- **Holiday Pay maps to `Overtime wages`.** Decided during Briar Glen vocabulary mapping. Unconventional (most operators treat Holiday like PTO) but the user's call.
- **Marketing labor maps to `Administrative labor`** (not `Sales, adv. & marketing` which is Non-Labor). Keeps the Labor/Non-Labor section split clean.
- **Closed-vocabulary constraint.** Description_Map can grow with new raw descriptions, but the Label column has a fixed 54-entry vocabulary. Adding a new Label is a deliberate decision that requires also adding a new aggregation row to `T12 Raw Data` and `Monthly Trending`. Not done casually.
- **`Other Non Operating Revenue & Expense` (Yardi) and grand totals are dropped at parser-time, not mapped.** Cleaner than mapping to `Depreciation — EXCLUDED` because they don't belong in T12 Input at all.

---

## Known issues / limitations (v0.1.0)

1. **Two formats verified.** RealPage / AppFolio / manual GL exports not yet tested. Format-registry pattern makes adding them small.
2. **Single property only.** Multi-property T12s out of scope.
3. **Sign convention not normalized.** Both verified operators use the same convention; non-standard signs will need a per-format rule.
4. **No partial-year detection.** A 6-month T12 would silently land as 6 months in cols C-H with cols I-N blank. Downstream formulas would still SUM correctly, but no annualization.
5. **`Description_Map` updates land in user's downloaded workbook.** Mappings added via the in-app matcher persist only in that download. If the user starts a fresh deal from a clean template, they re-do the mapping for any vocabulary not in the v0.1.0 baseline.
6. **Conditional formatting drop on save.** Same openpyxl limitation as RR's existing T12 paste. Visual-only impact.
7. **Template-edit propagation — RESOLVED for the master Analyzer.** The user's master `ALF_Financial_Analyzer_Only.xlsx` was migrated to the v0.1.4 substrate on 2026-05-02 (see CHANGELOG-T12 entry). Any *other* pre-v0.1.0 populated Analyzers in circulation (e.g., from prior deals) still lack the named ranges, helper col N, and Path B SUMIF rewrites — those would need the same migration applied (`tools/migration/migrate_analyzer.py`), or to be rebuilt from a fresh template.

---

## How the analyst uses the app

1. Open https://rrnormalizer.streamlit.app/
2. Upload rent roll (existing, required).
3. Optional: upload mapping override workbook (RR-side; existing).
4. Optional: set Property Care Type default (existing).
5. Optional: upload ALF Financial Analyzer (existing as of v1.11.0).
6. **Optional: upload Raw T12 file** (NEW for T12 Normalizer).
7. App processes immediately.
8. **If any T12 descriptions were UNMATCHED**, an interactive matcher form appears with Label/Section/CareType/Flag dropdowns per unmatched description. User maps them and clicks "Apply mappings & enable download."
9. Click **Download Normalized Rent Roll** for the 6-tab analyst workbook (existing).
10. Click **Download Analyzer with both data** for the populated combined workbook (NEW). Disabled until: rent roll uploaded AND Analyzer uploaded AND raw T12 uploaded AND all UNMATCHED resolved.

**UI version pill convention:** when output combines RR + T12 work, both versions appear in the title row (e.g., `RR v1.11.0 · T12 v0.1.0`). When only RR ran, only RR's version. When only T12 ran (unusual without RR), only T12's. Each module's version surfaces in the `Run_Info` tab of any output workbook it touched.

---

## What's next after v0.1.0

- **v0.2.0+:** verify against a third T12 format (RealPage or AppFolio when a sample arrives). Format-registry pattern means this is small.
- **Future:** multi-property T12 splitter; sign-convention auto-detection; partial-year annualization.
- **When code-side reconciliation lands** (RR-vs-T12 variance flagging, `UW Output` extraction, multi-period comparison): spin out `SPEC-Analyzer.md` / `CHANGELOG-Analyzer.md` as Track 3 with its own version stream.

---

## Working principles (carried forward from Track 1)

Things that worked well on RR and confirmed during the T12 kickoff:

- Show proposed changes before building.
- Verify against real data at every step. Two formats verified before code; this is the right pattern.
- Bump version on every release. Template iterations during pre-v0.1.0 work are tracked here, not in version constants — those start at v0.1.0 when code ships.
- Honest about library limitations (e.g., openpyxl `insert_rows` doesn't reliably update formula references — surfaced and worked around).
- One track at a time. T12 chats only touch T12 files unless explicitly cross-cutting.

Things to avoid:

- Long unbroken chats spanning multiple features. Split by feature.
- Designing T12 logic from one operator format alone. The Briar Glen case proved this — Salem alone wouldn't have surfaced the no-account-number case, the embedded subtotal patterns, or the L2L line.
- Multi-file changes without verifying each landed.
- Cross-track edits in single-track chats.

---

## Maintenance protocol

**At the start of every T12-related chat:**

> "Read SPEC-T12.md and CHANGELOG-T12.md at https://github.com/ErikJ-Stack/rent-roll-normalizer. Then [task]."

**At the end of every chat that changes T12 code or template:**

> "Update SPEC-T12.md to reflect what changed. Add a CHANGELOG-T12.md entry. Bump T12 version constants if code shipped. Commit and push."

**Cross-cutting changes** (`app.py`, `period_date.py`, `requirements.txt`, the version-pill UI, anything that touches both tracks) reference both:

> "Read SPEC-RR.md, SPEC-T12.md, and README.md at https://github.com/ErikJ-Stack/rent-roll-normalizer. Then [task]."

**Mid-chat scope changes — stop and confirm.** If a T12 chat is asked to touch RR territory (or vice versa), the chat must stop and ask: *"This is [other track] scope. Open a fresh chat, or proceed knowing this becomes a cross-cutting session?"* Don't quietly drift. Drift produces sessions whose commits straddle both changelogs in ways that are hard to disentangle later — see `journal.md` 2026-05-06 for an example. Common drift triggers: a T12 chat being asked about `app.py` UI behavior, an RR chat being asked about `Description_Map` vocabulary or substrate edits, either chat being asked to "also update the README".

This keeps each chat's context bounded. RR-only chats don't drag in T12 history; T12-only chats don't drag in RR's quirks. Cross-cutting work is rare enough that the wider context is acceptable when it happens.
