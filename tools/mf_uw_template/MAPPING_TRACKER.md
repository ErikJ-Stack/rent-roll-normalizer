# MF UW Model — Mapping Tracker

> Generated from `tools/mf_uw_template/registry.json` on 2026-06-04 12:27 UTC.  **Do not edit by hand** — edit `registry.json` and re-run `python tools/mf_uw_template/build_mapping_artifacts.py`.

- Product line: **MF** (multifamily). No Analyzer substrate — source is the raw operator docs in `MF Docs/`.
- Primary template: `v15` → `assets/MF_UW_Model_v15.xlsx`
- Intake sheets: `Rent Roll Analysis`, `T-12 Analysis`

## Status legend

- **`mapped`** — 1:1 mapping confirmed by header/label match + semantic review of the operator doc vs the template column.
- **`proposed`** — Best-guess mapping; needs confirmation before a future writer relies on it.
- **`gap_source`** — Template column wants data the basic operator doc does not expose cleanly (e.g. per-unit ancillary fee breakouts, AR aging requiring a resident-key join, the COA->bucket mapping). A future mf_* parser must supply it.
- **`gap_target`** — An operator value has no column in the template to receive it.
- **`derived`** — Template cell is computed by formula from the pasted data (template-internal); writer must not overwrite.
- **`manual`** — Template field is filled by the analyst by hand / external research (e.g. Prop Info market data, Scenarios assumptions); not part of the intake pipeline.
- **`header_only`** — Section separator / label row with no value; skip in writer.

## Status rollup

| Status | Count |
|---|---|
| `gap_source` | 21 |
| `mapped` | 19 |
| `proposed` | 5 |
| `derived` | 1 |
| **Total concepts** | **46** |

## Status rollup by path

| Path | Total | mapped | gap_source | proposed | other |
|---|---|---|---|---|---|
| **metadata** | 4 | 2 | 0 | 2 | 0 |
| **rent_roll** | 37 | 14 | 20 | 3 | 0 |
| **t12** | 5 | 3 | 1 | 0 | 1 |

## Mappings by path & category

### METADATA · PROPERTY / PERIOD → PROP INFO + HEADERS

#### metadata (4)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Property Name** <br/> `property_name` | `RR!A3` | `Prop Info!B4` | `mapped` | Drives Cover!B5, every sheet title (=IF('Prop Info'!B4=""...)), and the Rent Roll Analysis / T-12 Analysis health checks. Present in all four operator doc header blocks. |
| **Total Units** <br/> `units_total` | `derived` | `Prop Info!B6` | `mapped` | Prop Info!B6 is the denominator for occupancy %, PUPM, and the Rent Roll Analysis G5 reconciliation (RR count I5 must equal B6). |
| **Rent Roll period / as-of date** <br/> `rr_period_date` | `RR!A4` | `Rent Roll Analysis!A5` | `proposed` | RR Analysis A5 'Date:' label cell. Exact target cell for the value (vs label) to be confirmed when the writer is built. |
| **T-12 period range** <br/> `t12_period` | `T-12!A5` | `T-12 Analysis!C105` | `proposed` | Drives the 12 monthly column headers on T-12 Analysis Layer 1 (C105:N105). The T-12 monthly columns and period must align with the operator's actual months. |

### RENT ROLL PATH · OPERATOR RR (+AR) → RENT ROLL ANALYSIS GRID ROW 273+

#### rr_identity (5)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Building** <br/> `rr_bldg` | `RR!A` | `Rent Roll Analysis!A273+` | `mapped` | Source 'Bldg-Unit' (e.g. 'A1') splits: building prefix -> A, unit -> B. Hidden Lakes uses single-letter building + unit number. |
| **Unit #** <br/> `rr_unit` | `RR!A` | `Rent Roll Analysis!B273+` | `mapped` | Unit portion of 'Bldg-Unit'. |
| **Unit Type** <br/> `rr_type` | `RR!B` | `Rent Roll Analysis!C273+` | `mapped` | MF floorplan code (bed x bath). Feeds the floor-plan rollups in Recapture & Upside / Rental Comps. |
| **Square Feet** <br/> `rr_sf` | `RR!C` | `Rent Roll Analysis!D273+` | `mapped` |  |
| **Resident** <br/> `rr_resident` | `RR!E` | `Rent Roll Analysis!F273+` | `mapped` | Vacant units show '-- Vacant --'. The '**' prefix convention drives the Legal flag (see rr_legal). |

