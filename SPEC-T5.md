# SPEC-T5.md — Webapp Dashboard Surface (Track 5)

> Track 5 specification — surfacing the Analyzer's `Dashboard` sheet data
> inside the Streamlit webapp as a mobile-friendly tab, rendered before /
> without the user opening the downloaded xlsx in Excel.
>
> **Status:** v0.1.0 (initial release).
> **Current code version:** T5 v0.1.0.
> **Target Analyzer substrate:** v0.2.11.

---

## 1. Where this fits

Track 5 sits **between the writer pipeline and the download** — the
Streamlit app already parses RR + T12 + AR and produces a populated
Analyzer; Track 5 reads the in-memory parse results and renders an
analyst-facing dashboard before the user downloads anything.

```
RR upload (Track 1) → NormalizeResult ─┐
T12 upload (Track 2) → T12ParseResult ─┼─→ compute_dashboard() ─→ DashboardModel ─→ render_dashboard()
AR upload (optional) → AROutput ───────┘                                                  │
                                                                                          ▼
                                                                              Streamlit "📊 Dashboard" tab
```

The Dashboard tab is shown alongside the existing Download tab:
`st.tabs(["📊 Dashboard", "⬇️ Download"])`. The download flow is unchanged
— the xlsx still ships with its native `Dashboard` sheet, charts, and
formula layer. Track 5 is **additive**.

## 2. Module shape

| File | Role |
| --- | --- |
| `dashboard_model.py` | Pure Python — `compute_dashboard(rr_result, t12_result, ar_result=None, ...) -> DashboardModel`. Mirrors the xlsx Dashboard's underlying T12 Analytics formulas in Python. No Streamlit imports. |
| `dashboard_ui.py` | Streamlit-only — `render_dashboard(model)`. Mobile-friendly single-scroll layout. No business logic. |
| `tests/test_dashboard_model.py` | Regression: reconstructs RR + T12 inputs from a populated Analyzer fixture, calls `compute_dashboard()`, asserts each metric matches the xlsx's `data_only=True` cached values. |
| `tests/fixtures/dashboard/README.md` | Documents where to drop a populated Analyzer fixture (gitignored). |

`app.py` is the integration seam — adds `from dashboard_model import compute_dashboard` + `from dashboard_ui import render_dashboard`, wraps the existing post-parse Export section in `st.tabs(["📊 Dashboard", "⬇️ Download"])`.

## 3. Why pure Python (not a formula evaluator)

openpyxl cannot evaluate Excel formulas — reading `data_only=True` on a
Python-written workbook returns `None` for every formula cell. The xlsx
`Dashboard` is itself a formula-reference layer over `T12 Analytics`,
which aggregates `T12 Raw Data` (per-Description_Map-label sums) and
`Rent Roll Recon` (per-care-type bed counts + payer mix). Three paths
were considered:

1. **Add `formulas` or `pycel` dependency + recalc** — heavy dep on
   Streamlit Cloud; library quirks across the formula surface; slow.
2. **Subprocess LibreOffice headless to recalc** — won't run on
   Streamlit Cloud; ~5-10 sec per render; no interactivity.
3. **Re-derive metrics in Python** ← chosen. Bounded scope (~60 metrics,
   simple arithmetic over already-parsed `NormalizeResult` +
   `T12ParseResult` + `AROutput`). Zero new dependency. Testable.

Drift guard: the regression test against the populated-Analyzer fixture
catches divergence in either direction (Python or xlsx).

## 4. What the model computes

The `DashboardModel` dataclass has 44 fields organized into sections
mirroring the xlsx Dashboard's layout:

- **Headline tiles:** occupancy %, EBITDARM margin, going-in cap, RevPOR,
  EGI, EBITDAR, EBITDARM, price/bed.
- **Capacity & occupancy:** licensed beds (IL/AL/MC/total), occupied beds.
- **Revenue & rate:** GPR, blended ADR, RevPAB, LOC %, bad debt %,
  loss-to-lease %, vacancy %.
