# CLAUDE.md

> Onboarding doc for any Claude session (chat or Claude Code) working on this repo. Read this first — it points to canonical truth and surfaces facts that previously had to be grubbed for.

**Last updated:** 2026-05-11 (after substrate v0.1.8 — Branch 3 analytical coverage)

---

## What this repo is

Two parallel pipelines feeding one underwriting workbook:

1. **Rent Roll Normalizer (RR)** — Streamlit app that turns any operator's rent roll into a normalized bed-level Excel output.
2. **T12 Normalizer (T12)** — parser + writer that turns various T12 financial-statement formats into a normalized monthly trending Excel.

Both pipelines populate a shared destination workbook: `ALF_Financial_Analyzer_Only.xlsx` (the "Analyzer"). The Analyzer is the underwriting substrate — RR drives Rent Roll Input, T12 drives T12 Input, and the analytical sheets reconcile + roll up to UW Output.

A separate downstream full-underwriting sheet (not in this repo) consumes UW Output. Optimizing the Analyzer to be a clean handoff to that sheet is an active workstream.

## Local clone path

`C:\Users\erikj\Downloads\rent_roll_app` — Windows machine, PowerShell.

## Live deploy

https://rrnormalizer.streamlit.app/ — Streamlit Community Cloud, auto-deploys from `origin/main` on push (~30-60 sec lag). **Reboot-first rule:** if live behavior diverges from a verified local run on the same file, assume stale module cache and reboot from share.streamlit.io before debugging.

---

## Three workstream tracks

The repo runs three parallel tracks. They share an Analyzer but are otherwise independent. **Track 1 chats do not edit Track 2 or Track 3 files** — see "Scope discipline" below.

### Track 1 — RR Normalizer (RR-side code)

| What | Where |
| --- | --- |
| Code | `app.py`, `normalizer.py`, `mappings.py`, `pre_cleaner.py`, `period_date.py`, `reports.py`, `writer.py` |
| Spec | `SPEC-RR.md` |
| Changelog | `CHANGELOG-RR.md` |
| Current version | RR v1.15.0 |

### Track 2 — T12 Normalizer (T12-side code + Analyzer substrate)

| What | Where |
| --- | --- |
| Code | `t12_normalizer.py`, `t12_normalizer_writer.py`, plus T12 sections of `app.py` |
| Spec | `SPEC-T12.md` |
| Changelog | `CHANGELOG-T12.md` |
| Bundled workbook | `ALF_Financial_Analyzer_Only.xlsx` |
| Migration scripts | `tools/migration/migrate_to_v01N.py` (one per substrate version) |
| Verification harness | `tools/verify_t12_v020.py` (parser-side; runs all four reference fixtures) |
| Current code version | T12 v0.2.1 |
| Current substrate version | v0.1.8 |

**Module naming gotcha (verified 2026-05-10).** Four `t12_*` files exist and they are NOT duplicates — the `t12_` prefix originally meant "operates on the T12-shaped destination workbook" (which is now the Analyzer), not "operates on T12 data." Every one is imported by `app.py` and serves a distinct role:

| File | Function | Role |
| --- | --- | --- |
| `t12_translator.py` | `translate_for_t12()` | Translates Condensed_RR vocabulary → Analyzer data-validation vocabulary (e.g. `1BR` → `1 Bedroom`). RR-side (Track 1). |
| `analyzer_rr_writer.py` | `populate_t12()` | Writes the translated RR into the Analyzer's `Rent Roll Input` sheet. RR-side (Track 1). Was named `t12_writer.py` until 2026-05-10 — see CHANGELOG-RR.md and journal.md for the rename. The exception class it exports is still `T12CapacityError` (preserved to keep the rename surgical; could be renamed to `AnalyzerRRCapacityError` in a follow-up). |
| `t12_normalizer.py` | `parse_t12()` | Parses raw T12 financial statements (Yardi / MRI / BrokerFinancialSummary format registry). T12-side (Track 2). |
| `t12_normalizer_writer.py` | `populate_t12_input()` | Writes parsed T12 GL detail into the Analyzer's `T12 Input` sheet. T12-side (Track 2). |

If a future chat is tempted to delete one as "duplicate," check `app.py` lines 46-51 and 795-806 — all four are wired into the orchestration. The 2026-05-10 rename of `t12_writer.py` → `analyzer_rr_writer.py` was the first pass at disambiguation; the partner file `t12_translator.py` could similarly be renamed to `analyzer_rr_translator.py` if the symmetry becomes important.

### Track 3 — Analyzer optimization (workbook-only, no code)

Optimizing the Analyzer's structure for the downstream UW handoff. Workbook edits, new sheets, named ranges, cell comments. Does not touch RR or T12 code. Workstream began 2026-05-07.

