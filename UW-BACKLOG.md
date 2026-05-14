# UW-BACKLOG.md — forward-looking changes for the underwriting workbook

Items the analytical sheets need but haven't shipped yet. Each entry has a
track, a target version, and a status. Items move to **Shipped** when they
land; they keep their `BL-NNNN` ID so cross-references in CHANGELOG entries
stay stable.

**Numbering:** sequential `BL-NNNN`. New items get the next number; reuse is
forbidden. When closing, leave the ID in place and add a `Shipped in <release>`
line + a one-paragraph summary.

**Sort:** within each status section, by track then target version.

**Sources to sweep when adding new items:** "Out of scope" / "Carry-forwards
opened" sections in [CHANGELOG-T12.md](CHANGELOG-T12.md) and
[CHANGELOG-RR.md](CHANGELOG-RR.md), plus the "Open carry-forwards" section in
[CLAUDE.md](CLAUDE.md). Items here are the authoritative forward-looking
list — the CHANGELOG carry-forward notes are pointers, not the source of
truth.

---

## Pending

### [BL-0001] Finer ancillary Labels in `Description_Map`
- **Track:** Substrate (Track 3) · target **substrate v0.2.0**
- **Surfaced in:** substrate v0.1.12 Section M (this release)
- **Description:** Section M3 collapses 5 of the 7 default Homestead IL fees
  (Elective Transfer / Meal Delivery / Motorized Scooter / Housekeeping /
  Laundry) into the single Label `Other community revenue`. The Section M3
  formula detects shared-bucket Labels and shows "(shared — see row N)" on
  subsequent occurrences to avoid double-reporting the same dollar amount.
  Per-fee T12 attribution is impossible until each fee has its own Label.
- **Scope:** add 5 new Labels — `Meal Income`, `Housekeeping Income`,
  `Laundry Income`, `Scooter Fee Revenue`, `Transfer Fee Revenue`. Each
  needs (a) row in `Description_Map`, (b) aggregation row in `T12 Raw Data`
  with SUMIF formulas, (c) row in `Monthly Trending` (with downstream row
  shift handled per the openpyxl quirks documented in CHANGELOG-T12 v0.1.5).
  Closed vocabulary grows from 55 → 60 Labels.
- **Why deferred from v0.1.12:** vocabulary expansion is a substrate-version
  increment (v0.2.0 territory), not a patch. v0.1.12 ships the analytical
  surface that exposes the need.
- **Depends on:** nothing. Orthogonal to BL-0003 (RR Input expansion) but
  mutually amplifying — when both ship, Section M validates *both* sides of
  the ancillary revenue picture.

### [BL-0002] V5 chart — empty rendering for broker-format rent rolls
- **Track:** Substrate (Track 3) · target **substrate v0.1.13** or **v0.2.0**
- **Surfaced in:** substrate v0.1.11 (chart axis fix) verification on
  Homestead.
- **Description:** The V5 doughnut (AL Acuity Mix) on T12 Analytics queries
  `Rent Roll Input!K` (Care Level) grouped by `Basic / Level 2-7`. Homestead
  and other broker-condensed formats have no per-bed acuity tiers — column K
  is empty for all 176 rows, so SUMIFS for every category returns $0 and the
  doughnut renders empty. Not a chart bug; data limitation.
- **Options:**
  - (a) Accept and document — V5 only useful when source has acuity.
  - (b) Fall back to "Care Level $ grouped by Care Type" when source has no
    acuity. Repurposes V5 for broker-format sources.
  - (c) Hide chart conditionally when the underlying SUMIFS all return $0
    (set chart `plotVisOnly` + a conditional data-source switch).
- **Recommended:** **(c)** — preserves the chart for sources that DO have
  acuity (e.g. Salem, Oaks at Beaufort) while not showing an empty doughnut
  for sources that don't.

