# T12 Normalizer — Specification

> **For future chats:** This document is the source of truth for the T12 Normalizer (Track 2). Read it before making changes to any T12-related code. Update it in the same commit as any change.

**Live app:** https://rrnormalizer.streamlit.app/ (shared with RR Normalizer)
**Repo:** https://github.com/ErikJ-Stack/rent-roll-normalizer (shared, public)
**Owner:** Erik J (`Erikjayj@gmail.com`, GitHub: `ErikJ-Stack`)
**Stack:** Python · Streamlit · pandas · openpyxl · Streamlit Community Cloud (free tier)
**Current version:** Unreleased — spec scaffold only. First code release will be v0.1.0.
**Status:** Designed, not yet built.

---

## What this project does

A senior-housing T12 normalization tool. Companion to the Rent Roll Normalizer in the same repo. Analysts upload a raw T12 export from any property management system; the app cleans it and writes GL detail rows into the user's analysis workbook.

The T12 Normalizer never writes a standalone T12 workbook of its own. The user's analysis workbook already contains the analyst views (Raw Data, Monthly Trending, Mapping Review, etc.) — our job is to feed it clean rows.

---

## Relationship to other modules in this repo

This repo houses two normalizer modules and one combined output:

- **Rent Roll Normalizer** (Track 1) — see `SPEC-RR.md` / `CHANGELOG-RR.md`. Currently v1.9.0.
- **T12 Normalizer** (Track 2) — this document. Currently unreleased.
- **Combined Analyzer output** — both modules write into the user-provided `ALF_Financial_Analyzer_Only.xlsx` workbook. RR data → `Rent Roll Input!A7+`. T12 data → `T12 Input!A12+`. The reconciliation, monthly trending, and UW Output staging all live in the workbook's formulas, not in our Python.

`app.py` orchestrates both. A single run can produce both: standalone Normalized RR workbook + populated Analyzer (RR + T12 data both written) when all required uploads are present.

"Track 2" / "Track 1" is project-management vocabulary, not anything in the codebase.

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

## File inventory (planned)

| File | Status | Purpose |
| --- | --- | --- |
| `t12_normalizer.py` | planned for v0.1.0 | T12 parser. Reads raw T12, returns clean GL detail DataFrame. |
| `t12_normalizer_writer.py` | planned for v0.1.0 | Loads user's Analyzer / T12 Normalizer template. Writes A:O row 12+ of `T12 Input` sheet. Preserves col P formula and all other tabs. |
| `app.py` | shared (existing) | Will gain optional uploaders for Raw T12 and Analyzer template, plus a third download button. |
| `period_date.py` | shared (existing, reused as-is) | Filename → period date extraction. Same six patterns work for T12 filenames. |

Filenames are conventions; rename in code if the implementation calls for it, then update this table.

---

## Data flow

### Stage 1 — Raw T12 → Clean GL DataFrame

Input: any senior-housing T12 export `.xlsx`. v0.1.0 verifies against Yardi-style "Income to Budget" reports (Salem Road sample).

**Hierarchy expected in raw T12:**
- Property header rows (Salem: rows 1-10).
- Section banners (`  Revenue`, `  Operating Expenses`, `  Non-Operating Expenses`).
- Subsection banners (`    Rent Revenue`, `    Maintenance/Housekeeping`, etc.).
- GL detail rows (`      40000`, `      AL Base Rate Income`, twelve monthly values, T-12 total).
- Subtotals (`    Total - Rent Revenue`).
- Big totals (`Total Revenue`, `EBITDARM`, `EBITDAR`, `EBITDA`, `Net Income`).

**Detection rule:** a row is GL detail iff `TRIM(colA)` parses as a number. This rule:
- Matches the Coverage Check formula in `T12 Input!P` (`ISNUMBER(VALUE(TRIM(A12)))`) — consistent with the destination workbook's own classification.
- Cleanly separates Salem's ~76 GL detail rows from banners and subtotals.
- Will need re-validation on the next operator format we encounter.

