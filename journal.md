# Chat Journal — rent-roll-normalizer

A running log of substantive chat sessions on this repo. One entry per session.
Each entry captures: scope, what shipped, what drifted, and the commit(s) the
session produced. Use this for handoff between chats and for tracing why a
particular commit looks the way it does.

Newest at top.

---

## 2026-05-07 — T12 Substrate v0.1.6 (Analyzer optimization, Branches 1+4)

**Started as:** "Optimize the analyzer before it goes into the full underwriting sheet." Read SPEC-RR, SPEC-T12, both changelogs, README, and the prior journal entry. Walked the bundled `ALF_Financial_Analyzer_Only.xlsx` to ground the work.

**Stayed as:** A T12 chat throughout. The architectural constraint set up front ("additive only — new sheets / sections / cells / named ranges OK; existing aggregators untouched") held cleanly. RR-side files not touched.

### Frame

Drew a 4-branch optimization mind map: correctness, handoff readiness, analytical coverage, substrate. User picked Branches 1 + 4 first (foundation), then 3 (depth), then 2 (handoff). Spun up `OPTIMIZATION-DECISIONS.md` in the chat as the running decisions log per "if context is going to thin, recommend an MD" preference. Net 14 decisions logged, 8 "discovered facts" sections from grounding investigation.

The journal's "one track at a time" lesson from 2026-05-06 informed an explicit boundary call mid-design: Cluster B (sign guards + partial-year T12) was identified as code-side work and deferred to a future Track 2 chat (D-12) rather than crossing tracks within this session.

### What shipped

**Substrate v0.1.5 → v0.1.6.** All workbook-side. Built and validated end-to-end inside this chat:

- **`tools/migration/migrate_to_v016.py`** — idempotent migration script, ~500 lines. Operates in order: add Cover (front) → Cluster A formula fixes → add Workbook Health (back, hidden) → populate AZ1:AZ5 anchors on all 13 sheets → add 5 named ranges → wire `T12 Analytics!B2` to `=Property_Name` → add 5 cell comments → run 11 verification checks. Smoke-tested on the actual bundled Analyzer, then LibreOffice-recalc'd to confirm 0 formula errors across all 13 sheets.

- **Cluster A — Correctness fixes (4 ships):**
  - `Rent Roll Recon!H20` chunked-literals rewrite. The `_xlfn._LONGTEXT` artifact was the headline bug — caused by Excel's per-literal 255-char cap blowing up the 5-item investigation lists in cases 3 and 4 of the diagnostic. New formula has 6 literals max-255-chars, joined with `&`. Total formula 1068 chars; round-trips clean through openpyxl with no `_xlfn._LONGTEXT` and resolves to the right diagnostic message on a populated workbook.
  - `UW Output!R29` (Bonus wages) sibling-pattern fill against `T12 Analytics!E64`/`F64`.
  - `UW Output!R57` (Bad debt expense) sibling-pattern fill against `T12 Analytics!E98`/`F98`.
  - `UW Output!R61` (Lease / ground lease) — paper-over fill per D-04. Points at `T12 Analytics!E102`/`F102` even though those still return `=0`. Indent fixed (0.0 → 1.0) to match siblings R60 / R62.

- **Cluster C — Workbook Health (1 new sheet):**
  - Hidden, last position. Three sections: Workbook Map (formula-driven, 13 rows pulling from per-sheet `AZ1:AZ5`), Validation (7 live $ checks with ✓/⚠ status, ±$1 leakage tolerance per D-08), Diagnostics (capacity utilization from existing UW Output cells, 3 version pills from Cover, last-open timestamp).

- **Cluster D — Cover + supporting work:**
  - Cover sheet (first tab, visible). 4 blocks: Property / Versions / Links / About. Property name at B5 is the canonical home of the new `Property_Name` named range.
  - Anchor cells `AZ1:AZ5` populated on all 13 sheets — predictable location, verified empty pre-migration on every existing sheet (rightmost data column on any sheet is U; AZ is column 52).
  - 5 named ranges: `RR_Period_Date`, `T12_Period_Date`, `RR_Input_Data`, `T12_Input_Data`, `Property_Name`. Joins existing `DescMap_Description` and `DescMap_Label`.
  - `T12 Analytics!B2` (was empty) wired to `=Property_Name`.
  - 5 light cell comments on the hardest-to-decode formulas: `Monthly Trending!B5` (T12 rollup INDEX/MATCH pattern), `T12 Analytics!E37` (GPR), `T12 Analytics!E52` (EGI), `T12 Analytics!E110` (EBITDAR after mgmt fee), `Rent Roll Recon!H20` (RR↔T12 gap diagnostic).

