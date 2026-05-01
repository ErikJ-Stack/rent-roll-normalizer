# Changelog — T12 Normalizer

All notable changes to the T12 Normalizer (Track 2). Independent version stream from the Rent Roll Normalizer (Track 1, currently v1.9.0). This changelog covers T12 work only — see `CHANGELOG-RR.md` for RR releases.

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
- **Vocabulary mapping ownership:** the destination workbook's `Description_Map` sheet (~230 entries) owns raw → standard description mapping. Our parser passes descriptions through after TRIM. No second mapping system in code.
- **Sign convention:** pass-through. Salem's signs are conventional (revenue +, expense +, concessions -). Non-standard signs deferred until encountered.
- **Predecessor output:** v1.7.0's "T12 with Rent Roll" download (Rent Roll Input only, into `ALF_T12_Intake_Final.xlsx`) is superseded by the new "Download Analyzer with RR + T12 Data" output.
- **Version tracking:** independent version streams. RR continues at v1.9.0. T12 begins at v0.1.0 when first code lands. UI pill shows both side-by-side when both modules ran (`RR v1.9.0 · T12 v0.1.0`).

### Documentation discipline

- This changelog and `SPEC-T12.md` join `SPEC-RR.md` and `CHANGELOG-RR.md` (currently named `SPEC.md` and `CHANGELOG.md` in the repo — to be renamed in the same commit that adds these files).
- `T12_NORMALIZER_KICKOFF.md` is superseded by `SPEC-T12.md`. Move to `docs/archive/` once v0.1.0 ships, or earlier if root tidiness matters.
- `README.md` to be lightly updated in the same commit: add a top-level "Repo contents" section explaining the two tracks + the Analyzer destination.

---

## Planned for [0.1.0]

First code release. Targets:

### Add

- `t12_normalizer.py` — parser module. Header detection (skip property headers + month-label rows), GL-detail row classification (`TRIM(colA)` numeric test), TRIM on description, pass-through values. Returns clean DataFrame.
- `t12_normalizer_writer.py` — Analyzer paste at `T12 Input!A12+`. Idempotent re-run (clears prior data first). Capacity check raises `T12CapacityError` if >500 GL rows. Preserves col P formula and all other tabs.
- T12-side version constants (`T12_VERSION`, `T12_LAST_UPDATED`) alongside RR's existing constants.

### Change

- `app.py` — Raw T12 uploader, Analyzer uploader, third download button "Download Analyzer with RR + T12 Data". Version pill shows both versions when both modules ran.
- `Run_Info` tab in any output the T12 module touched gets T12 version + run timestamp + source filename.

### Verify

- Salem end-to-end: ~76 GL rows written to `T12 Input!A12:A87`, all rows show non-UNMATCHED in col P (Description_Map already has Salem's vocabulary), `T12 Raw Data` aggregations match Salem's own totals row-by-row, `T12_Calc` hidden sheet preserved, all visible aggregator tabs preserved.

---

## How the version stream relates to Track 1

RR and T12 evolve independently. A change to RR (e.g., adding a third operator format) bumps RR only. A change to T12 (e.g., adding RealPage support) bumps T12 only. A change to shared infrastructure (`app.py` UI, `period_date.py`, `requirements.txt`) bumps whichever track the change primarily serves; if it serves both equally, bump both.

Each track's version surfaces in the UI pill and in the `Run_Info` tab of any output that track touched.
