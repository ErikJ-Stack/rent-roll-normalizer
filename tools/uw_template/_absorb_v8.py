"""
_absorb_v8.py — Registry absorption for ALF_UW_Template_v8.xlsx (2026-06-12).

Operator dropped `Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v8.xlsx`
("use this as the new updated version template"). Verified cell-by-cell against
the committed v6 binary (see CHANGELOG-UWT v0.10.0):

- **All 188 registry v6 targets are IDENTICAL in v8** — T-12 Analysis,
  Scenarios, and Prop Info target cells did not move. The 94 T-12 Analysis
  diffs are new T-3/T-1 annualized diagnostics (row 9 area) + Section I
  skeleton mapping-label reorder (writer clears/rewrites Section I anyway).
  The 152 Scenarios diffs are the col-F CHOOSE refactor + col-G ratio fixes +
  B141:E141 basis upgrades — none a writer target.
- **Rent Roll Analysis: new col AV "NER $/mo (amort)"** (net effective rent,
  concession amortized over `AC174` months, default 12) — template-owned
  fill-down at AV214:AV613. New analysis blocks at rows 174–191:
  NET EFFECTIVE / CONCESSIONS (AB175:AD191) + RECENT MOVE-INS — LAST 10
  (AF175:AN186 with AP/AQ helper arrays). AT (Conc Source) + AU (Effective
  Conc $) are now template-formula columns (were analyst-input in v5/v6).
- **THE PASTE-GRID RE-ANCHOR (the substantive change):** every RR Analysis
  aggregate (in v8 AND, it turns out, in v6 rev2) reads rows **214:613** —
  the operator's true grid is header row 213 / data 214+. The v6-era writer
  anchor (211) was stale against rev2: beds pasted at 211–213 fell outside
  every diagnostic and bed #3 clobbered the operator's 213 header row. v8
  targets re-anchor every `…211+` rent_roll address to `…214+`.
- Cover!A3 self-stamps "Template Version 9.0 — Updated 2026-06-11
  (IRR-hurdle waterfall)". The FILE is named v8; the registry keys on the
  filename per established convention. Waterfall/LP Return/XIRR/Acq Costs
  diffs are analyst-side (no writer targets).

Run:  python tools/uw_template/_absorb_v8.py
Idempotent — re-running on an absorbed registry is a no-op.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

REGISTRY = Path(__file__).parent / "registry.json"

RR_SHEET = "Rent Roll Analysis"
RE_ANCHOR = re.compile(r"^([A-Z]+)211(\+)$")

TEMPLATES_V8 = {
    "file": "assets/ALF_UW_Template_v8.xlsx",
    "released": "2026-06-11",
    "supersedes": "v6",
    "self_stamp": "Cover!A3 = 'Template Version 9.0 - Updated 2026-06-11 (IRR-hurdle waterfall)' — registry keys on the v8 FILENAME per convention",
    "intake_sheets": ["Prop Info", "T-12 Analysis", "Rent Roll Analysis"],
    "annual_total_column": "N",
    "monthly_columns": ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"],
    "monthly_header_row": 56,
    "rent_roll_paste_anchor": "Rent Roll Analysis!A214",
    "rent_roll_header_row": 213,
    "rent_roll_data_end_row": 613,
    "rent_roll_last_col": "AV",
    "rent_roll_diagnostic_rows": "1-209 (formula-derived; aggregates read $214:$613) + legacy duplicate header at 210 (cosmetic leftover of the v0.9.0 fix #4 restore; the operator's live header is row 213)",
    "rent_roll_template_formula_cols": "K L V W X Y AA AB AP AT AU AV — template-owned fill-downs inside the paste band; writer must never write them (AT/AU newly formula-driven in v8; were analyst-input)",
    "sheet_count": 16,
    "income_model": "actual_t12",
    "t12_layout_note": "T-12 Analysis layout identical to v6 rev2 — EGI N80, Total Labor N102, EBITDARM N134, EBITDAR N135, EBITDA N136, Section I 141-190, Section J 194-196. New T-3/T-1 annualized diagnostics at row 9 (C9:G9, non-target).",
    "new_in_v8": [
        "Rent Roll Analysis col AV 'NER $/mo (amort)' — net effective rent, concessions amortized over AC174 months (default 12); fill-down AV214:AV613",
        "Rent Roll Analysis rows 174-191: NET EFFECTIVE / CONCESSIONS block (AB175:AD191) + RECENT MOVE-INS — LAST 10 block (AF175:AN186, AP/AQ helper arrays)",
        "AT (Conc Source) auto-derived via IFS; AU (Effective Conc $) formula — both were analyst-input in v5/v6",
        "Scenarios col-F CHOOSE refactored to $B$4:$E$4 MATCH; col-G ratio denominators fixed; B141:E141 basis upgraded with Acquisition Costs linkage",
        "Waterfall rebuilt as IRR-hurdle structure (121x16, was 101x14) — analyst-side",
        "Cover A3 version stamp",
    ],
    "template_quirks": [
        "K/L/V/W fill-downs cover only rows 214-389 (176 data rows — a working-file artifact); deals >176 beds lose Total LOC / Total Sched / PSF formulas on the overflow rows until the operator fills down. Flagged to operator 2026-06-12.",
        "AA/AB fill-downs cover 345 rows (214-558).",
    ],
}

NER_CONCEPT = {
    "key": "rr_ner_amort",
    "label": "NER $/mo (amortized concessions)",
    "category": "rent_roll_derived",
    "source": {
        "system": "derived",
        "name": "template_formula",
        "resolves_to": "Template-owned: =J - amortized concession (AC over AC174 months); occupied rows only",
    },
    "targets": {
        "v8": {"sheet": RR_SHEET, "address": "AV214+"},
    },
    "status": "derived",
    "notes": "New in v8. Template fill-down AV214:AV613 referencing the AC174 amort-term input (default 12 mo). Writer skips (derived) — never paste over it. Feeds the NET EFFECTIVE / CONCESSIONS block (AD177+ Avg NER/mo).",
    "path": "rent_roll",
}


def main() -> None:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))

    if "v8" in reg.get("templates", {}) and reg["registry_version"] == "0.7.0":
        print("Registry already at 0.7.0 with templates.v8 — no-op.")
        return

    reg["templates"]["v8"] = TEMPLATES_V8

    reanchored = 0
    inherited = 0
    for c in reg["concepts"]:
        t6 = (c.get("targets") or {}).get("v6")
        if not t6:
            continue
        t8 = copy.deepcopy(t6)
        addr = t8.get("address") or ""
        if t8.get("sheet") == RR_SHEET:
            m = RE_ANCHOR.match(addr)
            if m:
                t8["address"] = f"{m.group(1)}214+"
                reanchored += 1
            else:
                inherited += 1
        else:
            inherited += 1
        c["targets"]["v8"] = t8

    if not any(c.get("key") == "rr_ner_amort" for c in reg["concepts"]):
        reg["concepts"].append(NER_CONCEPT)

    reg["registry_version"] = "0.7.0"
    reg["generated_phase"] = (
        "Track 4 v8 — operator template v8 absorbed (2026-06-12). All 188 v6 "
        "targets verified identical; rent_roll paste grid re-anchored 211+ -> 214+ "
        "(header row 213; aggregates read $214:$613 — fixes the stale-211 anchor "
        "that dropped the first beds out of every RR Analysis diagnostic). New "
        "derived concept rr_ner_amort (AV214+). Default template v6 -> v8."
    )

    REGISTRY.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ── verify ───────────────────────────────────────────────────────────────
    reg2 = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = []
    checks.append(("registry_version 0.7.0", reg2["registry_version"] == "0.7.0"))
    checks.append(("templates.v8 present", "v8" in reg2["templates"]))
    by_key = {c["key"]: c for c in reg2["concepts"]}
    checks.append(("rr_unit_# -> A214+", by_key["rr_unit_#"]["targets"]["v8"]["address"] == "A214+"))
    checks.append(("rr_ach -> AR214+", by_key["rr_ach"]["targets"]["v8"]["address"] == "AR214+"))
    checks.append(("egi unchanged N80", by_key["egi"]["targets"]["v8"]["address"] == by_key["egi"]["targets"]["v6"]["address"]))
    checks.append(("rr_ner_amort present", "rr_ner_amort" in by_key and by_key["rr_ner_amort"]["status"] == "derived"))
    n_v8 = sum(1 for c in reg2["concepts"] if (c.get("targets") or {}).get("v8"))
    checks.append((f"v8 targets count ({n_v8})", n_v8 >= 189))
    ok = all(p for _, p in checks)
    for label, p in checks:
        print(("PASS " if p else "FAIL ") + label)
    print(f"re-anchored: {reanchored} | inherited: {inherited} | concepts: {len(reg2['concepts'])}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