### Discovered facts worth carrying forward

Logged in `OPTIMIZATION-DECISIONS.md` as F-1 through F-8. Highlights:

- **`Rent Roll Recon!H20 _xlfn._LONGTEXT` root cause** (F-1) — Excel's per-literal 255-char cap, not a missing function or anything more exotic. The fix is mechanical once you see it.
- **UW Output R65 was misclassified as a bug initially** (D-03) — turned out to be a visual section separator (bold + navy `FF2F5597` fill, identical to R69). Correct call after inspecting the formatting was to drop it from the bug list, not invent an NOI definition.
- **The bundled Analyzer was missing the Cover sheet** that `SPEC-RR.md` lists as part of the expected structure (F-3). Spec was right; bundle had drifted. Now fixed.
- **`T12 Analytics!R102` is still `=0`** (F-2 / A-5) — was supposed to get an INDEX/MATCH per the v0.1.4 substrate plan, but never landed. Logged as deferred for v0.1.7+; it's the only reason `UW Output!R61 Lease` will display `$0` after this migration.

### Process lessons from this session

1. **Showing trumps explaining when a question lands wrong.** When the user asked "where is H20?" instead of picking a fix path, the right move was to draw the spreadsheet grid showing exactly which cell was broken and what its four output cases are, before re-asking. Worked. Also worth doing the same when "what's a named range?" landed — minimal Excel literacy assumption is safer than maximal.
2. **Verifying anchor location empirically before committing the convention.** The `AZ1:AZ5` choice was checked against every sheet's `max_column` before being proposed; otherwise it could have collided with one of the analytical sheets that legitimately uses high column letters.
3. **The migration script's verification block is worth its weight.** 11 boolean checks at the end of `migrate_to_v016.py` caught the AZ5-empty-string-renders-as-0 issue immediately on first run — fix took one minute. Without the verification, that would have shown up as a cosmetic bug an analyst spotted later.

### Commits this session

To produce after pulling the migration script and docs into the repo:

- `<hash>` — `Substrate v0.1.5 -> v0.1.6: Cover + Workbook Health, named ranges, H20 fix, UW Output gaps, anchor cells, light comments`

(One commit covers everything. Alternative: split into "Cluster A bug fixes" + "Clusters C/D new sheets and convention" + "Cell comments and named ranges" if granular history is preferred — three commits, same diff total.)

### Files at session end

- New: `tools/migration/migrate_to_v016.py`
- New: `OPTIMIZATION-DECISIONS.md` (carry-forward decision log; lives at repo root)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (substrate v0.1.6, regenerated by running the migration on the v0.1.5 file). **Filename unchanged** — `app.py` v1.12.0 references this exact path in `_load_analyzer()`. The chat-output `analyzer_v016.xlsx` was a within-chat naming artifact only; final filename in the repo is `ALF_Financial_Analyzer_Only.xlsx`.
- Updated: `SPEC-T12.md` (current-version bump + new v0.1.6 entry in Template substrate section)
- Updated: `CHANGELOG-T12.md` (new `[Substrate template v0.1.6]` entry at top)
- Untouched: `SPEC-RR.md`, `CHANGELOG-RR.md`, `app.py`, `t12_normalizer.py`, `README.md`

### Known follow-ups for future chats

- **Cluster B (Track 2 chat)** — sign-convention guards + partial-year T12 handling. Code-side work in `t12_normalizer.py` and `app.py`. Should reference `OPTIMIZATION-DECISIONS.md` D-12 boundary as the carry-forward pointer.
- **Branch 3 (Analytical coverage)** — sensitivities, scenarios, debt/returns, IL/AL/MC expense splits. The next optimization round per the mind map sequencing.
- **Branch 2 (Handoff readiness)** — designed last, since it depends on what Branch 3 adds to UW Output.
- **`T12 Analytics!R102` lease formula fix** (substrate v0.1.7) — small, scoped, eligible to bundle with whatever other aggregator work earns its keep next.
- **README.md** — still RR-only framing per the prior journal note. Independent task.

