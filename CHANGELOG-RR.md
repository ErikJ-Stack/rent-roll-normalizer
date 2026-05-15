# Changelog — Rent Roll Normalizer

All notable changes to the Rent Roll Normalizer.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a chat, add an entry here in the same commit.

---

## [1.17.5] — 2026-05-15

### Summary

**Closes UW-BACKLOG BL-0011** — function + class rename on `analyzer_rr_writer.py` to complete the Track 1 misnamed-T12-symbol cleanup that began with the file renames on 2026-05-10 (`t12_writer.py` → `analyzer_rr_writer.py`) and 2026-05-14 (`t12_translator.py` → `analyzer_rr_translator.py`, BL-0010). Bundled in one tidy-up PR with two cross-cutting docs items: BL-0013 (targeted README modernization) and BL-0014 (CLAUDE.md hygiene — drop stale Open carry-forwards bullets that had drifted, expand openpyxl quirk #4 with the qualified-range-endpoint trap from BL-0001).

No behavioral change. Pure refactor / docs.

### What changed (BL-0011)

- **`analyzer_rr_writer.py`**: `populate_t12()` → `populate_rr_input()`. Function now accurately describes what it populates (the Analyzer's `Rent Roll Input` sheet, not the `T12 Input` sheet). Mirrors the partner `populate_t12_input()` on `t12_normalizer_writer.py` which correctly does populate `T12 Input`.
- **`analyzer_rr_writer.py`**: `T12CapacityError` → `AnalyzerRRCapacityError`. Exception class name now matches the file rename done 2026-05-10.
- **`analyzer_rr_writer.py`**: parameter rename `t12_bytes` → `analyzer_bytes` and updated 2 sites of inline error/comment text from "T12 workbook" → "Analyzer workbook" — completes the cleanup at the function-body level too.
- **`app.py`**: import statement updated; 1 call site (`populate_rr_input(...)`); 1 except clause (`AnalyzerRRCapacityError`).
- **`CLAUDE.md`** "Module naming gotcha" table: `populate_t12()` → `populate_rr_input()` cell, T12CapacityError note removed (no longer "preserved as historical artifact"). Also added a forward-looking note on the surviving `translate_for_t12()` function name, explaining why it's left alone unless it becomes a confusion source.
- **`SPEC-T12.md`** module-naming-history paragraph: rewrites the "T12CapacityError retains its old name" sentence to record the BL-0011 rename.

Historical changelog / journal entries (this file's older sections, `CHANGELOG-T12.md`, `journal.md`) are NOT rewritten — they're records of what shipped at past versions, so they keep their original `populate_t12` / `T12CapacityError` references for accuracy. Same convention as the 2026-05-10 file rename.

### What changed (BL-0013 — README modernization)

- **Versions table** at top: bumped to RR v1.17.5 / 2026-05-15.
- **Data-capture coverage section**: was "At RR v1.16.0 + substrate v0.1.10 (cols A-AB)"; now "At RR v1.17.4 + substrate v0.2.2 (cols A-AH)". Adds the v0.1.13 per-fee ancillary cols (AC-AG) and the v0.2.2 Total Ancillary rollup (AH). Mentions the v0.2.1 5 finer T12 Labels closing the per-fee attribution gap on Section M, and the v1.17.4 parser-side Notes-rerouter for Homestead concession patterns.
- **Analyzer-at-a-glance section**: reframed as "Track 3 four-branch roadmap fully closed at substrate v0.2.0" (was "post-Branch 3"). Adds Section M description (per-fee capture-rate at rows 121-167) alongside Sections H/K/L. Adds `UW Export` sheet + Pre-Export Gate descriptions (substrate v0.2.0).
- **Versioning section**: substrate convention `v0.1.N` → `v0.X.Y` (substrate is now on the v0.2.x line).
- **UW-BACKLOG.md mention**: added to both the Versioning section (forward-looking changes pointer) and the Further Reading table.

### What changed (BL-0014 — CLAUDE.md hygiene)

- **"Open carry-forwards" section**: header date refreshed; the entire "Medium priority (still open)" + "Low priority" sub-sections removed (they were stale by weeks — "Branch 2 — Handoff readiness" was listed as open while it had shipped as BL-0009 / substrate v0.2.0; "Substrate version-detection bug suspected" was listed while it had shipped as BL-0008). Replaced with a single sentence pointing readers at UW-BACKLOG.md as the source of truth.
- **openpyxl quirk #4**: expanded with the qualified-range-endpoint trap from BL-0001's migration. Documents both the failure mode (`T12_Calc!$N$1:$N$500`'s endpoint is mis-caught by the unqualified-ref regex and shifted on row inserts) and the canonical fix (capture template formulas AFTER the shift sweep, not before — see `tools/migration/migrate_to_v021.py:312-321` for the worked example). Section heading bumped from "Three" to "Four" since quirk #4 is now substantive.
- **Module naming gotcha table** (also in scope): `populate_t12()` → `populate_rr_input()` cell, T12CapacityError historical-artifact note removed.

### Files

- `analyzer_rr_writer.py` — function/class/parameter renames + docstring updates
- `app.py` — import + call site + except clause + RR_VERSION 1.17.4 → 1.17.5 + RR_LAST_UPDATED → 2026-05-15
- `README.md` — targeted updates per BL-0013
- `CLAUDE.md` — Module naming gotcha + Open carry-forwards section + openpyxl quirk #4
- `SPEC-T12.md` — module-naming-history paragraph
- `UW-BACKLOG.md` — BL-0011 / BL-0013 / BL-0014 moved from Pending to Shipped
- `journal.md` — session entry at top
- `CHANGELOG-RR.md` (this entry)

### Verification

- `python3 -c "import analyzer_rr_writer"` — module imports cleanly with new symbols (`populate_rr_input`, `AnalyzerRRCapacityError`); old symbols (`populate_t12`, `T12CapacityError`) confirmed removed.
- `python3 -c "import ast; ast.parse(open('app.py').read())"` — app.py parses cleanly.
- `grep -E "populate_t12\b|T12CapacityError" *.py` — zero remaining live references in code (historical mentions in CHANGELOG / journal preserved).

---

## [1.17.4] — 2026-05-14

### Summary

**Companion to substrate v0.2.2 + new parser-side concession-from-Notes rerouter.** Two changes bundled in the same PR per the established cross-cutting pattern:

1. **`_detect_substrate_version()` sentinel addition (`app.py`)** — adds a v0.2.2+ check for the new Rent Roll Input!AH4 ("Total\nAncillary $") cell. Maintains the newest-first sentinel ordering.
2. **`normalizer.py` — `_reroute_recurring_concessions()` post-process pass** — closes the user-feedback gap surfaced against the v0.2.1 Homestead populated workbook (2026-05-14). Concession dollars buried in Homestead's `Misc.` GL column with a human-readable explanation in `Notes` are now correctly routed to `Concession $` (col I) instead of `Other LOC $` (col O).

### Why (parser change)

Some operators (Homestead-format especially) post concession amounts to a `Misc.` GL column with the explanation in `Notes`, leaving the structured `Concession $` column empty. The `Misc.` GL flows into our `Other LOC $` catchall (per `_looks_care` broadening in v1.16.2). So the concession value is *captured* but lives in the wrong bucket — Section M / UW Output sees the operator as having more residual ancillary expense and less concession activity than reality.

User feedback against the v0.2.1 Homestead populated workbook flagged 17 rows where `Notes` mentioned "concession" but `Concession $` was empty and `Other LOC $` was negative. Of those 17:
- **16 are recurring** (`$XXX/mo concession`, `$XXX concession ending DATE`, `$XXX concession remaining`, `ongoing concession`, `waived CF`) — these should be in `Concession $`.
- **1 is one-time** (`(half off $1047 concession)`) — descriptive parenthetical, leave in `Other LOC $`.

### What changed (parser)

**`normalizer.py`:**

1. New regex constants `_RECURRING_CONCESSION_PATTERNS` and `_ONE_TIME_CONCESSION_PATTERNS` — conservative match patterns for the two classes:
   - Recurring: 5 patterns (per-month markers, "remaining"/"ending" qualifiers, "ongoing", "waived CF").
   - One-time: 1 pattern (`(half off ...`).
2. New regex constant `_END_DATE_PATTERNS` — extracts `M/D/YYYY` or `M/YYYY` from "ending DATE" markers.
3. New helpers:
   - `_classify_concession_notes(notes) -> 'recurring' | 'one-time' | 'unknown'` — one-time markers OVERRIDE recurring.
   - `_extract_concession_end_date(notes) -> 'M/D/YYYY' | 'M/YYYY' | ''`.
4. New post-process function `_reroute_recurring_concessions(condensed)` — operates on the constructed Condensed_RR DataFrame. For each row where `_classify_concession_notes(Notes) == 'recurring'` AND `Other LOC $ < 0` AND `Concession $` is empty/zero:
   - Move the negative value: `Concession $` ← `Other LOC $`, `Other LOC $` ← `0.0`.
   - Extract end date if present, write to `Concession End Date`.
5. The pass is called from `normalize_rent_roll()` immediately after Condensed_RR construction, before mapping audit / return.

**Conservative gating** — only acts when ALL gates pass:
- Notes literally contains the word `concession`
- A recurring-marker pattern matches
- No one-time marker matches
- Other LOC $ is negative (positive Other LOC $ is something else, leave alone)
- Concession $ is empty/zero (don't clobber operator-provided values)

### Verification

End-to-end smoke test against the user's source RR (`2026-04-24 Homestead Village Rent Roll v2.xlsx`):

- 17 rows with "concession" in Notes
- **16 of 16 recurring rows correctly moved** from Other LOC $ → Concession $
- **1 of 1 one-time row correctly left alone** (A12 — Sams mom, "half off $1047")
- **6 of 6 end dates correctly extracted** (G6: 8/31/2026, E6: 7/31/2026, E13: 7/31/2026, F6: 12/2026, C5: 8/31/2026, K14: 9/30/2026)

Classifier unit tests: 25/26 pass (the one miss is an inverted-order speculative pattern not present in actual fixtures).

### What didn't change

- `_looks_care` keyword list (still routes `Misc.` → Other LOC $ at the bucket-routing stage).
- Existing `detect_concession_cols()` (still detects structured concession columns from operators that use them, e.g. Salem / Briar Glen).
- The output schema (still 30-col Condensed_RR; no new columns).

### Why bundled with substrate v0.2.2

Cross-cutting Track 1 (parser + version-detect) + Track 3 (substrate migration). Per the session pattern (BL-0001, BL-0003, BL-0009 all bundled), user authorized cross-cutting PRs.

### Files changed

- `app.py` — `_detect_substrate_version()` sentinel addition for v0.2.2; `RR_VERSION` 1.17.3 → 1.17.4
- `normalizer.py` — concession rerouter (~95 lines: 4 helpers + 1 post-process call site)
- (Substrate side: see `CHANGELOG-T12.md` `[Substrate template v0.2.2]` for the migration that motivated this patch.)

---

## [1.17.3] — 2026-05-14

### Summary

**Companion patch to substrate v0.2.1 (BL-0001).** Widens `_detect_substrate_version()` to match `vN.N.N` instead of `v0.1.N`, and adds two new sentinel checks (T12 Raw Data!B16 == "Meal Income" → v0.2.1+; "UW Export" sheet present → v0.2.0+) to the fallback chain. Bundled in the same PR as the substrate migration per the established cross-cutting pattern.

### Why

The prior regex `^v0\.1\.\d+$` was added in v1.17.1 (BL-0008) to handle the per-version sentinel-cell fallbacks. It was too narrow — any Analyzer at substrate v0.2.0 or v0.2.1 has `Cover!B8 = "v0.2.0"` / `"v0.2.1"`, which fails the regex, so detection falls through to the sentinel chain and returns `"v0.1.14+"` (because the I87 / A168 / etc. checks all still match). Cosmetic — the sidebar caption misreports — but confusing during deal review.

### What changed

**`app.py` — `_detect_substrate_version()`:**

1. Primary regex widened: `^v0\.1\.\d+$` → `^v\d+\.\d+\.\d+$`. Accepts any future major/minor without further code changes.
2. Two new sentinel checks prepended to the fallback chain (before the v0.1.14+ checks so detection is precise):
   - `T12 Raw Data!B16 == "Meal Income"` → return `"v0.2.1+"` (the v0.2.1 vocabulary expansion sentinel).
   - `"UW Export" in wb.sheetnames` → return `"v0.2.0+"` (the v0.2.0 flagship sheet).

**`app.py` — `RR_VERSION`:** `"1.17.2"` → `"1.17.3"`.

### Verification

Direct call against the post-migration bundled v0.2.1 Analyzer:

```
Bundled v0.2.1 Analyzer detected as: v0.2.1
Expected:                            v0.2.1
```

Primary path hits — the widened regex matches `v0.2.1` and returns it as-is. (Pre-patch, this returned `v0.1.14+` via the sentinel-cell fallback.)

### Files changed

- `app.py` — `_detect_substrate_version()` regex + 2 new sentinels; `RR_VERSION` bump
- (Substrate side: see `CHANGELOG-T12.md` `[Substrate template v0.2.1]` for the migration that motivated this patch.)

---

## [1.17.2] — 2026-05-14

### Summary

**UW-BACKLOG BL-0010 closed.** Pure refactor: module rename `t12_translator.py` → `analyzer_rr_translator.py`. Completes the Track 1 file disambiguation that began on 2026-05-10 (when `t12_writer.py` was renamed to `analyzer_rr_writer.py`). No behavioral change — `translate_for_t12()` signature, translation tables, and pass-through semantics are all unchanged.

### Why

The `t12_` prefix is a historical artifact from when the destination workbook was a standalone T12 intake template. Once the bundled-Analyzer flow shipped (RR v1.12.0), the prefix on Track 1 modules became misleading — a translator that converts RR vocabulary into Analyzer vocabulary has nothing to do with T12 GL detail. The 2026-05-10 rename of the writer half left the translator half stranded with the old name; this finishes the pair so future readers don't wonder which Track owns which file.

### What changed

**Module rename — `t12_translator.py` → `analyzer_rr_translator.py`:** done via `git mv` to preserve history. File contents unchanged.

**Import path — `app.py`:** single-line update at line 50, `from t12_translator import translate_for_t12` → `from analyzer_rr_translator import translate_for_t12`.

**Docstring reference — `analyzer_rr_writer.py`:** in `populate_t12()` docstring, `DataFrame from t12_translator.translate_for_t12()` → `DataFrame from analyzer_rr_translator.translate_for_t12()`.

**Version bump — `app.py`:** `RR_VERSION` `"1.17.1"` → `"1.17.2"`.

### What didn't change

- `translate_for_t12()` function name (still the public entry point — renaming would touch every caller without a clarity gain).
- `T12CapacityError` exception class exported by `analyzer_rr_writer.py` (kept for the same "rename surgical" reason recorded on 2026-05-10).
- Function name `populate_t12()` on `analyzer_rr_writer.py` (also a historical artifact; renaming is a separate follow-up, not bundled here).
- Translation tables (`STATUS_MAP`, `APT_TYPE_MAP`, `CARE_LEVEL_MAP`, `PAYER_MAP`) — verbatim.

### Verification

- Static check: `grep -r "t12_translator" .` returns only changelog / spec / docs references describing the historical name. No live imports.
- Import smoke test: `python -c "from analyzer_rr_translator import translate_for_t12; print(translate_for_t12)"` succeeds; original `from t12_translator import ...` now raises `ModuleNotFoundError` as expected.
- No substrate change, no migration script needed.

### Files changed

- `t12_translator.py` → `analyzer_rr_translator.py` — file rename (git mv)
- `app.py` — import path; `RR_VERSION` bump
- `analyzer_rr_writer.py` — docstring reference
- `CLAUDE.md` — module naming gotcha table + paragraph (now reflects 2-rename history); Last updated line
- `SPEC-RR.md` — file inventory; current-version line; Track 1 stamp
- `SPEC-T12.md` — naming paragraph at line 41
- `README.md` — project layout listing; versions table row
- `UW-BACKLOG.md` — BL-0010 moved Pending → Shipped

---

## [1.17.1] — 2026-05-14

### Summary

**UW-BACKLOG BL-0008 closed.** Single-file patch in `app.py`: rewrites `_detect_substrate_version()` to accurately report newer substrate versions instead of stale-capping at `v0.1.5`. Cross-cuts with substrate v0.1.15 (`BL-0002` closed — V5 chart empty-state UX). Both ship in the same PR per user request to bundle them.

### Why

Prior implementation (since v1.12.0) only knew the v0.1.4 and v0.1.5 Description_Map markers. Any Analyzer at substrate v0.1.6 through v0.1.14 returned `"v0.1.5"` — the sidebar caption silently misreported the actual substrate of every populated Analyzer downloaded since the substrate moved past v0.1.5. Cosmetic (display-only; never gates functionality) but confusing during deal review.

### What changed

**App — `app.py`:** `_detect_substrate_version()` rewritten with a three-tier resolution strategy:

1. **Primary**: read `Cover!B8` (canonical version stamp set by every migration since v0.1.4). If it matches `v0.1.N`, return as-is.
2. **Fallback heuristic** (newest-to-oldest sentinel cells, used when `Cover!B8` is missing or damaged):
   - `Rent Roll Recon!I87` contains `"Actual"`+`"PSF"` → `v0.1.14+`
   - `T12 Analytics!A168` contains `"Reconciliation"` → `v0.1.14+`
   - `Rent Roll Input!AC4` contains `"Meal Plan"` → `v0.1.13+`
   - `Rent Roll Recon!A119` starts with `"M "` → `v0.1.12+`
   - `Rent Roll Input!V4` contains `"2nd Person"` → `v0.1.10+`
3. **Legacy Description_Map heuristic** (pre-v0.1.10 fallback): unchanged from prior `2nd Person Revenue` / `Auto Expense` / `Lease / ground lease` checks.

All exception paths preserve the original `"(unknown)"` failure mode.

**App — `app.py` (version bump):** `RR_VERSION` `"1.17.0"` → `"1.17.1"`; `RR_LAST_UPDATED` updated.

### Verification

Sanity-checked detection against two reference workbooks:

| Workbook | `Cover!B8` | Detected | Outcome |
| --- | --- | --- | --- |
| Bundled v0.1.14 (post-PR #17 main) | `v0.1.14` | `v0.1.14` ✅ | Primary path |
| User's populated Homestead workbook | `v0.1.10` | `v0.1.10` ✅ | Primary path |

After this PR ships + the substrate v0.1.15 companion is applied, both will report `v0.1.15`.

### Companion (substrate v0.1.15)

Bundled in the same PR — see [CHANGELOG-T12.md](CHANGELOG-T12.md) `[Substrate template v0.1.15]` for the substrate-side details (BL-0002 closure: V5 chart empty-state UX).

### Files changed

- `app.py` — `_detect_substrate_version()` rewritten; version bump
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.15 (Track 3 companion)
- `tools/migration/migrate_to_v0115.py` — new idempotent migration script (Track 3 companion)
- `SPEC-RR.md` — current-version line
- `SPEC-T12.md` — current-version line (substrate v0.1.15 reference)
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — version references
- `UW-BACKLOG.md` — `BL-0002` + `BL-0008` moved to Shipped
- `CHANGELOG-RR.md` — this entry
- `CHANGELOG-T12.md` — `[Substrate template v0.1.15]` entry

---

## [1.17.0] — 2026-05-13

### Summary

**UW-BACKLOG BL-0003 — RR Input expansion: per-fee ancillary columns.** Splits what previously lumped into `Other LOC $` (col O) into 5 named per-fee columns at `Rent Roll Input!AC-AG`: `Meal Plan $`, `Scooter Fee $`, `Housekeeping $`, `Laundry $`, `Pet $`. Other LOC $ remains as the catchall for unmatched care headers (Diabetes, Misc, anything else). Cross-cutting Track 1 (parser + writer + 5 new bed-record fields + 5 new Condensed_RR cols) **plus** Track 3 (substrate v0.1.13 — see [CHANGELOG-T12.md](CHANGELOG-T12.md) `[Substrate template v0.1.13]` for the substrate-side mechanics). Bundled into a single PR per user spec.

Companion to substrate v0.1.12 Section M (Operator Fee Schedule). With the per-fee columns now populated by the parser, **Section M2 capture rate / M4 implied per-resident rate now compute for Meal Delivery / Motorized Scooter Fee / Housekeeping / Laundry** — not just Second Person Fee. Section M2's previous "falls into M5 Misc. (see UW-BACKLOG BL-0003)" placeholder text is replaced with real `INDIRECT` formulas off the new RR Input Col mapping (added at v0.1.13).

### Closes [UW-BACKLOG BL-0003](UW-BACKLOG.md)

### Why

v0.1.12 shipped Section M with 4 of the 7 default fees deferred to M5 Misc. (no per-resident RR data to compute capture rates). That deferred work was logged as `BL-0003`. This release closes it.

### What changed

**Mapping rules — `mappings.py`:**
- `DEFAULT_CARE_BUCKETS` extended with 8 new bucket-routing rules:
  - `\bmeal\b` → `Meal Plan $`
  - `\bscooter\b`, `\bmobility\b`, `\btransport\b` → `Scooter Fee $`
  - `\bhousekeeping\b`, `\bh\s*/\s*k\b` → `Housekeeping $`
  - `\blaundry\b` → `Laundry $`
  - `\bpet\b` → `Pet $`
- Diabetes, Misc, anything else care-related still flows to the existing `Other LOC $` catchall via `classify_care_bucket`'s fallback. No changes to that fallback behavior.

**Parser — `normalizer.py`:**
- `bucket_sums` initialized with 9 buckets (was 4): adds `Meal Plan $` / `Scooter Fee $` / `Housekeeping $` / `Laundry $` / `Pet $`.
- Bed record dict gains 5 new fields (one per new bucket).
- `Total LOC $` per-bed sum extended to include the new buckets — but the dollar total is **unchanged** because the same source dollars are now distributed across more columns instead of all going to Other LOC $.
- `CONDENSED_COLUMNS` grows 25 → 30. New columns at positions 26-30 (Z-AD on Condensed_RR sheet); existing cols 1-25 retain their fixed positions.

**Writer — `analyzer_rr_writer.py`:**
- New constants: `COL_AC_INDEX = 29`, `COL_AG_INDEX = 33`, `SOURCE_COLUMNS_AC_TO_AG` (5-element list).
- Idempotent clear extended to AC-AG so re-runs don't leave ghost data.
- v1.17.0 cols are detected optionally (`has_v117_cols`) so a pre-v1.17.0 `translated_df` still writes cleanly.

**App — `app.py`:**
- `RR_VERSION` `"1.16.2"` → `"1.17.0"`.

**Substrate — `tools/migration/migrate_to_v0113.py`** (Track 3 companion — substrate v0.1.12 → v0.1.13):
- See [CHANGELOG-T12.md](CHANGELOG-T12.md) `[Substrate template v0.1.13]` for the substrate-side details. In summary: 5 new column headers at Rent Roll Input row 4 cols AC-AG, Total LOC $ formula at T7:T606 extended to include AC-AG, Section M1 gets a 5th column "RR Input Col" pre-populated for the 5 default fees that have direct RR matches, Section M2/M4 rewritten with universal INDIRECT formulas off the new col so any analyst-added M1 row auto-computes if it has an RR Input Col set. M2 eligibility unified to all-occupied beds (not just IL — per user spec couples can occur in any care type).

### Verification

End-to-end fixture regression — all four fixtures green:

| Fixture | Beds | Care Level $ | Concession $ | Total LOC $ | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Salem (Oaks) | 50 ✅ | $28,125.81 ✅ | $-2,841.45 / 7 ✅ | $36,675.00 ✅ | Yardi — no per-fee ancillary cols in source |
| Briar Glen (MRI) | 79 ✅ | $234,360.00 ✅ | $-14,132.00 / 16 ✅ | $235,710.00 ✅ | MRI — no per-fee ancillary cols in source |
| Oaks at Beaufort | 104 ✅ | $33,436.13 ✅ | $-4,484.85 / 8 ✅ | $41,201.13 ✅ | **NEW**: surfaces $65 in Laundry $ (was buried in Other LOC) |
| Homestead Pensacola | 176 (62/62/52) | $0.00 ✅ | n/a | $-8,466.75 ✅ (was the same total before — split, not changed) | **NEW**: Pet $100, Housekeeping $1,450, Laundry $630 split out from Other LOC |

**Other LOC $ → split sum invariant** for Homestead:
- Pre-split: Other LOC $ = $-9,966.75 (everything lumped)
- Post-split: Other LOC $ = $-12,146.75 (Diabetes + Misc residual) + Pet $100 + Housekeeping $1,450 + Laundry $630 + Meal $0 + Scooter $0 = **$-9,966.75** ✓

Sum of new named buckets + remaining Other LOC = original Other LOC. Total LOC $ preserved. No double-counting.

### Migration path for existing populated workbooks

Workbooks downloaded before this release sit at substrate v0.1.10, v0.1.11, or v0.1.12. Migration scripts handle one substrate version step each — chain them in order:

```
python tools/migration/migrate_to_v0111.py file.xlsx file_v0111.xlsx
python tools/migration/migrate_to_v0112.py file_v0111.xlsx file_v0112.xlsx
python tools/migration/migrate_to_v0113.py file_v0112.xlsx file_v0113.xlsx
```

Or simpler: re-run the live app on the same RR + T12, get a fresh download with v0.1.13 substrate baked in and the v1.17.0 parser populating the new cols.

Verified end-to-end on the user's downloaded Homestead populated workbook (v0.1.10) chained through v0.1.12 → v0.1.13 with all 11 verification checks green at each step.

### Files changed

- `mappings.py` — 8 new DEFAULT_CARE_BUCKETS rules
- `normalizer.py` — bucket_sums + bed record dict + CONDENSED_COLUMNS + condensed builder all extended for 5 new buckets
- `analyzer_rr_writer.py` — `SOURCE_COLUMNS_AC_TO_AG` constant + write block + idempotent clear extension
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.13
- `tools/migration/migrate_to_v0113.py` — new idempotent migration script (5 install steps, 11-check verification)
- `app.py` — version bump
- `SPEC-RR.md` — current-version line
- `CHANGELOG-T12.md` — `[Substrate template v0.1.13]` entry (Track 3 companion)
- `SPEC-T12.md` — current-version line
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — substrate version reference
- `UW-BACKLOG.md` — `BL-0003` moved from Pending to Shipped
- `CHANGELOG-RR.md` — this entry

### Carry-forwards opened by this round

- **None blocking.** With BL-0003 closed, the next obvious follow-ups in `UW-BACKLOG.md` are:
  - `BL-0001` (substrate v0.2.0): finer ancillary T12 Labels (`Meal Income`, `Housekeeping Income`, etc.) so Section M3 stops returning `(shared bucket)` notes.
  - `BL-0004` / `BL-0005` / `BL-0006` (substrate v0.1.14): small Track 3 patches surfaced by v0.1.10 (T12 Analytics 2P reconciliation, Workbook Health AR aggregation, Section K PSF dispersion stats).

### Side observation worth tracking

Homestead's `Other LOC $` post-split is **-$12,146.75** (residual = Diabetes + Misc, both partially negative). The residual was negative before too (entire OCR was -$9,966.75); the split just makes the negative-net portion visible as a residual after attributing the named buckets. **If this persists across future Homestead-format deals**, consider adding a `BL-NNNN` for Misc/Diabetes credit reconciliation against T12 `Concessions & specials`.

---

## [1.16.2] — 2026-05-13

### Summary

Single-file patch on `normalizer.py`. Adds `meal`, `scooter`, `mobility`, `transport` to the `looks_care` keyword list in the care-bucket auto-detector. **UW-BACKLOG BL-0007** — closes the keyword side of the Section M v0.1.12 follow-up by ensuring per-resident meal-delivery / motorized-scooter / mobility-aid / resident-transport charges flow into `Other LOC $` if any source rent roll exposes them as named columns.

### Why

Substrate v0.1.12 introduced **Section M** (Operator Fee Schedule & Ancillary Reconciliation) on `Rent Roll Recon`. The default 7-fee schedule includes Meal Delivery and Motorized Scooter Fee; the M2 RR-side capture for those fees needs the parser to actually capture those columns into `Other LOC $` (today, in advance of BL-0003 splitting them into named columns at `Rent Roll Input!AC-AH`). v1.15.1 already widened the keyword list for Homestead-style ancillaries (pet / housekeeping / h/k / laundry / misc / diabet); this patch extends to the four remaining common ancillary names.

### Foundation that doesn't change

The auto-catch-into-`Other LOC $` heuristic in `detect_care_groups` recognizes a "standalone care/ancillary column" (header is itself the bucket, no prefix-suffix split) only when the cleaned header contains a known care-related keyword. Without that gate, every numeric column in a rent roll would be picked up — including non-care numerics like account numbers, IDs, etc. Adding to the keyword list is the safe, narrow way to expand coverage.

### What changed

**Parser — `normalizer.py`:**
- `_looks_care` keyword list (inside `detect_care_groups`) extended with 4 new entries: `meal`, `scooter`, `mobility`, `transport`. Each is a case-insensitive substring match against the cleaned header.
- Inline comment updated to reference v1.16.2 + UW-BACKLOG BL-0007 and to forward-reference BL-0003 (the cross-cutting PR that will split these out into named columns at `Rent Roll Input!AC-AH`).

**App — `app.py`:**
- `RR_VERSION` `"1.16.1"` → `"1.16.2"`; `RR_LAST_UPDATED` `"2026-05-12"` → `"2026-05-13"`.

**Docs — `SPEC-RR.md`:**
- Current-version line replaced.

**Docs — `UW-BACKLOG.md`:**
- `BL-0007` moved from `Pending` to `Shipped`; entry retains its `BL-0007` ID and gains a `Shipped in <release>` note + a one-paragraph summary of the keyword additions.

### Verification

Regression check against all three baseline-tracked fixtures: **all green**.

| Fixture | Beds | Care Level $ | Concession $ | Notes |
| --- | ---: | ---: | ---: | --- |
| Salem (Oaks) | 50 | $28,125.81 ✅ | $-2,841.45 across 7 rows ✅ | Yardi — no meal/scooter columns |
| Briar Glen (Vitality) | 79 | $234,360.00 ✅ | $-14,132.00 across 16 rows ✅ | MRI-style — no meal/scooter columns |
| Oaks at Beaufort | 104 | $33,436.13 ✅ | $-4,484.85 across 8 rows ✅ | Yardi — no meal/scooter columns |
| Homestead Pensacola | 176 (62 IL + 62 AL + 52 MC) | n/a | n/a | Broker-condensed — bundles meal/scooter into the existing `Misc.` column |

**Observation on Homestead specifically:** the four new keywords (`meal`/`scooter`/`mobility`/`transport`) don't add new dollars on Homestead because the broker format collapses optional services into a single `Misc.` column rather than breaking them out by name. This patch is **future-proofing for other operators** whose source rent rolls do break those services out as named columns (no such operator is in our verified set today, but the cost of the four keyword additions is zero where unused). The downstream value comes when BL-0003 ships and Section M's M2 starts reading per-fee columns at `Rent Roll Input!AC-AH`.

**Observation worth a future follow-up:** Homestead's `Other LOC $` total nets to **-$9,966.75** (negative). This means some `Pet` / `H/K` / `Laundry` / `Misc.` entries are credits (negative dollars). Not introduced by this patch and not a regression — but flagged for review since it could indicate hidden concessions or write-offs that should reconcile against T12 `Concessions & specials`. **Add to UW-BACKLOG.md if it persists.**

### Files changed

- `normalizer.py` — 4 keywords appended to `_looks_care` list + inline comment update
- `app.py` — version bump
- `SPEC-RR.md` — current-version line replaced
- `UW-BACKLOG.md` — `BL-0007` moved to Shipped
- `CHANGELOG-RR.md` — this entry

---

## [1.16.1] — 2026-05-12

### Summary

Patch release. Fixes a long-standing concession-doubling bug on Yardi-style rent rolls (Salem, Beaufort). The bug was originally surfaced during v1.13.0 baseline verification but logged as a Known issue for a separate chat. This chat reapplies the fix against the current v1.16.0 codebase. **Parser-only change** — single function (`detect_concession_cols`); no UI, no writer, no substrate, no doc layout changes beyond a single decision-section addition.

### Root cause

`detect_concession_cols` in `normalizer.py` was matching both the bare-prefix concession column and its `(month)`-suffixed sibling as separate concession sources:

* `Assisted Living ongoing concession`        ← bare-prefix snapshot
* `Assisted Living ongoing concession (January 2026)` ← month-suffixed accrual

Both columns hold identical per-row values in the operators verified (the bare column is a static reference; the `(month)` column is the actual monthly accrual). The bare-prefix variant matches the generic `\bconcession\b` pattern. The `(month)` variant matches the same pattern. Naive collection summed each row's discount twice. Salem read $-5,682.90 (2× the SPEC baseline of $-2,841.45); Beaufort read $-8,969.70 silently (2× the broker's reported $-4,484.85 total).

### What changed

**Parser — `normalizer.py`:**
- Added a de-dupe pass to `detect_concession_cols`. After the initial collection, for every `(month)`-suffixed column we compute its prefix via the existing `_strip_bucket_suffix` helper. Bare-prefix columns whose cleaned header matches the prefix of any `(month)`-suffixed sibling are dropped. Standalone bare-prefix columns with no `(month)` sibling (Briar Glen `Recurring Discounts`, `One-Time Incentives`) are kept.

**App — `app.py`:**
- `RR_VERSION` `"1.16.0"` → `"1.16.1"`; `RR_LAST_UPDATED` `"2026-05-11"` → `"2026-05-12"`.

**Docs — `SPEC-RR.md`:**
- Current-version line replaced.
- "Track 1 is at v1.14.0; Track 2 is at v0.2.0; bundled Analyzer substrate is at v0.1.7" updated to v1.16.1 / v0.2.1 / v0.1.10 (this line had been stale since v1.15.0; corrected during this patch).
- Concession-detection decision section gains a "Bare-prefix + `(month)`-suffixed pair de-duplication" note explaining why the de-dupe pass exists and which fixtures it affects.
- Verified-formats table: Salem `Concession $` row regains its `$-2,841.45 (7 rows)` baseline (was already there); Beaufort row gains its newly-verified `$-4,484.85 (8 rows)` baseline (was `"(covered by Salem)"`); Beaufort Care Level $ collapsed from `AL $18,720 + MC $14,716.13` to the sum `$33,436.13` with the breakdown in a parenthetical for cleaner table display.

### Verification

Pre-fix baseline against current v1.16.0 codebase confirmed the bug still exists on origin/main — `detect_concession_cols` was unchanged since v1.13.0 across the 30+ commits since.

| Fixture | Concession $ (pre-fix) | Concession $ (post-fix) | Expected | Notes |
| --- | ---: | ---: | ---: | --- |
| Salem | $-5,682.90 | $-2,841.45 | $-2,841.45 | matches SPEC baseline (restored) |
| Briar Glen | $-14,132.00 | $-14,132.00 | $-14,132.00 | unchanged — de-dupe is no-op |
| Oaks at Beaufort | $-8,969.70 | $-4,484.85 | $-4,484.85 | matches broker `Total Marketing Incentive Charges`; was silently wrong |
| Homestead Pensacola | $0.00 | $0.00 | $0.00 | no concession column in source; unchanged |

All other RR metrics across all four fixtures are unchanged (bed counts, Care Type distributions, Care Level $, Status counts). The v1.16.0 data-capture columns (2nd Person Rent, Notes, Balance, ACH, PSF, etc.) are not touched.

### Why this fix took 5 days to land

Originally surfaced and patched in a working tree on 2026-05-07 against the then-current v1.13.0 codebase. That commit (`8dc1e08` on safety branch `claude/v1-13-1-attempt-stale-2026-05-07`) bundled documentation rewrites alongside the code fix. By the time of push, the codebase had advanced to v1.16.0 through 8 PRs and the bundled commit was unmergeable — version numbers would have stepped backwards, the README would have overwritten two newer README refreshes, and the docs touched files (`OPTIMIZATION-DECISIONS.md`, `CLAUDE.md`, renamed `analyzer_rr_writer.py`) that didn't exist in the stale view. The current PR pulls forward only the 14-line code change against the current parser, re-verifies against all four fixtures, and lands as a focused patch.

### Files changed

- `normalizer.py` — `detect_concession_cols` de-dupe pass
- `app.py` — version bump
- `SPEC-RR.md` — current-version line, Track-versions inline reference, Concession-detection decision section (de-dupe note added), Verified-formats table (Salem + Beaufort concession baselines)
- `CHANGELOG-RR.md` — this entry

---

## [1.16.0] — 2026-05-11

### Summary

Captures **7 new data fields per resident** that were previously being dropped silently — discovered against the Homestead fixture by tying out source-rent-roll charges to the Condensed_RR output. Combined with the v1.15.1 keyword widening (which recovered Pet / H/K / Laundry / Misc. / Diabetes into `Other LOC $`), this round adds dedicated columns for:

1. **2nd Person Rent $** — housing revenue for couples, tied to apartment not care needs. Aligns with the T12 substrate's pre-existing `2nd Person Revenue` Label so RR ↔ T12 reconciliation now nets to zero on 2P revenue. Verified: 4 couples in the Homestead fixture now populate ($650 / $725 / $800).
2. **Move-out Date** — for vacate forecasting in UW revenue projections. Was already captured in `Normalized_Beds` (col R) but dropped from `Condensed_RR` — now in both.
3. **Balance** — outstanding AR per resident → bad-debt indicator.
4. **Notes** — free-form context (rate-negotiation history, lease anomalies, transfer notes). 33 rows in the Homestead fixture have populated notes including the diagnostic "HK $100 eff 3/1- sec occ $650" that confirms the SP value.
5. **Market PSF / Actual PSF** — rate per sqft. Derivable from Market/Actual Rate ÷ Sq Ft but having them explicit reduces downstream calc burden and makes the RR fully self-describing.
6. **ACH** — auto-pay enrollment flag → collection-velocity signal.

### What changed

**Parser — `normalizer.py`:**
- 6 new entries in `FIELD_PATTERNS`: `second_person_rent`, `balance`, `notes`, `ach`, `market_psf`, `actual_psf`. Existing `move_in` / `move_out` patterns also widened in v1.15.1 to catch Homestead's `Rent Start` / `Rent End` / `MoveOut Date` headers.
- New `_normalize_flag(v)` helper for boolean-ish source values (handles `"X"`, `"Yes"`, `1`, `True`, etc. → `"X"`; everything else → `""`).
- Bed-level dict extended to capture the 7 new fields.
- `Total Monthly Revenue` calc now includes `+ second_person_rent` — 2P is incremental housing revenue and was previously excluded.
- `CONDENSED_COLUMNS` grows 18 → 25; new columns appended at positions 19-25 (S-Y in the Condensed_RR sheet) so existing cols A-R retain their fixed positions for analyzer_rr_writer's mapping.

**Writer — `analyzer_rr_writer.py`:**
- New `SOURCE_COLUMNS_V_TO_AB` tuple maps the 7 new fields to Rent Roll Input cols V-AB.
- `populate_t12()` writes the new cols after the existing S=Period Date and T-U formula columns, preserving the analyzer substrate's formula layout. Move-out Date (col W of Rent Roll Input) carries `mm/dd/yyyy` number format.
- Idempotent clear extended to cols V-AB so re-runs don't leave ghost data.

**App — `app.py`:**
- `RR_VERSION = "1.16.0"`; `RR_LAST_UPDATED = "2026-05-11"`.

**Substrate — `tools/migration/migrate_to_v0110.py`:** (Track 3 companion — substrate v0.1.9 → v0.1.10)
- Adds 7 new column headers at Rent Roll Input row 4 cols V-AB, styled to match the existing navy header row.
- Extends `Total Monthly Rev` formula at U7:U606: `=IFERROR(H{r}+IFERROR(I{r},0)+T{r},0)` → `=IFERROR(H{r}+IFERROR(I{r},0)+T{r}+IFERROR(V{r},0),0)` so 2nd Person Rent flows into the per-resident TMR.
- Stamps Cover!B8 + 13 AZ4 anchors to v0.1.10.
- 8-check verification block; idempotent — gate checks both stamp AND that row-4 V header is present.

**T12 translator — `t12_translator.py`:** no changes needed. The translator passes through unrecognized columns via `df.copy()`, so the 7 new fields flow through to the Analyzer write step unchanged.

### Verification

End-to-end smoke against the Homestead fixture:
1. `normalize_rent_roll()` → 176 rows, 25 cols, 4 couples with non-zero 2nd Person Rent $.
2. `translate_for_t12()` → 25 cols preserved.
3. `populate_t12()` against the v0.1.10 Analyzer → Rent Roll Input cols A-AB populated, including A3 (Homestead Village property name) + V (2P rent) + Y (notes) + Z/AA (PSF) + AB (ACH).
4. Sandra & Darryl Owens row 19: V=$650 (SP), O=$100 (H/K), Y="HK $100 eff 3/1- sec occ $650" — splits source's $750 ancillary total correctly between dedicated 2P col + Other LOC.
5. Total Monthly Rev formula at U19 now references V19: `=IFERROR(H19+IFERROR(I19,0)+T19+IFERROR(V19,0),0)`.

### Carry-forwards opened by this round

- **Rent Roll Recon updates (Track 3, future)**: the new IL deep-dive section K could surface PSF stats (avg / range across IL) by adding 2-3 formulas. Skipped this round to keep the substrate change minimal — sized as a small future v0.1.11.
- **2P revenue reconciliation (Track 3, future)**: T12 Analytics could add a new row that compares `SUM('Rent Roll Input'!V) × 12` (RR-projected 2P revenue annualized) against `T12 Raw Data!2nd Person Revenue` (T12 actual). Same pattern as Section B revenue reconciliation in Rent Roll Recon. Sized as future v0.1.11.
- **Balance aggregation (Track 3, future)**: total outstanding AR across all residents as a Workbook Health validation. Useful but not blocking.

### Why this is Track 1 (with Track 3 companion)

Parser changes that capture new source fields are Track 1 by CLAUDE.md scope discipline. The Analyzer substrate change to receive those new fields (column headers + extended TMR formula) is Track 3. Bundled into the same chat per user authorization 2026-05-11.

---

## [1.15.1] — 2026-05-11

### Summary

Fix for the user-reported bug against v1.15.0: Homestead per-resident ancillary charges (Pet / H/K / Laundry / Misc. / Diabetes) were silently dropped by the parser despite the Homestead fixture having them populated. Verified against 12 occupied IL residents — every one had non-zero charges that didn't make it into the Condensed_RR output.

### Root cause

The auto-catch-into-`Other LOC $` heuristic at `normalizer.py:251-256` gated on a narrow keyword list. None of Homestead's column names (`Pet`, `H/K`, `Laundry`, `Misc.`, `Diabetes`) contained any of the recognized keywords, so the parser silently skipped them.

### What changed

**Parser — `normalizer.py`:**
- Widened the `looks_care` keyword list to include `pet`, `housekeeping`, `h/k`, `laundry`, `misc`, `diabet`. All flow into `Other LOC $` via the existing bucket logic. 13 IL residents in the Homestead fixture now show non-zero `Other LOC $` (was 0 before).
- 2nd Person Rent (SP column) is **intentionally excluded** from this keyword expansion — it gets its own dedicated column at v1.16.0 (Tier 1.2) because it's housing revenue, not care-LOC, and the T12 substrate v0.1.5 already has a dedicated `2nd Person Revenue` Label that needs a 1:1 RR-side counterpart.
- Added `r"^rent\s*start$"` to `move_in` patterns and `r"^move\s*out\s*date$"` / `r"^moveout\s*date$"` / `r"^rent\s*end$"` to `move_out` patterns. Homestead's `Rent Start` / `MoveOut Date` / `Rent End` headers now match.

**App — `app.py`:**
- `RR_VERSION = "1.15.1"`.

### Verification

Smoke test against Homestead fixture: 13 IL residents now have `Other LOC $` populated (Pet / H/K / Laundry / Misc.). Move-in Date populated for all 176 rows (was sparse).

### Carry-forward to v1.16.0

SP (Second Person Rent) is still not captured — by design, it gets a dedicated column in v1.16.0.

---

## [1.15.0] — 2026-05-11

### Summary

Track 1 follow-up to substrate v0.1.8 Branch 3 analytical coverage: the RR Analyzer writer (`analyzer_rr_writer.populate_t12`) now stamps the property name into `Rent Roll Input!A3` automatically, derived from the uploaded RR filename. This closes the Track 1 carry-forward opened by substrate v0.1.8, which left A3 as analyst-paste-only. Now the property name flows automatically from "Salem Road T-12 1.31.26.xlsx" → A3 of the Analyzer → T12 Analytics!B2 (via the 3-priority formula installed at v0.1.8) → Workbook Health Property_Name validation. Manual override still works — analyst can paste a different name into A3 after download; the next re-run from app will rewrite it from the new RR upload.

### What changed

**New shared module — `property_name.py`:**
- `derive_property_name(filename: str) -> str` — best-effort filename → property name. Strips date stamps (`1.31.26`, `2025.12`, `2026-04-24`, `Mar 2026`, etc.), boilerplate (`T-12`, `T12`, `RR`, `Rent Roll`, `P&L`, `Profit and Loss`, `Statement`, `Financial Summary`, `v2`, `(1)`), and normalizes separators (`_`, `-`) to spaces. Falls back to the raw stem if cleaning leaves nothing.
- Verified against 15 representative filenames including the four T12 reference fixtures, Homestead RR, and edge cases (empty input, Windows path, UNIX path, bare property name).
- Cross-track utility — used by both `analyzer_rr_writer.py` (Track 1) and `t12_normalizer_writer.py` (Track 2). Bumping its behavior should consider both writers.

**Writer — `analyzer_rr_writer.py`:**
- `populate_t12()` accepts a new `source_filename: str = ""` keyword. When non-empty, the derived property name is written to `Rent Roll Input!A3` per the substrate v0.1.8 contract. Empty filename or empty derivation leaves A3 untouched (so a bad filename doesn't clobber an analyst-typed value carried in from a prior session).
- Idempotent: each call rewrites A3 from the new RR file's derived name. Matches the existing "writer manages the Rent Roll Input sheet" contract that already clears A7:S606 before each write.

**App — `app.py`:**
- `RR_VERSION = "1.15.0"`, `RR_LAST_UPDATED = "2026-05-11"`.
- `populate_t12(...)` call passes `source_filename=getattr(rr_file, "name", "")`. Falls back to "" if `rr_file` has no `name` attribute (e.g. a future programmatic caller passing raw bytes).

**Docs:**
- `SPEC-RR.md` — Current version line bumped to v1.15.0; file inventory entry for `property_name.py` added.
- `CHANGELOG-RR.md` — this entry.
- `CLAUDE.md` — Track 1 follow-up carry-forward marked closed; current RR version bumped to v1.15.0.

### Carry-forwards opened by this change

- **None.** This closes the Track 1 carry-forward from substrate v0.1.8 cleanly. The companion Track 2 follow-up (T12 writer stamp at T12 Input!A10) is shipped as T12 v0.2.1 in a separate commit on the same branch.

### Verification

In-process smoke test (`_smoke_t1.py`, not committed) confirms:
1. `"Salem Road T-12 1.31.26.xlsx"` → A3 = `"Salem Road"`.
2. `"2026-04-24 Homestead Village Rent Roll v2.xlsx"` → A3 = `"Homestead Village"`.
3. Empty / unspecified `source_filename` → A3 untouched.
4. T12 Analytics B2 formula still resolves through the 3-priority chain.

Unit-level: `_test_property_name.py` (not committed) covers 15 filename patterns end-to-end, all green.

### Why this is Track 1 (not Track 3)

The substrate workbook change shipped at v0.1.8 (Track 3) reserved the value cell. Stamping content into that cell from a parser-side filename is application logic — Track 1 territory per CLAUDE.md scope discipline. The user explicitly authorized cross-track work in the same chat (the 2026-05-11 Branch 3 + writer-follow-ups bundle) so this was done in the same session; future writer-side changes should be scoped to their own Track 1 chat.

---

## [1.14.0] — 2026-05-08

### Summary

Homestead-style broker-condensed rent roll format support (Homestead Village Pensacola verified — 176 units across IL/AL/MC). Three categories of source vocabulary the parser previously didn't understand are now mapped: a new set of column header labels (`Unit ID`, `Cottage`, `Area`, `Category`, `BR/BA`, `Market / Mo YYYY`, `Actual / Mo YYYY`, `Status`), the `STU` apt_type code, and the `NTV` (Notice To Vacate) status code. Self-contained vacant rows with no resident name now emit instead of being silently dropped (the previous behavior cost 40 of 176 units on the Homestead file). Pre-cleaner extended to drop the Homestead end-of-sheet pricing-summary table and the `ERRORS!!!` / `Current Date:` chrome at the top.

### Added

- **`normalizer.py` FIELD_PATTERNS additions.** Header-classification patterns for the Homestead-style broker-condensed format:
  - `unit`: `^unit\s*id$` (Homestead's unique cottage+room identifier, e.g. `A1`). Placed first so it wins over the generic `^unit$` fallback. With first-wins semantics in the build loop, the per-cottage `Unit` column (which would otherwise overwrite this) falls through unmapped — leaving `unit_id` set to the unique `Unit ID` value.
  - `apt_type`: `^br\s*/\s*ba$` (Homestead's `BR/BA` column with `STU` / `1BR` / `2BR` values).
  - `market_rate`: `^market\s*/\s*mo(\s*\d{4})?$` (Homestead's `Market / Mo 2026`-style year-suffixed column).
  - `actual_rate`: `^actual\s*/\s*mo(\s*\d{4})?$` (matching pair).
  - `bed_status`: `^status$` (Homestead self-contained: one row per unit with `Status` column carrying the per-unit status).
  - `sqft`: `^area$` (Homestead's square-footage column label).
  - `care_type`: `^category$` (Homestead's IL / AL / MC-I / MC-JK column — values resolve via existing `\bil\b` / `\bal\b` / `\bmc\b` rules).
- **`mappings.py` apt_type rule.** `\bstu\b` → `Studio` (Homestead-style code, parallel to existing `\bstd\b` Briar Glen rule).
- **`mappings.py` bed_status rule.** `\bntv\b` → `Notice`, ordered before `\boccupied\b` so Homestead's `Occ w/ NTV` value resolves to `Notice` rather than falling through unmapped. NTV is "Notice To Vacate" — semantically the unit is currently occupied but on notice; the bed-status taxonomy collapses that to `Notice`.
- **`pre_cleaner.py` banner prefixes.** `errors!!!` and `current date:` — Homestead's row-2 chrome cells.
- **`pre_cleaner.py` totals signals.** `il subtotal`, `al subtotal`, `mc subtotal`, `double-check`, `avg area` — all anchored markers for the Homestead end-of-sheet pricing-summary table that follows the unit list. The first match (`avg area` on the second-table header row) cuts the entire summary block, including the secondary `Unit ID` / `# Units` header that would otherwise leak through as 6 garbage records (4 IL-cottage rows + a "Monthly Total" row + a "Double-Check" row).

### Changed

- **`normalizer.py` `_row_is_self_contained_unit()`.** Previously required a resident name (or `*Vacant` marker) on the row to qualify as self-contained. Now also accepts a recognized `bed_status` value, gated on the value matching one of the known status keywords (`occupied`, `vacant`, `notice`, `hold`, `ntv`, etc.). Rationale: Homestead reports `VACANT` per row in the Status column even when the resident slot is empty, and the prior logic silently dropped 40 of the 176 truly-vacant rows because they had no resident name to qualify them. The keyword gate prevents summary-block rows where the Status column happens to hold a number or a label like "Monthly Total" from emitting as junk records. SPEC-RR §"Self-contained row detection" updated to reflect the dual signal.

### Verified

- **Homestead Village Pensacola rent roll** (176 units across IL=62 / AL=62 / MC=52):
  - 176 rows out, exact match to source pricing-summary subtotals (was: 136 rows, 40 missing — every truly-vacant unit dropped silently).
  - Care Type breakdown: IL=62 / AL=62 / MC=52 — exact match to source (was: every row blank; broke `Rent Roll Recon` COUNTIFS).
  - Status breakdown: 128 Occupied + 43 Vacant + 5 Notice = 176 (was: every row stamped `Occupied` via the no-bed_status fallback inference).
  - Apt Type, Sq Ft, Market Rate, Actual Rate columns all populated (were: blank for every row).
  - Unit IDs preserved as unique `A1` / `B1` / etc. (was: just the per-cottage number `1`, causing 10× collisions).
  - Zero unmapped values across all five tracked categories (apt_type, bed_status, payer, care_level, care_type).
  - Pre-cleaner stats: 216 input rows → 184 output rows; cuts at input row 189 (the `Avg Area` header of the secondary table); drops 26 rows after totals (the entire pricing-summary block).
- **Salem (Oaks)**, **Briar Glen**, **Oaks at Beaufort** baselines: no regression expected — none of the new patterns overlap with their existing header vocabulary, the new bed_status fallback is gated on recognized status keywords (Briar Glen's `*Vacant` resident marker still flows through the existing resident-name path with the inline status strip at lines 602-607), and the new pre-cleaner signals are operator-specific phrases. **Worth a smoke test on the next run of any Salem/Briar/Beaufort file.**

### Known issues

- **`CLAUDE.md` "hanging branch" carry-forward note is stale.** The note flags `claude/mystifying-wu-33a0f6` as containing unmerged v1.13.0 work, but commit `667fd67` ("RR v1.12.0 -> v1.13.0: Memory Care detection (Oaks at Beaufort)") IS on main. CLAUDE.md updated in the same commit as this release to remove the note and refresh `Current version` to v1.14.0.
- **`README.md`** still has the RR-only framing and doesn't mention the Homestead format. Same low-pri carry-forward as before.

### Versions

- `APP_VERSION` / `RR_VERSION`: `1.13.0` → `1.14.0`
- `APP_LAST_UPDATED` / `RR_LAST_UPDATED`: `2026-05-07` → `2026-05-08`
- `T12_VERSION`: `0.2.0` (unchanged)
- Bundled Analyzer substrate: v0.1.7 (unchanged)

### Files changed

- `normalizer.py` — FIELD_PATTERNS additions for Homestead headers; `_row_is_self_contained_unit()` accepts bed_status as an alternate signal
- `mappings.py` — `\bstu\b` → Studio; `\bntv\b` → Notice (ordered before `\boccupied\b`)
- `pre_cleaner.py` — banner prefix and totals-signal additions for Homestead chrome and pricing-summary block
- `app.py` — version bump
- `SPEC-RR.md` — current-version line, Verified-formats table (Homestead Pensacola row), Self-contained row detection section
- `CHANGELOG-RR.md` — this entry
- `journal.md` — session entry
- `CLAUDE.md` — Last-updated date, RR current-version line, hanging-branch carry-forward removed

---

## [1.13.0] — 2026-05-07

### Summary

Memory Care detection for Oaks-style rent rolls (Oaks at Beaufort verified). Three categories of source vocabulary the parser previously didn't understand are now mapped: the `Horizons` wing label (Oaks's name for the Memory Care wing), the `Comfort Care 1/2/3/4` acuity tier vocabulary used inside MC, and a second `Care Level $` column group on each row dedicated to MC charges. Surface area: `mappings.py` rule additions + a one-block change in `normalizer.py` for the Care Level extraction loop.

### Added

- **`mappings.py` Care Type rules.** `\bhorizons\b` → MC and `\bcomfort\s*care\b` → MC. The Horizons rule resolves the building/wing fallback for any resident in that wing; the Comfort Care rule lets a resident's Care Type resolve from the level value alone (the Care Level fallback in the chain), e.g. when neither the Care Type column nor the Building column carries a recognizable code but the level cell reads "Comfort Care 3."
- **`mappings.py` Care Level rules.** `Comfort Care 1/2/3/4/5` → `Level 1-5`; `Comfort Care 6+` → `Level 6+`. Same Level scheme as Assisted Living, just under a different label.
- **`mappings.py` Care Bucket rule.** `memory\s*care` → `Care Level $`. Makes any column whose header contains "Memory Care" (e.g. `OAKS SENIOR LIVING MEMORY CARE (January 2026)`) flow into the Care Level revenue bucket alongside the parallel `OAKS SENIOR LIVING ASSISTED LIVING (January 2026)` column. Pre-fix, MC charges fell into the `Other LOC $` auto-catch.

### Changed

- **`normalizer.py` Care Level extraction.** Previous logic broke out of the Care Level group scan after the first hit, regardless of whether that group's level column was actually populated on the row. For Oaks at Beaufort the AL group's level column is *always blank* on MC residents (because the AL column is reserved for AL residents), so the loop locked onto a NaN cell and never read the MC level. Now the loop iterates ALL groups whose bucket is `Care Level $` and picks the first one with a non-blank level value on this row. NaN cells (numpy float NaN, "nan" strings) are treated as blank during this scan.

### Verified

- **Oaks at Beaufort rent roll** (104 beds, 51 occupied — 28 AL + 23 MC):
  - 50 Horizons rows now resolve as Care Type = MC (was: blank, all 50 flagged in Exceptions).
  - MC Care Level distribution: 9× Level 3, 9× Level 2, 3× Level 1, 2× Level 4 (was: blank for all).
  - MC charges: $14,716.13 in `Care Level $` (was: in `Other LOC $`).
  - AL Care Level $ now $18,720.00 — $400 higher than pre-fix because room 207A (an AL resident with both AL Basic + a Comfort Care 1 add-on) now correctly sums both Level $ columns.
  - Zero unmapped values across all five tracked categories.
- **Salem (Oaks)** baseline: 50 beds, Care Level $ $28,125.81 — unchanged. *(Salem's concession total reads $-5,682.90 vs. SPEC baseline $-2,841.45 — a 2× factor that appears to predate this release. Not introduced by this change. Tracked for a separate fix; see Known issues.)*
- **Briar Glen** baseline: 79 beds, Care Level $ $234,360.00, Concession $ $-14,132.00 (16 rows) — all unchanged.

### Known issues

- **Salem concession doubling (pre-existing, not introduced here).** Salem's `Concession (January 2026)` column and the underlying `Concession` column both match the generic `\bconcession\b` pattern in `_CONCESSION_PATTERNS`, so concessions sum twice. SPEC-RR baseline says $-2,841.45 (7 rows); current parser returns $-5,682.90 (still 7 rows). Pending separate fix — likely `(month)` suffix should win over the bare-prefix match, or the bare-prefix variant should be excluded when a `(month)` variant exists in the same source. Surfaced during v1.13.0 baseline verification but out of scope for this release.
- **Resident with charges in BOTH AL and MC level columns.** Care Level $ correctly sums; Care Level (label) shows only the first non-blank label encountered (typically AL's). Edge case — observed once across the 104 Beaufort rows. Acceptable.

### Versions

- `APP_VERSION` / `RR_VERSION`: `1.12.0` → `1.13.0`
- `APP_LAST_UPDATED` / `RR_LAST_UPDATED`: `2026-05-06` → `2026-05-07`
- `T12_VERSION`: `0.1.1` (unchanged)
- Bundled Analyzer substrate: v0.1.5 (unchanged)

### Files changed

- `mappings.py` — Care Type, Care Level, Care Bucket rule additions
- `normalizer.py` — Care Level extraction loop scans all `Care Level $` groups, NaN-aware blank check
- `app.py` — version bump
- `SPEC-RR.md` — current-version line, Verified-formats table (Oaks at Beaufort row), Care Type rule patterns list, new "Multiple Care Level $ groups" decision section, Comfort Care vocabulary note
- `CHANGELOG-RR.md` — this entry

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
