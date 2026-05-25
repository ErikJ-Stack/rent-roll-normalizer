# CHANGELOG-T5 — Webapp Dashboard Surface (Track 5)

Per-release notes for the webapp dashboard track. Newest at top.

See [SPEC-T5.md](SPEC-T5.md) for the canonical spec.

---

## v0.1.2 — UI polish: currency input, headline box, compressed sidebar (2026-05-24)

Three UX polish changes following walkthrough of v0.1.1:

- **Currency-formatted purchase price.** Sidebar input is now a
  `st.text_input` with a `_parse_currency()` helper that accepts
  `$18,000,000`, `18000000`, `18,000,000`, or shorthand `18M` / `500K`.
  A `💰 **$18,000,000**` confirmation caption renders underneath when
  the parsed value is > 0. Smoke-tested against 12 input shapes.
- **Headline panel boxed in.** `_render_headline()` now wraps its
  metric tiles in `st.container(border=True)` with a centered
  "HEADLINE" eyebrow label, splits into two row-groups (must-see
  ratios above an `st.divider()`, financial-scale tiles below). Reads
  as a hero panel instead of just-another-section.
- **Sidebar compressed.** Removed `Property Defaults`, `Optional`,
  `Output` subheaders and the 5 dividers between them. New structure:
  `📁 Uploads` group (everything file-shaped), `💵 Underwriting` group
  (purchase price + care type default), `⚙️ Advanced` expander
  (collapsed by default — combines the RR sheet-name override, RR
  mapping override, and Analyzer template override into one place).
  Drops ~30% of sidebar vertical space on a 13" laptop.

### Files

- `app.py` — sidebar restructure, `_parse_currency()` module-level
  helper, `T5_VERSION` bumped to `0.1.2`.
- `dashboard_ui.py` — `_render_headline()` boxed via
  `st.container(border=True)`.

### Verification

- `python3 -m unittest tests.test_dashboard_model` → **27 / 27 pass**.
- Currency parser smoke: 12/12 input shapes parse as expected (incl.
  empty, garbage, whitespace, `$` prefix, comma thousands, `M`/`K`
  shorthand, decimal-M).

---

## v0.1.1 — Top-level Dashboard / Workspace tabs + purchase price input (2026-05-24)

Two UX changes following live walkthrough of v0.1.0:

- **Top-level switch tabs.** `st.tabs(["📊 Dashboard", "🛠️ Workspace"])` now
  sits directly under the "Underwriting Intake" title. The Dashboard tab is
  a clean slate — only the dashboard renders, no analyst review tables, no
  parsing UI, no download buttons cluttering the view. The Workspace tab
  holds everything else (RR + T12 + AR upload review, analyst sub-tabs,
  Export downloads). v0.1.0's bottom-of-page nested `[Dashboard, Download]`
  tabs are removed; downloads are now a flat `Export` section inside the
  Workspace tab.
- **Purchase price input** (`st.number_input`) added to the sidebar under
  a new "Underwriting Inputs" section. Pipes through `compute_dashboard()`
  as `purchase_price=<value>` so the **Going-in cap rate**, **EBITDAR cap**,
  and **Price / bed** tiles populate without the analyst needing to open
  the downloaded xlsx and set `T12 Analytics!E117`. Leave at 0 for the
  default behavior (cap-rate tiles dim).

### Files

