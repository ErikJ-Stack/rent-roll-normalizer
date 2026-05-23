# Changelog — T12 Normalizer

All notable changes to the T12 Normalizer (Track 2). Independent version stream from the Rent Roll Normalizer (Track 1, currently v1.17.5). This changelog covers T12 work only — see `CHANGELOG-RR.md` for RR releases.

Format: each version has a section with date, summary, and per-file change notes. Newest at top.

When making a code change in a T12-related chat, add an entry here in the same commit.

---

## [Substrate template v0.2.11] — 2026-05-23

### Summary

**Closes the Track-3-shaped portion of UW-BACKLOG BL-0023** (AR & Collections module). Adds two presentation-layer touches that surface AR signal at the workbook's top-level views without changing any AR computation logic. Pairs with v0.2.10 (sheet + Workbook Health gates) and the parser/writer/UI work shipped alongside in the AR module commits (`ar_normalizer.py`, `ar_writer.py`, `app.py` wiring).

### What changed (migrate_to_v0211.py)

- **A. Dashboard variance tile at K10:L13** (previously empty):
  - K10:L10 (merged) title "BAD DEBT VARIANCE" matching the REVPOR/EBITDARM headline-tile style (Calibri 9pt bold white on blue FF5B9BD5).
  - K11:L12 (merged) value formula: `=IF('AR & Collections'!Z1=0,"— upload AR to populate",'AR & Collections'!C56)`. Calibri 12pt bold navy on white, wrapped, centered. Tile is dormant when Z1=0 (no AR uploaded), live ⚪/✓/⚠ when Z1=1.
  - K13:L13 (merged) footnote "= T12 bad debt − annualized AR write-offs" (Calibri 9pt italic gray on FFF2F2F2).
- **B. Cover row 11 AR Module version line.** `A11 = "AR Module"`, `B11 = "v0.1.0"`. Sits in the existing empty row between T12 Normalizer (R10) and the Links section (R12) — no row inserts. Style borrowed from A10/B10 for consistency.
- **C. Cover!B8 stamped v0.2.11 + AZ4 on all 16 sheets.**

### Idempotency

