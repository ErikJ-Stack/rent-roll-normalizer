# ALF UW Template — Mapping Tracker

> Generated from `tools/uw_template/registry.json` on 2026-05-26 18:12 UTC.  **Do not edit by hand** — edit `registry.json` and re-run `python tools/uw_template/build_mapping_artifacts.py`.

- Analyzer source: `ALF_Financial_Analyzer_Only.xlsx` (substrate `v0.2.14`)
- Primary template: `v4` → `Sample Files/ALF_UW_Template_v4.xlsx`
- Intake sheets: `Prop Info`, `T-12 Analysis`, `Rent Roll Analysis`

## Status legend

- **`mapped`** — 1:1 mapping confirmed by label match + semantic review.
- **`proposed`** — Best-guess mapping; needs user confirmation before writer relies on it.
- **`gap_source`** — Template wants data the Analyzer does not currently expose via UW Export (e.g. monthly buckets, 2nd-person breakout).
- **`gap_target`** — UW Output produces a value the template has no row to receive (e.g. EBITDA row 68).
- **`header_only`** — UW Output row is a visual section separator with no value; skip in writer.
- **`manual`** — Template field is filled by the analyst by hand / from external research (not part of the UW pipeline).
- **`derived`** — Template cell is computed by formula from other mapped cells (template-internal); writer must not overwrite.
- **`decided_pending_upstream`** — Mapping decision is locked but the upstream Analyzer change has not yet shipped. Writer cannot ship until the upstream column lands.
- **`substrate_ready_parser_pending`** — Upstream substrate change has shipped (column reserved + headers + named-range scope), but the parser does not yet populate the column. Writer clears the slot defensively. Waiting on a source fixture.

## Status rollup

| Status | Count |
|---|---|
| `mapped` | 95 |
| `gap_source` | 5 |
| `proposed` | 4 |
| `derived` | 3 |
| `gap_target` | 2 |
| `header_only` | 1 |
| `substrate_ready_parser_pending` | 1 |
| **Total concepts** | **111** |

## Status rollup by path

| Path | Total | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| **t12** | 72 | 62 | 2 | 1 | 4 | 3 |
| **rent_roll** | 35 | 33 | 0 | 0 | 0 | 2 |
| **ar** | 4 | 0 | 0 | 4 | 0 | 0 |

## Mappings by path & category

### T-12 PATH · UW OUTPUT → T-12 ANALYSIS

#### metadata (4)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Property Name** <br/> `property_name` | `@Property_Name → Cover!B5` | `Prop Info!B4` | `mapped` | Named range. Same value drives UW Export!B3 metadata header. |
| **Rent Roll Period (as-of date)** <br/> `rr_period_date` | `@RR_Period_Date → Rent Roll Recon!B2` | `Rent Roll Analysis!B5` | `proposed` | Template's `Date:` cell at A5/B5 likely takes RR period. Confirm format expectations. |
| **T12 Period End** <br/> `t12_period_date` | `@T12_Period_Date → T12 Analytics!E2` | `—` | `gap_target` | Template Layer 3 monthly header (B56:M56) is hardcoded Apr-25..Mar-26. To respect the actual T12 period the writer would need to overwrite those headers, or template needs a single period cell. |
| **Substrate version stamp** <br/> `substrate_version` | `Cover!B8` | `—` | `gap_target` | Template has no version-stamp cell. Recommend adding one (e.g. Cover!F1 in template) so each populated copy carries provenance. |

