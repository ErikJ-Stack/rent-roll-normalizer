# CHANGELOG-MF

Release log for the **MF** (multifamily) product line. Newest at top.

See `SPEC-MF.md` for the current spec and `CLAUDE.md` for product-line phasing
and the `mf_` naming convention.

---

## MF v0.5.0 — 2026-06-04 — OM (Offering Memorandum) intake ships (Track 4-MF P3)

Closes the last big MF intake gap: the 4th operator doc type. A broker OM PDF now
extracts into the MF UW Model's **Prop Info** (property details + market block)
and **Rental Comps** (submarket comp set). This was the "OM intake — NOT BUILT"
open-question.

**New `mf_om_extractor.py`** — `parse_mf_om(source, *, engine="llm"|"basic",
api_key=None) -> MFOMResult`. PyMuPDF (`pymupdf`) extracts the OM text. Two
selectable engines:
- **LLM (default)** — hands the OM text to Claude with a structured-output tool
  schema (maximal scope: property facts, market/demographics, rent comps,
  broker pro-forma) and maps the validated JSON onto typed dataclasses
  (`MFPropInfo` / `MFMarketData` / `MFRentComp` / `MFProForma` / `MFOMResult`).
  Robust across the wildly different broker layouts (verified against three
  real OMs: MMG/Blairstone, IPA/Avana, CBRE/Ascend — each lays comps out
  differently). Needs the `anthropic` SDK + an API key (passed in or
  `ANTHROPIC_API_KEY`).
- **Basic (no-API fallback)** — deterministic labelled `label`/`value` scan with
  plausibility guards. Reliably gets the labelled PROPERTY DETAILS block
  (Blairstone: 7/8 fields; units+year+county on all three) but not the
  free-form comp/market tables. Why two engines: OMs are glossy marketing PDFs
  where deterministic parsing is genuinely brittle, so AI extraction is primary
  — but the operator can pick Basic to skip the API.

**Writer** (`mf_uw_model_writer.populate_mf_model(..., om=MFOMResult)`) — writes
Prop Info `B5:B47` (details + market) and Rental Comps `Q8:AD22` (15 comps max).
RR-derived units/name take precedence (the rent roll is authoritative). The
template's `Z`/`AA` (eff-rent, $/SF) formulas + the SUBJECT row 7 are preserved.
Bedroom counts derive from the OM unit-mix when not stated explicitly; occupancy
is written as a fraction (96% → 0.96). The broker **pro-forma is captured but
intentionally NOT written** — UW trusts the T-12, not the broker's projections.

**App** (`_render_mf_intake`) — OM PDF uploader + an extraction-engine radio
(AI / Basic) + an API-key field (or Streamlit secrets); summary metrics + a
comp-table preview; `om=` flows into the populate call.

**Registry → v0.2.0** — +44 OM concepts (33 Prop Info, 11 Rental Comps) mapped
to `templates.v15`; the Prop Info manual-input note narrowed to the residual
AI-Market-Research cells; OM open-question retired. 46 → **90 concepts** (63
mapped / 5 proposed / 21 gap_source / 1 derived). `tools/mf_uw_template/_add_om_concepts.py`
(idempotent) + artifacts regenerated.

**Tests** — `tests/test_mf_om_extractor.py` (9): coercers, the LLM JSON→dataclass
mapping, writer integration (cells + formula preservation, RR-override), and the
basic engine on the three real OMs (skipped when `MF Docs/OM/` fixtures absent).
All 36 MF tests green. `requirements.txt` += `pymupdf`, `anthropic`.

---

## registry v0.1.3 — 2026-06-03 — Prune stale open-questions after the parser build

Housekeeping: the registry's `open_questions` listed 10 items, but the MF parser
build (v0.2.0–v0.4.4) had already closed most. Pruned 10 → 5: kept the genuinely
open work (**OM intake**, the low-priority **redIQ Sortable-RR ancillary path**,
**Column U Status Flag**) plus two consolidated traceability/reference entries
(what the build resolved — COA dictionary / AR join / status taxonomy / W-AK
breakout / template versioning / subsidy-in-GPR; and the 5-T-12-format +
2-RR-shape catalog). `registry_version` 0.1.2 → 0.1.3; artifacts regenerated;
no concept/target change (still 46).

---

## MF v0.4.4 — 2026-06-03 — Refresh committed MF UW Model to operator's revised v15

