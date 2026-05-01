# Rent Roll Normalizer — Specification

> **For future chats:** This document is the source of truth for the project. Read it before making changes. Update it in the same commit as any code change.

**Live app:** https://rrnormalizer.streamlit.app/
**Repo:** https://github.com/ErikJ-Stack/rent-roll-normalizer (public)
**Owner:** Erik J (`Erikjayj@gmail.com`, GitHub: `ErikJ-Stack`)
**Stack:** Python · Streamlit · pandas · openpyxl · Streamlit Community Cloud (free tier)
**Current version:** v1.11.0 (2026-05-01)

---

## What this project does

A senior-housing underwriting tool. Analysts upload a raw rent roll exported from any operator (Oaks, Briar Glen, Sunrise, Brookdale, etc.) and the app produces:

1. A standalone **Normalized RR workbook** — six tabs, professionally formatted, ready for analyst review
2. A populated **Analyzer workbook** — the analyst's own ALF Financial Analyzer template with rent roll data injected into its `Rent Roll Input` sheet starting at row 7

The Analyzer then drives the underwriting analysis (P&L, scenarios, returns) — those tabs already existed; this project just feeds them automatically.

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

**Streamlit caching gotcha:** sometimes the app doesn't pick up pushes. Fix: sign out and back in to share.streamlit.io, or click Reboot app on the dashboard. **Reboot-first rule:** if the live app's behavior diverges from a verified local run on the same file (e.g. local says 79 rows, live says 0), assume stale module cache and reboot before debugging. This has happened multiple times — see Pitfall 1 in the kickoff.

---

## File inventory

| File | Approx size | Purpose |
|---|---:|---|
| `app.py` | 14.7 KB | Streamlit entry — UI, sidebar, two download buttons |
| `normalizer.py` | 30+ KB | Header detection, parent-child parse, care bucket grouping, Care Type fallback chain, Shared detection, self-contained-row support |
| `pre_cleaner.py` | 6.4 KB | Strips totals/banners/blanks from raw DataFrame before header detection |
| `mappings.py` | 9.5 KB | Default mapping rules + override loader |
| `reports.py` | 6.7 KB | Builders for RR_Summary, RR_By_Type, RR_Exceptions |
| `writer.py` | 14.0 KB | Excel writer with full formatting |
| `t12_translator.py` | 3.6 KB | Translates Condensed_RR vocabulary → Analyzer vocabulary |
| `t12_writer.py` | 5.8 KB | Loads user's Analyzer, writes A:S row 7+, preserves all else |
| `period_date.py` | 4.5 KB | Extracts period date from filename |
| `mapping_template.xlsx` | 11.7 KB | Editable mapping override workbook for analysts |
| `requirements.txt` | 42 B | streamlit, pandas, openpyxl |

**Module naming history:** `t12_writer.py` and `t12_translator.py` are named historically — they now write RR data into the **Analyzer's** `Rent Roll Input` sheet. The "t12" in the filenames refers to the original (now legacy) T12 Intake destination, not to T12 data. A future cross-cutting commit may rename to `rr_to_analyzer_writer.py` / `rr_to_analyzer_translator.py`. (This same note also exists in `SPEC-T12.md`.)

---

## Data flow

### Stage 0 — Pre-cleaning (NEW in v1.8.0)

Raw DataFrame is run through `pre_cleaner.clean_raw_rent_roll()` which strips:
- **Trailing summary block** (rows from "Totals" / "Grand Total" / "Summary" onward)
- **Page banners** ("Rent Roll", "Page N", "Community:", "As of Date:", etc.)
- **Legend / instruction rows** ("x: Excluded Units", "Care Level Codes", etc.)
- **Section-label banner rows** (single-cell rows like `Briar Glen Alzheimer's Special Care Center (853)`)
- **Blank padding rows** (every cell empty)

Conservative by default — only drops rows we're confident are noise.

### Stage 0.5 — Smart sheet selection (NEW in v1.8.0)

When no sheet name is provided, the normalizer scores all sheets by row count × column count + signal hits ("unit", "apartment", "resident", "bed", etc.) in the first 20 rows. Picks the highest-scoring sheet. Avoids picking tiny "Document map" / legend sheets.

