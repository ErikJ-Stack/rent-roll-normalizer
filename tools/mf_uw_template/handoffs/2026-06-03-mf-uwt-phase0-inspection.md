# MF UW Model Handoff — `2026-06-03-mf-uwt-phase0-inspection`

---

**Status:** Verified (MF-UWT v0.1.0 / 2026-06-03)
**Model version:** v15 (inspected, committed reference to `assets/`)
**Registry version:** — → 0.1.0
**Triggered by:** Operator request 2026-06-03 — "let's move forward with integrating MF UW Template mapping"; operator dropped `MF_UW_Model_v15.xlsx`.
**Owner (Claude Code side):** MF Track 4 chat
**Owner (operator side):** Excel (model author)

## Summary

First MF Track 4 deliverable. The operator provided `MF_UW_Model_v15.xlsx` — a
23-sheet full multifamily acquisition underwriting model. This chat inspected it
cell-by-cell and reverse-engineered the **two data-intake paste paths**, then
built the MF mapping registry + tooling scaffold, mirroring the ALF Track 4
Phase-0 pattern (registry + artifacts + handoff infra; **no writer**). The
registry maps the raw operator intake docs in `MF Docs/` (Hidden Lakes) to the
two model targets. Because MF has no Analyzer substrate and no `mf_*` parser yet
(MF phases P1–P4 unbuilt), every concept that requires parser intelligence is
honestly flagged `gap_source` for the future MF intake build.

## What was inspected (model structure)

**Two intake paste paths** (the only writer targets; everything else is
analyst-driven or formula-derived):

1. **Rent Roll → `Rent Roll Analysis` grid.** Header row 272, paste anchor
   `A273`, data rows 273–1772 (1,500-unit capacity). 37 columns A–AK:
   identity (A Bldg / B Unit# / C Type / D SF / F Resident), status (E Status /
   G Legal-boolean from `**` name prefix), dates (H–K), rates (L Mkt / M Actual
   / N Sched / P Deposit), AR (O Balance / Q–T aging buckets), U Status Flag,
   V Notes, and **W–AK per-unit ancillary income breakouts** mirroring the
   `_StdCOA` other-income buckets. Rows 1–271 are formula-derived diagnostic
   dashboards (health check, status taxonomy, GPR reconciliation, lease
   expiration, days-vacant, tenure cohort, AR aging summary, top-10 delinquent)
   — writer must not overwrite.

2. **T-12 → `T-12 Analysis` Layer 1.** Header row 105, paste anchor `A106`,
   data rows 106–255. Cols: A Acct# / B Account Name (raw) / C–N 12 monthly /
   O T-12 Total (template `=SUM`) / **P → MAPPING** (`_StdCOA` bucket string).
   Col P drives every Layer-3 SUMIFS — it is the intelligence layer, the MF
   equivalent of ALF's `Description_Map`. Rows 1–101 (diagnostics + Layer-3
   standardized aggregation) and 257–262 (raw totals reconciliation) are
   formula-derived — writer must not overwrite.

**`_StdCOA`** (hidden sheet) is the bucket master list — 18 expense + 26 income
buckets. Col F lists the PSI source account numbers each bucket maps from
(seed for a future COA→bucket dictionary).

The intake anchors were confirmed from the model's own `Data Checklist`
cross-check formulas: `'T-12 Analysis'!N80` = EGI, `'Rent Roll Analysis'!I5` =
units-in-RR, `C94` = Total AR, `B113`/`D113` = legal/eviction cohort.

## Source side (operator docs in `MF Docs/`, Hidden Lakes — 143 units)

| Doc | Format | Maps to |
| --- | --- | --- |
| `RR-Hidden-Lakes-4-16-26.xlsx` | Yardi-CIM "Rent Roll - Cim", hdr row 7 | RR grid cols A–P (core) |
| `AR-Hidden-Lakes-3-31-26.xlsx` | Resident Aged Receivables, hdr row 6 | RR grid cols Q–T + V (join on Bldg-Unit) |
| `Sortable-RR-Hidden-Lakes-4-16-26.xlsx` | redIQ export (Floor Plan / Rent Roll / **Source Data** charge codes) | RR grid cols W–AK ancillary breakouts |
| `T12-NOI-Hidden-Lakes-3-31-26.xlsx` | PSI T-12 Income Statement, Cash Basis, hdr row 7 | T-12 Layer 1 cols A,B,C–N |

## Mapping result (registry 0.1.0 — 46 concepts)