#### capacity (7)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Licensed beds — IL** <br/> `licensed_beds_il` | `UW Output!B70` | `Prop Info!B16` | `mapped` | UW Output row 70 IL split. |
| **Licensed beds — AL** <br/> `licensed_beds_al` | `UW Output!C70` | `Prop Info!B17` | `mapped` |  |
| **Licensed beds — MC** <br/> `licensed_beds_mc` | `UW Output!D70` | `Prop Info!B18` | `mapped` |  |
| **Licensed bed count (total)** <br/> `licensed_beds_total` | `derived` | `Prop Info!B15` | `mapped` | Writer sums the three care-type counts. |
| **Stabilized occupied beds — IL** <br/> `occupied_beds_il` | `UW Output!B71` | `—` | `mapped` | Template has no occupied-bed split rows. Total occupancy is computed inside Rent Roll Analysis from the pasted rent roll; consider deferring or surfacing as a metadata cell. · v5: Closed in v5 — Prop Info rows 19-22 added. Writer populates B20 from UW Output!B71. |
| **Stabilized occupied beds — AL** <br/> `occupied_beds_al` | `UW Output!C71` | `—` | `mapped` | v5: Closed in v5 — writer populates B21 from UW Output!C71. |
| **Stabilized occupied beds — MC** <br/> `occupied_beds_mc` | `UW Output!D71` | `—` | `mapped` | v5: Closed in v5 — writer populates B22 from UW Output!D71. |

#### revenue (9)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Base rent (net of waterfall)** <br/> `base_rent_normalized` | `UW Output!E_or_F6` | `T-12 Analysis!N63` | `mapped` | Analyzer's 'Base rent (normalized)' is conceptually the net-of-vacancy/LTL/concessions rent that flows into EGI — matches template 'Net Rent Revenue'. Annual total only (col N). |
| **LOC / Care Services Revenue** <br/> `loc_revenue` | `UW Output!E_or_F7` | `T-12 Analysis!N64` | `mapped` |  |
| **Community / Move-in Fees** <br/> `community_movein_fees` | `UW Output!E_or_F8` | `T-12 Analysis!N65` | `mapped` |  |
| **Concessions & Specials** <br/> `concessions_specials` | `UW Output!E_or_F9` | `T-12 Analysis!N61` | `mapped` | Template puts Concessions in the GPR waterfall block (row 61) — Analyzer lists it as a revenue contra-line at row 9. Sign convention: should arrive negative-signed (Analyzer convention). |
| **Respite Care Revenue** <br/> `respite_care` | `UW Output!E_or_F10` | `T-12 Analysis!N66` | `mapped` |  |
| **Other Community Revenue** <br/> `other_community_revenue` | `UW Output!E_or_F11` | `T-12 Analysis!N68` | `mapped` |  |
| **Effective Gross Income (EGI)** <br/> `egi` | `UW Output!E_or_F12` | `T-12 Analysis!N69` | `mapped` |  |
| **2nd Person Revenue** <br/> `second_person_revenue` | `derived` | `T-12 Analysis!N67` | `gap_source` | Template has a dedicated 2P Revenue row but UW Output does not. Options: (a) extend UW Output with a new row; (b) writer derives from RR_Input_Data!V column directly; (c) leave blank for analyst entry. |
| **Bad Debt / Write-offs (revenue offset)** <br/> `bad_debt_writeoffs_revenue` | `UW Output!E_or_F57` | `T-12 Analysis!N62` | `proposed` | Conceptual divergence: template places Bad Debt as a revenue contra-line (row 62, above Net Rent Revenue at 63); Analyzer places it as an opex line (UW Output row 57). For the template to balance, the value should likely be pasted into row 62 AND row 106 reset to zero — or vice versa. Decide which placement is canonical for the model before writer ships. |

#### waterfall (5)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Gross Potential Rent (GPR)** <br/> `gpr_base` | `UW Output!E_or_F15` | `T-12 Analysis!N58` | `mapped` |  |
| **Physical vacancy loss** <br/> `physical_vacancy_loss` | `UW Output!E_or_F16` | `T-12 Analysis!N60` | `mapped` |  |
| **Physical vacancy rate %** <br/> `physical_vacancy_rate_pct` | `UW Output!E_or_F17` | `—` | `derived` | Template likely computes vacancy% in Rent Roll Analysis section C/E or T-12 Analysis section D; not a paste target. Writer must NOT write percentages into the dollar grid. |
| **Loss to Lease** <br/> `loss_to_lease` | `UW Output!E_or_F18` | `T-12 Analysis!N59` | `mapped` |  |
| **Loss to Lease as % of GPR** <br/> `loss_to_lease_pct_gpr` | `UW Output!E_or_F19` | `—` | `derived` |  |

