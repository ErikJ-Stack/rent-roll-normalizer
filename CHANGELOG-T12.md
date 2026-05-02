# Changelog — T12 Normalizer

All notable changes to the T12 Normalizer (Track 2). Independent version stream from the Rent Roll Normalizer (Track 1, currently v1.11.0). This changelog covers T12 work only — see `CHANGELOG-RR.md` for RR releases.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a T12-related chat, add an entry here in the same commit.

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
