"""
MF dashboard compute regression (mf_dashboard.compute_mf_dashboard).

Runs without pytest:  PYTHONPATH=. python tests/test_mf_dashboard.py

Uses the gitignored Hidden Lakes fixtures in `MF Docs/` (real operator data
per repo convention) — skips cleanly when absent. Anchors the institutional
metrics to values cross-checked against the parsed statements on 2026-06-12:
NOI ties the as-reported statement penny-exact; the income waterfall sums to
EGI; T-3 annualization uses the trailing three months × 4.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DOCS = ROOT / "MF Docs"
RR = DOCS / "RR-Hidden-Lakes-4-16-26-xlsx.xlsx"
T12 = DOCS / "T12-NOI-Hidden-Lakes-3-31-26-xlsx.xlsx"


def main() -> int:
    if not (RR.exists() and T12.exists()):
        print(f"SKIP: Hidden Lakes fixtures not found under {DOCS} (gitignored)")
        return 0

    from mf_normalizer import parse_mf_rr
    from mf_t12_normalizer import parse_mf_t12
    from mf_dashboard import compute_mf_dashboard

    rr = parse_mf_rr(RR.read_bytes())
    t12 = parse_mf_t12(T12.read_bytes())
    m = compute_mf_dashboard(rr, t12, purchase_price=20_000_000,
                             property_name="Hidden Lakes")

    checks = [
        ("units 143", m.units == 143),
        ("physical occ computed", m.physical_occ is not None and 0 < m.physical_occ < 1),
        ("GPR present", m.gpr is not None and m.gpr > 0),
        ("EGI = computed income", abs(m.egi - t12.computed["income"]) < 0.01),
        ("NOI ties computed", abs(m.noi - t12.computed["noi"]) < 0.01),
        ("NOI ties as-reported", m.noi_reported is None or abs(m.noi - m.noi_reported) < 1.0),
        ("waterfall sums to EGI",
         abs((m.net_rental or 0) + (m.other_income or 0) - m.egi) < 0.01),
        ("opex rows populated", len(m.opex_rows) >= 5),
        ("opex total = sum of rows",
         abs(sum(r.annual for r in m.opex_rows) - m.opex_total) < 0.01),
        ("unit mix covers all units", sum(r.count for r in m.unit_mix) == m.units),
        ("T-3 annualized = last 3 months x 4",
         m.t3_annualized_income is None
         or abs(m.t3_annualized_income - sum(m.monthly_income[-3:]) * 4) < 0.01),
        ("going-in cap = NOI / price", abs(m.going_in_cap - m.noi / 20_000_000) < 1e-9),
        ("price per unit", abs(m.price_per_unit - 20_000_000 / m.units) < 0.01),
        ("flags built", len(m.flags) >= 5),
        ("NOI-tie flag present",
         any("NOI ties" in f.label or "NOI does not tie" in f.label for f in m.flags)),
    ]
    failed = [label for label, ok in checks if not ok]
    for label, ok in checks:
        print(("  PASS " if ok else "  FAIL ") + label)
    if failed:
        print(f"=== {len(failed)} check(s) failed ===")
        return 1
    print("=== all checks passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
