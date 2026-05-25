# CLAUDE.md

> Onboarding doc for any Claude session (chat or Claude Code) working on this repo. Read this first — it points to canonical truth and surfaces facts that previously had to be grubbed for.

**Last updated:** 2026-05-24 (Hotfix on v0.2.10/v0.2.11 bundled Analyzer — Excel was throwing "Repair Result … Removed Records: Formula from /xl/worksheets/sheet2.xml part" on open. Root cause: two label strings in the AR-module migrations started with `=` (`Dashboard!K13` v0.2.11 footnote `"= T12 bad debt − annualized AR write-offs"` and `AR & Collections!B47` v0.2.10 label `"= Implied closing AR"`). openpyxl's value setter classifies any leading-`=` string as a formula and writes it into `<f>`; Excel then strips the K13 one on open (couldn't parse it) and renders B47 as `#NAME?`. Both label strings rewritten with the leading `"= "` dropped — the "this row equals the formula next to it" relationship is structurally obvious from layout. Migration scripts (`migrate_to_v0210.py`, `migrate_to_v0211.py`) patched with inline comments + docstring notes so future label adds avoid the same trap; bundled `ALF_Financial_Analyzer_Only.xlsx` re-written in place (styling preserved). New 5th openpyxl quirk added to the "openpyxl quirks that bite migrations" section below. Whole-workbook re-scan shows zero remaining text-shaped formula cells. Dashboard!K11 AR variance formula was always valid and survived Excel's repair pass intact. Substrate stamp unchanged at v0.2.11. Earlier on 2026-05-23: Track 4 — UW Template integration Phase 0 ships: 72-concept modular mapping registry at `tools/uw_template/registry.json` against `ALF_UW_Template_v4.xlsx`, generator script + interactive HTML mind-map + MD/CSV trackers, `SPEC-UWT.md` + `CHANGELOG-UWT.md` seeded. UWT v0.1.0 — registry + docs only, no writer yet. 57/72 concepts cleanly mapped; 15 concepts flagged for Phase 1 disposition (Bad Debt placement, 2nd Person Revenue, monthly grid widening, EBITDA row, occupied beds, RR Analysis date format, monthly header overwrite). Earlier on 2026-05-23: substrate v0.2.10 + v0.2.11 — opens AND closes UW-BACKLOG **BL-0023** (AR & Collections module). New `AR & Collections` analytical sheet at index 8 (hidden by default; revealed when an AR aging file is uploaded). New `ar_normalizer.py` + `ar_writer.py` modules give the Streamlit app a third operator input (AR aging .xlsx/.csv) alongside RR and T12. Workbook Health B43 wrapped in AR-presence IF guard — `=IF('AR & Collections'!Z1=1, AR.C15, SUM('Rent Roll Input'!$X))` — so the RR-derived fallback is preserved bit-for-bit when no AR uploaded. P5 pre-export gate added at WH row 52 (inert "✓" when Z1=0, compares AR as-of to `RR_Period_Date` when Z1=1); READY-FOR-EXPORT summary shifted from row 52 → row 53 with B52 ANDed in. v0.2.11 adds Dashboard variance tile at K10:L13 + Cover AR module version line at A11/B11. `mappings.py` `DEFAULT_PAYER` extended with Managed Care + Medicare-Advantage / MCO rules (MA rules ordered BEFORE bare `\bmedicare\b`); `PAYER_FALLBACK` constant unchanged — AR ingest constructs `MappingSet(payer_fallback="Self-Pay + Other")` per-instance, RR behavior preserved. Bundled `ALF_Financial_Analyzer_Only.xlsx` forward-applied v0.2.4 → v0.2.10 → v0.2.11 directly per BL-0021 carry-forward (still skips intermediate v0.2.5-v0.2.9 substrate features). Live operator AR sample **PENDING** — built against synthetic at `tests/fixtures/ar/ar_synthetic_v01.xlsx` (12 residents × 14 cols, exercises all 7 payer buckets); fuzzy header rules will need expansion when real samples arrive. Cowork-authored design handoff (`2026-05-23-AR-Collections-Claude-Code-Handoff.md`) reviewed against codebase, 12 spec issues raised and decided here; handoff-back-to-Cowork block produced for spec Rev 2. **Only Pending backlog item: BL-0019** (persistent audit log, Track 1).)

---

## What this repo is

Two parallel pipelines feeding one underwriting workbook:

1. **Rent Roll Normalizer (RR)** — Streamlit app that turns any operator's rent roll into a normalized bed-level Excel output.
2. **T12 Normalizer (T12)** — parser + writer that turns various T12 financial-statement formats into a normalized monthly trending Excel.

Both pipelines populate a shared destination workbook: `ALF_Financial_Analyzer_Only.xlsx` (the "Analyzer"). The Analyzer is the underwriting substrate — RR drives Rent Roll Input, T12 drives T12 Input, and the analytical sheets reconcile + roll up to UW Output.

A separate downstream full-underwriting sheet (not in this repo) consumes UW Output. Optimizing the Analyzer to be a clean handoff to that sheet is an active workstream.

