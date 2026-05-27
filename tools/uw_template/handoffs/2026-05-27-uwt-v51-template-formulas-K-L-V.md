# UW Template Handoff — `2026-05-27-uwt-v51-template-formulas-K-L-V`

---

**Status:** Verified (UWT v0.5.3 / 2026-05-27)
**Template version:** v5 / v5.1 (in place at `assets/ALF_UW_Template_v5.xlsx`)
**Registry version:** 0.4.1 → 0.4.2
**Triggered by:** Operator-authored v5.1 dropped at `assets/ALF_UW_Template_v5.1.xlsx` 2026-05-27; renamed to `assets/ALF_UW_Template_v5.xlsx` per filename-consolidation policy.
**Owner (Claude Code side):** UWT v0.5.3 chat (2026-05-27)
**Owner (operator side):** Cowork → Excel (already done)

## Summary

Operator-reported: *"I removed the alf uw template v5 and replace with v5.1. That's the new updated one with corrections in the rent roll analysis tab."*

The "corrections" are six new template formulas at row 211+ on Rent Roll Analysis (fill-down through row 609). Three of those hit cells the writer was previously paste-targeting, which would have overwritten the template's formulas. Registry updated to reclassify those three concepts `mapped → derived` so the writer skips and the template self-derives.

## Template-side changes received (operator's v5.1 author work)

### A. New template formulas added at row 211+ (Rent Roll Analysis)

Six new formulas, fill-down to row 609:

| Cell | Formula | What it computes |
|---|---|---|
| `K211+` | `=IFERROR(IF(A211="","",N(AE211)+N(AF211)+N(AG211)+N(AH211)),0)` | Total LOC $ summed from per-fee ancillary cols (AE-AH) |
| `L211+` | `=IFERROR(IF(A211="","",N(J211)+N(K211)),0)` | Total Sched = Actual Rate + Total LOC |
| `V211+` | `=IFERROR(IF(OR(A211="",U211="",U211=0,J211=""),"",J211/U211),"")` | Actual PSF per month (Actual Rate / SqFt) |
| `W211+` | `=IFERROR(IF(V211="","",V211*12),"")` | Actual PSF per year (V × 12) |
| `AA211+` | `=IFERROR(IF(OR(A211="",I211="",J211=""),"",I211-J211),"")` | Mkt-Actual $ delta (Market - Actual) |
| `AB211+` | `=IFERROR(IF(OR(AA211="",I211=0,I211=""),"",AA211/I211),"")` | Mkt-Actual % delta |

W, AA, AB were already classified `derived` in the registry's `intake_targets_unmapped` block (no concept maps there). **K, L, V were not** — they had concepts pasting to them. Registry updated below.

### B. Other v5.1 deltas (informational)

- **A173 / B173 IFERROR wrapper stripped.** Operator's v5.1 source was authored from a pre-v0.4.4 baseline, so the v0.4.4 patch's IFERROR wrapper around `_xlfn.TEXTBEFORE(_xlfn.ANCHORARRAY(Z173),"|")` and `_xlfn.TEXTAFTER(_xlfn.ANCHORARRAY(Z173),"|")` was lost. Net impact: when Z173 spill is empty (e.g. no occupied units), A173/B173 throw `#N/A` instead of blank. **Carry-forward — see "Open follow-ups" below.**
- **Cover G1/H1 substrate stamp** — still empty. The 2026-05-26 handoff brief's substrate version stamp request was not absorbed in v5.1.
- **Rent Roll Analysis B5 date cell** — still empty. The 2026-05-26 handoff brief's RR Period date cell was not absorbed in v5.1.
- **Zip-part integrity** — operator's v5.1 has all 46 zip parts including `xl/metadata.xml` (XLDAPR / fDynamic) and `xl/webextensions/` (Claude-for-Excel taskpane). Healthier than the prior v5 in git HEAD (which had only 39 parts after past openpyxl operations).

## Mapping updates (registry v0.4.2)

Applied by `tools/uw_template/_absorb_v51_total_formulas.py` (idempotent; retained as audit trail):