### Stage 1 — Rent roll → Normalized DataFrame

Input: any senior-housing rent roll `.xlsx`.

The normalizer:
1. Auto-detects the header row by scanning the first 20 rows for high-signal column names
2. Walks rows with **three-way classification**:
   - **Parent-only**: has unit/apt info but no resident → set context, skip
   - **Self-contained**: has unit/apt info AND resident on same row → refresh context AND emit a record (Briar Glen single-bed pattern)
   - **Child bed**: has bed-level data only → emit record using prior context
3. Produces one row per bed
4. Runs a **second pass** to detect shared apartments (rooms with 2+ beds)

Each bed record is normalized for: Apt Type, Bed Status, Payer Type, Care Type (IL/AL/MC), Care Level (Level 1-5 or "Level 6+").

Care/ancillary monthly columns are auto-grouped by **two paths**:
- **Suffix path**: header has `level/amount/discount/(month)` suffix — prefix names the bucket
- **Standalone path**: header is itself a care-bucket name with no suffix (Briar Glen "Care Charges")

### Stage 2 — Normalized → 6-tab Excel output

Tabs: Condensed_RR, Normalized_Beds, RR_Summary, RR_By_Type, RR_Exceptions, Mapping_Reference, Run_Info.

### Stage 3 — Condensed_RR → Analyzer Rent Roll Input

When user uploads an Analyzer workbook, the app translates vocabulary and writes A:S row 7+ to the Analyzer's `Rent Roll Input` sheet, preserving everything else.

---

## Condensed_RR column layout (the 18-column analyst view)

