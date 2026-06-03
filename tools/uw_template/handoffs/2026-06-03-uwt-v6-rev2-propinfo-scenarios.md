# Handoff — v6 rev2 absorbed (Other Care) + Prop Info & Scenarios col-B mapping

- **Date:** 2026-06-03
- **Template version:** v6 (operator rev2 — adds Other Care care-type) → now canonical `assets/ALF_UW_Template_v6.xlsx`
- **Registry version:** 0.5.0 → **0.6.0**
- **UWT version:** 0.8.1 → **0.9.0**
- **Status:** **Verified** — mapping + fills implemented and tested end-to-end on Homestead RR v2 + March 2026 T12 (55 new cells populate). Section-D bug fixed in both canonical asset + operator's local copy. All 36 tests green.

## Trigger

Operator goal: *"I want the raw datas to populate into this ALF UW Template … Fill
in the Prop Info tab property details from RR. Scenarios tab T-12 Actuals (col B)
must be filled or linked to T-12 Analysis tab and rent roll. Complete the mapping
only."* Supplied: a `Deals/…/ALF_UW_Template_v6.xlsx`, Homestead RR v2, March 2026 T12.

## What was found

The operator's Deals-folder v6 was a **newer revision** than the committed
`assets/ALF_UW_Template_v6.xlsx` (registry v0.5.0's base). It added full **Other
Care (4th care type)** support across Prop Info / Scenarios / T-12 Analysis +
IFERROR hardening, **shifting ~70 v6 targets**. Mapping new tabs on the stale base
would have written into wrong cells (EGI→N77 = blank row; occupied IL→B20 = Total SUM).

Operator decision (AskUserQuestion): Deals file is **canonical v6**; col-B fill via
**writer-pasted values** (no template change); income **derived from RR+T-12**;
orphan expense lines **folded into Other/Misc**.

## What shipped (registry-only — `_absorb_v6_rev2_propinfo_scenarios.py`)

1. **Asset replaced** with the operator's Deals file.
2. **82 v6 targets re-synced** by validated non-uniform remap (income +1/+2/+3 from
   inserted Other-Care base/LOC + new actual-vacancy line; Prop Info +1 from Other-Care
   Units row). 0 label mismatches; every target lands on its correct label post-absorb.
3. **3 new T-12 Analysis income concepts**: `base_rent_other` N61, `loc_other` N66,
   `vacancy_credit_loss_actual` N77 (status `proposed`).
4. **3 Prop Info auto-fill concepts**: `rr_unit_count` B6, `rr_gross_sqft` B11,
   `asset_class` B13.
5. **52 Scenarios col-B concepts** (`scenarios` path): 38 expense mirrors (1:1 to
   T-12 Analysis; Auto Expense N117 + Lease N128 folded into Other/Misc B121) +
   14 income derived (beds/rate/vacancy/fees reverse-engineering).

195 concepts total. Artifacts regenerated.

## Prop Info — fillable vs manual (operator's "identify which can be filled")

| Auto-fillable from RR | Manual (not in RR/T12) |
| --- | --- |
| B4 Property Name (filename), B6 #Units, B11 Gross Sq Ft, B13 Asset Class, B15-B18 licensed beds, B21-B23 occupied beds | B5 Address, B7 Buildings, B8 Stories, B9 Year Built, B10 Lot Size, B12 Parking, B14 License Type, D13 Other-Care name, B26-B43 Market Data (AI tool), B45-B53 Utilities/Notes |

## Fills implemented + verified (same session)

`uw_output_model.compute_uw_output_values` now emits all 58 new keys; the writer's
existing computed-fallback path writes them (no writer change for the fills). Verified
on the real Homestead files: **55 cells populate** (3 Prop Info + 14 income + 38 expense,
minus Other-Care lines that are 0). Care Fees % ties LOC exactly; expenses mirror T-12
to the penny; Scenarios subtotal formulas preserved.

## Two bugs fixed in the operator's rev2 file

1. **Section-D** (`T-12 Analysis!B22/B23/B24`) pointed at `N58/N64/N71` (income line
   items) instead of GPR/Net Rent/EGI. Operator-approved fix → `N83/N86/N80`
   (`_fix_v6_rev2_section_d_refs.py`, metadata-preserving). Applied to **both** the
   canonical asset and the operator's local `Deals/…/ALF Templates/` copy.
2. **Writer `_T12_LAYOUT["v6"]`** still used prior-v6 rows (EBITDAR N132, Section I 138)
   → updated to rev2 (EBITDAR N135, Section I 141, Section J 194–196). Without this the
   finalize pass authored totals into wrong rows.

## No template change for the fills

Per the writer-paste mechanism, the fills alter **no template formula** — values land
in existing blue input cells. The only template edit was the operator-approved 3-cell
Section-D bug fix above.
