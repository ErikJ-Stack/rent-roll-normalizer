"""
Revert tools/uw_template/registry.json from v0.3.1 back to v0.3.0.

Triggered by the discovery that openpyxl's round-trip save on the v5
template silently dropped xl/metadata.xml (the dynamic-array XLDAPR /
fDynamic="1" block that the v0.4.3 Section R/S patch depends on) plus
xl/webextensions/ (the Claude-for-Excel add-in taskpane reference).

The v0.3.1 registry described template cells that no longer exist
(Cover!G1/H1 + RR Analysis B5 styled cell) because the template was
restored to git HEAD. Reverting concept statuses + version + closed
open_questions to match.

Idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools" / "uw_template" / "registry.json"


def revert():
    r = json.loads(REGISTRY.read_text())
    ops = []

    if r.get("registry_version") == "0.3.1":
        r["registry_version"] = "0.3.0"
        r["generated_phase"] = (
            "Track 4 Phase 3 — UW Template v5 absorbed. Writer supports v4 + v5 via "
            "templates.{version} blocks; v5 is now the binding default."
        )
        ops.append("registry_version 0.3.1 → 0.3.0")
    else:
        print(f"  · registry_version is {r.get('registry_version')!r} — no version revert")

    for c in r["concepts"]:
        key = c.get("key")

        if key == "substrate_version":
            if c.get("status") == "mapped":
                c["status"] = "gap_target"
                if "v5" in c.get("targets", {}):
                    c["targets"]["v5"] = None
                c["notes"] = (
                    "Template has no version-stamp cell. Recommend adding one (e.g. Cover!F1 "
                    "in template) so each populated copy carries provenance."
                )
                ops.append("substrate_version: mapped → gap_target (target removed)")

        elif key == "rr_period_date":
            if c.get("status") == "mapped":
                c["status"] = "proposed"
                c["notes"] = (
                    "Template's `Date:` cell at A5/B5 likely takes RR period. Confirm format expectations."
                )
                ops.append("rr_period_date: mapped → proposed")

        elif key == "t12_period_date":
            if c.get("status") == "derived_in_template":
                c["status"] = "gap_target"
                c["notes"] = (
                    "Template Layer 3 monthly header (B56:M56) is hardcoded Apr-25..Mar-26. "
                    "To respect the actual T12 period the writer would need to overwrite those "
                    "headers, or template needs a single period cell."
                )
                ops.append("t12_period_date: derived_in_template → gap_target")

    # Restore the 3 closed open_questions
    restore_open_qs = [
        "Date header at Rent Roll Analysis!A5 — does it expect RR period date in B5 or D5? Confirm format (yyyy-mm-dd vs Excel date).",
        "Cover substrate version stamp — deferred to v5.1 per the 2026-05-26 release handoff. Concept `substrate_version` stays gap_target for now.",
        "Rent Roll Analysis tab-header Period Date metadata cell — still pending in v5.1. Per-row Period Date (Analyzer col S) is not pasted; concept stays gap_target.",
    ]
    existing = r.get("open_questions", [])
    for q in restore_open_qs:
        already_present = any(q[:40] in e for e in existing)
        if not already_present:
            existing.append(q)
            ops.append(f"Restored open_question: {q[:60]}...")
    r["open_questions"] = existing

    if ops:
        REGISTRY.write_text(json.dumps(r, indent=2) + "\n")
        for op in ops:
            print(f"  ✓ {op}")
        print(f"\nRegistry reverted to v{r['registry_version']}.")
    else:
        print("No-op (registry already at target state).")

    status_count = {}
    for c in r["concepts"]:
        s = c.get("status", "?")
        status_count[s] = status_count.get(s, 0) + 1
    print(f"\nStatus rollup: {dict(sorted(status_count.items()))}")
    print(f"open_questions: {len(r.get('open_questions', []))}")


if __name__ == "__main__":
    revert()