| Col | Header | Source / Logic |
|---:|---|---|
| A | Unit # | `{Room}-{Bed}` composite (e.g., `101-A`); Briar Glen single-bed shows just room number |
| B | Room # | Apartment number from source (or Unit if no separate Apartment column) |
| C | Sq Ft | From source if present, else blank |
| D | Care Type | IL / AL / MC (via fallback chain) |
| E | Status | Occupied / Vacant / Hold / Notice / Model / Down |
| F | Apt Type | Studio / 1BR / 2BR / Companion / Semi-Private / Other; ` - Shared` suffix on multi-bed rooms |
| G | Market Rate | From source |
| H | Actual Rate | From source |
| I | Concession $ | Monthly concession from source |
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
- `DM` → MC (Briar Glen: Alzheimer's Care)
- `DU7` → MC (Briar Glen: Special Care)
- `LTC` → AL (Long-Term Care setting)
- `Alzheimer*`, `dementia` → MC

### Care Level — Level 1-5 plus Level 6+ bucket

User chose this over capping. Level 6, 7, 8+ all flow into `Level 6+`. For Analyzer paste, Level 6+ → Level 7, Level 1 → Basic.

For operators whose source has no acuity tiers (Briar Glen): Care Level is left **blank**. The Care Type column still resolves correctly.

### Shared apartment detection (second pass)

After parsing all bed rows, count beds per (Building, Room #) pair. Any room with 2+ beds gets ` - Shared` appended to its Apt Type on every row of that room. ` - Shared` suffix is stripped for Analyzer paste.

### Unit # composite

`{Room}-{Bed}` format. For single-Unit-column formats (Briar Glen), Unit IS the room — no building. For multi-column formats (Salem), Unit is the building code, Apartment is the room.

Briar Glen Privacy Level codes translate to bed letters: PRI/Single → no letter, SPA/DAS/QAS → A, SPB/DBS/QBS → B.

### Self-contained row detection (NEW in v1.8.0)

A row is "self-contained" if it has BOTH apartment-level info AND a **resident name** on the same row. Resident is the strict signal — rates alone don't qualify (Salem puts rates on parent rows).

Resolves Briar Glen single-bed format where everything is on one row per unit.

### Bed status fallback (NEW in v1.8.0)

If no `Bed Status` column exists, fall back to:
1. Resident name starting with `*Vacant` / `Vacant` / `(vacant)` → status = Vacant
2. Resident name present → status = Occupied
3. Resident name absent → status = Vacant

Briar Glen-specific: when status is detected from resident name, the `*Vacant` literal is stripped from the resident name field.

### Standalone care bucket columns (NEW in v1.8.0)

In addition to suffix-based detection (e.g., "AL Care (January 2026)"), the care-group detector now recognizes standalone columns whose name itself is the bucket: "Care Charges", "Med Mgmt", "Pharmacy", "Other Charges". The full header is treated as the monthly column.

Heuristic: the column must contain a care-related keyword (charge, service, care, medication, pharmacy, ancillary) to qualify, to avoid false positives.

### Concession detection — multi-column, negative-signed (NEW in v1.9.0)

`detect_concession_cols` recognizes multiple header patterns as concession sources and sums them all into `Concession $`:

- `Concession` (generic — covers Salem's `Concession (January 2026)`)
- `Recurring Discount(s)` (Briar Glen)
- `One-Time Incentive(s)` (Briar Glen)
- Generic `Discount` with a `(month)` suffix

**Sign convention: source values preserved (typically negative).** `Concession $ = -500` means a $500 reduction. `Total Monthly Revenue` adds the concession (`actual + LOC + concession`), which correctly applies a negative as a reduction. The Analyzer paste passes through column I as-is; the analyst sees `−500` in the standalone RR which reads naturally as "discount."

The care-group detector explicitly skips columns matching the concession patterns to prevent any future double-counting.

### Zero-vs-blank convention for numeric columns (NEW in v1.10.0)

**All** numeric output columns — both rates and per-bed dollar charges — output **blank** (None / NaN), not `0`, when there's no value. This lets analysts use `COUNT()` and `COUNTIF()` in Excel without zero-fills polluting the result.

**Pricing columns:**
- `Market Rate`, `Actual Rate`, `Rate Gap`, `Total Monthly Revenue`

**Charge columns:**
- `Concession $`, `Care Level $`, `Med Mgmt $`, `Pharmacy $`, `Other LOC $`, `Total LOC $`

A vacant bed in Briar Glen now has all 10 of these columns blank — visually distinct from an occupied bed with $0 in a single charge bucket.

**Filtering tip:** to find occupied beds, filter on `Status == "Occupied"` rather than `Actual Rate > 0`. Categorical fields are the source of truth for status.

**Implementation notes:**
- `_blank_if_zero(v)` helper in `normalizer.py` returns `None` for any numeric within 1e-9 of zero. Applied at the bed-record build step.
- Math (Rate Gap = market − actual, TMR = actual + LOC + concession) is computed on raw values BEFORE blanking, so derived columns stay correct.
- `reports.py` `build_summary` uses `fillna(0).mean()` for `Avg Market Rate (all beds)` and `Avg Actual Rate (all beds)` so the all-beds denominator includes vacant beds. `(occupied)` averages still skip blanks (correct — an occupied bed with blank rate is a data gap, not $0).
- `reports.py` `build_exceptions` coerces NaN to 0 via a local `_num()` helper before `<= 0` checks. Without this, `NaN <= 0` is False and would silently miss occupied-with-blank-rate data gaps.
- SUM() in Excel and pandas both treat NaN/None as 0 — totals are unaffected.

### Smart sheet selection (NEW in v1.8.0)

Multi-sheet workbooks (like Briar Glen with `Document map` + data sheet + legend) get an automatic best-sheet pick based on row × col + header signal scoring. Avoids tiny metadata sheets.

### Vocabulary translations for Analyzer paste

| Column | Condensed_RR → Analyzer |
|---|---|
| Apt Type | "1BR" → "1 Bedroom"; "2BR" → "2 Bedroom"; ` - Shared` suffix stripped; "Companion" → "Other" |
| Status | "Hold" / "Model" / "Down" → "Other" |
| Care Level | "Level 1" → "Basic"; "Level 6+" → "Level 7" |
| Payer | "VA Benefit" → "VA"; "Medicare" → "Other" |

### Period Date — auto-detect from filename

Six patterns in priority order: `YYYY-MM-DD`, `MM-DD-YYYY`, `M_D_YY`, `YYYY_MM`/`MM_YYYY`, `Mon_YYYY`, `MonDDYYYY`.

### Output filenames

- Standalone RR: `<source_stem> Normalized YYYY-MM-DD.xlsx`
- Populated Analyzer: `<analyzer_stem> with <rr_stem> YYYY-MM-DD.xlsx`

### Excel formatting

Charcoal + white theme: header `#2B2B2B`, white bold Calibri, banded rows, color-coded Status/Care Level/Care Type, currency `$#,##0`, dates `mm/dd/yyyy`, autofilters, frozen panes, print-ready.

### Design choices for end-user experience

- **Desktop-only by design.** Mobile uploads are unreliable on Streamlit Cloud's file uploader; underwriting workflow doesn't require mobile.

---

## Analyzer / T12 destination workbook structure

The canonical destination is now `ALF_Financial_Analyzer_Only.xlsx`. The legacy `ALF_T12_Intake_Final.xlsx` template is still compatible (same `Rent Roll Input!A7+` schema) but is deprecated for new use.

Both workbooks share the same expected layout for the destination sheet:
- Sheet named `Rent Roll Input` (the only sheet touched)
- Rows 1-6 untouched (header / instructions area)
- Rows 7-606 are the data area (max 600 bed rows per run)
- Cols T-U have IFERROR formulas to row 606 — left untouched
- Data validations on cols D / E / F / K / P
- All other tabs in the workbook are preserved exactly as uploaded

**Conditional formatting note:** openpyxl drops modern conditional formatting extensions on save (~49 KB lost from a 202 KB file). User accepted.

---

## Verified formats

| Format | Beds | Care Level $ | Concession $ | Notes |
|---|---:|---:|---:|---|
| Salem (Oaks) | 50 | $28,125.81 | $-2,841.45 (7 rows) | Original test case. Multi-column unit+apartment, Level 1-7 acuity, three care buckets. |
| Briar Glen | 79 (71 units, 8 shared) | $234,360.00 | $-14,132.00 (16 rows) | Single-column unit, two-letter care codes, *Vacant marker, monthly columns without suffixes, blank padding rows, totals block. Recurring Discounts + One-Time Incentives now mapped (v1.9.0). |

Both verified end-to-end on every release. Concession totals added to baseline in v1.9.0 to catch sign regressions.

---

## Known issues / limitations

1. **Conditional formatting drops on Analyzer save.** openpyxl limitation. User accepted.
2. **Sq Ft is blank** when source RR doesn't have it. Decision: don't fabricate.
3. **600-row Analyzer cap.** Hard limit by formula extent.
4. **No T12 normalizer yet** — separate component, not yet built. Next major piece of work.
5. **Streamlit Cloud free tier sleeps apps after 7 days idle.** First request after sleep takes ~30 seconds.
6. **Mobile upload not supported** — by design choice.

---

## How the analyst uses the app

1. Open https://rrnormalizer.streamlit.app/
2. Upload rent roll (sidebar, required)
3. Optional: upload mapping override workbook
4. Optional: upload ALF Financial Analyzer template
5. Optional: set Property Care Type default
6. App processes immediately
7. Click **Download Normalized Rent Roll** for the 6-tab analyst workbook
8. Click **Download Analyzer with Rent Roll** for the populated Analyzer (only available if an Analyzer was uploaded)

---

## What's next: T12 Normalizer

Still unbuilt. See CHANGELOG and the original handoff for context.

**Input:** raw T12 export (Yardi, RealPage, AppFolio, custom GL).

**Output:** populates `T12 Input` tab of the user's Analyzer template.

**Required logic:** account name normalization, month column detection, sign convention handling, annualization, mapping override workbook.

**Reference architecture from this project:** mappings.py override loader, Streamlit upload patterns, writer.py formatting, period_date.py, t12_writer.py paste pattern.

---

## Working principles

Things that worked well:
- Show proposed changes before building
- Single-select prompts for binary decisions
- Verify against real data at every step
- Bump APP_VERSION on every release
- Smaller commits across sessions

Things to avoid:
- Long unbroken chats — split by feature
- Multiple file changes without verifying each landed

---

## Maintenance protocol

**At the start of every chat:**
> "Read SPEC-RR.md and CHANGELOG-RR.md at https://github.com/ErikJ-Stack/rent-roll-normalizer. Then [task]."

**At the end of every chat that changes code:**
> "Update SPEC-RR.md to reflect what changed. Add a CHANGELOG-RR.md entry. Bump APP_VERSION and APP_LAST_UPDATED. Commit and push."
