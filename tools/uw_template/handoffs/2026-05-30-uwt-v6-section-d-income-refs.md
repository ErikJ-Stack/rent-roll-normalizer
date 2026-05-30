# UW Template Handoff — `2026-05-30-uwt-v6-section-d-income-refs`

---

**Status:** Pending operator — *interim programmatic patch applied (UWT v0.8.1 / 2026-05-30); durable template re-author is a separate operator task (see "Template-side changes required").*
**Template version:** v6 in place (formula-only repoint; no version bump)
**Registry version:** 0.5.0 (unchanged — no concept targets affected)
**Triggered by:** Operator-reported on a populated Briar Glen output (2026-05-30): "the T12 tab isn't populating properly."
**Owner (Claude Code side):** Track 4 chat
**Owner (operator side):** author the three Section-D repoints into the **Deals-folder canonical v6 template** in Excel (so the durable source isn't a Python round-trip), then re-drop

## Why this stays "Pending operator" despite the interim patch

The Claude Code side unblocked the immediate problem by patching
`assets/ALF_UW_Template_v6.xlsx` programmatically (matching the v0.7.1
precedent) so the next populate is correct *today*. But the **canonical v6
template lives in the operator's Deals folder**, authored in Excel — and per
the Track 4 ownership split + openpyxl quirk #6, a Python round-trip is not the
durable source of truth (it strips `xl/metadata.xml` / `xl/webextensions/`,
restored here only by re-injection from v5). So the template change is tracked
as a **separate operator task**: re-author the three Section-D cells in Excel
on the Deals-folder copy and re-drop it. Until then, the repo's `assets/v6`
carries the interim patch and the populate flow is correct. This row flips to
**Verified** when the operator-authored Deals-folder v6 reflects the repoint.

## Summary

A third v6 partial-repoint miss, same class as the two closed in v0.7.1. When
the operator rebuilt the v6 income section (actual-T-12 build first; GPR
waterfall demoted to a DIAGNOSTIC sub-block at N80-83; EGI moved up from N69 to
N77), the openpyxl repointing pass repointed the *EGI* chain (B5/B9/B11:
N69→N77) but missed the **Section-D income-summary** chain. So
`T-12 Analysis!B22/B23/B24` (GPR / Net Rent / EGI in the ECONOMIC vs. PHYSICAL
OCCUPANCY RECONCILIATION block) still pointed at the old v5 rows N58/N63/N69 —
which in v6 are the typically-$0 "Base Rent — IL" / "LOC / Care — AL" / "Meal
Income" lines. Result: the three headline cells (and B25 Economic Occupancy %,
which divides B23/B22) read $0 even though the entire Layer-3 data tier was
populated correctly. **This is a blank-template formula bug, not a writer or
data bug** — confirmed by diffing v5 (where N58/N63/N69 *were* GPR/NetRent/EGI).

Because this is the same low-risk single-cell-formula repoint that v0.7.1
handled programmatically (`_fix_v6_headers_and_metadata.py`), it was fixed the
same way rather than routed back to Cowork: `tools/uw_template/_fix_v6_section_d_refs.py`
repoints the three cells in `assets/ALF_UW_Template_v6.xlsx` and re-restores
the dynamic-array metadata that the openpyxl round-trip strips.

## Template-side changes required

### 1. `T-12 Analysis!B22` — repoint GPR

- **Before:** `=N58` (v5 row — in v6, "Base Rent — IL", $0)
- **After:** `=N80` (v6 "Gross Potential Rent (GPR)")
- **Styling:** unchanged
- **Why:** v6 income restructure moved GPR into the diagnostic sub-block at N80.

### 2. `T-12 Analysis!B23` — repoint Net Rent

- **Before:** `=N63` (v5 row — in v6, "LOC / Care — AL", $0)
- **After:** `=N83` (v6 "Net Rent (projected)")
- **Why:** Net Rent moved to N83 (= N80 + N81 + N82).

### 3. `T-12 Analysis!B24` — repoint EGI

- **Before:** `=N69` (v5 row — in v6, "Meal Income", $0)
- **After:** `=N77` (v6 "EFFECTIVE GROSS INCOME (EGI)")
- **Why:** EGI moved up to N77 in the restructure (same move that B5/B9/B11
  already got).

