# Chat Journal — rent-roll-normalizer

A running log of substantive chat sessions on this repo. One entry per session.
Each entry captures: scope, what shipped, what drifted, and the commit(s) the
session produced. Use this for handoff between chats and for tracing why a
particular commit looks the way it does.

Newest at top.

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
