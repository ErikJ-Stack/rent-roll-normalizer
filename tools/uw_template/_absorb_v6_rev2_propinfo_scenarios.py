"""
Absorb the operator's NEW v6 template revision (Deals-folder ALF_UW_Template_v6.xlsx)
and add the Prop Info + Scenarios col-B mappings.

Context (2026-06-03, Track 4 mapping task):
  The operator authored a newer v6 in Excel adding full "Other Care" (4th care type)
  support across Prop Info / Scenarios / T-12 Analysis, plus IFERROR hardening.
  This shifted ~70 registry v6 targets relative to the committed asset:
    - T-12 Analysis income section +1/+2/+3 (non-uniform; Other Care base/LOC rows +
      a new "Less: Vacancy/Credit Loss (actual)" line were inserted).
    - Prop Info: an "Other Care Units" row (19) was inserted -> rows >=19 shift +1.

What this script does (registry-only; idempotent on re-run):
  PHASE A  Re-sync every existing v6 T-12 Analysis + Prop Info target to the new rows
           (validated remap, 0 label mismatches).
  PHASE B  Add new income concepts the restructure introduced (Other Care base rent/LOC,
           Vacancy/Credit Loss actual) -- status 'proposed' (no Other Care in current deals).
  PHASE C  Add Prop Info auto-fillable fields: #Units (B6), Gross Sq Ft (B11), Asset Class (B13).
  PHASE D  Add Scenarios col-B 'Actuals (T-12)' concepts:
             - EXPENSE block: 1:1 mirror of T-12 Analysis (Auto Expense + Lease folded into Other/Misc).
             - INCOME block: derived (beds/rate/vacancy/fees) from RR + T-12 actuals.

NOTE: This is the MAPPING. The writer/evaluator changes that consume these new sources
(systems: 'mirror', 'derived_scenario', 'rr_aggregate') are the documented follow-on.
"""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tools/uw_template/registry.json"
ASSET = ROOT / "assets/ALF_UW_Template_v6.xlsx"
USER_FILE = Path("/Users/erikjavellana/Library/CloudStorage/OneDrive-(na)/"
                 "Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v6.xlsx")

NEW_REGISTRY_VERSION = "0.6.0"


def remap_t12(r: int) -> int:
    """Old committed-asset T-12 Analysis row -> new operator-file row. Validated 0-mismatch."""
    if r <= 60:
        return r
    if r == 61:
        return 62
    if 62 <= r <= 64:
        return r + 1
    if 65 <= r <= 74:
        return r + 2
    return r + 3


def remap_propinfo(r: int) -> int:
    """Prop Info: 'Other Care Units' row inserted at 19 -> rows >=19 shift +1."""
    return r + 1 if r >= 19 else r


def col_of(addr: str) -> str:
    return "".join(ch for ch in addr if ch.isalpha())


def row_of(addr: str) -> int:
    return int("".join(ch for ch in addr if ch.isdigit()))


