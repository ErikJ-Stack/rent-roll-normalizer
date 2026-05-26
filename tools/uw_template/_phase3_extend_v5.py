"""
Track 4 / Phase 3 — registry extension to v0.3.0 (absorb UW Template v5).

One-shot script that takes the Phase-1.5 registry (v0.2.1, 111 concepts, all
targeting template v4) and extends it to **also** map template v5, per the
2026-05-26 release of `ALF_UW_Template_v5.xlsx`.

Modular pattern preserved: every concept gains a `targets.v5` block alongside
its existing `targets.v4`. `templates.v5` block added to the registry header.
No v4 targets are removed (backward compat).

Status transitions (v4 → v5):
  - 7 `gap_target` concepts close into v5 mapped/derived targets:
      ebitda, opex_total_excl_mgmt, occupied_beds_il/al/mc,
      rr_care_level_tier, rr_total_ancillary, rr_preleased_date
  - rr_total_ancillary moves to status `derived` because template owns the
    AQ formula `=SUM(AK:AO)`; writer skips.
  - ebitdarm + ebitdar shift in v5 due to row 115 insert:
      ebitdarm v4 N115 → v5 N116
      ebitdar  v4 N116 → v5 N117

Substrate version pin: unchanged (v0.2.14 — v5 didn't change the substrate
contract, only added template-side rows/cols).

Idempotency: re-runs no-op if registry_version >= "0.3.0".

Usage: python tools/uw_template/_phase3_extend_v5.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "registry.json"

# ──────────────────────────────────────────────────────────────────────────────
# v5 template block
# ──────────────────────────────────────────────────────────────────────────────

V5_TEMPLATE = {
    "file": "Sample Files/ALF_UW_Template_v5.xlsx",
    "released": "2026-05-26",
    "supersedes": "v4",
    "intake_sheets": ["Prop Info", "T-12 Analysis", "Rent Roll Analysis"],
    "annual_total_column": "N",  # T-12 Analysis annual col
    "monthly_columns": ["B","C","D","E","F","G","H","I","J","K","L","M"],
    "monthly_header_row": 56,
    "monthly_header_strategy": (
        "Formula-driven from on-sheet Layer 1 raw row 122 "
        "(B56=C122, ..., M56=N122). No writer overwrite required."
    ),
    "rent_roll_paste_anchor": "Rent Roll Analysis!A211",
    "rent_roll_header_row": 210,
    "rent_roll_data_end_row": 610,  # capacity 400 units (211..610)
    "rent_roll_diagnostic_rows": "1-209 (formula-derived from paste; writer must not overwrite)",
    "rr_input_data_range": "'Rent Roll Input'!$A$7:$AJ$606  (unchanged from substrate v0.2.14)",
    "sheet_count": 16,
    "removed_sheets_vs_v4": ["Additional Fees"],
    "new_rows_vs_v4": [
        {"sheet": "T-12 Analysis", "row": 115,
         "label": "Total Operating Expenses (excl. mgmt)",
         "formula": "=N114-N113", "note": "Template owns formula; writer overwrites with UW Output value when present"},
        {"sheet": "T-12 Analysis", "row": 118,
         "label": "EBITDA",
         "formula": None, "note": "Label only; writer populates from UW Output row 68"},
        {"sheet": "Prop Info", "row": 19,
         "label": "Occupied Beds — Total",
         "formula": "=SUM(B20:B22)", "note": "Template formula; writer must not overwrite"},
        {"sheet": "Prop Info", "row": 20, "label": "Occupied Beds — IL"},
        {"sheet": "Prop Info", "row": 21, "label": "Occupied Beds — AL"},
        {"sheet": "Prop Info", "row": 22, "label": "Occupied Beds — MC"},
    ],
    "new_cols_vs_v4": [
        {"sheet": "Rent Roll Analysis", "col": "AP", "label": "Care Level Tier",
         "from_analyzer_col": "K"},
        {"sheet": "Rent Roll Analysis", "col": "AQ", "label": "Total Ancillary $",
         "formula": "=SUM(AK211:AO211)", "note": "Template-owned formula; writer skips"},
        {"sheet": "Rent Roll Analysis", "col": "AR", "label": "Preleased Date",
         "from_analyzer_col": "AJ  (substrate v0.2.14)"},
    ],
    "shifted_cols_vs_v4": [
        {"sheet": "Rent Roll Analysis", "label": "ACH", "v4": "AP", "v5": "AS"},
        {"sheet": "Rent Roll Analysis", "label": "Market PSF", "v4": "AQ", "v5": "AT"},
        {"sheet": "Rent Roll Analysis", "label": "Conc Source", "v4": "AR", "v5": "AU",
         "note": "Analyst-input; writer must preserve on re-paste"},
        {"sheet": "Rent Roll Analysis", "label": "Effective Conc $", "v4": "AS", "v5": "AV",
         "note": "Analyst-input or formula; writer must preserve on re-paste"},
    ],
    "deferred_to_v5_1": [
        "Cover substrate version stamp — concept `substrate_version` stays gap_target",
        "Per-row Period Date / metadata cell on Rent Roll Analysis tab header",
    ],
}

# v4 template block additions (data_end_row was missing — backfill)
V4_BACKFILL = {
    "data_end_row": 386,  # 211..386 = 176 rows
    "rent_roll_data_end_row": 386,
}

# ──────────────────────────────────────────────────────────────────────────────
# Concept v5 target overrides
#
# For each affected concept key, define the v5 target. None means "no v5 target"
# (rare — most concepts inherit v4 unchanged, but we declare them explicitly to
# make the registry future-proof).
#
# `_status_v5` (optional): if present, override the concept's status. Without it,
# status stays as-is.
# ──────────────────────────────────────────────────────────────────────────────

V5_TARGETS: dict[str, dict] = {
    # ── T-12 path: shifted ────────────────────────────────────────────────────
    "ebitdarm": {
        "_target": {"sheet": "T-12 Analysis", "address": "N116", "label_at": "A116",
                    "target_label": "EBITDARM"},
        "_status_v5": "mapped",
        "_notes": ("v5: row shifted from N115 (v4) → N116 due to new "
                   "'Total Operating Expenses (excl. mgmt)' row at N115. "
                   "Template has fallback formula `=N69-N85-N111`; writer "
                   "overwrites with UW Output row 66 value."),
    },
    "ebitdar": {
        "_target": {"sheet": "T-12 Analysis", "address": "N117", "label_at": "A117",
                    "target_label": "EBITDAR  (= NOI)"},
        "_status_v5": "mapped",
        "_notes": ("v5: row shifted from N116 (v4) → N117 due to new row 115 "
                   "insert. Writer populates from UW Output row 67."),
    },

    # ── T-12 path: closed gaps ────────────────────────────────────────────────
    "opex_total_excl_mgmt": {
        "_target": {"sheet": "T-12 Analysis", "address": "N115", "label_at": "A115",
                    "target_label": "Total Operating Expenses (excl. mgmt)"},
        "_status": "mapped",  # was gap_target
        "_notes": ("Closed in v5 — N115 has template formula `=N114-N113`. "
                   "Writer overwrites with UW Output row 63 value (Total opex "
                   "excl. mgmt) when present; falls back to template formula "
                   "on empty Analyzer."),
    },
    "ebitda": {
        "_target": {"sheet": "T-12 Analysis", "address": "N118", "label_at": "A118",
                    "target_label": "EBITDA"},
        "_status": "mapped",  # was gap_target
        "_notes": ("Closed in v5 — N118 row added (label only, no formula). "
                   "Writer populates from UW Output row 68."),
    },

    # ── Capacity: closed gaps ─────────────────────────────────────────────────
    "occupied_beds_il": {
        "_target": {"sheet": "Prop Info", "address": "B20", "label_at": "A20",
                    "target_label": "Occupied Beds — IL"},
        "_status": "mapped",
        "_notes": ("Closed in v5 — Prop Info rows 19-22 added. "
                   "Writer populates B20 from UW Output!B71."),
    },
    "occupied_beds_al": {
        "_target": {"sheet": "Prop Info", "address": "B21", "label_at": "A21",
                    "target_label": "Occupied Beds — AL"},
        "_status": "mapped",
        "_notes": "Closed in v5 — writer populates B21 from UW Output!C71.",
    },
    "occupied_beds_mc": {
        "_target": {"sheet": "Prop Info", "address": "B22", "label_at": "A22",
                    "target_label": "Occupied Beds — MC"},
        "_status": "mapped",
        "_notes": "Closed in v5 — writer populates B22 from UW Output!D71.",
    },

    # ── Rent Roll path: closed gaps + shifts ──────────────────────────────────
    "rr_care_level_tier_label": {
        "_target": {"sheet": "Rent Roll Analysis", "address": "AP211+",
                    "label_at": "AP210", "target_label": "Care Level Tier",
                    "paste_anchor": "Rent Roll Analysis!A211"},
        "_status": "mapped",  # was gap_target
        "_notes": ("Closed in v5 — UW Template col AP. Writer pastes from "
                   "Rent Roll Input col K (Care Level tier label, e.g. "
                   "Basic / Level 2-7)."),
    },
    "rr_preleased_date": {
        "_target": {"sheet": "Rent Roll Analysis", "address": "AR211+",
                    "label_at": "AR210", "target_label": "Preleased Date",
                    "paste_anchor": "Rent Roll Analysis!A211"},
        "_status": "mapped",  # was gap_target
        "_notes": ("Closed in v5 — UW Template col AR. Writer pastes from "
                   "Rent Roll Input col AJ (substrate v0.2.14 relocation). "
                   "Date format mm/dd/yyyy."),
    },
    "rr_total_ancillary": {
        "_target": {"sheet": "Rent Roll Analysis", "address": "AQ211+",
                    "label_at": "AQ210", "target_label": "Total Ancillary $",
                    "paste_anchor": "Rent Roll Analysis!A211",
                    "template_owned_formula": "=SUM(AK211:AO211)"},
        "_status": "derived",  # was gap_target
        "_notes": ("v5 added col AQ as a TEMPLATE-OWNED formula "
                   "`=SUM(AK:AO)`. Writer MUST NOT paste Analyzer col AH "
                   "values here — that would overwrite the formula. "
                   "Template re-derives from cols AK-AO which are writer-"
                   "populated."),
    },
}


def main() -> None:
    reg = json.loads(REG.read_text(encoding="utf-8"))

    if reg.get("registry_version", "0.0.0") >= "0.3.0":
        print(f"Registry already at v{reg['registry_version']} — no-op.")
        return

    # ── Header bumps ──────────────────────────────────────────────────────────
    reg["registry_version"] = "0.3.0"
    reg["generated_phase"] = (
        "Track 4 Phase 3 — UW Template v5 absorbed. Writer supports v4 + v5 "
        "via templates.{version} blocks; v5 is now the binding default."
    )
    # Substrate doesn't move with v5 (the v5 template changes don't require a
    # substrate bump). Keep v0.2.14.

    # ── Backfill v4 data_end_row ─────────────────────────────────────────────
    v4 = reg["templates"]["v4"]
    for k, val in V4_BACKFILL.items():
        v4.setdefault(k, val)
    v4["status"] = "supported (superseded by v5 as binding default)"

    # ── Add templates.v5 block ────────────────────────────────────────────────
    reg["templates"]["v5"] = V5_TEMPLATE

    # ── Apply per-concept v5 target overrides ────────────────────────────────
    by_key = {c["key"]: c for c in reg["concepts"]}
    updates = 0
    status_changes = []
    for key, spec in V5_TARGETS.items():
        if key not in by_key:
            print(f"  WARN: concept key {key!r} not found in registry — skipping")
            continue
        c = by_key[key]
        targets = c.setdefault("targets", {})
        targets["v5"] = spec["_target"]
        if "_status" in spec:
            old_status = c.get("status")
            c["status"] = spec["_status"]
            if old_status != spec["_status"]:
                status_changes.append((key, old_status, spec["_status"]))
        if "_status_v5" in spec:
            # v5-specific status — only meaningful if downstream tools learn to
            # read per-version status. For now, record in notes.
            pass
        if "_notes" in spec:
            existing = c.get("notes") or ""
            sep = " · " if existing else ""
            c["notes"] = f"{existing}{sep}v5: {spec['_notes']}"
        updates += 1

    # ── For all OTHER concepts, ensure they have an explicit v5 target ───────
    # (Inherit v4 unless explicitly overridden.) This keeps the registry
    # consistent: every concept has a target for each supported version, or
    # an explicit null.
    for c in reg["concepts"]:
        key = c["key"]
        if key in V5_TARGETS:
            continue
        targets = c.setdefault("targets", {})
        if "v5" in targets:
            continue
        # Inherit v4 verbatim — v5 didn't move this concept's target.
        targets["v5"] = targets.get("v4")

    # ── Resolve open questions that v5 closes ─────────────────────────────────
    closed_questions_prefixes = [
        "EBITDA row",  # gap closed
        "Occupied beds",  # gap closed
        "Preleased Date in template v5",  # gap closed (now lives at AR)
        "Monthly header cells",  # closed — v5 made them formula-driven
    ]
    before = len(reg.get("open_questions", []))
    reg["open_questions"] = [
        q for q in reg.get("open_questions", [])
        if not any(q.lstrip().startswith(p) for p in closed_questions_prefixes)
    ]
    after = len(reg["open_questions"])

    # ── Add a new note for what v5 explicitly didn't close ────────────────────
    deferred_questions = [
        ("Cover substrate version stamp — deferred to v5.1 per the 2026-05-26 "
         "release handoff. Concept `substrate_version` stays gap_target for now."),
        ("Rent Roll Analysis tab-header Period Date metadata cell — still pending "
         "in v5.1. Per-row Period Date (Analyzer col S) is not pasted; "
         "concept stays gap_target."),
    ]
    for q in deferred_questions:
        if q not in reg["open_questions"]:
            reg["open_questions"].append(q)

    # ── Write back ────────────────────────────────────────────────────────────
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Registry → v{reg['registry_version']}")
    print(f"  templates.v5 block added; v4 retained for backward compat")
    print(f"  {updates} concepts gained explicit v5 targets")
    print(f"  status changes:")
    for key, old, new in status_changes:
        print(f"    {key:40s}  {old:25s} → {new}")
    print(f"  open questions: {before} → {after} "
          f"({before - after + len(deferred_questions)} closed, "
          f"{len(deferred_questions)} added)")


if __name__ == "__main__":
    main()