#### labor (15)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Care Staff Labor** <br/> `labor_care_staff` | `UW Output!E_or_F22` | `T-12 Analysis!N71` | `mapped` |  |
| **Wellness / Care Coordinators** <br/> `labor_wellness` | `UW Output!E_or_F23` | `T-12 Analysis!N72` | `mapped` |  |
| **Contract / Agency Labor** <br/> `labor_agency` | `UW Output!E_or_F24` | `T-12 Analysis!N73` | `mapped` |  |
| **Activities Labor** <br/> `labor_activities` | `UW Output!E_or_F25` | `T-12 Analysis!N74` | `mapped` |  |
| **Dining / Food Service Labor** <br/> `labor_dining` | `UW Output!E_or_F26` | `T-12 Analysis!N75` | `mapped` |  |
| **Maintenance & HK Labor** <br/> `labor_maint_hk` | `UW Output!E_or_F27` | `T-12 Analysis!N76` | `mapped` |  |
| **Administrative Labor** <br/> `labor_admin` | `UW Output!E_or_F28` | `T-12 Analysis!N77` | `mapped` |  |
| **Bonus Wages** <br/> `labor_bonus` | `UW Output!E_or_F29` | `T-12 Analysis!N78` | `mapped` |  |
| **Overtime Wages** <br/> `labor_overtime` | `UW Output!E_or_F30` | `T-12 Analysis!N79` | `mapped` |  |
| **PTO Wages** <br/> `labor_pto` | `UW Output!E_or_F31` | `T-12 Analysis!N80` | `mapped` |  |
| **Payroll Taxes** <br/> `labor_payroll_taxes` | `UW Output!E_or_F32` | `T-12 Analysis!N81` | `mapped` |  |
| **Employee Benefits** <br/> `labor_benefits` | `UW Output!E_or_F33` | `T-12 Analysis!N82` | `mapped` |  |
| **Workers' Comp Insurance** <br/> `labor_workers_comp` | `UW Output!E_or_F34` | `T-12 Analysis!N83` | `mapped` |  |
| **Employee 401(k)** <br/> `labor_401k` | `UW Output!E_or_F35` | `T-12 Analysis!N84` | `mapped` |  |
| **Total Labor & Burden** <br/> `labor_total` | `UW Output!E_or_F36` | `T-12 Analysis!N85` | `mapped` | Subtotal — writer should write this even though template likely re-derives it; supports the reconciliation block at rows 4-5. |

