# AR & Collections — Build Complete + Spec Update Request

**Date:** 2026-05-23
**From:** Claude Code (webapp / rent_roll_app)
**To:** Cowork (spec authoring)
**Re:** `AR_Collections_Tab_Scope.md` Rev 1 → Rev 2 needed
**Status:** ✓ Code shipped end-to-end · spec needs to catch up to reality

---

## TL;DR

The AR & Collections module you spec'd in Rev 1 is **built, tested, committed, pushed, and live on the Streamlit deploy** as of 2026-05-23. The Rev 1 spec had **12 divergences** from codebase reality (terminology, taxonomy mismatches, impossible positions, etc.). All 12 were decided here against the live system and implemented — the spec now needs to be updated to Rev 2 to match what shipped so the design record stays accurate.

The webapp is now the canonical implementation. This doc covers (1) what shipped, (2) every Rev 1 → Rev 2 spec change needed.

---

## What shipped

### New operator input dimension

Streamlit users can now upload an **AR aging file (.xlsx or .csv)** alongside the existing Rent Roll and T12 uploads. Default is no AR (fully optional throughout — non-AR runs are bit-for-bit unchanged from before).

### Five commits on `main` (now on `origin/main`)

| Commit | What |
|---|---|
| `e2f26d5` | AR module foundation — substrate v0.2.10 + mappings extension |
| `05ebf7a` | AR aging parser (`ar_normalizer.py`) + synthetic fixture |
| `41db0bd` | AR writer (`ar_writer.py`) + Streamlit upload wiring |
| `983573c` | Substrate v0.2.11 — Dashboard variance tile + Cover AR version line |
| `0a5eaaa` | Docs finalization — CHANGELOG / journal / backlog / CLAUDE |

### Pieces of the pipeline

| Piece | File | Status |
|---|---|---|
| Parser | `ar_normalizer.py` (AR module v0.1.0) | ✓ Shipped |
| Writer | `ar_writer.py` | ✓ Shipped |
| Streamlit upload | `app.py` sidebar + orchestration Step 3 | ✓ Shipped |
| Substrate sheet | `tools/migration/migrate_to_v0210.py` (`AR & Collections` at sheet index 8, hidden by default) | ✓ Shipped |
| Workbook Health integration | B43 IF guard + P5 gate at row 52 | ✓ Shipped |
| Dashboard variance tile | `tools/migration/migrate_to_v0211.py` (K10:L13) | ✓ Shipped |
| Cover AR version line | A11/B11 | ✓ Shipped |
| Mappings extension | `mappings.py` Managed Care + MA/MCO rules | ✓ Shipped |
| Synthetic fixture | `tests/fixtures/ar/ar_synthetic_v01.xlsx` (12 residents × 14 cols) | ✓ Shipped |
| Live operator sample | n/a | **PENDING — see below** |

---

## Spec updates needed for Rev 2

The Rev 1 spec had 12 issues against codebase reality. All 12 were decided against the live system; please apply these updates to Rev 2 so the spec accurately reflects what shipped.

### 1. Framing

**Rev 1:** Calls the Analyzer a "webapp" with a "results view."
**Reality / Rev 2:** The Analyzer is an `.xlsx` workbook. The Streamlit app at `https://rrnormalizer.streamlit.app/` populates it. "Tabs" = Excel sheets. Update intro accordingly.

### 2. Payer taxonomy — §3 By-Payer Mix

**Rev 1:** Normalizes to 6 buckets: Private Pay / Medicaid / Medicare / VA / LTC / Other.
**Reality / Rev 2:** AR §3 has **7 buckets** matching `mappings.py` normalization targets:

| # | Bucket | Substrate row |
|---|---|---|
| 1 | Private Pay | C30 |
| 2 | Medicaid | C31 |
| 3 | Medicare | C32 |
| 4 | **Managed Care** *(new)* | C33 |
| 5 | VA Benefit *(not "VA")* | C34 |
| 6 | LTC Insurance *(not "LTC")* | C35 |
| 7 | **Self-Pay + Other** *(replaces "Other")* | C36 |

