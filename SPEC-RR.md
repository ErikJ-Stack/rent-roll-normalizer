# Rent Roll Normalizer — Specification

> **For future chats:** This document is the source of truth for the Rent Roll Normalizer (Track 1). Read it before making changes to any RR-related code. Update it in the same commit as any change. The T12 Normalizer (Track 2) has its own spec at `SPEC-T12.md` — read both when doing cross-cutting work.

**Live app:** <https://rrnormalizer.streamlit.app/>
**Repo:** <https://github.com/ErikJ-Stack/rent-roll-normalizer> (public)
**Owner:** Erik J (`Erikjayj@gmail.com`, GitHub: `ErikJ-Stack`)
**Stack:** Python · Streamlit · pandas · openpyxl · Streamlit Community Cloud (free tier)
**Current version:** v1.12.0 (2026-05-06) — UI reorganization, bundled-Analyzer default, override expander.

---

## What this project does

A senior-housing underwriting tool. Analysts upload a raw rent roll exported from any operator (Oaks, Briar Glen, Sunrise, Brookdale, etc.) and the app produces:

1. A standalone **Normalized RR workbook** — six tabs, professionally formatted, ready for analyst review.
2. A populated **ALF Financial Analyzer workbook** — the bundled Analyzer template with rent roll data injected into its `Rent Roll Input` sheet. When the analyst also uploads a raw T12, GL detail flows into the Analyzer's `T12 Input` sheet (handled by the T12 Normalizer — Track 2; see `SPEC-T12.md`).

The Analyzer then drives the underwriting analysis (P&L, scenarios, returns) — those tabs already existed in the substrate; this project just feeds them automatically.

### Two tracks, one app

* **Track 1 — Rent Roll Normalizer** (this document) — RR parsing, RR writer, Streamlit UI shell, Analyzer source resolution, period-date detection.
* **Track 2 — T12 Normalizer** (`SPEC-T12.md`) — T12 parser (Yardi + MRI format registry), T12 writer (`T12 Input` sheet), `Description_Map` lookup, UNMATCHED matcher form.

Both tracks ship in the same `app.py` and write into the same Analyzer workbook, but they have independent version streams. **Track 1 is at v1.12.0; Track 2 is at v0.1.1; bundled Analyzer substrate is at v0.1.5.**

---

## Architecture

```
User browser (any device, any OS — desktop only per design)
        │
        ▼
Streamlit Cloud (free tier) ── auto-rebuilds on push
        │  reads from
        ▼
GitHub: ErikJ-Stack/rent-roll-normalizer
        │  pushed from
        ▼
Local Windows machine: C:\Users\erikj\Downloads\rent_roll_app
```

**Standard deploy loop:**

1. Edit files locally
2. `git add . && git commit -m "..." && git push`
3. Streamlit Cloud auto-rebuilds in ~30-60 seconds
4. Hard-refresh app URL with `Ctrl+Shift+R`

**Streamlit caching gotcha:** sometimes the app doesn't pick up pushes. Fix: sign out and back in to share.streamlit.io, or click Reboot app on the dashboard. **Reboot-first rule:** if the live app's behavior diverges from a verified local run on the same file (e.g. local says 79 rows, live says 0), assume stale module cache and reboot before debugging.

---

## File inventory

