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

### [BL-0012] Section M — Misc/Diabetes credit reconciliation against T12 `Concessions & specials`
- **Track:** Substrate (Track 3) · target **substrate v0.2.2+**
- **Surfaced in:** RR v1.17.0 (BL-0003) "Side observation worth tracking"
  in CHANGELOG-RR.md.
- **Description:** Homestead's residual `Other LOC $` post-split is
  **-$12,146.75** (Diabetes + Misc, both partially negative — net
  credit). The residual was negative before BL-0003 too (entire OCR was
  -$9,966.75); the per-fee split just makes the negative-net portion
  visible as a residual after attributing the named buckets. The
  hypothesis is that the negative residual reflects discount/credit
  postings that operators sometimes route through Other LOC instead of
  the formal `Concessions` GL — but Section M5 currently treats
  negative residuals the same as positive, so it surfaces a misleading
  "✓ Misc. income share within band" note when the bucket is actually
  negative.
- **Scope:** add a Section M6 (or extend M5) on Rent Roll Recon that
  compares the residual `Other LOC $` (when negative) against the
  T12 `Concessions & specials` Label total. If the negative residual
  is plausible as misposted concessions, flag a reconciliation note;
  if not, surface a data-quality warning. Rough implementation: ~5-10
  cells on Rent Roll Recon below the existing Section M, conditional
  formula-driven with a ⚠ trigger when |negative residual| > 10% of
  T12 Concessions absolute value.
- **Conditional on:** observing the same negative-residual pattern in
  one more Homestead-format deal (or any non-Homestead operator). If
  it's idiosyncratic to this single Homestead fixture, defer
  indefinitely. If it persists, ship as part of substrate v0.2.2.
- **Depends on:** nothing structural. Reads existing Section M data
  + existing T12 Raw Data `Concessions & specials` Label.


---

## Shipped

### [BL-0016] Rent Roll Input!AH4 — missing header fill made "Total Ancillary $" label invisible
- **Shipped in:** substrate v0.2.4 (2026-05-16)
- **Track:** Substrate (Track 3)
- **Surfaced in:** User report on 2026-05-16 while inspecting the populated Homestead v0.2.3 Analyzer: "rent roll input tab has a missing label on row 4."
- **Summary:** Diagnosis confirmed the header text + white bold font were present at AH4 but the cell's PatternFill was transparent (`fill_type=None`, fgColor `00000000`), so white text rendered on the default white/default background — the column header was effectively invisible. AH was the new "Total Ancillary $" column added in substrate v0.2.2; the header palette step (green `FF1F6B52` for computed-column headers like T4 / U4, navy `FF1F3864` for input columns) was missed for AH specifically. v0.2.4 applies the green fill (AH is computed via `=IFERROR(V+AC+AD+AE+AF+AG,0)`, so green is correct per the substrate's existing convention). One-cell fix via `migrate_to_v024.py` Step A, shipped bundled with BL-0017.

### [BL-0017] Workbook-wide "intentionally blank" visual convention
- **Shipped in:** substrate v0.2.4 (2026-05-16)
- **Track:** Substrate (Track 3)
- **Surfaced in:** User report on 2026-05-16 (same chat as BL-0016): "T12 Analysis tab E36:E37 doesn't add up." Diagnosis split into three threads — (1) E vs. F columns are independent T12-vs-RR comparisons, not row totals; (2) E37 is correctly blank because Homestead's T12 reports `Gross Rent Revenue=0` per the H37 design note; (3) E36 + G36 store the 3-character string `"-"` with quotation marks as part of the text payload (`data_type='s'`), so Excel renders them as `"-"` with visible quote marks. Initial fix scoped narrow (just E36/G36 cleared to None) was then expanded after user pointed out the same literal `"-"` appears in 142 other cells on UW Output + 1 on Rent Roll Recon and all share the same design intent.
- **Summary:** v0.2.4 establishes a workbook-wide "intentionally blank" visual convention. **144 cells** — T12 Analytics E36/G36 (2), UW Output cols B/C/D × rows {8-12, 22-28, 30-36, 38-56, 58-60, 62-64, 66-68} (141), Rent Roll Recon D109 (1) — restyled as: **value=`—` (em-dash plain text, not formula or quoted) + fill=solid `FFF2F2F2` (light gray) + font color=`FFA0A0A0` (medium gray, preserving size/bold/italic) + horizontal alignment=center (preserving vertical/wrap/indent)**. New user-facing rule: gray + em-dash = "blank by design"; truly empty = "data not yet populated". The 144-cell target list is enumerated explicitly in `migrate_to_v024.py` `build_blank_targets()` — future migrations adding new "intentionally blank" cells should extend this list and apply the same treatment. **Out of scope:** formula-conditional blanks like T12 Analytics E37/G37/H38 that return `""` only when source data is missing. Those are "blank when data isn't here" not "blank by design"; permanent styling would mislead. A future BL can add Excel conditional formatting if that distinction matters in practice. Shipped bundled with BL-0016 via `migrate_to_v024.py` Step B.

