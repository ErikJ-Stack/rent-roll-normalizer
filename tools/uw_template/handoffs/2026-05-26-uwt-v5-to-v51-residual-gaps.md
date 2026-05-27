# UW Template Handoff — `2026-05-26-uwt-v5-to-v51-residual-gaps`

> ⚠ **2026-05-26 (later same day) — v0.5.0 attempted then rolled back.**
> Claude Code attempted to land both cells directly via openpyxl
> (`tools/uw_template/_patch_v5_to_v51_metadata_cells.py`). The cell-level
> fidelity diff (sheets / merged ranges / defined names / cell counts /
> ArrayFormula objects) appeared clean, but a deeper xlsx-zip-part
> inventory diff caught that `wb.save()` silently dropped
> **`xl/metadata.xml`** (the `XLDAPR`/`fDynamic` block that the v0.4.3
> Section R/S spilled-range formulas depend on) and **`xl/webextensions/`**
> (Claude-for-Excel add-in taskpane). Template restored from git; this
> brief reverted to **Pending operator**. **The openpyxl path is off the
> table for this template** — both cells must be authored externally in
> Excel via Cowork. See openpyxl quirk #6 in CLAUDE.md for the technical
> detail.

---

**Status:** Pending operator
**Template version:** v5 → v5.1 (proposed — minor)
**Registry version:** 0.3.0 → 0.3.1 (will bump on receipt of v5.1)
**Triggered by:** UWT v0.4.0 v5 absorption (2026-05-26). Two `gap_target` concepts explicitly deferred to v5.1 in the `open_questions` block; plus a third concept that v5 actually closes structurally but whose registry status is stale.
**Owner (Claude Code side):** Track 4 chat (UWT v0.4.3, 2026-05-26)
**Owner (operator side):** Cowork → Excel

## Summary

v5 closed 7 of the 10 gap_targets the prior handoff requested — three remain. Of those three:

- **One needs an Excel edit (provenance):** Cover sheet has no version-stamp cell. Adding a single cell at `Cover!F1` (or operator's pick) lets the writer stamp the Analyzer substrate version into each populated copy.
- **One needs an Excel edit (RR metadata):** Rent Roll Analysis row 5 has a `Date:` label at A5 with `=TODAY()` at D5 — that's the file-open date, not the RR period. A dedicated period-date cell on Rent Roll Analysis row 5 would let the writer surface the actual rent-roll as-of date.
- **One is a registry cleanup, no Excel work:** `t12_period_date` is still tagged `gap_target` in the registry but v5 actually closed it structurally — `T-12 Analysis!B56:M56` are formula-fed from the Layer 1 raw paste at row 122 in v5 (the registry's note describing the cells as hardcoded `Apr-25..Mar-26` is stale from v4). The writer doesn't need a target; the template derives months from the on-sheet raw T12 paste. Reclassify to `derived_in_template`.

This handoff is **minor** — two single-cell additions, no row inserts, no column inserts, no chart changes, no styling-band coordination needed.

---

## Template-side changes required

### 1. `Cover!F1` (or operator's preferred location) — Substrate version stamp cell

- **Current state in v5:** `Cover!A1` is the title `ASSISTED LIVING FACILITY — INVESTMENT SUMMARY`. Cells `B1:K1` are empty.
- **After (proposed):** New cell at `Cover!F1` (or wherever sits cleanly above the existing data band) carrying the substrate version. Adjacent label cell, e.g. `Cover!E1 = "Substrate:"`. Writer populates `F1` at populate-time from `Cover!B8` of the Analyzer (currently `v0.2.14`).
- **Styling:** Small (Calibri 9pt italic gray `FF595959`), right-aligned. Matches the v0.2.11 `Dashboard!N1` "Last updated" stamp pattern in the Analyzer (BL-0021).
- **Data validation / named ranges:** None.
- **Why:** Closes `gap_target` concept `substrate_version`. Provenance — when a populated UW Template lands on someone's desk three months from now, the substrate version is the single most useful piece of context for debugging discrepancies between the Analyzer build and the populated template's numbers.
- **Operator's call:** location. F1 is suggested; if you'd rather put it somewhere quieter (e.g. `Cover!K1`, or a "Workbook info" footer band at the bottom of Cover), pick what reads cleanest.

### 2. `Rent Roll Analysis!<cell>` — Rent Roll Period (as-of) cell

- **Current state in v5:** Row 5 has `A5: "Date:"`, `C5: "Property:"`, `D5: =TODAY()`, `E5: "Lic Beds (Prop):"`, `F5: ='Prop Info'!B15`. The `=TODAY()` at D5 evaluates to the file-open date (volatile), which is fine for "when was this diagnostic last refreshed" but doesn't carry the RR's period date. `B5` is empty.
- **After (proposed):** Two options:
  - **Option A (minimum-change):** Use `B5` as the RR period cell. `A5` already says `Date:`. Writer populates `B5` at populate-time from the Analyzer's `RR_Period_Date` named range (resolves to `Rent Roll Recon!B2`). Leave `D5 = TODAY()` alone — it remains the diagnostic refresh date.
  - **Option B (explicit-label):** Repurpose row 5 — `A5 = "RR Period:"`, `B5 = <RR period date, writer-populated>`, `C5 = "Diagnostic refreshed:"`, `D5 = TODAY()` (unchanged), `E5/F5` unchanged. Slightly clearer for an underwriter reading the file.
- **Styling:** Number format `mm/dd/yyyy` to match the date convention used in the rent roll body. Bold label, plain date value (matches the `E5/F5` band).
- **Data validation / named ranges:** None — but if `B5` becomes a named cell (e.g. `Template_RR_Period`), downstream waterfall / scenarios sheets could reference it instead of `Rent Roll Recon!B2` indirection.
- **Why:** Closes the `open_question` deferred to v5.1 ("Rent Roll Analysis tab-header Period Date metadata cell"). Also folds in the long-standing `proposed`-status `rr_period_date` concept (registry note: "Confirm format expectations").
- **Recommendation:** Option A — single-cell change, no label rework, preserves the existing D5 `=TODAY()` semantics.

---

## Mapping updates

Coupled registry edits to apply on receipt of `Sample Files/ALF_UW_Template_v5.xlsx` (re-upload after v5.1 author work). Bump `registry_version` `0.3.0` → `0.3.1`.

### Per-concept changes

| Concept key | Current status | Current v5 target | After v5.1 | Why |
| --- | --- | --- | --- | --- |
| `substrate_version` | `gap_target` | `null` | `mapped` → `{sheet: "Cover", address: "F1", label_at: "E1"}` (or operator's pick) | New cell exists |
| `rr_period_date` | `proposed` | `{sheet: "Rent Roll Analysis", address: "B5", label_at: "A5"}` | `mapped` | Format confirmed; cell populated by writer |
| `t12_period_date` | `gap_target` | `null` | `derived_in_template` — note: `B56:M56` formula-fed from on-sheet Layer 1 raw paste at row 122 in v5; writer has no target to write to and doesn't need one | Registry note was stale from v4 — no Excel work, registry-only correction |

### `open_questions` cleanup

Of the 8 currently in `registry.json`:

- ✓ #7 Cover substrate version stamp — closes when v5.1 cell exists.
- ✓ #8 Rent Roll Analysis tab-header Period Date — closes when v5.1 cell exists.
- ✓ #4 Date header at A5/B5 format — closes alongside #8 (format confirmed in v5.1 author work).

The following stay open (separate from this handoff):

- #1 Bad Debt placement (`N62` vs `N106`) — writer-scope decision, see "Writer-scope decisions" below.
- #2 2nd Person Revenue source (UW Output extension vs writer-side RR rollup) — writer-scope decision, doesn't block v5.1.
- #3 Monthly grid `B-M` — accept blank for v0.1.
- #5 Rent Roll Analysis rows 1-209 derived framing — already confirmed, ambient note.
- #6 AR aging row-level routing — upstream-blocked; needs resident-key join in `AR & Collections` substrate before AR concepts move off `gap_source`. Not v5.1 work.

### Re-run after registry edits

```
python tools/uw_template/build_mapping_artifacts.py
```

---

## Writer-scope decisions

These don't block v5.1 author work — they're answers the operator can give whenever. Recording them here so they're not forgotten.

### D1. Bad Debt placement — `N62` (revenue contra) vs `N106` (opex)?

- **Context:** v5 template has cells at both `T-12 Analysis!N62` (revenue contra-line in GPR waterfall band) and `T-12 Analysis!N106` (opex line). Analyzer's UW Output row 57 is a single "Bad debt expense" value. Writer currently writes to N62 only (registry's `_SPECIAL_SKIP_KEYS` blocks `opex_bad_debt_expense` at N106 to avoid double-counting).
- **Recommendation:** Confirm N62-only as the contract. ALF UW convention treats write-offs as revenue contra (the GL never recognizes the receivable as revenue), not opex. N106 stays in v5 as a vestigial slot — either delete it from v5.1 or leave it labeled but unpopulated.

### D2. 2nd Person Revenue — UW Output extension or writer-side RR rollup?

- **Context:** Template has a 2P Revenue row at `T-12 Analysis!N67`. UW Output doesn't break 2P out — 2P amounts are captured per-bed at `Rent Roll Input!V` and folded into Total Monthly Rev. Concept `second_person_revenue` is `gap_source` (source-side missing the breakout, not target-side missing the slot).
- **Recommendation:** Writer-side rollup from `Rent Roll Input!V` (sum × 12). Lowest friction; substrate change avoided. Defer to next writer iteration; not blocking v5.1.

---

## Verification checklist

### Operator side (in Excel after authoring v5.1)

- [ ] `Cover!F1` (or equivalent) carries a small italic gray version-stamp cell, with adjacent label.
- [ ] `Rent Roll Analysis!B5` exists as a date cell formatted `mm/dd/yyyy` (per Option A recommendation), ready to receive the RR period date from the writer.
- [ ] All v5 chart objects preserved.
- [ ] All v5 formula-derived columns preserved (`Rent Roll Analysis` cols V, X, Y, Z, AA, AB, AS, AQ — yes, AQ Total Ancillary is template-formula-owned).
- [ ] No round-trip through Google Sheets / LibreOffice (BL-0018 lesson — `_xludf.minifs` prefix corruption).
- [ ] File dropped at `Sample Files/ALF_UW_Template_v5.xlsx` (overwriting in place — same file name; v5.1 isn't a new file, just a minor revision).
- [ ] Optionally also drop a copy at `assets/ALF_UW_Template_v5.xlsx` (the committed canonical copy in the repo's `assets/` folder — the writer's `BUNDLED_UW_TEMPLATE_PATH` falls back to this when no override is uploaded).

### Claude Code side (next chat, on receipt of v5.1)

- [ ] Verify file presence and inspect new cells with openpyxl to capture exact addresses.
- [ ] Update `registry.json`:
  - [ ] `registry_version` `0.3.0` → `0.3.1`.
  - [ ] `substrate_version` concept: `targets.v5 = {...}`, status `gap_target` → `mapped`.
  - [ ] `rr_period_date` concept: status `proposed` → `mapped`.
  - [ ] `t12_period_date` concept: status `gap_target` → `derived_in_template`; rewrite the stale `notes` field describing v4 hardcoded headers.
  - [ ] Close open_questions #4, #7, #8.
- [ ] Re-run `python tools/uw_template/build_mapping_artifacts.py`.
- [ ] Re-run writer smoke + Homestead e2e — confirm `substrate_version` and `rr_period_date` now report `written` in `PopulateReport`.
- [ ] Bump UWT version `v0.4.3` → `v0.5.0` if writer behavior changed; `v0.4.4` if registry-only.
- [ ] Add `CHANGELOG-UWT.md` entry.
- [ ] Mark this handoff **Verified** in [HANDOFF_TRACKER.md](../HANDOFF_TRACKER.md).

---

## Cross-references

- **Prior handoff (superseded):** [`2026-05-25-uwt-v4-to-v5-template-gaps.md`](2026-05-25-uwt-v4-to-v5-template-gaps.md)
- **Spec:** [`SPEC-UWT.md`](../../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../../CHANGELOG-UWT.md) — v0.4.0 (v5 absorption) → v0.4.3 (Section R/S formula fill-downs) the immediate predecessors
- **Writer module:** [`uw_template_writer.py`](../../../uw_template_writer.py)
- **Authoritative handoff contract:** `Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md` (external)
- **Registry entries affected:** `substrate_version`, `rr_period_date`, `t12_period_date`
- **Substrate version mapped against:** v0.2.14 (no substrate change required)

## Notes for Cowork

- This is a **minor** revision of v5 — two single-cell additions. Author directly in `ALF_UW_Template_v5.xlsx` (don't fork to a new filename); the writer treats v5 and v5.1 as the same `template_version='v5'` binding. The registry change is in the concept entries, not in the `templates.v5` block schema.
- Both cells are above the data bands — zero risk of disturbing the rent roll paste anchor or T-12 Analysis layout.
- The v5 template already addresses the monthly-header concern that the prior handoff worried about (`T-12 Analysis!B56:M56` are `=C122..=N122` formulas in v5 — fed from the on-sheet raw T12 paste at row 122). No author work needed there; the registry just needs to catch up.