**Two product lines (added 2026-05-20).** Everything above is the **ALF** (senior-housing) product. A second **MF** (multifamily / conventional apartments) product line is being built in phases. The app gates on an **ALF/MF mode selector** shown right after login (`app.py`, just after `require_login()`), driven by `auth.allowed_modes(username)`. **Phase 0 (shipped):** the selector + access seam — every logged-in user currently sees both modes; MF renders a "coming soon" placeholder (`_render_mf_placeholder()`) and `st.stop()`s before the ALF pipeline, which runs **unchanged** in ALF mode. Per-user access-type gating (limiting a user to ALF-only or MF-only via a future `[auth.access]` secrets table) is deferred — `allowed_modes()` is the single seam where it lands. **Future MF phases (not built):** P1 MF RR normalizer → standalone MF workbook; P2 MF T12 + AR intake; P3 OM/comps extraction; P4 MF Analyzer + UW Template. MF has **no Analyzer** and shares none of the ALF care/payer/acuity data model — it's units/floorplans/leases. Sample data: `MF Docs/` (property *Hidden Lakes*: RR / T12 / AR / Sortable-RR). MF docs/specs will be added as those phases land; do not assume ALF conventions apply to MF.

**MF naming convention (locked 2026-05-20 — Option C, asymmetric prefix).** ALF code stays unprefixed (ALF = default, by virtue of being the original). **New MF code lives at the repo root with the `mf_` prefix**, mirroring the ALF module shape one-for-one. Shared utilities stay unprefixed. The MF naming convention:

| Concern | ALF (existing) | MF (planned) |
| --- | --- | --- |
| RR parser | `normalizer.py` | `mf_normalizer.py` |
| RR mappings (closed vocabularies) | `mappings.py` | `mf_mappings.py` |
| RR pre-cleaner | `pre_cleaner.py` | `mf_pre_cleaner.py` (if MF RR needs banner stripping) |
| RR reports | `reports.py` | `mf_reports.py` |
| Standalone RR workbook writer | `writer.py` | `mf_writer.py` |
| Analyzer RR translator | `analyzer_rr_translator.py` | `mf_analyzer_rr_translator.py` (Phase 4) |
| Analyzer RR writer | `analyzer_rr_writer.py` | `mf_analyzer_rr_writer.py` (Phase 4) |
| T12 parser | `t12_normalizer.py` | `mf_t12_normalizer.py` (parallel — MF chart of accounts differs even if file shape is similar) |
| T12 writer | `t12_normalizer_writer.py` | `mf_t12_normalizer_writer.py` |
| AR parser | *(none)* | `mf_ar_parser.py` |
| OM extractor | *(none)* | `mf_om_extractor.py` |
| Analyzer substrate (workbook) | `ALF_Financial_Analyzer_Only.xlsx` | `MF_Financial_Analyzer_Only.xlsx` (Phase 4) |
| Substrate migrations | `tools/migration/migrate_to_v0NN.py` | `tools/migration/mf_v0NN.py` (independent version stream) |
| Spec / changelog | `SPEC-RR.md` / `SPEC-T12.md` / `CHANGELOG-RR.md` / `CHANGELOG-T12.md` | `SPEC-MF.md` / `CHANGELOG-MF.md` |
| Shared (no prefix) | `auth.py` / `branding.py` / `property_name.py` / `period_date.py` / `app.py` | same — shared utilities stay unprefixed |
| Sample data | `Sample Files/` (gitignored) | `MF Docs/` (gitignored) |
| UW-BACKLOG | `UW-BACKLOG.md` | same file; BL-NNNN numbering is continuous across product lines (no separate MF numbering) |

**When the root gets crowded** (probably Phase 3-4 once 6+ `mf_*.py` files exist) — refactor into Option A subdirectory packages (`alf/` + `mf/`) then. The asymmetric prefix is explicitly a *near-term* choice that defers the subdirectory move until MF has enough code to justify it.

## Local clone path

`C:\One Drive Business\OneDrive - (na)\office\rent_roll_app` — Windows machine, PowerShell. **The repo lives inside OneDrive Business** (relocated 2026-05-21 from a former local-only location, which is dead — do not work from any old local copy outside OneDrive). Because git runs inside an actively-syncing OneDrive folder, follow the safety guidance in [`ONEDRIVE-WORKFLOW.md`](ONEDRIVE-WORKFLOW.md): run `tools\check_onedrive_sync.ps1` before git operations, push promptly after each commit, and never run destructive git ops mid-sync.

## Live deploy

https://rrnormalizer.streamlit.app/ — Streamlit Community Cloud, auto-deploys from `origin/main` on push (~30-60 sec lag). **Reboot-first rule:** if live behavior diverges from a verified local run on the same file, assume stale module cache and reboot from share.streamlit.io before debugging.

---

## Workstream tracks

The repo runs four parallel tracks. They share an Analyzer / UW pipeline but are otherwise independent. **Track N chats do not edit Track M files** without explicit cross-track authorization — see "Scope discipline" below.

