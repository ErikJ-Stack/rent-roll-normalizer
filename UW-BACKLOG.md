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

*(BL-0002, BL-0008, and BL-0010 moved to Shipped — see below.)*

---

## Shipped

### [BL-0010] Module rename — `t12_translator.py` → `analyzer_rr_translator.py`
- **Shipped in:** RR v1.17.2 (2026-05-14)
- **Track:** Refactor (Track 1)
- **Originally surfaced in:** 2026-05-10 partial rename (`t12_writer.py` →
  `analyzer_rr_writer.py`); the partner module was deferred to "whenever
  bundled."
- **Summary:** `git mv` rename. Single live import in `app.py` line 50
  updated; one docstring reference in `analyzer_rr_writer.py` updated.
  Function name `translate_for_t12()`, translation tables, and the
  exception class `T12CapacityError` (still exported by
  `analyzer_rr_writer.py`) all retained for surgical scope. CLAUDE.md
  "Module naming gotcha" rewritten to reflect that the Track 1 file
  disambiguation is now complete; only the legitimate Track 2 `t12_*`
  files (`t12_normalizer.py`, `t12_normalizer_writer.py`) remain with
  the prefix.

### [BL-0009] Branch 2 — Handoff readiness (UW Export + Pre-Export Gate + metadata header)
- **Shipped in:** substrate v0.2.0 (2026-05-14, flagship release)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** CLAUDE.md "Open carry-forwards" — long-standing
  Track 3 roadmap item from the four-branch plan.
- **Summary:** Three coordinated additions ship the final piece of the
  Track 3 roadmap. (1) New **`UW Export` sheet** at index 8 — title +
  italic instructions + 5-row metadata header (Property / RR period /
  T12 period / Substrate version / Generated timestamp) + 71-row × 8-col
  values-only mirror of UW Output via `='UW Output'!{cell}` formulas.
  When opened in Excel the cells evaluate to values; downstream consumer
  copies-as-values into their template. (2) New **Pre-Export Gate**
  section on Workbook Health (rows 46-52) aggregating existing V1-V8
  validation checks into four P-checks plus a single ✓/⚠ "READY FOR
  EXPORT" aggregate cell at row 52. (3) **Workbook Map extension**
  adding `UW Export` row at Workbook Health row 19. **The four-branch
  Track 3 roadmap is now fully closed** (Branches 1+4 in v0.1.6, Branch 3
  in v0.1.8 through v0.1.14, Branch 2 in this v0.2.0 release).

### [BL-0008] Substrate version-detection in `app.py`
- **Shipped in:** RR v1.17.1 (2026-05-14)
- **Track:** RR (Track 1)
- **Originally surfaced in:** CLAUDE.md "Open carry-forwards"
- **Summary:** Rewrote `_detect_substrate_version()` with a three-tier
  resolution strategy. Primary path reads `Cover!B8` (the canonical
  version stamp set by every migration since v0.1.4). Fallback uses
  newest-to-oldest sentinel cells (Rent Roll Recon!I87, T12 Analytics!A168,
  Rent Roll Input!AC4, Rent Roll Recon!A119, Rent Roll Input!V4). Legacy
  Description_Map heuristic preserved for pre-v0.1.10 Analyzers. The
  prior implementation was stale-capped at `v0.1.5` since v1.12.0.
  Sanity-checked on the bundled v0.1.14 Analyzer (reports `v0.1.14`) and
  user's populated Homestead workbook at v0.1.10 (reports `v0.1.10`).

### [BL-0002] V5 chart — empty rendering for broker-format rent rolls
- **Shipped in:** substrate v0.1.15 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** substrate v0.1.11 verification on Homestead
- **Summary:** Improved V5 (AL Acuity Mix) empty-state UX without
  restructuring the chart. (1) Wrapped `Rent Roll Recon!D59:D66` formulas
  with `IF($B$67=0, "", ...)` so the doughnut renders as a true empty
  frame (no zero-valued slices) when source has no acuity data.
  (2) Applied bold + pale-yellow fill styling to `T12 Analytics!K45`
  (the existing v0.1.8 conditional note "Property has no AL acuity data
  — flat-rate AL or unpopulated.") so the empty-state message reads as
  a warning attached to the chart instead of an ignorable label.
  
  Chose option (a) "accept and document" with strengthened styling rather
  than option (b) "fallback Care Type breakdown" because Homestead has
  $0 Care Level $ total across all 176 beds — a Care Type fallback
  chart would also be empty for the user's headline fixture. Option (c)
  "hide the chart" wasn't available in openpyxl without chart XML
  manipulation. When a flat-rate-AL fixture surfaces (Care Level $ > 0
  but no acuity tiers), revisit option (b) as a follow-up.

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