### [BL-0008] Substrate version-detection in `app.py`
- **Track:** RR (Track 1) · target whenever bundled with another RR change
- **Surfaced in:** CLAUDE.md "Open carry-forwards"
- **Description:** `_detect_substrate_version()` looks for `2nd Person
  Revenue` Label (v0.1.5 marker). v0.1.6-v0.1.12 all add no new Labels in
  `Description_Map`, so the detector returns `v0.1.5` for any v0.1.5+
  Analyzer. Cosmetic — display-only; never gates functionality.
- **Scope:** widen the marker list:
  - v0.1.10+: detect by `2nd Person Rent $` header presence at
    `Rent Roll Input!V4`
  - v0.1.11+: detect by chart catAx `axPos` value (would require parsing
    chart XML — overkill; v0.1.11 has no other distinguishing cell change)
  - v0.1.12+: detect by `Rent Roll Recon!A119` Section M title presence

### [BL-0009] Branch 2 — Handoff readiness (UW Export, pre-export gate, metadata header)
- **Track:** Substrate (Track 3) · target **substrate v0.2.0**
- **Surfaced in:** CLAUDE.md "Open carry-forwards" (long-standing Track 3
  roadmap item)
- **Description:** Per the Track 3 roadmap, the four-branch plan is:
  Branches 1+4 (correctness + substrate, closed in v0.1.6); Branch 3
  (analytical coverage, closed in v0.1.8 + extended in v0.1.10/v0.1.12);
  Branch 2 (Handoff readiness, **still open**). Includes:
  - **Pre-export gate**: validates required cells are populated; no formulas
    showing `#REF` / `#NAME` / `#N/A`; period date set; property name stamped.
  - **UW Export sheet**: values-only mirror of `UW Output` for clean
    copy-paste into the downstream full-underwriting sheet (which doesn't
    consume formulas — only values).
  - **Metadata header on UW Export**: deal name, period date, RR + T12
    versions, source filenames, run timestamp. Provides downstream sheet a
    full audit trail.
- **Scope:** larger feature — substantial Track 3 work. Likely the v0.2.0
  flagship release.

### [BL-0010] Module rename — `t12_translator.py` → `analyzer_rr_translator.py`
- **Track:** Refactor (cross-cutting) · target **whenever bundled**
- **Surfaced in:** 2026-05-10 partial rename (`t12_writer.py` →
  `analyzer_rr_writer.py`); the partner module was deferred.
- **Description:** Pair to the 2026-05-10 rename. `t12_translator.py`
  translates `Condensed_RR` vocabulary into the Analyzer's data-validation
  vocabulary — RR-side concern, despite the historical `t12_` prefix.
  Rename via `git mv`, update imports in `app.py`. The exception class
  `T12CapacityError` exported by `analyzer_rr_writer.py` retains its old
  name for the same "keep the rename surgical" reason — could be renamed
  to `AnalyzerRRCapacityError` in the same commit.
- **Scope:** 1 `git mv` + ~5 line updates across `app.py` (import) +
  `SPEC-RR.md` (file inventory) + `CLAUDE.md` (module naming gotcha
  paragraph).

---

## Shipped

### [BL-0004] T12 Analytics — 2P revenue reconciliation row
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added per-bed SP capture at col V)
- **Summary:** 3-row block on T12 Analytics rows 168-170 (after the existing
  KPI Dashboard color key at row 166). Compares `=SUM('Rent Roll Input'!$V$7:$V$606)*12`
  (RR-projected annual 2P revenue) against `=IFERROR('T12 Raw Data'!$R$15,0)`
  (T12 actual annual 2P revenue). Variance % + conditional note fires when
  \|variance\| > 10%. Placement chose rows 168+ because the natural slot at
  rows 42-44 had pre-existing horizontal merges (A43:H43, A45:H45) for visual
  breaks between GPR Waterfall and Other Revenue Normalization Bridge.