def main():
    reg = json.loads(REG.read_text())
    concepts = reg["concepts"]
    by_key = {c["key"]: c for c in concepts}

    # ---------------------------------------------------------------- PHASE A
    resynced = 0
    for c in concepts:
        t = c.get("targets", {}).get("v6")
        if not isinstance(t, dict):
            continue
        sheet = t.get("sheet")
        if sheet == "T-12 Analysis" and t.get("address"):
            col, r = col_of(t["address"]), row_of(t["address"])
            nr = remap_t12(r)
            if nr != r:
                t["address"] = f"{col}{nr}"
                if t.get("label_at"):
                    lc, lr = col_of(t["label_at"]), row_of(t["label_at"])
                    t["label_at"] = f"{lc}{remap_t12(lr)}"
                resynced += 1
        elif sheet == "Prop Info" and t.get("address"):
            col, r = col_of(t["address"]), row_of(t["address"])
            nr = remap_propinfo(r)
            if nr != r:
                t["address"] = f"{col}{nr}"
                if t.get("label_at"):
                    lc, lr = col_of(t["label_at"]), row_of(t["label_at"])
                    t["label_at"] = f"{lc}{remap_propinfo(lr)}"
                resynced += 1
    print(f"PHASE A: re-synced {resynced} v6 targets")

    # ---------------------------------------------------------------- PHASE B
    # New T-12 Analysis income lines the restructure introduced.
    new_t12_income = [
        ("base_rent_other", "Base Rent — Other Care", "income", "N61",
         {"system": "uw_output", "sheet": "UW Output", "note": "Other-care base rent; 0 for IL/AL/MC-only deals"}),
        ("loc_other", "LOC / Care Services — Other Care", "income", "N66",
         {"system": "uw_output", "sheet": "UW Output", "note": "Other-care LOC; 0 for IL/AL/MC-only deals"}),
        ("vacancy_credit_loss_actual", "Less: Vacancy / Credit Loss (actual)", "income", "N77",
         {"system": "uw_output", "sheet": "UW Output", "note": "T-12 actual vacancy/credit loss contra (new income line)"}),
    ]
    added_b = 0
    for key, label, cat, addr, src in new_t12_income:
        if key in by_key:
            continue
        concepts.append({
            "key": key, "label": label, "category": cat, "source": src,
            "targets": {"v4": None, "v5": None,
                        "v6": {"sheet": "T-12 Analysis", "address": addr, "label_at": "A" + addr[1:]}},
            "status": "proposed",
            "notes": "Added by operator's v6 rev2 income restructure (Other Care / actual-vacancy). "
                     "Writer/evaluator support is the follow-on.",
            "path": "t12",
        })
        added_b += 1
    print(f"PHASE B: added {added_b} new T-12 Analysis income concepts")

    # ---------------------------------------------------------------- PHASE C
    propinfo_new = [
        ("rr_unit_count", "# Units (physical rooms)", "capacity", "B6",
         {"system": "rr_aggregate", "formula": "COUNT of Rent Roll Input unit rows"},
         "Auto-fill from RR unit-row count."),
        ("rr_gross_sqft", "Gross Sq Ft", "capacity", "B11",
         {"system": "rr_aggregate", "formula": "SUM of Rent Roll Input unit Sq Ft column"},
         "Auto-fill from RR per-unit square footage sum."),
        ("asset_class", "Asset Class (IL/AL/MC/Other/Mix)", "capacity", "B13",
         {"system": "derived", "formula": "Label from care types present: single type -> that type, else 'Mix (IL/AL/MC)'"},
         "Derived from care types present in the RR."),
    ]
    added_c = 0
    for key, label, cat, addr, src, note in propinfo_new:
        if key in by_key:
            continue
        concepts.append({
            "key": key, "label": label, "category": cat, "source": src,
            "targets": {"v4": None, "v5": None,
                        "v6": {"sheet": "Prop Info", "address": addr, "label_at": "A" + addr[1:]}},
            "status": "proposed", "notes": note, "path": "rent_roll",
        })
        added_c += 1
    print(f"PHASE C: added {added_c} Prop Info auto-fill concepts")

    # ---------------------------------------------------------------- PHASE D
    # Scenarios col-B EXPENSE mirrors: (scenarios_addr, T-12 Analysis source addr, label)
    exp_mirror = [
        ("B81", ["N88"], "Care staff labor"),
        ("B82", ["N89"], "Wellness / care coordinators"),
        ("B83", ["N90"], "Contract / agency labor"),
        ("B84", ["N91"], "Activities labor"),
        ("B85", ["N92"], "Dining / food service labor"),
        ("B86", ["N93"], "Maintenance & housekeeping labor"),
        ("B87", ["N94"], "Administrative labor"),
        ("B88", ["N95"], "Bonus wages"),
        ("B91", ["N96"], "Overtime wages"),
        ("B92", ["N97"], "PTO wages"),
        ("B93", ["N98"], "Payroll taxes"),
        ("B94", ["N99"], "Employee benefits"),
        ("B95", ["N100"], "Workers' comp insurance"),
        ("B96", ["N101"], "Employee 401(k)"),
        ("B99", ["N104"], "Food cost"),
        ("B100", ["N105"], "Dining & kitchen supplies"),
        ("B101", ["N106"], "Nursing & care supplies"),
        ("B102", ["N107"], "Recreation & activity supplies"),
        ("B103", ["N108"], "R&M — fixed"),
        ("B104", ["N109"], "R&M — variable"),
        ("B105", ["N110"], "Housekeeping & laundry supplies"),
        ("B106", ["N111"], "Sales, advertising & marketing"),
        ("B107", ["N112"], "Referral fees"),
        ("B108", ["N113"], "Utilities"),
        ("B109", ["N114"], "Telephone / IT / technology"),
        ("B110", ["N115"], "P&C insurance"),
        ("B111", ["N116"], "Auto insurance"),
        ("B112", ["N118"], "Fire / security monitoring"),
        ("B113", ["N119"], "Pest elimination"),
        ("B114", ["N120"], "Real estate taxes"),
        ("B115", ["N121"], "Personal property taxes"),
        ("B116", ["N122"], "Legal expenses"),
        ("B117", ["N123"], "Professional services"),
        ("B118", ["N124"], "Bad debt expense"),
        ("B119", ["N125"], "Permits, licenses & dues"),
        ("B120", ["N126"], "Office, admin & G&A"),
        ("B121", ["N127", "N117", "N128"], "Other / miscellaneous (+ Auto Expense + Lease/Ground Lease)"),
        ("B123", ["N131"], "Management Fee"),
    ]
    added_d = 0
    for addr, srcs, label in exp_mirror:
        key = f"scn_exp_{addr.lower()}"
        if key in by_key:
            continue
        concepts.append({
            "key": key, "label": f"Scenarios Actuals — {label}", "category": "scenario_expense",
            "source": {"system": "mirror", "mirror_of": [f"T-12 Analysis!{s}" for s in srcs],
                       "note": "Writer pastes the computed T-12 Analysis value(s) (summed) into this blue input cell."},
            "targets": {"v4": None, "v5": None,
                        "v6": {"sheet": "Scenarios", "address": addr, "label_at": "A" + addr[1:]}},
            "status": "proposed",
            "notes": "Scenarios col-B Actuals; writer-paste value, no template change. Mirrors T-12 Analysis.",
            "path": "scenarios",
        })
        added_d += 1

    # Scenarios col-B INCOME derived: (addr, key_suffix, label, source-formula)
    inc_derived = [
        ("B39", "beds_il", "Licensed Beds — IL", "= licensed_beds_il"),
        ("B40", "rate_il", "Avg Monthly Rate — IL", "= base_rent_il_annual / occupied_beds_il / 12"),
        ("B42", "vacancy_il", "Vacancy % — IL", "= 1 - occupied_beds_il / licensed_beds_il"),
        ("B45", "beds_al", "Licensed Beds — AL", "= licensed_beds_al"),
        ("B46", "rate_al", "Avg Monthly Rate — AL", "= base_rent_al_annual / occupied_beds_al / 12"),
        ("B48", "vacancy_al", "Vacancy % — AL", "= 1 - occupied_beds_al / licensed_beds_al"),
        ("B51", "beds_mc", "Licensed Beds — MC", "= licensed_beds_mc"),
        ("B52", "rate_mc", "Avg Monthly Rate — MC", "= base_rent_mc_annual / occupied_beds_mc / 12"),
        ("B54", "vacancy_mc", "Vacancy % — MC", "= 1 - occupied_beds_mc / licensed_beds_mc"),
        ("B68", "loss_to_lease_pct", "Loss to Lease %", "= 0 (T-12 actual has no separate LtL inside EGI)"),
        ("B70", "concessions_baddebt_pct", "Concessions / Bad Debt %",
         "= (concessions_specials + bad_debt_writeoffs_revenue) / total_GPR"),
        ("B72", "care_fees_pct", "Care Services Fees %", "= total_loc / total_GPR"),
        ("B74", "second_person_rev", "2nd Person Revenue", "= T-12 Analysis 2nd Person Revenue (N68)"),
        ("B75", "other_income", "Other Income",
         "= SUM(community/move-in, respite, meal, HK, laundry, scooter, transfer, other community) N69:N76"),
    ]
    for addr, suf, label, formula in inc_derived:
        key = f"scn_inc_{suf}"
        if key in by_key:
            continue
        concepts.append({
            "key": key, "label": f"Scenarios Actuals — {label}", "category": "scenario_income",
            "source": {"system": "derived_scenario", "formula": formula,
                       "note": "Reverse-engineers the beds×rate model inputs so Scenarios EGI ties to T-12 actual EGI."},
            "targets": {"v4": None, "v5": None,
                        "v6": {"sheet": "Scenarios", "address": addr, "label_at": "A" + addr[1:]}},
            "status": "proposed",
            "notes": "Scenarios col-B Actuals income input; writer-paste derived value, no template change.",
            "path": "scenarios",
        })
        added_d += 1
    print(f"PHASE D: added {added_d} Scenarios col-B concepts")

    # ---------------------------------------------------------------- finalize
    reg["registry_version"] = NEW_REGISTRY_VERSION
    # status legend / category legend additions
    cats = reg.setdefault("category_legend", {})
    cats.setdefault("scenario_expense", "Scenarios tab 'Actuals (T-12)' expense input (mirrors T-12 Analysis)")
    cats.setdefault("scenario_income", "Scenarios tab 'Actuals (T-12)' income input (derived from RR + T-12)")
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    print(f"\nregistry_version -> {NEW_REGISTRY_VERSION} | total concepts: {len(concepts)}")

    # replace canonical asset
    shutil.copyfile(USER_FILE, ASSET)
    print(f"Replaced canonical asset: {ASSET}")


if __name__ == "__main__":
    main()