#### nonlabor (26)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Food Cost** <br/> `opex_food_cost` | `UW Output!E_or_F38` | `T-12 Analysis!N87` | `mapped` |  |
| **Dining & Kitchen Supplies** <br/> `opex_dining_supplies` | `UW Output!E_or_F39` | `T-12 Analysis!N88` | `mapped` |  |
| **Nursing & Care Supplies** <br/> `opex_nursing_supplies` | `UW Output!E_or_F40` | `T-12 Analysis!N89` | `mapped` |  |
| **Recreation Supplies** <br/> `opex_recreation_supplies` | `UW Output!E_or_F41` | `T-12 Analysis!N90` | `mapped` |  |
| **R&M Fixed** <br/> `opex_rm_fixed` | `UW Output!E_or_F42` | `T-12 Analysis!N91` | `mapped` |  |
| **R&M Variable** <br/> `opex_rm_variable` | `UW Output!E_or_F43` | `T-12 Analysis!N92` | `mapped` |  |
| **HK & Laundry Supplies** <br/> `opex_hk_laundry` | `UW Output!E_or_F44` | `T-12 Analysis!N93` | `mapped` |  |
| **Sales, Adv. & Marketing** <br/> `opex_marketing` | `UW Output!E_or_F45` | `T-12 Analysis!N94` | `mapped` |  |
| **Referral Fees** <br/> `opex_referral_fees` | `UW Output!E_or_F46` | `T-12 Analysis!N95` | `mapped` |  |
| **Utilities** <br/> `opex_utilities` | `UW Output!E_or_F47` | `T-12 Analysis!N96` | `mapped` |  |
| **Telephone / IT** <br/> `opex_telephone_it` | `UW Output!E_or_F48` | `T-12 Analysis!N97` | `mapped` |  |
| **P&C Insurance** <br/> `opex_pc_insurance` | `UW Output!E_or_F49` | `T-12 Analysis!N98` | `mapped` |  |
| **Auto Insurance** <br/> `opex_auto_insurance` | `UW Output!E_or_F50` | `T-12 Analysis!N99` | `mapped` |  |
| **Fire / Security Monitoring** <br/> `opex_fire_security` | `UW Output!E_or_F51` | `T-12 Analysis!N100` | `mapped` |  |
| **Pest Elimination** <br/> `opex_pest` | `UW Output!E_or_F52` | `T-12 Analysis!N101` | `mapped` |  |
| **Real Estate Taxes** <br/> `opex_re_taxes` | `UW Output!E_or_F53` | `T-12 Analysis!N102` | `mapped` | Template Section F (rows 40-44) provides a separate RE Tax accrual check — pro forma override expected. The Layer 3 paste at N102 carries the T-12 actual. |
| **Personal Property Taxes** <br/> `opex_personal_prop_taxes` | `UW Output!E_or_F54` | `T-12 Analysis!N103` | `mapped` |  |
| **Legal Expenses** <br/> `opex_legal` | `UW Output!E_or_F55` | `T-12 Analysis!N104` | `mapped` |  |
| **Professional Services** <br/> `opex_professional_services` | `UW Output!E_or_F56` | `T-12 Analysis!N105` | `mapped` |  |
| **Bad Debt Expense (opex placement)** <br/> `opex_bad_debt_expense` | `UW Output!E_or_F57` | `T-12 Analysis!N106` | `proposed` | See `bad_debt_writeoffs_revenue` — single Analyzer source maps to two template rows. Choose one placement (likely 62 OR 106) and zero the other. |
| **Permits, Licenses & Dues** <br/> `opex_permits_licenses` | `UW Output!E_or_F58` | `T-12 Analysis!N107` | `mapped` |  |
| **Office, Admin & G&A** <br/> `opex_office_ga` | `UW Output!E_or_F59` | `T-12 Analysis!N108` | `mapped` |  |
| **Other / Miscellaneous** <br/> `opex_misc` | `UW Output!E_or_F60` | `T-12 Analysis!N109` | `mapped` |  |
| **Lease / Ground Lease** <br/> `opex_lease_ground` | `UW Output!E_or_F61` | `T-12 Analysis!N110` | `mapped` | UW Output row 61 currently resolves to 0 (known upstream deferral — see UW-OUTPUT-HANDOFF-CONTRACT.md §4 item 4). Template will show $0 until upstream lease formula is fixed. |
| **Total Non-Labor** <br/> `opex_nonlabor_total` | `UW Output!E_or_F62` | `T-12 Analysis!N111` | `mapped` |  |
| **Total OpEx (excl. mgmt)** <br/> `opex_total_excl_mgmt` | `UW Output!E_or_F63` | `—` | `mapped` | Template's TOTAL OPERATING EXPENSES (row 114) is inclusive of management fee — no direct row for opex-excl-mgmt. Could derive as N111 + N85. · v5: Closed in v5 — N115 has template formula `=N114-N113`. Writer overwrites with UW Output row 63 value (Total opex excl. mgmt) when present; falls back to template formula on empty Analyzer. |