### [BL-0005] Workbook Health — total AR / Balance aggregation
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Balance column at `Rent Roll Input!X`)
- **Summary:** 3 new rows extending the Workbook Health DIAGNOSTICS section.
  Row 43: `G9 · Total outstanding AR` = `SUM('Rent Roll Input'!$X$7:$X$606)`.
  Row 44: `G10 · AR ÷ monthly EGI` = `B43 / ('Monthly Trending'!$N$21/12)`.
  Row 45: conditional note (merged A:D) — ⚠ fires when AR > 5% of monthly
  EGI; ✓ "within 5%" otherwise. Slots after the existing G8 'Last opened'
  volatile timestamp at row 42.

### [BL-0006] Rent Roll Recon Section K — Avg Actual PSF column
- **Shipped in:** substrate v0.1.14 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Actual PSF at `Rent Roll Input!AA`)
- **Summary:** New col I "Avg Actual PSF" on Section K IL unit-type table.
  I87 header + I88-I92 per-unit-type AVERAGEIFS on `Rent Roll Input!$AA$7:$AA$606`
  (Actual PSF) + I93 Total IL row. Same filter pattern as existing col D
  (Avg Rate). Sources from per-bed data captured at v1.16.0; cell-only
  extension of the existing table (cols A-H untouched, dispersion rows
  95-100 untouched). Complements the existing derived `$/Sq Ft` column at H
  (which divides Avg Rate ÷ Avg Sq Ft) — col I pulls the direct per-bed PSF
  average for cross-validation.

### [BL-0003] RR Input expansion — per-fee ancillary columns
- **Shipped in:** RR v1.17.0 + substrate v0.1.13 (2026-05-13)
- **Track:** RR (Track 1) + Substrate (Track 3) — cross-cutting single PR
- **Originally surfaced in:** substrate v0.1.12 Section M2 (4 of 7 default
  fees fell through to "no per-fee RR column yet" notes pointing here)
- **Summary:** Per-fee ancillary columns added at `Rent Roll Input!AC-AG`
  (`Meal Plan $`, `Scooter Fee $`, `Housekeeping $`, `Laundry $`, `Pet $`).
  `mappings.py` extended with 8 new bucket-routing rules; `normalizer.py`
  bucket_sums + bed record + CONDENSED_COLUMNS extended (25 → 30);
  `analyzer_rr_writer.py` writes the new fields. Substrate v0.1.13 adds the
  RRI columns, extends Total LOC $ formula to include AC-AG, adds a 5th
  "RR Input Col" mapping column to Section M1, and rewrites M2/M4 with
  universal `INDIRECT` formulas off that mapping. M2 eligibility unified
  to all-occupied beds (was IL-only for SP).
  **End-to-end on Homestead**: Pet $100, Housekeeping $1,450, Laundry $630
  split out from Other LOC $; Total LOC $ unchanged ($-9,966.75 of
  ancillary preserved across the 5 split + Other LOC catchall). Salem /
  Briar Glen / Beaufort baselines all green; Beaufort surfaces $65 in
  `Laundry $` previously buried in Other LOC $.

### [BL-0007] RR Other LOC keyword expansion — meal / scooter / mobility / transport
- **Shipped in:** RR v1.16.2 (2026-05-13, PR #15)
- **Track:** RR (Track 1)
- **Originally surfaced in:** substrate v0.1.12 Section M (M2 fees that "fall
  into Misc.")
- **Summary:** Added `meal`, `scooter`, `mobility`, `transport` to the
  `_looks_care` keyword list in `detect_care_groups` (`normalizer.py`).
  Matches v1.15.1's prior keyword broadening pattern. Future-proofs the
  parser for operators whose source rent rolls expose those services as
  named columns. **No impact on Homestead specifically** — its broker
  format bundles optional services into a single `Misc.` column rather
  than breaking them out. Regression-verified against all three baseline
  fixtures (Salem, Briar Glen, Beaufort) with no drift.

*(Pre-v0.1.12 closed items are documented in CHANGELOG-T12.md and
CHANGELOG-RR.md; no retroactive backfill needed here.)*