**Cleaning applied to GL detail rows:**
- `TRIM` account number (col A) and description (col B) — removes leading whitespace from the indented hierarchy. Without this, descriptions look ugly in the destination and the workbook's own SUMIFs (which are exact-string-match against `Description_Map` raw values) would fail.
- Pass description text through unchanged after trim. Description_Map (in the analysis workbook) owns vocabulary mapping; we don't replicate that logic in Python.
- Pass values through as-is. Sign convention preserved (revenue positive, expense positive, concessions negative — Yardi default).
- Pass T-12 Total column through to col O of destination.

### Stage 2 — Clean DataFrame → Analyzer paste

Loads the user's analysis workbook with openpyxl. Writes A:O at row 12+ of the `T12 Input` sheet. Preserves col P formula on every row (the workbook ships with 500 pre-filled `IF(ISNUMBER(...))`, INDEX/MATCH formulas in P12:P511 — we don't touch them). Saves and offers as download.

Idempotent re-run: clears any prior data in `T12 Input!A12:O511` before writing. Same pattern as `t12_writer.py` for `Rent Roll Input!A7:S606`.

Hidden helper sheets (`T12_Calc`, `RR_Calc`) and visible aggregator sheets (`T12 Raw Data`, `T12 Analytics`, `Monthly Trending`, `Mapping Review`, `Description_Map`, plus `Rent Roll Recon` and `UW Output` on the Analyzer specifically) are preserved untouched.

### What this module explicitly does NOT do (v0.1.0)

These are deliberate non-features. Each is documented here so the boundary is visible.

- **No vocabulary mapping in code.** The destination workbook's `Description_Map` sheet owns raw → standard description mapping (~230 entries). Our parser passes descriptions through after TRIM. Two sources of truth would be a maintenance burden and would drift.
- **No standalone T12 analyst workbook.** The destination workbook already contains Raw Data / Analytics / Monthly Trending / Mapping Review tabs. A standalone would duplicate work.
- **No sign-flipping.** Salem's signs are conventional. If a future T12 reverses (e.g., expenses reported negative), we'll handle it with a per-format rule when we hit it, not preemptively.
- **No annualization.** Salem is a full T12. If a partial-year T12 shows up, address then.
- **No multi-property splitting.** Salem is single-property. Multi-property GL exports out of scope.
- **No code-side reconciliation.** RR-implied GPR vs. T12 collected revenue variance, if/when it comes, lives in the Analyzer's formulas (`Rent Roll Recon` tab), not in our Python. When it eventually warrants Python (e.g., variance threshold flagging), spin out Track 3 (`SPEC-Analyzer.md`).

---

## T12 file expected structure (destination)

The user's analysis workbook (`ALF_Financial_Analyzer_Only.xlsx` or the standalone `ALF_T12-_Normalizer.xlsx`) contains a `T12 Input` sheet with this structure:

- Rows 1-11: instruction / instruction-like rows (untouched).
- **Rows 12-511: data area** — A:O written by app, col P has the pre-filled Coverage Check formula on every row (untouched).
- Hidden helper sheets `T12_Calc`, `RR_Calc` (do not touch).
- Visible aggregator sheets `T12 Raw Data`, `Monthly Trending`, `Mapping Review`, `Description_Map`. The Analyzer additionally has `T12 Analytics`, `Rent Roll Recon`, `UW Output` (do not touch).
- Capacity: 500 GL rows max per run. Salem produces ~76. Plenty of headroom.

App raises `T12CapacityError` with a clear message if exceeded. Same pattern as RR's `T12CapacityError` for the Rent Roll Input tab.

---

## Verified formats

| Format | GL detail rows | Period | Notes |
| --- | ---: | --- | --- |
| Yardi "Income to Budget" — Salem (Oaks at Salem Road) | (verify at v0.1.0) | T12 ending 1/31/2026 | Original test case. AL-only. Indented hierarchy. Standard signs. ~76 GL detail rows. |

More formats added as encountered. Each format earns a verification line plus any quirks documented under "Key decisions."

The Briar Glen lesson from Track 1 applies directly: one operator's format will not shape every parsing edge. Build for Salem first, verify, ship v0.1.0, then expand as new T12s arrive.

---

