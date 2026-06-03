# CHANGELOG-MF

Release log for the **MF** (multifamily) product line. Newest at top.

See `SPEC-MF.md` for the current spec and `CLAUDE.md` for product-line phasing
and the `mf_` naming convention.

---

## MF v0.2.1 — 2026-06-03 — MF mode goes live: T-12 intake in the app

Replaces the Phase-0 "Coming Soon" placeholder in MF mode with a **working T-12
uploader** — MF mode is no longer a dead stop. `app.py`:
- New `_render_mf_intake()` (replaces `_render_mf_placeholder()`): a T-12
  `file_uploader` → `parse_mf_t12()` → metrics (detected format / GL lines /
  coverage / period), a **reconciliation table** (computed income/expense/NOI
  vs the statement's own totals), a **standardized-bucket** table (the col-P
  values), parser warnings, and a **download button** for the paste-ready
  mapping CSV (Acct# / Account Name / 12 months / → MAPPING) ready for the MF UW
  Model's `T-12 Analysis` Layer 1 (anchor `A106`).
- New `_mf_t12_paste_csv(res)` helper; `from mf_t12_normalizer import parse_mf_t12`.

`app.py` compiles; the path is smoke-tested end-to-end (Hidden Lakes PSI → 80-row
CSV, 100% coverage, correct 12-month headers). This is the operator-requested
"unblock upload now" slice — RR / AR / OM uploaders and the MF UW Model writer
land next in the same tab.

---

## MF v0.2.0 — 2026-06-03 — MF parser build slice 1: T-12 normalizer + COA classifier

First real `mf_*` code — the foundation of the MF intake pipeline (the full
build, chosen by the operator, is RR + T-12 + AR → write into the MF UW Model;
this slice ships the T-12 path end-to-end). Promotes the COA seed into a live
classifier and a general 5-format T-12 parser.

**Shipped:**
- **`mf_mappings.py`** — MF closed vocabularies. Loads `coa_seed.csv` (single
  source of truth) into the layered classifier `classify_t12_account(acct, name)`
  (Yardi 5-digit account root → `70000-89999` EXCLUDED range → ordered
  name-regex → `— UNMAPPED —`). Income/expense bucket sets + `bucket_side()`;
  RR status taxonomy `normalize_status()`. No openpyxl dependency.
- **`mf_t12_normalizer.py`** — `parse_mf_t12(path|bytes|file)` → `MFT12Result`.
  **General by design** (not per-format branches): auto-detects the month-header
  row, the monthly column set (contiguous *or* odd-spaced), the total column,
  and account-number presence; extracts leaf GL lines (Yardi rollup-suffix
  `-098/-099/-199/-090/-999` exclusion + valued-vs-header logic), classifies
  each, and reconciles **by source section** (so utility-rebill contras in the
  expense section reduce opex instead of mis-summing as negative income).
  Emits 12-month vectors, format guess, coverage, and warnings.
- **`tests/test_mf_t12_normalizer.py`** — 15 CI-runnable classifier unit tests +
  5 end-to-end reconciliation cases (skip when the gitignored deal files are
  absent).

**Validation (all 5 catalogued formats, 100% leaf-coverage each):**
| Deal | Format | Income | Expense | NOI |
| --- | --- | --- | --- | --- |
| Hidden Lakes | PSI flat | — | — | $98,969 ✓ |
| Avana | Yardi | $5,346,350 ✓ | $1,807,466 ✓ | $3,538,884 ✓ |
| Ascend | Yardi/YSI | $3,572,817 ✓ | $1,520,302 ✓ | $2,052,515 ✓ |
| Copeland | Tzadik | $5,016,397 ✓ | $1,577,564 ✓ | $3,438,833 ✓ |
| Blairstone | QuickBooks | $5,805,382 ✓ | $2,415,119 △ | $3,390,263 △ |

△ Blairstone expense/NOI differ by exactly **$22,128.62** — the QuickBooks
total-vs-detail artifact in the broker's own subtotal rows (no matching detail
line). The parser's detail sum is the correct figure; surfaced as a warning.

**Seed update:** `coa_seed.csv` name rules broadened (199 acct + 44 name rules)
to close the name-only-chart tail (Online Ad, Painting, Lighting, Health, Vacant
Units, Risk Fees, G&A admin accounts, Laundry).

**Still to build (this is slice 1 of the operator's full-intake choice):**
`mf_normalizer` (RR) → `mf_ar_parser` (AR + Bldg-Unit join) → `mf_uw_model_writer`
(paste into the model + metadata restore) → `app.py` MF intake tab (replaces the
Phase-0 placeholder; 3 uploaders + download populated model).

---

## registry v0.1.2 — 2026-06-03 — COA → _StdCOA seed dictionary built + validated (5 T-12 formats)

Three more operator T-12s (Avana Stoney Ridge VA, Ascend Brunswick Village NC,
Copeland Village FL) brought the catalogued MF T-12 formats to **five**: PSI
flat, QuickBooks nested, **Yardi numbered ×2**, and Tzadik/AppFolio name-only.
Avana + Ascend share the **identical Yardi standard chart** (41000 Market Rent,
41100 Vacancy, 51010 Mgmt Salaries, 61030 Mgmt Fee, 62xxx Taxes, 63xxx
Insurance, 70000–89999 below-the-line) — so one account-number dictionary covers
every Yardi property.

**Shipped:**
- **`tools/mf_uw_template/coa_seed.csv`** — the COA → `_StdCOA` seed dictionary:
  199 `acct_root` rules (Yardi 5-digit chart) + a `70000-89999 → — EXCLUDED —`
  range + 43 ordered `name_regex` rules (for the no-account-number charts).
- **`tools/mf_uw_template/_seed_validate.py`** — local validation harness
  (per-format leaf extractors + the seed) reporting coverage. **100% of GL leaf
  lines classified** on Avana (156), Ascend (161), Copeland (65); plus Hidden
  Lakes (PSI via `_StdCOA` col F) and Blairstone (QuickBooks hand-map).
- **`tools/mf_uw_template/COA-SEED.md`** — format catalog (detection signatures
  per software), seed structure, validation results, and the caveat/anomaly log
  (utility-rebill section reconciliation; below-NOI exclusions; entity-level
  Mgmt-Fee/RE-Tax gaps; Copeland `Dues` $539,712.92 anomaly flagged).

This is the seed `mf_mappings.py` is promoted from at the parser build's first
slice (SPEC-MF §2.4 / §2.8 updated). Registry `0.1.1 → 0.1.2`; `open_questions`
updated (format catalog + seed recorded; 10 items); artifacts regenerated. No
concept/target change — still 46 concepts.

The five deals become the parser's regression-fixture set. `_seed_validate.py`
reads gitignored deal files by absolute path — a local prototype, **not** the
production parser.

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