| File | Approx size | Purpose |
| --- | --- | --- |
| `app.py` | ~32 KB | Streamlit entry — UI, sidebar, two download buttons, T12 status panel, UNMATCHED matcher form, bundled-Analyzer resolution |
| `normalizer.py` | 30+ KB | Header detection, parent-child parse, care bucket grouping, Care Type fallback chain, Shared detection, self-contained-row support |
| `pre_cleaner.py` | 6.4 KB | Strips totals/banners/blanks from raw DataFrame before header detection |
| `mappings.py` | 9.5 KB | Default mapping rules + override loader |
| `reports.py` | 6.7 KB | Builders for RR_Summary, RR_By_Type, RR_Exceptions |
| `writer.py` | 14.0 KB | Excel writer with full formatting (RR-side) |
| `t12_translator.py` | 3.6 KB | Translates Condensed_RR vocabulary → Analyzer's `Rent Roll Input` vocabulary |
| `t12_writer.py` | 5.8 KB | Loads Analyzer, writes A:S row 7+ on `Rent Roll Input`, preserves all else. Module name is historical — predates the Track 1 / Track 2 split. See "Module naming history" in `SPEC-T12.md`. |
| `t12_normalizer.py` | 19.5 KB | Track 2 — T12 parser. Format-registry pattern (Yardi + MRI). |
| `t12_normalizer_writer.py` | 12.7 KB | Track 2 — T12 writer. Writes `T12 Input!A12+`, appends `Description_Map` resolutions, adds `Run_Info` tab. |
| `period_date.py` | 4.5 KB | Extracts period date from filename across 6 patterns |
| `mapping_template.xlsx` | 11.7 KB | Editable mapping override workbook for analysts |
| `ALF_Financial_Analyzer_Only.xlsx` | ~150 KB | **Bundled Analyzer.** Loaded silently as the default destination workbook. Substrate at v0.1.5. |
| `tools/migration/migrate_analyzer.py` | one-shot | Applied the v0.1.0 → v0.1.4 substrate migration to the master Analyzer (2026-05-02). Archived for traceability. |
| `tools/migration/migrate_to_v015.py` | one-shot | Applied the v0.1.4 → v0.1.5 substrate migration (2026-05-04). Idempotent — detects `2nd Person Revenue` in `T12 Raw Data` and exits if already applied. |
| `tools/migration/verify_e2e.py` | one-shot | Pre-v0.1.0 verification harness with throwaway extractors. Superseded by `t12_normalizer.py`'s format registry; retained as reference. |
| `requirements.txt` | 42 B | streamlit, pandas, openpyxl |

---

## Data flow

### Stage 0 — Pre-cleaning (introduced v1.8.0)

Raw DataFrame is run through `pre_cleaner.clean_raw_rent_roll()` which strips:

* **Trailing summary block** (rows from "Totals" / "Grand Total" / "Summary" onward)
* **Page banners** ("Rent Roll", "Page N", "Community:", "As of Date:", etc.)
* **Legend / instruction rows** ("x: Excluded Units", "Care Level Codes", etc.)
* **Section-label banner rows** (single-cell rows like `Briar Glen Alzheimer's Special Care Center (853)`)
* **Blank padding rows** (every cell empty)

Conservative by default — only drops rows we're confident are noise.

### Stage 0.5 — Smart sheet selection (introduced v1.8.0)

When no sheet name is provided, the normalizer scores all sheets by row count × column count + signal hits ("unit", "apartment", "resident", "bed", etc.) in the first 20 rows. Picks the highest-scoring sheet. Avoids picking tiny "Document map" / legend sheets.

### Stage 1 — Rent roll → Normalized DataFrame

Input: any senior-housing rent roll `.xlsx`.

The normalizer:

1. Auto-detects the header row by scanning the first 20 rows for high-signal column names.
2. Walks rows with **three-way classification**:
   * **Parent-only**: has unit/apt info but no resident → set context, skip
   * **Self-contained**: has unit/apt info AND resident on same row → refresh context AND emit a record (Briar Glen single-bed pattern)
   * **Child bed**: has bed-level data only → emit record using prior context
3. Produces one row per bed.
4. Runs a **second pass** to detect shared apartments (rooms with 2+ beds).

Each bed record is normalized for: Apt Type, Bed Status, Payer Type, Care Type (IL/AL/MC), Care Level (Level 1-5 or "Level 6+").

Care/ancillary monthly columns are auto-grouped by **two paths**:

* **Suffix path**: header has `level/amount/discount/(month)` suffix — prefix names the bucket
* **Standalone path**: header is itself a care-bucket name with no suffix (Briar Glen "Care Charges")

### Stage 2 — Normalized → 6-tab Excel output

Tabs: Condensed_RR, Normalized_Beds, RR_Summary, RR_By_Type, RR_Exceptions, Mapping_Reference, Run_Info.

### Stage 3 — Condensed_RR → Analyzer's Rent Roll Input

The app translates vocabulary and writes A:S row 7+ to the Analyzer's `Rent Roll Input` sheet, preserving all other tabs/formulas/validations. The Analyzer is loaded from the bundled file by default; an override expander in the sidebar accepts a custom upload.

