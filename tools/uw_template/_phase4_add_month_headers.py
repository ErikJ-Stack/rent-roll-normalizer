"""
Track 4 / Phase 4 — registry extension: add 12 month-header concepts
(`t12_raw_month_1` through `t12_raw_month_12`) so the writer pulls
actual T-12 period months from the Analyzer instead of leaving
template hardcoded `Apr-25..Mar-26`.

WHY THIS EXISTS
  Operator-reported 2026-05-27: "header dates should be actual months
  and Year that's in the t12 raw data." Today the template's T-12
  Analysis row 122 (Layer 1 monthly headers) holds static strings
  `Apr-25`, `May-25`, ..., `Mar-26`. T-12 Analysis row 56 (Layer 3
  monthly headers) is formula-fed from row 122 via `B56=C122`,
  `C56=D122`, etc. — so propagating the actual months into row 122
  automatically updates row 56. The Analyzer's `T12 Input!C11:N11`
  already holds the real T-12 period months ("Apr 2025", "May 2025",
  ..., "Mar 2026") populated by the T12 normalizer.

  This script adds 12 scalar concepts to the registry that read each
  cell C11..N11 from T12 Input and write to C122..N122 on T-12
  Analysis. No writer code change — reuses the existing `cell` source
  system + scalar target write.

  This is the "cherry on top" piece of BL-0026 (T-12 Raw path). The
  larger Layer 1 raw GL paste remains blocked on operator direction
  pick (truncate / aggregate / template restructure), but the header
  row is independent and shippable now.

USAGE
  python tools/uw_template/_phase4_add_month_headers.py

  Idempotent — bails if registry already has `t12_raw_month_1`.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REG = ROOT / "registry.json"

# 12 month-header concepts, mapping Analyzer T12 Input row 11 cols C-N
# to UW Template T-12 Analysis row 122 cols C-N.
SOURCE_SHEET = "T12 Input"
SOURCE_ROW = 11
TARGET_SHEET_V4 = "T-12 Analysis"
TARGET_SHEET_V5 = "T-12 Analysis"
TARGET_ROW = 122
COL_LETTERS = ["C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
MONTH_LABELS = [
    "month 1 (T-12 start)", "month 2", "month 3", "month 4",
    "month 5", "month 6", "month 7", "month 8",
    "month 9", "month 10", "month 11", "month 12 (T-12 end)",
]


def main() -> None:
    reg = json.loads(REG.read_text(encoding="utf-8"))

    # Idempotency
    existing_keys = {c["key"] for c in reg["concepts"]}
    if "t12_raw_month_1" in existing_keys:
        print(f"Registry already has month-header concepts — no-op.")
        return

    # Build 12 concept entries
    new_concepts = []
    for i, (col, label) in enumerate(zip(COL_LETTERS, MONTH_LABELS), start=1):
        key = f"t12_raw_month_{i}"
        concept = {
            "key": key,
            "label": f"T-12 monthly header — {label}",
            "category": "t12_raw_headers",
            "path": "t12_raw",
            "source": {
                "system": "cell",
                "sheet": SOURCE_SHEET,
                "address": f"{col}{SOURCE_ROW}",
                "label": f"Analyzer {SOURCE_SHEET}!{col}{SOURCE_ROW} — operator's T-12 month header (e.g. 'Apr 2025')",
            },
            "targets": {
                "v4": None,
                "v5": {
                    "sheet": TARGET_SHEET_V5,
                    "address": f"{col}{TARGET_ROW}",
                    "label_at": f"A{TARGET_ROW}",
                    "target_label": f"Layer 1 header position {i} of 12",
                    "cascade_note": (
                        f"Row 122 monthly headers; auto-cascades to "
                        f"`T-12 Analysis!{COL_LETTERS[i-1] if i == 1 else chr(ord(col)-1)}56` "
                        f"via existing formula `={col}122` on row 56."
                    ),
                },
            },
            "status": "mapped",
            "notes": (
                "Operator-requested 2026-05-27 — header dates should reflect "
                "actual T-12 period months instead of template's hardcoded "
                f"'Apr-25' placeholders. Writer pastes Analyzer's T12 Input!"
                f"{col}{SOURCE_ROW} (the T12 normalizer-populated month header, "
                f"e.g. 'Apr 2025') into UW Template T-12 Analysis!{col}{TARGET_ROW}. "
                "Row 56's `={col}122` formula picks up the new value automatically. "
                "Independent of the broader BL-0026 Layer 1 raw GL paste."
            ),
        }
        new_concepts.append(concept)

    # Append to registry
    reg["concepts"].extend(new_concepts)

    # Add new category to legend if needed
    if "t12_raw_headers" not in reg.get("category_legend", {}):
        reg.setdefault("category_legend", {})["t12_raw_headers"] = (
            "T-12 raw header row — month labels propagated from Analyzer T12 "
            "Input row 11 to UW Template T-12 Analysis row 122. Auto-cascades "
            "to row 56's standardized-layer monthly headers via existing "
            "`={col}122` formulas."
        )

    # Bump registry version
    old_version = reg.get("registry_version", "0.4.0")
    reg["registry_version"] = "0.4.1"
    reg["generated_phase"] = (
        "Track 4 / Phase 4 — T-12 monthly headers added to registry. 12 new "
        "scalar concepts under path `t12_raw` propagate Analyzer T12 Input!"
        "C11:N11 (operator's actual T-12 period months) to UW Template "
        "T-12 Analysis!C122:N122. Row 56 (Layer 3 monthly headers) "
        "auto-updates via existing `={col}122` formula chain."
    )

    REG.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Registry → v{reg['registry_version']} (was v{old_version})")
    print(f"  + 12 month-header concepts added (path=t12_raw):")
    for c in new_concepts:
        src = c["source"]
        tgt = c["targets"]["v5"]
        print(
            f"    {c['key']:25s}  {src['sheet']}!{src['address']:6s}  "
            f"→  {tgt['sheet']}!{tgt['address']}"
        )
    print(f"  + category_legend extended with 't12_raw_headers'")


if __name__ == "__main__":
    main()
