"""
Update tools/uw_template/registry.json to v0.3.1.

Coupled to template v5.1 (the two metadata cells added by
_patch_v5_to_v51_metadata_cells.py):
  - substrate_version : gap_target → mapped (Cover!H1, label_at Cover!G1)
  - rr_period_date    : proposed → mapped (Rent Roll Analysis!B5)
  - t12_period_date   : gap_target → derived_in_template (B56:M56 = row 122
    in v5; no writer target needed)
  - registry_version  : 0.3.0 → 0.3.1
  - open_questions    : close #4, #7, #8

Idempotent — re-running on a v0.3.1 registry is a no-op.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools" / "uw_template" / "registry.json"


def patch():
    r = json.loads(REGISTRY.read_text())
    ops = []

    # 1. registry_version bump
    if r.get("registry_version") == "0.3.0":
        r["registry_version"] = "0.3.1"
        r["generated_phase"] = (
            "Track 4 Phase 3.5 — Template v5.1 metadata cells absorbed. "
            "Cover G1/H1 substrate version stamp + Rent Roll Analysis B5 RR period date. "
            "t12_period_date reclassified derived_in_template (v5 derives B56:M56 from on-sheet row 122)."
        )
        ops.append("registry_version 0.3.0 → 0.3.1")
    else:
        print(f"  · registry_version is {r.get('registry_version')!r} (not 0.3.0) — skipping bump")

    # 2. Concept updates
    for c in r["concepts"]:
        key = c.get("key")

        if key == "substrate_version":
            if c.get("status") == "gap_target":
                c["status"] = "mapped"
                c.setdefault("targets", {})
                c["targets"]["v5"] = {
                    "sheet": "Cover",
                    "address": "H1",
                    "label_at": "G1",
                }
                c["notes"] = (
                    "v5.1 added a substrate version stamp cell at Cover!H1 with adjacent "
                    "label at Cover!G1 ('Substrate:', italic gray 9pt). Writer populates "
                    "H1 from the Analyzer's Cover!B8 value (e.g. 'v0.2.14'). E1/F1 were "
                    "unavailable because A1:F1 is the merged title band."
                )
                ops.append(f"substrate_version: gap_target → mapped (Cover!H1, label_at G1)")
            else:
                print(f"  · substrate_version status is {c.get('status')!r} — skipping")

        elif key == "rr_period_date":
            if c.get("status") == "proposed":
                c["status"] = "mapped"
                c["notes"] = (
                    "v5.1 confirmed: Rent Roll Analysis!B5 is the RR Period (as-of) cell, "
                    "formatted mm/dd/yyyy. Writer populates from the Analyzer's RR_Period_Date "
                    "named range (resolves to Rent Roll Recon!B2). Sibling D5 (=TODAY()) "
                    "remains the diagnostic-refresh date and is left alone."
                )
                ops.append(f"rr_period_date: proposed → mapped (format confirmed mm/dd/yyyy)")
            else:
                print(f"  · rr_period_date status is {c.get('status')!r} — skipping")

        elif key == "t12_period_date":
            if c.get("status") == "gap_target":
                c["status"] = "derived_in_template"
                c["notes"] = (
                    "v5 derives the Layer 3 monthly headers (B56:M56) via formulas =C122..=N122 "
                    "from the on-sheet Layer 1 raw T-12 paste at row 122. Writer has no target "
                    "to write and doesn't need one — the template self-resolves. (Stale v4 note "
                    "describing hardcoded Apr-25..Mar-26 was misleading; v5 fixed structurally.)"
                )
                ops.append(f"t12_period_date: gap_target → derived_in_template (v5 self-resolves)")
            else:
                print(f"  · t12_period_date status is {c.get('status')!r} — skipping")

    # 3. Close open_questions #4, #7, #8
    # Identify by substring (positional indices are fragile)
    survivors = []
    closed = []
    for q in r.get("open_questions", []):
        is_q4 = "Date header at Rent Roll Analysis!A5" in q
        is_q7 = "Cover substrate version stamp" in q
        is_q8 = "Rent Roll Analysis tab-header Period Date metadata" in q
        if is_q4 or is_q7 or is_q8:
            closed.append(q[:80])
        else:
            survivors.append(q)
    if closed:
        r["open_questions"] = survivors
        ops.append(f"Closed {len(closed)} open_questions: " + " | ".join(c[:50] for c in closed))

    # Save
    if ops:
        REGISTRY.write_text(json.dumps(r, indent=2) + "\n")
        print("Applied:")
        for op in ops:
            print(f"  ✓ {op}")
        print(f"\nRegistry saved at v{r['registry_version']}.")
    else:
        print("No-op (registry already at target state).")

    # Status rollup
    status_count = {}
    for c in r["concepts"]:
        s = c.get("status", "?")
        status_count[s] = status_count.get(s, 0) + 1
    print(f"\nStatus rollup: {dict(sorted(status_count.items()))}")
    print(f"open_questions remaining: {len(r.get('open_questions', []))}")


if __name__ == "__main__":
    patch()