- `Managed Care` covers Medicare Advantage, MA Plan, MCO. New `mappings.py` rules added — MA rules ordered BEFORE bare `\bmedicare\b` (first-match-wins) so MA receivables don't get tagged as traditional Medicare.
- The Dashboard's existing Payer Mix at `O5:P14` uses the same 6-bucket variant of this taxonomy (no Medicare, since traditional Medicare is rare in ALF rent rolls). AR's view shows all 7 for full visibility.
- `PAYER_FALLBACK` constant unchanged — RR ingest still falls back to "Private Pay". AR ingest passes `payer_fallback="Self-Pay + Other"` via per-instance `MappingSet` override — keeps RR behavior unchanged.

### 3. Sheet position

**Rev 1:** "Position the new tab after T12 Analytics and before Dashboard."
**Reality / Rev 2:** **Sheet index 8** — between Monthly Trending (index 7) and UW Output (now index 9). The Rev 1 position was impossible because Dashboard is at sheet index 1 (since substrate v0.2.7 / BL-0018). Workbook narrative is now: data → reconcile → trend → **AR review** → export.

Updated 16-sheet ordering:

```
 0  Cover
 1  Dashboard
 2  T12 Analytics
 3  T12 Input
 4  T12 Raw Data
 5  Rent Roll Input
 6  Rent Roll Recon
 7  Monthly Trending
 8  AR & Collections          ← NEW (hidden by default)
 9  UW Output
10  UW Export
11  Mapping Review
12  Description_Map
13  RR_Calc (hidden)
14  T12_Calc (hidden)
15  Workbook Health (hidden)
```

### 4. Dashboard tiles — §Integration

**Rev 1:** Three new KPI tiles on Dashboard (DSO · % aged 90+ · variance flag).
**Reality / Rev 2:** **One tile only — the bad-debt variance flag at K10:L13** (the only open slot on the Dashboard). DSO and %aged 90+ live on the AR tab itself in §2.

Tile composition:
- K10:L10 (merged) title: "BAD DEBT VARIANCE"
- K11:L12 (merged) value formula: `=IF('AR & Collections'!Z1=0,"— upload AR to populate",'AR & Collections'!C56)` — dormant when no AR, live ⚪/✓/⚠ when uploaded
- K13:L13 (merged) footnote: "= T12 bad debt − annualized AR write-offs"

### 5. AR is optional — apply throughout

**Rev 1:** Implies AR is always uploaded.
**Reality / Rev 2:** **AR upload is optional; default is no AR file.** All integration points must be conditional via the `Z1` presence flag (0 = no AR data, 1 = populated by `ar_writer.py`):

| Touch point | When `Z1 = 0` (default) | When `Z1 = 1` (AR uploaded) |
|---|---|---|
| AR sheet visibility | Hidden | Visible |
| Workbook Health B43 | `=SUM('Rent Roll Input'!$X)` (RR-derived, bit-for-bit unchanged) | `='AR & Collections'!C15` (AR-derived) |
| Workbook Health P5 gate | "✓" (inert) | Compares C3 as-of to `RR_Period_Date` |
| Dashboard K10:L13 tile | "— upload AR to populate" | Live ⚪/✓/⚠ flag string |

### 6. Cross-sheet cell pins — §Integration → Reads from

**Rev 1:** Uses dot-notation (`monthly_trending.annualized_EGI`, etc.).
**Reality / Rev 2:** Pin to actual cells:

| Spec reference | Canonical cell |
|---|---|
| `monthly_trending.annualized_EGI` | `Monthly Trending!N26` |
| `t12_analytics.avg_occupied_beds` | `T12 Analytics!E7` |
| `t12_analytics.bad_debt_expense` | `T12 Analytics!E98` |
| `rent_roll.unit` (join key) | `Rent Roll Input!A` (primary), resident name secondary tiebreaker |
| Period date (RR) | `RR_Period_Date` named range (workbook-scoped, → `'Rent Roll Recon'!$B$2`) |

### 7. Workbook Health AR balance — §Integration

**Rev 1:** "Replace existing AR total with `ar_collections.total_AR`."
**Reality / Rev 2:** **Conditional, not replacement.** `Workbook Health!B43` is now:

```
=IF('AR & Collections'!Z1=1, 'AR & Collections'!C15, SUM('Rent Roll Input'!$X$7:$X$606))
```