> `B25` (`=IFERROR(B23/B22,0)`, Economic Occupancy %) needs no edit — it reads
> the now-correct B22/B23.

## Mapping updates

None. No registry concept targets Section D — these are intra-template
diagnostic formulas, not writer paste targets. `registry_version` stays 0.5.0.

## Writer-scope decisions

None — the writer is unaffected (it never touches B22/B23/B24; the Layer-3
rows it does write were already correct).

## Section F note (NOT in scope — flagged for operator awareness)

`T-12 Analysis!B41`/`B47` (RE Taxes / P&C "T-12 Actual") show `0` + a
"⚠ not in T-12 — verify with operator / broker" status, even though the actuals
exist in Layer 3 (N117 RE Taxes $82,969; N112 P&C $88,242 on Briar Glen). Those
are **analyst-input / pro-forma triangulation cells** — literal `0` in v5 too,
never auto-pulled. By design, left as-is. If the operator wants them
auto-populated, a future revision could wire `B41=N117` and `B47=N112` — but
that's a design call, not a regression fix.

## Verification checklist

**Claude Code side (done this chat):**
- [x] `_fix_v6_section_d_refs.py` pre-flight confirms N80/N83/N77 carry the GPR/NetRent/EGI labels before editing.
- [x] B22/B23/B24 repointed; B25 formula intact; v0.7.1's B56:M56 fix + income-restructure formulas (N77, N61) still intact.
- [x] `xl/metadata.xml` + 554 Section R/S `cm` markers re-restored; zip 40 parts; sheet count 16; Z173 still ArrayFormula.
- [x] Idempotent (re-run: 0 cells changed, all checks pass).
- [x] End-to-end populate (Homestead, v6): B22/B23/B24 → =N80/=N83/=N77, resolving to GPR $9,524,893 / Net Rent $6,951,136 / EGI $6,964,627; 101 concepts / 516 monthly cells.
- [x] All 5 suites in `tests/test_uw_output_model.py` green.
- [x] Corrected copy of the operator's reported output saved at `Downloads/Briar_Glen_UW_Template_2025-12-31_normalized_FIXED.xlsx`.

**Operator side — durable template re-author (separate task, makes this Verified):**
- [ ] In the **Deals-folder canonical v6 template**, in Excel, set `T-12 Analysis!B22 = =N80`, `B23 = =N83`, `B24 = =N77` (B25 needs no edit — it reads B22/B23).
- [ ] Save in Excel (NOT via a Python/Sheets round-trip — preserves `xl/metadata.xml` + the Claude add-in webextensions natively).
- [ ] Re-drop the re-authored v6 into the repo at `assets/ALF_UW_Template_v6.xlsx` (replaces the interim programmatic patch with the durable Excel-authored source).
- [ ] Confirm Section D reads non-zero on a populated output (GPR / Net Rent / EGI).
- [ ] (Optional, separate decision) decide whether Section F "T-12 Actual" sub-cells (B41/B47) should auto-pull from N117/N112.

## Cross-references

- **Backlog:** none (template formula fix, not a BL item).
- **Spec:** [`SPEC-UWT.md`](../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../CHANGELOG-UWT.md) — v0.8.1
- **Prior art:** v0.7.1 `_fix_v6_headers_and_metadata.py` (B56:M56 repoint + metadata restore) — same fix pattern.
- **Registry entries affected:** none.
- **Substrate version mapped against:** v0.2.14 (unchanged).

## Notes for Cowork

If the v6 template is ever re-authored from a fresh openpyxl pass, re-run the
full **v5→v6 row-move audit** on *every* upstream formula chain — Section D
(rows 22-24) and the B56:M56 header row are the two that the original repoint
missed. Diff against the v5 template's row map: any `=N{58,59,60,63,69}` that
survived into v6 is suspect (those rows changed meaning in the income
restructure). Don't roundtrip through Google Sheets / LibreOffice (BL-0018
lesson). The dynamic-array metadata (`xl/metadata.xml`) is restored
programmatically by the fix script — but a clean Excel-authored save is the
durable source of truth.
