# MF UW Model Handoff Tracker

Running log of changes Claude Code has made (or proposed) that require operator
action in the **MF UW Model** (`MF_UW_Model_v20.xlsx`, authored externally in
Excel). Newest at top.

This file is the **index**. Each row links to a dated handoff brief in
[`handoffs/`](handoffs/) with the full detail. New handoffs are created from
[`HANDOFF_TEMPLATE.md`](HANDOFF_TEMPLATE.md).

## Why this exists

The MF UW Model is the multifamily counterpart of the ALF UW Template. Per the
Track 4 ownership split, **the model is authored externally** (operator → Excel,
optionally via Cowork); Claude Code owns the **registry**
([`registry.json`](registry.json)) and — in a later phase — the **writer** /
parser (`mf_*` modules, not yet built).

When Claude Code work surfaces a model-side change — a missing column, a needed
new row, a structural addition — the chat that surfaced it produces a handoff
brief here instead of editing the model itself. The operator then picks up the
brief and authors the change in Excel.

## Important difference from the ALF track

MF has **no Analyzer substrate** and **no parser yet** (MF phases P1–P4 are
unbuilt — see CLAUDE.md). The "source" for the mapping is the raw operator
exports in `MF Docs/` (Hidden Lakes: redIQ / PSI / Yardi-CIM). The Phase-0
registry maps those raw shapes to the two model intake targets; a future
`mf_*` normalizer will standardize the source side and a writer will paste.
Until then, every concept that needs parser intelligence (COA→bucket mapping,
AR resident-key join, ancillary charge-code breakouts, status taxonomy) sits at
`gap_source`.

## When to create a new handoff

Trigger conditions (any one is enough):

- A registry entry's target cell changes (a model column/row shifts in a new
  model version).
- A new model version is dropped (e.g. v15 → v16).
- A `gap_target` surfaces — the intake produces a value the model has no column
  to receive.
- A writer-scope decision needs operator input that depends on model structure.

If a Claude Code change only touches the registry/artifacts without implying a
model-side edit, no handoff is needed.

## Index

| Date | Handoff | Model version | Registry version | Status | Summary |
| --- | --- | --- | --- | --- | --- |
| 2026-06-21 | [MF UW Model v20 absorption](handoffs/2026-06-21-mf-uwt-v20-absorption.md) | v15 → **v20** (committed to `assets/`) | 0.2.0 → **0.3.0** | **Verified** (MF v0.7.0 / 2026-06-21) — operator-authored, absorbed same session | Operator dropped `MF_UW_Model_v20.xlsx` ("update the MF template use; review the mapping"). Verified cell-by-cell: **all four writer target sheets (T-12 Analysis @106, Rent Roll Analysis @273 cols A–AK, Prop Info col B, Rental Comps @8) are layout-identical to v15 → zero concept target moved.** v20 deltas are display/formula-only: **+`Dashboard` sheet** (idx 1; sheet_count 23→24), **+ per-row chart-helper formula cols AL–AP** on Rent Roll Analysis (outside the writer's A–AK clear band → preserved), and a **new `xl/metadata.xml`** (Excel-365 dynamic arrays, 7 `cm` cells) that the writer's `_restore_dynamic_arrays` — a no-op on v15 — now actively preserves (7→7 verified). Bundled asset + `BUNDLED_MF_MODEL_PATH`/`_VERSION` + writer docstring repointed; `templates.v20` added with `targets.v20` verbatim-inherited on all 90 concepts; artifacts regenerated; writer test repointed to v20 + new `test_dynamic_arrays_preserved`. No operator follow-up required. |
| 2026-06-03 | [MF Track 4 Phase 0 — model inspection + mapping registry](handoffs/2026-06-03-mf-uwt-phase0-inspection.md) | v15 (inspected, committed to `assets/`) | — → **0.1.0** | **Verified** (MF-UWT v0.1.0 / 2026-06-03) — registry + artifacts + docs shipped; no writer | Operator dropped `MF_UW_Model_v15.xlsx` (23-sheet full MF acquisition model). Inspected cell-by-cell; reverse-engineered the two intake paste paths — **(1) operator RR (+AR aging) → `Rent Roll Analysis` grid row 273+** (37 grid cols A–AK), **(2) operator T-12 → `T-12 Analysis` Layer 1 row 106+** (raw paste + col-P `_StdCOA` bucket mapping). Built `registry.json` (46 concepts: 19 mapped / 5 proposed / 21 gap_source / 1 derived), the artifact generator, and the MD/CSV/HTML trackers. Reference copy committed to `assets/MF_UW_Model_v15.xlsx`. **No `mf_*` parser/writer exists** — the source side is raw `MF Docs/` exports; everything needing parser intelligence (COA→bucket map, AR Bldg-Unit join, ancillary charge-code breakouts W–AK, status taxonomy) is flagged `gap_source` for the future MF intake build (P1–P2). 7 open questions logged. |

## Status legend

- **Pending operator** — handoff produced; waiting for the model to be updated in Excel.
- **In progress** — operator has started authoring; not yet dropped back in.
- **Applied** — new model file present in `assets/`; registry not yet updated to point at it.
- **Verified** — registry updated; artifacts regenerated; handoff is closed.
- **Superseded** — handoff is no longer the action plan; kept for audit trail, cross-linked to the replacement.

When a handoff hits **Verified** or **Superseded**, leave the row in place and
update its Status. Newer handoffs slot in at the top.

## Mapping updates

Mapping updates ride **inline in each handoff**. The authoritative full-state
artifacts are regenerated by
[`build_mapping_artifacts.py`](build_mapping_artifacts.py):

- [`registry.json`](registry.json) — source of truth.
- [`MAPPING_TRACKER.md`](MAPPING_TRACKER.md) — human-readable.
- [`mapping_tracker.csv`](mapping_tracker.csv) — diffable.
- [`mapping_mindmap.html`](mapping_mindmap.html) — interactive.

Re-run `python tools/mf_uw_template/build_mapping_artifacts.py` after any
registry edit.