### [BL-0011] Function/class renames — `populate_t12()` → `populate_rr_input()` + `T12CapacityError` → `AnalyzerRRCapacityError`
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Refactor (Track 1)
- **Originally surfaced in:** RR v1.17.2 (BL-0010) `analyzer_rr_writer.py` rename — the CLAUDE.md note explicitly deferred the function/class renames as a "separate, more invasive follow-up."
- **Summary:** Completes the Track 1 misnamed-T12-symbol cleanup at file + function + class level. Changed: function `populate_t12()` → `populate_rr_input()` (mirrors the partner `populate_t12_input()` on `t12_normalizer_writer.py` which correctly populates `T12 Input`); exception `T12CapacityError` → `AnalyzerRRCapacityError` (matches the 2026-05-10 file rename); also took the opportunity to rename the function-body parameter `t12_bytes` → `analyzer_bytes` and clean up two "T12 workbook" → "Analyzer workbook" references in inline error text. Updated callers in `app.py` (1 import, 1 call site, 1 except clause). Updated live docs (CLAUDE.md "Module naming gotcha" table, SPEC-T12.md module-naming-history paragraph). Historical CHANGELOG / journal references to the old names left intact (records of what shipped at past versions). Verified: `analyzer_rr_writer` imports cleanly with new symbols, old symbols confirmed removed; `app.py` parses cleanly; zero remaining live `populate_t12\b` / `T12CapacityError` references in `*.py`. The only surviving `t12_*` symbol on the Track 1 side is the function name `translate_for_t12()` on `analyzer_rr_translator.py` — left alone since `for_t12` reads as "for the destination workbook" and renaming it would touch every caller of the translator. Bundled in one tidy-up PR with BL-0013 + BL-0014.

### [BL-0013] README.md modernization — T12 + bundled-Analyzer framing
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Documentation (cross-cutting)
- **Originally surfaced in:** RR v1.14.0 and earlier releases. Flagged as a known carry-forward across multiple chats.
- **Summary:** Targeted README updates (NOT a full rewrite — README had been substantially modernized since the BL ticket was opened, with dual-pipeline framing and T12 coverage already in place). Bumped the versions table to RR v1.17.5 / 2026-05-15. Refreshed the Data-capture coverage section from "RR v1.16.0 + substrate v0.1.10 (cols A-AB)" to "RR v1.17.4 + substrate v0.2.2 (cols A-AH)" — adds the v0.1.13 per-fee ancillary cols (AC-AG), the v0.2.2 Total Ancillary rollup (AH), the v0.2.1 5 finer T12 Labels closing the per-fee attribution gap on Section M, and the v1.17.4 parser-side Notes-rerouter for Homestead concession patterns. Reframed the Analyzer-at-a-glance section as "Track 3 four-branch roadmap fully closed at substrate v0.2.0" with Section M description and the v0.2.0 UW Export sheet + Pre-Export Gate descriptions. Updated the Versioning section (substrate convention `v0.1.N` → `v0.X.Y`) and added UW-BACKLOG.md mentions in both the Versioning section and the Further Reading table. Bundled in one tidy-up PR with BL-0011 + BL-0014.

### [BL-0014] CLAUDE.md hygiene — refresh "Open carry-forwards" + expand openpyxl quirk #4
- **Shipped in:** RR v1.17.5 (2026-05-15)
- **Track:** Documentation (Track 3-adjacent)
- **Originally surfaced in:** Sweep 2026-05-14, post-substrate v0.2.1.
- **Summary:** Two CLAUDE.md sections fixed. (1) **Open carry-forwards section** — header date refreshed to 2026-05-15 / post-substrate v0.2.3 + RR v1.17.5; the entire "Medium priority (still open)" + "Low priority" sub-sections deleted (they were stale by weeks — "Branch 2 — Handoff readiness" was listed as open while it had shipped as BL-0009 / substrate v0.2.0; "Substrate version-detection bug suspected" was listed while it had shipped as BL-0008). Replaced with a single sentence pointing readers at UW-BACKLOG.md as the source of truth. (2) **openpyxl quirk #4** — expanded with the qualified-range-endpoint trap from BL-0001's migration. Documents both the failure mode (`T12_Calc!$N$1:$N$500`'s endpoint is mis-caught by the unqualified-ref regex and shifted on row inserts, causing off-by-N SUMIF/SUMIFS drift after migrations) and the canonical fix (capture template formulas AFTER the shift sweep, not before — see `tools/migration/migrate_to_v021.py:312-321`). Section heading bumped from "Three" to "Four" since quirk #4 is now substantive. Module naming gotcha table also updated as part of BL-0011. Bundled in one tidy-up PR with BL-0011 + BL-0013. Did NOT include the journal.md back-fill of v0.1.11 → v0.2.2 entries — that observation remains unstaffed.