| Concept | Source col | v5 target | Before | After | Reason |
|---|---|---|---|---|---|
| `rr_total_loc` | Rent Roll Input `T` | Rent Roll Analysis `K211+` | `mapped` | `derived` | Template now owns `=N(AE)+N(AF)+N(AG)+N(AH)` |
| `rr_total_monthly_rev` | Rent Roll Input `U` | Rent Roll Analysis `L211+` | `mapped` | `derived` | Template now owns `=N(J)+N(K)` |
| `rr_actual_psf` | Rent Roll Input `AA` | Rent Roll Analysis `V211+` | `mapped` | `derived` | Template now owns `=J/U` |

Precedent: matches `rr_total_ancillary` (which became `derived` in UWT v0.4.0 when v5 added the `=SUM(AK:AO)` formula at AQ). The `derived` status is in `_DEFAULT_SKIP_STATUSES` so the writer skips automatically.

Status rollup: 104 mapped (was 107) · 4 proposed · 6 derived (was 3) · 5 gap_source · 2 gap_target · 1 header_only · 1 substrate_ready_parser_pending.

## Verification

Smoke test (`python3 tests/test_uw_template_writer.py`) passes:

- **Empty Analyzer:** 2 cells written / 15 skipped / 106 no_source (out of 123 concepts).
- **Homestead populated:** 99 concepts written / 2,311 cells / 16 skipped / 8 no_source.
  - EGI $7,001,957 at N69 ✓
  - EBITDA $1,417,385 at N118 ✓
  - EBITDARM $1,767,483 at N116 ✓
  - GPR $9,524,893 at N58 ✓
  - Occupied Beds 53 IL / 40 AL / 35 MC at Prop Info B20-B22 ✓
- **All 10 v5.1 template formulas preserved** in output (K, L, V, W, X, Y, AA, AB, AP, AT).
- **Writer-paste data intact** alongside the formulas (A211='A1', D211='1 Bedroom', E211='Occupied', J211=$2,926.84, U211=461, AR211='X').

Cell count regression vs v0.5.2:
- v0.5.2: 102 written / 3,244 cells (Homestead).
- v0.5.3: 99 written / 2,311 cells. Delta: -3 concepts × 176 rows + small adjustments for the J/U writer-source changes.

## Open follow-ups (rolled forward into a future handoff)

1. **A173 / B173 IFERROR wrapper missing in v5.1** — when Z173 spill is empty, A173/B173 throw `#N/A` instead of returning blank. Fix path: operator re-wraps in Cowork (next v5.1 author pass), or accept regression since populated templates always have at least one occupied unit. Recommend operator-side fix to keep the v0.4.4 protection.
2. **Cover G1/H1 substrate version stamp** — still pending from 2026-05-26 brief. Closes `gap_target` concept `substrate_version`.
3. **Rent Roll Analysis B5 RR Period date cell** — still pending from 2026-05-26 brief. Closes `proposed` concept `rr_period_date`.

These three items can be bundled into a single next-v5.1-revision author pass when convenient.

## Cross-references

- **Spec:** [`SPEC-UWT.md`](../../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../../CHANGELOG-UWT.md) — v0.5.3 entry
- **Absorber script:** [`_absorb_v51_total_formulas.py`](../_absorb_v51_total_formulas.py) (idempotent, audit trail)
- **Prior handoff:** [`2026-05-27-uwt-v51-unit-type-restructure.md`](2026-05-27-uwt-v51-unit-type-restructure.md) (the major v5.1 column restructure that shipped earlier in the day)
- **Pending operator-side handoff:** [`2026-05-26-uwt-v5-to-v51-residual-gaps.md`](2026-05-26-uwt-v5-to-v51-residual-gaps.md) (Cover stamp + B5 date)
- **Substrate version mapped against:** v0.2.14 (unchanged)

## Notes (xlsx integrity caveat)

The smoke test's *output* xlsx (populated UW Template) drops `xl/metadata.xml` and `xl/webextensions/` on the writer's `openpyxl.save()` per **openpyxl quirk #6**. The input template at `assets/ALF_UW_Template_v5.xlsx` has these parts intact (46 zip parts); the populated per-deal output produced by the writer does not (39 parts). The operator workaround per CLAUDE.md head and prior handoffs: **open the populated UW Template once in Excel and re-save**, which rebuilds `xl/metadata.xml` from the dynamic-array formula calls Excel finds in the workbook.

This is the same workaround established with v0.4.3. The roadmap item to eliminate this friction is the in-Python formula evaluator (4-8 hour follow-up); not implemented in this release.