## Known issues / limitations (v0.1.0)

1. **Single Yardi format verified.** RealPage / AppFolio / manual GL exports not yet tested.
2. **Single property only.** Multi-property T12s out of scope.
3. **Sign convention not flexible.** Salem's signs are pass-through; non-standard signs will need a per-format rule.
4. **No partial-year detection.** A 6-month T12 would silently land as 6 months in cols C-H with cols I-N blank. The destination workbook's formulas would still SUM correctly, but no annualization.
5. **`Description_Map` updates are user responsibility.** Unmatched descriptions show `UNMATCHED` in `T12 Input!P`; user adds them to `Description_Map` per the in-workbook instructions. Our parser does nothing to surface UNMATCHED rows back in the UI (yet).
6. **Conditional formatting drop on save.** Same openpyxl limitation as RR's T12 Intake paste. Will be inspected and noted at v0.1.0 release.

---

## How the analyst uses the app (proposed UI for v0.1.0)

1. Open https://rrnormalizer.streamlit.app/
2. Upload rent roll (existing, required).
3. Optional: upload mapping override workbook (RR-side; existing).
4. **Optional: upload Raw T12 file** (NEW for T12 Normalizer).
5. **Optional: upload Analyzer template** (NEW; supersedes the v1.7.0 T12 Intake template per kickoff decision).
6. Optional: set Property Care Type default (existing).
7. App processes immediately.
8. Click **Download Normalized Rent Roll** for the 6-tab analyst workbook (existing).
9. Click **Download Analyzer with RR + T12 Data** for the populated combined workbook (NEW). Replaces the v1.7.0 "T12 with Rent Roll" download.

**UI version pill convention:** when output combines RR + T12 work, both versions appear in the title row (e.g., `RR v1.9.0 · T12 v0.1.0`). When only RR ran, only RR's version. When only T12 ran (unusual), only T12's. Each module's version surfaces in the `Run_Info` tab of any output workbook it touched.

---

## What's next after v0.1.0

- **v0.2.0+:** verify against a second T12 format (RealPage or AppFolio when a sample arrives).
- **Future:** multi-property T12 splitter; sign-convention auto-detection; partial-year annualization; UNMATCHED row surfacing in the Streamlit UI.
- **When code-side reconciliation lands** (RR-vs-T12 variance flagging, `UW Output` extraction, multi-period comparison): spin out `SPEC-Analyzer.md` / `CHANGELOG-Analyzer.md` as Track 3 with its own version stream.

---

## Working principles (carried forward from Track 1)

Things that worked well on RR, applied here:

- Show proposed changes before building.
- Verify against real data at every step (Salem now; new formats as they arrive).
- Bump version on every release. Surface in the UI pill so deploys are verifiable from the live app.
- Honest about library limitations (e.g., openpyxl drops conditional formatting — flag, don't hide).
- Smaller commits across sessions; not all changes in one chat.

Things to avoid:

- Long unbroken chats spanning multiple features. Split by feature.
- Designing T12 logic from one operator format alone. The Briar Glen lesson — Salem alone wouldn't have shaped `pre_cleaner.py`. One Yardi T12 alone won't shape every parsing edge.
- Multi-file changes without verifying each landed.

---

## Maintenance protocol

**At the start of every T12-related chat:**

> "Read SPEC-T12.md and CHANGELOG-T12.md at https://github.com/ErikJ-Stack/rent-roll-normalizer. Then [task]."

**At the end of every chat that changes T12 code:**

> "Update SPEC-T12.md to reflect what changed. Add a CHANGELOG-T12.md entry. Bump T12 version constants. Commit and push."

**Cross-cutting changes** (`app.py`, `period_date.py`, `requirements.txt`, the version-pill UI, anything that touches both tracks) reference both:

> "Read SPEC-RR.md, SPEC-T12.md, and README.md at https://github.com/ErikJ-Stack/rent-roll-normalizer. Then [task]."

This keeps each chat's context bounded. RR-only chats don't drag in T12 history; T12-only chats don't drag in RR's Briar Glen quirks. Cross-cutting work is rare enough that the wider context is acceptable when it happens.