| What | Where |
| --- | --- |
| Decisions log | `OPTIMIZATION-DECISIONS.md` |
| Roadmap | 4 branches: 1 Correctness, 2 Handoff, 3 Analytical coverage, 4 Substrate. Branches 1+4 closed in v0.1.6. Branch 3 next. Branch 2 last. |

---

## Cross-cutting docs

| File | What it is |
| --- | --- |
| `journal.md` | Per-chat session log, newest at top. **Read the top entry before starting a new chat** — it usually has carry-forwards and known follow-ups. |
| `README.md` | Public-facing. Stale: still RR-only framing, doesn't mention T12 or the bundled-Analyzer flow. Update is a known follow-up but not a priority. |
| `CLAUDE.md` | This file. |

---

## Scope discipline (matters)

Per the journal 2026-05-06 retrospective, the project enforces "one track at a time" per chat. **A T12 chat does not edit RR files. An RR chat does not edit T12 files. A Track 3 chat does not touch any code.**

When a chat starts on track A and the user pivots toward track B, the assistant should stop and confirm: "We're now in [track B] territory. Fresh chat, or proceed knowing we're cross-cutting?" — rather than silently crossing.

Conversational examples should label placeholder text as `<REPLACE THIS>` so the user doesn't paste literal placeholders into commit messages (see `be3b134` for the cautionary tale).

---

## Open carry-forwards (as of 2026-05-11, post-substrate v0.1.8)

These are real backlogged items that previous chats deferred. They have a home; they're just not staffed yet.

### Closed 2026-05-11 (Substrate v0.1.8 — Branch 3 analytical coverage)

- ✓ **Branch 3 — Analytical coverage shipped (substrate v0.1.8).** New: T12 Analytics property-name & period-end auto-fill (B2 3-priority RR→T12→Cover, E2 LOOKUP rightmost-populated month), 5 chart objects on T12 Analytics K1:V44 (occupancy stacked col / rate-band histogram / payer-mix doughnut / 12-mo revenue trend / AL acuity doughnut), 5 conditional formula-driven note cells, Rent Roll Recon B2 latest-date default formula + dropdown DV, section K (IL unit-type mix + sqft + rate dispersion at rows 86-100), section L (MC auto-detect flat/tiered/FFS at rows 102-117). Migration via `migrate_to_v018.py` — 10 ops, 17-check verify, idempotent. Substrate cells A3 (RR Input) and A10 (T12 Input) reserved as property-name value targets (refinement 2026-05-11).
- ✓ **Track 1 — RR writer auto-stamp `Rent Roll Input!A3`** (RR v1.15.0). `analyzer_rr_writer.populate_t12()` now accepts `source_filename` kwarg and writes the derived property name. Closes the Track 1 carry-forward opened by substrate v0.1.8. New shared module `property_name.py` with `derive_property_name(filename)` strips date stamps + report boilerplate. Verified end-to-end on Salem / Briar Glen / Homestead filename patterns.
- ✓ **Track 2 — T12 writer auto-stamp `T12 Input!A10`** (T12 v0.2.1). `t12_normalizer_writer.populate_t12_input()` extends its existing `source_filename` parameter to also drive a property-name stamp at A10, via the shared `property_name.derive_property_name()` helper introduced in v1.15.0. Closes the Track 2 carry-forward opened by substrate v0.1.8. Combined smoke test confirms end-to-end pipeline: RR + T12 with same property → A3 + A10 populated; different uploads → each writer stamps its own derived name; T12 Analytics B2 (3-priority RR → T12 → Cover) resolves correctly.

### Closed 2026-05-08 (RR v1.14.0 — Homestead-style format)

- ✓ **Homestead Village Pensacola broker-condensed RR support** — shipped. Source headers `Unit ID` / `Cottage` / `Area` / `Category` / `BR/BA` / `Market / Mo YYYY` / `Actual / Mo YYYY` / `Status` now classify into the right canonical fields. Self-contained vacant rows (no resident name, but `Status=VACANT`) emit instead of being silently dropped — recovered 40 of 176 units that the prior parser was losing. Pre-cleaner cuts the end-of-sheet pricing-summary table at the `Avg Area` second-table header. `Occ w/ NTV` resolves to `Notice` (NTV rule ordered before `\boccupied\b`). Verified end-to-end: 176 rows out, IL=62/AL=62/MC=52 exact match, 0 unmapped.

### Closed 2026-05-08 (T12 v0.2.0 + Substrate v0.1.7, [PR #1](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/1))