#### rr_status (2)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Unit Status** <br/> `rr_status` | `RR!D` | `Rent Roll Analysis!E273+` | `proposed` | Template's status taxonomy is matched by COUNTIF wildcards: 'Occupied*', 'Vacant Unrented Ready', 'Vacant Unrented Not Ready', 'Down*', 'Vacant*Leased*'/'Vacant Rented*', 'Model'/'Employee'/'Office', 'Occupied No Notice'. Operator 'Unit Status' values (e.g. 'Occupied No Notice', 'Vacant Unrented Not Ready') already align closely; a future normalizer should confirm/standardize the closed vocab. proposed until the status-string map is locked. |
| **Legal / Eviction flag** <br/> `rr_legal` | `derived` | `Rent Roll Analysis!G273+` | `proposed` | Template col G is a boolean used by Section C (legal/eviction cohort), Q5 legal count, and B113/D113 (units flagged + AR exposure). Derive from the '**' name prefix; the Eviction Status Report / bankruptcy disclosures in the DD checklist may refine. 9 active evictions + 1 bankruptcy known on Hidden Lakes. |

#### rr_dates (4)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Move-In Date** <br/> `rr_move_in` | `RR!F` | `Rent Roll Analysis!H273+` | `mapped` | Drives the Resident Tenure Cohort analysis (Section G uses TODAY()-H). |
| **Lease Start** <br/> `rr_lease_start` | `RR!G` | `Rent Roll Analysis!I273+` | `mapped` |  |
| **Lease End** <br/> `rr_lease_end` | `RR!H` | `Rent Roll Analysis!J273+` | `mapped` | Drives the Lease Expiration Schedule (Section E, 24-month forward buckets keyed on col J). |
| **Expected Move-Out** <br/> `rr_exp_move_out` | `RR!I` | `Rent Roll Analysis!K273+` | `mapped` | Notice-to-vacate / scheduled move-out. Mostly blank in the source unless a move-out is scheduled. |

#### rr_rates (4)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Market Rent** <br/> `rr_market_rent` | `RR!J` | `Rent Roll Analysis!L273+` | `mapped` | Drives Market GPR (Section D B26), loss-to-lease, and vacancy loss. |
| **Actual Charges** <br/> `rr_actual_charges` | `RR!K` | `Rent Roll Analysis!M273+` | `mapped` | Total billed charges incl. ancillaries. Cross-check against Sched Chgs + the W-AK breakouts. |
| **Scheduled Charges** <br/> `rr_scheduled_charges` | `RR!L` | `Rent Roll Analysis!N273+` | `mapped` | Contractual base rent on occupied units. Drives Scheduled GPR (Section D B27) and avg-sched-per-unit metrics. |
| **Deposit Held** <br/> `rr_deposit` | `RR!N` | `Rent Roll Analysis!P273+` | `mapped` | Security deposit. Feeds Net Exposure (Balance - Deposit) on the Top-10 delinquent table. |

#### rr_ar (5)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Balance (AR)** <br/> `rr_balance` | `RR!M` | `Rent Roll Analysis!O273+` | `mapped` | Total AR balance per unit. Drives N5 Total AR, the delinquency tiers (<500 / >=500), and Top-10 delinquent list. Also present (and should reconcile) in the AR doc col J. |
| **AR Aging — 0-30 Days** <br/> `rr_ar_0_30` | `AR!E` | `Rent Roll Analysis!Q273+` | `gap_source` | Aging lives in a SEPARATE AR doc and must be joined to the RR grid on Bldg-Unit. Template note (A88) says 'paste from separate aging report into cols Q-T'. Requires the resident-key join the future mf_ar parser will own. The AR doc is dated Mar 2026 vs RR Apr 2026 — period-mismatch caveat. |
| **AR Aging — 31-60 Days** <br/> `rr_ar_31_60` | `AR!F` | `Rent Roll Analysis!R273+` | `gap_source` | See rr_ar_0_30 — same AR-join gap. |
| **AR Aging — 61-90 Days** <br/> `rr_ar_61_90` | `AR!G` | `Rent Roll Analysis!S273+` | `gap_source` | See rr_ar_0_30 — same AR-join gap. |
| **AR Aging — 90+ Days** <br/> `rr_ar_90_plus` | `AR!H` | `Rent Roll Analysis!T273+` | `gap_source` | See rr_ar_0_30 — same AR-join gap. Drives D94 aging-ties reconciliation: SUM(Q:T) must equal col-O Total AR. |

