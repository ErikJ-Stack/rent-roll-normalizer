"""
Track 4 / Phase 1 — registry extension to v0.2.0.

One-shot script that takes the Phase-0 registry.json (registry_version 0.1.0,
72 concepts, T-12 path only) and extends it to model the full three-path
handoff described in `2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md`:

  Path "t12"        — UW Output → T-12 Analysis  (existing 72 concepts)
  Path "rent_roll"  — Rent Roll Input rows 7+ → Rent Roll Analysis rows 211+
  Path "ar"         — AR & Collections → Rent Roll Analysis cols N–Q  (stubs)

Run once. Idempotent — re-runs detect already-extended registry and no-op.

After run, re-execute `python tools/uw_template/build_mapping_artifacts.py`
to regenerate the HTML / MD / CSV artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "registry.json"

# ──────────────────────────────────────────────────────────────────────────────
# Rent Roll path crosswalk — from handoff-contract §10.
#
# (analyzer_col, analyzer_label, ui_col, ui_label, category, status, notes)
#   ui_col = "" means no template target → status should be gap_target.
#   "—" labels stripped to None.
# ──────────────────────────────────────────────────────────────────────────────

RR_CROSSWALK = [
    # ─── identity / row keys ──────────────────────────────────────────────────
    ("A",  "Unit #",                  "A",  "Unit/Bed",                 "rr_identity",  "mapped",       ""),
    ("B",  "Room #",                  "B",  "Bed",                      "rr_identity",  "mapped",       "Renamed but 1:1."),
    ("C",  "Sq Ft",                   "T",  "Sq Ft (est)",              "rr_identity",  "mapped",       "Position shift A→T."),
    ("D",  "Care Type",               "C",  "Care Level",               "rr_identity",  "mapped",       "Renamed. Values IL/AL/MC unchanged."),
    ("E",  "Status",                  "D",  "Status",                   "rr_identity",  "mapped",       "Position shift E→D."),
    ("F",  "Apt Type",                "AC", "Apt Type",                 "rr_identity",  "mapped",       "Position shift F→AC. Possible label-form difference (e.g. '1BR' vs '1 Bedroom') — normalize upstream or handle in template."),
    ("R",  "Resident Name",           "E",  "Resident",                 "rr_identity",  "mapped",       "Position shift R→E."),

    # ─── dates ────────────────────────────────────────────────────────────────
    ("Q",  "Move-in Date",            "F",  "Move-In Date",             "rr_dates",     "mapped",       "Position shift Q→F."),
    ("W",  "Move-out Date",           "G",  "Discharge Date",           "rr_dates",     "mapped",       "Position shift W→G. Renamed."),
    ("J",  "Concession End Date",     "AE", "Concession End",           "rr_dates",     "mapped",       "Position shift J→AE."),
    ("S",  "Period Date",             "",   None,                       "rr_dates",     "gap_target",   "Analyzer col S is per-row; template has no per-row Period Date column. Capture as a single metadata cell in Rent Roll Analysis tab header (recommended v5)."),

    # ─── rates ────────────────────────────────────────────────────────────────
    ("G",  "Market Rate",             "H",  "Market Rate",              "rr_rates",     "mapped",       "Position shift G→H."),
    ("H",  "Actual Rate",             "I",  "Actual Charges",           "rr_rates",     "mapped",       "Position shift H→I. Renamed."),
    ("Z",  "Market PSF",              "AQ", "Market PSF",               "rr_rates",     "mapped",       "Position shift Z→AQ."),
    ("AA", "Actual PSF",              "U",  "$/SqFt/Mo",                "rr_rates",     "mapped",       "Position shift AA→U. Renamed."),
    ("I",  "Concession $",            "AD", "Concession $",             "rr_rates",     "mapped",       "Position shift I→AD."),
    ("V",  "2nd Person Rent $",       "AJ", "2nd Person $",             "rr_rates",     "mapped",       "Position shift V→AJ."),

    # ─── ancillary (Level of Care components) ─────────────────────────────────
    ("L",  "Care Level $",            "AF", "Care Level $",             "rr_ancillary", "mapped",       "Position shift L→AF."),
    ("K",  "Care Level (tier label)", "",   None,                       "rr_ancillary", "gap_target",   "Tier label (Basic / Level 2-7) has no template column. v5 wishlist: add a label col adjacent to AF Care Level $."),
    ("M",  "Med Mgmt $",              "AG", "Med Mgmt $",               "rr_ancillary", "mapped",       ""),
    ("N",  "Pharmacy $",              "AH", "Pharmacy $",               "rr_ancillary", "mapped",       ""),
    ("O",  "Other LOC $",             "AI", "Other LOC $",              "rr_ancillary", "mapped",       ""),
    ("AC", "Meal Plan $",             "AK", "Meal Plan $",              "rr_ancillary", "mapped",       "Position shift AC→AK."),
    ("AD", "Scooter Fee $",           "AL", "Scooter $",                "rr_ancillary", "mapped",       "Renamed."),
    ("AE", "Housekeeping $",          "AM", "Housekeeping $",           "rr_ancillary", "mapped",       ""),
    ("AF", "Laundry $",               "AN", "Laundry $",                "rr_ancillary", "mapped",       ""),
    ("AG", "Pet $",                   "AO", "Pet $",                    "rr_ancillary", "mapped",       ""),

    # ─── formula subtotals (formula in BOTH source and target) ────────────────
    ("T",  "Total LOC $",             "J",  "LOC Revenue",              "rr_subtotals", "mapped",       "Formula-derived in both. Writer should still paste-value the Analyzer's computed value; template formula re-derives but tie-out check needs the source figure."),
    ("U",  "Total Monthly Rev",       "K",  "Total Sched (Base+LOC)",   "rr_subtotals", "mapped",       "Formula-derived in both. Both = Actual + LOC only (no ancillary)."),
    ("AH", "Total Ancillary $",       "",   None,                       "rr_subtotals", "gap_target",   "Total Ancillary $ has no template column. v5 wishlist: add formula col `=AK+AL+AM+AN+AO` per row — no upstream change needed."),

    # ─── other per-row data ───────────────────────────────────────────────────
    ("P",  "Payer Type",              "R",  "Payer Type",               "rr_other",     "mapped",       "Position shift P→R."),
    ("X",  "Balance (AR)",            "L",  "AR Balance",               "rr_other",     "mapped",       "Position shift X→L. Renamed."),
    ("Y",  "Notes",                   "S",  "Notes",                    "rr_other",     "mapped",       "Position shift Y→S."),
    ("AB", "ACH",                     "AP", "ACH",                      "rr_other",     "mapped",       "Position shift AB→AP."),
]

# ──────────────────────────────────────────────────────────────────────────────
# AR aging stubs — handoff contract §11 (AR aging cols on UW Template).
#   Currently gap_source — gated on future row-level AR routing from
#   `AR & Collections` into `Rent Roll Input` (which would then paste through).
# ──────────────────────────────────────────────────────────────────────────────

AR_AGING_STUBS = [
    ("ar_aging_0_30",    "AR Aging — 0–30 Days",   "N", "0–30 Days"),
    ("ar_aging_31_60",   "AR Aging — 31–60 Days",  "O", "31–60"),
    ("ar_aging_61_90",   "AR Aging — 61–90 Days",  "P", "61–90"),
    ("ar_aging_90_plus", "AR Aging — 90+ Days",    "Q", "90+"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Deposit + Preleased Date — handled separately because of the AI conflict.
# ──────────────────────────────────────────────────────────────────────────────

NEW_STATUS_LEGEND = {
    "decided_pending_upstream": "Mapping decision is locked but the upstream Analyzer change has not yet shipped. Writer cannot ship until the upstream column lands.",
}

NEW_OPEN_QUESTIONS = [
    "Preleased Date relocation — RR v1.18.0 / substrate v0.2.13 (2026-05-25) put Preleased Date at `Rent Roll Input!AI`, but the 2026-05-25 handoff contract reserves AI for Deposit. Per user decision (2026-05-25 chat) Deposit gets AI; Preleased Date needs to move (likely AJ). This is a Track 1 + Track 3 cross-cutting follow-up: `mappings.py`/`normalizer.py` Preleased capture stays unchanged, but `analyzer_rr_writer.py` `COL_AI_INDEX` for Preleased Date relocates, substrate header at `Rent Roll Input!AI4` relocates, and the named range `RR_Input_Data` likely needs to widen past col S to cover the new ancillary cols.",
    "`RR_Input_Data` named range scope — currently `A7:S606`, but the rent roll paste path uses cols A–AH (now AI with Deposit). The named range no longer covers the full paste row. Decide: widen `RR_Input_Data` to `A7:AI606` (or wherever Deposit lands), or keep it as the legacy A:S range and document that ancillary cols are outside.",
    "Preleased Date in template v5 — no template target exists today. Either add a new column to Rent Roll Analysis (near move-in/move-out) or surface only in the diagnostic summary sections that reference the substrate's new Section N (Preleased exposure).",
    "Rent Roll Analysis header rows 1-209 — the contract specifies paste anchor at row 211 (header at 210). Rows 1-209 contain diagnostic sections that read from the pasted block via formulas. Writer must not touch rows 1-210. (Confirms the existing 'derived' framing for the upper section.)",
    "AR aging row-level routing — UW Template cols N-Q expect per-resident aging buckets, but the Analyzer's `AR & Collections` tab aggregates AR by payer, not by resident-bed. Routing aging $ to specific rent-roll rows needs an upstream substrate change (resident-key join into AR & Collections) before these concepts move off `gap_source`.",
]


def _existing_keys(reg: dict) -> set[str]:
    return {c["key"] for c in reg["concepts"]}


def _make_rr_concept(analyzer_col: str, analyzer_label: str,
                     ui_col: str, ui_label: str | None,
                     category: str, status: str, notes: str) -> dict:
    key_base = analyzer_label.lower()
    for ch in [" ", "/", "(", ")", "$", "—", "–", "-", ".", "&", ",", "'"]:
        key_base = key_base.replace(ch, "_")
    while "__" in key_base:
        key_base = key_base.replace("__", "_")
    key_base = key_base.strip("_")
    key = f"rr_{key_base}"

    target = None
    if ui_col:
        target = {
            "sheet": "Rent Roll Analysis",
            "address": f"{ui_col}211+",
            "label_at": f"{ui_col}210",
            "target_label": ui_label,
            "paste_anchor": "Rent Roll Analysis!A211",
        }

    return {
        "key": key,
        "label": analyzer_label,
        "category": category,
        "path": "rent_roll",
        "source": {
            "system": "rr_input",
            "sheet": "Rent Roll Input",
            "address": f"{analyzer_col}7:{analyzer_col}606",
            "column": analyzer_col,
            "label": analyzer_label,
        },
        "targets": {"v4": target},
        "status": status,
        "notes": notes,
    }


def _make_ar_concept(key: str, label: str, ui_col: str, ui_label: str) -> dict:
    return {
        "key": key,
        "label": label,
        "category": "ar_aging",
        "path": "ar",
        "source": {
            "system": "gap",
            "note": "Per-resident AR aging not currently exposed in Rent Roll Input. Future: route from AR & Collections via a resident-key join (upstream substrate change).",
        },
        "targets": {"v4": {
            "sheet": "Rent Roll Analysis",
            "address": f"{ui_col}211+",
            "label_at": f"{ui_col}210",
            "target_label": ui_label,
            "paste_anchor": "Rent Roll Analysis!A211",
        }},
        "status": "gap_source",
        "notes": "UW Template expects per-resident aging buckets. Analyzer's AR & Collections (substrate v0.2.10+) aggregates by payer, not by resident — row-level join needed upstream before this can move off gap_source.",
    }


def main() -> None:
    reg = json.loads(REG.read_text(encoding="utf-8"))

    # ─── Idempotency check ────────────────────────────────────────────────────
    if reg.get("registry_version", "0.1.0") >= "0.2.0":
        print(f"Registry already at v{reg['registry_version']} — no-op.")
        return

    existing = _existing_keys(reg)

    # ─── 1. Backfill path='t12' on existing concepts ──────────────────────────
    for c in reg["concepts"]:
        c.setdefault("path", "t12")

    # ─── 2. Header field updates ──────────────────────────────────────────────
    reg["registry_version"] = "0.2.0"
    reg["generated_phase"] = (
        "Track 4 Phase 1 — three-path mapping (T-12 + Rent Roll + AR). Still no writer."
    )
    reg["analyzer"]["substrate_version"] = "v0.2.11"  # match 2026-05-25 contract
    reg["analyzer"]["source_sheets"] = ["UW Output", "UW Export", "Rent Roll Input", "AR & Collections"]
    reg["analyzer"]["named_ranges_used"] = [
        "Property_Name", "RR_Period_Date", "T12_Period_Date", "RR_Input_Data",
    ]
    reg["analyzer"]["handoff_contract"] = (
        "Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/"
        "2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md (external — authoritative)"
    )

    # template intake sheets: confirm Rent Roll Analysis now in scope
    v4 = reg["templates"]["v4"]
    v4["intake_sheets"] = ["Prop Info", "T-12 Analysis", "Rent Roll Analysis"]
    v4["rent_roll_paste_anchor"] = "Rent Roll Analysis!A211"
    v4["rent_roll_header_row"] = 210
    v4["rent_roll_diagnostic_rows"] = "1-209 (formula-derived from paste; writer must not overwrite)"

    # ─── 3. Add rent_roll path concepts ───────────────────────────────────────
    rr_added = 0
    for tup in RR_CROSSWALK:
        c = _make_rr_concept(*tup)
        if c["key"] in existing:
            continue
        reg["concepts"].append(c)
        existing.add(c["key"])
        rr_added += 1

    # ─── 4. Add AR aging stubs ────────────────────────────────────────────────
    ar_added = 0
    for tup in AR_AGING_STUBS:
        c = _make_ar_concept(*tup)
        if c["key"] in existing:
            continue
        reg["concepts"].append(c)
        existing.add(c["key"])
        ar_added += 1

    # ─── 5. Deposit + Preleased Date (special cases per AI-conflict decision) ─
    deposit = {
        "key": "rr_deposit",
        "label": "Deposit",
        "category": "rr_other",
        "path": "rent_roll",
        "source": {
            "system": "rr_input",
            "sheet": "Rent Roll Input",
            "address": "AI7:AI606",
            "column": "AI",
            "label": "Deposit (pending upstream)",
            "status_note": "DECIDED 2026-05-25 to add Deposit to Rent Roll Input!AI. Upstream substrate change pending; Preleased Date (currently at AI per v0.2.13) needs to relocate first.",
        },
        "targets": {"v4": {
            "sheet": "Rent Roll Analysis", "address": "M211+",
            "label_at": "M210", "target_label": "Deposit",
            "paste_anchor": "Rent Roll Analysis!A211",
        }},
        "status": "decided_pending_upstream",
        "notes": "User decision 2026-05-25: Deposit gets `Rent Roll Input!AI`. Preleased Date (currently at AI per v0.2.13) must relocate before Deposit can land. Tracked as cross-track follow-up — see open_questions.",
    }
    if deposit["key"] not in existing:
        reg["concepts"].append(deposit)
        existing.add(deposit["key"])

    preleased = {
        "key": "rr_preleased_date",
        "label": "Preleased Date",
        "category": "rr_dates",
        "path": "rent_roll",
        "source": {
            "system": "rr_input",
            "sheet": "Rent Roll Input",
            "address": "AI7:AI606  (until relocated)",
            "column": "AI",
            "label": "Preleased Date",
            "status_note": "Lives at AI per RR v1.18.0 / substrate v0.2.13 (2026-05-25). To be relocated per Deposit decision — likely AJ.",
        },
        "targets": {"v4": None},
        "status": "gap_target",
        "notes": "Substrate v0.2.13 captures Preleased Date for the new Section N exposure block on Rent Roll Recon, but the UW Template v4 has no per-row Preleased Date column. v5 wishlist: add column near move-in/move-out, or surface via diagnostic-only.",
    }
    if preleased["key"] not in existing:
        reg["concepts"].append(preleased)
        existing.add(preleased["key"])

    # ─── 6. Status legend additions ───────────────────────────────────────────
    for k, v in NEW_STATUS_LEGEND.items():
        reg["status_legend"].setdefault(k, v)

    # ─── 7. Category legend additions ─────────────────────────────────────────
    reg["category_legend"].update({
        "rr_identity":  "Rent Roll: row-key columns (Unit, Bed, Care Level, Status, Resident, Sq Ft, Apt Type).",
        "rr_dates":     "Rent Roll: per-resident date fields (move-in, move-out, concession end, preleased, period).",
        "rr_rates":     "Rent Roll: per-bed rates and rate-derived $ (market, actual, PSF, concessions, 2P rent).",
        "rr_ancillary": "Rent Roll: Level-of-Care component columns (Care Level $, tier label, Med Mgmt, Pharmacy, Other LOC, Meal, Scooter, HK, Laundry, Pet).",
        "rr_subtotals": "Rent Roll: formula-derived subtotal columns (Total LOC, Total Monthly Rev, Total Ancillary).",
        "rr_other":     "Rent Roll: ACH, AR Balance, Notes, Deposit — non-rate, non-ancillary per-row data.",
        "ar_aging":     "AR aging buckets per resident (0-30, 31-60, 61-90, 90+) — currently gap_source.",
    })

    # ─── 8. Open questions ────────────────────────────────────────────────────
    reg.setdefault("open_questions", [])
    existing_q = set(reg["open_questions"])
    for q in NEW_OPEN_QUESTIONS:
        if q not in existing_q:
            reg["open_questions"].append(q)

    # ─── 9. Update intake_targets_unmapped ────────────────────────────────────
    # The whole-sheet "Rent Roll Analysis is fed by raw paste — future
    # enhancement" entry from Phase 0 is now obsolete because we're modeling
    # that path. Remove or replace.
    new_unmapped = []
    for u in reg.get("intake_targets_unmapped", []):
        is_rr_whole_sheet = (
            u.get("sheet") == "Rent Roll Analysis"
            and u.get("kind") == "manual"
            and "whole sheet" in (u.get("notes") or "").lower()
        )
        if is_rr_whole_sheet:
            continue  # supersede with the new path-aware entries below
        new_unmapped.append(u)
    new_unmapped.append({
        "sheet": "Rent Roll Analysis",
        "rows_range": "rows 1-209 (diagnostic sections A-R)",
        "kind": "derived",
        "notes": "Header diagnostic sections (Health Check, Census, Status Taxonomy, GPR Reconciliation, LOS Cohort, Days Vacant, Delinquency, Payer Mix, Rate-by-Care, Charge Variance, Deposit Coverage, Move-in Seasonality, Pre-Admission Pipeline, Wing Vacancy). All formula-derived from the row 211+ paste — writer must not overwrite.",
    })
    new_unmapped.append({
        "sheet": "Rent Roll Analysis",
        "rows_range": "row 211+",
        "kind": "paste_anchor",
        "notes": "34-col paste from Analyzer Rent Roll Input rows 7-606. Column positions DO NOT match 1:1 — see rent_roll path concepts. Formula-derived cols on the template side (V, X, Y, Z, AA, AB, AS) must NOT be overwritten by paste.",
    })
    new_unmapped.append({
        "sheet": "Rent Roll Analysis",
        "rows_range": "cols AR, AS",
        "kind": "manual",
        "notes": "Conc Source (AR) and Effective Conc $ (AS) are analyst-entered per-row. Writer must preserve any existing values on re-paste.",
    })
    new_unmapped.append({
        "sheet": "Rent Roll Analysis",
        "rows_range": "cols V, X, Y, Z, AA, AB",
        "kind": "derived",
        "notes": "$/SqFt/Yr (V), Care|UnitType (X), Care|Unit (Y), _key (Z), Mkt-Actual $ (AA), Mkt-Actual % (AB) — formula columns. Do not overwrite.",
    })
    reg["intake_targets_unmapped"] = new_unmapped

    # ─── 10. Write back ───────────────────────────────────────────────────────
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Registry extended to v{reg['registry_version']}:")
    print(f"  + path='t12' backfilled on all pre-existing concepts")
    print(f"  + {rr_added} rent_roll concepts added")
    print(f"  + {ar_added} ar concepts added")
    print(f"  + Deposit + Preleased Date concepts added (AI conflict logged)")
    print(f"  + {len(NEW_OPEN_QUESTIONS)} open questions appended")
    print(f"  + substrate mapped-against bumped to v0.2.11")
    print(f"  Total concepts now: {len(reg['concepts'])}")


if __name__ == "__main__":
    main()
