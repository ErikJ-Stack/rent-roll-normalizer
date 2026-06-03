# MF COA → `_StdCOA` seed dictionary

> The seed for the future `mf_t12_normalizer` + `mf_mappings.py` COA dictionary
> (SPEC-MF §2.4 / §2.8). Built and validated 2026-06-03 against **5 real
> operator T-12 formats**. Source of truth = `coa_seed.csv` (emitted by
> `_seed_validate.py`); this doc explains it.

## Why this exists

The T-12 path's intelligence layer is classifying each raw GL line into a
`_StdCOA` bucket (the model's `T-12 Analysis` col P, which drives every Layer-3
SUMIFS). The parser does this with a layered resolver; this dictionary is its
seed, grown from every operator T-12 we've seen.

## The 5 formats seen so far (parser's format detector must handle all)

| Deal | Software | Acct #s | Month cols | Total col | Leaf signature |
| --- | --- | --- | --- | --- | --- |
| Hidden Lakes | PSI (flat) | yes (4-digit) | C–N contiguous | O | acct# + name + months |
| Blairstone | QuickBooks (nested P&L) | no | **odd** cols G–AC | AE | indent leaf in col E/F; skip `Total *` |
| Avana Stoney Ridge | **Yardi** (numbered) | yes (`#####-###`) | C–N | O | col B = `"#####-### - Name"`; skip name `Total*` |
| Ascend Brunswick | **Yardi / YSI** | yes (`#####-###`) | C–N | O | acct# col A, indented name col B; leaf = indent 5 |
| Copeland Village | Tzadik / AppFolio-style | no | B–M | N | name-only col A; skip `Total*` + section headers |

**Key win:** Avana + Ascend share the **identical Yardi standard chart** (41000
Market Rent, 41010 Gain/Loss, 41100 Vacancy, 51010 Mgmt Salaries, 61030 Mgmt
Fee, 62xxx Taxes, 63xxx Insurance, 70000–89999 below-the-line). One
account-number dictionary covers every Yardi property — the highest-leverage
tier.

## Dictionary structure (`coa_seed.csv`)

Three tiers, applied in order (account first, name fallback):

| `tier` | `key` | Meaning |
| --- | --- | --- |
| `acct_root` | 5-digit root (e.g. `41100`) | Exact Yardi account → bucket. 199 rules. |
| `acct_range` | `70000-89999` | Any account in range → `— EXCLUDED (non-OpEx) —` (routine replacements, capital/renovation, non-operating, lease-up, D&A — below the NOI line). |
| `name_regex` | pattern | Name fallback for charts without numbers (Copeland, Blairstone) — ordered specific → generic. 43 rules. |

## Validation (coverage)

`python tools/mf_uw_template/_seed_validate.py` applies the seed to the real
files and reports coverage. Current result — **100% of GL leaf lines classified
on all three numbered/named samples**:

```
AVANA (Yardi):       156 leaves | mapped 156 (100%)
ASCEND (Yardi/YSI):  161 leaves | mapped 161 (100%)
COPELAND (Tzadik):    65 leaves | mapped  65 (100%)
```

Plus the two earlier hand-mapped samples (Hidden Lakes PSI via `_StdCOA` col F;
Blairstone QuickBooks). Coverage = "every line maps to *a* bucket." Bucket
*correctness* was assigned by inspection; the parser's integration test (income
vs expense section reconciliation to Total Income / NOI) is the next gate — see
caveats.

## Caveats / judgment calls baked into the seed

- **Utility rebills** (`*-Rebill`, `Reimbursement`) → `Utility Reimbursement`.
  These appear as **positive income** on Yardi income rows AND as **negative
  contras** inside the expense section. The bucket is right either way, but the
  parser must reconcile by **source section**, not bucket alone, to land EGI vs
  opex correctly.
- **Below-NOI** (Yardi 70000–89999: replacements, capital, lease-up, D&A,
  partnership) → `— EXCLUDED —`. Must not hit opex.
- **Non-revenue units:** `Employee`/`Courtesy Officer` → Employee Units;
  `Model`/`Office`/`Storage` units → Down Units Loss (judgment — both are
  intentional non-revenue allocations).
- **Make-Ready vs R&M:** turn-coded lines (paint contractor, carpet
  clean/repair, tub refinish, unit clean, drywall, housekeeper) → Make-Ready /
  Turnover; everything else under repairs → R&M.
- **Entity-level lines missing:** several deals have **no Management Fee** and/or
  **near-zero Real Estate Tax** (Copeland RE Tax = $4.61; Blairstone has
  neither) — paid at the entity level. Underwriting needs pro-forma inputs.
- **Anomaly to review:** Copeland `Dues` = **$539,712.92** under Office & Admin
  is implausibly large for dues — likely a misposted management fee or owner
  allocation. Mapped to G&A for coverage but **flagged for the analyst**.

## Next step

Promote this seed into `mf_mappings.py` when the parser build starts
(SPEC-MF §2.8 first slice). The 5 deals here are the parser's regression-fixture
set (synthetic copies committed under `tests/fixtures/`; the real files stay
local in the deal folders). `_seed_validate.py` is a local prototype harness —
it reads gitignored deal files by absolute path and is **not** the production
parser.