#### mgmt_noi (6)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Management Fee** <br/> `mgmt_fee` | `UW Output!E_or_F64` | `T-12 Analysis!N113` | `mapped` |  |
| **Total Operating Expenses (incl. mgmt)** <br/> `opex_total_incl_mgmt` | `derived` | `T-12 Analysis!N114` | `proposed` | Writer sums Analyzer rows 63 + 64 to fill N114. |
| **EBITDARM** <br/> `ebitdarm` | `UW Output!E_or_F66` | `T-12 Analysis!N115` | `mapped` | v5: v5: row shifted from N115 (v4) → N116 due to new 'Total Operating Expenses (excl. mgmt)' row at N115. Template has fallback formula `=N69-N85-N111`; writer overwrites with UW Output row 66 value. |
| **EBITDAR** <br/> `ebitdar` | `UW Output!E_or_F67` | `T-12 Analysis!N116` | `mapped` | Template equates EBITDAR with NOI (label A116: 'EBITDAR (= NOI)'). Analyzer treats NOI as a header-only row (UW Output 65) and EBITDAR as a distinct line at row 67. Map E67/F67 directly to N116. · v5: v5: row shifted from N116 (v4) → N117 due to new row 115 insert. Writer populates from UW Output row 67. |
| **EBITDA** <br/> `ebitda` | `UW Output!E_or_F68` | `—` | `mapped` | Template has no EBITDA row in Layer 3 (only EBITDARM and EBITDAR/NOI). Either add an EBITDA row to template or drop from writer scope. · v5: Closed in v5 — N118 row added (label only, no formula). Writer populates from UW Output row 68. |
| **NOI (separator)** <br/> `noi_separator` | `UW Output!65` | `—` | `header_only` | UW Output row 65 is a visual band — see UW-OUTPUT-HANDOFF-CONTRACT.md §4 gotcha #1. Writer must skip. |

### RENT ROLL PATH · RENT ROLL INPUT → RENT ROLL ANALYSIS ROW 211+

#### rr_identity (7)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Unit #** <br/> `rr_unit_#` | `Rent Roll Input!A7:A606` | `Rent Roll Analysis!A211+` | `mapped` |  |
| **Room #** <br/> `rr_room_#` | `Rent Roll Input!B7:B606` | `Rent Roll Analysis!B211+` | `mapped` | Renamed but 1:1. |
| **Sq Ft** <br/> `rr_sq_ft` | `Rent Roll Input!C7:C606` | `Rent Roll Analysis!T211+` | `mapped` | Position shift A→T. |
| **Care Type** <br/> `rr_care_type` | `Rent Roll Input!D7:D606` | `Rent Roll Analysis!C211+` | `mapped` | Renamed. Values IL/AL/MC unchanged. |
| **Status** <br/> `rr_status` | `Rent Roll Input!E7:E606` | `Rent Roll Analysis!D211+` | `mapped` | Position shift E→D. |
| **Apt Type** <br/> `rr_apt_type` | `Rent Roll Input!F7:F606` | `Rent Roll Analysis!AC211+` | `mapped` | Position shift F→AC. Possible label-form difference (e.g. '1BR' vs '1 Bedroom') — normalize upstream or handle in template. |
| **Resident Name** <br/> `rr_resident_name` | `Rent Roll Input!R7:R606` | `Rent Roll Analysis!E211+` | `mapped` | Position shift R→E. |

#### rr_dates (4)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Move-in Date** <br/> `rr_move_in_date` | `Rent Roll Input!Q7:Q606` | `Rent Roll Analysis!F211+` | `mapped` | Position shift Q→F. |
| **Move-out Date** <br/> `rr_move_out_date` | `Rent Roll Input!W7:W606` | `Rent Roll Analysis!G211+` | `mapped` | Position shift W→G. Renamed. |
| **Concession End Date** <br/> `rr_concession_end_date` | `Rent Roll Input!J7:J606` | `Rent Roll Analysis!AE211+` | `mapped` | Position shift J→AE. |
| **Preleased Date** <br/> `rr_preleased_date` | `Rent Roll Input!AJ7:AJ606` | `—` | `mapped` | Lives at Rent Roll Input!AJ as of substrate v0.2.14 (relocated from AI). Section N on Rent Roll Recon matches on Status='Preleased', not on the date column directly — the AI → AJ relocation had zero formula impact upstream. UW Template v4 still has no per-row Preleased Date column; status remains gap_target until template v5. · v5: Closed in v5 — UW Template col AR. Writer pastes from Rent Roll Input col AJ (substrate v0.2.14 relocation). Date format mm/dd/yyyy. |