Operator dropped a revised `MF_UW_Model_v15.xlsx` (still v15 filename — minor
revision; 325 KB → 385 KB, downstream/formatting changes). Refreshed the
committed reference `assets/MF_UW_Model_v15.xlsx` via a **verbatim byte-copy**
(no openpyxl round-trip — quirk #6).

**Pre-flight diff confirmed zero writer/registry impact:** identical 23 sheets,
and every writer-critical anchor unchanged — RR grid header (row 272, cols
A–AK), T-12 Layer 1 (row 105 / anchor A106), Prop Info A4/A6, `_StdCOA` (56
rows), and the key formulas (`N80`, `B58`, `I5`). So no `mf_uw_model_writer` /
registry changes; registry stays at `templates.v15`. Writer re-validated against
the new bytes — 10/10 assertions pass (RR grid, ancillary breakout AC, T-12
Layer 1, formula survival, Prop Info). 48 zip parts, valid.

---

## MF v0.4.3 — 2026-06-03 — Property name from the file header (not the filename)

On the populated Avana model the Cover title read **"Operations) Avana Stoney
Ridge"** — `derive_property_name()` (built for ALF filenames) mangles the
`(Operations)` in `"Rent Roll (Operations) - Avana Stoney Ridge 05.12.26.xlsx"`.
Fix: `parse_mf_rr` now extracts a clean `property_hint` from the RR's header band
(col A above the grid header — operator files carry a clean name like
"Avana Stoney Ridge"); the app uses `rr.property_hint or derive_property_name(...)`
so the Cover / Prop Info B4 / filename all show the real property. `MFRRResult`
gains `property_hint`. Verified: Avana → "Avana Stoney Ridge", Hidden Lakes →
"Hidden Lakes". (No change to the shared `derive_property_name`, so ALF is
unaffected.) The rest of the populated model was already correct — 263 units,
149 T-12 lines, EGI ~$5.0M computing.

---

## MF v0.4.2 — 2026-06-03 — RR charge-code breakout → per-unit ancillary columns (W–AK)

Operator note on the Avana RR: "Amenity Rent, Subsidy was not captured … col L
has different charge codes." The itemized parser (v0.4.1) **summed** all charge
codes into one scheduled total but didn't **break them out**, so Amenity Rent
etc. lost their identity in the model's per-unit ancillary columns.

**Shipped:**
- `mf_mappings.classify_charge_code(code)` — maps an RR charge code to a W–AK
  ancillary bucket (amenity / pet / parking / storage / valet / utility_reimb /
  late / application / mtm / admin / insurance_passthru / package / lease_lock /
  lease_break). Base Rent + Subsidy Rent (core contractual rent) and
  unrecognized codes return None → stay folded in the scheduled total only.
- `mf_normalizer`: per-charge-code amounts accumulate into `MFUnit.ancillary`
  (the scheduled **total is unchanged** — breakout is additive detail, not a
  re-split).
- `mf_uw_model_writer`: writes `MFUnit.ancillary` into Rent Roll Analysis cols
  W–AK (`_ANCILLARY_COL` map; e.g. Amenity Rent → AC Amenity Fees).
- `tests/test_mf_rr_ar.py`: asserts 384-11 amenity = $145 broken out + property
  amenity ≈ $11,120.

**Validation (Avana):** scheduled total still **$442,054** (= the report's
"Total:" row); **Amenity Rent → AC**: 384-11 N=$1,929 / AC=$145; property
amenity total **$11,120**. Subsidy Rent stays in the scheduled total (feeds GPR;
the model has no dedicated subsidy column). Hidden Lakes regression intact
(no charge-code column → no breakout). **Closes the W–AK ancillary gap_source
for itemized "Operations" RRs** (no redIQ Sortable-RR needed when col L itemizes
charges inline). A dedicated Subsidy column would be a model-side handoff.

---

## MF v0.4.1 — 2026-06-03 — RR parser: itemized "charge codes" format (multi-row per unit)

Operator-reported "unable to parse this RR" on an Avana Stoney Ridge rent roll
in the **"Rent Roll (Operations) - Rent Related Charge Codes"** format — a
*multi-row-per-unit* layout (unit identity on a header row; charges — Amenity
Rent, Base Rent, … — itemized across continuation rows with a blank Bldg-Unit;
an L-blank per-unit total row). `mf_normalizer` assumed one row per unit and
crashed (`int.strip()` on a non-string status).

**Fixes:**
- `mf_mappings.normalize_status()` hardened to coerce non-string inputs (the crash).
- `mf_normalizer` column mapping switched to **needle-priority** (map order wins,
  e.g. "Unit Type" over "Floor Plan"); added `charge code` + `gpr market` headers.
- **Block-based parsing:** rows group into per-unit blocks; in the itemized
  format Scheduled/Actual charges are **summed across the block's charge-code
  rows** (where the Charge Code column is populated — skipping the L-blank total
  row); one-row formats read the header row directly. Auto-detected by presence
  of a Charge Code column — **no regression** on the one-row format.
- `tests/test_mf_rr_ar.py` +`test_rr_itemized_charge_codes` (skip if absent).

**Validation:** Avana → **263 units** (244 occupied / 18 vacant); 384-11
scheduled = $1,929 = Amenity $145 + Base $1,784 (the L-blank $1,929 total row
correctly excluded). Hidden Lakes regression intact: **143 units** (66/77/9).
(Avana uses no `**` legal prefix → legal_count 0, expected.)

---

## MF v0.4.0 — 2026-06-03 — Full MF intake: writer + RR/AR app tab → populated MF UW Model

Closes the operator's full-intake build: upload RR + T-12 + AR → download a
**populated MF UW Model**.

**Shipped:**
- **`mf_uw_model_writer.py`** — `populate_mf_model(model_bytes, *, t12, rr,
  property_name, property_units)`. Pastes T-12 lines into `T-12 Analysis`
  Layer 1 (A106: Acct#/Name/12 months/`O=SUM` formula/`P` bucket; month headers
  aligned) and RR units (+joined AR) into the `Rent Roll Analysis` grid (A273,
  cols A–T incl. the Legal boolean and AR aging Q–T); sets Prop Info B4/B6.
  Clears prior example data; leaves every diagnostic/Layer-3 formula untouched.
- **`app.py`** — `_render_mf_intake()` rebuilt: RR / T-12 / AR uploaders + a
  model-override expander → per-doc summaries (RR units/occ/vac/legal; the
  T-12 detail panel; AR rows/total + join report) → **Populate the MF UW
  Model** → download the populated workbook. Bundled model at
  `assets/MF_UW_Model_v15.xlsx`; `BUNDLED_MF_MODEL_PATH` constant.
- **`tests/test_mf_uw_model_writer.py`** — CI-runnable (model is committed):
  synthetic RR/T-12 → asserts cell placement, the Legal boolean, AR aging,
  the `O=SUM` formula, Prop Info, and **formula survival** (EGI `=N67+N79`,
  `I5=COUNTA(...)`, bucket SUMIFS). 17/17 assertions pass.

**End-to-end (Hidden Lakes):** RR 143 units + T-12 80 lines → valid 23-sheet
workbook (324 KB), reloads clean; `Rent Roll Analysis!I5` now counts 143,
T-12 Layer-3 SUMIFS aggregate the pasted col-P buckets.

**openpyxl-quirk finding:** the v15 model has **no `xl/metadata.xml`** and no
dynamic-array spills (the 76 "array" hints are legacy CSE arrays, preserved by
openpyxl) — so the defensive `_restore_dynamic_arrays` call is a no-op here.
openpyxl does drop **cell comments, their indicators, the Claude-for-Excel
add-in, and custom doc properties** (no data/formulas/charts — the model has
zero charts/images) — surfaced as a report warning; open + re-save in Excel
only to recover those annotations. (Corrects the Phase-0 note that wrongly said
the committed model had metadata.xml.)

**Still open:** OM (Offering Memorandum) intake + the redIQ Sortable-RR
ancillary-fee breakouts (RR grid cols W–AK, best-effort per §2.7.2).

---

## MF v0.3.0 — 2026-06-03 — MF parser slice 2: RR + AR parsers

Adds the rent-roll and AR-aging parsers — the per-unit half of the intake.

**Shipped:**
- **`mf_normalizer.py`** — `parse_mf_rr(source) → MFRRResult` of `MFUnit`
  records (the `Rent Roll Analysis` grid fields). Header-driven fuzzy column
  mapping; unit rows identified by a recognized status (cleanly stops at the
  Charge-Code-Summary / Future-Resident blocks that trail the grid); Bldg-Unit
  split; legal flag from the `**` resident prefix; status normalized via
  `mf_mappings.normalize_status`. `unit_key()` helper = the AR join key.
- **`mf_ar_parser.py`** — `parse_mf_ar(source) → MFARResult` +
  `join_ar_to_units(units, ar)`. Joins aging to units on a normalized Bldg-Unit
  key with **two-way unmatched reporting** (AR rows with no unit; units with a
  balance but no AR detail) — never silently drops (decision §2.7.3).
- **`tests/test_mf_rr_ar.py`** — unit tests (Bldg-Unit split / join key) +
  Hidden Lakes e2e (skip when gitignored files absent).

**Validation (Hidden Lakes):** RR → **143 units** (66 occupied / 77 vacant /
9 legal-flagged — matches the DD checklist's 143 units + 9 evictions). AR →
**62 rows, $237,542.14 total**, joining **61/62** to units (the 1 unmatched,
`L3`, is genuinely absent from the RR grid); aging buckets reconcile to each
row's balance (gross of prepayments).

**Next:** `mf_uw_model_writer` (paste RR/AR/T-12 into `MF_UW_Model_v15.xlsx` +
metadata restore) → RR/AR uploaders + model download in the app tab.

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
