# CHANGELOG-UWT — ALF UW Template Integration (Track 4)

Per-release notes for the UW Template integration track. Newest at top.

See [SPEC-UWT.md](SPEC-UWT.md) for the canonical spec; the rollup of pending
work for this track lives in [UW-BACKLOG.md](UW-BACKLOG.md) once items are
opened (none yet — Phase 0 is the seed release).

---

## v0.9.0 — v6 rev2 absorbed (Other Care) + Prop Info & Scenarios col-B mapping (2026-06-03)

**Operator goal**: "I want the raw datas to populate into this ALF UW Template …
Fill in the Prop Info tab property details from RR. Scenarios tab T-12 Actuals
(col B) must be filled or linked to T-12 Analysis tab and rent roll. Complete the
mapping only." Operator supplied a `Deals/…/ALF_UW_Template_v6.xlsx`, the Homestead
RR v2, and the March 2026 T12.

**Critical finding (verify-canonical-source paid off again)**: the operator's
Deals-folder v6 is a **newer revision** than the repo's committed
`assets/ALF_UW_Template_v6.xlsx` that registry v0.5.0 mapped against. The operator
had authored full **"Other Care" (4th care type)** support across Prop Info,
Scenarios, and T-12 Analysis, plus IFERROR hardening — which **shifted ~70 v6
targets** off their registered cells. Mapping new tabs on top of the stale base
would have written good data into wrong cells (e.g. EGI to N77 where the new file
has a blank row; occupied IL beds to B20 where the new file has the Total SUM).

Per operator decision (AskUserQuestion), the Deals file is now **canonical v6**.

**Changes (registry-only; mapping. Writer/evaluator support is the follow-on):**

- **Asset replaced** — `assets/ALF_UW_Template_v6.xlsx` ← operator's Deals file.
- **Re-sync (82 targets)** — every v6 T-12 Analysis + Prop Info target re-pointed via
  a **validated non-uniform remap** (income +1/+2/+3: Other Care base rent N61, Other
  Care LOC N66, and a new "Less: Vacancy/Credit Loss (actual)" N77 line were inserted;
  Prop Info "Other Care Units" row 19 → occupied-beds +1). Remap validated **0 label
  mismatches** across all plain-label rows; post-absorb every target lands on its
  correct label cell. Key landings: EGI→N80, Total Labor→N102, Food Cost→N104,
  EBITDAR/NOI→N135, Mgmt Fee→N131, Occupied Beds IL/AL/MC→B21/B22/B23.
- **3 new T-12 Analysis income concepts** — `base_rent_other` (N61), `loc_other` (N66),
  `vacancy_credit_loss_actual` (N77); status `proposed` (0 for IL/AL/MC-only deals).
- **3 Prop Info auto-fill concepts** (`rr_unit_count`→B6, `rr_gross_sqft`→B11,
  `asset_class`→B13) — the only Prop Info fields derivable from RR; the rest (address,
  buildings, year built, market data, utilities) are genuinely manual.
- **52 Scenarios col-B "Actuals (T-12)" concepts** (new `scenarios` path):
  - **38 expense mirrors** — 1:1 to T-12 Analysis (labor B81-B96, non-labor B99-B121,
    Mgmt Fee B123). `Auto Expense` (N117) + `Lease/Ground Lease` (N128) folded into
    `Other / miscellaneous` (B121) so Total Expenses ties to T-12 NOI.
  - **14 income derived** — beds = licensed beds; rate = base rent ÷ occupied ÷ 12;
    vacancy % = 1 − occupied/licensed; care fees % = LOC/GPR; concessions/bad-debt %;
    2nd Person (N68); Other Income (Σ N69:N76). Reverse-engineers the beds×rate model
    so the Actuals column's EGI ties to T-12 actual EGI.

**Mechanism (operator decision)**: writer **pastes computed values** into the blue
input cells — **no template formula/function changes**. The cells stay manual inputs;
the analyst can still type over them. (Live-formula-link alternative declined.)

**Registry 0.5.0 → 0.6.0**: 137 → **195 concepts**. Status rollup: 117 mapped /
62 proposed / 8 derived / 4 gap_source / 2 gap_target / 1 header_only /
1 substrate_ready_parser_pending. New categories `scenario_expense` / `scenario_income`.
Absorber retained as audit trail: `tools/uw_template/_absorb_v6_rev2_propinfo_scenarios.py`.

**Fills implemented (same release).** `uw_output_model.compute_uw_output_values`
extended to emit the 58 new keys — Scenarios expense mirrors (reuse the T-12
Analysis values already computed; Auto Expense + Lease folded into Other/Misc),
Scenarios income derived (rate = base ÷ occupied ÷ 12; vacancy % = 1 − occ/licensed;
care-fees % = LOC ÷ GPR; concessions/bad-debt %; 2nd Person; Other Income), and
Prop Info aggregates (#Units = RR row count; Gross Sq Ft = Σ unit sqft; Asset Class
derived). **No writer code change for the fills** — the writer's existing
computed-fallback path (blank Analyzer source → `computed_values[key]`) writes them.
Verified end-to-end on Homestead RR v2 + March 2026 T12: **55 new cells populate** —
#Units 176, Gross Sq Ft 65,982, Asset Class "Mix (IL/AL/MC)"; Scenarios Care Fees %
ties LOC exactly, expenses mirror T-12 to the penny, subtotal formulas (B89/B122)
preserved.