#### rr_rates (6)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Market Rate** <br/> `rr_market_rate` | `Rent Roll Input!G7:G606` | `Rent Roll Analysis!H211+` | `mapped` | Position shift G→H. |
| **Actual Rate** <br/> `rr_actual_rate` | `Rent Roll Input!H7:H606` | `Rent Roll Analysis!I211+` | `mapped` | Position shift H→I. Renamed. |
| **Market PSF** <br/> `rr_market_psf` | `Rent Roll Input!Z7:Z606` | `Rent Roll Analysis!AQ211+` | `mapped` | Position shift Z→AQ. · v5: shifted from AQ211+ to AT211+ per 2026-05-26 contract §16 (new AP/AQ/AR inserts pushed analyst-input cols right) |
| **Actual PSF** <br/> `rr_actual_psf` | `Rent Roll Input!AA7:AA606` | `Rent Roll Analysis!U211+` | `mapped` | Position shift AA→U. Renamed. |
| **Concession $** <br/> `rr_concession` | `Rent Roll Input!I7:I606` | `Rent Roll Analysis!AD211+` | `mapped` | Position shift I→AD. |
| **2nd Person Rent $** <br/> `rr_2nd_person_rent` | `Rent Roll Input!V7:V606` | `Rent Roll Analysis!AJ211+` | `mapped` | Position shift V→AJ. |

#### rr_ancillary (10)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Care Level $** <br/> `rr_care_level` | `Rent Roll Input!L7:L606` | `Rent Roll Analysis!AF211+` | `mapped` | Position shift L→AF. |
| **Care Level (tier label)** <br/> `rr_care_level_tier_label` | `Rent Roll Input!K7:K606` | `—` | `mapped` | Tier label (Basic / Level 2-7) has no template column. v5 wishlist: add a label col adjacent to AF Care Level $. · v5: Closed in v5 — UW Template col AP. Writer pastes from Rent Roll Input col K (Care Level tier label, e.g. Basic / Level 2-7). |
| **Med Mgmt $** <br/> `rr_med_mgmt` | `Rent Roll Input!M7:M606` | `Rent Roll Analysis!AG211+` | `mapped` |  |
| **Pharmacy $** <br/> `rr_pharmacy` | `Rent Roll Input!N7:N606` | `Rent Roll Analysis!AH211+` | `mapped` |  |
| **Other LOC $** <br/> `rr_other_loc` | `Rent Roll Input!O7:O606` | `Rent Roll Analysis!AI211+` | `mapped` |  |
| **Meal Plan $** <br/> `rr_meal_plan` | `Rent Roll Input!AC7:AC606` | `Rent Roll Analysis!AK211+` | `mapped` | Position shift AC→AK. |
| **Scooter Fee $** <br/> `rr_scooter_fee` | `Rent Roll Input!AD7:AD606` | `Rent Roll Analysis!AL211+` | `mapped` | Renamed. |
| **Housekeeping $** <br/> `rr_housekeeping` | `Rent Roll Input!AE7:AE606` | `Rent Roll Analysis!AM211+` | `mapped` |  |
| **Laundry $** <br/> `rr_laundry` | `Rent Roll Input!AF7:AF606` | `Rent Roll Analysis!AN211+` | `mapped` |  |
| **Pet $** <br/> `rr_pet` | `Rent Roll Input!AG7:AG606` | `Rent Roll Analysis!AO211+` | `mapped` |  |