- **Profitability:** EBITDAR margin, EGI/opex per occupied bed, total opex.
- **Cost structure & labor:** total/direct labor % of EGI, overtime %,
  agency %, food PPD, mgmt fee %, P&C insurance %.
- **Valuation:** purchase price, EBITDAR cap.
- **Payer mix:** 7-payer table (count, % census, revenue, % revenue).
- **Care type breakdown:** IL/AL/MC + Blended rows.
- **Monthly EGI trend:** 12-month series.
- **Risk flags:** 7 indicators with ✅/⚠️/❌ status.
- **AL care level distribution** + optional **AR bad debt variance**.

The aggregation mirrors T12 Analytics col E:
`INDEX('T12 Raw Data'!R:R, MATCH("<Label>", 'T12 Raw Data'!B:B, 0))`
becomes a Python `totals[label] += row.total` over GL rows grouped by
their Description_Map label. The 24 non-labor labels, 8 direct-labor
labels, and 6 payroll-burden labels are constants in `dashboard_model.py`
matching the T12 Analytics layout.

## 5. Mobile-friendly rendering

The UI uses Streamlit primitives that reflow on narrow viewports:

- **Tiles:** `st.columns(2)` of `st.metric` (narrows but stays legible).
- **Tables:** `st.dataframe(..., use_container_width=True, hide_index=True)`.
- **Charts:** Altair via `st.altair_chart(..., use_container_width=True)`
  (donuts for payer mix and AL care level, bar chart for monthly EGI).
- **Risk flags:** `st.success/warning/error/info` per indicator —
  high-contrast colored alert boxes that work on small screens.
- **Layout:** single scrollable page (no nested tabs); section headers
  via `st.subheader` + `st.divider`.

## 6. Known xlsx Dashboard cross-reference bugs (Python correct)

Discovered during Track 5 build. Three Dashboard headline tiles in the
bundled v0.2.11 substrate reference single-care-type cells while being
labeled as blended/community values:

| Cell | Label on Dashboard | Pulls from | Actual content |
| --- | --- | --- | --- |
| `B6` | "Normalized community occupancy" | `T12 Analytics!F134` (`=C11/C6`) | **AL-only** occupancy |
| `F20` | "Blended ADR / day" | `T12 Analytics!F140` (`=D20/(D11*12)`) | **MC-only** ADR |
| `K6` | "Normalized RevPOR per resident" | `T12 Analytics!F143` (`=(D20+D27)/(D11*12)`) | **MC-only** RevPOR |

The Python model computes **structurally correct blended values**; the
regression test whitelists these three cells. A Track 3 substrate fix is
queued (separate spawned task) to rewrite Dashboard cross-refs to the
correct blended cells. Once the substrate fix lands, both the webapp
Dashboard tab and the downloaded xlsx Dashboard will show the same
(correct) numbers.

## 7. Versioning

T5 has its own version counter (`T5_VERSION` = `0.1.0`), independent of
RR / T12 / AR / substrate counters. The dashboard model is forward-
compatible with substrate v0.2.10+ (needs the AR module's `Z1` cell for
the AR variance tile; falls back cleanly when AR not uploaded).

## 8. Out of scope (Phase 0)

- **Purchase price input in the UI** — currently `purchase_price=None`
  is passed to `compute_dashboard()`. The xlsx's `T12 Analytics!E117`
  is still the analyst input. Future: add a sidebar `st.number_input`
  for purchase price, pipe through to the model for cap-rate tiles.
- **AR module visible inside the Dashboard tab** — currently
  `ar_result=None` is passed (the AR file is parsed later, only at
  download time). Future: lift AR parse up so the Dashboard tab can
  show the bad-debt variance immediately.
- **Per-resident drill-down** — current model is aggregate-only.
- **Custom benchmark thresholds** — risk-flag thresholds are
  hardcoded in `dashboard_ui.py` matching the xlsx Dashboard's
  values. Future: source from a config sheet for analyst override.
