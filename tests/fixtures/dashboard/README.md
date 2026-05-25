# Dashboard fixtures

Fixtures for `tests/test_dashboard_model.py` (Track 5, webapp dashboard
surface). Used as regression anchors against the bundled Analyzer's
`Dashboard` sheet `data_only=True` cached values.

## Fixture placement

Following the repo convention from `CLAUDE.md`:

| File | Status | Location |
|---|---|---|
| `regression_v0211.xlsx` | **Real operator data** (gitignored) | `Sample Files/dashboard/regression_v0211.xlsx` (repo root) |

The fixture is a **populated Analyzer** — one that has been through the
RR → T12 (→ AR) writer pipeline and then opened-and-saved in Excel so
the formula cache (`data_only=True`) is populated.

The initial development fixture was a Homestead Village populated
Analyzer:
`Analyzer with 2026-04-24 Homestead Village Rent Roll v2 + March 2026 T12 2026-04-24.xlsx`
copied into `Sample Files/dashboard/regression_v0211.xlsx`.

## What the test does

1. Reads `Rent Roll Input` cells (row 4 headers, rows 7+ data) →
   reconstructs a `NormalizeResult.condensed` DataFrame.
2. Reads `T12 Input` cells (row 11 month labels, rows 12+ GL detail)
   → reconstructs a `T12ParseResult.gl_rows` list.
3. Calls `compute_dashboard()` on the reconstructed inputs.
4. Compares each model field against the corresponding
   `Dashboard.<cell>.value` (cached Excel value).
5. Whitelists three known-divergence cells where the xlsx Dashboard has
   cross-reference bugs (`B6`, `F20`, `K6` — see `CHANGELOG-T5.md` for
   details).

## When fixture is absent

The test skips cleanly with `unittest.skipUnless` — no false negatives
in CI / dev environments that don't have the operator file on disk.

## Adding a new fixture

When you want to add coverage from a different deal:

1. Run the webapp on the new RR + T12 (+AR) → download the populated
   Analyzer.
2. **Open it in Excel and save** (this populates the formula cache).
3. Drop it in `Sample Files/dashboard/` with a descriptive name.
4. Add a new TestCase class in `tests/test_dashboard_model.py` keyed on
   the new fixture path. Bench-test thresholds may need adjusting if
   the new deal has substantially different ranges.