---

## 2026-05-06 — T12 Substrate v0.1.5 (Homestead Pensacola) + RR v1.12.0 (scope drift)

**Started as:** T12 chat. Read SPEC-T12.md + CHANGELOG-T12.md. Task: process the Homestead Pensacola broker financial summary file as a one-off.

**Ended as:** A cross-track session that also produced an RR v1.12.0 release.

**Scope discipline note:** This was a T12 chat. The RR-side work that landed mid-session (`app.py` v1.12.0, `CHANGELOG-RR.md`, `SPEC-RR.md` rewrite) was scope creep — should have been a separate RR chat per the "one track at a time" principle in `SPEC-T12.md`. The inflection point was the user's question about default-vs-uploaded Analyzer behavior in the app, which is RR territory. Should have been flagged with "this is RR scope — fresh chat, or proceed knowing we're crossing tracks?" and wasn't. After this session, `SPEC-T12.md` got a new line in the maintenance protocol making the rule explicit: T12 chats stop and confirm before touching RR files.

### What shipped

**T12 work (in scope):**

- **Homestead Pensacola broker file** (`2026-03_Homestead_Village_Pensacola_Financial_Summary.xlsx`) processed via Option C — one-off paste validation now, with v0.2.0 to ship a `BrokerFinancialSummaryFormat` class once mapping logic is proven.
- **60 new Description_Map entries** validated against Homestead. 21 are prefixed (`[Section] | [Description]` for ambiguous descriptions like `Payroll - Wages` which appears in 8 different departments). Three Second Persons rows initially mapped to Base rent — IL/AL/MC.
- **Substrate template v0.1.5** — added new revenue Label `2nd Person Revenue` so per-bed base rate calculations (Base rent ÷ ADC) stay clean. Inserted as a new row in `Monthly Trending` (R19) and `T12 Raw Data` (R15), with the EGI formula at the post-shift R21 rewritten to include the new R19 in the sum without disturbing R8 (Total base rent). Closed Label vocabulary grows from 54 → 55.
- **`tools/migration/migrate_to_v015.py`** — idempotent migration script. Three openpyxl quirks debugged during build: (1) `insert_rows()` shifts cells but not formula text — required full-workbook regex sweep across 833 formulas; (2) regex lookbehind originally excluded colons, breaking range endpoint refs like `F15:Q15`; (3) `insert_rows()` doesn't shift merged-cell range definitions, and using `unmerge_cells()` to fix it wipes displaced cell content — solution: `mr.shift(row_shift=delta)` to mutate bounds in-place.
- **End-to-end verification** on Homestead Pensacola: GL rows 101 / UNMATCHED 0 / Source $→Operating $ leakage $0.00 / EBITDAR $1,411,323.58 = broker NOI to the penny. R8 Total base rent $6,951,136.46 (clean, no Second Persons). R19 2nd Person Revenue $32,220.49 (NEW, isolated).
- **CHANGELOG-T12.md `[Substrate template v0.1.5]`** entry added documenting the change, the three openpyxl quirks, and the verification numbers.
- **SPEC-T12.md** updated: current version line bumped to "Template substrate at v0.1.5", v0.1.5 added to the Template substrate section.

**RR work (out of scope for a T12 chat — should have been a separate session):**

- **`app.py` v1.11.0 → v1.12.0**:
  - Bundled `ALF_Financial_Analyzer_Only.xlsx` loaded silently as default destination workbook (was: required upload)
  - "Advanced — override Analyzer template" expander at sidebar bottom for session-only overrides
  - Sidebar reorganized: Inputs (Rent Roll → Period Date → Raw T12) → Property Defaults → Optional → Output → Advanced
  - T12 parsing no longer requires uploaded Analyzer (bundled descmap is canonical)
  - Combined download produces populated Analyzer from RR alone (T12 optional)
  - Bug fix: T12 status panel had duplicate `tc.metric()` calls — first month metric was being overwritten by last month metric. 4-col → 5-col layout, all five metrics now display.
  - New helpers: `_detect_substrate_version()`, `_load_analyzer()`
