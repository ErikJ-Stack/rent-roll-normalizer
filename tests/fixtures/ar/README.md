# AR fixtures

Fixtures for `ar_normalizer.py` (Track 1, AR module). Used during parser
development and as regression anchors.

## Files

| File | Status | Purpose |
|---|---|---|
| `ar_synthetic_v01.xlsx` | **Synthetic** (committed) | Structural reference. 12 residents, 14 columns, headers chosen to exercise the fuzzy matcher. Not real operator data. |

## Live operator samples — PENDING

As of 2026-05-23, **no live AR aging sample has been received** from an
operator. The synthetic fixture above is the parser's only test anchor.

When a live sample lands:
- Drop it under `Sample Files/` (repo-root, **gitignored** — same rule as
  T12 fixtures per `CLAUDE.md`). Real property financials must not be
  committed.
- Expect to extend `ar_normalizer.HEADER_RULES` once you see real-world
  operator header variations. The synthetic was built against the spec's
  canonical column names; operator files in the wild will use other terms
  (e.g. "Outstanding" / "Bill Type" / etc.).
- After the parser cleanly handles one or two real samples, retire or
  shrink the synthetic and treat the live samples as the canonical
  fixtures.

## Synthetic fixture (`ar_synthetic_v01.xlsx`) — expected totals

The parser should compute these from `AR Aging` sheet:

| Bucket | Total |
|---|---:|
| Current (0-30) | 17,350 |
| 31-60 days | 7,250 |
| 61-90 days | 4,800 |
| 91-120 days | 2,400 |
| Over 120 days | 1,800 |
| **TOTAL AR** | **33,600** |
| 90+ subtotal | 4,200 |
| % aged 90+ | 12.50% |

Payer mix exercises all 7 `mappings.py` buckets including the v0.2.10
`Managed Care` addition (rows 107 / 111 / 112 → Medicare Advantage / MCO /
UHC MA Plan).