| Status | Count | What |
| --- | --- | --- |
| `mapped` | 19 | Direct header/label matches: RR identity/dates/rates, T-12 acct/name/monthly block, property name, unit count. |
| `proposed` | 5 | Status taxonomy, Legal flag derivation, Notes, period dates — direction clear, exact rule/cell to confirm at writer time. |
| `gap_source` | 21 | Needs parser intelligence: AR aging Q–T (Bldg-Unit join), the 15 ancillary breakouts W–AK (redIQ Source Data charge codes), the T-12 col-P `_StdCOA` mapping, col-U Status Flag. |
| `derived` | 1 | T-12 Total col O (template `=SUM`; writer must not overwrite). |

No `gap_target` — the model has a column for everything the intake produces.

## Model-side changes required

**None.** This handoff is inspection + mapping only. The v15 model is complete
and self-consistent; no operator Excel edit is requested. The `gap_source`
items resolve in a future **parser build (MF P1–P2)**, not via model edits.

## Mapping updates

- **New registry** `tools/mf_uw_template/registry.json` at `0.1.0` —
  `templates.v15` block, `_StdCOA` bucket vocabulary, 46 concepts across the
  `metadata` / `rent_roll` / `t12` paths, `intake_targets_unmapped` for the
  analyst-driven and formula-derived surface.
- **New generator** `build_mapping_artifacts.py` (port of the ALF generator,
  adapted for the MF source systems `mf_rr` / `mf_rr_sortable` / `mf_ar` /
  `mf_t12` and the metadata/rent_roll/t12 paths).
- **Artifacts** regenerated: `MAPPING_TRACKER.md`, `mapping_tracker.csv`,
  `mapping_mindmap.html`.

## Writer-scope decisions (deferred to the future MF parser build)

- **COA→bucket mapping (`t12_mapping`).** Should the PSI-account→`_StdCOA`
  dictionary live in a future `mf_mappings.py` (analogous to ALF's
  Description_Map) or as a lookup tab in the model? *Recommendation:*
  `mf_mappings.py`, keyed on account number with a name-regex fallback; seed
  from `_StdCOA` col F.
- **AR join.** Confirm Bldg-Unit is a stable join key across RR and AR docs and
  decide how to handle the period mismatch (RR Apr 2026 vs AR Mar 2026).
- **Ancillary breakouts.** Confirm the redIQ Sortable-RR `Source Data`
  charge-code grid is the canonical source for W–AK, and whether the basic RR
  is ever the only doc available (then W–AK stay blank).
- **Status taxonomy.** Lock the operator-status → template-status string map
  (the COUNTIF wildcards expect `Occupied*`, `Vacant Unrented Ready/Not Ready`,
  `Down*`, `Vacant*Leased*`/`Vacant Rented*`, `Model`/`Employee`/`Office`).

## Verification checklist

**Claude Code side (this chat):**
- [x] Reference copy committed at `assets/MF_UW_Model_v15.xlsx` (48 zip parts, intact — metadata.xml + webextensions preserved).
- [x] `registry.json` authored at `0.1.0`; loads clean; 46 concepts.
- [x] `build_mapping_artifacts.py` runs; MD/CSV/HTML regenerated.
- [x] `SPEC-MF.md` + `CHANGELOG-MF.md` seeded; CLAUDE.md MF Track 4 section added.
- [x] Handoff marked Verified.

## Cross-references

- **Spec:** [`SPEC-MF.md`](../../SPEC-MF.md)
- **Changelog:** [`CHANGELOG-MF.md`](../../CHANGELOG-MF.md)
- **Registry entries affected:** all 46 (new registry).
- **Source docs:** `MF Docs/` (gitignored).
- **Model source of truth (external):** `Deals/Acquisition/_Template/MF Templates/MF_UW_Model_v15.xlsx`.

## Notes for the operator / Cowork

- The committed `assets/MF_UW_Model_v15.xlsx` is a faithful byte-copy of the
  Deals-folder file (48 parts, including `xl/metadata.xml` for dynamic arrays
  and `xl/webextensions/`). If you revise the model, author in Excel and re-drop
  — do **not** round-trip through Python/openpyxl (drops metadata.xml → breaks
  any dynamic-array spills; openpyxl quirk #6) or Google Sheets / LibreOffice.
- The next MF Track 4 step is the **parser/writer (MF P1–P2)**, which closes the
  21 `gap_source` items. That is a separate, larger build — not part of Phase 0.
