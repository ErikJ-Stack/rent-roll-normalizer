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

### [BL-0003] RR Input expansion — per-fee ancillary columns
- **Track:** RR (Track 1) **+ substrate** (Track 3) · target
  **RR v1.17.0 + substrate v0.1.13**
- **Surfaced in:** substrate v0.1.12 Section M2 (4 of 7 default fees fall
  through to "no per-fee RR column yet" notes pointing here)
- **Description:** Today the RR parser lumps Meal / Scooter / Housekeeping /
  Laundry / other ancillaries into `Other LOC $` (col O on Rent Roll Input).
  Section M2's RR-capture rate works ONLY for fees with a direct RR column —
  currently `Second Person Rent` (col V, added v1.16.0). Adding named
  columns for the four most common ancillaries unlocks per-fee capture-rate
  validation in Section M.
- **Scope:**
  - **Parser** (`normalizer.py`): extend the keyword-bucketing logic in
    `_looks_care` (currently a flat "is this column a care line" check) to
    also categorize hits into named buckets — `meal`, `scooter` / `mobility`,
    `housekeeping` / `h/k`, `laundry`. Add fallback aggregate bucket for
    anything that matches `looks_care` but doesn't match a named bucket.
  - **Substrate**: add 4-6 new columns at `Rent Roll Input!AC-AH`:
    - `AC` `Meal Plan $` (monthly $)
    - `AD` `Scooter Fee $` (monthly $)
    - `AE` `Housekeeping $` (monthly $)
    - `AF` `Laundry $` (monthly $)
    - `AG` `Other Ancillary $` (monthly $ — catch-all that doesn't match the
      named buckets; preserves the existing Other-LOC-style total-protection)
    - `AH` `Total Ancillary $` (formula `=SUM(AC:AG)`)
  - **Writer** (`analyzer_rr_writer.py`): write the new fields into the new
    cols.
  - **Section M2**: rewrite the 4 currently-deferred fee rows (Meal Delivery,
    Motorized Scooter, Housekeeping, Laundry) to use real
    `COUNTIF / SUMIFS` against the new columns instead of the
    `"falls into M5 Misc."` placeholder text.
- **Why deferred:** cross-cutting (Track 1 parser + Track 3 substrate), should
  ship in its own scoped PR.
- **Depends on:** BL-0007 (RR Other LOC keyword expansion) — at least the
  meal / scooter / mobility / transport keywords. Can ship BL-0007 first to
  capture the dollars into the existing `Other LOC $`, then BL-0003 to split
  them out into named columns.

### [BL-0004] T12 Analytics — 2P revenue reconciliation row
- **Track:** Substrate (Track 3) · target **substrate v0.1.13**
- **Surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added per-bed
  SP capture)
- **Description:** Compare `SUM('Rent Roll Input'!V) × 12` (RR-projected
  annual 2P revenue from per-bed entries) against `T12 Raw Data!R15`
  (T12 actual annual 2P revenue). Same pattern as the Section B revenue
  reconciliation on Rent Roll Recon. Flags rate misalignment or
  under-collection.
- **Scope:** ~5 cells on T12 Analytics: implied / actual / variance %
  / conditional note (fire when variance > 10% one way or the other).

### [BL-0005] Workbook Health — total AR / Balance aggregation
- **Track:** Substrate (Track 3) · target **substrate v0.1.13**
- **Surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Balance
  column at `Rent Roll Input!X`)
- **Description:** Aggregate `Rent Roll Input!X` (Balance) into a Workbook
  Health validation row. Surface total outstanding AR + AR / monthly EGI %.
  Conditional note fires if AR > 5% of monthly EGI as a collection-velocity
  risk indicator.
- **Scope:** 2-3 cells on Workbook Health.

### [BL-0006] Rent Roll Recon Section K — PSF dispersion stats
- **Track:** Substrate (Track 3) · target **substrate v0.1.13**
- **Surfaced in:** substrate v0.1.10 carry-forward (RR v1.16.0 added Market
  PSF / Actual PSF at `Rent Roll Input!Z-AA`)
- **Description:** Section K's IL deep-dive already shows rate dispersion and
  avg sqft per unit-type. Adding avg / range of $/sqft (PSF) per unit-type
  catches under-priced legacy in-place residents along a dimension
  orthogonal to the existing rate-CV check.
- **Scope:** 1-2 new metric rows in Section K (rows 86-100). Pulls from
  `Rent Roll Input!Z` and `!AA`.

### [BL-0007] RR Other LOC keyword expansion — meal / scooter / mobility / transport
- **Track:** RR (Track 1) · target **RR v1.16.2 patch**
- **Surfaced in:** substrate v0.1.12 Section M (M2 fees that "fall into
  Misc.")
- **Description:** v1.15.1 widened `_looks_care` for `pet`, `housekeeping`,
  `h/k`, `laundry`, `misc`, `diabet`. Meal / scooter / mobility / transport
  still aren't caught — those source columns are silently dropped if their
  header doesn't match other keywords. Needed before BL-0003 can split them
  into named columns.
- **Scope:** 3-5 keyword additions in `normalizer.py`. Single-file patch,
  matches v1.15.1 pattern. Trivial.

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

*(Empty — items will move here as they ship. The pre-v0.1.12 closed
items are already documented in CHANGELOG-T12.md and CHANGELOG-RR.md;
no retroactive backfill needed here.)*