#### rr_ancillary (15)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **MTM Fees (per unit)** <br/> `rr_anc_mtm_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!W273+` | `gap_source` | Per-unit other-income breakout mirroring _StdCOA. Not in the basic RR doc; only the Sortable-RR 'Source Data' charge-code grid carries per-fee detail. Future mf_ parser must map charge codes -> buckets. |
| **Application Fees (per unit)** <br/> `rr_anc_application_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!X273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Late Fees (per unit)** <br/> `rr_anc_late_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!Y273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Utility Reimbursement (per unit)** <br/> `rr_anc_utility_reimbursement` | `Sortable-RR/Source Data` | `Rent Roll Analysis!Z273+` | `gap_source` | RUBS / utility billbacks. See rr_anc_mtm_fees — ancillary breakout gap. |
| **Pet Fees (per unit)** <br/> `rr_anc_pet_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AA273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Parking Income (per unit)** <br/> `rr_anc_parking_income` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AB273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Amenity Fees (per unit)** <br/> `rr_anc_amenity_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AC273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Admin Fees (per unit)** <br/> `rr_anc_admin_fees` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AD273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Insurance Pass-Thru (per unit)** <br/> `rr_anc_insurance_passthru` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AE273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Misc Other Income (per unit)** <br/> `rr_anc_misc_other_income` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AF273+` | `gap_source` | Catch-all other income. See rr_anc_mtm_fees — ancillary breakout gap. |
| **Storage / Common Bins (per unit)** <br/> `rr_anc_storage` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AG273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Package Service / Lockers (per unit)** <br/> `rr_anc_package_lockers` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AH273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Lease Lock Fee (per unit)** <br/> `rr_anc_lease_lock_fee` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AI273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Valet Trash (per unit)** <br/> `rr_anc_valet_trash` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AJ273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |
| **Lease Break Fee (per unit)** <br/> `rr_anc_lease_break_fee` | `Sortable-RR/Source Data` | `Rent Roll Analysis!AK273+` | `gap_source` | See rr_anc_mtm_fees — ancillary breakout gap. |

#### rr_other (2)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Status Flag** <br/> `rr_status_flag` | `—  (no operator source)` | `Rent Roll Analysis!U273+` | `gap_source` | Column U semantics unconfirmed; not in the operator RR. Defer until the writer pass clarifies whether it is analyst-input or derived. |
| **Notes** <br/> `rr_notes` | `AR!K` | `Rent Roll Analysis!V273+` | `proposed` | Best source is the AR doc's 'Last Delinquency Note' (joined on Bldg-Unit). Optional / informational column. |

### T-12 PATH · OPERATOR T-12 → T-12 ANALYSIS LAYER 1 ROW 106+

#### t12_raw (3)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **Account #** <br/> `t12_acct` | `T-12!A` | `T-12 Analysis!A106+` | `mapped` | PSI account number. Direct paste into Layer 1 col A. 101 GL lines on Hidden Lakes. |
| **Account Name (raw)** <br/> `t12_acct_name` | `T-12!B` | `T-12 Analysis!B106+` | `mapped` | Raw PSI account name. Direct paste into Layer 1 col B. |
| **12 monthly columns (Apr-25..Mar-26)** <br/> `t12_monthly_block` | `T-12!C:N` | `T-12 Analysis!C106:N255` | `mapped` | Direct 12-month paste block. Source period (Apr 2025-Mar 2026) aligns with the template's month headers. Layer 1 col O re-derives T-12 Total via =SUM(C:N); Layer 3 SUMIFS aggregate by bucket. |

#### t12_mapping (1)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **→ MAPPING (_StdCOA bucket per line)** <br/> `t12_mapping` | `—  (no operator source)` | `T-12 Analysis!P106+` | `gap_source` | THE intelligence layer of the T-12 path — the MF equivalent of ALF's Description_Map. Every Layer-3 SUMIFS keys on this string. A future mf_t12 normalizer must classify each raw line into a _StdCOA bucket. Pre-filled example mappings exist on rows 106-185 for Hidden Lakes (analyst-authored), demonstrating the target vocabulary. |

#### t12_derived (1)

| Concept | Source | Target (`v15`) | Status | Notes |
|---|---|---|---|---|
| **T-12 Total (per line)** <br/> `t12_total` | `derived` | `T-12 Analysis!O106+` | `derived` | Self-derives from the pasted monthly block. The operator T-12 has its own Total in col O; the template recomputes to stay internally consistent. |

## Unmapped template surface (writer does NOT populate)

- **`Prop Info`** (manual) — rows 5-47 (except B4/B6 which are mapped): Property physical details (buildings, year built, sq ft, parking, class), market data (MSA pop, income, vacancy, rent growth, supply), utility metering, value-add thesis. Per the Data Refresh sheet, market fields can auto-populate via Power Query (Census ACS / FRED) or a separate AI Market Research tool. Not part of the intake pipeline.
- **`T-12 Analysis`** (derived) — rows 1-101 + 257-262: Layer 1 (rows 105-255) is the paste target. Rows 1-54 are diagnostics (reconciliation, T-3/T-12 trend, econ-vs-physical occupancy, bad-debt layering, tax/insurance accrual checks). Rows 56-101 are Layer 3 standardized aggregation (SUMIFS by col-P bucket). Rows 257-262 are raw totals reconciliation. Writer must not overwrite any of these.
- **`Rent Roll Analysis`** (derived) — rows 1-271: The grid (rows 272 header + 273-1772 data) is the paste target. Rows 1-271 are diagnostic dashboards computed from the grid: health check (row 5), unit status taxonomy (C), GPR reconciliation (D), lease expiration schedule (E), days-vacant tracker (F), tenure cohort (G), AR aging summary (H), top-10 delinquent (I). Writer must not overwrite.
- **`Scenarios / Acquisition Costs / P&L / Loans / Waterfall / Exit / XIRR / Sensitivity / LP Return / Portfolio Rollup / Recapture & Upside / Capex / Payroll / Rental Comps / Lease-Up & Capital Call`** (manual) — —: Downstream underwriting model sheets (assumptions, debt, returns, sensitivity). Equivalent to the ALF downstream UW workbook — consume the analysis layers, not intake targets. Analyst-driven; out of scope for the intake mapping.

## Open questions

- OM (Offering Memorandum) intake — NOT BUILT. The 4th operator doc type (comps + property info -> Prop Info / Rental Comps). The main remaining MF intake build; needs a sample OM doc (none in MF Docs/ yet).
- redIQ Sortable-RR ancillary path — LOW PRIORITY. Itemized 'Operations' RRs now break out W-AK inline from col L (MF v0.4.2), so the Sortable-RR 'Source Data' charge-code path is only needed if an operator provides ONLY a non-itemized basic RR plus a separate Sortable-RR. Build if/when such a case appears.
- Column U 'Status Flag' (Rent Roll Analysis) — semantics still unconfirmed (analyst-input vs derived); deferred to whenever it matters (SPEC-MF §2.7).
- RESOLVED by the parser build (MF v0.2.0-v0.4.4, 2026-06-03), retained for traceability: (a) T-12 COA->_StdCOA dictionary -> coa_seed.csv + mf_mappings.classify_t12_account (5 formats, 100% coverage, penny-exact reconciliation); (b) AR Bldg-Unit join + period handling -> mf_ar_parser.join_ar_to_units (49/49 on Avana, >45-day warning, two-way unmatched report); (c) status taxonomy -> mf_mappings.normalize_status; (d) W-AK ancillary breakout for itemized RRs -> mf_mappings.classify_charge_code + writer; (e) template versioning -> reuse the v15 filename, refresh the committed asset via verbatim byte-copy after an anchor pre-flight diff (MF v0.4.4); (f) Subsidy Rent stays folded in scheduled charges -> GPR (operator-confirmed, no dedicated column).
- Reference — FIVE MF T-12 formats catalogued (the format detector handles all): PSI flat (Hidden Lakes), QuickBooks nested P&L (Blairstone), Yardi numbered (Avana), Yardi/YSI (Ascend), Tzadik/AppFolio name-only (Copeland). Avana + Ascend share the identical Yardi standard chart (41000 Market Rent, 41100 Vacancy, 51010 Mgmt Salaries, 61030 Mgmt Fee, 62xxx Taxes, 63xxx Insurance, 70000-89999 below-the-line). Two RR row shapes handled: one-row-per-unit + itemized 'charge codes' (multi-row). Each new operator format may still need the parser to learn it (broadens with samples).