**Two bugs found + fixed in the operator's rev2 file:**
1. **Section-D regression** — `T-12 Analysis!B22/B23/B24` (GPR/Net Rent/EGI diagnostic)
   pointed at `N58/N64/N71` (Base Rent IL / LOC AL / Meal Income). Operator-approved
   3-cell fix → `N83/N86/N80` via `_fix_v6_rev2_section_d_refs.py` (metadata-preserving
   per openpyxl quirk #6; restores rev2's own `metadata.xml`). Applied to **both** the
   canonical asset and the operator's local `Deals/…/ALF Templates/` copy.
2. **Writer `_T12_LAYOUT["v6"]` stale** — the finalize/Section-I pass still used the
   prior-v6 rows (EBITDAR N132, Section I 138). rev2 shifted these +3 → updated to
   EBITDAR N135 / EBITDA N136 / mirror rows (62,67,80,102,129,132–136) / Section I 141
   / Section J 194–196. Without this the writer authored totals into wrong rows.
3. **`_compute_derived` returned 0, not None, on a blank Analyzer** — `licensed_beds_total`
   (Prop Info!B15) and `opex_total_incl_mgmt` summed all-blank UW Output cells to `0`,
   which `_is_blank` doesn't treat as blank → the computed-fallback never fired and B15
   read 0 on a fresh build. Both now return `None` when no source cell is numeric, so
   the RR-derived total (176 on Homestead) flows through.
4. **Rent Roll Analysis row-210 header dropped in rev2** (found post-ship on an operator
   populate run reporting the "A210 is blank" warning) — the rev2 authoring left row 210
   entirely blank (v5 carries the full 47-col header Unit/Bed … Effective Conc $), so the
   populated sheet had no column titles above the 211+ paste band. Restored v5's header
   row verbatim (value + style) via `_fix_v6_rev2_rr_header_row.py` — Rent Roll Analysis
   is unchanged v5→v6 (both 47 cols) so labels map 1:1. Metadata-preserving; applied to
   canonical asset + operator's local copy. Warning now clears.
5. **T-12 Analysis income rows 58-79 monthly grid blank** (operator-reported: "if there's
   data it should get populated") — `compute_uw_output_monthly` emitted monthly series for
   labor / non-labor / aggregate revenue but **not** the per-care line items (Base Rent
   IL/AL/MC N58-60, LOC IL/AL/MC N63-65, 2nd Person N68, ancillary revenue N71-75). Those
   rows got their annual pasted to col N but a blank B–M grid. Added all per-line income
   keys to `compute_uw_output_monthly` (`base_rent_il/al/mc`, `loc_il/al/mc`,
   `second_person_revenue`, `rev_meal/housekeeping/laundry/scooter/transfer`). Rule: any
   income line with T-12 data now fills its monthly grid; `M()` returns zeros for labels
   with no GL data so genuinely-empty lines stay 0 (no spurious values). Verified: rows
   58-79 monthly tie to annual to the penny (660 monthly cells).

**All 36 tests green** (3 stale-v6 assertions in `test_uw_template_writer.py` updated
to rev2 rows + concept count 137→195). `UWT_VERSION` 0.8.1 → 0.9.0.

---

## v0.8.1 — v6 template Section-D income-summary repoint (2026-05-30)

**Operator-reported on a populated Briar Glen output**: "the T12 tab isn't
populating properly." Investigation found the **Layer-3 data was fully and
correctly populated** (Base Rent, labor, non-labor opex, monthly grid, Section
I raw — all there), but the **T-12 Analysis Section D** headline cells
(ECONOMIC vs. PHYSICAL OCCUPANCY RECONCILIATION) read $0:

| Cell | Label | Was (v5 ref) | v6 lands on | Fixed to |
| --- | --- | --- | --- | --- |
| `B22` | Gross Potential Rent (GPR) | `=N58` | "Base Rent — IL" ($0) | `=N80` |
| `B23` | Net Rent Revenue (billed) | `=N63` | "LOC / Care — AL" ($0) | `=N83` |
| `B24` | Total Revenue / EGI | `=N69` | "Meal Income" ($0) | `=N77` |

(and `B25` Economic Occupancy %, which divides `B23/B22`, read 0 as a
consequence.)

**Root cause — same class as the two v6 bugs fixed in v0.7.1.** When the
operator rebuilt the v6 income section (actual-T-12 build first; GPR waterfall
demoted to a DIAGNOSTIC sub-block at N80-83; EGI moved up from N69 to N77), the
openpyxl repointing pass repointed the *EGI* chain (B5/B9/B11: N69→N77) but
missed the *Section-D income-summary* chain — leaving B22/B23/B24 on the old v5
rows N58/N63/N69, which in v6 are the (typically $0) Base Rent IL / LOC AL /
Meal Income lines. This is the **openpyxl-quirk-#4 partial-repoint** that also
left `B56:M56` stale (closed in v0.7.1). **Not a writer bug** — the data tab is
correct; the bug is in the blank template's diagnostic formulas. Confirmed by
diffing the v5 template (where N58=GPR, N63=Net Rent, N69=EGI — so the old refs
were correct there).

**Fix** (`tools/uw_template/_fix_v6_section_d_refs.py`, mirrors the v0.7.1 fix
pattern): repoint `assets/ALF_UW_Template_v6.xlsx` `B22=N80`, `B23=N83`,
`B24=N77`, with a pre-flight that asserts the v6 target rows carry the expected
labels (GPR / Net Rent / EGI) before touching anything. The openpyxl edit
strips `xl/metadata.xml`, so it re-restores metadata + the 554 Section R/S `cm`
markers from v5 via `_restore_dynamic_arrays` (same as v0.7.1). Idempotent;
zip-part inventory unchanged (40 parts); sheet count 16; v0.7.1's B56:M56 fix
and all income-restructure formulas (N77 EGI, N61 Total Base) verified still
intact.

**Verified:** fix script's 11 checks all pass. End-to-end populate of the fixed
template against Homestead — B22/B23/B24 propagate as `=N80`/`=N83`/`=N77` and
resolve to GPR $9,524,893 / Net Rent $6,951,136 / EGI $6,964,627 (101 concepts,
516 monthly cells written). All 5 suites in `tests/test_uw_output_model.py`
green. Also produced a corrected copy of the operator's reported output at
`Downloads/Briar_Glen_UW_Template_2025-12-31_normalized_FIXED.xlsx` (in-place
3-cell repoint + metadata restore) — Briar Glen Section D now reads GPR
$5,736,477 / Net Rent $3,754,025 / EGI $3,859,123.

**Section F note (not a bug):** rows 41/47 (RE Taxes / P&C "T-12 Actual") show
`0` + "⚠ not in T-12 — verify with operator" even though the actuals exist in
Layer 3 (N117 RE Taxes, N112 P&C). Those are **analyst-input / pro-forma
triangulation cells** — literal `0` in v5 too, never auto-pulled from the T-12.
By design; left as-is. (A future template revision could optionally wire the
"T-12 Actual" sub-cells to `=N117`/`=N112`, but that's an operator design call,
not a regression.)

`UWT_VERSION` 0.8.0 → 0.8.1. Handoff brief filed at
`tools/uw_template/handoffs/2026-05-30-uwt-v6-section-d-income-refs.md` and
marked Verified (the fix was applied programmatically, matching the v0.7.1
precedent for low-risk single-cell-formula repoints).

---

## v0.8.0 — default template flipped to v6 (T-12 income restructure) (2026-05-29)

v6 is now the binding default for every populate. The flip was **not** a
one-line constant change: the T-12 Analysis finalize + Section-I passes were
hardcoded to v5 row positions and gated on `template_version == "v5"`, so a
naive flip would have silently regressed v6 outputs on monthly totals,
EBITDAR/EBITDA authoring, and Section I raw population (none caught by tests —
there was no v6 writer test). Both passes are now version-dispatched.

**Writer (`uw_template_writer.py`):**
- New `_T12_LAYOUT` per-version row map (v5 + v6) for the Layer-3 finalize and
  Section I/J reconciliation. v6 rows: EGI N77 (was N69), Total Labor N99 (N85),
  Total Non-Labor N126 (N111), Total Op Ex N129 (N114), Op Ex excl mgmt N130
  (N115), EBITDARM N131 (N116), EBITDAR N132 (N117, authored `=N131-N128`),
  EBITDA N133 (N118, authored `=N132`); Section I band 138–187 (+15 vs v5),
  Section J 191/192/193. v6 income is an actual-T12 build so there's no v5-style
  Net Rent monthly special-case (`net_rent_row=None`); the income subtotals
  N61/N65/N77 are mirrored across B–M instead.
- `_finalize_t12_layer3(ws, monthly, layout)` and `_write_section_i_raw(ws,
  raw_lines, layout)` take the layout map; the call site gates on
  `_T12_LAYOUT.get(template_version)` (v5 **and** v6).
- `populate_uw_template` default `template_version` `'v5'` → `'v6'`; CLI default
  likewise. v5/v4 still fully supported via the explicit param.

**App (`app.py`):**
- `BUNDLED_UW_TEMPLATE_PATH` → `assets/ALF_UW_Template_v6.xlsx` (the v0.7.1
  repaired binary — 40 parts, metadata + cm markers); `BUNDLED_UW_TEMPLATE_VERSION`
  `"v5"` → `"v6"`.
- `_detect_uw_template_version` now two-stage: v4-vs-v5+ on Rent Roll Analysis
  "Care Level Tier", then v5-vs-v6 on T-12 Analysis (`A77` EGI / `A114` Auto
  Expense). **Also fixed a pre-existing latent bug**: the stage-1 probe read
  AP210, but the v5.1 restructure moved "Care Level Tier" AP→AO, so every v5/v6
  upload-override was misclassifying as v4. Now probes AO210 (current) with
  AP210 as a pre-v5.1 fallback. (Harmless until now because the bundled default
  uses the constant, not detection — but a v6 upload override would have broken.)

**Tests (`tests/test_uw_template_writer.py`):** the two existing tests are pinned
to `template_version="v5"` (v5 regression preserved); two new v6 tests added —
`test_empty_analyzer_smoke_v6` (new default; asserts EGI formula at N77,
EBITDAR authored at N132, EBITDA at N133, monthly mirror at B77, 137 concepts /
16 sheets) and `test_populated_analyzer_e2e_v6` (Homestead fixture; EGI N77 /
EBITDARM N131 / EBITDAR N132 / EBITDA N133 all live formulas; 176 RR rows).
All four green; `test_uw_output_model` (5) + `test_dashboard_model` (27) green.

**Verified on Homestead fixture:** v6 EGI `=N61+N65+SUM(N66:N76)` at N77,
EBITDARM `=N77-N99-N126` at N131, EBITDAR `=N131-N128` at N132, EBITDA `=N132`
at N133; B77 monthly mirror `=B61+B65+SUM(B66:B76)`; dynamic arrays restored;
176 rent-roll rows. `UWT_VERSION` 0.7.1 → 0.8.0.

**Operator-side follow-up (outside repo):** adopt the repaired
`assets/ALF_UW_Template_v6.xlsx` into the `Deals/.../ALF Templates/` folder copy
(the Deals copy was locked/pre-fix at flip time). Optionally re-add the
Claude-for-Excel add-in (webextensions, not restored). **Still queued:** rebuild
the Homestead test fixture against substrate v0.2.15 to retire the
known-divergence whitelists (the v6 e2e shows 21 no_source on the old fixture —
the 14 new by-care income concepts aren't cached in it; the app passes
`computed_values` so this is a fixture artifact, not a runtime gap).

---

## v0.7.1 — v6 binary repaired: B56 headers + metadata.xml restored (2026-05-28)

Fixes the two v6-template bugs flagged in v0.7.0, programmatically (no operator
Excel round-trip required). `tools/uw_template/_fix_v6_headers_and_metadata.py`:

1. **B56:M56 monthly-header repoint** (openpyxl): `=C122..=N122` → `=C137..=N137`.
   The raw month-header row moved +15 in the income restructure; the operator's
   repointing pass missed this chain (openpyxl quirk #4). 12 cells fixed.
2. **`xl/metadata.xml` restored** (`_restore_dynamic_arrays`, the v0.6.1
   post-processor): the v6 binary was the pre-Excel-resave version (39 parts,
   no metadata) → Section R/S dynamic-array spills degraded. Sourced from
   `assets/ALF_UW_Template_v5.xlsx` (= v5.1 content; **Section R/S layout verified
   identical to v6 cell-by-cell** before injecting — Z173/C173/Q173/A173/B173/
   W211/X211/Y211 all match). 554 `cm` markers re-applied. v6 now 40 parts.

**Verified:** B56=`=C137`, M56=`=N137`; metadata.xml present; Section R Z173 still
an ArrayFormula; income-restructure formulas intact (EGI N77, Total Base N61);
all 5 suites green. A v6 *populated output* now also carries metadata.xml + 554
cm markers (the writer's `_restore_dynamic_arrays` finally has a source) — so
Section R/S spills work on per-deal outputs too.

**Not restored:** `xl/webextensions/` (the Claude-for-Excel taskpane add-in,
carrying v5's add-in fileId GUID). Re-installable — the operator re-adds the
add-in if they use it; not fabricated here.

**Default still v5** — the binary is now correct, so the only remaining gate is
the explicit one-line `BUNDLED_UW_TEMPLATE_VERSION` flip (held for operator
go-ahead + a confirming open-in-Excel). The operator should also adopt this
repaired `assets/ALF_UW_Template_v6.xlsx` back into their Deals/ folder copy.
`UWT_VERSION` 0.7.0 → 0.7.1.

---

## v0.7.0 — Template v6 absorbed: T-12 Analysis income restructure (2026-05-28)

Registry/engine/substrate absorption of the operator-authored **v6 template**
(per `Deals/.../2026-05-28-uwt-v6-release-handoff.md`). v6 rebuilds the T-12
Analysis Layer-3 INCOME block from the GPR→Net-Rent market-projection waterfall
into a full **actual-T12 build** (Base Rent IL/AL/MC + LOC IL/AL/MC by care +
ancillaries + contras → EGI at N77); demotes the GPR waterfall to a labeled
DIAGNOSTIC sub-section (N80-83); and adds an **Auto Expense** non-labor row
(N114) that closes a previously-hidden NOI overstatement.

**Row map verified cell-by-cell against `assets/ALF_UW_Template_v6.xlsx`** (not
trusted from the handoff doc) before building the registry.

### Registry → 0.5.0 (`_absorb_v6.py`)

`templates.v6` block (`income_model="actual_t12"`). 70 T-12 Analysis concepts
re-targeted (income restructured; labor +14; non-labor +14 then +15 after the
new Auto Expense row; NOI +15; `t12_raw_month_*` 122→137). 14 new concepts:
`base_rent_il/al/mc`, `total_base_rent`, `loc_il/al/mc`, `total_loc`, 5 ancillary
revenue lines, `opex_auto_expense`. `second_person_revenue` gap_source → mapped
(N66). `base_rent_normalized` + `loc_revenue` v6 targets **nulled** — N61/N65 are
template SUM formulas fed by the new by-care rows; the aggregates must not
clobber them (`loc_revenue` was). 137 concepts total.

### Engine (`uw_output_model.py` + `dashboard_model.py`)

- **Auto Expense fix:** added `"Auto Expense"` to `dashboard_model._LABELS_NON_LABOR`.
  It was routed by the Description_Map but absent from the non-labor sum, so its
  dollars fell out of opex → standardized EBITDARM overstated. On Homestead
  exactly **$6,061.32** = the standardized-vs-as-reported NOI gap. Now NOI ties:
  EBITDAR $1,417,385 → **$1,411,324** (= as-reported). Changes NOI by −$6,061 on
  every property (engine scalar); the v5 template (no Auto Expense row) is
  unaffected.
- Exposed 13 new keys for the v6 income rows (by-care base rent/LOC, 5 ancillary
  revenue, `opex_auto_expense`, `second_person_revenue`).
- **EGI now includes 2nd Person Revenue** (engine + dashboard) — see substrate
  v0.2.15 below; keeps the re-map EGI-neutral.

### Substrate v0.2.15 (`migrate_to_v0215.py`)

2nd-Person Description_Map re-map: 4 rows (r127 Second Person Fee + r400/401/402
Second Persons Revenue | care; r127 included per operator decision) `Base rent —
*` → `2nd Person Revenue`. **Critical companion fix caught by verifying the EGI
formula chain** (the handoff's "EGI unchanged" note missed it): the Analyzer's
`T12 Analytics!E52/F52` did NOT sum the "2nd Person Revenue" label, so the re-map
alone would drop 2nd-person dollars out of EGI. The migration amends E52 + F52
with an INDEX/MATCH term for that label. On Homestead, r127 = **$32,220.49** —
broken out of base rent, added back to EGI; EGI stays $7,001,957.

### Verification

All 5 suites green. `test_uw_output_model` whitelists the cached-fixture
divergences as documented known-effects: 5 keys × $6,061 (Auto Expense) + 2 keys
× $32,220 (2nd-person re-map). v6 populate end-to-end on Homestead: income rows +
Auto Expense N114 + 2nd Person N66 populate; all total/subtotal formulas
(N61/N65/N77/N99/N126/N131-133) preserved; EGI $7,001,957; NOI $1,411,324.

### Default still v5 — two operator follow-ups before flipping to v6

1. **v6 binary is the pre-Excel-resave version** (39 zip parts, missing
   `xl/metadata.xml` + `xl/webextensions/`). Section R/S dynamic-array spills on
   populated outputs are degraded until the operator opens v6 in Excel + saves +
   re-drops (the handoff §9 step). `BUNDLED_UW_TEMPLATE_VERSION` stays `"v5"`
   until then.
2. **v6 template bug (v6.1 fix):** Layer-3 monthly headers `B56:M56` still
   reference `=C122..=N122`, but the raw month-header row moved to 137 (Section I
   shifted +15). The operator's repointing pass missed this chain (openpyxl
   quirk #4). Cosmetic (headers blank; data cells writer-populated); should be
   `=C137..=N137`.

`UWT_VERSION` 0.6.4 → 0.7.0. Absorber + migration retained as audit trail.

---

## v0.6.4 — Section I (Layer 1 — Raw T-12) populated (2026-05-28)

Operator request: "the summarized Raw data should be inserted in Section I of T-12 Analysis." Section I is the Layer-1 raw-T12 paste grid (rows 122–172: `Acct # | Account Name | Apr-25…Mar-26 | T-12 Total | → MAPPING`) — previously an empty skeleton with pre-assigned bucket labels in col P. Two operator decisions confirmed: **rebuild one row per Analyzer label** and **Account Name = matched GL account names**.

### Engine — `compute_t12_raw_lines` (`uw_output_model.py`)

New function returning the summarized raw T-12 grouped by Description_Map label: `{label, section (Revenue/Expense), descriptions [raw GL names], monthly [12], total}`. Computed from the parsed `T12ParseResult.gl_rows` (not read from the Analyzer's `T12 Raw Data` sheet, whose monthly cells are formulas → blank on a fresh Analyzer — same cache caveat). Ordered in P&L sequence; unmapped GL lines excluded (mirrors `T12 Raw Data`).

### Writer — `_write_section_i_raw` + `populate_uw_template(..., raw_t12_lines=...)`

Rebuilds Section I: clears the skeleton (rows 123–172, cols A–P) and writes one row per label — B = matched GL account names (`" | ".join`), C–N = 12 monthly values, O = T-12 total, P = standardized bucket (label). Authors the **Section J raw-totals reconciliation** (Total Revenue / Total OpEx / EBITDAR) as live SUM formulas over the rows written. New `report.summary['section_i_raw_cells']`.

### Result (Homestead)

44 raw lines (8 revenue / 36 expense), 663 cells. Each row's 12 months tie to its T-12 Total; Section J EBITDAR reconciles to **$1,411,324 — the penny-exact as-reported NOI** (vs the standardized Layer-3 EBITDAR $1,417,385; the ~$6K gap is the bad-debt-as-revenue-contra standardization, which is exactly what the raw-vs-standardized reconciliation is for). New `tests/test_uw_output_model.py::test_section_i_raw_populated`. `UWT_VERSION` 0.6.3 → 0.6.4.

---

## v0.6.3 — T-12 Analysis totals as live formulas + waterfall sign fix (2026-05-28)

Operator-reported math inconsistencies on the populated UW Template's T-12 Analysis Layer 3: (1) the totals were pasted values that didn't recompute or tie to the line items; (2) the GPR→Net Rent income waterfall didn't subtract its loss lines ("$9.5M GPR minus losses ≠ $6.98M Net Rent"); (3) `Total Operating Expenses (N114) = 0`. Two operator decisions confirmed before implementing: **bad debt reduces EGI** (honor the template's N63 formula) and **monthly totals mirror formulas across B–M**.

### Root cause

The writer pasted computed values over the template's live total formulas (`N63 =N58+N59+N60+N61+N62`, `N69 =N63+…+N68`, `N85 =SUM(N71:N84)`, `N111`, `N114`, `N115 =N114-N113`, `N116 =N69-N85-N111`). And the income contra lines were pasted with Analyzer-convention signs (Vacancy +2,873,629, Bad Debt +37,329) while the template's *additive* Net Rent formula treats them as reductions — so the waterfall added losses instead of subtracting them.

### Fix (`uw_template_writer.py`)

- **Preserve template formulas.** The 9 Layer-3 total-row concepts (`base_rent_normalized`, `egi`, `labor_total`, `opex_nonlabor_total`, `opex_total_incl_mgmt`, `opex_total_excl_mgmt`, `ebitdarm`, `ebitdar`, `ebitda`) are skipped by the generic loop on T-12 Analysis so values never overwrite the formulas. Fixes the `N114 = 0` artifact.
- **Sign the contras** (`_T12_CONTRA_KEYS`): `loss_to_lease`, `physical_vacancy_loss`, `bad_debt_writeoffs_revenue` are negated when written to T-12 Analysis (annual + monthly), so `N63 = GPR + LtL + Vacancy + Concessions + BadDebt` ties to base rent net of concessions + bad debt.
- **`_finalize_t12_layer3`**: preserves col-N formulas, **authors the two the template left blank** (`N117 EBITDAR = N116-N113`, `N118 EBITDA = N117`), and **mirrors each total's col-N formula across the monthly grid B–M** (`=B63+B64+…`, `=SUM(B71:B84)`, …). Net Rent monthly (B63–M63) is pasted as `base − concessions − bad debt` per month (the GPR waterfall feeding N63 has no monthly dimension), and reconciles to the annual N63.

### Result (Homestead, evaluated)

All 9 totals are live formulas in col N + mirrored across B–M. Net Rent $6,750,961, **EGI $6,964,627** (bad debt now a revenue contra), Total Labor $3,060,543, Total Non-Labor $2,136,601 (bad debt no longer double-counted in opex). **EBITDARM $1,767,483 / EBITDAR $1,417,385 / EBITDA $1,417,385 — unchanged** (bad debt nets out of both EGI and opex at the EBITDARM line). Monthly Net Rent sums to the annual to the penny.

### Verification

`tests/test_uw_output_model.py` updated with an N-chain evaluator (openpyxl can't compute formulas): asserts totals are formulas, contras negative, and the evaluated chain gives EGI $6,964,627 / EBITDARM $1,767,483 / EBITDA $1,417,385; monthly line items + Net Rent tie to annual; total rows mirror formulas across B–M. `test_uw_template_writer.py` e2e updated (N69 is now a preserved formula). `UWT_VERSION` 0.6.2 → 0.6.3.

### Still open

Section I (Layer 1 — Raw T-12, rows 121+) remains empty — separate next item.

---

## v0.6.2 — T-12 Analysis monthly grid populated (cols B–M) (2026-05-28)

Operator-reported: the populated UW Template's **T-12 Analysis Layer-3 grid shows the T-12 Total column but the 12 monthly columns (Apr 2025 … Mar 2026) are all $0.** This was the original Phase-2 "monthly grid annual-only" locked default (writer wrote col N, left B–M blank) — by design, not a regression — but the operator wants the monthly trending visible.

### Layout (confirmed against the template)

Layer-3 months are **columns B–M** (12 cols; headers `=C122…=N122`), T-12 Total is **column N**, then O/P/Q (T-3 Annlzd / Per Bed/Mo / % of EGI). The B–M cells are literal-`0` paste targets — **not** formulas, even on subtotal rows (EGI N69 is a formula, but B69–M69 are plain 0s) — so each month must be pasted explicitly.

### Engine — `compute_uw_output_monthly` (`uw_output_model.py`)

New function returning `{concept_key: [12 monthly floats]}`, reusing `_aggregate_t12`'s month-by-month GL bucketing (same primitive the annual evaluator and `dashboard_model` use). Covers all T12-derived concepts: every labor + non-labor line item, base rent / LOC / other-revenue, the subtotals, and the EBITDA chain. GPR / physical_vacancy_loss / loss_to_lease are **omitted** — they're rent-roll projections with no monthly source, so those rows stay blank in the grid (matching the Analyzer's own T12 Analytics). Returns `{}` when no T12 uploaded.

### Writer — `populate_uw_template(..., computed_monthly=None)`

New optional param + `_write_monthly_grid` helper. For any concept whose target is a `T-12 Analysis` column-N scalar (the annual total), the 12 monthly values are pasted across cols B–M of the same row. Written unconditionally when monthly data is present (the grid is a pure paste target — no Analyzer-cached monthly to defer to). New `report.summary['monthly_cells_written']`.

### App

Populate flow calls `compute_uw_output_monthly(result, t12_parse_result)` and passes `computed_monthly=`. The success caption now notes the monthly cell count.

### Verification

- 636 monthly cells written (53 concepts × 12). Every populated row reconciles **to the penny**: Base Rent ΣB:M = $6,983,357 = N; EGI = $7,001,957 = N; Care Staff Labor = $1,184,692 = N; Total Labor = $3,060,543 = N. GPR row blank monthly (N = $9,524,893), as designed.
- New `tests/test_uw_output_model.py::test_monthly_grid_reconciles` asserts ≥500 monthly cells and that EGI/Base/Labor monthly sums equal their annual N. `UWT_VERSION` 0.6.1 → 0.6.2.

### Not in scope

Columns O (T-3 Annlzd), P (Per Bed/Mo), Q (% of EGI) remain blank — their per-row denominator/sign semantics weren't confirmed and they were never populated before (no regression). Candidates for a follow-up once the intended formula for each is pinned.

---

## v0.6.1 — Dynamic-array repair: Section R/S spills survive the writer (2026-05-28)

Operator-reported bug on the populated `Homestead_Village_UW_Template_2026-04-24_normalized.xlsx`: **Section R (Unit Type Pricing By Care Level, rows 170–181) displays only one row** (AL · 1 Bedroom) instead of the full Care Level × Unit Type matrix, so row 180/181 totals are understated (C180 = 14 vs ~272; J181 ≈ $943,841 vs ~10× that). No `#SPILL!`/`#VALUE!`/`#REF!` — silently wrong.

### Root cause — openpyxl quirk #6, on the output this time

`Rent Roll Analysis!Z173` (`=SORT(UNIQUE(FILTER($X$211:$X$610,…)))`) is the driver; `A173:Q173` lift off `Z173#`. In the committed template these are **dynamic arrays** marked by `xl/metadata.xml` (XLDAPR `fDynamic="1"`) + a `cm="1"` attribute on each anchor cell. openpyxl's `wb.save()` **drops `xl/metadata.xml` and every `cm` marker** — the formula *text* survives verbatim, but Excel then reads `<f t="array" ref="Z173">` as a **legacy CSE array scoped to one cell** → returns only the top-left value → the whole section collapses. An Excel re-save does *not* fix it (Excel already committed to the CSE interpretation); the only manual fix was re-entering every formula.

### Fix — `_restore_dynamic_arrays` post-processor (`uw_template_writer.py`)

After `wb.save()`, a pure `zipfile`+`re` post-processor (no new dependency) repairs the output:
1. Re-injects `xl/metadata.xml` verbatim from the original template.
2. Adds its content-type Override + a workbook relationship (`sheetMetadata`, unique rId).
3. Re-applies the `cm="N"` markers to the exact anchor cells that carried them in the template — matched by **sheet name** (robust to openpyxl's rel-id renumbering and `/xl/…` absolute targets) and only on cells that still hold a formula (`<f`). Faithful by construction: the writer never edits the dynamic-array anchors.

No-op when the template has no `xl/metadata.xml` (v4, or any workbook without dynamic arrays). Wrapped in try/except so a repair failure degrades to a warning, never breaks the populate. New `report.summary['dynamic_arrays_restored']` flag.

### Verification

- 557 `cm` markers restored (554 on Rent Roll Analysis + 3 on the second dynamic-array sheet); `Z173`/`A173`/`C173`/`Q173` all carry `cm="1"`; `xl/metadata.xml` present; output zip valid; openpyxl re-loads it; writer data intact (EGI $7,001,956.79 at N69, D211='1 Bedroom', Z173 still an ArrayFormula).
- New `tests/test_uw_output_model.py::test_dynamic_array_metadata_restored` asserts the repair flag, metadata.xml presence, ~557 cm markers, and Z173 carrying `cm`.

### Secondary issue flagged (not addressed here)

The bug report notes 128/400 `X211:X610` rows resolve to `""` (fail the `E="Occupied" AND C<>"" AND D<>""` gate). Most are legitimately vacant; worth a sanity check that no *occupied* unit is missing Care Level (col C) or Unit Type (col D) — those would be silently excluded from Section R. This is a data-completeness question on the Analyzer paste, not a writer bug; left for a follow-up if it recurs on a real deal.

---

## v0.6.0 — In-Python UW Output evaluator (kills the cache caveat) (2026-05-28)

Closes the single biggest UX friction in the populate flow. Until now the
writer read cached formula values from the Analyzer (`data_only=True`), but an
Analyzer the app just built in-memory via openpyxl has formula **text** with no
cached values — so every `uw_output`-system concept came through `no_source`
and the populated UW Template's `T-12 Analysis` tab was blank unless the
operator first round-tripped the Analyzer through Excel (download → open →
save → re-upload as override). This release computes those values directly in
Python, so the populate flow produces a fully-populated UW Template on the
first pass with no Excel round-trip.

User direction: *"go with 1"* (build the evaluator) + *"Extend
dashboard_model.py pure-Python pattern"* (the engine approach, chosen over
pulling in `formulas` / `pycel` / `xlcalculator`).

### New module — `uw_output_model.py`

`compute_uw_output_values(rr_result, t12_result, *, scenario='normalized') ->
{concept_key: value}`. Computes the 62 `uw_output`-system concepts plus the 2
dependent `derived` concepts (`licensed_beds_total`, `opex_total_incl_mgmt`)
directly from the parsed `NormalizeResult` + `T12ParseResult`. Re-uses Track 5
`dashboard_model`'s aggregation primitives (`load_description_map`,
`_aggregate_t12`, the `_LABELS_*` constants) — single source of truth for the
Description_Map label vocabulary and the GL-by-label grouping.

**Why it's correct.** `UW Output` is a thin reference layer over `T12
Analytics`, which sums `T12 Raw Data` per Description_Map Label and reads
`Rent Roll Recon` bed counts. The **normalized** scenario (col F, the default)
reads T12 Analytics col F for opex, and every opex line is `F{r} = =E{r}`, so
normalized == T12 actual. For base rent / LOC the normalized figure is the
"stabilized" value (`E20`/`E27`), but the stabilized formula
`B20 = B6·B10·B19·12` collapses algebraically to the T12 actual when the
target-occupancy assumption `B10 = B8` (its literal default). Verified
empirically on the Homestead fixture: `E16==E20`, `E23==E27`, `E52==F52`,
`E108==F108`. Analyst normalization overrides happen later in Excel; once the
analyst saves and re-uploads, the cached values exist and the writer prefers
them.

### Writer — `populate_uw_template(..., computed_values=None)`

New optional param. The fallback is applied **only when the Analyzer's cached
cell read is blank** — a saved-through-Excel (override) Analyzer with real
cached values still wins; the computed values only fill gaps. New
`ConceptResult.computed_fallback` flag; new `report.summary['computed_in_python']`
count. Fully backward-compatible — the existing smoke test (which uses the
cached Homestead fixture) still passes with `computed_in_python: 0`.

### App — `app.py`

The populate flow now calls `compute_uw_output_values(result, t12_parse_result)`
and passes it as `computed_values`. Property name (Prop Info!B4) and RR period
date (Rent Roll Analysis!B5) — both already in the app's hands and both blank
on a fresh Analyzer — are added to the dict too. The loud `st.warning`
walking operators through the Excel round-trip is replaced by an `st.success`
("N UW Output values computed in-Python … no Excel round-trip required")
plus a soft `st.info` only for the genuine no-T12 case. `UWT_VERSION`
`0.5.3 → 0.6.0`.

### Verification

- **`tests/test_uw_output_model.py`** (new, 2 layers, skip-on-missing-fixture):
  - *engine vs cached* — the engine reproduces the Homestead fixture's cached
    `UW Output` on 42 spot-checked concepts **to the penny** (EGI $7,001,956.79,
    EBITDARM $1,767,482.75, EBITDA $1,417,384.90, GPR $9,524,893.30, every
    labor + opex line item).
  - *writer fallback e2e* — a freshly-built (no-cache) Analyzer takes the
    T-12-path `no_source` count from **63 → 2** (61 values computed in-Python);
    `T-12 Analysis!N69/N116/N118/N115` all carry the correct numbers.
- Existing `tests/test_uw_template_writer.py` unchanged and still passes.

### Residual / out of scope

- The 2 remaining fresh-Analyzer `no_source` cells were closed by passing
  property name + period date from the app. The 7 `rent_roll`-path
  `no_source` (pharmacy / meal / scooter / care-level / preleased) are
  legitimately empty source columns for properties that don't carry that data
  — not a cache-caveat artifact.
- No new dependency (pure Python; reuses pandas/openpyxl already present).

---

## v0.5.3 — v5.1 K/L/V template-formula absorption (2026-05-27)

Operator-reported 2026-05-27: *"I removed the alf uw template v5 and replace with v5.1. That's the new updated one with corrections in the rent roll analysis tab."* Operator dropped `assets/ALF_UW_Template_v5.1.xlsx`; renamed to `assets/ALF_UW_Template_v5.xlsx` per filename-consolidation policy (matches v0.5.1 precedent).

### What v5.1 added template-side

Six new template formulas at Rent Roll Analysis row 211+ (fill-down through row 609):

| Cell | Formula | Computes |
|---|---|---|
| `K211+` | `=IFERROR(IF(A211="","",N(AE211)+N(AF211)+N(AG211)+N(AH211)),0)` | Total LOC $ from per-fee ancillaries |
| `L211+` | `=IFERROR(IF(A211="","",N(J211)+N(K211)),0)` | Total Sched (Actual Rate + Total LOC) |
| `V211+` | `=IFERROR(IF(OR(A211="",U211="",U211=0,J211=""),"",J211/U211),"")` | Actual PSF per month (J/U) |
| `W211+` | `=IFERROR(IF(V211="","",V211*12),"")` | Actual PSF per year (V*12) |
| `AA211+` | `=IFERROR(IF(OR(A211="",I211="",J211=""),"",I211-J211),"")` | Mkt-Actual $ delta |
| `AB211+` | `=IFERROR(IF(OR(AA211="",I211=0,I211=""),"",AA211/I211),"")` | Mkt-Actual % delta |

W, AA, AB were already classified `derived` in the registry's `intake_targets_unmapped` block — no concept mapped there, no registry change needed. **K, L, V were not** — three concepts had previously been writer-paste-targeting these cells.

### Registry → v0.4.2

Three concepts reclassified `mapped → derived` via `tools/uw_template/_absorb_v51_total_formulas.py` (idempotent; retained as audit trail):

| Concept | Source (Analyzer) | Target (v5) | Why moved |
|---|---|---|---|
| `rr_total_loc` | `Rent Roll Input!T` (Total LOC $) | `Rent Roll Analysis!K211+` | Template `=N(AE)+N(AF)+N(AG)+N(AH)` |
| `rr_total_monthly_rev` | `Rent Roll Input!U` (Total Monthly Rev) | `Rent Roll Analysis!L211+` | Template `=N(J)+N(K)` |
| `rr_actual_psf` | `Rent Roll Input!AA` (Actual PSF) | `Rent Roll Analysis!V211+` | Template `=J/U` |

The `derived` status is in `_DEFAULT_SKIP_STATUSES`, so the writer skips automatically — the template's formulas execute at populate-time using the writer-pasted source data. Precedent: matches `rr_total_ancillary` (became `derived` in UWT v0.4.0 when v5 added `=SUM(AK:AO)` at AQ).

Collision detection: a sweep across all rent_roll concepts × all template-formula cells caught exactly these three. No other collisions.

### Smoke test

`python3 tests/test_uw_template_writer.py` — all tests pass.

- **Empty Analyzer:** 2 cells written / 15 skipped / 106 no_source (out of 123).
- **Homestead populated:** 99 written / 2,311 cells (was 102 / 3,244 in v0.5.2; expected: -3 row-stride concepts × 176 rows).
- **All 10 v5.1 template formulas verified intact** in output (K, L, V, W, X, Y, AA, AB, AP, AT).
- Writer-paste cells preserved alongside formulas (`A211='A1'`, `D211='1 Bedroom'`, `E211='Occupied'`, `J211=$2,926.84`, `U211=461 sqft`, `AR211='X'` for ACH).
- T-12 spot-checks all green (EGI $7,001,957 at N69; EBITDA $1,417,385 at N118; EBITDARM $1,767,483 at N116; GPR $9,524,893 at N58).

### Carry-forwards (rolled into next handoff)

Operator's v5.1 source was authored from a pre-v0.4.4 baseline, so two regressions came along for the ride:

- **A173 / B173 IFERROR wrapper stripped.** PREV had `=IFERROR(TEXTBEFORE(ANCHORARRAY(Z173),"|"),"")`; NEW has bare `=_xlfn.TEXTBEFORE(_xlfn.ANCHORARRAY(Z173),"|")`. When Z173 spill is empty (e.g. no occupied units), A173/B173 throw `#N/A`. **Recommend re-wrapping in Cowork on next v5.1 author pass.**
- **Cover G1/H1 substrate stamp + Rent Roll Analysis B5 date** still empty — these were the 2026-05-26 handoff items; carry forward.

All three items bundled into `tools/uw_template/handoffs/2026-05-27-uwt-v51-template-formulas-K-L-V.md` "Open follow-ups" section. Recommended path: operator addresses all three in a single next Cowork pass.

### xlsx integrity caveat (unchanged)

The smoke test's *output* xlsx drops `xl/metadata.xml` and `xl/webextensions/` per **openpyxl quirk #6** (the writer uses openpyxl, which can't preserve these zip parts on save). Operator workaround per established pattern: open the populated UW Template once in Excel and re-save → Excel rebuilds `xl/metadata.xml` from the dynamic-array formula calls it finds. Same workaround as v0.4.3+. The in-Python formula evaluator roadmap item would eliminate this; not implemented.

### Files

- **Modified:** `assets/ALF_UW_Template_v5.xlsx` (replaced binary with operator's v5.1 content), `tools/uw_template/registry.json` (v0.4.1 → v0.4.2), `tools/uw_template/MAPPING_TRACKER.md` + `mapping_tracker.csv` + `mapping_mindmap.html` (regenerated), `app.py` (UWT_VERSION 0.5.2 → 0.5.3), `CHANGELOG-UWT.md` + `SPEC-UWT.md` + `CLAUDE.md` (this entry + Phase 3.7 row + head paragraph).
- **New:** `tools/uw_template/_absorb_v51_total_formulas.py` (absorber script), `tools/uw_template/handoffs/2026-05-27-uwt-v51-template-formulas-K-L-V.md` (handoff brief — status Verified).

---

## v0.5.2 — T-12 monthly headers from operator's raw T-12 (2026-05-27)

Operator-reported 2026-05-27 after sample-running v0.5.1 populated UW
Template: "The T12 data isn't populated. Check that the headers match
from the analyzer. Also, header dates should be actual months and Year
that's in the t12 raw data."

Three findings investigated:

  1. **Labels match correctly** ✓ — registry's target rows align with
     T-12 Analysis labels (EGI → N69, EBITDARM → N116, etc.). No fix
     needed.
  2. **T-12 data not populated** — cache caveat in action. The
     Analyzer the writer read from didn't have cached UW Output formula
     values (openpyxl doesn't compute formulas), so writer's
     `_resolve_source()` returned None for every t12-path concept,
     producing `no_source` outcomes across the board. None of the
     T-12 Analysis Layer 3 cells got writer-pasted; template's fallback
     SUM formulas at N69/N85/N111/N116 evaluate to 0 because upstream
     cells (N58, N71:N84, etc.) are all empty.
  3. **Hardcoded month headers** — `T-12 Analysis!C122:N122` are
     static `Apr-25`...`Mar-26` strings, not per-deal months. For any
     T-12 period other than Apr 2025 - Mar 2026, the template would
     show the wrong months on Layer 1 (Section 3) AND on Layer 3
     (row 56 monthly headers, which formula-pull from row 122).

### Shipped — fixes #1 and #3 (label finding) + #3 (month headers)

  **12 new month-header concepts** added to registry via
  `tools/uw_template/_phase4_add_month_headers.py`:

    t12_raw_month_1   T12 Input!C11 ('Apr 2025')  →  T-12 Analysis!C122
    t12_raw_month_2   T12 Input!D11 ('May 2025')  →  T-12 Analysis!D122
    ...
    t12_raw_month_12  T12 Input!N11 ('Mar 2026')  →  T-12 Analysis!N122

  Path: `t12_raw`. Status: `mapped`. Source.system: `cell` (existing
  scalar handler). 12 scalar concepts — no writer code change. Row 56's
  existing `=C122..=N122` formula chain auto-pulls the new values.

  Registry: 0.4.0 → 0.4.1. Total concepts: 111 → 123 (+12). New
  category: `t12_raw_headers`.

### Shipped — cache caveat surfaced loud-and-clear

  Promoted the in-app cache caveat banner from `st.info` to `st.warning`
  with explicit step-by-step instructions. Operators were hitting the
  cache caveat without realizing — populated UW Template's T-12 tab
  came up empty and they thought the writer was broken. The new warning:

    ⚠️ T-12 Analysis tab will be mostly BLANK — {N} of the T-12 values
    came through as no_source because openpyxl doesn't compute Excel
    formulas. The Analyzer this app just built has formula text but
    no cached values — and the writer reads cached values.

    To get a fully populated UW Template:
    1. Download the Analyzer (above).
    2. Open it in Excel. Wait for it to compute. Save it.
    3. Come back here and upload the saved-from-Excel Analyzer as
       "Analyzer template override" in the sidebar's Advanced expander.
    4. The page reruns. Re-download the UW Template.

    This is a known limitation (openpyxl quirk) — an in-Python
    formula evaluator is on the roadmap.

  Also added a ⚠️ Cache caveat callout to the **"What the app does"**
  workspace expander so operators see it BEFORE hitting the issue, not
  AFTER.

### Verification

  - Writer regression on Homestead populated fixture: 102 concepts
    written (was 90, +12 month headers) / 3,244 cells (was 3,232, +12).
  - Spot-check: T-12 Analysis C122 = 'Apr 2025', D122 = 'May 2025',
    ..., N122 = 'Mar 2026' (the real T-12 period months). Row 56's
    `=C122..=N122` formulas pick these up on Excel open.
  - Labels still align: registry's target rows for `egi` (N69),
    `ebitdarm` (N116), `ebitda` (N118), etc. match the template's
    A-column labels exactly.
  - Empty-Analyzer smoke test passes — concept count assertion
    updated 111 → 123.
  - `app.py` parses clean.
  - No registry schema changes — just additive new concepts.

### In-Python formula evaluator (roadmap, NOT in this release)

The cache caveat is the last big rough edge in the operator workflow.
Logged as a follow-up: embed `formulas` / `pycel` / `xlcalculator` (or
extend the `dashboard_model.py` pure-Python pattern from Track 5) so
the writer can read computed UW Output values directly from the
in-memory Analyzer the app just built, without requiring the Excel
round-trip. Estimated 4-8 hours; substantial but eliminates the
biggest UX friction.

### Out of scope

  - **BL-0026 (broader T-12 Raw path)** — still blocked on operator
    direction pick. The month headers shipped today are the
    independent "cherry on top" piece — they don't depend on the
    Layer 1 capacity question.
  - **BL-0027** (README modernization) — low priority.
  - **v5.1 metadata cells** (Cover stamp + RR Period Date in
    `_v51_metadata_cells` handoff brief) — still pending operator
    Excel pass; `_absorb_v51_metadata_cells.py` pre-wired.

### Versioning

  - UWT code version: **v0.5.2** (T-12 month-header concepts +
    cache-caveat UX).
  - Mapping registry version: **0.4.1** (additive — 12 new concepts).
  - Template versions supported: v4 + v5 (unchanged).
  - Analyzer substrate mapped against: v0.2.14 (unchanged).

---

## v0.5.1 — v5.1 column restructure absorbed (2026-05-27)

Operator authored v5.1 in Excel per the
`2026-05-27-uwt-v51-unit-type-restructure` handoff brief: Unit Type
moved to a new col D (immediately before Status), old W "Unit Type
(base)" and old AC "Apt Type" both dropped, everything between old
D-V right-shifted by 1, everything from old AD-AV left-shifted by 1
(closing the AC hole). Net Rent Roll Analysis column count: 48 → 47.

This release skips v0.5.0 (which was used by the rolled-back metadata-
cells attempt) to avoid version reuse.

### Shipped

  - **Template asset** — `assets/ALF_UW_Template_v5.xlsx` replaced
    in place with the operator's v5.1 restructured version. v5.1 IS
    v5 going forward — single canonical filename. Old v5 content
    preserved in git history at commit `5462df1` (v0.4.4) for
    rollback.
  - **A173/B173 IFERROR wrappers re-applied** — operator's v5.1 was
    authored from a v5 snapshot that pre-dated v0.4.4's fix, so the
    raw `TEXTBEFORE`/`TEXTAFTER` were back. Re-applied IFERROR
    wrappers via openpyxl so they don't return #N/A on empty Z173
    spill.
  - **Registry** — `tools/uw_template/_absorb_v51_column_restructure.py`
    applied. **CRITICAL SCOPE FIX caught during run**: initial
    absorber version shifted ALL concepts (including T-12 Analysis
    ones like `egi: N69 → O69`); fixed to filter on
    `target.sheet == "Rent Roll Analysis"` so only the restructured
    sheet's targets shift. T-12 Analysis, Prop Info, Cover all
    untouched. Final result: 36 concepts shifted (all rent_roll
    path), 75 concepts unchanged.

### Registry shifts applied

  | Direction | Count | Examples |
  |---|---|---|
  | Right-shift by 1 (old D-V → E-W) | 18 | `rr_status` D→E, `rr_sq_ft` T→U, `rr_actual_psf` U→V |
  | Special retarget AC → D | 1 | `rr_apt_type` (now writes new Unit Type col directly) |
  | Left-shift by 1 (old AD-AV → AC-AU) | 17 | `rr_concession` AD→AC, `rr_market_psf` AT→AS, `rr_ach` AS→AR |
  | **Total** | **36 concepts** | (all rent_roll path) |

  `registry_version` 0.3.0 → **0.4.0**.

### Verification

  - Pre-flight checks pass: D210="Unit Type", E210="Status", max_col=47,
    AC no longer "Apt Type" (now "Concession $" — left-shifted from AD).
  - Writer regression on Homestead populated fixture passes — 90
    concepts written / 3,232 cells (identical totals to v5).
  - Spot-checks:
    - D211 = `'1 Bedroom'` (new Unit Type col, writer paste from
      Analyzer col F)
    - E211 = `'Occupied'` (Status, right-shifted from D)
    - U211+ = Sq Ft writer paste (was T)
    - AP211 = `'=SUM(AJ211:AN211)'` (Total Ancillary $ template
      formula, left-shifted from AQ)
    - AQ211 = `None` (Preleased Date, left-shifted from AR; Janet
      Pierson is occupied not preleased — correct)
    - AR211 = `'X'` (ACH, left-shifted from AS)
    - T-12 Analysis cells UNCHANGED at original positions
      (`N69`/`N115`/`N116`/`N118` etc) — only Rent Roll Analysis
      shifted
  - `tests/test_uw_template_writer.py` updated for v5.1 layout — the
    `AQ211 should still hold =SUM(...)` assertion from v5 era was
    stale (formula moved to AP); replaced with broader v5.1 layout
    checks.

### What v5.1 did NOT include (still pending separate handoff)

The 2026-05-26 metadata-cells handoff (`Cover!G1/H1` substrate stamp
+ `Rent Roll Analysis!B5` RR period date cell) is **NOT** in this
v5.1 release. Operator may include in a subsequent Excel pass; the
`_absorb_v51_metadata_cells.py` absorber is still pre-wired.

### Bug found + fixed mid-release

First absorber run wrongly shifted ALL concepts, including T-12
Analysis ones (which the column restructure doesn't touch). Caught
via post-run spot-check (`egi: N63 → O63` — clearly wrong since
T-12 Analysis sheet wasn't restructured). Reverted via
`git checkout HEAD --` on the registry + artifacts, fixed absorber
to filter on `target.sheet == "Rent Roll Analysis"`, re-ran cleanly.
Lesson recorded in absorber's docstring + inline comment.

### Openpyxl quirk #6 implication

The operator authored v5.1 in Excel directly (per quirk #6 — column
inserts via openpyxl would strip `xl/metadata.xml`). My A173/B173
IFERROR re-application via openpyxl DOES drop metadata.xml — operator
needs to open the file in Excel once, accept the repair prompt, and
save to rebuild it. Same working pattern as v0.4.3/v0.4.4.

### Out of scope (unchanged)

  - In-Python formula evaluator (closes cache caveat) — still pending.
  - v5.1 metadata cells — Cover stamp + RR Period Date (separate
    operator pass, absorber pre-wired).
  - BL-0026 T-12 Raw path — still blocked on operator picking a
    direction.
  - BL-0027 README modernization — low priority.

### Versioning

  - UWT code version: **v0.5.1** (skipping v0.5.0 used by rolled-back
    attempt).
  - Mapping registry version: 0.4.0 (substantial structural shift).
  - Template versions supported: v4 + v5 (v5.1 is the new v5 — same
    `template_version="v5"` key, file overwritten in place).
  - Analyzer substrate mapped against: v0.2.14 (unchanged).

---

## v0.4.4 — Section R re-fix: W mirrors AC, A173/B173 IFERROR, D173 uses per-unit sq ft (2026-05-27)

Operator-reported Section R bug on Rent Roll Analysis: returns #N/A and
zeros despite v0.4.3's W/X/Y fill-down patch. Root cause traced to
operator's 2026-05-26 `deacc41` "refresh assets" edit, which **replaced**
v0.4.3's `W = =AC{r}` formulas with a substring-Notes-parser formula
(a what-if option I'd sketched in an earlier chat but never recommended).
Since real rent rolls don't carry "studio" / "1 bed" / "1br" / etc. in
col S (Notes), W resolved to "" everywhere → X to "" everywhere → Z173
spill empty → all of A173-I173 broken.

### Shipped (`tools/uw_template/_patch_v5_section_r_use_ac.py`)

CLI-runnable, idempotent. 4 surface changes to
`assets/ALF_UW_Template_v5.xlsx`:

  | Cell range | Old | New |
  |---|---|---|
  | **W211:W610** (400 cells) | `=IFERROR(IFS(ISNUMBER(SEARCH("studio",S{r})),...),"")` (substring Notes parser) | `=IF(AND($D{r}="Occupied", $AC{r}<>""), $AC{r}, "")` (gated AC reference) |
  | **A173** | `=TEXTBEFORE(ANCHORARRAY(Z173),"|")` (raw — shows #N/A on empty spill) | `=IFERROR(TEXTBEFORE(ANCHORARRAY(Z173),"|"),"")` |
  | **B173** | `=TEXTAFTER(ANCHORARRAY(Z173),"|")` | `=IFERROR(TEXTAFTER(ANCHORARRAY(Z173),"|"),"")` |
  | **D173** | `=IFERROR(XLOOKUP(ANCHORARRAY(B173),{"Studio";"1 Bedroom";...},{450;700;1000;1300;350;900},""),"")` (hardcoded estimates) | `=IFERROR(AVERAGEIFS($T$211:$T$610,$C$211:$C$610,ANCHORARRAY(A173),$AC$211:$AC$610,ANCHORARRAY(B173)),"")` (real per-unit sq ft from col T) |

The W change is the substantive fix; A173/B173 wrap raw TEXTBEFORE/
TEXTAFTER calls so blank Z173 spills don't show #N/A; D173 swap uses
actual per-unit sq ft from col T instead of the placeholder lookup table.

### Why W = gated AC reference (not substring-Notes-parser)

  - **Col AC ("Apt Type") already holds the canonical unit type.** The
    writer pastes Analyzer col F (normalized closed vocab: Studio /
    1 Bedroom / 2 Bedroom / 3 Bedroom / Suite / Cottage) into AC at
    populate-time. Always present, always normalized.
  - **Col S (Notes) is free-form** — lease/concession context, not
    structured. Parsing it for unit type is fragile and fails on real
    rent rolls.
  - **Occupancy gate** ensures vacants and unmapped rows contribute
    nothing to Section R's SORT/UNIQUE/FILTER unique-key spill.

### Verification

  - 9/9 patch verification checks pass (W formulas at start/mid/end of
    range, A173/B173/D173 wrappers, Z173 SORT/FILTER unchanged, sheet
    count 16, RR Analysis max_row 610).
  - Writer regression on Homestead populated fixture passes — 90
    concepts written / 3,232 cells; W211 in output = the new gated AC
    formula; X211 still concats correctly; Z173 still ArrayFormula.
  - Idempotency confirmed (re-run = no-op via `_is_already_patched()`
    detection on the `$AC211<>""` marker in W211).

### Openpyxl quirk #6 implication

This patch round-trips the file through openpyxl, which silently drops
`xl/metadata.xml` (the XLDAPR block) per quirk #6 documented in
CLAUDE.md (and the v0.5.0 rollback). After this patch ships, the
operator must open the file in Excel ONCE and save it — Excel detects
the missing part on open, offers to repair, and rebuilds the
metadata.xml with correct dynamic-array properties. This round-trip
has been the working pattern since v0.4.3 — Excel's repair is
forgiving for surface-only formula changes like this one.

### Out of scope (unchanged)

  - In-Python formula evaluator (closes cache caveat) — still pending.
  - BL-0026 T-12 Raw path — blocked on operator picking a direction
    (Layer 1 capacity mismatch: 50 rows template vs 100+ rows real GL).
  - BL-0027 README modernization — low priority.
  - v5.1 template metadata cells — operator authoring queued; absorption
    script pre-wired at `tools/uw_template/_absorb_v51_metadata_cells.py`.

### Versioning

  - UWT code version: **v0.4.4** (Section R re-fix).
  - Mapping registry version: 0.3.0 (unchanged).
  - Template versions supported: v4 + v5 (v5 default).
  - Bundled v5 re-patched at `assets/ALF_UW_Template_v5.xlsx`.
  - Analyzer substrate mapped against: v0.2.14 (unchanged).

### Note on v0.5.0 number

v0.5.0 was used by the rolled-back v5 → v5.1 metadata-cells attempt
(see entry below). Future successful v5.1 absorption will be v0.5.1
to avoid version reuse.

---

## v0.5.0 — Attempted then rolled back (2026-05-26)

**This release did NOT ship.** Rolled back the same session due to openpyxl
round-trip data loss discovered post-patch. See "v0.5.0 (rolled back)"
detail below; the **handoff infrastructure** described later did ship and
stands.

### What was attempted

Two surface-only cell additions via `tools/uw_template/_patch_v5_to_v51_metadata_cells.py`:
`Cover!G1 "Substrate:"` label + `Cover!H1` placeholder for writer-populated
substrate stamp; `Rent Roll Analysis!B5` styled `mm/dd/yyyy` for writer-populated
RR period. Cell-level fidelity check appeared clean (sheets / merged ranges /
defined names / RRA cell count / Section R/S ArrayFormula objects all
preserved verbatim). Registry bumped to v0.3.1; smoke tests passed at the
openpyxl read/write layer.

### Why rolled back

A deeper zip-part inventory diff (post-cleanup) found openpyxl's `wb.save()`
silently dropped **6 xlsx parts**:

  - **`xl/metadata.xml`** (810 bytes lost) — `XLDAPR` / `fDynamic="1"`
    metadata. This is Excel's dynamic-array properties block, which tells
    Excel that the v0.4.3 Section R/S spilled-range formulas (`Z173`'s
    `SORT(UNIQUE(FILTER(...)))`, `C173`'s `COUNTIFS(...,ANCHORARRAY(Z173))`,
    spilling across 7×13 cells via `_xlfn._xlws.SORT` / `_xlfn.UNIQUE` /
    `_xlfn._xlws.FILTER` / `_xlfn.ANCHORARRAY`) are **dynamic arrays**.
    Without it, Excel may demote these to single-cell results or render
    `#SPILL!`. **The v0.4.3 patch's whole reason-for-existing depends on
    this metadata.** openpyxl has no API to preserve it on save.
  - **`xl/webextensions/*`** (3 files, ~1.3 KB) — Claude-for-Excel add-in
    taskpane registration (`wa200009404` from the Office Add-in store).
    Re-installable but real loss.
  - **`xl/sharedStrings.xml`** (74 KB) — string deduplication table. openpyxl
    inlines strings into each sheet on save (sheet sizes grow correspondingly).
    Functionally equivalent; no content lost.
  - **`xl/calcChain.xml`** (167 KB) — Excel's formula dependency graph.
    Excel rebuilds on open; no real loss but contributes to file-size delta.
  - **`xl/comments[1-5].xml`** and **`xl/drawings/vmlDrawing*.vml`** renamed
    to `xl/comments/commentN.xml` and `xl/drawings/commentsDrawingN.vml` with
    smaller sizes — comment shape metadata may have been minimally trimmed.

The cell-level fidelity check missed all of this because it only inspected
Worksheet objects' visible attributes (cell values, formulas, merged ranges,
defined names). The xlsx-as-zip-archive view exposes the parts openpyxl
doesn't model.

### Rollback actions taken

`assets/ALF_UW_Template_v5.xlsx` restored from git commit `deacc41` (the
v0.4.3 ship state). Registry reverted to v0.3.0 via
`tools/uw_template/_revert_registry_to_v030.py`. UWT_VERSION restored to
`0.4.3`. Three `open_questions` re-opened. `MAPPING_TRACKER.md` /
`mapping_tracker.csv` / `mapping_mindmap.html` regenerated. The two
patch scripts (`_patch_v5_to_v51_metadata_cells.py` and
`_revert_registry_to_v030.py`) retained as audit trail — do NOT re-run
the patch script without first solving the openpyxl-XLDAPR-loss problem.

### Lesson recorded

Added a 6th item to the "openpyxl quirks that bite migrations" section in
CLAUDE.md: **openpyxl's `wb.save()` does not preserve `xl/metadata.xml`
or `xl/webextensions/`**. For any workbook that uses Excel 365 dynamic
arrays (`SORT` / `UNIQUE` / `FILTER` / `ANCHORARRAY` spilling), a Python
round-trip through openpyxl will silently break the dynamic-array
semantics even though every Cell object inspects clean. The cell-level
fidelity diff is necessary but not sufficient — also diff the zip part
inventory.

### Path forward for v5.1

Switch to the protocol path. The 2026-05-26 handoff brief
(`tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md`)
remains the active spec. The operator authors the two cells directly in
Excel via Cowork, re-drops the file, and a future Track 4 chat absorbs
registry-side without touching the template file.

---

## v0.4.3 — v5 template patch: Section R / Section S formula fill-downs (2026-05-26)

### What landed on the template

Two surface-only cell additions to `assets/ALF_UW_Template_v5.xlsx`,
above the data band — zero risk to charts, formulas, paste anchors, or
styling bands:

  | Cell | Content | Purpose |
  |------|---------|---------|
  | `Cover!G1` | `"Substrate:"` (label, italic gray 9pt, right-aligned) | Static label |
  | `Cover!H1` | empty, styled placeholder | Writer populates from Analyzer `Cover!B8` (e.g. `v0.2.14`) — provenance for each populated copy |
  | `Rent Roll Analysis!B5` | empty, `mm/dd/yyyy` formatted | Writer populates from Analyzer `RR_Period_Date` named range (resolves to `Rent Roll Recon!B2`). Sibling `D5 (=TODAY())` left alone as the diagnostic-refresh date. |

**Placement note:** the original plan put the substrate stamp at `E1/F1`
but `A1:F1` is a merged title band — those cells are read-only
`MergedCell` objects in openpyxl. Relocated one column right to `G1/H1`
which sit cleanly outside the merge.

### Patch tool

`tools/uw_template/_patch_v5_to_v51_metadata_cells.py` — CLI-runnable,
idempotent. Pre/post fidelity diff confirms 16 sheets / 240 merged ranges
/ 5 defined names / 3,417 RRA non-empty cells all preserved; v0.4.3
Section R/S ArrayFormulas (`Z173`, `C173`, `W211..W610`) preserved
verbatim; T-12 Analysis monthly headers (`B56..M56 = C122..N122`)
preserved verbatim. Cover gains exactly 1 non-empty cell (the G1 label)
as expected.

### Registry updates (`tools/uw_template/registry.json`)

`registry_version` 0.3.0 → **0.3.1**. Three concept-level changes:

  | Concept | Before | After | Why |
  |---------|--------|-------|-----|
  | `substrate_version` | `gap_target`, `targets.v5 = null` | `mapped`, `targets.v5 = {sheet: "Cover", address: "H1", label_at: "G1"}` | Template cell now exists |
  | `rr_period_date` | `proposed`, `targets.v5.B5` already set | `mapped` | Format confirmed (`mm/dd/yyyy`); writer populates from `RR_Period_Date` named range |
  | `t12_period_date` | `gap_target`, `targets.v5 = null` | `derived_in_template` (new status), no target needed | v5 derives `B56:M56` from on-sheet Layer 1 row 122 via `=C122..=N122` — writer has nothing to write. (The v4 note describing hardcoded `Apr-25..Mar-26` was stale; v5 fixed this structurally without anyone noticing in the registry.) |

`open_questions` shrinks 8 → 5. Closed: #4 (Date header A5/B5 format),
#7 (Cover substrate stamp — deferred to v5.1), #8 (Rent Roll Analysis
tab-header Period Date metadata cell — deferred to v5.1). Surviving:
Bad Debt placement, 2nd Person Revenue source, monthly grid B-M policy,
RRA header rows 1-209 derived framing (informational), AR aging
row-level routing (upstream-blocked).

### Status rollup

  Before v0.5.0 (registry v0.3.0):  95 mapped · 4 proposed · 2 gap_target · 5 gap_source · 3 derived · 1 header_only · 1 substrate_ready_parser_pending
  After v0.5.0 (registry v0.3.1):   97 mapped · 3 proposed · 0 gap_target · 5 gap_source · 3 derived · 1 derived_in_template · 1 header_only · 1 substrate_ready_parser_pending

**Zero `gap_target` concepts remain.** Every Analyzer-exposed concept
the writer cares about has a template-side target. Remaining `gap_source`
items are all upstream-blocked (AR row-level routing pending the AR↔RR
resident-key join; `second_person_revenue` pending the UW Output
extension vs. RR-direct decision).

### Smoke-test results

`python tests/test_uw_template_writer.py`:

  - Empty-Analyzer smoke (bundled `ALF_Financial_Analyzer_Only.xlsx`
    v0.2.14, no deal data): **3 cells written** (was 2 — gained
    `substrate_version` since `Cover!B8` always has a value, even on
    the empty fixture).
  - Populated Homestead e2e: **91 concepts / 3,233 cells written**
    (was 90 / 3,232). New writes verified:
      - `Cover!H1` ← `'v0.2.4'` (the Homestead fixture's substrate stamp)
      - `Rent Roll Analysis!B5` ← `datetime(2026, 4, 24)` (the RR period)
    Existing writes regression-clean: EGI $7,001,957 at `N69`, EBITDA
    $1,417,385 at `N118`, EBITDARM $1,767,483 at `N116`, GPR $9,524,893
    at `N58`, Occupied Beds 53/40/35 at Prop Info `B20-B22`, AQ211
    formula `=SUM(AK211:AO211)` preserved (template-owned formula not
    overwritten by writer).

### Handoff infrastructure (already in place from commit `031e24f`, augmented this session)

**Correction recorded post-fact:** an earlier draft of this entry claimed
the handoff infrastructure shipped with v0.5.0. It did not. The
infrastructure (`HANDOFF_TRACKER.md`, `HANDOFF_TEMPLATE.md`, the
`handoffs/` directory, the original `2026-05-25-uwt-v4-to-v5-template-gaps.md`
brief, and the CLAUDE.md Track 4 "Handoff protocol" paragraph + table
rows) had already shipped earlier on 2026-05-26 in commit **`031e24f`**
(`feat: UWT v0.2.0 → v0.4.0 — Phase 1-3`).

This session's contribution to the handoff infrastructure was
**augmentative, not creative**:

  - Added `tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md` as the new active brief (closes the two `gap_target` concepts deferred to v5.1 per the 2026-05-26 release `open_questions` list).
  - Marked `tools/uw_template/handoffs/2026-05-25-uwt-v4-to-v5-template-gaps.md` Superseded with a banner noting v5 absorption via UWT v0.4.0 hours earlier already closed 7 of the 10 gap_targets it requested.
  - Added `Superseded` as a new status in `HANDOFF_TRACKER.md`'s status legend (alongside the pre-existing Pending / In progress / Applied / Verified).
  - Updated `HANDOFF_TRACKER.md`'s index table with the new 2026-05-26 row at the top and the older 2026-05-25 row's Status moved to Superseded.

Also written this session (outside the repo): a user-level feedback
memory (`uw-template-handoff-protocol`) so future chats follow the
protocol without re-discovering it.

**Important precedent (chat-specific):** v0.5.0 broke the
"don't-edit-the-template-directly" protocol that `031e24f` had
established, because the v5.1 changes looked trivial (two cells above
the data band, no merged ranges, no formulas, no styling band) and the
fast-path-via-openpyxl appeared lower risk than operator-authored Excel
round trip. The path was explicitly user-approved. The
zip-part-inventory diff (added to openpyxl quirk #6) proved otherwise.
Future Track 4 chats should default to the handoff protocol unless the
user makes a similar exception call **and** a zip-part inventory diff
is added to the fidelity check.

---

## v0.4.3 — v5 template patch: Section R / Section S formula fill-downs (2026-05-26)

Operator-reported bug after v0.4.2 ship: Section R (rows 170-181, "Unit
Type Pricing by Care Level") on the populated UW Template returns
**#CALC! everywhere**. Diagnosis traced to the dynamic-array driver at
`Rent Roll Analysis!Z173`:

  ```
  =SORT(UNIQUE(FILTER($X$211:$X$610,$X$211:$X$610<>"")))
  ```

`FILTER` on an all-empty range with no `if_empty` argument throws #CALC!,
which then poisons every spillover cell in C173:Q179. Same shape on
Section S (rows 182-188 reading `$AU$211:$AU$610`) — counts to 0
everywhere instead of #CALC!, but same root cause.

### Root cause

The Section R/S ArrayFormulas at row 173 are intact (verified — Z173,
C173, Q173 are all `<openpyxl.worksheet.formula.ArrayFormula>` objects).
But the **formula-derived columns W / X / Y at rows 211-610 have NO
formulas** in the v5 template. The operator who authored the v5 template
externally in Excel cleaned the data rows but didn't re-fill the formula
columns. Headers exist at W210/X210/Y210 ("Unit Type (base)" /
"Care|UnitType" / "Care|Unit (all)") but the data rows are empty.

### Shipped

`tools/uw_template/_patch_v5_section_r_formulas.py` — CLI-runnable
patcher, idempotent. Fills 1,200 cells (400 rows × 3 cols):

  | Col | Formula at row r | Purpose |
  |-----|------------------|---------|
  | **W** | `=AC{r}` | Mirror AC (Apt Type) — already writer-populated from Analyzer col F's normalized closed vocab (Studio / 1 Bedroom / 2 Bedroom / 3 Bedroom / Suite / Cottage). Required by Section R's SqFt lookup at row 171. |
  | **X** | `=IF(AND(D{r}="Occupied",C{r}<>"",W{r}<>""),C{r}&"|"&W{r},"")` | Care\|UnitType, **occupied-only**. Drives Section R's unique-key SORT/UNIQUE/FILTER at Z173. |
  | **Y** | `=IF(AND(C{r}<>"",W{r}<>""),C{r}&"|"&W{r},"")` | Care\|Unit, all care+type rows incl vacants. Drives Section R denominators. |

Idempotency gate: bails as a no-op if `W211` already holds a formula or
value. Re-runs are safe.

CLI:
  ```
  python tools/uw_template/_patch_v5_section_r_formulas.py
      [path/to/ALF_UW_Template_v5.xlsx]
  ```
  Default target: committed `assets/ALF_UW_Template_v5.xlsx`. Operator can
  also run on their Deals-folder canonical copy.

### What this patch does NOT do

- **Column AU (Conc Source)** left empty. The 2026-05-25 handoff contract
  §11 calls AU "Manual analyst entry," and the operator's diagnostic note
  flagged the auto-classifier sketch as "rough — confirm column meanings
  before using." Section S will continue to show 0 counts until analyst
  data is entered there. Auto-classification can ship as a v5.1 template
  addition if needed.
- **Columns Z (_key), AA (Mkt-Actual $), AB (Mkt-Actual %)** also empty
  per contract §13's formula-derived list, but the operator hasn't
  reported them as blocking any section. Left alone for now.

### Verification

  - Patch ran cleanly on `assets/ALF_UW_Template_v5.xlsx`: 1,200 cells
    written (400 W + 400 X + 400 Y), 6/6 verification checks passed
    (headers preserved, W/X/Y at start/mid/end-of-range are formulas,
    W611 is empty so no overwrite past data range).
  - Idempotency confirmed (re-run = no-op).
  - **Writer round-trip on Homestead populated fixture**: formulas
    survive the writer's openpyxl load+save cycle intact:
    - W211 → `=AC211`
    - X211 → `=IF(AND(D211="Occupied",C211<>"",W211<>""),C211&"|"&W211,"")`
    - Y211 → `=IF(AND(C211<>"",W211<>""),C211&"|"&W211,"")`
    - AC211 → `'1 Bedroom'` (writer-paste)
    - Z173 still `<ArrayFormula>` object — Section R's driver intact
  - **Cell counts post-populate** (Homestead): 176 AC-data cells +
    400 W-formula cells — every populated row will have W resolve via
    AC, then X/Y derive from C+W.
  - Writer regression tests (`tests/test_uw_template_writer.py`) still
    pass — 90 concepts written / 3,232 cells.

### Operator-side note

The patch operates on the committed `assets/` asset. The operator should
re-run it on their `Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v5.xlsx`
canonical copy too (or simply replace that file with the patched repo
copy). Future v5.1 template work (Cover substrate stamp + tab-header
Period Date) should preserve the W/X/Y fill-downs — note added to the
BL-0027 / v5.1 handoff queue.

### Versioning

  UWT code version: v0.4.3 (Phase 2.5 patch).
  Mapping registry version: 0.3.0 (unchanged).
  Template versions supported: v4 + v5 (v5 default).
  Bundled v5 patched at: `assets/ALF_UW_Template_v5.xlsx` (1,200 new
    formula cells in W/X/Y at rows 211-610).
  Analyzer substrate mapped against: v0.2.14 (unchanged).

---

## v0.4.2 — Phase 2.5 follow-up: bundled template + override pattern (2026-05-26)

User feedback after v0.4.1 ship: "I don't see a download for ALF UW
Template" — the v0.4.1 pattern required uploading a template every
session to get a populated copy, which is friction the Analyzer doesn't
have. v0.4.2 mirrors the Analyzer's load pattern exactly: bundled by
default, override under Advanced.

### Shipped (app.py changes only — no API change to writer)

- **New constants**:
  - `BUNDLED_UW_TEMPLATE_PATH = Path(__file__).parent / "assets" / "ALF_UW_Template_v5.xlsx"`
  - `BUNDLED_UW_TEMPLATE_VERSION = "v5"`
- **New helper `_load_uw_template(uploaded_file)`** — mirrors
  `_load_analyzer()`. Returns `(template_bytes, source_label,
  template_version)`. Upload wins; falls back to the committed asset.
  Raises `FileNotFoundError` with a clear message if neither exists.
- **New helper `_detect_uw_template_version(template_bytes)`** —
  best-effort version detection. Probes `Rent Roll Analysis!AP210`
  (v5's "Care Level Tier" header that doesn't exist in v4). Falls back
  to `"v5"` on any error (file not openable, missing sheet, etc.).
  Uses `read_only=True` for fast load — no full workbook parse.
- **Sidebar restructure**:
  - **Removed** the standalone "UW Template (.xlsx) — optional"
    file_uploader between the AR section and the Underwriting section.
  - **Promoted** the scenario radio to always-visible (was conditional
    on `uw_template_file is not None` in v0.4.1). Now reads "UW Template
    scenario" with the same help text. Lives at the same sidebar
    position the uploader used to occupy.
  - **Added** a "UW Template override (.xlsx)" file_uploader in the
    Advanced expander, immediately after the existing "Analyzer template
    override" — parallel placement, parallel help text ("Upload to
    override for this session only").
  - **Sidebar version footer** extended:
    `RR v{RR_VERSION} · T12 v{T12_VERSION} · AR v{AR_VERSION} · T5
    v{T5_VERSION} · UWT v{UWT_VERSION}` (UWT was missing in v0.4.1).
- **Workspace populate flow restructure**:
  - Removed the `if uw_template_file is not None:` outer guard.
    Populate now fires unconditionally on every successful Analyzer
    build (i.e. when `can_download` is True).
  - Calls `_load_uw_template(uw_template_override_file)` up front to
    resolve the source.
  - New "Using UW Template: **<source>** (`<version>`)" caption appears
    immediately under the section header — mirrors the existing "Using
    Analyzer: ..." caption pattern.
  - `populate_uw_template()` call now passes the resolved
    `template_version` explicitly instead of relying on the default
    (the helper returns `v5` for bundled, `v4` or `v5` for override per
    auto-detection).

### UX impact

Operator's flow changes from:

  - **v0.4.1**: "I uploaded an RR + T12 but I don't see a UW Template
    download" (because the upload was never done).

To:

  - **v0.4.2**: RR upload → Analyzer download + populated UW Template
    download both appear automatically. To use a non-default template
    (legacy v4 / v5.1 candidate / per-deal customization), expand
    Advanced and upload an override.

### Version auto-detection notes

`_detect_uw_template_version()` is intentionally lightweight — single
cell probe at `Rent Roll Analysis!AP210`. v5 has "Care Level Tier"
there; v4 doesn't (cols AP-AR didn't exist before v5). The fallback
to v5 on any error is deliberate — v5 is the binding default and the
registry's primary supported version. A user uploading a corrupted or
non-ALF .xlsx will get a writer error downstream rather than crash here.

### Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` — parses
  clean at 1,523 lines (was 1,456 in v0.4.1; +67 LOC for the helpers +
  caption + sidebar restructure).
- `tests/test_uw_template_writer.py` — both smoke + Homestead e2e
  still pass on the writer module (writer didn't change; only the
  caller pattern changed).
- The `_detect_uw_template_version()` probe was sanity-checked against
  the committed `assets/ALF_UW_Template_v5.xlsx` (returns `"v5"`) and
  conceptually against a v4 (`Sample Files/ALF_UW_Template_v4.xlsx`
  has no AP210 header → returns `"v4"`).

### Out of scope (unchanged from v0.4.1)

- **In-Python formula evaluator** for the cache caveat — still pending.
- **v5.1 template completions** (Cover substrate stamp + RR Analysis
  tab-header Period Date).
- **BL-0026 — T-12 Raw path** — still deferred.
- **AR row-level routing**.

### Versioning

- UWT code version: **v0.4.2** (Phase 2.5 follow-up).
- Mapping registry version: **0.3.0** (unchanged).
- Template versions supported: **v4** + **v5** (v5 default; auto-detected
  from `Rent Roll Analysis!AP210`).
- Bundled template path: `assets/ALF_UW_Template_v5.xlsx`.
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.4.1 — Phase 2.5: Streamlit UI integration (2026-05-26)

Closes the user-experience gap that's been open since Phase 2. The writer
module exists and works end-to-end, but until this release the operator
had to either (a) paste-values manually per the contract's intended motion
or (b) run `python uw_template_writer.py` via CLI. Now: upload the UW
Template in the sidebar, get a populated copy as a second download
alongside the Analyzer.

### Shipped (app.py changes only — no API change)

- **Sidebar** — new file_uploader `"UW Template (.xlsx) — optional"`
  positioned after the AR uploader + as-of-date block. When the analyst
  uploads, a horizontal radio appears below for scenario selection
  (`normalized` default / `t12_actual`). The radio renders only when a
  template is uploaded.
- **Workspace tab** — after the existing combined-Analyzer download
  button, a new `📋 Populate UW Template` section appears (gated on
  `uw_template_file is not None`). It:
  1. Reads the uploaded template bytes.
  2. Calls `populate_uw_template(final_bytes, uw_template_bytes,
     scenario=...)` — the just-built Analyzer bytes are the source.
  3. Builds a per-deal filename via `derive_property_name(rr_file.name)`:
     `<Property>_UW_Template_<RR period>_<scenario>.xlsx`. Property name
     sanitized (alphanumerics + space/dash/underscore only; spaces → `_`).
  4. Surfaces a one-line summary caption: "Writer populated **{N} of
     {total}** concepts ({cells:,} cells). Scenario: `{scenario}`."
  5. Drill-in expander `🔍 Populate report (details)` — auto-expanded on
     warnings; shows warnings + outcome counts + per-error notes.
  6. Emits the populated-template download button.
  7. **Cache caveat info banner**: when any t12-path concept comes through
     as `no_source`, surfaces an `st.info` walking the analyst through
     the round-trip-through-Excel workaround (download Analyzer → open
     in Excel → save → re-upload via Advanced expander's "Analyzer
     template override" → re-download). Surfaces the openpyxl-doesn't-
     compute-formulas reality clearly instead of leaving them confused.
- **Constants**: `UWT_VERSION = "0.4.1"` + `UWT_LAST_UPDATED =
  "2026-05-26"` added alongside the existing track version constants.
  `RR_VERSION` bumped `"1.18.0"` → `"1.18.1"` (was lagging behind the
  RR v1.18.1 writer shipped earlier the same day — `ANALYZER_SUBSTRATE_VERSION`
  was already at `"0.2.14"` so the constants now agree across the board).
- **Error surfacing**: catches `UWTemplateWriterError` for clean
  reporting; falls back to generic `Exception` with `st.error` for
  unanticipated failures (matches the pattern used by the existing
  RR/T12/AR error handlers above it).

### Design choices

- **Operator uploads the template each session** rather than bundling
  v5 in the repo. Trade-off: one extra file upload per session, but
  zero infra and the operator can swap template versions easily when
  v5.1 ships.
- **Radio for scenario** (not multi-write). Writing both columns would
  double the cell churn for marginal value; analysts can re-run with
  the alternate scenario when needed.
- **Inline summary + drill-in expander** rather than a results page.
  The summary tells you what happened in one line; the expander surfaces
  details when needed without cluttering the success path.
- **Cache caveat banner** is conditional (only fires when t12-path
  `no_source` outcomes exist) — silent on the happy path where the
  analyst already round-tripped through Excel.

### Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` — parses
  clean at 1,394 lines.
- Writer regression test (`tests/test_uw_template_writer.py`) still
  passes on v5 (90 concepts written / 3,232 cells on Homestead).
- No new tests for the Streamlit wiring — Streamlit's session-state
  testing is awkward and the existing writer-module tests cover the
  underlying call path.

### Known limitation surfaced this release

- **Cache state on freshly-built Analyzer bytes**: openpyxl doesn't
  compute formulas, so the Analyzer bytes the app builds via
  `populate_rr_input` / `populate_t12_input` / `populate_ar_collections`
  have *no cached UW Output values*. The writer reads `data_only=True`,
  which returns `None` for uncomputed formulas. Net effect: when the
  analyst uses the inline populate-UW-Template flow on a fresh
  Analyzer (no Excel round-trip), most t12-path concepts come through
  as `no_source`. The cache caveat banner surfaces this clearly. A
  future enhancement could embed a formula evaluator (pycel / formulas
  / xlcalculator) in the pipeline to compute Analyzer values in-Python
  before the writer reads them — non-trivial but would remove the
  Excel-round-trip step entirely.

### Out of scope (still pending)

- **v5.1 template completions** (operator side): Cover substrate version
  stamp + RR Analysis tab-header Period Date metadata cell.
- **Deposit parser support** — substrate slot ready, fixture pending.
- **AR row-level routing** — substantial Track 2/3 upstream work.
- **In-Python formula evaluator** to close the cache caveat (see above).

### Committed-asset addendum (2026-05-26, same release)

Operator dropped a clean blank v5 template at `assets/ALF_UW_Template_v5.xlsx`
(repo root `assets/` — same convention as `fortis_logo.svg` and the Pingkas
logos). Registry's `templates.v5.file` repointed from
`Sample Files/ALF_UW_Template_v5.xlsx` → `assets/ALF_UW_Template_v5.xlsx`;
test fixture `TEMPLATE_V5` constant repointed to match. This makes
writer smoke tests runnable from a cold checkout without needing the
gitignored Sample Files copy. v4 working copy stays in Sample Files —
not committed, not the binding default. Structural verification on the
committed file: 16 sheets, no data rows in Rent Roll Analysis A211+,
Prop Info B4/B20-B22 all empty, AQ211 holds `=SUM(AK211:AO211)` formula.

### Versioning

- UWT code version: **v0.4.1** (Phase 2.5).
- Mapping registry version: **0.3.0** (unchanged from v0.4.0).
- Template versions supported: **v4** + **v5** (v5 default).
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.4.0 — Phase 3: UW Template v5 absorbed (2026-05-26)

Operator authored `ALF_UW_Template_v5.xlsx` externally in Excel (per the
2026-05-25 v4→v5 handoff brief) and dropped it at
`Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v5.xlsx`. v5 is
now the **binding** template version as of 2026-05-26; v4 is retained for
backward compat.

### Shipped

- **Sample Files canonical** — `Sample Files/ALF_UW_Template_v5.xlsx`
  copied in from the Deals folder to remain the registry's canonical
  template location (per the 2026-05-25 decision).
- **Registry extended to v0.3.0**:
  - New `templates.v5` block: intake sheets, paste anchor, capacity
    (`rent_roll_data_end_row: 610` → 400 units, up from v4's 175),
    `monthly_header_strategy` (formula-driven from on-sheet Layer 1 row
    122 — no writer overwrite needed), inventory of new/shifted rows and
    columns, removed sheets (`Additional Fees`), and items deferred to
    v5.1 (Cover substrate stamp; tab-header Period Date metadata cell).
  - v4 block backfilled with `data_end_row: 386` for parity.
  - **Per-concept `targets.v5`** for every concept (inherit v4 unless
    v5 shifted/added the target):
    - **T-12 row shifts** due to new row 115 insert:
      `ebitdarm` N115→N116, `ebitdar` N116→N117.
    - **T-12 closed gaps**:
      `opex_total_excl_mgmt` → N115 (template formula `=N114-N113`;
      writer overwrites with UW Output row 63 when present);
      `ebitda` → N118 (new label-only row; writer populates from UW
      Output row 68).
    - **Capacity closed gaps**:
      `occupied_beds_il/al/mc` → Prop Info `B20/B21/B22` (new rows 19-22
      added; B19 is template-derived sum, writer doesn't touch).
    - **Rent Roll closed gaps**:
      `rr_care_level_tier_label` → AP211+ (writer pastes from Analyzer
      col K); `rr_preleased_date` → AR211+ (writer pastes from Analyzer
      col AJ post-substrate-v0.2.14); `rr_total_ancillary` → AQ211+ but
      status `derived` (template-owned formula `=SUM(AK:AO)`; writer
      skips).
    - **Rent Roll col shifts** per contract §16 (analyst-input cols
      pushed right by 3 to make room for new AP/AQ/AR):
      `rr_ach` AP→**AS**; `rr_market_psf` AQ→**AT**.
- **Writer (`uw_template_writer.py`) updated**:
  - Default `template_version` flipped `v4` → **`v5`**.
  - Reads `rent_roll_data_end_row` from `templates.{v}` block and uses
    it to cap `_write_column_stride` per call. Source-overflow case
    (Analyzer has more populated rows than the template can hold) is
    surfaced as a `PopulateReport` warning, not a crash.
  - CLI default also flipped to v5.
- **Tests updated**:
  - Both smoke tests now exercise v5 by default; `TEMPLATE` constant
    points at `Sample Files/ALF_UW_Template_v5.xlsx`.
  - Empty smoke expects 16 sheets (was 17 — `Additional Fees` removed
    in v5), no longer expects the A210-blank warning (v5 has the header).
  - Populated e2e spot-checks four new v5 features:
    - T-12 Analysis N115 (Total OpEx excl. mgmt — new row)
    - T-12 Analysis N116 (EBITDARM — shifted from N115)
    - T-12 Analysis N118 (EBITDA — new row)
    - Prop Info B20/B21/B22 (Occupied Beds split — new rows)
  - **AQ-formula-preserved assertion**: verifies the template's
    `=SUM(AK211:AO211)` formula at AQ211 survives the writer round-trip
    (the bug caught + fixed during this release — see "Bug caught"
    below).
- **Artifacts regenerated** — `mapping_mindmap.html`, `MAPPING_TRACKER.md`,
  `mapping_tracker.csv` now show both `v4` and `v5` columns per concept.
- **Open questions**: 11 → 8. Four v5 closures
  (EBITDA row, Occupied beds, Preleased v5 column, monthly header
  overwrite). Two new items added (Cover stamp deferred to v5.1; tab-
  header Period Date metadata cell still pending).

### Status rollup at v0.4.0

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 62 | 2 | 1 | 4 | 3 |
| rent_roll | 35 | 33 | 0 | 0 | 0 | 2 |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **95 (86%)** | **2** | **5** | **4** | **5** |

Mapped: 88 → **95** (+7 net — the 7 v4 gap_targets that close into v5
mapped targets). Gap_target: 10 → **2** (only `substrate_version` and
`t12_period_date` remain).

### Bug caught + fixed mid-release

First test run on v5 revealed that `rr_market_psf` (v4 target AQ) was
overwriting v5's new Total Ancillary $ formula cell. Root cause: my Phase
3 extender script inherited v4 targets blindly for concepts not in the
explicit override map, but the 2026-05-26 contract §16 specifies four col
shifts (AP→AS, AQ→AT, AR→AU, AV) that I'd missed. Patched both shifted
concepts (`rr_ach` AP→AS, `rr_market_psf` AQ→AT); analyst-input cols
(`Conc Source` AR→AU, `Effective Conc $` AS→AV) aren't in our registry so
no further action. Test now verifies `AQ211` retains its formula
post-write — drift guard against this exact class of bug.

### Populated-Analyzer e2e on v5 (Homestead, 176 beds)

- **90 concepts written, 3,232 cells populated** (was 85 / 3,627 on v4 —
  fewer cells because the v5 capacity cap of 400 truncates Analyzer's
  formula-column reads of cols T/U more tightly than v4's previously-
  unbounded stride).
- T-12 Analysis N69 EGI $7,001,957 (unchanged ✓)
- T-12 Analysis N115 Total OpEx excl. mgmt **$5,234,474** (new ✓)
- T-12 Analysis N116 EBITDARM $1,767,483 (shifted ✓)
- T-12 Analysis N118 EBITDA **$1,417,385** (new ✓)
- Prop Info B20/B21/B22 Occupied Beds **53 / 40 / 35** (new ✓)
- Rent Roll Analysis AP211 Care Level Tier (None for first bed — fixture
  doesn't populate K for IL units), AR211 Preleased Date (None —
  fixture predates v0.2.13 Preleased capture).
- AQ211 `=SUM(AK211:AO211)` formula preserved ✓.

### Out of scope (Phase 3)

- **Phase 2.5 — Streamlit UI integration** — still pending. Writer ships
  with new v5 default but the app doesn't expose it yet.
- **v5.1 follow-ups** (per Deals-folder release handoff):
  - Cover substrate version stamp (template-side)
  - Rent Roll Analysis tab-header Period Date metadata cell
- **Phase 4 — AR row-level routing** — still pending (gap_source unchanged).
- **Deposit parser support** — still pending a source fixture.

### Versioning

- UWT code version: **v0.4.0** (Phase 3 — v5 absorbed).
- Mapping registry version: **0.3.0**.
- Template version supported: **v4** + **v5** (v5 default).
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.3.0 — Phase 2: writer module (2026-05-25)

The first piece of Track 4 that produces a file. `uw_template_writer.py`
populates an ALF UW Template from a populated Analyzer in a single
pure-function call, driven entirely by the mapping registry.

### Shipped

- **`uw_template_writer.py`** — ~400 LOC.
  - Public API: `populate_uw_template(analyzer_bytes, template_bytes, *,
    template_version='v4', scenario='normalized', registry_path=None,
    include_statuses=None, allow_special_keys=None) -> (bytes, PopulateReport)`.
  - Source-system dispatch on `concept.source.system`:
    - `uw_output` → reads `UW Output!{column}{row}` where `column` resolves
      via `scenario` (`E` for `t12_actual`, `F` for `normalized`); also
      handles literal `B`/`C`/`D` for IL/AL/MC splits.
    - `rr_input` → reads a full column-stride from
      `Rent Roll Input!{column}7:{column}606`, returns a 600-element list.
    - `named_range` → resolves the named range to a qualified address and
      reads the cell.
    - `cell` → direct sheet+address read.
    - `derived` → hard-coded compute for the small set of derived concepts
      (`licensed_beds_total`, `opex_total_incl_mgmt`).
    - `gap` → returns None (writer skips at the no_source branch).
  - Target write modes:
    - Scalar: single cell `{Sheet}!{address}`.
    - Row-stride (address ends in `+`): writes down the column from
      `{start_row}` skipping blank source values. Preserves any template
      cells the source doesn't populate.
  - Loads Analyzer with `data_only=True` (reads cached formula values —
    the Analyzer must be saved through Excel first), template with
    `data_only=False` (preserves formula cells the writer doesn't touch).
  - `PopulateReport` dataclass: per-concept `ConceptResult` (key, path,
    status, outcome, target_address, cells_written, notes, sample_value)
    plus aggregate summary and warnings list.
- **`tests/test_uw_template_writer.py`** — two tests:
  - `test_empty_analyzer_smoke` (always runs) — bundled empty Analyzer +
    Sample Files template. Verifies no crash, report shape, skip-status
    rules, special-key skip on `opex_bad_debt_expense`, bytes round-trip,
    sheet count preserved (17).
  - `test_populated_analyzer_e2e` (skipped if fixture absent) — Homestead
    populated Analyzer. Spot-checks EGI / EBITDARM / GPR values on T-12
    Analysis, confirms 176 populated rows on Rent Roll Analysis row 211+,
    surfaces first-N written concepts for visual inspection.

### Defaults locked in (writer's stance on open questions)

The registry's `open_questions` are mostly **not** strict blockers — the
writer ships with defensible defaults and lets users override at call time:

- **Scenario**: `normalized` (col F). Contract §8 specifies col F is the
  underwriting figure; col E (t12_actual) is for variance.
- **Bad Debt placement**: writes `bad_debt_writeoffs_revenue` →
  `T-12 Analysis!N62` (template's structural revenue contra-line).
  Hard-coded skip on `opex_bad_debt_expense` (would target N106 but would
  double-count). Override with
  `allow_special_keys={'opex_bad_debt_expense'}`.
- **Monthly grid**: annual total only (col N). Cols B–M (Apr-25..Mar-26
  monthly buckets) left blank — the registry's t12 targets all use `N{row}`.
- **Monthly headers**: not overwritten. Template's hardcoded
  `Apr-25..Mar-26` remains.
- **Skip set** (default): `gap_source`, `gap_target`, `header_only`,
  `derived`, `manual`, `substrate_ready_parser_pending`,
  `decided_pending_upstream`.
- **Include set** (default): `{mapped, proposed}`. Override via
  `include_statuses=`.

### Empty-Analyzer smoke (bundled v0.2.14)

Run: 111 concepts processed, **2 cells written** (the few that resolve to
non-blank even on the empty bundled file), 89 no_source, 20 skipped.
One warning about `Rent Roll Analysis!A210` being blank — the Sample Files
working copy of the template predates the contract's row-210 header, so
the canonical template in `Deals/Acquisition/_Template/` won't trigger
this warning.

### Populated-Analyzer end-to-end (Homestead, 176 beds)

Run on `Sample Files/Analyzer with 2026-04-24 Homestead Village Rent Roll
v2 + March 2026 T12 2026-04-24.xlsx`:

- **85 concepts written, 3,627 cells populated**, 6 no_source, 20 skipped.
- Spot-checks: EGI $7,001,957 / EBITDARM $1,767,483 / GPR $9,524,893 —
  values flow correctly through `UW Output!F{12,66,15}` → `T-12 Analysis!N{69,115,58}`.
- Rent Roll Analysis row 211: A1, A1, IL, Occupied, "Janet (Francis) Pierson" —
  first bed row written cleanly. **176 populated rows** in cols A-AC.
- Property Name = None — this fixture is pre-v0.2.8, so `Cover!B5` is a
  manual-entry cell that wasn't populated. Not a writer bug; surfaces a
  fixture limitation cleanly via `no_source` outcome.

### CLI

`python uw_template_writer.py <analyzer.xlsx> <template.xlsx> <output.xlsx>
[--scenario normalized|t12_actual] [--template-version v4]
[--registry path/to/registry.json]` for ad-hoc runs outside the app.

### Out of scope (Phase 2)

- **App integration (Phase 2.5)** — no Streamlit UI button yet. Writer is
  module-level; integration into `app.py` is a follow-up.
- **Cover!B5 named-range resolution on pre-v0.2.8 fixtures** — the
  Homestead fixture predates Cover!B5's auto-resolver formula. No writer
  fix needed; users with current-substrate Analyzers won't see this.
- **Monthly bucket data** — see Phase 3 (extend UW Export contract to
  expose monthly).
- **AR aging row-level routing** — see Phase 4.
- **Deposit parser support** — still waiting on a source-RR fixture with
  a Deposit field (substrate slot is ready since v0.2.14).
- **Template canonical-copy refresh** — Sample Files working copy doesn't
  have rows 177-210 yet; canonical template in
  `Deals/Acquisition/_Template/` does. Replacing the repo's working copy
  is a separate Track 4 housekeeping task.

### Versioning

- UWT code version: **v0.3.0** (Phase 2 — writer module).
- Mapping registry version: **0.2.1** (unchanged — schema is stable).
- Template version supported: **v4**.
- Analyzer substrate mapped against: **v0.2.14**.

---

## v0.2.1 — AI conflict resolved (2026-05-25)

Registry-only release closing the two open questions about column-AI
assignment that v0.2.0 surfaced. Companion to substrate v0.2.14 + RR v1.18.1
(both shipped earlier in the day, same 2026-05-25 chat).

### Shipped

- **Registry bumped** `0.2.0 → 0.2.1`; `analyzer.substrate_version`
  `v0.2.11 → v0.2.14` (matches the just-shipped substrate).
- **`rr_preleased_date`** — source address `AI7:AI606 (until relocated)`
  → `AJ7:AJ606`. Status stays `gap_target` (UW Template v4 still has no
  Preleased Date column — v5 wishlist).
- **`rr_deposit`** — status `decided_pending_upstream` →
  `substrate_ready_parser_pending`. Substrate slot at `Rent Roll Input!AI`
  is now ready (v0.2.14 migration shipped); parser support pending a
  source-RR fixture with a Deposit field. New status added to
  `status_legend`.
- **`v4.rr_input_data_range`** added — documents the widened named-range
  scope `'Rent Roll Input'!$A$7:$AJ$606` (was `$A$7:$S$606`).
- **`open_questions` resolved (2):**
  - Q1 *"Preleased Date relocation"* — closed by substrate v0.2.14.
  - Q2 *"`RR_Input_Data` named range scope"* — closed by v0.2.14 widen.
- **`open_questions` added (1):** Preleased Date still has no UW Template
  v5 column even after the relocation — track 4 follow-up for template v5.
- **Generator updated** (`build_mapping_artifacts.py`):
  - New status `substrate_ready_parser_pending` added to STATUS_COLOR,
    HTML pill class, and status filter dropdown.
- **Artifacts regenerated** — `mapping_mindmap.html`, `MAPPING_TRACKER.md`,
  `mapping_tracker.csv` all carry the v0.2.1 registry.

### Rollup at v0.2.1

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 57 | 7 | 1 | 4 | 3 |
| rent_roll | 35 | 31 | 3 | 0 | 0 | 1 *(substrate_ready_parser_pending)* |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **88 (79%)** | **10** | **5** | **4** | **4** |

Counts unchanged from v0.2.0 — only statuses moved. **Open questions: 12 → 11**
(2 closed, 1 added).

### Out of scope (Phase 1.5)

- Still no writer module — Phase 2.
- Still no Streamlit UI changes.
- No Deposit parser work (waiting on a source fixture).
- No template v5 work.

### Versioning

- UWT code version: **v0.2.1** (Phase 1.5 — AI conflict resolved).
- Mapping registry version: **0.2.1**.
- Template version mapped: **v4** (unchanged).
- Analyzer substrate mapped against: **v0.2.14**.

---

## v0.2.0 — Phase 1: Rent Roll + AR paste paths (2026-05-25)

Extends the Phase-0 single-path registry to model the full **three paste
paths** documented in the 2026-05-25 handoff contract
(`Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md`).
User-provided contract + companion `2026-05-25-uw-template-input-map.html`
input map became the authoritative source for the Rent Roll path crosswalk.

### Shipped

- **Registry extension** to v0.2.0 — 72 → 111 concepts. Path field added to
  every concept (`t12` / `rent_roll` / `ar`). Existing T-12 concepts
  backfilled with `path: 't12'`. Substrate mapped-against bumped v0.2.9 → v0.2.11.
- **Rent Roll path — 35 concepts** mapping `Rent Roll Input` rows 7+ to
  `Rent Roll Analysis` rows 211+ (header row 210). Position shifts captured
  (e.g. Analyzer col F → UW col AC; Analyzer col R → UW col E). Three
  source-side gaps flagged as `gap_target`:
  - `K` Care Level tier label — no template column (v5 wishlist)
  - `S` Period Date — per-row in source, but UW Template wants it as a
    single metadata cell in the tab header
  - `AH` Total Ancillary — no template column (v5 wishlist: formula col
    `=AK+AL+AM+AN+AO`)
  Six new categories: `rr_identity` / `rr_dates` / `rr_rates` /
  `rr_ancillary` / `rr_subtotals` / `rr_other`.
- **AR path — 4 concepts** for aging buckets at `Rent Roll Analysis` cols
  N–Q. All `gap_source` — gated on upstream resident-key join in
  `AR & Collections` (Track 3 follow-up).
- **Deposit concept** (`rr_deposit`) at status `decided_pending_upstream` —
  user-decided 2026-05-25 to land at `Rent Roll Input!AI`. Maps to UW col M.
- **Preleased Date concept** (`rr_preleased_date`) at status `gap_target` —
  v0.2.13 substrate (also 2026-05-25) put Preleased Date at `Rent Roll
  Input!AI`, which now conflicts with the Deposit decision above.
  Per-user-decision Preleased relocates (likely to AJ) — logged in
  `open_questions` as a cross-cutting Track 1 + Track 3 follow-up.
- **Generator extended** (`build_mapping_artifacts.py`):
  - Path filter (T-12 / Rent Roll / AR / all) added to mind-map HTML toolbar.
  - Path-coloured section headers and per-row path tags.
  - Markdown tracker now groups by **path × category** with a top-level
    "Status rollup by path" table.
  - CSV header gains a `path` column (first col).
  - New status legend entry `decided_pending_upstream`.
- **5 new `open_questions`** logged:
  1. Preleased Date relocation (AI conflict — Track 1 + Track 3 cross-cutting)
  2. `RR_Input_Data` named range scope (currently `A7:S606` — too narrow
     for the new cols V–AI paste path)
  3. Preleased Date in template v5 — no target today
  4. Rent Roll Analysis header rows 1–209 (writer must not touch)
  5. AR aging row-level routing — upstream resident-key join needed
- **`intake_targets_unmapped`** updated: removed Phase-0 placeholder ("whole
  RR Analysis sheet manual paste"); replaced with three specific entries
  covering diagnostic rows 1–209, the row-211 paste anchor, and the
  formula / manual columns (V, X, Y, Z, AA, AB, AR, AS).
- **`SPEC-UWT.md`** restructured for three-path framing; `CHANGELOG-UWT.md`
  this entry; `CLAUDE.md` Track 4 row + last-updated stamp.

### Rollup at Phase 1

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 57 | 7 | 1 | 4 | 3 |
| rent_roll | 35 | 31 | 3 | 0 | 0 | 1 |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **88 (79%)** | **10** | **5** | **4** | **4** |

### Decisions made this release

- **AI column → Deposit, Preleased relocates.** Cross-cutting follow-up
  filed; substrate v0.2.14 (or follow-up) needs to move Preleased Date out
  of AI before Deposit can land. `mappings.py` / `normalizer.py` Preleased
  capture stays unchanged; only `analyzer_rr_writer.py` `COL_AI_INDEX` for
  Preleased Date relocates, plus the substrate header at `Rent Roll
  Input!AI4` and the `RR_Input_Data` named-range scope.
- **Repo's `Sample Files/ALF_UW_Template_v4.xlsx` stays canonical for the
  registry** (per-deal Deals folder copies are workspace artifacts).
- **Flat schema with `path` field** — chosen over nested-by-path or
  separate-registries-per-path. Registry schema unchanged (still
  `uw-mapping/v1`).

### Out of scope (Phase 1)

- No writer module (still mapping-only).
- No Streamlit UI changes.
- No edits to Analyzer code or substrate (substrate stays at v0.2.13 from
  the v0.1.18 / Section N work that also shipped 2026-05-25; registry
  *targets* v0.2.11 from the handoff contract since v0.2.12 / v0.2.13 do
  not change UW Output structure).
- No execution of the AI-column relocation (logged as an open question, not
  built here — that's a separate cross-cutting PR).

### Versioning

- UWT code version: **v0.2.0** (Phase 1).
- Mapping registry version: **0.2.0**.
- Template version mapped: **v4** (unchanged).
- Analyzer substrate mapped against: **v0.2.11** (from handoff contract).

---

## v0.1.0 — Phase 0: inspection + mapping registry (2026-05-23)

Track 4 seed release. No code that mutates anything — purely an inspection
pass over `ALF_UW_Template_v4.xlsx`, a modular mapping registry against
Analyzer substrate v0.2.9, and generated artifacts.

### Shipped

- **`tools/uw_template/registry.json`** — 72-concept semantic-key mapping
  registry, schema `uw-mapping/v1`. Version-keyed targets (`targets.v4 = {...}`)
  so future template versions extend rather than rewrite. 57 of 72 concepts
  are `mapped` (79%); the remaining 15 are `proposed`, `gap_source`, `gap_target`,
  `header_only`, or `derived`. Six categories: metadata (4) / capacity (7) /
  revenue (9) / waterfall (5) / labor (15) / nonlabor (26) / mgmt_noi (6).
- **`tools/uw_template/build_mapping_artifacts.py`** — generator that emits
  the three artifacts below from `registry.json`. Re-run after any registry
  edit. Modular: no schema changes required to add template `v5` later.
- **`tools/uw_template/mapping_mindmap.html`** — self-contained interactive
  visualizer (no CDN), filter by status / search / switch template version.
- **`tools/uw_template/MAPPING_TRACKER.md`** — human-readable tracker with
  status legend, rollup table, and per-category mapping tables.
- **`tools/uw_template/mapping_tracker.csv`** — diffable CSV (one row per
  concept × template version) for spotting drift across template versions.
- **`SPEC-UWT.md`** — Track 4 spec: scope, registry schema, structural
  mismatches, phase plan, versioning, layout.
- **`CHANGELOG-UWT.md`** — this file.
- **`CLAUDE.md`** — Track 4 row added to the workstream tracks table.

### Structural findings (carry-forward to Phase 1)

The Phase 1 writer cannot ship until these are answered. Filed as
`open_questions` in `registry.json`:

1. **Bad Debt placement** — revenue contra (template `N62`) vs opex
   (template `N106`). UW Output exposes one value; template has two slots.
2. **2nd Person Revenue** — template has dedicated `N67`; Analyzer rolls 2P
   into `Rent Roll Input!V` and does not break it out at UW Output.
3. **Monthly grid** — template `T-12 Analysis!B56:M56` headers
   `Apr-25..Mar-26` invite 12-month bucket paste; UW Export only exposes
   annual. Phase 1 stance: fill col N only, leave B-M blank. Phase 2
   widens the upstream contract.
4. **EBITDA row** — UW Output row 68 has no template target. Add to
   template (request to template author) or drop from writer scope.
5. **Occupied beds** — UW Output row 71 (IL/AL/MC) has no Prop Info target.
6. **`Rent Roll Analysis!A5` date format** — confirm RR period date format
   (yyyy-mm-dd vs Excel date) and which cell receives it (B5 vs D5).
7. **Monthly header cells** — should writer overwrite hardcoded
   `Apr-25..Mar-26` with actual T-12 months from `T12_Period_Date`, or
   leave the placeholder?

### Out of scope (Phase 0)

- No `uw_template_writer.py` — Phase 0 is mapping-only.
- No Streamlit UI changes — no new download button.
- No edits to Analyzer (Track 3) — substrate stays at v0.2.9.
- No commitable copy of the template — `Sample Files/ALF_UW_Template_v4.xlsx`
  remains gitignored. A canonical committable copy under
  `tools/uw_template/assets/` is deferred to Phase 1 once writer mechanics
  are decided.
- No journal entry on the registry's behalf for Tracks 1/2/3.
- `_raw_extraction.json` and `_template_v4_dump.txt` are build artifacts
  used during inspection — left in place for reproducibility but not
  consumed by the writer.

### Versioning

- UWT code version: **v0.1.0** (Phase 0 seed).
- Mapping registry version: **0.1.0** (stamped in `registry.json`).
- Template version mapped: **v4** (filename: `ALF_UW_Template_v4.xlsx`).
- Analyzer substrate mapped against: **v0.2.9**.