- `app.py` — restructured: top-level tabs after title, all main-pane
  content wrapped in `with top_tab_workspace:`, clean dashboard render in
  `with top_tab_dashboard:` at the very end (uses vars defined inside the
  workspace block since Python `with` doesn't create scope). New sidebar
  section "Underwriting Inputs" with `purchase_price_input`. `T5_VERSION`
  bumped to `0.1.1`.

### Verification

- `python3 -m unittest tests.test_dashboard_model` → **27 / 27 pass**.
- `ast.parse(app.py)` → clean.

---

## v0.1.0 — Initial release: in-app Dashboard tab (2026-05-24)

Track 5 seed release. Surfaces the same data as the bundled Analyzer's
`Dashboard` sheet inside the Streamlit webapp as a mobile-friendly tab,
rendered without the user needing to open the downloaded xlsx in Excel.

### Shipped

- **`dashboard_model.py`** — pure-Python compute layer.
  `compute_dashboard(rr_result, t12_result, ar_result=None, ...) -> DashboardModel`.
  44-field dataclass covering headline tiles, capacity, revenue, profitability,
  cost structure, valuation, payer mix, care-type breakdown, monthly EGI
  series, risk flags, AL care level distribution, and AR variance text.
  Re-implements the T12 Analytics col-E aggregation pattern in Python
  (`totals[label] += row.total` over GL rows mapped through Description_Map),
  avoiding the openpyxl-can't-evaluate-formulas trap.
- **`dashboard_ui.py`** — Streamlit-only renderer. `render_dashboard(model)`.
  Mobile-first single-scroll layout: `st.metric` tiles in `st.columns(2)`
  (auto-narrows on phones), `st.dataframe(use_container_width=True)` for
  tables, Altair donut + bar charts via `st.altair_chart(use_container_width=True)`,
  `st.success/warning/error` for risk flags.
- **`app.py`** — wraps the existing post-parse export section in
  `st.tabs(["📊 Dashboard", "⬇️ Download"])`. Dashboard tab calls
  `compute_dashboard` + `render_dashboard`. Download tab holds the
  unchanged RR + combined-Analyzer download buttons. New imports:
  `dashboard_model.compute_dashboard`, `dashboard_ui.render_dashboard`,
  `property_name.derive_property_name` (hoisted from inline).
- **`tests/test_dashboard_model.py`** — 27-case regression suite.
  Reconstructs `NormalizeResult` + `T12ParseResult` from a populated
  Analyzer fixture's `Rent Roll Input` + `T12 Input` cells, runs
  `compute_dashboard()`, asserts each metric matches the xlsx's
  `data_only=True` cached values within tolerance. All 27 pass on the
  Homestead Village fixture (RR 2026-04-24 + March 2026 T12).
- **`tests/fixtures/dashboard/README.md`** — fixture-placement
  convention (populated Analyzer goes in `Sample Files/dashboard/`,
  gitignored).
- **`SPEC-T5.md`** + **this CHANGELOG**.

### Known xlsx Dashboard cross-reference bugs (Python is correct)

Discovered during the regression-test run. Three Dashboard cells in the
bundled v0.2.11 substrate reference single-care-type cells in T12
Analytics while being labeled as blended/community values on the
Dashboard:

| Dashboard cell | Labeled as | Pulls from | Should reference |
| --- | --- | --- | --- |
| `B6` | "Normalized community occupancy" | `T12 Analytics!F134` (=C11/C6, **AL-only**) | a blended (E11/E6) cell |
| `F20` | "Blended ADR / day" | `T12 Analytics!F140` (=D20/(D11*12), **MC-only**) | a blended (E16/(E11*12)) cell |
| `K6` | "Normalized RevPOR per resident" | `T12 Analytics!F143` (=(D20+D27)/(D11*12), **MC-only**) | a blended ((E16+E23)/(E11*12)) cell |

Homestead fixture impact:
- Occupancy: xlsx shows 64.5% (AL-only), Python shows 72.7% (blended, correct).
- ADR: xlsx shows $6,802 (MC-only), Python shows $4,546 (blended, correct).
- RevPOR: xlsx shows $6,802 (MC-only), Python shows $4,562 (blended, correct).

The Python model computes structurally-correct blended values. The
regression test whitelists these three cells with explicit "known
divergence" tests. A Track 3 substrate-side fix is queued as a separate
worktree task — when it lands, the webapp Dashboard tab and the
downloaded xlsx Dashboard will align.

### Known limitations (deferred to v0.2.0)

- **Purchase price** is not yet wired through the UI (`purchase_price=None`
  is passed to `compute_dashboard()`). Cap-rate tiles show "—" until the
  analyst sets `T12 Analytics!E117` in the downloaded xlsx. A sidebar
  `st.number_input` for purchase price is a small follow-up.
- **AR module** is not yet visible inside the Dashboard tab — the AR
  file is parsed later, only at download time. The AR variance tile
  (`ar_bad_debt_variance` field) is present in the model but renders as
  `None` until AR parsing is lifted up.
- **No per-resident drill-down** — the model is aggregate-only by design.

### Verification

- `python3 -m unittest tests.test_dashboard_model` → **27 tests pass**.
- `python3 -c "import ast; ast.parse(open('app.py').read())"` → app.py
  parses cleanly with the new tab wiring.
- Manual smoke against the bundled Analyzer + Homestead Village
  populated fixture: every metric matches the xlsx within 0.5% relative
  tolerance except the three known-divergence cells documented above.

### Carry-forwards

- Live deploy verification (Streamlit Community Cloud reboot after
  push) — pending.
- The spawned Track 3 task for the Dashboard cross-reference bugs
  (B6/F20/K6) — pending.
- Optional `st.dialog` modal variant — explicitly NOT shipped per user
  guidance (mobile readability priority means full-tab beats modal).