- ✓ **`BrokerFinancialSummaryFormat` parser class** — shipped. Third T12 format detects via `Historical Performance` at A4, walks row 4 for the rightmost contiguous monthly run, applies banner-prefix disambiguation (`Direct Care | Payroll - Wages`) with subtotal-pop, and stops at `Non-Operating` / `Wages Analysis` / `Payroll Summary` banners. Reconciles Homestead to NOI $1,411,323.58 to the penny.
- ✓ **Cluster B — sign-convention guards + partial-year T12 handling** — shipped. `_check_sign_convention()` flags positive-sum CONCESSION rows (suffix-aware so banner names aren't false-positives). `_count_populated_months()` + optional `annualize_partial_year` flag. App surfaces a partial-year warning + sidebar checkbox.
- ✓ **`T12 Analytics!R102` lease formula** — fixed in substrate v0.1.7 with INDEX/MATCH against `T12 Raw Data!R:R`. UW Output R61 Lease will now display real values when source has lease data.
- ✓ **`T12 Raw Data` SUMIFS N501 vs N500 cosmetic** — swept (636 cells) in v0.1.7 migration.

### Medium priority (still open)

- **Branch 2 — Handoff readiness.** Pre-export gate, UW Export sheet (values-only mirror), metadata header, source trail. **Track 3 chat — Branch 2 was sequenced after Branch 3 per OPTIMIZATION-DECISIONS.md.** With Branch 3 + the Track 1/2 writer-side follow-ups all closed in the 2026-05-11 session, Branch 2 is the only remaining open Analyzer-optimization workstream.

### Low priority

- **README.md update** — bring it from RR-only framing to current dual-pipeline state.
- **Substrate version-detection bug suspected.** App's `_detect_substrate_version()` looks for `2nd Person Revenue` (v0.1.5 marker) in the Description_Map column B; v0.1.6/v0.1.7/v0.1.8 add no new Labels there, so the detector returns `v0.1.5` for any of v0.1.5+. Cosmetic — worth widening the marker list when the bundle next changes Label vocabulary.

---

## Conventions worth knowing

- **Versioning:** RR app version (`v1.X.Y`), T12 code version (`v0.X.Y`), Analyzer substrate version (`v0.1.N`). Three independent counters. Substrate version is stamped on `Cover!B8` and on every sheet's `AZ4` anchor cell.
- **Newest-at-top** in journal.md, CHANGELOG-RR.md, CHANGELOG-T12.md.
- **Migration scripts are idempotent** — re-running on an already-migrated workbook is a no-op. Pattern: `migrate_to_v01N.py` lives in `tools/migration/`. Always include a verification block at the end.
- **Per-sheet anchor cells** at `AZ1:AZ5` on every sheet — purpose / category / visibility / version / notes. Drives the Workbook Health Map section. Predictable location, verified empty across all sheets pre-v0.1.6.
- **Named ranges** are listed in OPTIMIZATION-DECISIONS.md (Named-range definitions section). Currently: `DescMap_Description`, `DescMap_Label`, `RR_Period_Date`, `T12_Period_Date`, `RR_Input_Data`, `T12_Input_Data`, `Property_Name`.
- **Workbook Health is hidden by default.** Right-click any tab → Unhide → Workbook Health to reach diagnostics, validation, and the workbook map.
- **`Sample Files/` is the local-only T12 fixtures directory** at repo root. Gitignored — files contain real property financials and must not be committed. The four canonical fixtures (Salem / Briar Glen / Homestead Pensacola Financial Summary / Homestead - March 2026 T12) live here and are referenced by `tools/verify_t12_v020.py`. New developers need to populate the directory before running the verify harness.

---

## Three openpyxl quirks that bite migrations

Documented from real bugs hit during migration script work:

1. `wb.defined_names[name] = DefinedName(...)` is the v3.x assignment form. `defined_names.append()` was removed.
2. Empty-string cell values render as `0` in Excel/Calc when read back. Leave the cell truly unset, or wrap with `=IF(ref="","",ref)` in formula context.
3. `Cell.alignment` is read-only. To mutate one attribute (e.g. indent), re-assign the whole `Alignment(...)` object preserving the others. Same for `Font`, `PatternFill`, `Border`.
4. (From 2026-05-06) `insert_rows()` shifts cells but not formula text — full-workbook regex sweep needed to update shifted refs. Lookbehind regex must include colons to catch range endpoints (`F15:Q15`). `insert_rows()` doesn't shift merged-cell range definitions; use `mr.shift(row_shift=delta)` to mutate bounds in-place — `unmerge_cells()` wipes displaced cell content.

---

## Starting a new chat — checklist for Claude

1. Read this file first.
2. Read the top entry of `journal.md` for the most recent session's carry-forwards.
3. Identify which Track the user's request belongs to. If ambiguous, ask before proceeding.
4. If the work is on Track 2 (substrate), assume migration script + spec update + changelog entry are all required deliverables — not just the code.
5. If context starts thinning, recommend spinning up a working MD (e.g. `OPTIMIZATION-DECISIONS.md` style) before the chat hits the wall.
