"""
Absorb v5.1's K211/L211 template-formula additions.

User-reported (2026-05-27): v5.1 added 6 template formulas to row 211+ on
Rent Roll Analysis. Three of those (K211, L211, V211) hit cells that were
previously writer-paste targets:

  - K211: =IFERROR(IF(A211="","",N(AE211)+N(AF211)+N(AG211)+N(AH211)),0)
          ↳ Total LOC $ summed from per-fee ancillary cols
          ↳ rr_total_loc concept used to paste-value Analyzer's `Rent Roll Input!T` here

  - L211: =IFERROR(IF(A211="","",N(J211)+N(K211)),0)
          ↳ Total Sched (Actual Rate + Total LOC)
          ↳ rr_total_monthly_rev concept used to paste-value Analyzer's `Rent Roll Input!U` here

  - V211: =IFERROR(IF(OR(A211="",U211="",U211=0,J211=""),"",J211/U211),"")
          ↳ Actual PSF = Actual Rate / SqFt
          ↳ rr_actual_psf concept used to paste-value Analyzer's `Rent Roll Input!AA` here

Now that the template owns the formula at K/L, the writer must NOT overwrite
them with a paste-value (would lose self-recompute semantics). Reclassify
both concepts: mapped → derived. The `derived` status is in
`_DEFAULT_SKIP_STATUSES`, so writer skips automatically. Matches the existing
precedent of `rr_total_ancillary` (which became derived in v0.4.0 when v5
added the `=SUM(AK:AO)` formula at AQ).

Other v5.1 row-211 additions (V/W/AA/AB) are already-derived cells that the
registry's `intake_targets_unmapped` block lists as "do not overwrite" — no
registry change needed for those.

Idempotent — re-running on a v0.4.2 registry is a no-op.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools" / "uw_template" / "registry.json"


def absorb():
    r = json.loads(REGISTRY.read_text())
    ops = []

    if r.get("registry_version") == "0.4.1":
        r["registry_version"] = "0.4.2"
        r["generated_phase"] = (
            "Track 4 v0.4.2 — v5.1 K211/L211 template-formula absorption. "
            "rr_total_loc + rr_total_monthly_rev moved mapped → derived (template "
            "owns the formula now, writer skips)."
        )
        ops.append("registry_version 0.4.1 → 0.4.2")

    for c in r["concepts"]:
        key = c.get("key")

        if key == "rr_total_loc":
            if c.get("status") == "mapped":
                c["status"] = "derived"
                old_notes = (c.get("notes") or "").strip()
                c["notes"] = (
                    "v5.1 template added formula `=IFERROR(IF(A{r}=\"\",\"\","
                    "N(AE{r})+N(AF{r})+N(AG{r})+N(AH{r})),0)` at K211+, "
                    "computing Total LOC from per-fee ancillary cols. Writer "
                    "must skip — template self-derives at populate-time from "
                    "writer-pasted per-fee values. Status: mapped → derived."
                )
                if old_notes:
                    c["notes"] += f" · Prior note: {old_notes}"
                ops.append("rr_total_loc: mapped → derived (template owns K211 formula)")

        elif key == "rr_total_monthly_rev":
            if c.get("status") == "mapped":
                c["status"] = "derived"
                old_notes = (c.get("notes") or "").strip()
                c["notes"] = (
                    "v5.1 template added formula `=IFERROR(IF(A{r}=\"\",\"\","
                    "N(J{r})+N(K{r})),0)` at L211+, computing Total Sched "
                    "(Actual Rate + Total LOC). Writer must skip — template "
                    "self-derives at populate-time. Status: mapped → derived."
                )
                if old_notes:
                    c["notes"] += f" · Prior note: {old_notes}"
                ops.append("rr_total_monthly_rev: mapped → derived (template owns L211 formula)")

        elif key == "rr_actual_psf":
            if c.get("status") == "mapped":
                c["status"] = "derived"
                old_notes = (c.get("notes") or "").strip()
                c["notes"] = (
                    "v5.1 template added formula `=IFERROR(IF(OR(A{r}=\"\","
                    "U{r}=\"\",U{r}=0,J{r}=\"\"),\"\",J{r}/U{r}),\"\")` at "
                    "V211+, computing Actual PSF = Actual Rate / SqFt per row. "
                    "Writer must skip — template self-derives at populate-time. "
                    "Status: mapped → derived. (Analyzer's own AA column "
                    "remains unused on this target; downstream consumers read "
                    "the template's computed value.)"
                )
                if old_notes:
                    c["notes"] += f" · Prior note: {old_notes}"
                ops.append("rr_actual_psf: mapped → derived (template owns V211 formula)")

    if ops:
        REGISTRY.write_text(json.dumps(r, indent=2) + "\n")
        for op in ops:
            print(f"  ✓ {op}")
        print(f"\nRegistry now at v{r['registry_version']}.")
    else:
        print("No-op (registry already at target state).")

    from collections import Counter
    cnt = Counter(c['status'] for c in r['concepts'])
    print(f"\nStatus rollup: {dict(sorted(cnt.items()))}")


if __name__ == "__main__":
    absorb()