When Z1=0 (no AR uploaded), the RR-derived formula evaluates exactly as it did before AR work — non-AR runs see no surface change. The fallback was preserved bit-for-bit to guarantee regression-clean behavior. When Z1=1, B43 reads the AR sheet's Total AR.

### 8. Pre-export gate P5 — §Integration

**Rev 1:** Adds "P5 · AR period matches RR period" to the pre-export gate.
**Reality / Rev 2:** **Conditional gate at Workbook Health row 52.** Formula:

```
=IF('AR & Collections'!Z1=0,"✓",
 IF('AR & Collections'!C3=RR_Period_Date,"✓","⚠ AR period ≠ RR period"))
```

When Z1=0 (no AR uploaded), P5 defaults to "✓" so READY-FOR-EXPORT (now at row 53, was row 52) doesn't fail for non-AR runs. The summary was shifted one row down (verified zero external refs to `Workbook Health!B52` before the shift); B52 (P5) was added to its `AND(...)` formula.

### 9. Payer mapping source — §3 ingest

**Rev 1:** "Normalize via existing payer mapping rules."
**Reality / Rev 2:** Rules live in [`mappings.py`](mappings.py) — specifically `DEFAULT_PAYER` (lines 65-79). v0.2.10 extension added:
- New `Managed Care` bucket
- Rules for `medicare advantage`, `MA plan`, `managed care`, `MCO` (MA rules BEFORE bare `medicare` to win the first-match)
- AR ingest constructs `MappingSet(payer_fallback="Self-Pay + Other")` per-instance; RR's module-level `PAYER_FALLBACK = "Private Pay"` is unchanged.

### 10. Bundled file note — §Reference files

**Rev 1:** References `ALF_Financial_Analyzer_Only.xlsx` as static.
**Reality / Rev 2:** The bundled `ALF_Financial_Analyzer_Only.xlsx` **is editable** (not locked). AR ships through two migration scripts (`migrate_to_v0210.py` and `migrate_to_v0211.py`) AND the bundled file was forward-applied directly (v0.2.4 → v0.2.10 → v0.2.11) per the BL-0021 carry-forward convention. The bundled is now at substrate v0.2.11 with the AR sheet baked in — users get AR by default without forward-rolling.

Note: the bundled still skips v0.2.5-v0.2.9 intermediate substrate features per BL-0021 history. This is intentional and documented.

### 11. Module ownership for hide/show