### Track 1 — RR Normalizer (RR-side code)

| What | Where |
| --- | --- |
| Code | `app.py`, `normalizer.py`, `mappings.py`, `pre_cleaner.py`, `period_date.py`, `reports.py`, `writer.py` |
| Spec | `SPEC-RR.md` |
| Changelog | `CHANGELOG-RR.md` |
| Current version | RR v1.17.1 |

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
| Current substrate version | v0.2.11 bundled (chain through v0.2.11; bundled forward-applied v0.2.4 → v0.2.10 → v0.2.11 directly per BL-0021 — skips intermediate v0.2.5-v0.2.9 substrate features) |
| AR module code version | AR v0.1.0 (`ar_normalizer.py` + `ar_writer.py` — built against synthetic fixture, live operator sample pending) |

**Module naming gotcha (updated 2026-05-15 after BL-0011 — Track 1 disambiguation now fully complete at file + function + class level).** Four modules historically shared a `t12_` prefix because the destination workbook was originally a standalone T12 intake template — the prefix meant "operates on the T12-shaped destination workbook," not "operates on T12 data." Once the bundled Analyzer flow shipped (RR v1.12.0) the prefix became misleading. The two Track 1 modules have now been renamed; the remaining `t12_*` files are the legitimate T12-data modules. All four are imported by `app.py` and serve distinct roles:

| File | Function | Role |
| --- | --- | --- |
| `analyzer_rr_translator.py` | `translate_for_t12()` | Translates Condensed_RR vocabulary → Analyzer data-validation vocabulary (e.g. `1BR` → `1 Bedroom`). RR-side (Track 1). Was named `t12_translator.py` until 2026-05-14 (BL-0010) — see CHANGELOG-RR.md for the rename. The function name `translate_for_t12()` is the last `t12_` symbol on the Track 1 side; left alone for now since `for_t12` reads as "for the destination" rather than "for T12 data" — rename only if it becomes a confusion source. |
| `analyzer_rr_writer.py` | `populate_rr_input()` | Writes the translated RR into the Analyzer's `Rent Roll Input` sheet. RR-side (Track 1). Was named `t12_writer.py` until 2026-05-10. The function `populate_t12()` was renamed to `populate_rr_input()` and the exception class `T12CapacityError` was renamed to `AnalyzerRRCapacityError` on 2026-05-15 (BL-0011). |
| `t12_normalizer.py` | `parse_t12()` | Parses raw T12 financial statements (Yardi / MRI / BrokerFinancialSummary format registry). T12-side (Track 2). |
| `t12_normalizer_writer.py` | `populate_t12_input()` | Writes parsed T12 GL detail into the Analyzer's `T12 Input` sheet. T12-side (Track 2). |

If a future chat is tempted to delete one as "duplicate," check `app.py` lines 46-51 (imports) and the orchestration block around 880-940 — all four are wired in. The two surviving `t12_*` files now legitimately operate on T12 data; the prior cross-track artifacts are all cleaned up.

### Track 3 — Analyzer optimization (workbook-only, no code)

Optimizing the Analyzer's structure for the downstream UW handoff. Workbook edits, new sheets, named ranges, cell comments. Does not touch RR or T12 code. Workstream began 2026-05-07.

| What | Where |
| --- | --- |
| Decisions log | `OPTIMIZATION-DECISIONS.md` |
| Roadmap | 4 branches: 1 Correctness, 2 Handoff, 3 Analytical coverage, 4 Substrate. Branches 1+4 closed in v0.1.6. Branch 3 next. Branch 2 last. |

### Track 4 — ALF UW Template integration (downstream consumer)

Wiring the Analyzer's `UW Output` / `UW Export` surface into the downstream **ALF UW Template** workbook (per-deal populated copy). Workstream began 2026-05-23. Phase 0 (this initial release) is inspection + mapping only — no writer yet.

| What | Where |
| --- | --- |
| Spec | `SPEC-UWT.md` |
| Changelog | `CHANGELOG-UWT.md` |
| Handoff contract (Analyzer side) | `UW-OUTPUT-HANDOFF-CONTRACT.md` |
| Mapping registry (data) | `tools/uw_template/registry.json` |
| Artifact generator | `tools/uw_template/build_mapping_artifacts.py` |
| Mind-map visualizer | `tools/uw_template/mapping_mindmap.html` |
| Tracker (human-readable) | `tools/uw_template/MAPPING_TRACKER.md` |
| Tracker (diffable CSV) | `tools/uw_template/mapping_tracker.csv` |
| Template source file | `Sample Files/ALF_UW_Template_v4.xlsx` (gitignored) |
| Current code version | UWT v0.1.0 (Phase 0 seed — registry + docs only) |
| Mapped against template | `v4` |
| Mapped against substrate | v0.2.9 (Phase 0 was scoped before v0.2.10/v0.2.11 AR module shipped — substrate refresh deferred to Phase 1 since neither v0.2.10 nor v0.2.11 added new `UW Output` rows) |