#### rr_subtotals (3)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Total LOC $** <br/> `rr_total_loc` | `Rent Roll Input!T7:T606` | `Rent Roll Analysis!J211+` | `mapped` | Formula-derived in both. Writer should still paste-value the Analyzer's computed value; template formula re-derives but tie-out check needs the source figure. |
| **Total Monthly Rev** <br/> `rr_total_monthly_rev` | `Rent Roll Input!U7:U606` | `Rent Roll Analysis!K211+` | `mapped` | Formula-derived in both. Both = Actual + LOC only (no ancillary). |
| **Total Ancillary $** <br/> `rr_total_ancillary` | `Rent Roll Input!AH7:AH606` | `—` | `derived` | Total Ancillary $ has no template column. v5 wishlist: add formula col `=AK+AL+AM+AN+AO` per row — no upstream change needed. · v5: v5 added col AQ as a TEMPLATE-OWNED formula `=SUM(AK:AO)`. Writer MUST NOT paste Analyzer col AH values here — template re-derives from cols AK-AO which are writer-populated. |

#### rr_other (5)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **Payer Type** <br/> `rr_payer_type` | `Rent Roll Input!P7:P606` | `Rent Roll Analysis!R211+` | `mapped` | Position shift P→R. |
| **Balance (AR)** <br/> `rr_balance_ar` | `Rent Roll Input!X7:X606` | `Rent Roll Analysis!L211+` | `mapped` | Position shift X→L. Renamed. |
| **Notes** <br/> `rr_notes` | `Rent Roll Input!Y7:Y606` | `Rent Roll Analysis!S211+` | `mapped` | Position shift Y→S. |
| **ACH** <br/> `rr_ach` | `Rent Roll Input!AB7:AB606` | `Rent Roll Analysis!AP211+` | `mapped` | Position shift AB→AP. · v5: shifted from AP211+ to AS211+ per 2026-05-26 contract §16 (new AP/AQ/AR inserts pushed analyst-input cols right) |
| **Deposit** <br/> `rr_deposit` | `Rent Roll Input!AI7:AI606` | `Rent Roll Analysis!M211+` | `substrate_ready_parser_pending` | Substrate slot ready at Rent Roll Input!AI (v0.2.14). Parser support deferred until a source rent roll with a Deposit column lands as a fixture. Once parsed, RR writer at COL_AI_INDEX=35 will populate. |

### AR PATH · AR & COLLECTIONS → RENT ROLL ANALYSIS COLS N–Q

#### ar_aging (4)

| Concept | Source | Target (`v4`) | Status | Notes |
|---|---|---|---|---|
| **AR Aging — 0–30 Days** <br/> `ar_aging_0_30` | `—  (not in Analyzer)` | `Rent Roll Analysis!N211+` | `gap_source` | UW Template expects per-resident aging buckets. Analyzer's AR & Collections (substrate v0.2.10+) aggregates by payer, not by resident — row-level join needed upstream before this can move off gap_source. |
| **AR Aging — 31–60 Days** <br/> `ar_aging_31_60` | `—  (not in Analyzer)` | `Rent Roll Analysis!O211+` | `gap_source` | UW Template expects per-resident aging buckets. Analyzer's AR & Collections (substrate v0.2.10+) aggregates by payer, not by resident — row-level join needed upstream before this can move off gap_source. |
| **AR Aging — 61–90 Days** <br/> `ar_aging_61_90` | `—  (not in Analyzer)` | `Rent Roll Analysis!P211+` | `gap_source` | UW Template expects per-resident aging buckets. Analyzer's AR & Collections (substrate v0.2.10+) aggregates by payer, not by resident — row-level join needed upstream before this can move off gap_source. |
| **AR Aging — 90+ Days** <br/> `ar_aging_90_plus` | `—  (not in Analyzer)` | `Rent Roll Analysis!Q211+` | `gap_source` | UW Template expects per-resident aging buckets. Analyzer's AR & Collections (substrate v0.2.10+) aggregates by payer, not by resident — row-level join needed upstream before this can move off gap_source. |