**Rev 1:** "Tab is hidden / disabled until AR uploaded."
**Reality / Rev 2:** The AR sheet exists in every Analyzer file (because it's a substrate-level sheet). Its `sheet_state` is controlled per cycle by a new **`ar_writer.py`** module (mirrors `analyzer_rr_writer.py` shape). When AR is uploaded, `ar_writer.populate_ar_collections()` sets `sheet_state = 'visible'`; when AR is absent, the sheet stays at the migration default `'hidden'`.

### 12. Annualization basis — §4

**Rev 1:** "writeoffs_period × 12 (or ×4/×1 per period basis)."
**Reality / Rev 2:** Pinned: **monthly basis (× 12) is the default**, analyst-editable via the `C4 Period basis` cell on the AR sheet. `C54` (period write-offs annualized) reads `=C45*12`. Variance tolerance default 20% at `C5`, analyst-editable.

---

## Items in Rev 1 that stayed unchanged

These shipped exactly as spec'd — no Rev 2 updates needed:

- §1 Aging Summary buckets and formulas
- §2 KPI formulas (subject to cell pins from item 6)
- §3 normalization mechanics (subject to taxonomy from item 2)
- §4 roll-forward mechanics + variance tolerance default
- §5 Flag triggers (with caveat — see Pending below)
- §7 Decisions locked (all 5)
- UW Output / UW Export — unchanged
- Rent Roll Input schema — unchanged
- T12 Normalizer — unchanged

---

## Pending — intentionally deferred from v0.1.0

These are known carry-forwards documented in `UW-BACKLOG.md` (BL-0023) and `CLAUDE.md` "Closed 2026-05-23" entry.

### Live operator AR sample — **PENDING**

The parser's fuzzy header rules were built against the synthetic fixture at `tests/fixtures/ar/ar_synthetic_v01.xlsx` (12 residents × 14 cols, exercises all 7 payer buckets). Once a real operator AR aging file is received, the rules will need expansion to absorb operator-specific naming variations.

**Convention:** live operator samples go in `Sample Files/` (gitignored — same rule as the T12 fixtures); synthetic stays committed in `tests/fixtures/ar/` as the structural reference.

When a live sample lands, expect a brief follow-up cycle: parse the real file, identify which headers don't match, extend `HEADER_RULES` in `ar_normalizer.py`, re-verify, commit.

### AR ↔ Rent Roll row-level join — §5 flags

Two of the §5 flags require joining AR rows to Rent Roll Input rows in the same workbook:

- C62 — "Resident in 90+ with active concession" (needs RR concession column lookup)
- C63 — "Vacant bed with non-zero AR" (needs RR status column lookup)

Currently stubbed to 0 in v0.1.0. Implementing requires `ar_writer.py` to read `Rent Roll Input` from the workbook it's writing to. Reasonable next iteration; not blocking.

### Standalone `CHANGELOG-AR.md`

Currently AR work is consolidated into `CHANGELOG-T12.md` under the v0.2.10 / v0.2.11 substrate entries. When the AR pipeline matures (post live-sample iteration), spin out `CHANGELOG-AR.md` to track AR module versions independently.

---

## Reference data for Rev 2

If you need exact reference data while updating the spec, these are the canonical pins as of 2026-05-23:

### AR & Collections sheet structure (substrate v0.2.10)

| Section | Rows | Key cells |
|---|---|---|
| Settings band | 3-5 | C3 (as-of date), C4 (period basis), C5 (variance tolerance) |
| §1 Aging Summary | 7-18 | C9-C13 (bucket totals), C15 (TOTAL AR), C17 (90+ subtotal), C18 (% aged 90+) |
| §2 KPIs | 20-26 | C22 (DSO), C23 (AR÷EGI), C24 (%90+), C25 (collection effectiveness), C26 (per-bed) |
| §3 Payer Mix | 28-37 | C30-C36 ($ outstanding), E30-E36 (% aged 90+), F30-F36 (concentration flag) |
| §4 Roll-Forward | 40-57 | C42 (prior), C43-46 (period flows), C47 (implied), C48 (reported), C49 (gap) |
| §4 Bad-Debt | 51-57 | C52 (tolerance), C53 (T12 BD), C54 (annualized), C55 (variance), **C56 (variance flag — fed to Dashboard tile)**, C57 (implied reserve change) |
| §5 Flags | 60-66 | C62-C66 |
| Presence flag | row 1 | **Z1** (0 = no AR data, 1 = populated) |

### Workbook Health changes (substrate v0.2.10)

| Cell | Old | New |
|---|---|---|
| B43 | `=SUM('Rent Roll Input'!$X$7:$X$606)` | `=IF('AR & Collections'!Z1=1,'AR & Collections'!C15,SUM('Rent Roll Input'!$X$7:$X$606))` |
| A52 | "READY FOR EXPORT?" (summary) | "P5 · AR period matches RR period (inert if no AR)" |
| B52 | summary formula | P5 formula (see item 8) |
| A53 | (was empty) | "READY FOR EXPORT?" (moved from row 52) |
| B53 | (was empty) | summary formula with `B52="✓"` ANDed in |

### Dashboard changes (substrate v0.2.11)

| Cell | Content |
|---|---|
| K10:L10 (merged) | Title "BAD DEBT VARIANCE" |
| K11:L12 (merged) | `=IF('AR & Collections'!Z1=0,"— upload AR to populate",'AR & Collections'!C56)` |
| K13:L13 (merged) | Footnote "= T12 bad debt − annualized AR write-offs" |

### Cover changes (substrate v0.2.11)

| Cell | Content |
|---|---|
| A11 | "AR Module" |
| B11 | "v0.1.0" |
| B8 | "v0.2.11" (bumped) |

---

## After Rev 2 ships

Once Rev 2 is published reflecting these decisions, the spec and the live implementation will be in sync. Next major iteration will be **live-operator-sample triage** — at that point, expect targeted spec edits if real operator AR formats reveal anything the synthetic missed (probably mostly header-naming variations).

---

*All decisions in this doc were made and shipped in chat session 2026-05-23 against the live codebase at `https://github.com/ErikJ-Stack/rent-roll-normalizer` (branch `main`, ending at commit `0a5eaaa`).*