**Modular registry pattern.** `registry.json` is keyed on semantic concepts (`egi`, `labor_care_staff`, `licensed_beds_il`, ...) with version-keyed targets (`targets.v4 = {...}`). Adding template `v5` later means extending the registry — no code change to the generator or future writer. Re-run `python tools/uw_template/build_mapping_artifacts.py` after any registry edit to regenerate the HTML / MD / CSV artifacts.

---

## Cross-cutting docs

| File | What it is |
| --- | --- |
| `journal.md` | Per-chat session log, newest at top. **Read the top entry before starting a new chat** — it usually has carry-forwards and known follow-ups. |
| `README.md` | Public-facing. Stale: still RR-only framing, doesn't mention T12 or the bundled-Analyzer flow. Update is a known follow-up but not a priority. |
| `ARCHITECTURE.md` | Full workflow + data-flow map: module inventory, public contracts (CONDENSED_COLUMNS, GLRow/T12ParseResult, substrate write-targets), Mermaid diagrams of both pipelines + the substrate + migration chain, and the modularity/extension points. Read when you need the system shape rather than the history. |
| `COSMETIC-CHANGES.md` | Tracker for visual/branding-only changes to the Streamlit app (color scheme, logo, fonts). Does not move the RR/T12/substrate version counters. Newest at top. |
| `CLAUDE.md` | This file. |

---

## Scope discipline (matters)

Per the journal 2026-05-06 retrospective, the project enforces "one track at a time" per chat. **A T12 chat does not edit RR files. An RR chat does not edit T12 files. A Track 3 chat does not touch any code.**

When a chat starts on track A and the user pivots toward track B, the assistant should stop and confirm: "We're now in [track B] territory. Fresh chat, or proceed knowing we're cross-cutting?" — rather than silently crossing.

Conversational examples should label placeholder text as `<REPLACE THIS>` so the user doesn't paste literal placeholders into commit messages (see `be3b134` for the cautionary tale).

---

## Open carry-forwards (refreshed 2026-05-21, post-substrate v0.2.9 chart-link fixes)

**The authoritative forward-looking list lives in [`UW-BACKLOG.md`](UW-BACKLOG.md).** Read that file for what's pending. The historical "closed" notes below stay here purely for traceability of how prior chats deferred work; the "Medium / Low priority" sub-sections that used to live here have been removed because they had drifted (e.g. "Branch 2 — Handoff readiness" was open for weeks here while it had already shipped as BL-0009 / substrate v0.2.0). When you want to know what's open, check UW-BACKLOG.md, not this section.

### Closed 2026-05-23 (Substrate v0.2.10 + v0.2.11 — AR & Collections module · BL-0023)

- ✓ **AR & Collections module shipped end-to-end** — third operator input (AR aging .xlsx/.csv) alongside RR and T12, with full upload → parse → write → populated-Analyzer pipeline behind the Streamlit UI. Four files of new code (`ar_normalizer.py`, `ar_writer.py`, `tests/fixtures/ar/ar_synthetic_v01.xlsx`, `tests/fixtures/ar/README.md`); two new migration scripts (`tools/migration/migrate_to_v0210.py`, `tools/migration/migrate_to_v0211.py`); modifications to `mappings.py` (additive — Managed Care bucket + MA/MCO rules, RR `PAYER_FALLBACK` unchanged), `app.py` (imports, version constants, sidebar AR uploader + conditional as-of date, orchestration Step 3, filename builder, caption, error handler, version-footer bump, stale `ANALYZER_SUBSTRATE_VERSION` constant corrected "0.2.4" → "0.2.11"), and the bundled `ALF_Financial_Analyzer_Only.xlsx` (forward-applied v0.2.4 → v0.2.10 → v0.2.11 directly).

- ✓ **Substrate v0.2.10 (`migrate_to_v0210.py`)** — New `AR & Collections` sheet at index 8 (between Monthly Trending and UW Output), HIDDEN by default. 163 cells across 5 spec sections (Aging Summary / KPIs / By-Payer Mix / Roll-Forward & Bad-Debt / Flags). `Z1` = AR presence flag (0=no data, 1=populated). Workbook Health!B43 wrapped in IF guard reading `Z1`: when Z1=0 → original `SUM('Rent Roll Input'!$X)` (bit-for-bit preserved); when Z1=1 → reads AR sheet `C15` Total AR. P5 pre-export gate added at WH row 52 ("AR period matches RR period — inert if no AR"); READY-FOR-EXPORT summary shifted row 52 → row 53 with B52 ANDed in. Verified zero external refs to WH!B52 before the shift. Cross-sheet pins: Monthly Trending!N26 (annualized EGI), T12 Analytics!E7 (avg occupied beds), T12 Analytics!E98 (bad debt expense), RR_Period_Date (named range). 19-check verify, idempotent, regression-clean.

- ✓ **Substrate v0.2.11 (`migrate_to_v0211.py`)** — Dashboard variance tile at K10:L13 (previously empty): K10:L10 title "BAD DEBT VARIANCE" (REVPOR-style navy fill), K11:L12 merged value formula `=IF('AR & Collections'!Z1=0,"— upload AR to populate",'AR & Collections'!C56)` (dormant when no AR, live ⚪/✓/⚠ when uploaded), K13:L13 footnote. Cover row 11 AR Module version line at A11/B11 (sits in the existing blank row between T12 Normalizer at R10 and Links section at R12 — no row inserts). 11-check verify, idempotent, regression-clean.

