# Changelog — T12 Normalizer

All notable changes to the T12 Normalizer (Track 2). Independent version stream from the Rent Roll Normalizer (Track 1, currently v1.10.0). This changelog covers T12 work only — see `CHANGELOG-RR.md` for RR releases.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a T12-related chat, add an entry here in the same commit.

---

## [Unreleased]

### Spec scaffolded — no code yet

- `SPEC-T12.md` drafted: architecture, data flow, file inventory, key decisions, planned UI, known limitations, maintenance protocol. Mirrors the structure of `SPEC-RR.md` for consistency across tracks.

### Discovery answers captured (from kickoff chat)

These pin down the scope before any code is written:

- **Repo placement:** Track 2 lives in the existing `rent-roll-normalizer` repo as a sibling to RR. Renaming the repo deferred until the Analyzer becomes Track 3 with its own code.
- **App deploy:** Shared Streamlit app at `https://rrnormalizer.streamlit.app/`. Gains optional Raw T12 and Analyzer uploaders + a third download button.
- **Verified target format for v0.1.0:** Yardi "Income to Budget" (Salem Road sample, T12 ending 1/31/2026, ~76 GL detail rows after filtering).
- **Output target:** the user's `ALF_Financial_Analyzer_Only.xlsx` Analyzer workbook is the primary destination. The standalone `ALF_T12-_Normalizer.xlsx` template uses the same `T12 Input!A12+` paste pattern, so both work via one writer.
- **Vocabulary mapping ownership:** the destination workbook's `Description_Map` sheet (~230 entries) owns raw → standard description mapping. Our parser passes descriptions through after TRIM. No second mapping system in code. Parser reads `Description_Map` only to surface UNMATCHED descriptions in the UI.
- **Sign convention:** pass-through. Salem's signs are conventional (revenue +, expense +, concessions -). Non-standard signs deferred until encountered.
- **Predecessor output:** v1.7.0's "T12 with Rent Roll" download (Rent Roll Input only, into `ALF_T12_Intake_Final.xlsx`) is superseded by the new "Download Analyzer with RR + T12 Data" output.
- **Version tracking:** independent version streams. RR is at v1.10.0. T12 begins at v0.1.0 when first code lands. UI pill shows both side-by-side when both modules ran (`RR v1.10.0 · T12 v0.1.0`).
- **Module naming history:** `t12_writer.py` (Track 1) writes RR data into a T12 destination — the "t12" in the name refers to the destination, not the input. New module `t12_normalizer_writer.py` (Track 2) writes T12 data into a T12 destination. Rename to `rr_to_analyzer_writer.py` deferred to a future cross-cutting commit. Documented in `SPEC-T12.md` "Module naming history" section. **`SPEC-RR.md` does not yet have this note** — to be added when the Track 1 chat next opens, or in a later cross-cutting commit.
- **UNMATCHED row surfacing promoted to v0.1.0** (was previously listed as future). Implemented via Python-side `Description_Map` lookup, not Excel formula evaluation.

### Sequencing note

T12 v0.1.0 implementation is paused until Track 1 (Path B chat) lands its Analyzer-as-paste-target work. Once Path B ships and pushes:

1. Pull latest `app.py` (which will already accept the Analyzer template upload for the RR side).
2. Resume T12 chat: build `t12_normalizer.py`, `t12_normalizer_writer.py`, add T12 uploader and UNMATCHED banner to `app.py` on top of Path B's changes.
3. No `app.py` merge conflicts because the two tracks touch the file sequentially, not in parallel.

This is consistent with the "one track at a time" working principle.

### Documentation discipline

- This changelog and `SPEC-T12.md` join `SPEC-RR.md` and `CHANGELOG-RR.md` (already renamed in the repo).
- `T12_NORMALIZER_KICKOFF.md` is superseded by `SPEC-T12.md`. Move to `docs/archive/` once v0.1.0 ships, or earlier if root tidiness matters.
- `README.md` to be lightly updated when v0.1.0 ships: add a top-level "Repo contents" section explaining the two tracks + the Analyzer destination. Currently README references only the RR track.

---

## Planned for [0.1.0]

First code release. Targets:

### Add

- `t12_normalizer.py` — parser module. Header detection (skip property headers + month-label rows), GL-detail row classification (`TRIM(colA)` numeric test), TRIM on description, pass-through values. Returns clean DataFrame **plus a list of UNMATCHED descriptions** (looked up against the destination workbook's `Description_Map`).
- `t12_normalizer_writer.py` — Analyzer paste at `T12 Input!A12+`. Idempotent re-run (clears prior data first). Capacity check raises `T12CapacityError` if >500 GL rows. Preserves col P formula (P12:P511) and all other tabs.
- T12-side version constants (`T12_VERSION`, `T12_LAST_UPDATED`) alongside RR's existing constants.

### Change

- `app.py` — Raw T12 uploader, third download button "Download Analyzer with RR + T12 Data", UNMATCHED warning banner. (The Analyzer uploader itself is added by Path B; T12 chat reuses it.) Version pill shows both versions when both modules ran.
- `Run_Info` tab in any output the T12 module touched gets T12 version + run timestamp + source filename.

### Verify

- Salem end-to-end: ~76 GL rows written to `T12 Input!A12:A87` (depending on actual count from the parser), `Description_Map` lookup produces expected count of UNMATCHED (likely 0 since Description_Map is Salem-aware), `T12 Raw Data` aggregations match Salem's own subtotals row-by-row, `T12 Analytics` populated, `T12_Calc` hidden sheet preserved, all visible aggregator tabs preserved, col P12:P511 formulas intact.

---

## How the version stream relates to Track 1

RR and T12 evolve independently. A change to RR (e.g., adding a third operator format) bumps RR only. A change to T12 (e.g., adding RealPage support) bumps T12 only. A change to shared infrastructure (`app.py` UI, `period_date.py`, `requirements.txt`) bumps whichever track the change primarily serves; if it serves both equally, bump both.

Each track's version surfaces in the UI pill and in the `Run_Info` tab of any output that track touched.

The "one track at a time" principle means a chat is RR-only OR T12-only OR explicitly cross-cutting — never accidentally cross-cutting. If you find yourself editing both `SPEC-RR.md` and `SPEC-T12.md` in a single chat, stop and confirm whether that's intentional cross-cutting work or scope creep.