### [BL-0015] Rent Roll Recon row 16 — GPR realignment (`$H` × occupied → `$G` × all units)
- **Shipped in:** substrate v0.2.3 (2026-05-14)
- **Track:** Substrate (Track 3)
- **Originally surfaced in:** user-reported on 2026-05-12 against the populated Homestead v0.1.10 Analyzer ("Row 16 says Gross RR at 100% occupancy is $565k but the market rate total is $809k"). First implementation shipped as substrate v0.1.11 in [PR #12](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/12); PR went stale while main moved through v0.1.12 → v0.2.2, was closed unmerged + re-implemented here as v0.2.3 with the current 14-sheet anchor list and the v0.1.11 substrate number reused on main for an unrelated chart-axis fix.
- **Summary:** Realigns `Rent Roll Recon!B16:D16` with the intent already documented in column H ("Gross contracted rates before concessions"). Old formula summed Actual Rate (`'Rent Roll Input'!$H`) over occupied units only — producing "current contracted at actual rate" rather than the Gross Potential Rent at 100% occupancy that the row's role as the underwriting anchor demands. New formula sums Market Rate (`$G`) over all units regardless of status, by care type. On Homestead populated: E16 reconciles from $565,140 → **$809,567** (IL $167k + AL $328k + MC $315k). Row 17 (effective net after concessions) is unchanged — its `H + I` is already correct because concessions are negative-signed (per [SPEC-RR.md L184](SPEC-RR.md)). A16 label rewritten to "RR Gross Potential Rent / mo  (Market × all units)" ("contracted" was misleading once vacants are included). H16 note rewritten to state GPR semantics + identify the row16-vs-row17 gap as vacancy + market-vs-actual premium ($244k on Homestead). Migration via `migrate_to_v023.py` — 3 ops, 9-check verify, idempotent. Closes the loop on the user-reported issue from 2026-05-12.

### [BL-0001] Finer ancillary Labels in `Description_Map`
- **Shipped in:** substrate v0.2.1 (2026-05-14) + RR v1.17.3 (companion `_detect_substrate_version()` widening)
- **Track:** Substrate (Track 3) + companion patch on RR (Track 1)
- **Originally surfaced in:** substrate v0.1.12 Section M (the analytical
  surface that exposed the per-fee attribution gap)
- **Summary:** 5 new Labels added to the closed vocabulary (55 → 60):
  `Meal Income`, `Housekeeping Income`, `Laundry Income`,
  `Scooter Fee Revenue`, `Transfer Fee Revenue`. Each gets (a) a row in
  T12 Raw Data with SUMIF formulas against `T12_Calc` (cols F-R), (b) a
  row in Monthly Trending with INDEX/MATCH formulas against T12 Raw
  Data (cols B-N), (c) typical Description→Label mappings appended to
  Description_Map (14 new rows, 2-4 per Label). Section M D-column on
  Rent Roll Recon re-pointed: 5 of the 7 default fees (rows 124-129
  except 127) move from `Other community revenue` → their new specific
  Labels. M3's `(shared — see row N)` heuristic resolves automatically
  since each row's COUNTIF finds no duplicates. EGI on Monthly
  Trending R26 (was R21) rewritten to include the 5 new rows.
  Migration via `migrate_to_v021.py` — single 5-row insert at each
  destination (`insert_rows(target, amount=5)`), full-workbook shift
  sweep for row refs ≥ threshold, idempotent gate, 13-check
  verification. Companion `app.py` patch widens the version-detection
  regex `v0\.1\.\d+` → `v\d+\.\d+\.\d+` so v0.2.x reports accurately;
  bundled in the same PR. **UW-BACKLOG is now empty** for the first
  time since this file was introduced in substrate v0.1.12.

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
