# CHANGELOG-MF

Release log for the **MF** (multifamily) product line. Newest at top.

See `SPEC-MF.md` for the current spec and `CLAUDE.md` for product-line phasing
and the `mf_` naming convention.

---

## registry v0.1.1 — 2026-06-03 — Second MF T-12 format logged (QuickBooks nested P&L)

A new operator T-12 (Blairstone at Governors Square, Tallahassee FL — deal
`MF_FL_Tallahassee_Blairstone`) surfaced a **second MF T-12 format**: a
QuickBooks-style nested P&L (parent/sub-account indenting, leaf labels in col E
or F, 12 monthly values in odd columns G–AC, TOTAL in AE, no account numbers) —
materially different from Hidden Lakes' flat PSI export. Mapped by hand to
`_StdCOA` (39 leaf lines; income ties to $5,805,382.10; expense detail
$2,415,119.35); a paste-ready col-P CSV was saved beside the source file in the
deal folder for drop-in to the model's `T-12 Analysis` Layer 1.

Logged as `open_questions` item #8 so the future `mf_t12` parser handles both
formats. Data-quality caveats recorded: cash-basis collected rent (GPR bucket =
collected, not market — no Vacancy/Concessions/Bad-Debt lines); no Real Estate
Taxes or Management Fee lines (entity-level → pro-forma needed); a negative
`Water and Sewer Tenant` billback inside expenses (→ Utility Reimbursement); and
a $22,128.62 total-vs-detail gap living only in the broker's subtotal/Total
rows (QuickBooks export artifact). Registry `0.1.0 → 0.1.1`; artifacts
regenerated. No concept or target change — registry shape unchanged at 46
concepts.

---

## MF-UWT v0.1.0 — 2026-06-03 — MF Track 4 Phase 0: UW Model mapping registry

**Track:** MF Track 4 (UW Model integration). Inspection + mapping only — no
parser, no writer.

Operator dropped `MF_UW_Model_v15.xlsx` (23-sheet full multifamily acquisition
underwriting model) and asked to begin integrating the MF UW template mapping.
This release inspects the model cell-by-cell, reverse-engineers the two
data-intake paste paths, and builds the MF mapping registry + tooling scaffold,
mirroring the ALF Track 4 Phase-0 pattern.

**Shipped:**
- **Reference copy** committed to `assets/MF_UW_Model_v15.xlsx` (48 zip parts —
  `xl/metadata.xml` + `xl/webextensions/` intact; faithful byte-copy of the
  operator's Deals-folder file).
- **`tools/mf_uw_template/registry.json`** (`registry_version` 0.1.0, schema
  `mf-uw-mapping/v1`) — 46 concepts across the `metadata` / `rent_roll` / `t12`
  paths; `templates.v15` block; `_StdCOA` bucket vocabulary (18 expense + 26
  income); `intake_targets_unmapped` for the analyst-driven + formula-derived
  surface; 7 open questions. Status rollup: **19 mapped / 5 proposed / 21
  gap_source / 1 derived**.
- **`tools/mf_uw_template/build_mapping_artifacts.py`** — generator ported from
  the ALF version, adapted for the MF source systems (`mf_rr`,
  `mf_rr_sortable`, `mf_ar`, `mf_t12`) and the metadata/rent_roll/t12 paths.
- **Artifacts** generated: `MAPPING_TRACKER.md`, `mapping_tracker.csv`,
  `mapping_mindmap.html`.
- **Handoff infra:** `HANDOFF_TRACKER.md`, `HANDOFF_TEMPLATE.md`, and the first
  brief `handoffs/2026-06-03-mf-uwt-phase0-inspection.md` (Verified).
- **Docs:** `SPEC-MF.md` (new — MF spec, §1 UW Model mapping) and this
  changelog. CLAUDE.md gained an MF Track 4 section.

**The two intake paste paths (reverse-engineered):**
1. **Rent Roll → `Rent Roll Analysis` grid** — header row 272, anchor `A273`,
   rows 273–1772 (1,500-unit capacity), 37 cols A–AK. AR aging in Q–T (joined
   from the separate AR doc on Bldg-Unit); per-unit ancillary income breakouts
   in W–AK mirroring `_StdCOA`.
2. **T-12 → `T-12 Analysis` Layer 1** — header row 105, anchor `A106`, rows
   106–255. Col P (`→ MAPPING`) carries the `_StdCOA` bucket per raw line and
   drives every Layer-3 SUMIFS — the MF equivalent of ALF's Description_Map.

**Source grounding:** mapped against the raw Hidden Lakes operator exports in
`MF Docs/` (Yardi-CIM RR, redIQ Sortable-RR, PSI T-12 Cash-Basis, Resident Aged
Receivables) since MF has no Analyzer substrate.

**Deferred (the 21 gap_source items) to the future MF parser build (P1–P2):**
the T-12 PSI-account → `_StdCOA` mapping dictionary, the AR Bldg-Unit join, the
redIQ charge-code → ancillary-bucket breakouts (W–AK), and the status-taxonomy /
Legal-flag normalization. No `mf_*` parser or writer code exists yet — Phase 0
is registry + docs only, exactly as ALF Track 4 started.

**No model-side change requested** — v15 is complete and self-consistent; the
gaps close on the source/parser side, not via Excel edits.
