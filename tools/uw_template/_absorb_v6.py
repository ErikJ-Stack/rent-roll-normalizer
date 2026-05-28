"""
Absorb UW Template v6 into the registry (0.4.2 → 0.5.0).

v6 = major T-12 Analysis income restructure (per the 2026-05-28 release
handoff). The GPR→Net-Rent market-projection waterfall is replaced with a
full actual-T12 income build (Base Rent IL/AL/MC + LOC IL/AL/MC + ancillaries
+ contras → EGI at N77); the old GPR waterfall is demoted to a DIAGNOSTIC
sub-section (N80-N83); a new Auto Expense row (N114) is added inside the
Non-Labor SUM, closing the $6,061 standardized-vs-as-reported NOI gap.

This script:
  1. registry_version 0.4.2 → 0.5.0
  2. adds templates.v6 block (income_model="actual_t12")
  3. adds targets.v6 to every existing concept (T-12 Analysis ones get new
     rows per the VERIFIED row map below; Rent Roll Analysis / Prop Info /
     Cover concepts inherit their v5 target unchanged)
  4. adds 14 new concepts (12 line items + 2 derived subtotals)
  5. flips second_person_revenue gap_source → mapped (now fed by the v0.2.15
     Description_Map re-map)

Row map VERIFIED 2026-05-28 against assets/ALF_UW_Template_v6.xlsx cell-by-cell
(not trusted from the handoff doc alone).

Default template_version stays v5 (the v6 binary is the pre-Excel-resave
version missing metadata.xml; flip happens once the operator re-drops the
46-part Excel-resaved v6). Idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools" / "uw_template" / "registry.json"

# ── Explicit v6 row map for existing T-12 Analysis concepts (key → row) ──────
# Income block (restructured — not a simple shift):
V6_ROW = {
    "gpr_base": 80,                  # → DIAGNOSTIC GPR
    "loss_to_lease": 81,             # → DIAGNOSTIC
    "physical_vacancy_loss": 82,     # → DIAGNOSTIC
    "concessions_specials": 75,      # contra
    "bad_debt_writeoffs_revenue": 76,  # contra
    "base_rent_normalized": 61,      # → Total Base Rent subtotal
    "loc_revenue": 65,               # → Total LOC subtotal
    "community_movein_fees": 67,
    "respite_care": 68,
    "second_person_revenue": 66,     # + status flip below
    "other_community_revenue": 74,
    "egi": 77,
    # Labor block (rows 71-85 shift +14):
    "labor_care_staff": 85, "labor_wellness": 86, "labor_agency": 87,
    "labor_activities": 88, "labor_dining": 89, "labor_maint_hk": 90,
    "labor_admin": 91, "labor_bonus": 92, "labor_overtime": 93,
    "labor_pto": 94, "labor_payroll_taxes": 95, "labor_benefits": 96,
    "labor_workers_comp": 97, "labor_401k": 98, "labor_total": 99,
    # Non-labor block, +14 through Auto Insurance (N99→N113):
    "opex_food_cost": 101, "opex_dining_supplies": 102, "opex_nursing_supplies": 103,
    "opex_recreation_supplies": 104, "opex_rm_fixed": 105, "opex_rm_variable": 106,
    "opex_hk_laundry": 107, "opex_marketing": 108, "opex_referral_fees": 109,
    "opex_utilities": 110, "opex_telephone_it": 111, "opex_pc_insurance": 112,
    "opex_auto_insurance": 113,
    # Non-labor, +15 after the new Auto Expense row at 114:
    "opex_fire_security": 115, "opex_pest": 116, "opex_re_taxes": 117,
    "opex_personal_prop_taxes": 118, "opex_legal": 119, "opex_professional_services": 120,
    "opex_bad_debt_expense": 121, "opex_permits_licenses": 122, "opex_office_ga": 123,
    "opex_misc": 124, "opex_lease_ground": 125, "opex_nonlabor_total": 126,
    # NOI block (+15):
    "mgmt_fee": 128, "opex_total_incl_mgmt": 129, "opex_total_excl_mgmt": 130,
    "ebitdarm": 131, "ebitdar": 132, "ebitda": 133,
}

# t12_raw_month_1..12 target cells (Layer 1 raw month-header row moved 122 → 137).
# In v5 they sat at C122..N122 (col by month). Map to C137..N137.
_MONTH_COLS = ["C","D","E","F","G","H","I","J","K","L","M","N"]
for i, col in enumerate(_MONTH_COLS, start=1):
    V6_ROW_RAW = None  # handled inline below

# ── 14 new v6 concepts ───────────────────────────────────────────────────────
# 12 line items (engine computes from T12 label sums via compute_uw_output_values)
# + 2 derived subtotals (template SUM formulas — writer skips).
NEW_CONCEPTS = [
    # (key, label, category, t12_label_source, v6_row, status)
    ("base_rent_il", "Base Rent — IL", "revenue", "Base rent — IL", 58, "mapped"),
    ("base_rent_al", "Base Rent — AL", "revenue", "Base rent — AL", 59, "mapped"),
    ("base_rent_mc", "Base Rent — MC", "revenue", "Base rent — MC", 60, "mapped"),
    ("total_base_rent", "Total Base Rent", "revenue", None, 61, "derived"),
    ("loc_il", "LOC / Care Services — IL", "revenue", "LOC revenue — IL", 62, "mapped"),
    ("loc_al", "LOC / Care Services — AL", "revenue", "LOC revenue — AL", 63, "mapped"),
    ("loc_mc", "LOC / Care Services — MC", "revenue", "LOC revenue — MC", 64, "mapped"),
    ("total_loc", "Total LOC / Care Services", "revenue", None, 65, "derived"),
    ("rev_meal_income", "Meal Income", "revenue", "Meal Income", 69, "mapped"),
    ("rev_housekeeping_income", "Housekeeping Income", "revenue", "Housekeeping Income", 70, "mapped"),
    ("rev_laundry_income", "Laundry Income", "revenue", "Laundry Income", 71, "mapped"),
    ("rev_scooter_fee", "Scooter Fee Revenue", "revenue", "Scooter Fee Revenue", 72, "mapped"),
    ("rev_transfer_fee", "Transfer Fee Revenue", "revenue", "Transfer Fee Revenue", 73, "mapped"),
    ("opex_auto_expense", "Auto Expense", "nonlabor", "Auto Expense", 114, "mapped"),
]


def absorb():
    r = json.loads(REGISTRY.read_text())
    ops = []

    if r.get("registry_version") != "0.5.0":
        r["registry_version"] = "0.5.0"
        r["generated_phase"] = (
            "Track 4 v6 — T-12 Analysis income restructure to actual-T12 categories. "
            "templates.v6 (income_model=actual_t12); by-care Base Rent + LOC, 5 ancillary "
            "income lines, Auto Expense; GPR waterfall demoted to diagnostic. Default "
            "template stays v5 until the Excel-resaved v6 binary lands."
        )
        ops.append("registry_version → 0.5.0")

    # 1. templates.v6 block (copy v5, adjust)
    if "v6" not in r["templates"]:
        v6 = dict(r["templates"]["v5"])
        v6["file"] = "assets/ALF_UW_Template_v6.xlsx"
        v6["released"] = "2026-05-28"
        v6["supersedes"] = "v5.1"
        v6["income_model"] = "actual_t12"  # vs v5 implicit gpr_waterfall
        v6["monthly_header_strategy"] = (
            "Formula-driven from on-sheet Layer 1 raw row 137 (B56 SHOULD be =C137..=N137). "
            "KNOWN v6 BUG: B56:M56 still reference row 122 (pre-restructure) — operator "
            "repointing pass missed this chain (openpyxl quirk #4). Cosmetic header-only; "
            "fix in v6.1."
        )
        v6["sheet_count"] = 16
        v6["income_block_note"] = (
            "Layer 3 INCOME rebuilt to actual-T12 categories (rows 58-77); GPR waterfall "
            "demoted to DIAGNOSTIC sub-section (rows 79-83, does NOT feed EGI). EGI N77 = "
            "N61+N65+SUM(N66:N76). Auto Expense new at N114 inside TOTAL NON-LABOR (N126)."
        )
        v6["binary_caveat"] = (
            "assets/ALF_UW_Template_v6.xlsx as dropped is the pre-Excel-resave openpyxl "
            "version (39 zip parts, missing xl/metadata.xml + xl/webextensions). Operator "
            "must open in Excel + save to restore metadata.xml before populated outputs "
            "have working Section R/S dynamic-array spills. Default stays v5 until then."
        )
        r["templates"]["v6"] = v6
        ops.append("added templates.v6 block")

    by_key = {c["key"]: c for c in r["concepts"]}

    # 2. Existing concepts: add targets.v6
    for c in r["concepts"]:
        key = c["key"]
        tv5 = (c.get("targets") or {}).get("v5")
        if not tv5:
            continue
        if "v6" in c["targets"]:
            continue  # idempotent
        sheet = tv5.get("sheet")
        if sheet == "T-12 Analysis":
            if key in V6_ROW:
                row = V6_ROW[key]
                c["targets"]["v6"] = {
                    "sheet": "T-12 Analysis",
                    "address": f"N{row}",
                    "label_at": f"A{row}",
                }
                ops.append(f"{key}: targets.v6 N{row}")
            elif key.startswith("t12_raw_month_"):
                # month-header cells move from row 122 → 137 (col unchanged)
                old_addr = tv5["address"]
                col = "".join(ch for ch in old_addr if ch.isalpha())
                c["targets"]["v6"] = {
                    "sheet": "T-12 Analysis",
                    "address": f"{col}137",
                }
                ops.append(f"{key}: targets.v6 {col}137")
            else:
                # any unmapped T-12 Analysis concept — inherit v5 (shouldn't happen)
                c["targets"]["v6"] = dict(tv5)
                ops.append(f"{key}: targets.v6 INHERIT v5 (unmapped — review)")
        else:
            # Rent Roll Analysis / Prop Info / Cover — v6 didn't move these
            c["targets"]["v6"] = dict(tv5)

    # 3. second_person_revenue: gap_source → mapped (fed by v0.2.15 re-map)
    spr = by_key.get("second_person_revenue")
    if spr and spr.get("status") == "gap_source":
        spr["status"] = "mapped"
        spr["notes"] = (
            (spr.get("notes") or "") +
            " · v6: re-mapped Description_Map labels (Second Persons Revenue | care + "
            "Second Person Fee → '2nd Person Revenue' label, substrate v0.2.15) now feed "
            "this; target N66. EGI unchanged (pure reallocation out of Base Rent)."
        ).strip()
        ops.append("second_person_revenue: gap_source → mapped")

    # 4. New concepts
    existing_keys = set(by_key)
    for key, label, category, t12_label, row, status in NEW_CONCEPTS:
        if key in existing_keys:
            continue
        concept = {
            "key": key,
            "label": label,
            "category": category,
            "path": "t12",
            "source": (
                {"system": "derived",
                 "formula": "Template SUM subtotal — writer skips; template self-derives."}
                if status == "derived" else
                {"system": "uw_output_derived",
                 "t12_label": t12_label,
                 "note": "Computed by compute_uw_output_values from the T12 Description_Map "
                         "label sum; passed to the writer via computed_values=."}
            ),
            "targets": {
                "v6": {"sheet": "T-12 Analysis", "address": f"N{row}", "label_at": f"A{row}"}
            },
            "status": status,
            "notes": f"New in v6 (income restructure). T-12 Analysis N{row}.",
        }
        r["concepts"].append(concept)
        ops.append(f"NEW concept {key} → N{row} ({status})")

    REGISTRY.write_text(json.dumps(r, indent=2) + "\n")

    print(f"Applied {len(ops)} ops:")
    for op in ops:
        print(f"  ✓ {op}")
    from collections import Counter
    cnt = Counter(c["status"] for c in r["concepts"])
    print(f"\nregistry_version: {r['registry_version']} | concepts: {len(r['concepts'])}")
    print(f"status rollup: {dict(sorted(cnt.items()))}")


if __name__ == "__main__":
    absorb()