- ✓ **`ar_normalizer.py` (AR module v0.1.0)** — Public API: `parse_ar_file(path_or_buffer) -> AROutput`. Fuzzy header matcher (13 regex rules, first-match-wins, ordered specific→generic so "Over 90" disambiguates from "Over 60"). Per-row sum-check with ±0.01 tolerance. `_coerce_number` handles `$`, `,`, and `(parens-as-negative)`. Accepts both .xlsx (path or BytesIO with `.name`) and .csv inputs — verified 4 source shapes (CSV/XLSX × path/BytesIO) parse identically. Constructs `MappingSet(payer_fallback="Self-Pay + Other")` per-instance unless caller passes own MappingSet. `AROutput` + `ARRow` dataclasses define the contract `ar_writer.py` consumes.

- ✓ **`ar_writer.py`** — `populate_ar_collections(analyzer_bytes, ar_output, ...) -> bytes` matching RR/T12 writer pipeline shape. Writes Z1=1, optional C3 as-of override, all 5 §1 aging totals, all 7 §3 payer rows, §4 roll-forward optionals (only if present), §5 flag cells (computes payer-concentration flag inline; RR-join flags C62/C63 stubbed to 0). Flips sheet_state hidden → visible. Raises `AROutputError` when AR & Collections sheet absent (substrate < v0.2.10).

- ✓ **`app.py` Streamlit wiring** — AR file_uploader (.xlsx/.csv) added to sidebar after T12 block, with conditional as-of date override defaulting to the RR period date. Orchestration Step 3 after RR+T12 writers; AR is optional throughout (no gating; non-AR downloads unchanged). Filename builder refactored to a `name_parts` list that appends "AR" tag when AR uploaded. Version footer now `RR vX · T12 vY · AR vZ`. Error handler routes `AROutputError` with a clear "substrate v0.2.10+ required" message for users of override Analyzers.

- ✓ **`mappings.py` extension** — Added Managed Care bucket + rules for Medicare Advantage, MA Plan, MCO. MA rules placed BEFORE bare `\bmedicare\b` (first-match-wins, so MA receivables don't get tagged as traditional Medicare). `PAYER_FALLBACK` constant unchanged — AR uses `MappingSet(payer_fallback="Self-Pay + Other")` per-instance, RR behavior preserved. All 14 `normalize_payer` test cases pass (existing + new + AR-instance fallback).

- ✓ **Cowork handoff review** — User-supplied `2026-05-23-AR-Collections-Claude-Code-Handoff.md` (Rev 1) reviewed against codebase. 12 spec issues raised: terminology (xlsx vs webapp), payer taxonomy mismatch (spec 6 buckets vs Dashboard 6 vs mappings.py 5+fallback), impossible sheet position ("after T12 Analytics, before Dashboard" since Dashboard is index 1), Workbook Health AR-replace claimed additive but actually disruptive, 3 Dashboard tiles requested but K10:L13 only fits one, missing cell pins, etc. All 12 decided here to fit current webapp flow; handoff-back-to-Cowork block produced for spec Rev 2. The webapp is the canonical implementation; spec catches up next.

- ✓ **Live operator AR sample PENDING** — built against synthetic `tests/fixtures/ar/ar_synthetic_v01.xlsx` (12 residents × 14 cols, exercises all 7 mappings.py payer buckets incl. new Managed Care via "Medicare Advantage" / "MCO" / "UHC MA Plan" rows). Fuzzy header rules will need expansion when real operator headers arrive. Sample-file convention: live operator samples go in `Sample Files/` (gitignored), synthetic stays in `tests/fixtures/ar/` (committed) as structural reference.

- ✓ **Deferred (intentionally out of scope for v0.1.0):** AR↔RR row-level join for §5 C62/C63 flags (resident-in-90+-with-concession, vacant-with-non-zero-AR) — needs ar_writer extension to read Rent Roll Input from the same workbook. Stubbed to 0. Standalone CHANGELOG-AR.md (consolidated into CHANGELOG-T12.md under v0.2.10/v0.2.11 for now).

### Closed 2026-05-21 (Substrate v0.2.9 — Dashboard chart-link fixes on the chain · BL-0020)

- ✓ **`migrate_to_v029.py` ports BL-0020's three chart-data-link fixes onto the migration chain.** Problem it solved: `migrate_to_v027.py` inserts the Dashboard from `v027_assets/dashboard_template.xlsx`, which has three buggy chart links — so any workbook forward-rolled through the chain got broken charts, even though the bundled file (user's hand-edited copy) had them fixed. v0.2.9 surgically corrects: Fix 1 — `Dashboard!C97:C108` EGI series `Monthly Trending` row 21 (Housekeeping) → row 26 (EGI); Fix 2 — `Dashboard!F90:F93` Payer Mix pie `Rent Roll Recon` col B (unit counts) → col I (revenue ratios); Fix 3 — doughnut chart [1] payer rows moved `O14:O19` → `O9:O14` contiguous, series range shrunk `$O$8:$O$19` → `$O$8:$O$14` with rebuilt 7-pt caches. No template asset / no row inserts. Idempotent — the data-move is guarded to the buggy state (`O9` empty AND `O14 == "Medicaid"`), so re-runs and already-fixed Dashboards aren't corrupted. Full chain v0.2.4 → v0.2.9 tested clean. **Resolved the v0.2.8 collision** — BL-0020 is now unambiguously v0.2.9, BL-0022 keeps v0.2.8, and the closed PR #34 branch's `migrate_to_v028.py` is superseded (do NOT revive — use `migrate_to_v029.py`). Bundled file unchanged (stays user-managed v0.2.4 per BL-0021); v0.2.9 only makes the *chain* reproduce correct charts.