Gate triple-checks Cover!B8, Dashboard!K10 title, Cover!A11 label. Re-run is a clean no-op. Per-op guards mean partial-state migrations recover cleanly (e.g., if A11 has a hand-edit, it's preserved with a warning).

### Regression test

14 untouched sheets differ ONLY on AZ4; Cover diffs limited to {AZ4, B8, A11, B11}; Dashboard diffs limited to {AZ4, K10, K11, K13}. No collateral damage to existing tile layout, charts, or named ranges.

### Files

- `tools/migration/migrate_to_v0211.py` (new) — Dashboard tile + Cover AR line + version stamp.
- Bundled `ALF_Financial_Analyzer_Only.xlsx` forward-rolled v0.2.10 → v0.2.11.
- `app.py`: `ANALYZER_SUBSTRATE_VERSION` bumped "0.2.4" → "0.2.11" (was stale — missed when v0.2.10 shipped earlier in the same session; corrected now alongside v0.2.11). `ANALYZER_LAST_UPDATED` → "2026-05-23".

---

## [Substrate template v0.2.10] — 2026-05-23

### Summary

**Opens UW-BACKLOG BL-0023** (AR & Collections module). Substrate-side component of a multi-piece initiative that also ships `ar_normalizer.py` / `ar_writer.py` / Streamlit upload wiring as code (see the commits for the Track 1-shaped pieces). v0.2.10 introduces a new analytical sheet at the workbook's substrate level and extends Workbook Health with AR-conditional logic.

### What changed (migrate_to_v0210.py)

- **A. New "AR & Collections" sheet at index 8** (between Monthly Trending and UW Output), HIDDEN by default. 163 cells across 5 sections:
  - §1 Aging Summary (rows 7-18) — bucket totals (0-30 / 31-60 / 61-90 / 91-120 / 120+), Total AR at C15, 90+ subtotal at C17, % aged 90+ at C18.
  - §2 Key Ratios / KPIs (rows 20-26) — DSO, AR÷monthly EGI, %aged 90+, Collection effectiveness, Avg balance per occupied bed. Cross-sheet pins: `Monthly Trending!N26` (annualized EGI), `T12 Analytics!E7` (avg occupied beds).
  - §3 By-Payer Mix (rows 28-37) — 7 payer rows matching mappings.py normalization targets (Private Pay / Medicaid / Medicare / Managed Care / VA Benefit / LTC Insurance / Self-Pay + Other), with concentration flag.
  - §4 Roll-Forward & Bad-Debt Reconciliation (rows 40-57) — period roll formula, T-12 bad debt cross-check at row 53 (refs `T12 Analytics!E98`), variance flag at row 56 (⚪/✓/⚠), implied reserve change at row 57.
  - §5 Flags & Exceptions (rows 60-66) — resident-in-90+-with-concession, vacant-with-AR, payer concentration, sum-check mismatch, period-date mismatch.
  - `Z1` = AR presence flag (0=no data, 1=populated by ar_writer.py). Pivot enabling Workbook Health B43 + P5 conditional behavior below.

- **B. Workbook Health!B43 wrapped in IF guard:**
  ```
  =IF('AR & Collections'!Z1=1, 'AR & Collections'!C15, SUM('Rent Roll Input'!$X$7:$X$606))
  ```
  RR-derived fallback (the existing pre-AR formula) preserved bit-for-bit when Z1=0, so non-AR analyses see no surface change.

- **C. P5 gate at Workbook Health row 52** ("AR period matches RR period — inert if no AR"). Formula compares AR sheet's C3 as-of date to `RR_Period_Date`; defaults to "✓" when Z1=0 so non-AR runs don't fail READY-FOR-EXPORT. The READY-FOR-EXPORT summary at row 52 moved to row 53 with B52 ANDed into its formula. Verified no external references to `Workbook Health!B52` before the shift.

- **D. Cover!B8 stamped v0.2.10 + AZ4 on all 16 sheets** (anchor list grows 15 → 16 because AR & Collections joins).

### Idempotency

Gate checks Cover!B8 == "v0.2.10" AND AR & Collections at index 8. 19-check verify, regression-clean against bundled (untouched sheets only differ on AZ4 + Cover!B8).

### Files

- `tools/migration/migrate_to_v0210.py` (new) — sheet build + Workbook Health rewrites + version stamp.
- Bundled `ALF_Financial_Analyzer_Only.xlsx` forward-applied v0.2.4 → v0.2.10 directly (per BL-0021 carry-forward; bundled still lacks v0.2.5-v0.2.9 substrate features).
- `mappings.py` (Track 1 shared infra) — extended `DEFAULT_PAYER` with Managed Care + Medicare-Advantage / MCO rules; `PAYER_FALLBACK` unchanged (RR behavior preserved). AR ingest constructs `MappingSet(payer_fallback="Self-Pay + Other")` per-instance.

---

## [Substrate template v0.2.9] — 2026-05-21

### Summary

**Closes UW-BACKLOG BL-0020** (Dashboard chart-data-link bug fixes) as a proper forward-rolling migration, AND resolves a `v0.2.8` version-number collision.

BL-0020's three chart fixes were originally a `migrate_to_v028.py` on branch `claude/bl-0020-dashboard-data-link-fixes` (PR #34), but that PR was **closed unmerged** when the user wholesale-replaced the bundled Analyzer (BL-0021). The fixes ended up present only in the bundled file, not in any migration on `main` — and the `v0.2.8` number got re-used on `main` for BL-0022 (`Cover!B5` resolver). Net effect: anyone forward-rolling a workbook through the chain got a Dashboard with **broken charts**, because `migrate_to_v027.py` inserts the buggy Dashboard from `v027_assets/dashboard_template.xlsx` and nothing downstream fixed it. This migration restores chain reproducibility and disambiguates the version numbers (BL-0020 → v0.2.9, BL-0022 stays v0.2.8).

### What changed (migrate_to_v029.py)

Surgical cell + chart patch on the Dashboard sheet — **no template asset, no sheet add/remove, no row inserts.**

#### Fix 1 — "Monthly EGI Trend" line chart plotted Housekeeping Income

`Dashboard!C97:C108` (feeds chart [3]) referenced `Monthly Trending!B21:M21`. Row 21 = Housekeeping Income since v0.1.7 / BL-0001 moved EGI to row 26. Rewrote all 12 cells to row 26.

#### Fix 2 — "Payer Mix — Revenue Share" pie plotted unit counts

`Dashboard!F90:F93` (feeds chart [4]) referenced `Rent Roll Recon!B40:B43` (COUNTIFS unit counts). The chart title says Revenue Share, so the source should be col I (`H/H47` revenue ratios). Replaced `!B{row}` → `!I{row}` in all 4 cells (both occurrences per cell).

#### Fix 3 — Doughnut chart [1] rendered 5 empty slices

The doughnut series spanned `Dashboard!$O$8:$O$19` (12 rows) but payer labels sat at `O8` + `O14:O19` with a 5-row gap (`O9:O13` empty) → Excel drew 5 empty slices. Fix: move the `O14:O19` payer rows (Medicaid / LTC Insurance / VA / Managed Care / Self-Pay / Other) up to `O9:O14` (contiguous with the `O8` Private Pay row), clear `O15:O19`, and shrink the chart series range to `$O$8:$O$14` (cat) / `$P$8:$P$14` (val) with rebuilt 7-point caches.

Charts [3] (EGI) and [4] (Payer Mix) auto-pick-up corrected values because only the underlying C/F cell formulas changed, not those charts' own ranges. Only chart [1] (doughnut) needed a range mutation.

### Idempotency

Gate on `Cover!B8 == "v0.2.9"`. The C97:C108 / F90:F93 rewrites are self-idempotent. The doughnut data-move is the only non-idempotent op, so it is **guarded** — it fires only when the Dashboard is in the buggy state (`O9` empty AND `O14 == "Medicaid"`). Verified: running v0.2.9 directly on an already-fixed Dashboard (the user's bundled copy) skips the move and does NOT corrupt the layout.

### Chain test

Full chain `v0.2.4 (bundled) → v0.2.5 → v0.2.6 → v0.2.7 → v0.2.8 → v0.2.9` verified: at v0.2.7 the Dashboard gets the buggy v027-asset charts; v0.2.9 corrects all three. End state confirmed — C97:C108 = row 26, F90:F93 = col I, doughnut O8:O14 contiguous with 7-point cache, plus all v0.2.5 (M6) / v0.2.6 (AH4 fill) / v0.2.8 (Cover!B5 resolver) work intact.

### The v0.2.8 collision (now resolved)

There were briefly two `migrate_to_v028.py` files both stamping v0.2.8: BL-0022's (Cover!B5, merged to `main`) and BL-0020's (Dashboard charts, on the closed PR #34 branch). With BL-0020 now shipping as **v0.2.9**, the collision is gone. The closed branch's `migrate_to_v028.py` is **superseded** — do not revive it; use `migrate_to_v029.py` instead.

### Files

- `tools/migration/migrate_to_v029.py` (new) — surgical chart-link patch, 6-check verification block.
- Bundled `ALF_Financial_Analyzer_Only.xlsx` **not bumped** (stays at the v0.2.4 user-managed copy per BL-0021). The user's bundled Dashboard already has these fixes; v0.2.9 exists so the *migration chain* reproduces them.

---

## [Substrate template v0.2.8] — 2026-05-20

### Summary

**Closes UW-BACKLOG BL-0022.** Track 3 narrow-scope fix: `Cover!B5` (the `Property_Name` named-range source) was a static manual-entry cell while the RR v1.15.0 + T12 v0.2.1 writers had been auto-stamping the property name into `Rent Roll Input!A3` / `T12 Input!A10` since 2026-05-11. `T12 Analytics!B2`'s 3-priority resolver (RR → T12 → `Property_Name`) picked up the name correctly via path 1, but Cover itself stayed blank — and with it `Dashboard!B2`'s title formula (which references `Cover!B5` directly), `UW Export!B3` (`=IFERROR(Property_Name,"(not set)")`), `Workbook Health!B27`, and Pre-Export Gate `B49` all reported "missing" / "(not set)" / empty despite the writer-stamped inputs being present.

v0.2.8 rewrites `Cover!B5` to a 2-priority resolver formula (RR → T12 → "") — no fallback to `Property_Name` since that would be circular (`Property_Name → Cover!B5`). Cover now auto-populates whenever either writer has stamped its input; all 5 downstream consumers cascade automatically.

Pure substrate change. No row inserts, no existing-formula edits on any other sheet, no named-range additions, no sheet additions. Migration is 4 ops, idempotent on the version stamp, with defensive preservation of any user-typed text already in `Cover!B5`.

### What changed (migrate_to_v028.py)

- **A. Rewrite `Cover!B5`** with a 2-priority property-name resolver:
  ```
  =IFERROR(
    IF(LEN(TRIM('Rent Roll Input'!A3))>0,'Rent Roll Input'!A3,
    IF(LEN(TRIM('T12 Input'!A10))>0,'T12 Input'!A10,
    "")),
    "")
  ```
  Same priority-1/priority-2 chain that `T12 Analytics!B2` uses, minus the priority-3 `Property_Name` fallback. When neither writer-stamped source has a value, B5 evaluates to "" — consistent with the prior "blank when no data" semantics.

  **Defensive skip:** if `Cover!B5` already contains a static (non-formula) string at migration time, the rewrite is skipped and the user's typed value is preserved. This handles the case where someone has manually set the property name and doesn't want it auto-overwritten.

- **B. Rewrite `Cover!A19` docstring.** Old text: "Property name entered at B5 above propagates to T12 Analytics via the Property_Name named range." (manual-entry framing — now inaccurate). New text: "Property name at B5 auto-resolves from Rent Roll Input!A3 → T12 Input!A10 (writer-stamped). Type into B5 to manually override. Propagates to all consumers via the Property_Name named range." Preserves user customization if A19 has been hand-edited away from the standard docstring lineage.

- **C + D. Stamp** `Cover!B8` → `v0.2.8` and all 15 anchor `AZ4` cells.

### Consumer impact

`Cover!B5` is referenced by 7 cells across 5 sheets. Behavior after v0.2.8:

| Consumer | Before | After |
|---|---|---|
| `Cover!B5` (the cell itself, rendered on the Cover tab) | Blank (manual entry) | Property name auto-resolved from writer inputs |
| `Dashboard!B2` title formula | Renders "UNDERWRITING DASHBOARD" with no property name | Renders "UNDERWRITING DASHBOARD  —  \<PropertyName\>" |
| `T12 Analytics!B2` (3-priority, falls back to `Property_Name`) | Already resolved via path 1 (RR!A3) | Unchanged — path 1 still wins; if RR + T12 ever both empty, B5 is now the same formula |
| `UW Export!B3` `=IFERROR(Property_Name,"(not set)")` | "(not set)" | Property name |
| `Workbook Health!B27` workbook map property name row | "missing" | Property name |
| `Workbook Health!C27` ✓/⚠ status | ⚠ | ✓ |
| `Workbook Health!B49` Pre-Export Gate property-name check | ⚠ "Set property name on Cover!B5" | ✓ |

The B49 warning message ("Set property name on Cover!B5") is unchanged — still semantically accurate as a fallback path (typing into B5 still overrides the formula on subsequent re-saves).

### Idempotency

Gate (`is_already_v028()`) checks `Cover!B8 == "v0.2.8"`. Re-running on a v0.2.8 file is a no-op (just re-saves). If a user manually types text into `Cover!B5` after v0.2.8 ships, that text is preserved on subsequent re-runs because the formula-injection step's `looks_like_user_text` guard sees non-formula static text and skips.

### Verification (10 checks)

`Cover!B8 == "v0.2.8"`; all 15 anchor `AZ4` cells = `v0.2.8`; `Cover!B5` either has the new formula OR is user-typed static text (both valid post-states); `Cover!A19` docstring updated or user-customized; sanity checks that M5 (R169) + M6 (R178) on Rent Roll Recon from v0.2.5 are intact; `T12 Analytics!B2` 3-priority formula intact (we deliberately do NOT modify the T12 Analytics resolver — Cover!B5 changes naturally cascade through); Dashboard sheet still at sheetnames index 1 from v0.2.7.

### Chain-test result (bundled v0.2.4 → v0.2.8)

The bundled `ALF_Financial_Analyzer_Only.xlsx` was reset to v0.2.4 in BL-0021 (2026-05-19). Chain-running `migrate_to_v025` → `v026` → `v027` → `v028` against a fresh copy of the bundled file lands cleanly at v0.2.8 with all verification checks green at every step. No regressions to v0.2.5 (Section M6), v0.2.6 (BL-0016 AH4 fill / BL-0017 144-cell intentional-blank), or v0.2.7 (Dashboard sheet + AZ anchors).

### Bundled Analyzer stays at v0.2.4

Per the BL-0021 (2026-05-19) directive — "Future substrate work either accepts the v0.2.4 regressions or runs the migration chain forward first" — this PR does **not** bump the bundled `ALF_Financial_Analyzer_Only.xlsx`. The migration script is the deliverable; the bundled file remains at the user's hand-edited v0.2.4 baseline. Users who want the v0.2.8 behavior run the chain `v025 → v026 → v027 → v028` on their own workbook.

### Files

- `tools/migration/migrate_to_v028.py` (new, ~195 lines, 4 ops / 10-check verify / idempotent)
- `SPEC-T12.md` (current substrate version bumped, v0.2.8 entry added to history)
- `CHANGELOG-T12.md` (this file)
- `CLAUDE.md` (last-updated + Current substrate version bumped)
- `UW-BACKLOG.md` (BL-0022 closed entry)

### Cross-track note

Track 3 (workbook + migration code only) — no Track 1 / Track 2 code changed. User-authorized for this chat (2026-05-20).

---

## [Bundled Analyzer reset to user-authored copy] — 2026-05-19

> **Not a substrate version bump.** This is a user-directed wholesale replacement of the bundled `ALF_Financial_Analyzer_Only.xlsx`. The substrate migration chain (v0.1.0 → v0.2.7, plus the closed-unmerged v0.2.8 on branch `claude/bl-0020-dashboard-data-link-fixes`) is preserved in `tools/migration/` for reproducibility, but the bundled file no longer represents the output of running that chain.

### Summary

**Closes UW-BACKLOG BL-0021** (regression by user request). Replaces the v0.2.7 bundled Analyzer with the user's locally-edited copy from `C:\One Drive Business\OneDrive - (na)\office\rent_roll_app\ALF_Financial_Analyzer_Only.xlsx`. Adds a "Last updated: 2026-05-19" stamp at `Dashboard!N1` per user request to surface the bundled file's modification date in the workbook itself.

The user prefers their hand-edited Excel copy as canon over the migration-chain-derived bundled file. v0.2.7 (BL-0018) shipped the Dashboard structure successfully but inherited three chart-data-link bugs from the user's source file; v0.2.8 (BL-0020, closed unmerged) tried to fix those bugs on top of v0.2.7. After v0.2.8, user decided they'd rather have their own file as the bundled default than have the repo apply targeted patches.

### What the bundled file is now

- **Substrate stamp:** `Cover!B8 = "v0.2.4"` (from the user's local file, NOT a new version). The migration scripts v0.2.5 / v0.2.6 / v0.2.7 / v0.2.8 are still in `tools/migration/` and can be re-applied if the user later wants to forward-roll the bundled file.
- **Sheet count:** 15.
- **Sheet list:** Cover, Dashboard (with user's chart-data-link fixes intact — `Dashboard!C97:C108` references EGI row 26, `Dashboard!F90:F93` references revenue ratios at col I, doughnut chart range $O$8:$O$14 with contiguous data at O9:O13), T12 Analytics, T12 Input, T12 Raw Data, Rent Roll Input, Rent Roll Recon, Monthly Trending, UW Output, UW Export, Mapping Review, Description_Map, RR_Calc, T12_Calc, Workbook Health.
- **New cell:** `Dashboard!N1` = `"Last updated: 2026-05-19"` (Calibri 10pt italic gray FF595959, right-aligned). Static text, not a TODAY() formula — the intent is to surface the file's edit date, not always show "today."

### What is NOT in the bundled file anymore (vs the v0.2.7 main HEAD)

The user's local file was based on the v0.2.4 substrate baseline before any of v0.2.5 / v0.2.6 / v0.2.7's work was applied to it. Wholesale-copying that file undoes:

- **BL-0012 (v0.2.5)** — Section M6 negative-residual reconciliation rows (`Rent Roll Recon!A178:B183`). The bundled file no longer has the Misc/Diabetes credit reconciliation against T12 Concessions.
- **BL-0016 (v0.2.6)** — `Rent Roll Input!AH4` green `FF1F6B52` fill. The "Total Ancillary $" header is once again rendered as white-bold on transparent fill (invisible).
- **BL-0017 (v0.2.6)** — 144-cell "intentionally blank" treatment. T12 Analytics E36/G36, Rent Roll Recon D109, and UW Output cols B/C/D × selected rows all revert from em-dash + light gray fill back to the literal `"-"` text payload (renders with visible quote marks).
- **BL-0008 (RR v1.17.1) substrate side** — `RR_Calc` MINIFS / MAXIFS formulas have `_xludf.` prefix re-introduced (Google Sheets / LibreOffice round-trip artifact). Works in those tools, may misrender in some Excel versions.
- **v0.2.7 structural** — `Dashboard!AZ1:AZ5` anchor block is absent (user's local Dashboard lacks the substrate anchor convention). Workbook Health Pivot table refs against `T12 Analytics!AZ1:AZ5` will read empty since the user's file relocated those anchors to `AM1:AM5` (intentional or accidental drift).

### How to forward-roll the bundled file again (if needed)

The migration chain still works against the bundled file (which is at v0.2.4):

```
python tools/migration/migrate_to_v025.py ALF_Financial_Analyzer_Only.xlsx ALF_Financial_Analyzer_Only.xlsx
python tools/migration/migrate_to_v026.py ALF_Financial_Analyzer_Only.xlsx ALF_Financial_Analyzer_Only.xlsx
python tools/migration/migrate_to_v027.py ALF_Financial_Analyzer_Only.xlsx ALF_Financial_Analyzer_Only.xlsx
python tools/migration/migrate_to_v028.py ALF_Financial_Analyzer_Only.xlsx ALF_Financial_Analyzer_Only.xlsx  # closed PR but script exists on branch
```

WARNING: this would override the user's Dashboard customizations (v0.2.7's `migrate_to_v027.py` removes any existing Dashboard sheet before inserting its own). Re-running v0.2.7 would lose the user's chart-data-link fixes; v0.2.8 was specifically built to ADD those fixes on top of v0.2.7's structural changes. So forward-rolling needs the v0.2.8 step.

---

## [Substrate template v0.2.7] — 2026-05-19

### Summary

**Closes UW-BACKLOG BL-0018** — Dashboard sheet redesign. Replaces the v0.2.4 "Investment Dashboard" with a denser, chart-rich "Dashboard" sheet authored externally by the user in Excel. Sheet count stays at 15; the new Dashboard slots into the same index 1 position immediately after Cover.

Track 3 / Substrate only — no RR or T12 code changes, no formula changes on any other sheet, no row inserts, no named-range changes.

### What changed (migrate_to_v027.py)

#### A. Remove `Investment Dashboard` sheet

The v0.2.4 Investment Dashboard (340 cells, no embedded charts, 52-column layout) is fully superseded by the new Dashboard. Removed via `del wb["Investment Dashboard"]`.

#### B. Insert new `Dashboard` sheet at index 1

437 styled cells, 6 native Excel charts (BarChart × 2, DoughnutChart, plus 3 more titled charts), 72 merged ranges, 17-column visible layout (B:Q with anchor block at AZ), navy tab color `FF1F4E79`.

Sourced from a committed template asset at `tools/migration/v027_assets/dashboard_template.xlsx` (26 KB, single-sheet workbook trimmed from the user's authored copy). Cells copied via the established `_copy_cell` helper (preserves font/fill/border/alignment/number_format/protection); charts copied via `copy.deepcopy(chart)` since openpyxl Chart objects carry their data-series references as string formulas that survive the deep-copy.

**96 unique cross-sheet refs**:

| Source sheet | Refs | Populated on v0.2.6 |
| --- | --- | --- |
| T12 Analytics | 52 | 52 |
| Rent Roll Recon | 31 | 31 |
| Monthly Trending | 12 | 12 |
| Cover | 1 (B5) | 0 (user-populated at runtime via `Property_Name` named range) |

No reference to the (now-removed) Investment Dashboard. No new named ranges required.

#### C. AZ1:AZ5 anchor block on new sheet

| Cell | Value |
| --- | --- |
| AZ1 | `Underwriting at-a-glance KPI dashboard with embedded charts` |
| AZ2 | `Analytical (handoff)` |
| AZ3 | `visible` |
| AZ4 | `v0.2.7` |
| AZ5 | `All value cells are formula references into T12 Analytics, Rent Roll Recon, Monthly Trending, and Cover. 6 native Excel charts embedded. No source-of-truth data lives here. Supersedes the v0.2.4-v0.2.6 Investment Dashboard.` |

#### D. Substrate version stamp

`Cover!B8` and all 15 `AZ4` anchors bumped `v0.2.6` → `v0.2.7`. 15-sheet anchor list updated: `"Investment Dashboard"` slot now reads `"Dashboard"`. All other anchor positions unchanged.

### Idempotency

Gate checks ALL FOUR:
1. `Cover!B8 == "v0.2.7"`
2. `"Dashboard"` is in `wb.sheetnames`
3. `wb.sheetnames.index("Dashboard") == 1` (immediately after Cover)
4. `"Investment Dashboard"` is NOT in `wb.sheetnames`

Re-running on already-migrated workbook is a no-op (`wb.save()` with no mutations). Partial pre-state (e.g. Dashboard inserted but Investment Dashboard not yet removed) is handled by per-step `has_X / has_Y` guards.

### Files

- `tools/migration/migrate_to_v027.py` (new) — 14-check verification block.
- `tools/migration/v027_assets/dashboard_template.xlsx` (new, 26 KB) — single-sheet workbook with the Dashboard sheet captured from the user's Excel-authored copy.
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer re-stamped to v0.2.7 (sheet count 15 → 15, Investment Dashboard → Dashboard).

### Out of scope

- The user's authored file was based on v0.2.4 and had been round-tripped through Google Sheets / LibreOffice, which re-introduced `_xludf.MINIFS` / `minifs` lowercase prefixes on `RR_Calc` and `Rent Roll Recon`, missed the v0.2.5 Section M6 rows, missed the v0.2.6 BL-0016 AH4 fill, missed the v0.2.6 BL-0017 144-cell intentional-blank styling, and accidentally relocated T12 Analytics AZ-column anchors to the AM column. **None of those regressions were carried forward** — the migration starts from the current v0.2.6 base and only adds the Dashboard. v0.2.5 + v0.2.6 substrate work confirmed intact post-migration (Rent Roll Recon!A178-A183 = Section M6 conditional rows; Rent Roll Input!AH4 fill = `FF1F6B52`; 5 spot-checked BL-0017 cells = em-dash + `FFF2F2F2` fill + `FFA0A0A0` font color).
- "Investment Dashboard" name retained in this changelog and prior CHANGELOG entries (records of what shipped at past versions).

---

## [Substrate template v0.2.6] — 2026-05-18

### Summary

**Closes UW-BACKLOG BL-0016 + BL-0017** — both originally deferred to manual Excel handling on 2026-05-16. User re-confirmed on 2026-05-18 to ship via substrate migration after all. The abandoned v0.2.4 implementation at commit `fac129d` on branch `claude/serene-panini-3ad41d` was ported forward and re-numbered to chain after v0.2.5 / BL-0012.

Two coordinated Track 3 fixes on visual conventions — no formula changes, no row inserts, no named-range additions.

### What changed (migrate_to_v026.py)

#### A. BL-0016 — `Rent Roll Input!AH4` header fill

The AH "Total Ancillary $" header was added in substrate v0.2.2 with correct white-bold font but `fill_type=None` (transparent). White-on-default renders as a blank cell — the column header was invisible. v0.2.6 applies the green `FF1F6B52` `PatternFill` matching `T4` / `U4` (the substrate's computed-column header palette; navy `FF1F3864` is for input columns).

One-cell change. Header text + font preserved unchanged.

#### B. BL-0017 — Workbook-wide "intentionally blank" visual convention

144 cells across 3 sheets currently store the literal 3-character string `"-"` (a double-quote, dash, double-quote payload — renders in Excel with visible quote marks). All 144 share the same "intentionally blank, not just missing data" design intent. v0.2.6 applies the user-approved gray-with-em-dash treatment:

| Attribute | Treatment |
| --- | --- |
| Value | `"—"` (em-dash, plain text — no quote chars) |
| Fill | `PatternFill(start_color="FFF2F2F2", solid)` — light gray |
| Font color | `FFA0A0A0` — medium gray (preserves size/bold/italic/name/underline/strike) |
| Horizontal alignment | `center` (preserves vertical/wrap/indent/shrink/rotation) |

**New user-facing rule:** *gray + em-dash = "blank by design"; truly empty = "data not yet populated".*

**Target cell inventory (144 total):**

| Sheet | Cells | Count |
| --- | --- | --- |
| T12 Analytics | E36, G36 | 2 |
| Rent Roll Recon | D109 (MC "Other / unmapped" Avg Care Level) | 1 |
| UW Output | cols B/C/D × rows {8-12, 22-28, 30-36, 38-56, 58-60, 62-64, 66-68} | 141 |

UW Output rows enumerated as: 5 (Other-revenue+EGI) + 7 (OpEx S1) + 7 (OpEx S2) + 19 (OpEx detail) + 3 (Total OpEx+NOI) + 3 (Capex) + 3 (Below-the-line) = 47 rows × 3 cols = 141.

**Out of scope (intentionally deferred):** formula-conditional blanks like `T12 Analytics!E37/G37/H38` that return `""` only when source data is missing. Those are "blank when data isn't here" — permanent styling would mislead when they populate. Excel `DifferentialStyle` conditional formatting prototyped on 2026-05-16 but never shipped; defer to a future v0.2.7+ if a clean approach surfaces.

### Idempotency

Gate checks BOTH:
1. `Cover!B8 == "v0.2.6"`,
2. `Rent Roll Input!AH4` fill is the green `FF1F6B52`,
3. `UW Output!B8` already has the styled-blank treatment.

Per-cell idempotency on the blank-styling pass: each cell tested via `_is_already_styled()` (em-dash value AND gray fill); already-styled cells are skipped, not re-applied. Partial pre-state (e.g. some cells styled, some not) is gracefully re-converged on rerun.

### Verification

10/10 checks pass on the bundled Analyzer:

```
  1. Cover!B8 = 'v0.2.6'                                              : True
  2. All 15 AZ4 = v0.2.6                                              : True (15 sheets)
  3. AH4 fill = 'FF1F6B52' (target 'FF1F6B52')                        : True
  4. AH4 text 'Total\nAncillary $' preserved                          : True
  5. AH4 font bold preserved                                          : True
  6. All 144 blank-targets styled (144/144)                           : True
  7. Sample (T12 Analytics E36):
       value='—' (target '—')
       fill='FFF2F2F2' (target 'FFF2F2F2')
       font color='FFA0A0A0' (target 'FFA0A0A0')
       align horizontal='center' (target 'center')
```

### Files changed

- `tools/migration/migrate_to_v026.py` — new idempotent migration script (~300 lines, ported from the abandoned `claude/serene-panini-3ad41d` commit `fac129d`)
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.2.6
- `CHANGELOG-T12.md` — this entry
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — bundled-substrate version stamp
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — Last updated line + current substrate version
- `UW-BACKLOG.md` — BL-0016 + BL-0017 moved Pending → Shipped

### Out of scope (carry-forwards opened)

None. **UW-BACKLOG is now empty** for the second time (first was 2026-05-14 after BL-0001 closed — that emptiness lasted ~4 hours before BL-0011..BL-0014 got teed up).

---

## [Substrate template v0.2.5] — 2026-05-16

### Summary

**UW-BACKLOG BL-0012 closed — Section M Misc/Diabetes credit reconciliation against T12 `Concessions & specials`.** Pure substrate addition: new Section M6 on `Rent Roll Recon` (rows 178-183) that catches **negative** residuals on the M5 "Misc. Income" bucket and reconciles them against the T12 `Concessions & specials` Label. M5 already handles positive residuals; M6 fires only on the negative branch (`B173 < 0`) so the two sections are non-overlapping.

### Why

Surfaced in CHANGELOG-RR.md v1.17.0 (BL-0003) "Side observation worth tracking": Homestead's residual `Other LOC $` post-split is **-$12,146.75** (Diabetes + Misc, both partially negative — net credit). The hypothesis was that operators sometimes route discount/credit postings through the Other LOC bucket instead of the formal `Concessions` GL. Section M5 currently treats negative residuals the same as positive, so it surfaces a misleading "✓ Misc. income share within band" note when the bucket is actually a net credit.

The original BL ticket gated this on "observing the same negative-residual pattern in one more deal." Ungated per user direction to close out the remaining backlog item.

### What changed (migrate_to_v025.py)

Section M6 layout on `Rent Roll Recon`:

```
R178:  M6  —  Negative residual check  (Misc. credits vs T12 Concessions & specials)
                                                           [merged A178:G178, navy header style]
R179:  Residual from M5 (annual)                | =B173
R180:  T12 'Concessions & specials' — annual    | =IFERROR(VLOOKUP("Concessions & specials",
                                                          'T12 Raw Data'!$B:$R, 17, 0), 0)
R181:  Residual / T12 Concessions (abs)         | =IFERROR(ABS(B179)/ABS(B180), 0)
R183:  (merged A183:I183) conditional note — 4 branches:
         IF B179 >= 0:                                "" (positive — M5's domain)
         ELIF B180 == 0:                              ⚠ "Negative residual = $X in Other LOC bucket,
                                                          but T12 has no Concessions & specials line
                                                          for reconciliation. Verify GL routing."
         ELIF ABS(B179)/ABS(B180) > 10%:              ⚠ "Negative residual = $X is N.N% of T12
                                                          Concessions ($Y). Likely misposted
                                                          concessions — review GL routing for
                                                          Other LOC credits."
         ELSE:                                        ✓ "Negative residual = $X within reconciliation
                                                          tolerance (≤10% of T12 Concessions $Y)."
```

Threshold: **10%** of `|T12 Concessions & specials|`. Hard-coded — easy to surface to a tunable cell in a future v0.2.6+ if multiple deals show the residual-to-concessions ratio varying meaningfully.

Styling mirrors the existing M5 block (R169 header, R170 data row, R176 conditional note) — same fonts, fills, alignment, number formats. M6 sits in the previously-empty rows 178+ (max_row was 199 pre-migration; no shift required).

### Idempotency

Gate checks both `Cover!B8 == "v0.2.5"` AND `Rent Roll Recon!A178` starts with `"M6"`. Re-run on already-migrated workbook is a no-op.

### Verification

9/9 verification checks pass on the bundled Analyzer:

```
  1. Cover!B8 = 'v0.2.5'                                              : True
  2. All 15 AZ4 = v0.2.5                                              : True (15 sheets)
  3. M6 header at R178 starts with 'M6'                               : True
  4. R179 B references B173 (M5 residual)                             : True
  5. R180 B = VLOOKUP('Concessions & specials', ...)                  : True
  6. R181 B = ABS(B179)/ABS(B180) ratio                               : True
  7. R183 conditional note (4 branches)                               : True
  8. R183 merged A:I                                                  : True
  9. R178 merged A:G                                                  : True
```

### Out of scope (carry-forwards opened)

None. The Section M6 surface is self-contained and fires off existing M5 + T12 Raw Data inputs.

### Files changed

- `tools/migration/migrate_to_v025.py` — new idempotent migration script (~270 lines)
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.2.5
- `CHANGELOG-T12.md` — this entry
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — bundled-substrate version stamp
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — Last updated line
- `UW-BACKLOG.md` — BL-0012 moved Pending → Shipped

---

## [Substrate template v0.2.4] — 2026-05-16

### Summary

Track 3 additive: new top-of-workbook **`Investment Dashboard`** sheet inserted at index 1, immediately after `Cover`. Pure formula-reference layer over `T12 Analytics` and `Rent Roll Recon` — every value cell is either a static label or a cross-sheet formula reference into one of those two sheets. No source-of-truth data lives on the dashboard; **no existing formula on any other sheet changes**; no row inserts; no named-range additions. Sheet count goes 14 → 15.

Why this matters: the existing analytical sheets (`T12 Analytics`, `Rent Roll Recon`, `UW Output`) are dense reference grids — useful for an analyst working line-by-line, but slow to scan when you just want to know "is this deal interesting?" The Investment Dashboard collapses the headline numbers an underwriter wants at first contact (occupancy, EGI, EBITDARM margin, going-in cap, price-per-bed, payer mix, acuity, key risk flags) onto a single sheet at the front of the workbook. Because it lives at index 1, it's also what a recipient sees when they open a populated Analyzer for the first time.

Sourced from the Beaufort Rent Roll 1.31.26 + Beaufort T-12 1.31.26 populated Analyzer (in `Sample Files/`, gitignored). Only the dashboard sheet was extracted into the migration's template asset — the rest of that workbook is property-specific data and does not enter the repo.

### What changed (migrate_to_v024.py)

- **A. Insert `Investment Dashboard` worksheet at index 1** (immediately after `Cover`). Copied cell-by-cell from `tools/migration/v024_assets/investment_dashboard_template.xlsx` — 335 styled cells preserving fonts / fills / borders / alignment / number formats / protections, 7 column widths (A=2 narrow gutter; B=29 label; C-E ~16 each for IL/AL/MC; G/H ~16-22 for total + status), 9 row heights (R2=24 title, R8=26 headline tile, section banners at R11/19/30/48/59/70/85 = 16). No merged cells, no charts, no conditional formatting, no data validations on the dashboard itself.
- **B. Stamp AZ1:AZ5 anchor metadata** on `Investment Dashboard` per Workbook Health convention:
  - `AZ1` = "Investment-grade KPI roll-up of T12 Analytics + Rent Roll Recon" (purpose)
  - `AZ2` = "Analytical (handoff)" (category)
  - `AZ3` = "visible" (visibility)
  - `AZ4` = `v0.2.4` (version)
  - `AZ5` = "All cells are formula references into T12 Analytics and Rent Roll Recon. No source-of-truth data lives here." (notes)
- **C. Stamp** `Cover!B8` → `v0.2.4` and all **15 anchor `AZ4` cells** (was 14 through v0.2.3 — Investment Dashboard joins the anchor list).

### Sheet contents — seven sections

| Section | Rows | What it surfaces | Source |
|---|---|---|---|
| AT-A-GLANCE T12 ACTUAL | 6-9 | Headline tiles: Licensed Beds · Physical Occupancy · EGI · EBITDARM Margin · Going-In Cap · Price/Bed. Each with a sub-label (target gap, normalized sibling, stabilized cap, etc.) | `T12 Analytics!E6/E8/E52/E162/E118/E123` + sub-cells |
| 1 · OCCUPANCY & CAPACITY | 11-17 | IL/AL/MC/Total grid: licensed beds, avg occupied, occupancy %, vacant, beds-to-fill-to-stabilization. Status column: `=IF(F15>=G15,"✓ At target",IF(F15>=G15-0.1,"⚠ Below","✗ Distressed"))` | `T12 Analytics!B6:E11` + `Rent Roll Recon!B9:E9` |
| 2 · REVENUE & RATE PERFORMANCE | 19-28 | ADR / RevPOR / RevPAB / LOC% / Base rent / LOC rev / EGI by IL/AL/MC + Blended + Normalized + Delta. RR-vs-T12 base rent gap (annualized %) | `T12 Analytics!E141:E146/E16/E23/E52` + `Rent Roll Recon!E19:E20` |
| 3 · MARGIN & COST STRUCTURE | 30-46 | Total OpEx + 8 cost-ratio rows with benchmark column (labor 55-65%, agency ≤3%, OT ≤5%, food 6-9%, food PPD $8-14, P&C 4-7%, bad debt ≤2%, mgmt 5-7%) + EBITDARM/EBITDAR $/% T12-vs-normalized | `T12 Analytics!E105/E148:E160/E108/F108/E110/F110/E162/F162/E164/F164` |
| 4 · VALUATION & ACQUISITION | 48-57 | Purchase price / going-in caps (EBITDARM, EBITDAR post-mgmt) / price-per-bed splits (AL, MC) / gross revenue multiple / EBITDARM multiple. Cap-rate expansion shown as `=D51-C51` formatted "+X.XX%" | `T12 Analytics!E117/E118/E120/E123:E125/E127/E128` |
| 5 · PAYER MIX | 59-68 | 7-row × 4-col grid: Private Pay / Medicaid / LTC Insurance / VA / Managed Care / Self-Pay / Other × Residents / % Mix / Monthly Rev / % Revenue. Total row sums | `Rent Roll Recon!B40:I46` |
| 6 · AL CARE LEVEL DISTRIBUTION | 70-81 | Basic + L2-L7 × Residents / % Occupied / Total $/mo / Avg $/Res / % LOC Rev. Total row sums | `Rent Roll Recon!B59:G65` |
| 7 · KEY RISKS & NORMALIZATION CALLOUTS | 85-94 | 7 risk flags with 🔴🟠🟢 marker, observation, linked metric value, UW impact narrative. Example: "🔴 Going-in EBITDARM cap is negative on T12 actuals → Deal underwrites only on stabilization" | mostly `T12 Analytics` + a few `Rent Roll Recon` cross-refs |

### Why a template asset rather than programmatic construction

The dashboard has 335 styled cells with bold section banners, banded section-header backgrounds, borders, indents, percent / currency / general number formats, and conditional emoji glyphs in formulas. Encoding all of that as Python `Font` / `Fill` / `Border` / `Alignment` / number-format objects would balloon the migration script by an order of magnitude and make every future styling tweak require a Python diff. Instead, the source sheet is captured once into a committed template xlsx, and the migration copies it cell-by-cell at runtime. Trade-off: the template xlsx is now a permanent fixture in the repo (`tools/migration/v024_assets/investment_dashboard_template.xlsx`); future style edits go through Excel/LibreOffice on that file, not through code.

### Idempotency

Gate (`is_already_v024()`) checks **both** `Cover!B8 == "v0.2.4"` **AND** `Investment Dashboard` exists at sheetnames index 1. Re-running on a v0.2.4 file is a no-op (just re-saves). The script also handles the partial-state case where the sheet exists but the version stamp is older: anchors are refreshed without re-copying the sheet, so post-migration cell edits aren't blown away.

### Verification (11 checks)

`Cover!B8 == "v0.2.4"`, `Investment Dashboard` sheet exists, sheet at sheetnames index 1, dimensions ≥ 90 rows × 7 cols, B2 title contains "INVESTMENT DASHBOARD", B8 is a `T12 Analytics` formula reference, B15 label contains "occupancy", AZ1 purpose stamped, AZ3 visibility stamped, AZ4 self-stamp = `v0.2.4`, all 15 anchor `AZ4` = `v0.2.4`.

### Cross-checks against the destination Analyzer's referenced cells

Pre-migration sweep of the 56 distinct `T12 Analytics` cells the dashboard references against the destination's pre-v0.2.4 `T12 Analytics` (max_row = 170) confirmed all but one resolve to existing populated cells. The single exception is `T12 Analytics!E117` (Purchase price) — that's a manual analyst-input cell, expected to be blank in the template (the cap-rate formulas at `E118`/`E120` IFERROR-out cleanly when E117 is empty). All 27 distinct `Rent Roll Recon` references resolve against the destination's pre-v0.2.4 Rent Roll Recon (max_row = 176). No dangling references after migration.

### Files

- `tools/migration/migrate_to_v024.py` (new — 280 lines)
- `tools/migration/v024_assets/investment_dashboard_template.xlsx` (new — single-sheet template, source for the dashboard copy)
- `ALF_Financial_Analyzer_Only.xlsx` (regenerated — sheet count 14 → 15, substrate stamp v0.2.4)
- `SPEC-T12.md` (current substrate version bumped, v0.2.4 entry added to history)
- `CLAUDE.md` (last-updated line, current substrate version, closed-item note)
- `journal.md` (new 2026-05-16 entry)

### Cross-track note

This is Track 3 (workbook-only) work — no Track 1 or Track 2 code changed. Per CLAUDE.md scope discipline, dashboard work was user-authorized for this chat (2026-05-16).

---

## [Substrate template v0.2.3] — 2026-05-14

### Summary

**Closes UW-BACKLOG BL-0015.** Track 3 single-cell fix realigning `Rent Roll Recon!B16:D16` with the intent already documented in column H ("Gross contracted rates before concessions"). Old formula summed Actual Rate (`'Rent Roll Input'!$H`) over occupied units only, producing "current contracted at actual rate" rather than the Gross Potential Rent at 100% occupancy that the row's role as the underwriting anchor demands. New formula sums Market Rate (`$G`) over all units regardless of status, by care type. On Homestead populated: E16 reconciles from $565,140 → **$809,567** (IL $167k + AL $328k + MC $315k). Rows 17-20 unchanged — row 17's `H + I` was already correct because concessions are negative-signed.

This fix was originally implemented as substrate v0.1.11 in [PR #12](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/12) on 2026-05-12. The PR went stale while main moved through v0.1.12 → v0.2.2 (and the v0.1.11 substrate number was reused on main for an unrelated chart-axis fix). PR #12 was closed unmerged + re-implemented here as v0.2.3 with the current 14-sheet anchor list.

### What changed (migrate_to_v023.py)

- **A. Row 16 formulas rewritten** at `Rent Roll Recon!B16:D16`:
  ```
  Old:  SUMIFS('Rent Roll Input'!$H, ..., E<>Vacant, E<>Eviction, D=<care>)
  New:  SUMIFS('Rent Roll Input'!$G, ..., D=<care>)
  ```
  Status filter removed (`E<>Vacant`, `E<>Eviction`) because GPR is by definition at 100% occupancy. `E16 = SUM(B16:D16)` is unchanged.
- **B. Row 16 label** at `A16` rewritten from "RR gross contracted base rent / mo" to "RR Gross Potential Rent / mo  (Market × all units)". "Contracted" was misleading once vacants are included.
- **C. Row 16 note** at `H16` rewritten from "Gross contracted rates before concessions" to "Gross Potential Rent — Market Rate × all units at 100% occupancy. Excludes concessions & vacancy loss. Row 16 − Row 17 = vacancy + market-vs-actual gap." Now states the GPR semantics explicitly and identifies what the row16-vs-row17 gap measures (Homestead: $244,427).
- **D. Stamp** `Cover!B8` and all 14 anchor `AZ4` cells to `v0.2.3`.

### Why this is a Track 3 fix, not a Track 1/2 code change

The bug was in the Analyzer template's formula, not in any RR or T12 parser code. Both writers were correctly populating columns G (Market Rate) and H (Actual Rate) on Rent Roll Input — the formula was just reading the wrong column. Substrate-only fix.

### Idempotency

Gate (`is_already_v023()`) checks BOTH the version stamp AND that B16 references `$G`. Re-running on a v0.2.3 file is a no-op (just re-saves).

### Verification

9 checks: Cover!B8 stamp, all 14 AZ4 stamps, B16/C16/D16 each sum `$G` with the right care code, row 16 has no Vacant/Eviction filter, E16 still `=SUM(B16:D16)`, A16 label updated, H16 note updated, row 17 untouched (still `$H + $I` with status filter — sanity check that we didn't accidentally rewrite the wrong row).

### Cross-checks on populated Homestead sample

| Quantity | v0.2.2 | v0.2.3 |
|---|---|---|
| Row 16 IL / AL / MC | $133,730 / $226,457 / $204,953 | $167,156 / $327,776 / $314,635 |
| **Row 16 total** | **$565,140** | **$809,567** |
| Row 17 total | $565,140 | $565,140 (unchanged) |
| Row 16 − Row 17 | $0 | $244,427 (= vacancy loss + market-vs-actual premium) |

The post-fix gap of $244k on Homestead matches independent occupancy + premium math: 43 vacant units × ~$2.5k market × occupancy mix + small actual-vs-market premium on occupied units.

### Files

- `tools/migration/migrate_to_v023.py` (new)
- `ALF_Financial_Analyzer_Only.xlsx` (regenerated)
- `UW-BACKLOG.md` (BL-0015 added to Shipped)
- `SPEC-T12.md` (current substrate version bumped, v0.2.3 entry added to history)
- `CLAUDE.md` (last-updated, current substrate version, closed-item note)
- `journal.md` (session entry at top)

---

## [Substrate template v0.2.2] — 2026-05-14

### Summary

**User-feedback round against the Homestead populated v0.2.1 workbook.** Three coordinated Rent Roll Input fixes that close out the visual + structural gaps left by the v0.1.10 (cols V–AB) and v0.1.13 (cols AC–AG) column extensions. Cross-cuts with RR v1.17.4 (companion `_detect_substrate_version()` sentinel + parser-side concession-from-Notes rerouter).

### What changed (migrate_to_v022.py)

#### A. Format consistency on Rent Roll Input cols V–AH

The v0.1.10 and v0.1.13 column extensions used a different default style than the pre-existing cols A–U:

| Attribute | Pre-existing A–U | New V–AG (v0.1.10/v0.1.13) | After v0.2.2 |
| --- | --- | --- | --- |
| Header font size | 8 bold | 10 bold | 8 bold |
| Data number format | `$#,##0.00` / `mm/dd/yyyy` | `General` (no formatting) | `$` for monetary, date for W |
| Data row fill | `FFFFFFC7` (pale yellow) | `00000000` (transparent) | `FFFFFFC7` |
| Column widths | per-col widths set | unset | per-col widths set |

Step A applies the matching styling cell-by-cell: header sz=8, `$#,##0.00;"($"#,##0.00);-` on monetary cols (V, X, AC–AG, AH), `mm/dd/yyyy` on W (Move-out Date), `$#,##0.00` on Z/AA (PSF cols), pale-yellow `FFFFFFC7` data fill across all data rows 7-606, and column widths per col semantics (V=11, W=12, X=11, Y=30 for Notes text, Z/AA=10 for PSF, AB=8 for ACH flag, AC–AG=11, AH=13).

Total cells modified in Step A: ~7,800 (12 cols × header + 600 data rows).

#### B. Split T (Total LOC $) + add new col AH (Total Ancillary $)

Pre-v0.2.2 T was a mixed-semantics rollup:

```
T = L + M + N + O + IFERROR(AC,0) + IFERROR(AD,0) + IFERROR(AE,0) + IFERROR(AF,0) + IFERROR(AG,0)
   ── Care/LOC charges ──   ── 5 per-fee ancillary fees (added in v0.1.13) ──
```

The label "Total LOC $" no longer reflected what was in the cell. v0.2.2 splits this:

- **T (Total LOC $)** reverts to pure LOC: `=IFERROR(L+M+N+O,0)`.
- **NEW col AH (Total Ancillary $)** = `=IFERROR(IFERROR(V,0)+IFERROR(AC,0)+IFERROR(AD,0)+IFERROR(AE,0)+IFERROR(AF,0)+IFERROR(AG,0),0)` — the 2nd Person Rent + 5 per-fee ancillary cols, in one explicit sum.

#### C. Rewrite U (Total Monthly Rev) for transparency

Pre-v0.2.2:
```
U = H + IFERROR(I,0) + T + IFERROR(V,0)
```
The +V was needed because T didn't include V; the AC–AG were silently included via T. After step B, V is inside AH and AC–AG are no longer in T:

```
U = H + IFERROR(I,0) + T + IFERROR(AH,0)    (post-v0.2.2)
```

The math is structurally identical (V is now inside AH). The structure is now `Total Monthly Rev = Actual Rate + Concession + Total LOC + Total Ancillary` — every contributor is visible at one hop.

### What changed (RR companion v1.17.4 — bundled in this PR)

**`_detect_substrate_version()` sentinel addition (`app.py`):** prepended to the fallback chain (newest-first):
- `Rent Roll Input!AH4` contains `"Total"` + `"Ancillary"` → `v0.2.2+`

**`normalizer.py` — concession-from-Notes rerouter:** new `_reroute_recurring_concessions()` post-process pass that detects negative `Other LOC $` values whose Notes column contains a recurring-concession marker (`$XXX/mo concession`, `$XXX concession ending DATE`, `$XXX concession remaining`, `ongoing concession`, `waived CF`) and **moves the value from Other LOC $ to Concession $** (with end-date extraction into `Concession End Date` when present). One-time / parenthetical mentions like `(half off $1047 concession)` are explicitly left alone. See `CHANGELOG-RR.md` `[1.17.4]` for full detail.

### Idempotency

Gate checks both `Cover!B8 == "v0.2.2"` AND `Rent Roll Input!AH4 == "Total\nAncillary $"`. Re-run on already-migrated workbook is a no-op.

### Verification

12/12 verification checks pass on the bundled Analyzer:

```
   1. Cover!B8 = 'v0.2.2'                                              : True
   2. All 14 AZ4 = v0.2.2                                              : True (14 sheets)
   3. AH4 sentinel = 'Total\nAncillary $'                              : True
   4. T7 = pure LOC (L+M+N+O, no AC..AG)                               : True
   5. AH7 = V+AC+AD+AE+AF+AG (Total Ancillary)                         : True
   6. U7 = H+I+T+AH (rewritten, no +V)                                 : True
   7. V4 header font size = 8 (was 10)                                 : True
   8. AC7 number_format includes $ sign                                : True
   9. AC7 fill = FFFFFFC7 (pale yellow)                                : True
  10. W7 number_format = mm/dd/yyyy (Move-out Date)                    : True
  11. Column widths set on V-AH per spec                               : True
  12. T606 (last row) also rewritten                                   : True
```

### Files changed

- `tools/migration/migrate_to_v022.py` — new idempotent migration script (~470 lines)
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.2.2
- `app.py` — sentinel addition for v0.2.2 + RR_VERSION bump
- `normalizer.py` — concession-from-Notes rerouter
- `CHANGELOG-T12.md` — this entry
- `CHANGELOG-RR.md` — companion `[1.17.4]` entry
- `SPEC-T12.md` / `SPEC-RR.md` — current-version lines
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — Last updated line + current substrate version

### Out of scope (carry-forwards opened)

None. The user-feedback issues (formatting, formula transparency, concession routing) are all addressed in this release.

---

## [Substrate template v0.2.1] — 2026-05-14

### Summary

**UW-BACKLOG BL-0001 closed — finer ancillary Labels in `Description_Map`.** Surfaced by substrate v0.1.12 Section M (Operator Fee Schedule & Ancillary Reconciliation): M2 / M3 / M4 were reporting 5 of the 7 default Homestead IL fees against the shared catchall Label "Other community revenue", with the M3 `(shared — see row N)` heuristic preventing double-reporting but also preventing per-fee T12 attribution. This release adds 5 dedicated Labels so each of those fees can be attributed at the GL level.

Closed vocabulary grows **55 → 60 Labels**.

Cross-cuts with RR v1.17.3 — `_detect_substrate_version()` in `app.py` is widened to accept the `vN.N.N` pattern (was capped at `v0.1.N`, so v0.2.0 / v0.2.1 fell through to the sentinel-cell fallback). Bundled in the same PR.

### Five new Labels

| Label                 | Replaces routing of                                      |
| --------------------- | -------------------------------------------------------- |
| `Meal Income`         | Meal Plan Revenue, Meal Plan Income, Dining Revenue, …   |
| `Housekeeping Income` | Housekeeping Income, H/K Income, Housekeeping Revenue    |
| `Laundry Income`      | Laundry Income, Laundry Revenue                           |
| `Scooter Fee Revenue` | Motorized Scooter Fee, Mobility Fee, Scooter Fee         |
| `Transfer Fee Revenue`| Elective Transfer Fee, Transfer Fee                       |

Each previously got mapped to `Other community revenue` (the catchall). After this release, those source descriptions match the new specific Labels via Description_Map, populate their own rows on T12 Raw Data + Monthly Trending, and Section M can isolate per-fee T12 totals.

### What changed (migrate_to_v021.py)

The migration follows the v0.1.5 row-insertion pattern documented in CHANGELOG-T12.md, scaled to insert 5 rows at once (`insert_rows(target, amount=5)`).

#### A. T12 Raw Data — insert 5 rows at R16

5 new SUMIF rows inserted between `2nd Person Revenue` at R15 and the old `Other community revenue` at R16 (which shifts to R21). Each new row mirrors the R15 template:
- col A = `"Revenue"`
- col B = new Label
- cols F-Q (monthly Jan-Dec) = `=SUMIF(T12_Calc!$N$1:$N$505, "<NewLabel>", T12_Calc!$B$1:$B$505)`
- col R (annual) = `=SUM(F{row}:Q{row})`

After insert, all workbook formulas referencing T12 Raw Data row ≥ 16 get their row refs shifted by +5 (696 cells across T12 Analytics + T12 Raw Data internal SUMs). **Template formulas are captured AFTER the shift sweep** — the v0.1.5 implementation captured pre-shift, which caused the new rows' SUMIF range endpoints to lag the bumped-up neighbors. Post-shift capture keeps every row's `$N$505` consistent.

#### B. Monthly Trending — insert 5 rows at R20

5 new INDEX/MATCH rows inserted between `2nd Person Revenue` at R19 and the old `Other community revenue` at R20 (which shifts to R25). EGI shifts from R21 → R26. Each new row mirrors R19's INDEX/MATCH template:
- col A = new Label
- cols B-M = `=IFERROR(INDEX('T12 Raw Data'!<col>:<col>, MATCH("<NewLabel>", 'T12 Raw Data'!B:B, 0)), 0)`
- col N (annual) = `=SUM(B{row}:M{row})`

After insert, 147 formula cells shifted across Rent Roll Recon (1) + Monthly Trending (145) + Workbook Health (1). The EGI formula at the new R26 is explicitly rewritten to include the 5 new rows (`=B8+B10+B11+B15+B16+B17+B18+B19+B20+B21+B22+B23+B24+B25` instead of just `+B25`).

#### C. Description_Map — 14 new Description→Label appends

The Description_Map uses dynamic defined-name ranges (`DescMap_Description`, `DescMap_Label` via COUNTA) that auto-extend, so no row insertion is needed — appending at the bottom is enough. 14 typical operator-side descriptions added, mapped to the 5 new Labels:

| New Label             | Source descriptions added (count)                                    |
| --------------------- | -------------------------------------------------------------------- |
| Meal Income           | Meal Income, Meal Plan Revenue, Meal Plan Income, Dining Revenue (4) |
| Housekeeping Income   | Housekeeping Income, Housekeeping Revenue, H/K Income (3)            |
| Laundry Income        | Laundry Income, Laundry Revenue (2)                                  |
| Scooter Fee Revenue   | Scooter Fee, Motorized Scooter Fee, Mobility Fee (3)                 |
| Transfer Fee Revenue  | Transfer Fee, Elective Transfer Fee (2)                              |

#### D. Rent Roll Recon Section M D-column re-points

5 of the 7 default fees on Section M1 (rows 123-129) have their `T12 Label` (col D) changed from `Other community revenue` to the matching new Label:

| Row | Fee Name              | Old D-column                | New D-column          |
| --- | --------------------- | --------------------------- | --------------------- |
| 124 | Elective Transfer Fee | Other community revenue     | Transfer Fee Revenue  |
| 125 | Meal Delivery         | Other community revenue     | Meal Income           |
| 126 | Motorized Scooter Fee | Other community revenue     | Scooter Fee Revenue   |
| 128 | Housekeeping          | Other community revenue     | Housekeeping Income   |
| 129 | Laundry               | Other community revenue     | Laundry Income        |

M2 / M3 / M4 read these via relative references, so the per-fee attribution propagates automatically. M3's `(shared — see row N)` detection resolves: COUNTIF finds no duplicates so each row gets its own VLOOKUP T12 total. M5 ("Other community revenue residual") still works correctly — only the unchanged D123 (Community Fee → Community / move-in fees, not a residual contributor) remains in the M5 attribution sum.

#### E. RR v1.17.3 companion patch — `_detect_substrate_version()` widening

The version-detection regex in `app.py` was `^v0\.1\.\d+$` — it didn't match `v0.2.0` or `v0.2.1`, so any Analyzer at v0.2.x fell through to the sentinel-cell fallback (which reported `v0.1.14+` based on the Rent Roll Recon!I87 sentinel that's still present). Widened to `^v\d+\.\d+\.\d+$`. Added two new sentinel checks for the fallback chain (T12 Raw Data!B16 == "Meal Income" → v0.2.1+; presence of "UW Export" sheet → v0.2.0+).

### Idempotency

Gate checks both `Cover!B8 == "v0.2.1"` AND `T12 Raw Data!B16 == "Meal Income"` — re-running on an already-migrated workbook prints `"Workbook is already at v0.2.1. No-op (will re-save)."` and exits.

### Verification

13/13 verification checks on the bundled Analyzer:

```
   1. Cover!B8 = 'v0.2.1'                                              : True
   2. All 14 AZ4 = v0.2.1                                              : True (14 sheets)
   3. T12 Raw Data R16-R20 = the 5 new labels                          : True
   4. T12 Raw Data R21 = 'Other community revenue' (shifted +5)        : True
   5. T12 Raw Data F16 SUMIF refers to 'Meal Income'                   : True
   6. Monthly Trending R20-R24 = the 5 new labels                      : True
   7. Monthly Trending R25 = 'Other community revenue' & R26 = EGI     : True
   8. Monthly Trending B26 EGI includes new rows B20-B24 + B25         : True
   9. Monthly Trending B20 INDEX/MATCH refers to 'Meal Income'         : True
  10. Rent Roll Recon Section M D124-D129 re-pointed to new Labels     : True
  11. Description_Map appended 14/14 new descriptions                  : True
  12. Rent Roll Recon B174 EGI ref shifted to Monthly Trending N26     : True
  13. Sentinel: T12 Raw Data!B16 = 'Meal Income'                       : True
```

### Files changed

- `tools/migration/migrate_to_v021.py` — new idempotent migration script (~580 lines)
- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.2.1
- `app.py` — `_detect_substrate_version()` regex + sentinel chain widened; `RR_VERSION` 1.17.2 → 1.17.3
- `CHANGELOG-T12.md` — this entry
- `CHANGELOG-RR.md` — companion `[1.17.3]` entry for the version-detection widening
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — current-version line + Track 1 stamp
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — Last updated line + current substrate version
- `UW-BACKLOG.md` — BL-0001 moved Pending → Shipped

### Out of scope (carry-forwards opened)

None. With BL-0001 closed, **the UW-BACKLOG forward-looking list is empty** for the first time since UW-BACKLOG.md was introduced in substrate v0.1.12. (BL-0010 — the partner `t12_translator.py` rename — also closed in RR v1.17.2 immediately before this release.)

---

## [Substrate template v0.2.0] — 2026-05-14

### Summary

**v0.2.0 flagship release — BL-0009 closed.** Branch 2 (Handoff readiness) — the final open Analyzer-optimization workstream from the four-branch Track 3 roadmap. Ships three coordinated additions to round out the downstream-handoff story:

1. **New `UW Export` sheet** — values-only mirror of UW Output for clean copy-paste into the downstream full-underwriting sheet (which doesn't consume formula references back into this workbook — only static values).
2. **Pre-Export Gate** — compact aggregated readiness check on Workbook Health that surfaces a single ✓ / ⚠ "READY FOR EXPORT" indicator before the analyst hands the file off.
3. **Workbook Map extension** — UW Export added to the existing sheet directory.

Pure Track 3 substrate work. No RR/T12 code changes. The minor-version bump (v0.1.x → **v0.2.0**) reflects the new top-level sheet rather than a breaking change to existing semantics.

### What changed (migrate_to_v020.py)

#### A. UW Export sheet (NEW)

Inserted at index 8 — between UW Output and Mapping Review in the tab order. Sheet layout:

```
Row 1     :  Title (merged A:H, navy fill)
             "UW Export  —  Values-only mirror of UW Output"
Row 2     :  Instructions (merged A:H, italic)
             "Copy A9:H79 … into the downstream UW template …"
Rows 3-7  :  Metadata header (label in col A, formula in col B merged to H):
             - Property name:        =IFERROR(Property_Name, "(not set)")
             - Rent roll period:     =IF(ISNUMBER(RR_Period_Date), TEXT(...), "(not set)")
             - T12 period:           =IF(ISNUMBER(T12_Period_Date), TEXT(...), "(not set)")
             - Substrate version:    =Cover!$B$8
             - Generated (open time): =TEXT(NOW(), "yyyy-mm-dd hh:mm")
Row 8     :  Visual break
Rows 9-79 :  Values-only mirror of UW Output rows 1-71 across cols A-H.
             Each cell uses ='UW Output'!{cell}. Header row at row 12
             (mirror of UW Output row 4) gets header styling.
```

Sheet-level: gridlines hidden, col A width 28, cols B-H width 14, AZ1 holds the sheet-purpose label `"Values-only mirror of UW Output for downstream paste"`, AZ4 holds the v0.2.0 version stamp.

Why formulas not static values: openpyxl cannot evaluate formulas, so the writer pipeline can't produce truly static values at write-time. The formula approach is cleaner anyway — when the analyst opens the file in Excel and the chain (Rent Roll Input → T12 Analytics → UW Output → UW Export) re-evaluates, the mirror reflects the latest computed state. The downstream consumer uses Excel's **Paste-Special: Values** when pulling from UW Export into their template, producing a fully static destination.

#### B. Pre-Export Gate (Workbook Health rows 46-52)

Adds a fourth section to Workbook Health:

```
Row 46:  "4 · PRE-EXPORT GATE"  (subtitle bar)
Row 47:  headers: Check | Status
Row 48:  P1 · RR + T12 period dates set       → reads V3+V4 (rows 25-26)
Row 49:  P2 · Property name populated          → reads Property_Name named range
Row 50:  P3 · RR + T12 input rows present      → reads V6+V7 (rows 28-29)
Row 51:  P4 · Source $→Operating $ leakage ≤±$1 → reads V1 (row 23)
Row 52:  READY FOR EXPORT?  →  ✓ READY / ⚠ NOT READY   (aggregate AND across P1-P4)
```

Each P-check is a formula reference to an existing V-row validation cell that's been on Workbook Health since v0.1.4. No new validation criteria invented — just packages them as a downstream-handoff readiness aggregate.

Row 52 aggregate is bold + yellow-fill — visually distinct from the per-check rows above. Reads `"✓ READY — UW Export tab is good to copy"` or `"⚠ NOT READY — resolve the ⚠ items above first"` based on whether all four sub-checks pass.

#### C. Workbook Map extension

Adds `"UW Export"` at Workbook Health row 19 (a previously-empty visual break before Section 2). Cell B19 reads `='UW Export'!AZ1` — pulls the sheet-purpose label set at install time.

#### D. ANCHOR_SHEETS extended from 13 → 14

The migration's ANCHOR_SHEETS tuple now includes UW Export so the AZ4 anchor count is 14 (was 13 through v0.1.15). All 14 anchors stamped to `v0.2.0`. Cover!B8 stamped to `v0.2.0`.

### Idempotency

Gate (`is_already_v020()`) checks BOTH the version stamp AND that the `UW Export` sheet exists with the title at A1. Re-runs on partial-state files safely re-apply — if `UW Export` is partial, the migration drops and recreates it cleanly rather than in-place patching (the sheet is content-only, no analyst-edited cells to preserve).

### Verification

13-check verification block: Cover!B8 stamped, all 14 AZ4 stamped, UW Export sheet exists + title row 1 + Property name metadata (label + formula) + Substrate version metadata formula + Mirror A9 = `'UW Output'!A1` + Mirror H79 = `'UW Output'!H71`, Pre-Export Gate title + P1 sub-check + aggregate formula present, Workbook Map includes UW Export.

Migration verified end-to-end on:

- **Bundled v0.1.15 → v0.2.0**: 13/13 checks pass. File size 194,779 → 199,228 bytes (+4,449 bytes — new sheet with 71 mirror rows × 8 cols + 5 metadata rows + Pre-Export Gate cells).
- **User's populated Homestead workbook** chained `v0.1.10 → v0.1.12 → v0.1.13 → v0.1.14 → v0.1.15 → v0.2.0` — all checks green at each step.
- **Idempotency**: re-running on a v0.2.0 file exits cleanly with `"Workbook is already at v0.2.0. No-op (will re-save)."`

### Closes BL-0009 — full Branch 2 scope

The original BL-0009 entry listed three components for Branch 2:

| Sub-item | Status |
| --- | --- |
| Pre-export gate | ✅ Shipped (Workbook Health rows 46-52, aggregate cell 52) |
| UW Export sheet (values-only mirror) | ✅ Shipped (71-row mirror with formula references to UW Output) |
| Metadata header on UW Export | ✅ Shipped (rows 3-7: Property name / RR period / T12 period / substrate version / generated timestamp) |

### What remains in [UW-BACKLOG.md](UW-BACKLOG.md) after this release

- `BL-0001` — finer ancillary T12 Labels (Description_Map vocabulary expansion). Reasonable next v0.2.1+ candidate.
- `BL-0010` — module rename `t12_translator.py` → `analyzer_rr_translator.py` refactor. Whenever bundled.

The four-branch Track 3 roadmap is now **fully closed**:
- Branches 1+4 (correctness + substrate) — closed in v0.1.6
- Branch 3 (analytical coverage) — closed in v0.1.8, extended through v0.1.14
- Branch 2 (Handoff readiness) — **closed in v0.2.0 (this release)**

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.2.0
- `tools/migration/migrate_to_v020.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference (substrate v0.2.0)
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — version references
- `UW-BACKLOG.md` — `BL-0009` moved to Shipped
- `CHANGELOG-T12.md` — this entry

---

## [Substrate template v0.1.15] — 2026-05-14

### Summary

**UW-BACKLOG BL-0002 closed** — V5 chart empty-state UX. When a source rent roll has no per-bed acuity tier data (Homestead-style broker-condensed formats, or flat-rate AL operators), the AL Acuity Mix doughnut on `T12 Analytics` previously rendered an empty frame with 8 zero-value slices in the legend, leaving the analyst with no in-workbook context for why. Two coordinated tweaks fix this without restructuring the chart or adding new sheets.

Companion to **RR v1.17.1** (UW-BACKLOG BL-0008 — version detection rewrite). Both ship in the same PR.

### What changed (migrate_to_v0115.py)

- **A. Blank D59:D66 when no acuity data** — wraps the 8 existing `IFERROR(SUMIFS(...), 0)` formulas at `Rent Roll Recon!D59:D66` so they return `""` (empty) when `$B$67 = 0` (zero occupied AL beds with any acuity tier filled in):
  ```
  Old:  =IFERROR(SUMIFS(...), 0)
  New:  =IF($B$67=0, "", IFERROR(SUMIFS(...), 0))
  ```
  Doughnut charts treat empty cells as "no slice" — V5 now renders as a true empty frame instead of 8 zero-value slices with legend labels. Analyst-customized SUMIFS (if any) survive the migration verbatim because the wrapper splices in the inner formula unchanged.

- **B. Style the existing V5 conditional note at `T12 Analytics!K45`** — the cell already contains (since v0.1.8) a 3-branch `IF` formula whose empty-state branch returns `"Property has no AL acuity data — flat-rate AL or unpopulated."`. The note was visible but visually identical to a label. v0.1.15 adds:
  - **Bold font** (Calibri 10 bold, dark text)
  - **Pale yellow fill** (`#FFF2CC`) — matches the warning palette used by other Workbook Health and Section M conditional notes
  - **Left + wrap_text alignment**

  The formula itself is **untouched** — only the styling changes. When the formula returns the `✓` branch (acuity data present), the cell is still bold + yellow, which is fine: the ✓ now reads as a confirmation banner. The cosmetic mismatch is the tradeoff for not needing conditional formatting (which openpyxl's formula-based CF support is unreliable for and would have ballooned the migration scope).

- **C. Stamp** `Cover!B8` and 13 `AZ4` anchors to `v0.1.14` → `v0.1.15`.

### Why option (a) instead of (b) or (c) from the backlog

The original BL-0002 entry listed three options:
- (a) Accept and document — V5 only useful when source has acuity
- (b) Fall back to "Care Level $ grouped by Care Type" when no acuity
- (c) Hide chart conditionally

Implementation analysis during this release:
- **(b)** would create useful content for *flat-rate AL operators* (some Care Level $ data, no acuity tiers) but is **not a fix for Homestead specifically** — Homestead has $0 Care Level $ total across all 176 beds (broker format doesn't expose per-bed LOC). A Care Type fallback chart would also be empty for Homestead.
- **(c)** "hide the chart" — openpyxl's chart object doesn't expose a "hide if all-zero data" toggle. The closest available primitive is the `plotVisOnly` attribute, which only controls how hidden source cells are plotted; the chart frame stays rendered. A real hide would require chart XML manipulation we'd want to avoid.
- **(a)** with **strengthened styling** is the lowest-risk improvement that ships the user-visible benefit (clear in-workbook context for empty V5) without changing chart structure or data flow.

When a future deal surfaces a flat-rate-AL fixture (Care Level $ > 0 but no acuity), revisit BL-0002-style fallback content as a follow-up.

### Idempotency

Gate (`is_already_v0115()`) checks BOTH the version stamp AND that `Rent Roll Recon!D59` already starts with the v0.1.15 wrapper prefix `=IF($B$67=0,"",`. Re-runs on partial-state files safely re-apply.

### Verification

7-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, all 8 acuity-data cells wrapped (D59:D66), K45 note bold, K45 note fill = `FFFFF2CC`, K45 note styling check (combined), K45 note formula intact.

Migration verified end-to-end on:
- **Bundled v0.1.14 → v0.1.15**: 7/7 checks pass. File size 194,732 → 194,779 bytes (+47 bytes — minimal, consistent with 8 formula wraps + 1 cell style change + 14 stamps).
- **User's populated Homestead workbook** chained `v0.1.10 → v0.1.12 → v0.1.13 → v0.1.14 → v0.1.15` — Cover!B8 reads `v0.1.15`, D59 formula carries the new wrapper, K45 styled bold + yellow.
- **Idempotency**: re-running on a v0.1.15 file exits cleanly with `"Workbook is already at v0.1.15. No-op (will re-save)."`

### Companion (RR v1.17.1)

Bundled in the same PR — see [CHANGELOG-RR.md](CHANGELOG-RR.md) `[1.17.1]` for the RR-side `_detect_substrate_version()` rewrite (BL-0008).

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.15
- `tools/migration/migrate_to_v0115.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — version references
- `UW-BACKLOG.md` — `BL-0002` + `BL-0008` moved to Shipped
- `CHANGELOG-T12.md` — this entry
- `CHANGELOG-RR.md` — `[1.17.1]` entry

---

## [Substrate template v0.1.14] — 2026-05-14

### Summary

Three small Track 3 patches surfaced in v0.1.10 carry-forwards, bundled into a single substrate increment per UW-BACKLOG prioritization. Pure substrate change — no RR/T12 code changes.

**Closes [UW-BACKLOG BL-0004, BL-0005, BL-0006](UW-BACKLOG.md).**

### What changed (migrate_to_v0114.py)

- **A. BL-0004 — T12 Analytics: 2P revenue reconciliation row** at rows 168-170:
  - Row 168: subsection title (merged A:G) — `RR ↔ T12 — 2nd Person Revenue Reconciliation`
  - Row 169: column headers (Metric / RR projection / T12 actual / Variance % / Note)
  - Row 170: data row — `=SUM('Rent Roll Input'!$V$7:$V$606)*12` (RR annual projection) vs. `=IFERROR('T12 Raw Data'!$R$15,0)` (T12 actual annual). Variance % + conditional note: ⚠ fires at \|variance\| > 10%; ✓ "reconciles within 10% of T12" otherwise.

  Placement: chose rows 168-170 (after the existing KPI Dashboard color key at row 166) instead of slotting into rows 42-44 because of pre-existing `A43:H43` and `A45:H45` horizontal merges in the GPR Waterfall area. Appending past row 166 is cleaner than disrupting merge ranges; the new block stands alone as an addendum and doesn't risk breaking adjacent formulas.

- **B. BL-0005 — Workbook Health: total AR / Balance aggregation** at rows 43-45:
  - Row 43: `G9 · Total outstanding AR (Σ Rent Roll Input!X)` — `=SUM('Rent Roll Input'!$X$7:$X$606)`
  - Row 44: `G10 · AR ÷ monthly EGI (collection-velocity indicator)` — `=IFERROR(B43/('Monthly Trending'!$N$21/12),0)`
  - Row 45: conditional note (merged A:D) — ⚠ fires when `AR > 5% of monthly EGI`; ✓ "within 5% of monthly EGI" otherwise.

  Placement: directly after the existing `G8 · Last opened (volatile)` row at 42. The new rows extend the Diagnostics section without disturbing it.

- **C. BL-0006 — Rent Roll Recon Section K: Avg Actual PSF column** at col I rows 87-93:
  - I87: header — `Avg Actual\nPSF`
  - I88-I92: per-unit-type AVERAGEIFS on `Rent Roll Input!$AA$7:$AA$606` (Actual PSF, captured at v1.16.0). Same filter pattern as col D (Avg Rate) — period selector + occupied + IL care type + unit type.
  - I93: Total IL row — same formula without the unit-type filter.

  Placement: extends the existing IL unit-type table (cols A-H) with a new col I. Doesn't touch the dispersion rows below (rows 95-100). Source data already exists at `Rent Roll Input!AA` per substrate v0.1.10.

- **D. Stamp** `Cover!B8` and 13 `AZ4` anchors to `v0.1.14`.

### Idempotency

Gate (`is_already_v0114()`) checks BOTH the version stamp AND three sentinel cells (one per BL): T12 Analytics!A168 contains "Reconciliation", Workbook Health!A43 contains "G9", Rent Roll Recon!I87 contains "Actual" and "PSF". Re-runs on partial-state files safely re-apply.

### Verification

13-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, BL-0004 title row + RR projection formula + T12 actual formula, BL-0005 G9 label + AR sum formula + G10 label, BL-0006 I87 header + I88 Studio formula + I93 Total IL formula, plus Section K unit-type table intact + Section L MC structure intact (regression guards).

Migration verified end-to-end on:
- **Bundled v0.1.13 Analyzer** → v0.1.14 cleanly. File size 193,915 → 194,732 bytes (+817 bytes — small, consistent with ~13 new functional cells + 14 stamps).
- **User's populated Homestead workbook** chained v0.1.10 → v0.1.12 → v0.1.13 → v0.1.14 — all 13 checks green at each step.
- **Idempotency**: re-running on a v0.1.14 file exits cleanly with `"Workbook is already at v0.1.14. No-op (will re-save)."`

### What's left in UW-BACKLOG.md after this release

- `BL-0001` (substrate v0.2.0): finer ancillary T12 Labels (`Meal Income`, `Housekeeping Income`, etc.)
- `BL-0002` (substrate v0.2.0): V5 chart fallback for broker-format rent rolls with no acuity
- `BL-0008` (RR, whenever bundled): substrate version detection in `app.py`
- `BL-0009` (substrate v0.2.0 flagship): Branch 2 Handoff readiness (UW Export, pre-export gate, metadata header)
- `BL-0010` (refactor, whenever): `t12_translator.py` → `analyzer_rr_translator.py` rename

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.14
- `tools/migration/migrate_to_v0114.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — substrate version reference
- `UW-BACKLOG.md` — `BL-0004` / `BL-0005` / `BL-0006` moved from Pending to Shipped
- `CHANGELOG-T12.md` — this entry

---

## [Substrate template v0.1.13] — 2026-05-13

### Summary

Track 3 companion to RR v1.17.0 (UW-BACKLOG BL-0003 — RR Input expansion). Two coordinated changes:

1. **Rent Roll Input gets 5 new columns at AC-AG** to receive the per-fee ancillary breakdown produced by the v1.17.0 parser: `Meal Plan $` / `Scooter Fee $` / `Housekeeping $` / `Laundry $` / `Pet $`. Other LOC $ (col O) remains as the catchall. Total LOC $ formula at T7:T606 extended to include AC-AG so the per-resident total is unchanged — only the distribution across columns changes.

2. **Section M (Rent Roll Recon rows 121-167) gets a 5th M1 column "RR Input Col"** plus a complete M2 / M4 rewrite using universal `INDIRECT` formulas off that column. Previously only Second Person Fee had real per-fee capture-rate / implied-rate formulas; now Meal Delivery / Motorized Scooter / Housekeeping / Laundry compute too because they have direct RR Input column matches. M2 eligibility unified to all-occupied beds in the selected period (was: occupied IL only for SP — per user spec, couples can occur in any care type).

### What changed (migrate_to_v0113.py)

- **A. RRI new column headers** at row 4 cols AC-AG (5 cells styled to match the existing navy header).
- **B. Total LOC $ formula extension** at T7:T606:
  ```
  Old: =IFERROR(L{r}+M{r}+N{r}+O{r},0)
  New: =IFERROR(L{r}+M{r}+N{r}+O{r}+IFERROR(AC{r},0)+IFERROR(AD{r},0)+
                 IFERROR(AE{r},0)+IFERROR(AF{r},0)+IFERROR(AG{r},0),0)
  ```
  Pattern-matched on the exact prior shape so customized formulas (if any) are left intact.
- **C1. Section M1 "RR Input Col" header** at E122 + pre-populated default mappings for the 7 default fees:
  - Community Fee → `""` (event-based; no per-fee RR col)
  - Elective Transfer Fee → `""` (rare event; no per-fee RR col)
  - Meal Delivery → `AC`
  - Motorized Scooter Fee → `AD`
  - Second Person Fee → `V` (existing v0.1.10 column)
  - Housekeeping → `AE`
  - Laundry → `AF`
- **C2. Section M2 universal formulas** (rows 135-143):
  - Eligible #: `COUNTIFS(occupied across all care types, period selector)` — same for all 9 rows
  - Capturing #: `IF(E{m1_row}="", "—", COUNTIF(INDIRECT("'Rent Roll Input'!"&E{m1_row}&"7:606"), ">0"))`
  - Capture %: `IFERROR(C/B, "")`
  - Note: dynamic — `"✓ Direct RR match (col X)"` when E set, `"No per-fee RR column"` otherwise
- **C3. Section M4 universal formulas** (rows 159-167):
  - T12 $/mo from M3 (unchanged behavior)
  - RR # capturing pulled from M2
  - Implied $/resident: only when E set AND counts numeric
  - Variance % vs. M1 schedule
  - Conditional note: `"✓ Implied rate within 5% of schedule"` / `"⚠ Implied rate differs by X%"` / `"Falls into M5 Misc."` based on E-col + variance threshold
- **D. Stamp** `Cover!B8` and 13 `AZ4` anchors to `v0.1.13`.

Section M3 / M5 unchanged — the v0.1.12 formulas were already forward-compatible. M5's SUMPRODUCT for "fees attributed to OCR via M2 capture" begins producing real deductions automatically once Meal/Scooter/HK/Laundry rows have populated M2 capture #'s.

### Idempotency

Gate (`is_already_v0113()`) checks BOTH the version stamp AND that `Rent Roll Input!AC4` reads `Meal Plan` (verifying the new headers landed). Re-runs on a partial-state file safely re-apply.

### Verification

11-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, 5 new RRI headers present, Total LOC formula extended in 600 rows, M1 col E header / 5 default mappings, M2 INDIRECT formula present, M2 eligibility unified (no IL filter), M4 implied-rate formula generic, Sections K and L intact.

End-to-end migration verified on:
- **Bundled v0.1.12 Analyzer** → v0.1.13 cleanly. File size 183,103 → 193,915 bytes (+10,812 bytes consistent with 5 new header cells + 600 row × 1 col formula extension + 9 × 4 cells of M1/M2/M4 rewrites).
- **User's populated Homestead workbook** chained through v0.1.10 → v0.1.12 → v0.1.13 — all 11 checks green at each step.
- **Idempotency**: re-running on a v0.1.13 file exits cleanly with `"Workbook is already at v0.1.13. No-op (will re-save)."`

### Migration path for users

Workbooks at substrates older than v0.1.12 must chain through prior migrations in order. Each script handles one substrate version step:

```
python tools/migration/migrate_to_v0111.py file.xlsx file_v0111.xlsx
python tools/migration/migrate_to_v0112.py file_v0111.xlsx file_v0112.xlsx
python tools/migration/migrate_to_v0113.py file_v0112.xlsx file_v0113.xlsx
```

Or skip the chaining: re-run the live app to get a fresh download with v0.1.13 substrate.

### Out of scope (logged in UW-BACKLOG.md)

- **`BL-0001`** still pending: finer ancillary T12 Labels (`Meal Income`, `Housekeeping Income`, etc.) so Section M3 stops returning `(shared bucket)` notes. Substrate v0.2.0 vocabulary expansion.
- **`BL-0004` / `BL-0005` / `BL-0006`** still pending: small Track 3 patches surfaced by v0.1.10 (T12 Analytics 2P reconciliation row, Workbook Health AR aggregation, Section K PSF dispersion stats). Substrate v0.1.14 candidates.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.13
- `tools/migration/migrate_to_v0113.py` — new idempotent migration script
- `SPEC-T12.md` — current-version line
- `SPEC-RR.md` — Track-versions inline reference
- `README.md` — versions table + migration script listing
- `CLAUDE.md` — substrate version reference
- `UW-BACKLOG.md` — `BL-0003` moved to Shipped
- `CHANGELOG-T12.md` — this entry

(See [CHANGELOG-RR.md](CHANGELOG-RR.md) `[1.17.0]` for the Track 1 parser / writer / mapping changes that this substrate companions.)

---

## [Substrate template v0.1.12] — 2026-05-13

### Summary

Adds **Section M** (Operator Fee Schedule & Ancillary Revenue Reconciliation) to `Rent Roll Recon` rows 119-172. Captures the operator's published fee schedule as a structural part of the underwriting analysis and reconciles published rates against T12 actuals through the chain: schedule → RR-side capture (count + %) → T12 12-month actuals → implied per-resident rate → schedule fidelity %.

Five sub-sections:

- **M1 — Published schedule (analyst paste-in)**: 7 default fee rows (Community Fee / Elective Transfer / Meal Delivery / Motorized Scooter / Second Person / Housekeeping / Laundry) plus 2 blank rows for property-specific additions. Column D = T12 Label, validated against `DescMap_Label` named range.
- **M2 — RR-side capture (auto)**: for fees with a direct per-resident column on `Rent Roll Input`, count eligible vs. capturing residents and compute capture %. Today only Second Person Fee has a direct match (`Rent Roll Input!V`, added v0.1.10). Other 6 fees show `n/a (one-time)` or `falls into M5 (see UW-BACKLOG BL-0003)`.
- **M3 — T12 actuals (auto)**: VLOOKUP from the M1 T12 Label into `T12 Raw Data!R` (annual total). Shared-bucket detection: when multiple M1 fees map to the same Label (typical for `Other community revenue`), the 2nd+ occurrences display `(shared — see row N)` instead of duplicating the value.
- **M4 — Implied per-resident rate (T12 ÷ RR count vs. schedule)**: per user spec, divides T12 monthly $ by RR # capturing → implied per-resident rate → variance % vs. M1 schedule. Conditional note fires when |variance| > 5%. Only computable today for SP; others fall into M5.
- **M5 — Misc. Income (residual)**: T12 `Other community revenue` annual + monthly + per-fee attribution + residual + % of EGI. Conditional note fires when residual > 15% of EGI, pointing the analyst to UW-BACKLOG BL-0003.

### What changed (migrate_to_v0112.py)

- **A. Section M installation** on `Rent Roll Recon` at rows 119-172:
  - Section title (row 119), 5 subsection titles (M1 row 121, M2 row 133, M3 row 143, M4 row 153, M5 row 163)
  - M1: 9 paste-in rows × 4 cols (Fee Name / Published $ / Basis / T12 Label) with data validation on the Label column
  - M2: 9 auto-computed rows × 5 cols
  - M3: 9 auto-computed rows × 5 cols (VLOOKUP + shared-bucket detection)
  - M4: 9 auto-computed rows × 7 cols (implied rate + variance + conditional note)
  - M5: 5 metric rows + 1 conditional note row, anchored to `'Monthly Trending'!$N$21` (EGI annual)
- **B. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.12`.

### Idempotency

Gate (`is_already_v0112()`) checks BOTH the version stamp AND that `Rent Roll Recon!A119` already starts with `"M "` (the Section M title prefix). Re-runs on a partial-state file safely re-apply.

### Verification

10-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, Section M title in place, M1 subsection title, 7 default fees installed, M2 SP COUNTIF formula references `Rent Roll Input!V`, M3 first row VLOOKUP formula references `T12 Raw Data`, M4 SP variance formula references D column (implied rate), M5 residual formula references B column (computed delta), Sections K and L (rows 86-117) intact.

Migration verified end-to-end on:
- **Bundled v0.1.11 Analyzer** → migrates cleanly to v0.1.12, file size 180,003 → 183,103 bytes (+3,100 bytes, consistent with ~50 new rows of content)
- **User's populated Homestead workbook** (RR + T12 baked in) → same verification result; Section M installs cleanly alongside existing data

### Idempotency proven

Re-running the migration on an already-v0.1.12 file exits cleanly: `"Workbook is already at v0.1.12. No-op (will re-save)."` No double-installation, no formula corruption.

### Companion: UW-BACKLOG.md

This release introduces `UW-BACKLOG.md` at the repo root as the authoritative forward-looking list of underwriting workbook changes. Prior "Out of scope" / "Carry-forward" notes scattered across CHANGELOG-T12 and CHANGELOG-RR have been swept into 10 `BL-NNNN` entries. New items are added there; closed items move to the `Shipped` section but keep their IDs so cross-references remain stable.

The Section M work itself opens 4 new backlog items (BL-0001, BL-0003, BL-0004, BL-0007) — finer T12 Labels, RR Input expansion, T12 Analytics 2P reconciliation row, and the meal/scooter RR keyword widening. All are wired into Section M's conditional notes so the analyst sees them in-workbook when relevant.

### Out of scope (logged in UW-BACKLOG.md)

- **BL-0001**: Finer ancillary Labels in `Description_Map` (Meal Income, HK Income, Laundry Income, Scooter Fee Revenue, Transfer Fee Revenue). Substrate v0.2.0 territory — vocabulary expansion, not a patch.
- **BL-0003**: RR Input expansion for per-fee ancillary columns. Cross-cutting Track 1 + Track 3; ships as its own scoped PR.
- **BL-0004**: T12 Analytics 2P reconciliation row. Substrate v0.1.13 candidate.
- **BL-0007**: Meal / scooter / mobility / transport keyword additions in `_looks_care`. RR v1.16.2 patch candidate.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.12
- `tools/migration/migrate_to_v0112.py` — idempotent migration script
- `UW-BACKLOG.md` — **new file** at repo root; 10 initial entries swept from prior changelogs + this release
- `SPEC-T12.md` — current-version line bumped to v0.1.12; file inventory adds `migrate_to_v0112.py` row
- `SPEC-RR.md` — Track-versions inline line bumped (v0.1.11 → v0.1.12); Section M referenced in the Analyzer-source section
- `README.md` — versions table + migration script listing updated
- `CLAUDE.md` — substrate version bumped to v0.1.12; carry-forwards section condensed to point at UW-BACKLOG.md
- `CHANGELOG-T12.md` — this entry

---

## [Substrate template v0.1.11] — 2026-05-13

### Summary

Patch fix for a chart category-axis positioning bug introduced when the five `T12 Analytics` charts were added at substrate v0.1.8 (Branch 3 analytical coverage). All three axis-bearing charts (V1, V2, V4) had their category axis incorrectly positioned at `axPos="l"` (left) when it should be `axPos="b"` (bottom) for vertical column and line charts.

The bug visibly manifests on the V4 LineChart (T12 Revenue Trend): Excel can't reconcile two axes both claiming the left position and falls back to rendering the categories (month labels) as legend entries with no plot area. V1 (Occupancy stacked column) and V2 (Rate Dispersion clustered column) had the same bug technically but Excel tolerates BarChart axis ambiguity — they rendered correctly to the eye. This fix brings them to spec-compliance and removes the risk of stricter future Excel versions silently breaking them.

### What changed (migrate_to_v0111.py)

- **A. Chart category-axis position fix.** For each chart on `T12 Analytics` whose title matches V1 / V2 / V4, flip `x_axis.axPos` from `"l"` to `"b"`. The value axis (`y_axis.axPos`) is left at `"l"` — correct for vertical charts. V3 (Payer Mix doughnut) and V5 (AL Acuity Mix doughnut) have no axes and are skipped.
- **B. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.11`.

No new sheets, no new named ranges, no new formulas, no header changes. Three byte-level edits inside three chart XML files (l → b in `<catAx><axPos val="l"/>`) plus 14 cell stamps.

### Idempotency

Gate (`is_already_v0111()`) checks BOTH the version stamp AND that V4's `x_axis.axPos` already reads `"b"`. Re-runs on a partial-state file safely re-apply.

### Verification

6-check verification block: `Cover!B8` stamped, all 13 `AZ4` stamped, three target charts have catAx `"b"` (was `"l"`), valAx unmoved at `"l"`, V3 and V5 doughnuts still present (sanity).

Round-trip test against the v0.1.10 bundled Analyzer + the user-reported populated Homestead workbook: in both cases, all three target charts flip cleanly to `"b"`, the value axis stays at `"l"`, and the doughnut charts are untouched. File size delta on the bundled Analyzer: +10 bytes (3 axPos edits + 14 stamps) — confirms no other content was dropped or rewritten during the openpyxl save.

End-to-end smoke after applying the migration: parser pipeline produces a populated Analyzer whose `Description_Map` and formula sheets are unchanged from pre-migration. Re-opening the populated file in Excel renders V4 as a 12-point line chart with months on the X axis (was: empty plot + months as a vertical legend list).

### How this bug got introduced

When `migrate_to_v018.py` created the five charts at substrate v0.1.8, the chart construction code likely copied axis configuration from another chart type without adjusting `axPos`. The bug only surfaced when V4 (the LineChart) was actually populated with monthly trend data — V1 and V2 happened to render fine despite being equally wrong, so the issue stayed latent until a Homestead-with-T12 run hit V4 with real data.

### Out of scope (logged for v0.1.12+)

- The carry-forwards from v0.1.10 still stand: `Rent Roll Recon` section K PSF stats, T12 Analytics 2P reconciliation row, `Workbook Health` AR aggregation.
- V5's empty rendering on broker-format rent rolls (Homestead has no per-bed acuity tiers, so SUMIFS for Basic/Level 2-7 all return $0). Either accept that V5 is meaningful only when source has acuity, or rework V5 to fall back to "Care Level $ grouped by Care Type" for sources without acuity. Design decision, not a bug.

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — bundled Analyzer migrated to v0.1.11
- `tools/migration/migrate_to_v0111.py` — idempotent migration script
- `SPEC-T12.md` — current-version line bumped, file inventory updated
- `SPEC-RR.md` — Track-versions inline line bumped (substrate v0.1.10 → v0.1.11)
- `CHANGELOG-T12.md` — this entry; also corrected header line's stale Track 1 reference (was v1.11.0; now v1.16.1)

---

## [Substrate template v0.1.10] — 2026-05-11

### Summary

Track 3 companion to RR v1.16.0 (Track 1 data-capture expansion). Adds 7 new column headers to `Rent Roll Input` row 4 at columns V-AB, after the existing T-U formula columns. Extends the `Total Monthly Rev` formula at `U7:U606` to include the new 2nd Person Rent column. No new sheets, no new named ranges, no rewiring of existing aggregators — purely a column-extension of the existing Rent Roll Input schema.

### What changed (migrate_to_v0110.py)

- **A. New headers at Rent Roll Input row 4 cols V-AB**, styled to match the existing navy `FF1F3864` header row:
  - V: `2nd Person Rent $` (Tier 1.2 — RR ↔ T12 2P reconciliation enabler)
  - W: `Move-out Date` (Tier 2.1 — vacate forecasting)
  - X: `Balance` (Tier 2.2 — bad-debt indicator)
  - Y: `Notes` (Tier 2.3 — free-form context)
  - Z: `Market PSF` (Tier 3.1)
  - AA: `Actual PSF` (Tier 3.1)
  - AB: `ACH` (Tier 3.2 — collection-velocity flag)
- **B. Total Monthly Rev formula extension at U7:U606:**
  ```
  =IFERROR(H{r}+IFERROR(I{r},0)+T{r},0)
    -> =IFERROR(H{r}+IFERROR(I{r},0)+T{r}+IFERROR(V{r},0),0)
  ```
  Adds `+V{r}` (2nd Person Rent) to the per-resident total. 2P is incremental housing revenue and was previously excluded — without this fix, V would be populated but never flow into TMR or downstream aggregators that read U.
- **C. Stamp** `Cover!B8` and all 13 anchor `AZ4` cells to `v0.1.10`.

### Idempotency

Gate (`is_already_v0110()`) checks BOTH the version stamp AND that the row-4 V header is present. The formula-update step gates on the exact old-pattern match per row, so cells with customized formulas are left untouched on re-run.

### Verification

5-check verification block: Cover!B8 stamped, all 13 AZ4 stamped, 7 new headers present at V-AB, TMR formula extended in sample rows (DATA_START / mid / DATA_END), existing A4 header (`Unit #`) intact.

End-to-end smoke against the Homestead fixture: RR v1.16.0 → translate → populate v0.1.10 Analyzer → Sandra & Darryl Owens row 19 has V=$650 (2P) + O=$100 (H/K) = $750 total, Notes captured ("HK $100 eff 3/1- sec occ $650"), Move-in Date 2026-02-23, Market PSF 8.12, ACH "X", and U19 formula correctly references V19.

### Out of scope (logged for v0.1.11+)

- `Rent Roll Recon` section K (IL deep-dive at rows 86-100) could surface PSF stats now that the substrate has those columns. Small addition (2-3 cells).
- `T12 Analytics` could add a new row that reconciles `SUM('Rent Roll Input'!V) × 12` (RR-projected 2P annualized) against `T12 Raw Data!2nd Person Revenue` (T12 actual). Same shape as Section B revenue reconciliation. Useful enhancement.
- `Workbook Health` could aggregate `Balance` column as a total-AR validation. Useful but not blocking.

### Carry-forwards opened

None blocking. The three items above are nice-to-haves that don't gate any downstream UW work.

---

## [Substrate template v0.1.9] — 2026-05-11

### Summary

Bug fix on top of v0.1.8. Two issues surfaced when a user opened the substrate-v0.1.8 populated Analyzer in Excel: (a) the period-selector dropdown on `Rent Roll Recon!B2` rendered empty, and (b) the cell didn't auto-populate the latest period. Same root cause behind both: `RR_Calc!A2:A13` (the dropdown source + the v0.1.8 LOOKUP target) was pre-populated with `_xludf.minifs(...)` formulas. The `_xludf.` prefix is a Google Sheets / LibreOffice user-defined-function marker that Excel does not recognize as a function name — every cell resolved to `#NAME?`, the `IFERROR(..., "")` wrapper returned `""`, and my v0.1.8 LOOKUP-against-RR_Calc found no numeric value to return.

### What changed

**Migration script — `tools/migration/migrate_to_v019.py`:**

- **A. Drop `_xludf.` prefix from 12 cells in `RR_Calc!A2:A13`** — `_xludf.minifs(...)` → `MINIFS(...)`. Excel-native MINIFS evaluates these correctly; the dropdown now populates with the sorted unique period dates and the chain feeds downstream cells as designed.
- **B. Rewrite `Rent Roll Recon!B2` formula** to read directly from `Rent Roll Input!$S$7:$S$606` via `MAX`, dropping the transitive dependency on RR_Calc. Belt-and-suspenders — if RR_Calc ever drifts again, B2 still works:
  ```excel
  =IF(MAX('Rent Roll Input'!$S$7:$S$606)>0,MAX('Rent Roll Input'!$S$7:$S$606),"")
  ```
  Data validation on B2 (the dropdown sourced from RR_Calc) is left in place — now that RR_Calc evaluates correctly, the dropdown lets analysts override to an earlier period.
- **C. Stamp `Cover!B8` and all 13 anchor `AZ4` cells to v0.1.9.**

Idempotent — `is_already_v019()` gate checks both the version stamp AND that no `_xludf` prefix remains in RR_Calc, so the migration safely re-applies on partial-state files. 6-check verification block confirms: Cover B8 stamped, all 13 AZ4 stamped, zero `_xludf` remaining workbook-wide, RR_Calc!A2 uses native MINIFS, B2 references direct MAX on Rent Roll Input!S, B2 data validation intact.

### Why this is in scope

Analogous to the v0.1.6 H20 `_xlfn._LONGTEXT` chunked-literal repair (Cluster A correctness fix). The architectural constraint of "additive only" is preserved — these are formula-text repairs on broken formulas, not a rewrite of an aggregator's logic. RR_Calc's intent (produce sorted unique period dates) is unchanged; only the Excel-incompatible function-name prefix is removed.

### Files

- `tools/migration/migrate_to_v019.py` — new migration script.
- `ALF_Financial_Analyzer_Only.xlsx` — bundled regenerated at v0.1.9.
- `SPEC-T12.md`, `CLAUDE.md`, `OPTIMIZATION-DECISIONS.md`, `journal.md` — current-version refs + new design entry / decision / session note.

### Verification

- 6-check migration verifier: all green on first clean run, idempotent re-run is a no-op.
- Functional smoke: load v0.1.9 bundled Analyzer, populate via `analyzer_rr_writer.populate_t12()` with 4 rows at period 04/24/2026, confirm the saved file has `Rent Roll Recon!B2` formula referencing `MAX('Rent Roll Input'!$S$7:$S$606)` and zero `_xludf` anywhere. (Excel-side calculation of the formula confirmed manually against the user's reported repro.)

### Carry-forwards opened by this round

- **None.** This is a pure bug fix that closes the user-reported issue. Branch 2 (Handoff readiness) remains the next open Analyzer-optimization workstream.

---

## [0.2.1] — 2026-05-11

### Summary

Track 2 follow-up to substrate v0.1.8 Branch 3 analytical coverage: the T12 Analyzer writer (`t12_normalizer_writer.populate_t12_input`) now stamps the property name into `T12 Input!A10`, derived from the uploaded T12 filename. Closes the Track 2 carry-forward opened by substrate v0.1.8. T12 Analytics!B2 (3-priority RR → T12 → Cover) now sees A10 populated when a T12 is uploaded — so if no RR is uploaded for the same property, B2 falls through to the T12-derived name instead of the Cover!B5 default.

### What changed

**Writer — `t12_normalizer_writer.py`:**
- New `from property_name import derive_property_name` import (shared cross-track utility introduced in RR v1.15.0).
- `populate_t12_input()` already received `source_filename` — that path is now extended: when non-empty, the derived property name is written to `T12 Input!A10` after the GL detail rows. Empty filename or empty derivation leaves A10 untouched.
- Step numbering in the function body shifted: prior Step 4 (Description_Map append) and Step 5 (Run_Info upsert) become Steps 5 and 6; new Step 4 is the property-name stamp.
- Idempotent: each call rewrites A10 from the new T12 file's derived name. Matches the existing "writer manages the T12 Input sheet" contract.

**App — `app.py`:**
- `T12_VERSION = "0.2.1"` (was 0.2.0); `T12_LAST_UPDATED = "2026-05-11"`.
- No call-site change needed — `populate_t12_input()` already received `source_filename`; the new behavior consumes it.

**Docs:**
- `SPEC-T12.md` — Current version line bumped to v0.2.1; brief note in the parser/writer section about the A10 stamp.
- `CHANGELOG-T12.md` — this entry.
- `CLAUDE.md` — Track 2 follow-up carry-forward marked closed; current T12 version bumped to v0.2.1.

### Verification

In-process smoke test (`_smoke_t2.py`, not committed) covers the end-to-end pipeline through both writers:
1. RR + T12 uploaded with same filename property prefix → A3 and A10 both populated with the derived name.
2. RR + T12 from different uploads → A3 from RR-derived, A10 from T12-derived (RR wins in B2 by 3-priority order).
3. T12 only (no RR) → A3 empty, A10 populated.
4. Empty `source_filename` → A10 untouched.
5. T12 Analytics B2 formula still resolves cleanly through the 3-priority chain.

### Why this is Track 2 (not Track 3)

Same logic as the RR v1.15.0 commit: substrate cell reservation was Track 3 work (substrate v0.1.8); stamping content into that cell from a parser-side filename is application logic — Track 2 territory. Bundled into the same chat as Track 1 per user authorization on 2026-05-11.

---

## [Substrate template v0.1.8] — 2026-05-11

Branch 3 of the Analyzer optimization roadmap (analytical coverage). All edits additive — new formulas in currently-empty cells (`T12 Analytics!B2`/`E2`), new chart objects on currently-empty `T12 Analytics!K1:V44`, and two new sections appended at the bottom of `Rent Roll Recon` (rows 86-117). No existing aggregators rewired. Workbook-only — no code changes to `t12_normalizer.py` / `t12_normalizer_writer.py` / `analyzer_rr_writer.py` / `app.py`. Design captured in `OPTIMIZATION-DECISIONS.md` decisions D-15 through D-22.

### What changed (Track 3 — workbook substrate)

**Property name + period plumbing** (closes F-9, F-10, F-11 from the 2026-05-11 grounding inspection):
- Reserved single-cell property-name value targets: `Rent Roll Input!A3` and `T12 Input!A10`. No separate labels — the cell location itself is the documented contract. Until Track 1/2 writer follow-ups land, these cells are analyst-paste; the analyst types once and T12 Analytics!B2 picks it up.
- Rewired `T12 Analytics!B2` from `=Property_Name` to a 3-priority formula: `Rent Roll Input!A3` → `T12 Input!A10` → `Property_Name` (Cover!B5). Until writer follow-ups land, behavior identical to before — `Property_Name` is the only populated source.
- Installed `T12 Analytics!E2` rightmost-populated-month formula: `=IFERROR(LOOKUP(2,1/('T12 Input'!$C$11:$N$11<>""),'T12 Input'!$C$11:$N$11),"")`. Partial-year safe. Named range `T12_Period_Date` now resolves; Workbook Health row 26 auto-validates.

**Property snapshot visuals on T12 Analytics** (closes F-13):
- 5 chart objects at `K1:V44` (industry-standard senior-housing UW visual set per CBRE / NIC MAP research):
  - V1 — Occupancy by Care Type (stacked column, IL/AL/MC × Occupied/Vacant/Notice/Eviction)
  - V2 — Rate Dispersion (clustered column, 5 rate bands × IL/AL/MC three-series)
  - V3 — Payer Mix (doughnut, 7 payer types as % of total monthly revenue)
  - V4 — T12 Revenue Trend (line, 12 months of total operating revenue)
  - V5 — AL Acuity Mix (doughnut, Basic/Level 2-7 distribution)
- 5 conditional formula-driven note cells at `K15`/`K30`/`P15`/`P30`/`K45` — context messages that update with the underlying data (e.g. "⚠ Medicaid revenue share 35% — reimbursement rate risk" only fires when Medicaid > 30%).
- Hidden helper block at `K46:V52` for rate-bucket counts (V2 source) and at `K53:V54` for monthly revenue totals (V4 source). Bucket boundaries: $0-1,999 / $2,000-3,999 / $4,000-5,999 / $6,000-7,999 / $8,000+. Revenue source: `SUMIFS('T12 Raw Data'!F:F..Q:Q, A:A, "Revenue")` — sums all Revenue-section rows per month.

**Rent Roll Recon period default + dropdown** (closes F-11):
- `Rent Roll Recon!B2` set to `=IFERROR(LOOKUP(9.99E+307,'RR_Calc'!$A$2:$A$13),"")` — returns the latest date from the ascending-sorted period list.
- Data validation list on B2 sourced from `RR_Calc!$A$2:$A$13`. Analyst can override via dropdown; once overridden, the formula is replaced by the static date (standard Excel behavior). Re-running the migration restores the formula default — flagged as expected idempotency side effect.

**Rent Roll Recon section K — IL Unit-Type Mix, Size & Rate Dispersion** (closes F-14):
- New section at rows 86-100 (append, not insert — avoids openpyxl `insert_rows()` formula-text quirk).
- Columns: Unit Type / Count / % of IL / Avg Rate / Min Rate / Max Rate / Avg Sq Ft / $/Sq Ft.
- Apt-type breakouts: Studio / 1 Bedroom / 2 Bedroom / Cottage / Villa / Other (filter on `Rent Roll Input!F`).
- Summary rows: rate spread (max − min), CV proxy ((max − min) ÷ avg ÷ √12), avg sq ft, sq ft range, $/sq ft.
- Conditional note at A100: flags wide IL rate dispersion (CV > 25%) as possible legacy in-place rates.

**Rent Roll Recon section L — MC Care Structure auto-detect** (closes F-15):
- New section at rows 102-117.
- B103 pattern detector: counts distinct populated K-column values among occupied MC residents and classifies as Flat-rate / Tiered / Fee-for-service.
- Tier mapping (rows 106-108): substring match on K values — Basic/Tier 1/Level 1 → Tier 1, Moderate/Tier 2/Level 2-3 → Tier 2, Advanced/Tier 3/Level 4-7 → Tier 3. Row 109 (Other / unmapped) catches FFS.
- Summary rows: avg base rent / resident, avg care charge / resident, care charge ÷ base rent ratio (flag if > 30%), total MC monthly revenue.
- Conditional note at A117: pattern-specific guidance — "Flat-rate MC detected.", "Tiered MC detected. Verify per-tier staffing model.", or "Fee-for-service MC detected. Review individual care plans for sustainability."

**Substrate version stamp** `v0.1.7 → v0.1.8` (`Cover!B8`, all 13 anchor `AZ4` cells).

### Files

- `tools/migration/migrate_to_v018.py` — new migration script. 10 operations, 17-check verification block. Re-run on a v0.1.8 file is a no-op via the `is_already_v018` guard.
- `ALF_Financial_Analyzer_Only.xlsx` — bundled regenerated at v0.1.8.
- `OPTIMIZATION-DECISIONS.md` — added Branch 3 design (Clusters B3.1-B3.5), discovered facts F-9 through F-15, decisions D-15 through D-22.
- `SPEC-T12.md` — Current Template substrate version line bumped; v0.1.8 entry appended to substrate history.
- `CHANGELOG-T12.md` — this entry.
- `CLAUDE.md` — version line, last-updated, carry-forward updates.
- `journal.md` — session entry.

### Carry-forwards opened by this round

- **Track 1 follow-up — RR writer stamp.** Modify `writer.py` to write the parsed property name into `Rent Roll Input!A3`. Until this lands, A3 is analyst-paste only and T12 Analytics B2 continues to fall back to Cover!B5.
- **Track 2 follow-up — T12 writer stamp.** Same idea for `t12_normalizer_writer.py` → `T12 Input!A10`.
- **Branch 2 — Handoff readiness** remains open per the Track 3 roadmap (UW Export mirror, pre-export gate, metadata header).

### Verification

`tools/migration/migrate_to_v018.py` 17-check block: Cover!B8 = v0.1.8, all 13 AZ4 stamped, B2 3-priority formula references RR Input A3 + T12 Input A10, E2 LOOKUP formula present, 5 chart objects on T12 Analytics, helper rate-bucket block populated, helper V4 monthly revenue row populated, 5 conditional note cells present, Rent Roll Recon B2 formula + DV present, IL section K header at A86, IL total row at B93, MC section L header at A102, MC pattern detector at B103, RR Input A3 reserved (no leftover label), T12 Input A2 cleared (A10 is the writer target), all named ranges intact. Idempotent — re-run on v0.1.8 file is a no-op via gate that checks both `Cover!B8` and the corrected B2 formula text.

Cell scan over all 13 sheets confirms zero formula error strings (`#NAME?` / `#REF!` / `#VALUE!` / `#DIV/0!` / `#N/A` / `#NUM!` / `#NULL!`) introduced.

---

## [0.2.0] — 2026-05-08

Adds `BrokerFinancialSummaryFormat` (third T12 format) and Cluster B robustness hooks (sign-convention guards + partial-year T12 detection). Closes the v0.1.6 carry-forward documented in OPTIMIZATION-DECISIONS.md D-12 and the BrokerFinancialSummaryFormat carry-forward from journal 2026-05-06.

### Added

- **`BrokerFinancialSummaryFormat`** — third T12 format alongside Yardi and MRI.
  - **Detection:** A4 contains `Historical Performance` (case-insensitive). When multiple sheets match, picks the first (matches Homestead's `Summary` over `P&L-Dumps`).
  - **Column selection:** broker files may have 12 to 54+ datetime cells in row 4 (Homestead has 39 across CY / T12 / T6M / T2M / T1M sections). Parser walks row 4 right-to-left and returns the **rightmost contiguous monotonic monthly run** (≤12 cells). For Homestead Summary that picks cols AB:AM (Apr 2025 → Mar 2026, the T12 block); for March_2026 single-sheet it picks B:M.
  - **Banner-prefix disambiguation.** Each section banner (col A text + all 12 monthly cells truly None) becomes the prefix for the next GL rows: `Direct Care | Payroll - Wages` vs `Marketing | Payroll - Wages`. Subtotal rows pop the sub-banner back to the top-level "Revenues" so siblings (`Concessions`, `Respite Revenue`, `Move-In Fees`, `Other Income`) emit unprefixed.
  - **Pre-financial preamble drop.** Drops everything before the first banner matching `Revenue` / `Revenues` (filters Census / ADC / Room Rates summaries).
  - **Post-P&L cutoff.** Stops on banners matching `Non-Operating` / `Wages Analysis` / `Payroll Summary` (drops below-NOI items + broker analytical sections).
  - **Standard signs.** No per-format sign override; revenue +, expense +, concessions − (matches Yardi/MRI).
  - **Total computed locally.** Broker "Totals" column (when present at col 14 of March_2026 or col 40 of Homestead) is ignored; parser sums the 12 monthly values.
- **`_check_sign_convention(gl_rows)`** — Cluster B B-1. Returns warnings for descriptions containing `CONCESSION` (suffix-only match — banner-name keyword false-positives suppressed) with positive totals. Defensive; doesn't fire on any of the four verified fixtures.
- **`_count_populated_months(gl_rows)`** — Cluster B B-2. Counts how many of the 12 month columns have at least one non-zero GL value across all rows. Drives partial-year detection downstream.
- **`_annualize_rows(gl_rows, populated_months)`** — pure-Python annualizer. Multiplies monthly + total by 12/N.
- **`parse_t12(..., annualize_partial_year: bool = False)`** — new optional kwarg. Controlled by the app's sidebar checkbox; when `True` and `populated_months < 12`, parser scales values before returning.
- **`T12ParseResult` fields** — `sign_warnings: List[str]`, `populated_months: int`, `was_annualized: bool`. Backwards-compatible (positional args unchanged).
- **`tools/verify_t12_v020.py`** — parser-side end-to-end harness covering all four reference fixtures with deterministic checks (format detection, GL row count, source $, populated months, implied NOI for broker, sign-warning + UNMATCHED counts). Substrate-level EGI / EBITDARM unchanged from v0.1.6 — workbook formulas are untouched, so v0.1.1's verified $2,201,865 (Salem) / $3,763,229 (Briar Glen) continue to hold.

### Changed

- **`GRAND_TOTAL_PREFIXES`** extended with `SUBTOTAL,` and `SUBTOTAL ` (broker convention catches `Subtotal, Room & Board`, `Subtotal, Care Level`, etc.).
- **`EXPLICIT_DROP_LIST`** extended with `NOI on Statement` and `Check` (broker-specific summary lines that aren't GL detail).
- **`app.py`** — sidebar gets an "Annualize partial-year T12" checkbox (disabled until a T12 is uploaded). T12 status panel surfaces partial-year warning when `populated_months < 12`, and lists every `sign_warning`. Period-label display tolerates partial-year padded-empty labels. Version pill shows `T12 v0.2.0`.

### Verified end-to-end (2026-05-08)

All four fixtures parse against the v0.1.7 Description_Map (after Phase 4 substrate appends):

| Fixture | Format | GL rows | UNMATCHED | Months | Implied NOI / Source $ |
| --- | --- | ---: | ---: | ---: | ---: |
| Salem | Yardi (Income to Budget) | 73 | 0 | 12 | source = $4,249,047.98 |
| Briar Glen | MRI R12MINCS | 91 | 0 | 12 | source = $8,306,657.64 |
| Homestead Pensacola | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 (broker NOI to the penny) |
| March 2026 | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 |

Both broker fixtures share identical T12 data (101 unique parser-produced descriptions, $12,592,590 source); they differ only in workbook layout (Homestead is multi-section dashboard, March_2026 is single-sheet T12).

### Notes

- **Banner-prefix is always-on for broker files.** The parser does not consult Description_Map to decide whether to prefix. Phase 4 substrate v0.1.7 ships 99 prefixed Description_Map entries to make Homestead/March_2026 zero-UNMATCHED end-to-end. Future operators may need similar substrate vocabulary additions.
- **Salem's source $ now includes Management Fees** ($131,579.65 — fixed in v0.1.1) — unchanged at v0.2.0.
- **Cluster B partial-year detection counts MONTH columns with any non-zero GL value.** A row of zeros in March doesn't count March as populated, but a row of -$1 in March does.

---

## [Substrate template v0.1.7] — 2026-05-08

Workbook-side companion to T12 code v0.2.0. Closes the substrate carry-forwards from v0.1.6 (R102 lease formula, N501→N500 cosmetic, Cluster B partial-year row) and ships the Description_Map vocabulary needed to make Homestead / March_2026 broker fixtures zero-UNMATCHED end-to-end.

### Fixed

- **`T12 Analytics!E102` (Lease / ground lease)** — was `=0` placeholder per v0.1.4 plan that never landed. Replaced with `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`. Sibling `F102` set to `=E102`. UW Output R61 (Lease) now displays real values when source has lease data, instead of $0.
- **`T12 Raw Data` SUMIFS range mismatch** — 636 formula cells had `T12_Calc!$X$1:$X$501` (legacy from v0.1.5 row insert). Swept to `$X$1:$X$500` to match T12_Calc's actual 500-row data area. Cosmetic; T12_Calc row 501 reads empty either way, so no $ effect.

### Added

- **`Workbook Health!A30` — V8 partial-year T12 validation row.** Formula: `=COUNTA('T12 Input'!C11:N11)` paired with `=IF(B30=12,"✓","⚠")`. Surfaces partial-year T12s alongside V1-V7 in the existing Validation section (replaces the formerly-blank gutter row 30 between Validation and Diagnostics).
- **99 Description_Map entries (Homestead vocabulary).** Mechanically derived from the populated_analyzer's v0.1.5 Option-C work: for each parser-produced unique broker description, its suffix-Label mapping is inherited (e.g., `Direct Care | Payroll - Overtime → Overtime wages`, `Utilities | Electric → Utilities`, `Marketing | Payroll - Wages → Administrative labor`). All 99 map cleanly to the existing 54-Label closed vocabulary. After this addition, both Homestead Pensacola and March_2026 broker fixtures parse with **zero UNMATCHED descriptions**.

### Changed

- **Substrate version stamp** `v0.1.6 → v0.1.7` (Cover!B8, all 13 anchor `AZ4` cells).

### Migration script

- **`tools/migration/migrate_to_v017.py`** — idempotent. Operations: apply lease formula at E102/F102 → sweep $501→$500 across T12 Raw Data → add V8 partial-year validation row → append 99 Description_Map entries (skipping any already-present keys) → stamp version cells → run 7 verification checks.

### Verified end-to-end (2026-05-08)

- Migration ran clean against v0.1.6 bundled `ALF_Financial_Analyzer_Only.xlsx`. All 7 verification checks pass.
- Re-run (v0.1.7 → v0.1.7) is a no-op via the `is_already_v017` guard.
- Description_Map row count grows from 311 → 410 (311 existing + 99 new).
- All four reference fixtures (Salem, Briar Glen, Homestead, March_2026) produce 0 UNMATCHED when parsed against the v0.1.7 substrate.

---

## [Substrate template v0.1.6] — 2026-05-07

Workbook-side optimization round per OPTIMIZATION-DECISIONS.md (Branches 1 + 4 of the optimization mind map). Cluster B (sign-convention guards, partial-year T12 handling) is code-side and ships separately on Track 2.

### Added

- **Cover sheet** at first tab position. Carries property name, substrate version, RR / T12 normalizer version pills, repo + app links, and a short About block. Property name lives canonically at `Cover!B5` and propagates via the new `Property_Name` named range.
- **Workbook Health sheet** at last position, hidden by default. Three sections: Workbook Map (formula-driven from per-sheet anchor cells), Validation (7 live $ checks), Diagnostics (capacity utilization, version pills, last-open timestamp).
- **Per-sheet anchor cells** at `AZ1:AZ5` on all 13 sheets — purpose / category / visibility / version / notes. Drives the Workbook Map section. AZ5 (notes) left empty by default.
- **5 named ranges**: `RR_Period_Date` (`Rent Roll Recon!B2`), `T12_Period_Date` (`T12 Analytics!E2`), `RR_Input_Data` (`Rent Roll Input!A7:S606`), `T12_Input_Data` (`T12 Input!A12:O511`), `Property_Name` (`Cover!B5`). Joins the existing two (`DescMap_Description`, `DescMap_Label`).
- **Light cell comments** on 5 hardest-to-decode formula cells: `Monthly Trending!B5` (T12 rollup INDEX/MATCH pattern), `T12 Analytics!E37` (GPR), `T12 Analytics!E52` (EGI), `T12 Analytics!E110` (EBITDAR after mgmt fee), `Rent Roll Recon!H20` (RR↔T12 gap diagnostic).

### Fixed

- **`Rent Roll Recon!H20` `#NAME?` error** — the diagnostic message cell that interprets the RR-vs-T12 base rent gap was broken in every populated workbook because its 5-item investigation lists exceeded Excel's 255-char-per-literal cap and got serialized as `_xlfn._LONGTEXT(...)` calls Excel doesn't recognize. Rewritten with chunked literals (each ≤255 chars, joined with `&`). Same four-case logic, same message content, parses clean. Cell now displays its intended diagnostic instead of `#NAME?`.
- **UW Output R29 (Bonus wages)** — formula gap. `B29:D29` set to `"-"`, `E29` and `F29` now point at `T12 Analytics!E64`/`F64` (sibling-pattern fill).
- **UW Output R57 (Bad debt expense)** — same gap pattern. Filled to point at `T12 Analytics!E98`/`F98`.
- **UW Output R61 (Lease / ground lease)** — was fully empty including `G61` variance. Filled to point at `T12 Analytics!E102`/`F102` (currently `=0` placeholder; see deferred bug below). Indent fixed (0.0 → 1.0) to match siblings R60 / R62.
- **`T12 Analytics!B2` (Property name)** — wired to `=Property_Name`. Was empty; now propagates from Cover sheet input.

### Changed

- **Substrate version** stamp `v0.1.5 → v0.1.6` (Cover!B8, all 13 anchor AZ4 cells).

### Deferred

- **`T12 Analytics!R102`** still `=0` placeholder. Replacing with the planned INDEX/MATCH against `T12 Raw Data!B:B` for "Lease / ground lease" requires rewiring an existing aggregator, which was out of scope for this round per the architectural constraint. Result: `UW Output!R61 Lease` displays `$0` until v0.1.7 picks this up. Tracked in OPTIMIZATION-DECISIONS.md A-5.
- **`T12 Raw Data` SUMIFS range cosmetic mismatch** — some shifted rows still reference `$N$1:$N$501` instead of `$N$1:$N$500` (artifact of the v0.1.5 migration). Harmless; same-as-before. Logged for next migration that touches the range.

### Migration script

- **`tools/migration/migrate_to_v016.py`** — idempotent. Operates in order: add Cover sheet → apply Cluster A formula fixes → add Workbook Health sheet → populate AZ anchor cells on all 13 sheets → add 5 named ranges → wire `T12 Analytics!B2` → add cell comments → verify (11 checks).

### Verified end-to-end (2026-05-07)

- Migration runs clean on `ALF_Financial_Analyzer_Only.xlsx` (empty v0.1.5 template).
- Re-running on a v0.1.6 file is a no-op (idempotency works).
- LibreOffice recalc of the migrated empty template produces **0 formula errors** across all 13 sheets.
- `Rent Roll Recon!H20` resolves to `"Gap = $0 — RR and T12 are perfectly aligned."` (case 1 of 4) on the empty template — was `#NAME?` before.
- Workbook Health Map section pulls correctly from all 13 anchor cells via formula refs.
- Validation section fires `⚠` on missing RR/T12 period dates and Property name (correct behavior on an empty template).

### Notes

- Three openpyxl quirks worth flagging for future migrations on this workbook:
  1. `wb.defined_names[name] = DefinedName(...)` is the v3.x assignment form — `defined_names.append()` was removed.
  2. Empty-string cell values render as `0` in Excel/Calc when read back. Preferred: leave the cell truly unset (skip the assignment) rather than write `""`. Workaround in formula context: wrap with `=IF(ref="","",ref)`.
  3. `Cell.alignment` is read-only; to mutate one attribute (e.g. indent) re-assign the whole `Alignment(...)` object preserving the others.

---

## [Substrate template v0.1.5] — 2026-05-04

Substrate-only change (no code release). Adds one new Label, `2nd Person Revenue`, to the closed vocabulary (54 → 55 Labels). Migration script `migrate_to_v015.py` applies idempotently to any v0.1.4 Analyzer.

### Why

Surfaced on Homestead Pensacola broker file (2026-05-04). Broker reported second-occupant revenue as three separate line items by care type (`Second Persons Revenue | Independent Living`, `... | Assisted Living`, `... | Memory Care`). v0.1.4 substrate had no Label for this — collapsing into `Base rent — IL/AL/MC` would inflate the per-bed base rate (Base rent ÷ ADC). At Homestead the inflation was modest ($43/bed/mo on AL is the largest), but the principle is right: a second occupant generates additional revenue at a fixed rate, separate from base rent. Per-bed base rate calculations now stay clean.

### Changed

- **T12 Raw Data**: new row at R15 `2nd Person Revenue` (was Other community revenue). Helper SUMIF formulas across F:Q reference T12_Calc!N matching the new Label string. Col R `=SUM(F15:Q15)`. Old R15+ shifted down by 1.
- **Monthly Trending**: new row at R19 `2nd Person Revenue` (was Other community revenue). Col B uses standard `=IFERROR(INDEX('T12 Raw Data'!F:F,MATCH("2nd Person Revenue",'T12 Raw Data'!B:B,0)),0)` pattern with month-equivalent formulas across C:M. Col N `=SUM(B19:M19)`. EGI formula at (post-shift) R21 rewritten from `=B8+B10+B11+B15+B16+B17+B18+B19` to `=B8+B10+B11+B15+B16+B17+B18+B19+B20` — adds the new R19 (2nd Person) to the sum while preserving Total base rent (R8) clean. Old R19+ shifted down by 1.
- **T12 Analytics**: 4 cells (E38, H38, E39, E40) patched to follow Physical Vacancy and Loss to Lease references as they shifted from `T12 Raw Data!$R$55/$R$56` → `$R$56/$R$57`.
- **Description_Map**: no schema changes. New Label becomes referenceable when descriptions map to it; vocabulary lookup unaffected.

### Migration mechanics

Three openpyxl quirks discovered and worked around in `migrate_to_v015.py`. Documenting here because the same patterns will apply to any future Label-insert substrate change:

1. **`insert_rows()` shifts cell positions but does not update formula text.** 684 cells in T12 Raw Data and 145 cells in Monthly Trending have formulas referencing rows >= insert point that all need explicit row-ref updates. Plus 4 external refs in T12 Analytics. Solution: full-workbook formula sweep with regex-based row shifting, handling both qualified (`'Sheet'!A19`) and unqualified (`B19`) refs, including range endpoints (`F15:Q15`).
2. **Range-endpoint refs need the lookbehind regex to allow colons.** Initial pattern `(?<![A-Za-z_!:])` excluded the second endpoint of a range like `F15:Q15` because `:` was in the lookbehind. Fix: `(?<![A-Za-z_!])` — drop the colon — so both endpoints get shifted.
3. **`insert_rows()` does not shift merged-cell range definitions.** The original substrate has `A21:N21` (LABOR section header) merged. After insert at R19, the LABOR text moves to R22 but the merge range still says A21:N21 — and the row that shifted into R21 (the EGI subtotal) ends up *inside* the stale merge range, causing Excel to silently drop its non-A column values on save (merged cells only keep the top-left value). **Critical: don't fix this with `unmerge_cells()` then `merge_cells()` with new addresses.** That triggers openpyxl's unmerge logic which clears the non-top-left cells of the merge — but those cells now hold real shifted content, which gets wiped. Fix: use the merge range's `shift(row_shift=delta)` method to mutate bounds in-place without unmerge.

### Verified end-to-end (2026-05-04)

Homestead Pensacola repopulated against v0.1.5 substrate:

| Metric | Result | Target | OK |
| --- | ---: | ---: | --- |
| GL rows written | 101 | 101 | ✓ |
| UNMATCHED descriptions | 0 | 0 | ✓ |
| Source $ → Operating $ leakage | $0.00 | $0.00 | ✓ |
| R8 Total base rent (CLEAN, no 2nd person) | $6,951,136.46 | $6,951,136.46 | ✓ |
| R19 2nd Person Revenue (NEW, isolated) | $32,220.49 | $32,220.49 | ✓ |
| R21 EFFECTIVE GROSS INCOME | $7,001,956.79 | $7,001,956.79 | ✓ |
| R69 EBITDARM | $1,761,421.43 | $1,761,421.43 | ✓ |
| R70 EBITDAR (= broker NOI on Statement) | $1,411,323.58 | $1,411,323.58 | ✓ |

### Files changed

- `ALF_Financial_Analyzer_Only.xlsx` — migrated to v0.1.5 substrate
- `migrate_to_v015.py` — migration script (idempotent; detects `2nd Person Revenue` in T12 Raw Data and exits if already applied)
- `SPEC-T12.md` — updated current-version line and Template substrate section
- `CHANGELOG-T12.md` — this entry

Pre-existing `Rent Roll Recon!H20` `#NAME?` is **not** introduced by this migration; it's a substrate-level issue documented in [0.1.0]. Migration verified against an empty v0.1.4 substrate (recalc: 0 errors, 10,953 formulas all evaluate clean).

---

## [0.1.1] — 2026-05-02

Patch release. Fixes a Yardi-extractor bug that silently dropped Salem's $131,579.65 Management Fees line. Briar Glen and the rest of the v0.1.0 verification numbers are unaffected.

### Fixed

- **`t12_normalizer.py` — Yardi extractor no longer requires a numeric account #.** v0.1.0's `YardiIncomeToBudgetFormat.extract()` required col A to contain a numeric account number on every GL row, applied *before* the three drop-rules. This was a defensive guard against picking up section headers and subtotals, but it was too strict: Yardi sometimes reports single-line expenses (notably property-management fees) as section-banner-style rows with no account number, and v0.1.0 silently dropped them. The check is removed; the three drop-rules (no $, grand-total pattern, explicit drop-list) are sufficient on their own. Account # is still preserved when present (most rows) and stored as `""` when absent. Format **detection** in `YardiIncomeToBudgetFormat.detect()` still uses the "≥3 numeric account #s in body" heuristic — that's about identifying which file is a Yardi T12, not which rows to keep.
- **`t12_normalizer.py` — added `Non-Operating Expenses` to the explicit drop-list.** Yardi's "Non-Operating Expenses" appears twice in Salem's source: once at row 134 as a section header (col O blank, caught by drop-rule 1) and once at row 137 as a subtotal of the preceding GL rows (col O = $45,161.67, but no `TOTAL` prefix so drop-rule 2 misses it). Without this fix, removing the account-# filter would have caused row 137 to double-count rows 135 (`Depreciation Expense`) and 136 (`Other Non Operating Revenue & Expense`). Added per the spec's documented pattern: "New non-operating descriptions added to this list when encountered."

### Verified end-to-end (2026-05-02)

Salem now reconciles to source on every line. Briar Glen unchanged.

| Metric | Salem (Yardi) | Briar Glen (MRI) |
| --- | ---: | ---: |
| GL rows written | 73 (was 72 at v0.1.0) | 91 (unchanged) |
| UNMATCHED at parse | 0 ✓ | 0 ✓ |
| Source $ | $4,249,047.98 (v0.1.0: $4,117,468.33; +$131,579.65 management fee) | $8,306,657.64 (unchanged) |
| Operating $ (T12 Raw Data total) | $4,205,759.14 (v0.1.0: $4,074,179.49; +$131,579.65) | $8,310,006.39 (unchanged) |
| Depreciation — EXCLUDED $ | $43,288.84 (unchanged) | -$3,348.75 (unchanged) |
| Leakage | $0.00 ✓ ZERO | $0.00 ✓ ZERO |
| EGI (`Monthly Trending!N20`) | $2,201,864.71 ✓ (unchanged — management fee doesn't affect revenue) | $3,763,228.77 ✓ (unchanged) |
| TOTAL OPEX excl. mgmt (`Monthly Trending!N66`) | $1,872,314.78 ✓ (unchanged — substrate's R66 already excludes mgmt) | $4,358,616.18 ✓ (unchanged) |
| Management fee (`Monthly Trending!N67`) | $131,579.65 ✓ (was $0.00 at v0.1.0 — bug fixed) | $188,161.44 ✓ (already correct in v0.1.0) |
| EBITDARM (`Monthly Trending!N68`) | $329,549.93 ✓ (unchanged — substrate excludes mgmt by accounting standard) | -$595,387.41 ✓ (unchanged) |
| EBITDAR (`Monthly Trending!N69`) | $197,970.28 ✓ (was $329,549.93 at v0.1.0 — now correctly subtracts management fee) | -$783,548.85 ✓ (unchanged) |

**Salem source-side cross-check.** Source row 126 EBITDARM = $329,549.93 → matches Salem R68 ✓. Source row 128 Management Fees = $131,579.65 → matches Salem R67 ✓. Source row 130 EBITDAR = $197,970.28 → matches Salem R69 ✓. Salem now ties to source on all four rows.

**Why EBITDARM didn't change.** The substrate's R66 (`TOTAL OPEX (excl. mgmt)`) deliberately excludes the management-fee line, and R68 EBITDARM = EGI − R66. So Management fee not appearing at all (v0.1.0 bug) versus appearing in R67 separately (v0.1.1 fix) makes no difference to EBITDARM by design — that's the accounting-standard definition. The bug surfaced at R69 EBITDAR, which is EBITDARM − R67. v0.1.0's R69 was wrong by exactly the missing management fee.

### How this was caught

Reported by user during post-v0.1.0 testing: "There was an omitted expense item in the Salem Road T12. Management fee was not included." User pointed to Description_Map row 122 (`Management Fees → Management fee`, ready and waiting) and Salem source row 128 (the actual line in the raw T12). Diagnosis traced to the Yardi extractor's strict account-# pre-filter dropping Salem's row 128 before drop-rules ran.

### Notes

- v0.1.0's verification table (72 GL rows, all-zero leakage already) was internally consistent — the missing management fee was getting dropped at parse time, so neither the source-side total nor the aggregated total counted it. The bug was a *missing line item*, not a *miscalculated line item*. This is why the v0.1.0 leakage check passed despite the bug.
- No app.py UI behavior changes. T12_VERSION constant bumped to `"0.1.1"`.
- No template substrate changes. Description_Map already had the mappings; the bug was upstream of the workbook.

---

## [0.1.0] — 2026-05-02

First T12 code release. Substantial template substrate work landed in the kickoff chat before any Python code was written — those iterations are documented below as part of the v0.1.0 ship scope. The code release on 2026-05-02 adds parser, writer, and `app.py` integration on top of that substrate.

### Added

- **`t12_normalizer.py`** — Format-registry parser. `T12Format` ABC with `detect(wb)` / `extract(wb, sheet)` methods. `YardiIncomeToBudgetFormat` (detects sheet named `Income to Budget` first, falls back to scanning for ≥3 numeric account-# rows) and `MriR12mincsFormat` (sheet name match) registered. Three drop-rules applied in order during extraction: no-$-value, grand-total pattern (TOTAL/NET prefixes, EBITDA/EBITDAR/EBITDARM keywords, exact NET INCOME / NET OPERATING INCOME), explicit drop-list (initially `Other Non Operating Revenue & Expense`). Returns `T12ParseResult` (gl_rows, month_labels normalized to `MMM YYYY`, unmatched, format_name, sheet_name). Raises `UnknownT12FormatError` if no format matches. UNMATCHED detection runs against the destination workbook's `Description_Map` set.
- **`t12_normalizer_writer.py`** — Idempotent destination writer. Loads the user's Analyzer / standalone Normalizer template (v0.1.4 substrate). Clears `T12 Input!A12:O511` + `T12 Input!C11:N11` before writing (prevents ghost rows on re-upload). Writes 12 month labels to C11:N11 with text format, then GL detail rows to A:O. Col P (Coverage Check formula), `T12_Calc!N` helper col, named ranges (`DescMap_Description`, `DescMap_Label`), and all other tabs untouched. Capacity 500 GL rows; raises `T12NormalizerCapacityError` if exceeded. Optionally appends UNMATCHED-resolution mappings to `Description_Map` after the last data row — the dynamic named ranges pick them up via COUNTA without formula edits. Upserts a `Run_Info` tab with T12 version, run timestamp, source filename, format detected, GL rows written, and Description_Map appends.
- T12-side version constants in `app.py`: `T12_VERSION = "0.1.0"`, `T12_LAST_UPDATED = "2026-05-02"`, alongside the existing `RR_VERSION` / `RR_LAST_UPDATED`.

### Changed

- **`app.py`** — Raw T12 uploader added to sidebar (optional). Interactive UNMATCHED matcher form appears when the parser returns unresolved descriptions: per-row Label combobox (sourced from the Analyzer's existing 54-entry vocabulary), Section dropdown (Revenue / Labor / Non-Labor / Excluded), CareType dropdown (`-` / IL / AL / MC), Flag dropdown (8 substrate values + blank). Resolutions persist in `st.session_state.t12_resolutions` and survive Streamlit reruns; submission validates that Label and Section are filled. Single combined download "Analyzer with both data" replaces v1.7.0's RR-only Analyzer paste; disabled until rent roll AND Analyzer AND raw T12 are uploaded AND all UNMATCHED are resolved. Combined flow writes RR data to `Rent Roll Input!A7+` first via the existing `t12_writer.populate_t12()` (historical name; see SPEC-T12 §"Module naming history"), then layers T12 data on top via the new `t12_normalizer_writer.populate_t12_input()`. Standalone Normalized RR download stays available whenever a rent roll is uploaded. Version pill renders both versions: `RR v1.11.0 · T12 v0.1.0`. Page title updated to "Rent Roll & T12 Normalizer".
- **Behavior change worth flagging.** v1.11.0's "Analyzer with Rent Roll" download (RR data only into Analyzer) is **retired** in this release per SPEC-T12 §"How the analyst uses the app". The single Analyzer download now always carries both RR and T12 data. Existing users who upload only an RR + Analyzer (no T12) will see the combined download stay disabled and only get the standalone Normalized Rent Roll. This is deliberate — the Analyzer is now defined as a both-data deliverable.

### Verified end-to-end (2026-05-02)

Numbers reconcile to the penny on both reference samples. Tested via parser → writer → LibreOffice recalc (`scripts/recalc.py`) → read post-recalc cell values.

| Metric | Salem (Yardi) | Briar Glen (MRI) |
| --- | ---: | ---: |
| GL rows written | 72 / 72 ✓ | 91 / 91 ✓ |
| UNMATCHED at parse | 0 ✓ | 0 ✓ |
| Source $ (`T12 Input!O` sum) | $4,117,468.33 | $8,306,657.64 |
| Operating $ (`T12 Raw Data` total) | $4,074,179.49 | $8,310,006.39 |
| Depreciation — EXCLUDED $ (`T12 Input` col P filter) | $43,288.84 | -$3,348.75 |
| Leakage = source − operating − excluded | $0.00 ✓ ZERO | $0.00 ✓ ZERO |
| EGI (`Monthly Trending!N20`) | $2,201,864.71 ✓ | $3,763,228.77 ✓ |
| EBITDARM (`Monthly Trending!N68`) | $329,549.93 ✓ | -$595,387.41 ✓ |

Additional verifications:

- **Idempotent re-run** — Wrote Salem (72 rows), then Briar Glen (91 rows) on top of the same workbook. Result: exactly 91 rows in `T12 Input`, no ghost Salem rows, month labels swapped to Briar Glen's Jan–Dec 2025.
- **Capacity guard** — `T12NormalizerCapacityError` fires correctly on 501 synthetic rows; exactly 500 rows accepted (boundary OK).
- **UNMATCHED resolution loop** — Synthetic test injected a fake description (`Pickleball League Sponsorship Income`) with mapping {Other community revenue / Revenue / `-` / blank}. Mapping appended to `Description_Map` row 316. Post-recalc, T12 Input col P resolved the fake description to its label correctly via the dynamic named range — confirming `DescMap_Description` / `DescMap_Label` auto-extension works as designed.
- **Substrate preservation** — All 11 sheets, both named ranges, the hidden `T12_Calc!N` helper col, the 612 SUMIF formulas in `T12 Raw Data`, and rows 1-10 of `T12 Input` (title, instructions, layout note) confirmed intact post-write.
- **Run_Info tab** — Created with all 10 T12-side keys present (version, last-updated, run timestamp, source filename, format detected, source sheet, GL rows written, months detected, UNMATCHED at parse, Description_Map appends).

**Pre-existing substrate issue, not introduced by v0.1.0.** Recalc reports a single `#NAME?` error at `Rent Roll Recon!H20` on every output. Identical pre-write and post-write across both Salem and Briar Glen runs, so this is a substrate-level issue in the migrated master Analyzer (introduced during the master Analyzer migration on 2026-05-02), not anything this release added. Worth a separate substrate-cleanup pass; outside v0.1.0 scope.

### Template iterations (all ship with v0.1.0)

#### Master Analyzer migration — applied 2026-05-02

The five template iterations below were originally landed on the standalone T12 Normalizer template (`ALF_T12-_Normalizer.xlsx`). The user's master Analyzer (`ALF_Financial_Analyzer_Only.xlsx`) was at the pre-v0.1.0 substrate state and needed the same edits applied so that v0.1.0's parser/writer code can target either workbook.

Migration applied via `migrate_analyzer.py` (one-shot script, archived under `tools/migration/`). All five batches landed cleanly, end-to-end verification matched targets to the penny:

| Format | GL rows | UNMATCHED | EGI | EBITDARM |
| --- | ---: | ---: | ---: | ---: |
| Yardi (Salem) | 72 | 0 | $2,201,864.71 | $329,549.93 |
| MRI (Briar Glen) | 91 | 0 | $3,763,228.77 | -$595,387.41 |

Both dollar values reconcile exactly against the standalone T12 template's verification numbers, confirming the migrated master is structurally identical to the standalone v0.1.4 substrate.

**Salem GL-row count correction:** the standalone-template verification table reads "73 GL rows" for Salem. The accurate count after applying parser drop-rule #3 (`Other Non Operating Revenue & Expense` on the explicit drop-list) is 72. The "73" figure was the count before the drop-list filter ran. Corrected in the verification tables in SPEC-T12.md. Total dollars and EGI/EBITDARM unaffected — that one row was already routed to `Depreciation — EXCLUDED` either way.

**openpyxl side effects on save** (known limitations, no formula impact): conditional formatting rules dropped, data validation rules dropped. Both are visual/structural only. Mentioned here for traceability; same limitation as RR's existing T12 paste flow.

**RR-side sheets untouched.** `Rent Roll Input`, `Rent Roll Recon`, `T12 Analytics`, `UW Output`, `RR_Calc` were not modified by the migration. RR v1.11.0 functionality preserved.

**Re-running the migration is safe with caveats** — script checks pre-state and warns rather than blindly applying edits. If run on an already-migrated workbook, it would emit warnings on every batch. Idempotent on Description_Map duplicate removal, named ranges, helper col, and label-row inserts; the row-shift in Monthly Trending is the one batch that would not be idempotent, so don't re-run on already-migrated workbooks without checking.

#### Template v0.1.4 — Monthly Trending fixes

The architectural Path B fix (template v0.1.3) made T12 Raw Data work correctly, but Monthly Trending had pre-existing bugs that were exposed once aggregation started flowing real numbers. Five fixes:

- **R10 (Physical Vacancy)** and **R11 (Loss to Lease)** — dropped `ABS()` wrapper. These rows now flow through with their original signs (negative when reported by source). Returns 0 when source value is missing instead of `""`, so downstream addition in EGI works without errors.
- **R20 (EGI)** — extended formula from `=B8+B15+B16+B17+B18+B19` to `=B8+B10+B11+B15+B16+B17+B18+B19`. Self-applying rule per user direction: when Vacancy/L2L lines are present in source, base rent is treated as gross and these get subtracted (via negative signs); when absent, they evaluate to 0 and contribute nothing (base rent is treated as net). Verified: Salem (no V/L2L) EGI = $2,201,865; Briar Glen (L2L = -$139K) EGI = $3,763,229.
- **New row R53 (`Auto Expense`)** — inserted between Auto insurance (R52) and Fire / security monitoring (now R54). All rows R53-R68 shifted to R54-R69. Done via manual read-row → write-row pattern after openpyxl's `insert_rows()` proved unreliable (it shifted col A labels but didn't update formula references in shifted rows; first attempt corrupted the workbook).
- **R64 (Lease / ground lease)** — replaced `=0` placeholder with proper INDEX/MATCH lookup against `T12 Raw Data!Lease / ground lease` row.
- **R65 (Total non-labor opex)** — both B and N columns rebuilt to sum full range R40:R64 (25 rows). Pre-existing N-column bug (was stopping at N59) is now fixed; this had been understating Salem's Total non-labor opex by ~$100K and Briar Glen's by ~$261K.
- **R66, R68, R69** — references shifted to point at correct rows post-Auto-Expense insert. R66 (TOTAL OPEX) now `=B38+B65`. R68 (EBITDARM) now `=B20-B66`. R69 (EBITDAR) now `=B68-B67`.
- **N-column self-references R54-R63 and R67** — fixed off-by-1 bug introduced during the row shift. Each row's T12 total now correctly sums its own row's monthly values.

End-to-end verification: every row passes audit. All self-sum N-column formulas reference their own row. All cross-row formulas (Total base rent, EGI, Total direct labor, etc.) have matching B-column and N-column references.

#### Template v0.1.3 — Path B architectural fix

The original `T12 Raw Data` SUMIF formulas hardcoded raw description strings (e.g., `SUMIF(..., "ALZ Base Rate Income", ...) + SUMIF(..., "Memory Care Base Rate Income", ...) + SUMIF(..., "MC Base Rate Income", ...)`). Adding new operator vocabulary to `Description_Map` made T12 Input col P resolve correctly but did NOT make T12 Raw Data aggregate the new descriptions — Raw Data's hardcoded list didn't include them. Path B replaces this with a label-based aggregation that picks up new vocabulary automatically:

- **New helper column `T12_Calc!N`** (500 rows) — formula `=IFERROR(INDEX(DescMap_Label, MATCH(A{r}, DescMap_Description, 0)), "")` per row. Pre-computes the Label for every row's description.
- **Rewrote 612 SUMIFs in T12 Raw Data** (51 label rows × 12 monthly cols) from chained-against-raw-descriptions to single `SUMIF(T12_Calc!$N$1:$N$500, "<label>", T12_Calc!$<month>$1:$<month>$500)`. Result: any new operator vocabulary added to `Description_Map` flows through aggregation automatically — no formula maintenance ever.
- **Removed duplicate `Auto Expenses` entry** from `Description_Map` (kept R125 → `Auto Expense`, deleted R152 → `Office, admin & G&A`). The MATCH function returns first hit so R125 was already winning; deletion just cleaned up dead-code data.
- **Added `Auto Expense` row to T12 Raw Data** (at R57). Salem's `Auto Expenses` and Briar Glen's `Auto and Mileage Expense` and `Bus/Shuttle Service` now have an aggregation home.
- **Added `Lease / ground lease` row to T12 Raw Data** (at R58). Future-proofs against ground-leased-property T12s; no current operator uses this label, but the orphan-label leakage is gone.

End-to-end verification confirms zero dollar leakage on either format. Salem: $4,117,468 in source = $4,074,180 to operating + $43,289 to Depreciation EXCLUDED. Briar Glen: $8,306,658 in source = $8,310,006 to operating + $-3,349 to Depreciation EXCLUDED.

#### Template v0.1.2 — Briar Glen vocabulary mapping

Added 82 new entries to `Description_Map` (rows 235-316) covering MRI/Briar Glen vocabulary. Hard constraint enforced throughout: only the existing 54 Labels used, no new categories created. 8 entries auto-skipped because the descriptions already exist in `Description_Map` with the correct labels (`Late Charges`, `Referral Fees`, `Payroll Taxes`, `Workers Comp Insurance`, `Maintenance Supplies`, `Gas`, `Water`, `Real Estate Taxes`).

Mapping decisions made across 6 batches (Revenue, Administration, Property Mgmt + Marketing, Labor & Benefits, Maintenance + Food + Operating + Resident Services, Common Area + Turn + Utilities + Insurance + Taxes). Notable judgment calls:

- **Holiday Pay → `Overtime wages`** (per user direction; flagged that PTO would be more conventional).
- **Marketing labor → `Administrative labor`** (keeps Labor/Non-Labor section split clean; alternative `Sales, adv. & marketing` would have crossed sections).
- **Corporate Taxes → `Depreciation — EXCLUDED`** (treats this as non-operating; excluded from NOI calculation).
- **Approach C for Labor section:** department-first for Salaries (G&A → Admin labor, Nursing → Care staff, etc.), pay-type for Overtime/PTO/Holiday/Bonus (collapsed across departments).

Description_Map went from 229 entries to 311 entries (82 new + 229 existing - 0 removed). The duplicate `Auto Expenses` removal in v0.1.3 brought it to 310 effective entries.

#### Template v0.1.1 — GL-detect formula change + row 11 headers + instruction rewrite

Three changes preparing the template for both Yardi and MRI formats:

- **Col P GL-detect formula** changed from `IF(ISNUMBER(VALUE(TRIM(A12))),...)` to `IF(TRIM(B12)<>"",...)`. Account number column becomes optional (Yardi populates it, MRI doesn't). All 500 col P formulas (P12:P511) rewritten with the new test.
- **Row 11 unmerged** (was a single banner cell `↓ Paste your T12 starting at A12`) and populated with column headers: A=`Account #`, B=`Description`, O=`T12 Total`, P=`Coverage Check`. Cols C-N intentionally blank — writer fills these per upload with detected month labels.
- **Row 4-7 instructions rewritten** to reflect the new app-driven workflow (upload to Streamlit, use in-app matcher, download). Replaces the old "Ctrl+C, Ctrl+V into A12, manually fix UNMATCHED" workflow.
- **Row 9 layout note updated** to describe the new column structure with optional Account #.

#### Template v0.1.0 — Dynamic named ranges

First template substrate work. Added two workbook-scoped defined names:

- `DescMap_Description` = `Description_Map!$A$5:INDEX(Description_Map!$A:$A, MAX(5, COUNTA(Description_Map!$A:$A)+4))`
- `DescMap_Label` = `Description_Map!$B$5:INDEX(Description_Map!$B:$B, MAX(5, COUNTA(Description_Map!$A:$A)+4))`

Rewrote 500 col P formulas in `T12 Input` from hardcoded `Description_Map!$A$5:$A$284` references to the named ranges. Result: `Description_Map` can grow indefinitely without needing formula maintenance. Replaces the original "50-row headroom" approach with proper dynamic ranges.

The `MAX(5, ...)` floor prevents Excel from rejecting an empty-data-area range (`A5:A4` is invalid; `MAX(5,0+4)=5` keeps it valid even pathologically).

### Architectural decisions (implemented in v0.1.0 code)

These pin down the implementation scope before code is written:

- **Format-registry pattern.** Each supported T12 format is a class with `detect()` and `extract()` methods. Adding a format is a small change. v0.1.0 ships with `YardiIncomeToBudgetFormat` and `MriR12mincsFormat`.
- **Three parser drop-rules**, applied in order: drop rows with no $ value; drop rows whose description matches a grand-total pattern (`TOTAL `, `NET `, `EBITDA`, `EBITDAR`, `EBITDARM`, exact match `NET INCOME` / `NET OPERATING INCOME`); drop rows in an explicit drop-list (initially: `Other Non Operating Revenue & Expense`).
- **UNMATCHED in-app matching with write-to-Description_Map.** Interactive Streamlit form lets user map unmatched descriptions (Label / Section / CareType / Flag) and writes them to the destination workbook's `Description_Map` on download. Mappings persist for re-uploads. Approach A from Interpretation A vs. B decision earlier in the chat.
- **Single combined download button.** "Analyzer with both data" — replaces v1.7.0's RR-only Analyzer paste. Disabled until rent roll AND Analyzer AND raw T12 are uploaded, AND all UNMATCHED are mapped. The standalone Normalized Rent Roll download (existing) stays.
- **Separate writer module** (`t12_normalizer_writer.py`) — does not extend the existing `t12_writer.py` (which writes RR data). Keeps boundaries clean. Naming-history note in SPEC.
- **Parser writes month labels to row 11.** C11:N11 of `T12 Input` get filled with normalized `MMM YYYY` labels detected from each format's source row (Yardi row 9, MRI row 11). Format-specific extraction, uniform output.
- **Description_Map ships pre-populated.** v0.1.0 baseline is 310 effective entries (Yardi-aware + MRI-aware vocabulary). Future operators add their delta via the in-app matcher.

### Sequencing note (resolved)

Track 1's Path B (Analyzer-as-paste-target rename) shipped as RR v1.11.0 in commit `9cb4edd`. The T12 chat resumed after that, with template work landing in subsequent commits during the kickoff chat. Code work is the next deliverable.

### Documentation discipline

- This changelog and `SPEC-T12.md` join `SPEC-RR.md` and `CHANGELOG-RR.md`.
- `T12_NORMALIZER_KICKOFF.md` is superseded by `SPEC-T12.md`. Move to `docs/archive/` once v0.1.0 ships, or earlier if root tidiness matters.
- `README.md` to be updated when v0.1.0 ships: top-level "Repo contents" section explaining the two tracks + the Analyzer destination.

---

## How the version stream relates to Track 1

RR and T12 evolve independently. A change to RR (e.g., adding a third operator format) bumps RR only. A change to T12 (e.g., adding RealPage support) bumps T12 only. A change to shared infrastructure (`app.py` UI, `period_date.py`, `requirements.txt`) bumps whichever track the change primarily serves; if it serves both equally, bump both.

Each track's version surfaces in the UI pill and in the `Run_Info` tab of any output that track touched.

The "one track at a time" principle means a chat is RR-only OR T12-only OR explicitly cross-cutting — never accidentally cross-cutting. If a chat finds itself editing both `SPEC-RR.md` and `SPEC-T12.md`, stop and confirm whether that's intentional cross-cutting work or scope creep.