- **`CHANGELOG.md` → `CHANGELOG-RR.md`** (rename via `git mv` for symmetry with `CHANGELOG-T12.md`)
- **`SPEC.md` → `SPEC-RR.md`** (rename + full content rewrite to bring it from v1.9.0 state up to v1.12.0 + Analyzer-source section + versioning convention guidance + doc rename history)
- **`CHANGELOG-RR.md` `[1.12.0]`** entry added documenting the RR v1.12.0 changes
- **`CHANGELOG-RR.md` `[T12 Normalizer cross-reference]`** entry added pointing readers to `CHANGELOG-T12.md` for the parallel T12 stream that landed during the v1.10.0–v1.12.0 window

### Commits produced this session

- `18f55bc` — `Substrate v0.1.4 -> v0.1.5: add '2nd Person Revenue' Label` *(T12 — in scope)*
- `be3b134` — `Analyzer: <describe your edit in 1 line>` — User edited the bundled Analyzer's `Rent Roll Recon!B2` dropdown for Period Selection mid-chat. Commit message used the literal placeholder text from a workflow example I'd given earlier; not corrected to avoid the rebase + force-push complexity. Real description: "Minor Dropdown data change: Rent Roll Recon B2 Dropdown for Period Selection". *(Cosmetic Analyzer edit — borderline, technically substrate territory but contains zero substrate-version-affecting changes)*
- `2331b32` — `RR v1.11.0 -> v1.12.0: bundled Analyzer default, sidebar reorg, T12 panel bug fix` *(RR — out of scope for this T12 chat)*

### Files at session end

- T12 docs: `SPEC-T12.md` and `CHANGELOG-T12.md` reflect substrate v0.1.5
- RR docs: `SPEC-RR.md` and `CHANGELOG-RR.md` reflect app v1.12.0 (renamed from `SPEC.md` / `CHANGELOG.md`)
- Bundled Analyzer: `ALF_Financial_Analyzer_Only.xlsx` at substrate v0.1.5, plus the `be3b134` cosmetic dropdown edit
- Migration script: `tools/migration/migrate_to_v015.py`
- README.md: untouched (still RR-only framing — reflects pre-T12 era)

### Known follow-ups (NOT for this chat — for future sessions)

- **README.md is stale.** Still describes the project as RR-only. Doesn't mention T12 normalizer, doesn't mention the bundled Analyzer flow, doesn't link to SPEC-T12.md or CHANGELOG-T12.md. Worth a separate pass — could be a cross-cutting chat or could be split as a small RR-side update.
- **`be3b134` commit message** is the literal placeholder text. If polish matters more than chat-time-spent, fix later via interactive rebase + force-push.
- **v0.2.0 BrokerFinancialSummaryFormat class** (per Option C plan) — promote Homestead's mapping logic into `t12_normalizer.py` as a third format alongside Yardi and MRI. Separate T12 chat.
- **Pre-existing `Rent Roll Recon!H20` `#NAME?`** in populated outputs — substrate-level issue noted in CHANGELOG-T12 [0.1.0]. Not introduced this session.
- **T12 Raw Data SUMIF range** slightly extended during v0.1.5 migration — some shifted rows now reference `T12_Calc!$N$1:$N$501` instead of `$N$1:$N$500`. Harmless (T12_Calc has 500 data rows so row 501 reads empty), but cosmetically inconsistent. Worth tightening if a future migration script touches T12 Raw Data rows.

### Process lessons

1. **Stop at the boundary.** When the user shifts topic from T12 to RR (or vice versa), the right move is to ask: "We're now in [other track] territory. Fresh chat, or proceed knowing we're cross-cutting?" Continuing without flagging it produces sessions like this one that have to be retroactively split in journal entries.
2. **The `be3b134` placeholder commit** is a small symptom of the same disease — a maintenance workflow example was given conversationally, the user followed it literally, and there was no checkpoint to confirm the placeholder was meant to be replaced. Conversational examples should label placeholder text as `<REPLACE THIS>` or similar.
3. **Reading the actual repo before assuming structure** would have saved several rounds of confusion about doc filenames (`CHANGELOG.md` vs `CHANGELOG-RR.md` etc.). Default to `web_fetch` early when working with a repo, not late.

### Verified end-to-end at session close

- v0.1.5 substrate validates clean: 0 errors, 10,953 formulas
- Homestead populated Analyzer ties to broker NOI: $1,411,323.58 to the penny
- v1.12.0 app shipped to origin/main, deployed to Streamlit Cloud at https://rrnormalizer.streamlit.app/

---