### Closed 2026-05-19 (Bundled-Analyzer wholesale reset · BL-0021 + BL-0020)

- ✓ **Bundled `ALF_Financial_Analyzer_Only.xlsx` wholesale-replaced with user's hand-edited Excel copy** (BL-0021, NOT a substrate bump). User opted to replace the v0.2.7-derived bundled file with their OneDrive copy at `C:\One Drive Business\OneDrive - (na)\office\rent_roll_app\ALF_Financial_Analyzer_Only.xlsx`. Bundled file now has `Cover!B8 = "v0.2.4"` and lacks BL-0012 (Section M6), BL-0016 (AH4 fill), BL-0017 (144-cell intentional-blank), and BL-0018 (v0.2.7 Dashboard structural with AZ anchors). User informed of regressions before approving (twice). Migration scripts v0.2.5 → v0.2.8 stay in `tools/migration/` for reproducibility. **The bundled file is now a user-managed artifact** — future substrate work needs to either accept regressions or forward-roll first via the migration chain.
- ✓ **Dashboard `N1` = `"Last updated: 2026-05-19"`** stamp per user request (BL-0021 second deliverable). Static text, Calibri 10pt italic gray `FF595959`, right-aligned. Position: between the title merge (`B2:M2`) and the right-side data table at `O1:Q3`. Static date intentional (intent = "when was the file last edited," not "always show today" via TODAY()).
- ✓ **BL-0020 chart-data-link fixes** present in bundled file via wholesale-copy (PR #34 / `migrate_to_v028.py` closed unmerged but the fixes themselves are in the user's authored Dashboard). `Dashboard!C97:C108` → EGI row 26 (was Housekeeping row 21), `Dashboard!F90:F93` → revenue ratios at col I (was unit counts at col B), doughnut chart series range `$O$8:$O$14` with contiguous data at O9:O13 (was `$O$8:$O$19` with empty slices). These fixes were later ported onto the migration chain proper as `tools/migration/migrate_to_v029.py` (substrate v0.2.9, 2026-05-21 — see the "Closed 2026-05-21" entry above). The original PR #34 branch `claude/bl-0020-dashboard-data-link-fixes` (which held a now-superseded `migrate_to_v028.py` + `v028_assets/`) has been **deleted** — use `migrate_to_v029.py` instead.

### Closed 2026-05-19 (Substrate v0.2.7 — Dashboard sheet redesign · BL-0018)

- ✓ **`Investment Dashboard` sheet replaced with redesigned `Dashboard` sheet.** Sheet count stays at 15. User authored the new sheet externally in Excel and dropped it in on 2026-05-19. New sheet: 437 cells, **6 native Excel charts** (BarChart × 2 + DoughnutChart + 3 more titled charts), 72 merged ranges, 17-col visible layout (B:Q), navy tab color `FF1F4E79`, AZ1:AZ5 anchor block. Pure formula-reference layer — 96 unique cross-sheet refs (Cover B5, T12 Analytics × 52, Rent Roll Recon × 31, Monthly Trending × 12); 95 resolve to populated cells on v0.2.6, the one outlier is `Cover!B5` (Property Name, user-populated at runtime via `Property_Name` named range). Migration via `tools/migration/migrate_to_v027.py` — sources from committed template asset `tools/migration/v027_assets/dashboard_template.xlsx` (26 KB single-sheet workbook). Cells copied via the established `_copy_cell` helper; charts copied via `copy.deepcopy(chart)` since openpyxl Chart objects carry their series references as string formulas that survive deep-copy. Anchor list re-roll: 15-sheet list updated `"Investment Dashboard"` → `"Dashboard"`. 14-check verify, idempotent (gate checks Cover!B8 == v0.2.7 AND Dashboard at index 1 AND Investment Dashboard absent). **Drift not carried forward:** the user's authored file was based on v0.2.4 and had been round-tripped through Google Sheets / LibreOffice (re-introducing `_xludf.MINIFS` / lowercase `minifs` prefixes on RR_Calc + Rent Roll Recon, missing the v0.2.5 Section M6 rows, missing the v0.2.6 BL-0016 AH4 fill, missing the v0.2.6 BL-0017 144-cell intentional-blank styling, plus an accidental T12 Analytics anchor relocation AZ→AM). Migration starts from the current v0.2.6 base and only adds the Dashboard, preserving all v0.2.5 + v0.2.6 substrate work intact (post-migration spot-checks confirmed). UW-BACKLOG is now empty.

### Closed 2026-05-16 (Substrate v0.2.4 — Investment Dashboard sheet)

- ✓ **Investment Dashboard sheet added at workbook front.** New `Investment Dashboard` sheet inserted at index 1, immediately after `Cover` (sheet count 14 → 15). 97 rows × 7 cols (B2:H98), 335 styled cells, sourced from the Beaufort populated Analyzer (Rent Roll 1.31.26 + T-12 1.31.26). Pure formula-reference layer over `T12 Analytics` + `Rent Roll Recon` — no existing-data mutation, no row inserts, no named-range additions, no formula on any other sheet changes. Seven sections: (1) AT-A-GLANCE headline tiles (rows 7-9: Beds / Occupancy / EGI / EBITDARM margin / Going-In Cap / Price-per-Bed), (2) OCCUPANCY & CAPACITY (rows 11-17), (3) REVENUE & RATE PERFORMANCE (rows 19-28), (4) MARGIN & COST STRUCTURE (rows 30-46), (5) VALUATION & ACQUISITION (rows 48-57), (6) PAYER MIX (rows 59-68), (7) AL CARE LEVEL DISTRIBUTION (rows 70-81), plus KEY RISKS & NORMALIZATION CALLOUTS (rows 85-94, 🔴🟠🟢 flagged). Migration via `tools/migration/migrate_to_v024.py` — copies sheet from a committed template asset at `tools/migration/v024_assets/investment_dashboard_template.xlsx` (335 cells with full style preservation), 11-check verify, idempotent (gate checks both version stamp AND sheet-exists-at-position-1). Substrate version stamp v0.2.3 → v0.2.4 across `Cover!B8` and all 15 anchor `AZ4` cells (anchor list grows 14 → 15 because Investment Dashboard joins). All but one of the 56 distinct dashboard cell refs into `T12 Analytics` resolve to populated cells (`T12 Analytics!E117` Purchase Price is an analyst-input cell, expected blank). Cross-track work — user-authorized 2026-05-16 (chat was originally a Track 1 password-gate session for the Streamlit app; user explicitly pivoted).

### Closed 2026-05-14 (Substrate v0.2.3 — Rent Roll Recon row 16 GPR fix · BL-0015)

- ✓ **Rent Roll Recon row 16 — "RR gross contracted base rent / mo" mis-calculating against its own H-note intent.** User-reported on 2026-05-12 against the populated Homestead v0.1.10 Analyzer: row 16 read $565,140 but the Rent Roll Input Market Rate total was $809,567 — and the row's H-column note ("Gross contracted rates before concessions") clearly described the latter. Originally implemented as substrate v0.1.11 in PR #12; PR went stale while main moved through v0.1.12 → v0.2.2 (and v0.1.11 substrate number was reused on main for an unrelated chart-axis fix). Re-implemented here as v0.2.3 against the current 14-sheet anchor list. Fix: B16/C16/D16 rewritten to sum `'Rent Roll Input'!$G` over all units (no status filter) by care type, A16 label rewritten to "RR Gross Potential Rent / mo  (Market × all units)", H16 note rewritten to state GPR semantics + identify row16-vs-row17 gap = vacancy + market-vs-actual premium. Rows 17-20 unchanged. Migration via `migrate_to_v023.py` (3 ops, 9-check verify, idempotent). Closes UW-BACKLOG BL-0015.

### Closed 2026-05-11 (RR v1.16.0 + Substrate v0.1.10 — Data-capture expansion)

- ✓ **RR per-resident charges + housing-revenue fields previously dropped now captured.** User reported (against RR v1.15.0) that the Homestead populated Analyzer was missing 2nd Person rent, Pet, H/K, Laundry, Misc., and other per-resident charges. v1.15.1 (keyword widening — `looks_care` heuristic now catches `pet`, `housekeeping`, `h/k`, `laundry`, `misc`, `diabet`) recovered 13 IL residents' Other LOC $. v1.16.0 added 7 new dedicated columns: `2nd Person Rent $` (4 couples populated $650-$800 in Homestead fixture), `Move-out Date`, `Balance`, `Notes` (33 rows captured incl. "HK $100 eff 3/1- sec occ $650"), `Market PSF`, `Actual PSF`, `ACH`. Companion substrate v0.1.10 adds matching headers at Rent Roll Input!V4:AB4 and extends Total Monthly Rev formula to include +V (2nd Person Rent). 2P rent now reconciles 1:1 against the T12 substrate's pre-existing `2nd Person Revenue` Label. End-to-end verified: Sandra & Darryl Owens (Homestead A14) splits source's $750 ancillary total correctly into V=$650 (SP) + O=$100 (H/K). Cross-track work (Track 1 normalizer / writer / app + Track 3 substrate migration) — user-authorized on 2026-05-11.

### Closed 2026-05-11 (Substrate v0.1.9 — Period-default bug fix)

- ✓ **Rent Roll Recon!B2 period dropdown empty / no latest-date default in Excel** — root cause: pre-existing `_xludf.minifs(...)` formulas in RR_Calc!A2:A13 (Google Sheets / LibreOffice UDF prefix that Excel doesn't recognize → `#NAME?` → IFERROR-empty). v0.1.9 migration drops the `_xludf.` prefix from all 12 RR_Calc cells (native MINIFS works) AND rewrites Rent Roll Recon!B2 to read directly from `Rent Roll Input!$S$7:$S$606` via MAX, so the latest-date default works even if RR_Calc ever drifts again. Migration via `migrate_to_v019.py` (3 ops, 6-check verify, idempotent).

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

## Five openpyxl quirks that bite migrations

Documented from real bugs hit during migration script work:

1. `wb.defined_names[name] = DefinedName(...)` is the v3.x assignment form. `defined_names.append()` was removed.
2. Empty-string cell values render as `0` in Excel/Calc when read back. Leave the cell truly unset, or wrap with `=IF(ref="","",ref)` in formula context.
3. `Cell.alignment` is read-only. To mutate one attribute (e.g. indent), re-assign the whole `Alignment(...)` object preserving the others. Same for `Font`, `PatternFill`, `Border`.
4. (From 2026-05-06, expanded 2026-05-15 after BL-0001) `insert_rows()` shifts cells but not formula text — full-workbook regex sweep needed to update shifted refs. Lookbehind regex must include colons to catch range endpoints (`F15:Q15`). `insert_rows()` doesn't shift merged-cell range definitions; use `mr.shift(row_shift=delta)` to mutate bounds in-place — `unmerge_cells()` wipes displaced cell content.

   **The qualified-range-endpoint trap (BL-0001 / `migrate_to_v021.py`).** When a formula contains a cross-sheet qualified range like `T12_Calc!$N$1:$N$500`, the qualified-pattern regex matches the *first* cell (`$N$1`) as a single cross-sheet ref — the *endpoint* (`$N$500`) falls outside that match and is then re-caught by the unqualified-ref regex, which assumes it's a same-sheet reference and bumps it on row inserts. Result: the endpoint shifts (e.g. `$N$500` → `$N$505` after a 5-row insert) while everything else in the qualified range stays put. Surfaces as off-by-N SUMIF/SUMIFS drift after migrations.

   **Canonical fix:** capture template formulas you intend to *replicate* (e.g. for new rows) **AFTER** the shift sweep, not before. Reading post-shift bakes in any drift on the template row's own range endpoints, so every replicated row's endpoints stay consistent with each other (even if they're all "wrong" relative to the table size — but consistent matters more than absolute, and the v0.1.7 sweep proved harmless when endpoints are one row past the data). See `tools/migration/migrate_to_v021.py` `step_t12_raw_data()` lines 312-321 for the worked example. The v0.1.6 / v0.1.7 "SUMIFS N501 vs N500 cosmetic" was the first symptom of this same artifact.

5. (From 2026-05-24, after the v0.2.10/v0.2.11 sheet2.xml repair fix) **Label strings that start with `"="` are silently misclassified as formulas.** openpyxl's `Cell.value` setter routes any `str` whose first character is `=` into `data_type='f'` and writes it into the `<f>` element on save. Excel then tries to parse the body as a formula — best case it renders `#NAME?`, worst case it strips the cell on open with the dreaded "Removed Records: Formula from /xl/worksheets/sheetN.xml part" repair dialog. This bit `Dashboard!K13` (v0.2.11 footnote `"= T12 bad debt − annualized AR write-offs"`) and `AR & Collections!B47` (v0.2.10 label `"= Implied closing AR"`) — both intended as plain labels with a leading `=` for typographic effect.

   **Canonical fix:** **never start a label string with `=`.** The "this row/tile equals the formula to its right/below" relationship is structurally obvious from the surrounding layout; the `=` prefix is implied. If you absolutely need the visible `=` glyph, use a non-`=` look-alike (`≈`, `≡`, `:`) or prefix the literal text with a non-breaking space (`" = ..."`) so `startswith("=")` returns False. Either way, add an inline comment so the next reader doesn't "fix" it back. Detection: a whole-workbook scan that flags any `data_type=='f'` cell whose formula body parses as a plain English phrase (no parens, no operators) catches this class — see the diagnostic snippet under commit `24dbafe`.

---

## Starting a new chat — checklist for Claude

1. Read this file first.
2. Read the top entry of `journal.md` for the most recent session's carry-forwards.
3. Identify which Track the user's request belongs to. If ambiguous, ask before proceeding.
4. If the work is on Track 2 (substrate), assume migration script + spec update + changelog entry are all required deliverables — not just the code.
5. If context starts thinning, recommend spinning up a working MD (e.g. `OPTIMIZATION-DECISIONS.md` style) before the chat hits the wall.