### Stage 4 — Raw T12 → Analyzer's T12 Input *(Track 2 — see `SPEC-T12.md`)*

When the user also uploads a raw T12, the T12 Normalizer parses it, surfaces UNMATCHED descriptions for in-app mapping, and writes GL detail into the Analyzer's `T12 Input` sheet. New `Description_Map` entries from the matcher are appended to the downloaded Analyzer (NOT written back to the bundled repo file).

---

## Analyzer source

Starting with v1.12.0, the app loads the destination Analyzer workbook from one of two places:

1. **Bundled (default).** `ALF_Financial_Analyzer_Only.xlsx` in the repo root is loaded silently on every run. This is the canonical Analyzer for the deployed app — it's at the current substrate version (v0.1.5 as of this writing) and contains the canonical 55-Label `Description_Map` vocabulary that T12 UNMATCHED matching depends on.

2. **Override (optional).** Users can upload a custom Analyzer via the "Advanced — override Analyzer template" expander at the bottom of the sidebar. The upload wins for that session only; the bundled repo file is never modified. Use cases: adding new data to a previously-populated Analyzer from a prior deal, working with a v0.1.4-substrate (or earlier) Analyzer that hasn't been migrated yet, or testing a candidate substrate edit before promoting it.

The `_load_analyzer()` function in `app.py` resolves the source and returns `(bytes, source_label, substrate_version)`. Source label is one of `"bundled (repo)"` or `"uploaded: <filename>"`. Substrate version is detected heuristically from `Description_Map` markers — display-only; never gates functionality.

### Updating the bundled Analyzer

Cosmetic edits to the bundled file (formatting, column widths, conditional formatting, sheet tab colors) are pushed via standard git workflow:

1. Open `ALF_Financial_Analyzer_Only.xlsx` in Excel, edit, save, close
2. `git add ALF_Financial_Analyzer_Only.xlsx`
3. `git commit -m "Analyzer: <describe edit>"`
4. `git push`

Streamlit Cloud auto-redeploys from the repo on push.

**Substrate-level edits** (new Labels, formula changes, row inserts, named range changes) are a different workflow — they require a `CHANGELOG-T12.md` substrate-version entry, a migration script in `tools/migration/`, and verification against known-good test files (Salem, Briar Glen, Homestead). See `CHANGELOG-T12.md` `[Substrate template v0.1.5]` for the most recent example.

### Description_Map propagation

When a user resolves UNMATCHED T12 descriptions through the in-app matcher, those new mappings are appended to the downloaded Analyzer's `Description_Map`. They are NOT written back to the bundled repo file.

If a recurring operator's mappings should become part of the canonical vocabulary, the workflow is:

1. Resolve them in-app once (gets them into a downloaded Analyzer).
2. Manually copy the new entries into the bundled `ALF_Financial_Analyzer_Only.xlsx` via Excel.
3. Commit and push the updated bundled file.

Or, alternatively, treat per-deal Description_Map additions as ephemeral (the matcher remembers them in session state for repeat runs of the same operator, which is usually enough).

---

## Condensed_RR column layout (the 18-column analyst view)

| Col | Header | Source / Logic |
| --- | --- | --- |
| A | Unit # | `{Room}-{Bed}` composite (e.g., `101-A`); Briar Glen single-bed shows just room number |
| B | Room # | Apartment number from source (or Unit if no separate Apartment column) |
| C | Sq Ft | From source if present, else blank |
| D | Care Type | IL / AL / MC (via fallback chain) |
| E | Status | Occupied / Vacant / Hold / Notice / Model / Down |
| F | Apt Type | Studio / 1BR / 2BR / Companion / Semi-Private / Other; ` - Shared` suffix on multi-bed rooms |
| G | Market Rate | From source |
| H | Actual Rate | From source |
| I | Concession $ | Monthly concession from source (negative-signed) |
| J | Concession End Date | From source |
| K | Care Level | Level 1-5 or `Level 6+` (blank if source has no acuity tiers, e.g. Briar Glen) |
| L | Care Level $ | Monthly care charge (renamed from "AL Care Level $" in v1.8.0) |
| M | Med Mgmt $ | Monthly med management charge |
| N | Pharmacy $ | Monthly pharmacy charge |
| O | Other LOC $ | Auto-catch sum of any unmapped care/ancillary columns |
| P | Payer Type | Private Pay / Medicaid / Medicare / VA Benefit / LTC Insurance |
| Q | Move-in Date | From source |
| R | Resident Name | From source |