## Unmapped template intake (rows the writer does NOT populate)

- **`Prop Info`** (manual) — [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 44, 45, 46, 47]: Property details (location, year built, sq ft, parking), market data, competitive rents, utility metering, value-add thesis. Per template A2 note, market fields can auto-populate from a separate 'AI Market Research tool'. Not part of this UW pipeline.
- **`T-12 Analysis`** (derived) — rows 1-54: Layer 3 (rows 55+) is the paste target. Rows 1-54 are diagnostic outputs computed from Layer 3 — writer must not overwrite. Rows 4-16 are reconciliation/trend dashboards; rows 18-27 are economic-vs-physical occupancy; rows 29-35 are bad-debt layered analysis; rows 37-50 are RE tax / P&C accrual checks.
- **`T-12 Analysis`** (gap_source) — B-M: Template Layer 3 expects 12 months of bucket-level data; UW Export only exposes annual totals via col N target. Future enhancement: widen UW Export to expose Monthly Trending data, then writer fills B-M; for v0.1 leave B-M blank.
- **`T-12 Analysis`** (manual) — rows 117-177: Layer 1 (raw T-12 paste, rows 119-172) is the operator's source GL — analyst pastes operator's T-12 directly here, not from Analyzer. Section J (173-177) computes raw totals from Layer 1 for tie-out.
- **`Rent Roll Analysis`** (derived) — rows 1-209 (diagnostic sections A-R): Header diagnostic sections (Health Check, Census, Status Taxonomy, GPR Reconciliation, LOS Cohort, Days Vacant, Delinquency, Payer Mix, Rate-by-Care, Charge Variance, Deposit Coverage, Move-in Seasonality, Pre-Admission Pipeline, Wing Vacancy). All formula-derived from the row 211+ paste — writer must not overwrite.
- **`Rent Roll Analysis`** (paste_anchor) — row 211+: 34-col paste from Analyzer Rent Roll Input rows 7-606. Column positions DO NOT match 1:1 — see rent_roll path concepts. Formula-derived cols on the template side (V, X, Y, Z, AA, AB, AS) must NOT be overwritten by paste.
- **`Rent Roll Analysis`** (manual) — cols AR, AS: Conc Source (AR) and Effective Conc $ (AS) are analyst-entered per-row. Writer must preserve any existing values on re-paste.
- **`Rent Roll Analysis`** (derived) — cols V, X, Y, Z, AA, AB: $/SqFt/Yr (V), Care|UnitType (X), Care|Unit (Y), _key (Z), Mkt-Actual $ (AA), Mkt-Actual % (AB) — formula columns. Do not overwrite.

## Open questions

- Bad Debt placement — revenue contra (template row 62) vs opex (template row 106). Need user decision before writer ships.
- 2nd Person Revenue — extend UW Output to expose, or have writer pull directly from Rent Roll Input!V?
- Monthly grid — accept blank B-M in v0.1, or widen UW Export contract first?
- Date header at Rent Roll Analysis!A5 — does it expect RR period date in B5 or D5? Confirm format (yyyy-mm-dd vs Excel date).
- Rent Roll Analysis header rows 1-209 — the contract specifies paste anchor at row 211 (header at 210). Rows 1-209 contain diagnostic sections that read from the pasted block via formulas. Writer must not touch rows 1-210. (Confirms the existing 'derived' framing for the upper section.)
- AR aging row-level routing — UW Template cols N-Q expect per-resident aging buckets, but the Analyzer's `AR & Collections` tab aggregates AR by payer, not by resident-bed. Routing aging $ to specific rent-roll rows needs an upstream substrate change (resident-key join into AR & Collections) before these concepts move off `gap_source`.
- Cover substrate version stamp — deferred to v5.1 per the 2026-05-26 release handoff. Concept `substrate_version` stays gap_target for now.
- Rent Roll Analysis tab-header Period Date metadata cell — still pending in v5.1. Per-row Period Date (Analyzer col S) is not pasted; concept stays gap_target.
