"""
_absorb_v11.py — Registry absorption for ALF_UW_Template_v11.xlsx (2026-06-16).

Operator dropped `Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v11.xlsx`
("this is the updated ALF UW Template … update as needed"), alongside a new
ALF_Financial_Analyzer_Only.xlsx (substrate v0.3.0 — handled separately).

Verified cell-by-cell against the committed v8 binary (see CHANGELOG-UWT v0.11.0):

- **All 189 registry v8 targets have IDENTICAL labels in v11** — T-12 Analysis,
  Scenarios, and Prop Info (rows ≤24) target cells did not move.
- **The substantive change: the RR Analysis paste grid re-anchored 214 → 224.**
  v11 inserted a new "S. CONCESSIONS AUDIT" taxonomy block at rows ~205-211,
  pushing the header from row 213 → **223** and the data band from 214-613 →
  **224-623**. Every RR Analysis aggregate now reads `$224:$623` (confirmed:
  E9 `AVERAGEIFS($L$224:$L$623,...)`). The writer derives the anchor from the
  registry templates block, so this is a registry-only change (no writer logic
  edit) — same pattern as the v8 absorption (211 → 214).
- **The v8 >176-bed fill-down quirk is FIXED**: K/L/V/W (and AA/AB) fill-downs
  now cover the FULL band 224-623, not just 176 rows. No quirk to carry forward.
- **Prop Info expanded 53 → 57 rows** (manual MARKET DATA zone, rows 30+):
  split "Population Growth Rate" → MSA + City, and "Competitor Occupancy Rate"
  → per-segment IL/AL/MC/Other. All manual analyst inputs — NO writer targets
  (the registry only auto-fills Prop Info B4/B6/B11/B13/B15-18/B20-24, all ≤24,
  all unchanged).
- **metadata.xml absent but NOT needed**: v11 uses 573 legacy CSE array
  formulas and ZERO Excel-365 dynamic-array spill functions (no SORT/UNIQUE/
  FILTER/ANCHORARRAY), so the writer's `_restore_dynamic_arrays` correctly
  no-ops. Self-contained — Section R/S matrices are CSE arrays.
- **T-12 Analysis layout unchanged** vs v8/v6 rev2 (197×20, EGI N80, EBITDARM
  N134, EBITDAR N135, EBITDA N136, Section I/J 141/194). P&L max_row 130→131
  is a phantom empty row (no concept targets). Same 48 cols (A-AV).

No new concepts (the new Section S + Prop Info expansion are analyst-driven /
formula-derived, not writer targets). `rr_ner_amort` re-anchors AV214+ → AV224+.

Run:  python tools/uw_template/_absorb_v11.py
Idempotent — re-running on an absorbed registry is a no-op.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

REGISTRY = Path(__file__).parent / "registry.json"

RR_SHEET = "Rent Roll Analysis"
RE_ANCHOR = re.compile(r"^([A-Z]+)214(\+)$")

TEMPLATES_V11 = {
    "file": "assets/ALF_UW_Template_v11.xlsx",
    "released": "2026-06-16",
    "supersedes": "v8",
    "self_stamp": "File named v11; registry keys on the FILENAME per convention.",
    "intake_sheets": ["Prop Info", "T-12 Analysis", "Rent Roll Analysis"],
    "annual_total_column": "N",
    "monthly_columns": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"],
    "monthly_header_row": 56,
    "rent_roll_paste_anchor": "Rent Roll Analysis!A224",
    "rent_roll_header_row": 223,
    "rent_roll_data_end_row": 623,
    "rent_roll_last_col": "AV",
    "rent_roll_diagnostic_rows": "1-222 (formula-derived; aggregates read $224:$623). New Section S 'CONCESSIONS AUDIT' block at rows ~205-211 caused the +10 shift vs v8. Legacy duplicate header at row 210 from the v8 lineage may persist (cosmetic); the operative header is row 223.",
    "rent_roll_template_formula_cols": "K L V W X Y AA AB AP AT AU AV — template-owned fill-downs; writer must never write them. v11 fill-downs cover the FULL band 224-623 (the v8 >176-bed quirk is fixed).",
    "sheet_count": 16,
    "income_model": "actual_t12",
    "t12_layout_note": "T-12 Analysis layout identical to v8/v6 rev2 — EGI N80, Total Labor N102, EBITDARM N134, EBITDAR N135, EBITDA N136, Section I 141-190, Section J 194-196.",
    "new_in_v11": [
        "RR Analysis paste grid re-anchored 214 -> 224 (header 213 -> 223) — new Section S 'CONCESSIONS AUDIT' taxonomy block at rows ~205-211 pushed everything down 10 rows.",
        "K/L/V/W/AA/AB fill-downs extended to the full band 224-623 (fixes the v8 >176-bed quirk).",
        "Prop Info 53 -> 57 rows: MARKET DATA split into MSA + City population growth and per-segment Competitor Occupancy (IL/AL/MC/Other). Manual inputs, no writer targets.",
        "metadata.xml dropped on the operator's Excel save — harmless (573 legacy CSE arrays, no dynamic-array spills).",
    ],
    "binary_health": "41 zip parts; metadata.xml absent (not needed — no spill formulas), webextensions + calcChain present. Excel-native save.",
}


def main() -> None:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))

    if "v11" in reg.get("templates", {}) and reg["registry_version"] == "0.8.0":
        print("Registry already at 0.8.0 with templates.v11 — no-op.")
        return

    reg["templates"]["v11"] = TEMPLATES_V11

    reanchored = 0
    inherited = 0
    for c in reg["concepts"]:
        t8 = (c.get("targets") or {}).get("v8")
        if not t8:
            continue
        t11 = copy.deepcopy(t8)
        addr = t11.get("address") or ""
        if t11.get("sheet") == RR_SHEET:
            m = RE_ANCHOR.match(addr)
            if m:
                t11["address"] = f"{m.group(1)}224+"
                reanchored += 1
            else:
                inherited += 1
        else:
            inherited += 1
        c["targets"]["v11"] = t11

    reg["registry_version"] = "0.8.0"
    reg["generated_phase"] = (
        "Track 4 v11 — operator template v11 absorbed (2026-06-16). All 189 v8 "
        "targets verified identical; rent_roll paste grid re-anchored 214+ -> 224+ "
        "(header 213 -> 223; aggregates read $224:$623 — new Section S concessions-"
        "audit block pushed the grid down 10 rows). Fill-downs now cover the full "
        "band (v8 >176-bed quirk fixed). Default template v8 -> v11. Paired with "
        "Analyzer substrate v0.2.16 -> v0.3.0 (UW Output +1 row at bottom, T-12 "
        "Analytics +OTH col, Description_Map +155 GL descriptions)."
    )

    REGISTRY.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ── verify ───────────────────────────────────────────────────────────────
    reg2 = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_key = {c["key"]: c for c in reg2["concepts"]}
    checks = [
        ("registry_version 0.8.0", reg2["registry_version"] == "0.8.0"),
        ("templates.v11 present", "v11" in reg2["templates"]),
        ("rr_unit_# -> A224+", by_key["rr_unit_#"]["targets"]["v11"]["address"] == "A224+"),
        ("rr_ach -> AR224+", by_key["rr_ach"]["targets"]["v11"]["address"] == "AR224+"),
        ("rr_ner_amort -> AV224+", by_key["rr_ner_amort"]["targets"]["v11"]["address"] == "AV224+"),
        ("egi unchanged N80", by_key["egi"]["targets"]["v11"]["address"] == by_key["egi"]["targets"]["v8"]["address"]),
        ("prop unit count B6 unchanged",
         by_key["rr_unit_count"]["targets"]["v11"]["address"] == by_key["rr_unit_count"]["targets"]["v8"]["address"]),
    ]
    n_v11 = sum(1 for c in reg2["concepts"] if (c.get("targets") or {}).get("v11"))
    checks.append((f"v11 targets count ({n_v11})", n_v11 >= 189))
    ok = all(p for _, p in checks)
    for label, p in checks:
        print(("PASS " if p else "FAIL ") + label)
    print(f"re-anchored: {reanchored} | inherited: {inherited} | concepts: {len(reg2['concepts'])}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