---

## Key decisions

### Care Type detection (IL/AL/MC) — fallback chain

When no explicit "Care Type" column exists, fall back through:

1. Explicit Care Type column on the row
2. Apartment-context Care Type (parent-level column)
3. **Building / Unit code** (Salem's "AL" → AL)
4. **Care Level raw value** (e.g., "Assisted Living Level 6" → AL, Briar Glen's "DM" → MC)
5. Property Default from sidebar dropdown
6. Blank + flag in Exceptions tab

Provenance recorded in `Care Type Source` column.

**Care Type rule patterns** in `mappings.py` include operator-specific codes:

* `DM` → MC (Briar Glen: Alzheimer's Care)
* `DU7` → MC (Briar Glen: Special Care)
* `LTC` → AL (Long-Term Care setting)
* `Alzheimer*`, `dementia` → MC

### Care Level — Level 1-5 plus Level 6+ bucket

User chose this over capping. Level 6, 7, 8+ all flow into `Level 6+`. For Analyzer paste, Level 6+ → Level 7, Level 1 → Basic.

For operators whose source has no acuity tiers (Briar Glen): Care Level is left **blank**. The Care Type column still resolves correctly.

### Shared apartment detection (second pass)

After parsing all bed rows, count beds per (Building, Room #) pair. Any room with 2+ beds gets ` - Shared` appended to its Apt Type on every row of that room. ` - Shared` suffix is stripped for Analyzer paste.

### Unit # composite

`{Room}-{Bed}` format. For single-Unit-column formats (Briar Glen), Unit IS the room — no building. For multi-column formats (Salem), Unit is the building code, Apartment is the room.

Briar Glen Privacy Level codes translate to bed letters: PRI/Single → no letter, SPA/DAS/QAS → A, SPB/DBS/QBS → B.

### Self-contained row detection (introduced v1.8.0)

A row is "self-contained" if it has BOTH apartment-level info AND a **resident name** on the same row. Resident is the strict signal — rates alone don't qualify (Salem puts rates on parent rows).

Resolves Briar Glen single-bed format where everything is on one row per unit.

### Bed status fallback (introduced v1.8.0)

If no `Bed Status` column exists, fall back to:

1. Resident name starting with `*Vacant` / `Vacant` / `(vacant)` → status = Vacant
2. Resident name present → status = Occupied
3. Resident name absent → status = Vacant

Briar Glen-specific: when status is detected from resident name, the `*Vacant` literal is stripped from the resident name field.

### Standalone care bucket columns (introduced v1.8.0)

In addition to suffix-based detection (e.g., "AL Care (January 2026)"), the care-group detector now recognizes standalone columns whose name itself is the bucket: "Care Charges", "Med Mgmt", "Pharmacy", "Other Charges". The full header is treated as the monthly column.

Heuristic: the column must contain a care-related keyword (charge, service, care, medication, pharmacy, ancillary) to qualify, to avoid false positives.

### Concession detection — multi-column, negative-signed (introduced v1.9.0)

`detect_concession_cols` recognizes multiple header patterns as concession sources and sums them all into `Concession $`:

* `Concession` (generic — covers Salem's `Concession (January 2026)`)
* `Recurring Discount(s)` (Briar Glen)
* `One-Time Incentive(s)` (Briar Glen)
* Generic `Discount` with a `(month)` suffix

**Sign convention: source values preserved (typically negative).** `Concession $ = -500` means a $500 reduction. `Total Monthly Revenue` adds the concession (`actual + LOC + concession`), which correctly applies a negative as a reduction. The Analyzer paste passes through column I as-is; the analyst sees `−500` in the standalone RR which reads naturally as "discount."

The care-group detector explicitly skips columns matching the concession patterns to prevent any future double-counting.

### Smart sheet selection (introduced v1.8.0)

Multi-sheet workbooks (like Briar Glen with `Document map` + data sheet + legend) get an automatic best-sheet pick based on row × col + header signal scoring. Avoids tiny metadata sheets.

### Vocabulary translations for Analyzer paste

| Column | Condensed_RR → Analyzer |
| --- | --- |
| Apt Type | "1BR" → "1 Bedroom"; "2BR" → "2 Bedroom"; ` - Shared` suffix stripped; "Companion" → "Other" |
| Status | "Hold" / "Model" / "Down" → "Other" |
| Care Level | "Level 1" → "Basic"; "Level 6+" → "Level 7" |
| Payer | "VA Benefit" → "VA"; "Medicare" → "Other" |

### Period Date — auto-detect from filename

Six patterns in priority order: `YYYY-MM-DD`, `MM-DD-YYYY`, `M_D_YY`, `YYYY_MM`/`MM_YYYY`, `Mon_YYYY`, `MonDDYYYY`.

### Output filenames

* Standalone RR: `<source_stem> Normalized YYYY-MM-DD.xlsx`
* Populated Analyzer (RR-only): `Analyzer with <rr_stem> YYYY-MM-DD.xlsx`
* Populated Analyzer (RR + T12): `Analyzer with <rr_stem> + <t12_stem> YYYY-MM-DD.xlsx`

### Excel formatting

Charcoal + white theme: header `#2B2B2B`, white bold Calibri, banded rows, color-coded Status/Care Level/Care Type, currency `$#,##0`, dates `mm/dd/yyyy`, autofilters, frozen panes, print-ready.

### Design choices for end-user experience

* **Desktop-only by design.** Mobile uploads are unreliable on Streamlit Cloud's file uploader; underwriting workflow doesn't require mobile.

---

## Analyzer file expected structure

The bundled `ALF_Financial_Analyzer_Only.xlsx` (substrate v0.1.5) contains these sheets:

* `Cover` — version metadata
* `Rent Roll Input` — RR Normalizer writes A:S rows 7-606. Cols T-U have IFERROR formulas to row 606. Data validations on cols D/E/F/K/P. Max 600 bed rows per run.
* `Rent Roll Recon` — analyst review tab
* `Rent Roll Output` — produced from RR_Calc
* `RR_Calc` — helper sheet
* `T12 Input` — T12 Normalizer writes A:O rows 12-511. Max 500 GL rows per run. *(see `SPEC-T12.md`)*
* `T12_Calc` — helper sheet with col N descmap-lookup formula *(see `SPEC-T12.md`)*
* `T12 Raw Data` — aggregator sheet *(see `SPEC-T12.md`)*
* `Description_Map` — canonical 55-Label vocabulary *(see `SPEC-T12.md`)*
* `Monthly Trending` — analyst output *(see `SPEC-T12.md`)*
* `T12 Analytics` — analyst output *(see `SPEC-T12.md`)*
* `UW Output` — final underwriting output

**Conditional formatting note:** openpyxl drops modern conditional formatting extensions on save (~49 KB lost from a 202 KB file). User accepted.

---

## Verified formats

| Format | Beds | Care Level $ | Concession $ | Notes |
| --- | --- | --- | --- | --- |
| Salem (Oaks) | 50 | $28,125.81 | $-2,841.45 (7 rows) | Original test case. Multi-column unit+apartment, Level 1-7 acuity, three care buckets. |
| Briar Glen | 79 (71 units, 8 shared) | $234,360.00 | $-14,132.00 (16 rows) | Single-column unit, two-letter care codes, *Vacant marker, monthly columns without suffixes, blank padding rows, totals block. Recurring Discounts + One-Time Incentives mapped (v1.9.0). |

Both verified end-to-end on every release. Concession totals added to baseline in v1.9.0 to catch sign regressions.

T12 verification covers Salem, Briar Glen, and Homestead Pensacola — see `SPEC-T12.md` "Verified end-to-end" table.

---

## Known issues / limitations

1. **Conditional formatting drops on Analyzer save.** openpyxl limitation. User accepted.
2. **Sq Ft is blank** when source RR doesn't have it. Decision: don't fabricate.
3. **600-row Analyzer cap on RR side, 500-row cap on T12 side.** Hard limits by formula extent.
4. **Pre-existing `Rent Roll Recon!H20` `#NAME?`** in populated outputs. Documented in `CHANGELOG-T12.md` `[0.1.0]`. Substrate-level issue, not introduced by any specific release.
5. **Streamlit Cloud free tier sleeps apps after 7 days idle.** First request after sleep takes ~30 seconds.
6. **Mobile upload not supported** — by design choice.

---

## How the analyst uses the app

1. Open <https://rrnormalizer.streamlit.app/>.
2. Upload rent roll (sidebar, required).
3. (Period date auto-detects from filename; override if needed.)
4. Optional: upload raw T12. (UNMATCHED descriptions, if any, surface in a matcher form below the KPIs.)
5. Optional: set Property Care Type default for single-care-setting buildings.
6. Optional: upload mapping override workbook.
7. Optional: type a sheet name to override auto-detection.
8. (App processes immediately — bundled Analyzer is loaded silently as the destination workbook.)
9. Click **Download Normalized Rent Roll** for the standalone 6-tab analyst workbook.
10. Click **Download Analyzer with data** for the populated Analyzer with RR (and T12, if uploaded) baked in.

If the analyst needs to use a different Analyzer for a specific session (populated Analyzer from a prior deal, candidate substrate edit, etc.), they expand "Advanced — override Analyzer template" at the bottom of the sidebar and upload there.

---

## Versioning

`APP_VERSION` / `RR_VERSION` is bumped on every push of `app.py`. Convention through v1.12.0 has been minor bumps for any UI change. **Going forward**, prefer:

* **Major** (e.g., `2.0.0`) — breaking change to download format, output structure, or Analyzer write contract.
* **Minor** (e.g., `1.13.0`) — new feature, new uploader, new tab, new download option.
* **Patch** (e.g., `1.12.1`) — bug fix only, formatting tweak, doc-only change in `app.py` like a label edit, or maintenance re-push.

The previous convention (minor bump for everything) is preserved in the historical changelog but going forward, prefer the standard semver split. Maintenance commits that don't change behavior — version-pill alignment, dependency pins, comment-only edits — should use a patch bump under this guidance.

`T12_VERSION` is independent — see `SPEC-T12.md` "How the version stream relates to Track 1".

---

## Maintenance protocol

**At the start of every chat:**

> "Read SPEC-RR.md, SPEC-T12.md, and README.md at <https://github.com/ErikJ-Stack/rent-roll-normalizer>. Then [task]."

**At the end of every chat that changes RR-side code:**

> "Update SPEC-RR.md to reflect what changed. Add a CHANGELOG-RR.md entry. Bump APP_VERSION and APP_LAST_UPDATED. Commit and push."

**At the end of every chat that changes T12-side code or substrate:**

> "Update SPEC-T12.md and CHANGELOG-T12.md. Bump T12_VERSION (and substrate version if applicable). Commit and push."

**Cross-cutting work (touches both tracks):**

The "one track at a time" principle means a chat is RR-only OR T12-only OR explicitly cross-cutting — never accidentally cross-cutting. If a chat finds itself editing both `SPEC-RR.md` and `SPEC-T12.md`, stop and confirm whether that's intentional cross-cutting work or scope creep.

---

## Doc rename history

* **2026-05-06** — `CHANGELOG.md` → `CHANGELOG-RR.md`, `SPEC.md` → `SPEC-RR.md`. Symmetrical naming with `CHANGELOG-T12.md` / `SPEC-T12.md`. Rename via `git mv` to preserve history. The T12-side docs (introduced 2026-05-01) had been written assuming the `-RR` suffix would exist; this commit brings the RR-side docs into line.

---

## Working principles

Things that worked well:

* Show proposed changes before building.
* Single-select prompts for binary decisions.
* Verify against real data at every step.
* Bump APP_VERSION on every release.
* Smaller commits across sessions.

Things to avoid:

* Long unbroken chats — split by feature.
* Multiple file changes without verifying each landed.
* Inventing version numbers — read `CHANGELOG-RR.md` and `CHANGELOG-T12.md` to see what's already documented before assuming where to bump.
