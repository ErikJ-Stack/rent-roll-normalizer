# CHANGELOG-UWT — ALF UW Template Integration (Track 4)

Per-release notes for the UW Template integration track. Newest at top.

See [SPEC-UWT.md](SPEC-UWT.md) for the canonical spec; the rollup of pending
work for this track lives in [UW-BACKLOG.md](UW-BACKLOG.md) once items are
opened (none yet — Phase 0 is the seed release).

---

## v0.4.2 — Phase 2.5 follow-up: bundled template + override pattern (2026-05-26)

User feedback after v0.4.1 ship: "I don't see a download for ALF UW
Template" — the v0.4.1 pattern required uploading a template every
session to get a populated copy, which is friction the Analyzer doesn't
have. v0.4.2 mirrors the Analyzer's load pattern exactly: bundled by
default, override under Advanced.

### Shipped (app.py changes only — no API change to writer)

- **New constants**:
  - `BUNDLED_UW_TEMPLATE_PATH = Path(__file__).parent / "assets" / "ALF_UW_Template_v5.xlsx"`
  - `BUNDLED_UW_TEMPLATE_VERSION = "v5"`
- **New helper `_load_uw_template(uploaded_file)`** — mirrors
  `_load_analyzer()`. Returns `(template_bytes, source_label,
  template_version)`. Upload wins; falls back to the committed asset.
  Raises `FileNotFoundError` with a clear message if neither exists.
- **New helper `_detect_uw_template_version(template_bytes)`** —
  best-effort version detection. Probes `Rent Roll Analysis!AP210`
  (v5's "Care Level Tier" header that doesn't exist in v4). Falls back
  to `"v5"` on any error (file not openable, missing sheet, etc.).
  Uses `read_only=True` for fast load — no full workbook parse.
- **Sidebar restructure**:
  - **Removed** the standalone "UW Template (.xlsx) — optional"
    file_uploader between the AR section and the Underwriting section.
  - **Promoted** the scenario radio to always-visible (was conditional
    on `uw_template_file is not None` in v0.4.1). Now reads "UW Template
    scenario" with the same help text. Lives at the same sidebar
    position the uploader used to occupy.
  - **Added** a "UW Template override (.xlsx)" file_uploader in the
    Advanced expander, immediately after the existing "Analyzer template
    override" — parallel placement, parallel help text ("Upload to
    override for this session only").
  - **Sidebar version footer** extended:
    `RR v{RR_VERSION} · T12 v{T12_VERSION} · AR v{AR_VERSION} · T5
    v{T5_VERSION} · UWT v{UWT_VERSION}` (UWT was missing in v0.4.1).
- **Workspace populate flow restructure**:
  - Removed the `if uw_template_file is not None:` outer guard.
    Populate now fires unconditionally on every successful Analyzer
    build (i.e. when `can_download` is True).
  - Calls `_load_uw_template(uw_template_override_file)` up front to
    resolve the source.
  - New "Using UW Template: **<source>** (`<version>`)" caption appears
    immediately under the section header — mirrors the existing "Using
    Analyzer: ..." caption pattern.
  - `populate_uw_template()` call now passes the resolved
    `template_version` explicitly instead of relying on the default
    (the helper returns `v5` for bundled, `v4` or `v5` for override per
    auto-detection).

### UX impact

Operator's flow changes from:

  - **v0.4.1**: "I uploaded an RR + T12 but I don't see a UW Template
    download" (because the upload was never done).

To:

  - **v0.4.2**: RR upload → Analyzer download + populated UW Template
    download both appear automatically. To use a non-default template
    (legacy v4 / v5.1 candidate / per-deal customization), expand
    Advanced and upload an override.

### Version auto-detection notes

`_detect_uw_template_version()` is intentionally lightweight — single
cell probe at `Rent Roll Analysis!AP210`. v5 has "Care Level Tier"
there; v4 doesn't (cols AP-AR didn't exist before v5). The fallback
to v5 on any error is deliberate — v5 is the binding default and the
registry's primary supported version. A user uploading a corrupted or
non-ALF .xlsx will get a writer error downstream rather than crash here.

### Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` — parses
  clean at 1,523 lines (was 1,456 in v0.4.1; +67 LOC for the helpers +
  caption + sidebar restructure).
- `tests/test_uw_template_writer.py` — both smoke + Homestead e2e
  still pass on the writer module (writer didn't change; only the
  caller pattern changed).
- The `_detect_uw_template_version()` probe was sanity-checked against
  the committed `assets/ALF_UW_Template_v5.xlsx` (returns `"v5"`) and
  conceptually against a v4 (`Sample Files/ALF_UW_Template_v4.xlsx`
  has no AP210 header → returns `"v4"`).

### Out of scope (unchanged from v0.4.1)

- **In-Python formula evaluator** for the cache caveat — still pending.
- **v5.1 template completions** (Cover substrate stamp + RR Analysis
  tab-header Period Date).
- **BL-0026 — T-12 Raw path** — still deferred.
- **AR row-level routing**.

### Versioning

- UWT code version: **v0.4.2** (Phase 2.5 follow-up).
- Mapping registry version: **0.3.0** (unchanged).
- Template versions supported: **v4** + **v5** (v5 default; auto-detected
  from `Rent Roll Analysis!AP210`).
- Bundled template path: `assets/ALF_UW_Template_v5.xlsx`.
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.4.1 — Phase 2.5: Streamlit UI integration (2026-05-26)

Closes the user-experience gap that's been open since Phase 2. The writer
module exists and works end-to-end, but until this release the operator
had to either (a) paste-values manually per the contract's intended motion
or (b) run `python uw_template_writer.py` via CLI. Now: upload the UW
Template in the sidebar, get a populated copy as a second download
alongside the Analyzer.

### Shipped (app.py changes only — no API change)

- **Sidebar** — new file_uploader `"UW Template (.xlsx) — optional"`
  positioned after the AR uploader + as-of-date block. When the analyst
  uploads, a horizontal radio appears below for scenario selection
  (`normalized` default / `t12_actual`). The radio renders only when a
  template is uploaded.
- **Workspace tab** — after the existing combined-Analyzer download
  button, a new `📋 Populate UW Template` section appears (gated on
  `uw_template_file is not None`). It:
  1. Reads the uploaded template bytes.
  2. Calls `populate_uw_template(final_bytes, uw_template_bytes,
     scenario=...)` — the just-built Analyzer bytes are the source.
  3. Builds a per-deal filename via `derive_property_name(rr_file.name)`:
     `<Property>_UW_Template_<RR period>_<scenario>.xlsx`. Property name
     sanitized (alphanumerics + space/dash/underscore only; spaces → `_`).
  4. Surfaces a one-line summary caption: "Writer populated **{N} of
     {total}** concepts ({cells:,} cells). Scenario: `{scenario}`."
  5. Drill-in expander `🔍 Populate report (details)` — auto-expanded on
     warnings; shows warnings + outcome counts + per-error notes.
  6. Emits the populated-template download button.
  7. **Cache caveat info banner**: when any t12-path concept comes through
     as `no_source`, surfaces an `st.info` walking the analyst through
     the round-trip-through-Excel workaround (download Analyzer → open
     in Excel → save → re-upload via Advanced expander's "Analyzer
     template override" → re-download). Surfaces the openpyxl-doesn't-
     compute-formulas reality clearly instead of leaving them confused.
- **Constants**: `UWT_VERSION = "0.4.1"` + `UWT_LAST_UPDATED =
  "2026-05-26"` added alongside the existing track version constants.
  `RR_VERSION` bumped `"1.18.0"` → `"1.18.1"` (was lagging behind the
  RR v1.18.1 writer shipped earlier the same day — `ANALYZER_SUBSTRATE_VERSION`
  was already at `"0.2.14"` so the constants now agree across the board).
- **Error surfacing**: catches `UWTemplateWriterError` for clean
  reporting; falls back to generic `Exception` with `st.error` for
  unanticipated failures (matches the pattern used by the existing
  RR/T12/AR error handlers above it).

### Design choices

- **Operator uploads the template each session** rather than bundling
  v5 in the repo. Trade-off: one extra file upload per session, but
  zero infra and the operator can swap template versions easily when
  v5.1 ships.
- **Radio for scenario** (not multi-write). Writing both columns would
  double the cell churn for marginal value; analysts can re-run with
  the alternate scenario when needed.
- **Inline summary + drill-in expander** rather than a results page.
  The summary tells you what happened in one line; the expander surfaces
  details when needed without cluttering the success path.
- **Cache caveat banner** is conditional (only fires when t12-path
  `no_source` outcomes exist) — silent on the happy path where the
  analyst already round-tripped through Excel.

### Verification

- `python -c "import ast; ast.parse(open('app.py').read())"` — parses
  clean at 1,394 lines.
- Writer regression test (`tests/test_uw_template_writer.py`) still
  passes on v5 (90 concepts written / 3,232 cells on Homestead).
- No new tests for the Streamlit wiring — Streamlit's session-state
  testing is awkward and the existing writer-module tests cover the
  underlying call path.

### Known limitation surfaced this release

- **Cache state on freshly-built Analyzer bytes**: openpyxl doesn't
  compute formulas, so the Analyzer bytes the app builds via
  `populate_rr_input` / `populate_t12_input` / `populate_ar_collections`
  have *no cached UW Output values*. The writer reads `data_only=True`,
  which returns `None` for uncomputed formulas. Net effect: when the
  analyst uses the inline populate-UW-Template flow on a fresh
  Analyzer (no Excel round-trip), most t12-path concepts come through
  as `no_source`. The cache caveat banner surfaces this clearly. A
  future enhancement could embed a formula evaluator (pycel / formulas
  / xlcalculator) in the pipeline to compute Analyzer values in-Python
  before the writer reads them — non-trivial but would remove the
  Excel-round-trip step entirely.

### Out of scope (still pending)

- **v5.1 template completions** (operator side): Cover substrate version
  stamp + RR Analysis tab-header Period Date metadata cell.
- **Deposit parser support** — substrate slot ready, fixture pending.
- **AR row-level routing** — substantial Track 2/3 upstream work.
- **In-Python formula evaluator** to close the cache caveat (see above).

### Committed-asset addendum (2026-05-26, same release)

Operator dropped a clean blank v5 template at `assets/ALF_UW_Template_v5.xlsx`
(repo root `assets/` — same convention as `fortis_logo.svg` and the Pingkas
logos). Registry's `templates.v5.file` repointed from
`Sample Files/ALF_UW_Template_v5.xlsx` → `assets/ALF_UW_Template_v5.xlsx`;
test fixture `TEMPLATE_V5` constant repointed to match. This makes
writer smoke tests runnable from a cold checkout without needing the
gitignored Sample Files copy. v4 working copy stays in Sample Files —
not committed, not the binding default. Structural verification on the
committed file: 16 sheets, no data rows in Rent Roll Analysis A211+,
Prop Info B4/B20-B22 all empty, AQ211 holds `=SUM(AK211:AO211)` formula.

### Versioning

- UWT code version: **v0.4.1** (Phase 2.5).
- Mapping registry version: **0.3.0** (unchanged from v0.4.0).
- Template versions supported: **v4** + **v5** (v5 default).
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.4.0 — Phase 3: UW Template v5 absorbed (2026-05-26)

Operator authored `ALF_UW_Template_v5.xlsx` externally in Excel (per the
2026-05-25 v4→v5 handoff brief) and dropped it at
`Deals/Acquisition/_Template/ALF Templates/ALF_UW_Template_v5.xlsx`. v5 is
now the **binding** template version as of 2026-05-26; v4 is retained for
backward compat.

### Shipped

- **Sample Files canonical** — `Sample Files/ALF_UW_Template_v5.xlsx`
  copied in from the Deals folder to remain the registry's canonical
  template location (per the 2026-05-25 decision).
- **Registry extended to v0.3.0**:
  - New `templates.v5` block: intake sheets, paste anchor, capacity
    (`rent_roll_data_end_row: 610` → 400 units, up from v4's 175),
    `monthly_header_strategy` (formula-driven from on-sheet Layer 1 row
    122 — no writer overwrite needed), inventory of new/shifted rows and
    columns, removed sheets (`Additional Fees`), and items deferred to
    v5.1 (Cover substrate stamp; tab-header Period Date metadata cell).
  - v4 block backfilled with `data_end_row: 386` for parity.
  - **Per-concept `targets.v5`** for every concept (inherit v4 unless
    v5 shifted/added the target):
    - **T-12 row shifts** due to new row 115 insert:
      `ebitdarm` N115→N116, `ebitdar` N116→N117.
    - **T-12 closed gaps**:
      `opex_total_excl_mgmt` → N115 (template formula `=N114-N113`;
      writer overwrites with UW Output row 63 when present);
      `ebitda` → N118 (new label-only row; writer populates from UW
      Output row 68).
    - **Capacity closed gaps**:
      `occupied_beds_il/al/mc` → Prop Info `B20/B21/B22` (new rows 19-22
      added; B19 is template-derived sum, writer doesn't touch).
    - **Rent Roll closed gaps**:
      `rr_care_level_tier_label` → AP211+ (writer pastes from Analyzer
      col K); `rr_preleased_date` → AR211+ (writer pastes from Analyzer
      col AJ post-substrate-v0.2.14); `rr_total_ancillary` → AQ211+ but
      status `derived` (template-owned formula `=SUM(AK:AO)`; writer
      skips).
    - **Rent Roll col shifts** per contract §16 (analyst-input cols
      pushed right by 3 to make room for new AP/AQ/AR):
      `rr_ach` AP→**AS**; `rr_market_psf` AQ→**AT**.
- **Writer (`uw_template_writer.py`) updated**:
  - Default `template_version` flipped `v4` → **`v5`**.
  - Reads `rent_roll_data_end_row` from `templates.{v}` block and uses
    it to cap `_write_column_stride` per call. Source-overflow case
    (Analyzer has more populated rows than the template can hold) is
    surfaced as a `PopulateReport` warning, not a crash.
  - CLI default also flipped to v5.
- **Tests updated**:
  - Both smoke tests now exercise v5 by default; `TEMPLATE` constant
    points at `Sample Files/ALF_UW_Template_v5.xlsx`.
  - Empty smoke expects 16 sheets (was 17 — `Additional Fees` removed
    in v5), no longer expects the A210-blank warning (v5 has the header).
  - Populated e2e spot-checks four new v5 features:
    - T-12 Analysis N115 (Total OpEx excl. mgmt — new row)
    - T-12 Analysis N116 (EBITDARM — shifted from N115)
    - T-12 Analysis N118 (EBITDA — new row)
    - Prop Info B20/B21/B22 (Occupied Beds split — new rows)
  - **AQ-formula-preserved assertion**: verifies the template's
    `=SUM(AK211:AO211)` formula at AQ211 survives the writer round-trip
    (the bug caught + fixed during this release — see "Bug caught"
    below).
- **Artifacts regenerated** — `mapping_mindmap.html`, `MAPPING_TRACKER.md`,
  `mapping_tracker.csv` now show both `v4` and `v5` columns per concept.
- **Open questions**: 11 → 8. Four v5 closures
  (EBITDA row, Occupied beds, Preleased v5 column, monthly header
  overwrite). Two new items added (Cover stamp deferred to v5.1; tab-
  header Period Date metadata cell still pending).

### Status rollup at v0.4.0

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 62 | 2 | 1 | 4 | 3 |
| rent_roll | 35 | 33 | 0 | 0 | 0 | 2 |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **95 (86%)** | **2** | **5** | **4** | **5** |

Mapped: 88 → **95** (+7 net — the 7 v4 gap_targets that close into v5
mapped targets). Gap_target: 10 → **2** (only `substrate_version` and
`t12_period_date` remain).

### Bug caught + fixed mid-release

First test run on v5 revealed that `rr_market_psf` (v4 target AQ) was
overwriting v5's new Total Ancillary $ formula cell. Root cause: my Phase
3 extender script inherited v4 targets blindly for concepts not in the
explicit override map, but the 2026-05-26 contract §16 specifies four col
shifts (AP→AS, AQ→AT, AR→AU, AV) that I'd missed. Patched both shifted
concepts (`rr_ach` AP→AS, `rr_market_psf` AQ→AT); analyst-input cols
(`Conc Source` AR→AU, `Effective Conc $` AS→AV) aren't in our registry so
no further action. Test now verifies `AQ211` retains its formula
post-write — drift guard against this exact class of bug.

### Populated-Analyzer e2e on v5 (Homestead, 176 beds)

- **90 concepts written, 3,232 cells populated** (was 85 / 3,627 on v4 —
  fewer cells because the v5 capacity cap of 400 truncates Analyzer's
  formula-column reads of cols T/U more tightly than v4's previously-
  unbounded stride).
- T-12 Analysis N69 EGI $7,001,957 (unchanged ✓)
- T-12 Analysis N115 Total OpEx excl. mgmt **$5,234,474** (new ✓)
- T-12 Analysis N116 EBITDARM $1,767,483 (shifted ✓)
- T-12 Analysis N118 EBITDA **$1,417,385** (new ✓)
- Prop Info B20/B21/B22 Occupied Beds **53 / 40 / 35** (new ✓)
- Rent Roll Analysis AP211 Care Level Tier (None for first bed — fixture
  doesn't populate K for IL units), AR211 Preleased Date (None —
  fixture predates v0.2.13 Preleased capture).
- AQ211 `=SUM(AK211:AO211)` formula preserved ✓.

### Out of scope (Phase 3)

- **Phase 2.5 — Streamlit UI integration** — still pending. Writer ships
  with new v5 default but the app doesn't expose it yet.
- **v5.1 follow-ups** (per Deals-folder release handoff):
  - Cover substrate version stamp (template-side)
  - Rent Roll Analysis tab-header Period Date metadata cell
- **Phase 4 — AR row-level routing** — still pending (gap_source unchanged).
- **Deposit parser support** — still pending a source fixture.

### Versioning

- UWT code version: **v0.4.0** (Phase 3 — v5 absorbed).
- Mapping registry version: **0.3.0**.
- Template version supported: **v4** + **v5** (v5 default).
- Analyzer substrate mapped against: **v0.2.14** (unchanged).

---

## v0.3.0 — Phase 2: writer module (2026-05-25)

The first piece of Track 4 that produces a file. `uw_template_writer.py`
populates an ALF UW Template from a populated Analyzer in a single
pure-function call, driven entirely by the mapping registry.

### Shipped

- **`uw_template_writer.py`** — ~400 LOC.
  - Public API: `populate_uw_template(analyzer_bytes, template_bytes, *,
    template_version='v4', scenario='normalized', registry_path=None,
    include_statuses=None, allow_special_keys=None) -> (bytes, PopulateReport)`.
  - Source-system dispatch on `concept.source.system`:
    - `uw_output` → reads `UW Output!{column}{row}` where `column` resolves
      via `scenario` (`E` for `t12_actual`, `F` for `normalized`); also
      handles literal `B`/`C`/`D` for IL/AL/MC splits.
    - `rr_input` → reads a full column-stride from
      `Rent Roll Input!{column}7:{column}606`, returns a 600-element list.
    - `named_range` → resolves the named range to a qualified address and
      reads the cell.
    - `cell` → direct sheet+address read.
    - `derived` → hard-coded compute for the small set of derived concepts
      (`licensed_beds_total`, `opex_total_incl_mgmt`).
    - `gap` → returns None (writer skips at the no_source branch).
  - Target write modes:
    - Scalar: single cell `{Sheet}!{address}`.
    - Row-stride (address ends in `+`): writes down the column from
      `{start_row}` skipping blank source values. Preserves any template
      cells the source doesn't populate.
  - Loads Analyzer with `data_only=True` (reads cached formula values —
    the Analyzer must be saved through Excel first), template with
    `data_only=False` (preserves formula cells the writer doesn't touch).
  - `PopulateReport` dataclass: per-concept `ConceptResult` (key, path,
    status, outcome, target_address, cells_written, notes, sample_value)
    plus aggregate summary and warnings list.
- **`tests/test_uw_template_writer.py`** — two tests:
  - `test_empty_analyzer_smoke` (always runs) — bundled empty Analyzer +
    Sample Files template. Verifies no crash, report shape, skip-status
    rules, special-key skip on `opex_bad_debt_expense`, bytes round-trip,
    sheet count preserved (17).
  - `test_populated_analyzer_e2e` (skipped if fixture absent) — Homestead
    populated Analyzer. Spot-checks EGI / EBITDARM / GPR values on T-12
    Analysis, confirms 176 populated rows on Rent Roll Analysis row 211+,
    surfaces first-N written concepts for visual inspection.

### Defaults locked in (writer's stance on open questions)

The registry's `open_questions` are mostly **not** strict blockers — the
writer ships with defensible defaults and lets users override at call time:

- **Scenario**: `normalized` (col F). Contract §8 specifies col F is the
  underwriting figure; col E (t12_actual) is for variance.
- **Bad Debt placement**: writes `bad_debt_writeoffs_revenue` →
  `T-12 Analysis!N62` (template's structural revenue contra-line).
  Hard-coded skip on `opex_bad_debt_expense` (would target N106 but would
  double-count). Override with
  `allow_special_keys={'opex_bad_debt_expense'}`.
- **Monthly grid**: annual total only (col N). Cols B–M (Apr-25..Mar-26
  monthly buckets) left blank — the registry's t12 targets all use `N{row}`.
- **Monthly headers**: not overwritten. Template's hardcoded
  `Apr-25..Mar-26` remains.
- **Skip set** (default): `gap_source`, `gap_target`, `header_only`,
  `derived`, `manual`, `substrate_ready_parser_pending`,
  `decided_pending_upstream`.
- **Include set** (default): `{mapped, proposed}`. Override via
  `include_statuses=`.

### Empty-Analyzer smoke (bundled v0.2.14)

Run: 111 concepts processed, **2 cells written** (the few that resolve to
non-blank even on the empty bundled file), 89 no_source, 20 skipped.
One warning about `Rent Roll Analysis!A210` being blank — the Sample Files
working copy of the template predates the contract's row-210 header, so
the canonical template in `Deals/Acquisition/_Template/` won't trigger
this warning.

### Populated-Analyzer end-to-end (Homestead, 176 beds)

Run on `Sample Files/Analyzer with 2026-04-24 Homestead Village Rent Roll
v2 + March 2026 T12 2026-04-24.xlsx`:

- **85 concepts written, 3,627 cells populated**, 6 no_source, 20 skipped.
- Spot-checks: EGI $7,001,957 / EBITDARM $1,767,483 / GPR $9,524,893 —
  values flow correctly through `UW Output!F{12,66,15}` → `T-12 Analysis!N{69,115,58}`.
- Rent Roll Analysis row 211: A1, A1, IL, Occupied, "Janet (Francis) Pierson" —
  first bed row written cleanly. **176 populated rows** in cols A-AC.
- Property Name = None — this fixture is pre-v0.2.8, so `Cover!B5` is a
  manual-entry cell that wasn't populated. Not a writer bug; surfaces a
  fixture limitation cleanly via `no_source` outcome.

### CLI

`python uw_template_writer.py <analyzer.xlsx> <template.xlsx> <output.xlsx>
[--scenario normalized|t12_actual] [--template-version v4]
[--registry path/to/registry.json]` for ad-hoc runs outside the app.

### Out of scope (Phase 2)

- **App integration (Phase 2.5)** — no Streamlit UI button yet. Writer is
  module-level; integration into `app.py` is a follow-up.
- **Cover!B5 named-range resolution on pre-v0.2.8 fixtures** — the
  Homestead fixture predates Cover!B5's auto-resolver formula. No writer
  fix needed; users with current-substrate Analyzers won't see this.
- **Monthly bucket data** — see Phase 3 (extend UW Export contract to
  expose monthly).
- **AR aging row-level routing** — see Phase 4.
- **Deposit parser support** — still waiting on a source-RR fixture with
  a Deposit field (substrate slot is ready since v0.2.14).
- **Template canonical-copy refresh** — Sample Files working copy doesn't
  have rows 177-210 yet; canonical template in
  `Deals/Acquisition/_Template/` does. Replacing the repo's working copy
  is a separate Track 4 housekeeping task.

### Versioning

- UWT code version: **v0.3.0** (Phase 2 — writer module).
- Mapping registry version: **0.2.1** (unchanged — schema is stable).
- Template version supported: **v4**.
- Analyzer substrate mapped against: **v0.2.14**.

---

## v0.2.1 — AI conflict resolved (2026-05-25)

Registry-only release closing the two open questions about column-AI
assignment that v0.2.0 surfaced. Companion to substrate v0.2.14 + RR v1.18.1
(both shipped earlier in the day, same 2026-05-25 chat).

### Shipped

- **Registry bumped** `0.2.0 → 0.2.1`; `analyzer.substrate_version`
  `v0.2.11 → v0.2.14` (matches the just-shipped substrate).
- **`rr_preleased_date`** — source address `AI7:AI606 (until relocated)`
  → `AJ7:AJ606`. Status stays `gap_target` (UW Template v4 still has no
  Preleased Date column — v5 wishlist).
- **`rr_deposit`** — status `decided_pending_upstream` →
  `substrate_ready_parser_pending`. Substrate slot at `Rent Roll Input!AI`
  is now ready (v0.2.14 migration shipped); parser support pending a
  source-RR fixture with a Deposit field. New status added to
  `status_legend`.
- **`v4.rr_input_data_range`** added — documents the widened named-range
  scope `'Rent Roll Input'!$A$7:$AJ$606` (was `$A$7:$S$606`).
- **`open_questions` resolved (2):**
  - Q1 *"Preleased Date relocation"* — closed by substrate v0.2.14.
  - Q2 *"`RR_Input_Data` named range scope"* — closed by v0.2.14 widen.
- **`open_questions` added (1):** Preleased Date still has no UW Template
  v5 column even after the relocation — track 4 follow-up for template v5.
- **Generator updated** (`build_mapping_artifacts.py`):
  - New status `substrate_ready_parser_pending` added to STATUS_COLOR,
    HTML pill class, and status filter dropdown.
- **Artifacts regenerated** — `mapping_mindmap.html`, `MAPPING_TRACKER.md`,
  `mapping_tracker.csv` all carry the v0.2.1 registry.

### Rollup at v0.2.1

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 57 | 7 | 1 | 4 | 3 |
| rent_roll | 35 | 31 | 3 | 0 | 0 | 1 *(substrate_ready_parser_pending)* |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **88 (79%)** | **10** | **5** | **4** | **4** |

Counts unchanged from v0.2.0 — only statuses moved. **Open questions: 12 → 11**
(2 closed, 1 added).

### Out of scope (Phase 1.5)

- Still no writer module — Phase 2.
- Still no Streamlit UI changes.
- No Deposit parser work (waiting on a source fixture).
- No template v5 work.

### Versioning

- UWT code version: **v0.2.1** (Phase 1.5 — AI conflict resolved).
- Mapping registry version: **0.2.1**.
- Template version mapped: **v4** (unchanged).
- Analyzer substrate mapped against: **v0.2.14**.

---

## v0.2.0 — Phase 1: Rent Roll + AR paste paths (2026-05-25)

Extends the Phase-0 single-path registry to model the full **three paste
paths** documented in the 2026-05-25 handoff contract
(`Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md`).
User-provided contract + companion `2026-05-25-uw-template-input-map.html`
input map became the authoritative source for the Rent Roll path crosswalk.

### Shipped

- **Registry extension** to v0.2.0 — 72 → 111 concepts. Path field added to
  every concept (`t12` / `rent_roll` / `ar`). Existing T-12 concepts
  backfilled with `path: 't12'`. Substrate mapped-against bumped v0.2.9 → v0.2.11.
- **Rent Roll path — 35 concepts** mapping `Rent Roll Input` rows 7+ to
  `Rent Roll Analysis` rows 211+ (header row 210). Position shifts captured
  (e.g. Analyzer col F → UW col AC; Analyzer col R → UW col E). Three
  source-side gaps flagged as `gap_target`:
  - `K` Care Level tier label — no template column (v5 wishlist)
  - `S` Period Date — per-row in source, but UW Template wants it as a
    single metadata cell in the tab header
  - `AH` Total Ancillary — no template column (v5 wishlist: formula col
    `=AK+AL+AM+AN+AO`)
  Six new categories: `rr_identity` / `rr_dates` / `rr_rates` /
  `rr_ancillary` / `rr_subtotals` / `rr_other`.
- **AR path — 4 concepts** for aging buckets at `Rent Roll Analysis` cols
  N–Q. All `gap_source` — gated on upstream resident-key join in
  `AR & Collections` (Track 3 follow-up).
- **Deposit concept** (`rr_deposit`) at status `decided_pending_upstream` —
  user-decided 2026-05-25 to land at `Rent Roll Input!AI`. Maps to UW col M.
- **Preleased Date concept** (`rr_preleased_date`) at status `gap_target` —
  v0.2.13 substrate (also 2026-05-25) put Preleased Date at `Rent Roll
  Input!AI`, which now conflicts with the Deposit decision above.
  Per-user-decision Preleased relocates (likely to AJ) — logged in
  `open_questions` as a cross-cutting Track 1 + Track 3 follow-up.
- **Generator extended** (`build_mapping_artifacts.py`):
  - Path filter (T-12 / Rent Roll / AR / all) added to mind-map HTML toolbar.
  - Path-coloured section headers and per-row path tags.
  - Markdown tracker now groups by **path × category** with a top-level
    "Status rollup by path" table.
  - CSV header gains a `path` column (first col).
  - New status legend entry `decided_pending_upstream`.
- **5 new `open_questions`** logged:
  1. Preleased Date relocation (AI conflict — Track 1 + Track 3 cross-cutting)
  2. `RR_Input_Data` named range scope (currently `A7:S606` — too narrow
     for the new cols V–AI paste path)
  3. Preleased Date in template v5 — no target today
  4. Rent Roll Analysis header rows 1–209 (writer must not touch)
  5. AR aging row-level routing — upstream resident-key join needed
- **`intake_targets_unmapped`** updated: removed Phase-0 placeholder ("whole
  RR Analysis sheet manual paste"); replaced with three specific entries
  covering diagnostic rows 1–209, the row-211 paste anchor, and the
  formula / manual columns (V, X, Y, Z, AA, AB, AR, AS).
- **`SPEC-UWT.md`** restructured for three-path framing; `CHANGELOG-UWT.md`
  this entry; `CLAUDE.md` Track 4 row + last-updated stamp.

### Rollup at Phase 1

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| t12 | 72 | 57 | 7 | 1 | 4 | 3 |
| rent_roll | 35 | 31 | 3 | 0 | 0 | 1 |
| ar | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **88 (79%)** | **10** | **5** | **4** | **4** |

### Decisions made this release

- **AI column → Deposit, Preleased relocates.** Cross-cutting follow-up
  filed; substrate v0.2.14 (or follow-up) needs to move Preleased Date out
  of AI before Deposit can land. `mappings.py` / `normalizer.py` Preleased
  capture stays unchanged; only `analyzer_rr_writer.py` `COL_AI_INDEX` for
  Preleased Date relocates, plus the substrate header at `Rent Roll
  Input!AI4` and the `RR_Input_Data` named-range scope.
- **Repo's `Sample Files/ALF_UW_Template_v4.xlsx` stays canonical for the
  registry** (per-deal Deals folder copies are workspace artifacts).
- **Flat schema with `path` field** — chosen over nested-by-path or
  separate-registries-per-path. Registry schema unchanged (still
  `uw-mapping/v1`).

### Out of scope (Phase 1)

- No writer module (still mapping-only).
- No Streamlit UI changes.
- No edits to Analyzer code or substrate (substrate stays at v0.2.13 from
  the v0.1.18 / Section N work that also shipped 2026-05-25; registry
  *targets* v0.2.11 from the handoff contract since v0.2.12 / v0.2.13 do
  not change UW Output structure).
- No execution of the AI-column relocation (logged as an open question, not
  built here — that's a separate cross-cutting PR).

### Versioning

- UWT code version: **v0.2.0** (Phase 1).
- Mapping registry version: **0.2.0**.
- Template version mapped: **v4** (unchanged).
- Analyzer substrate mapped against: **v0.2.11** (from handoff contract).

---

## v0.1.0 — Phase 0: inspection + mapping registry (2026-05-23)

Track 4 seed release. No code that mutates anything — purely an inspection
pass over `ALF_UW_Template_v4.xlsx`, a modular mapping registry against
Analyzer substrate v0.2.9, and generated artifacts.

### Shipped

- **`tools/uw_template/registry.json`** — 72-concept semantic-key mapping
  registry, schema `uw-mapping/v1`. Version-keyed targets (`targets.v4 = {...}`)
  so future template versions extend rather than rewrite. 57 of 72 concepts
  are `mapped` (79%); the remaining 15 are `proposed`, `gap_source`, `gap_target`,
  `header_only`, or `derived`. Six categories: metadata (4) / capacity (7) /
  revenue (9) / waterfall (5) / labor (15) / nonlabor (26) / mgmt_noi (6).
- **`tools/uw_template/build_mapping_artifacts.py`** — generator that emits
  the three artifacts below from `registry.json`. Re-run after any registry
  edit. Modular: no schema changes required to add template `v5` later.
- **`tools/uw_template/mapping_mindmap.html`** — self-contained interactive
  visualizer (no CDN), filter by status / search / switch template version.
- **`tools/uw_template/MAPPING_TRACKER.md`** — human-readable tracker with
  status legend, rollup table, and per-category mapping tables.
- **`tools/uw_template/mapping_tracker.csv`** — diffable CSV (one row per
  concept × template version) for spotting drift across template versions.
- **`SPEC-UWT.md`** — Track 4 spec: scope, registry schema, structural
  mismatches, phase plan, versioning, layout.
- **`CHANGELOG-UWT.md`** — this file.
- **`CLAUDE.md`** — Track 4 row added to the workstream tracks table.

### Structural findings (carry-forward to Phase 1)

The Phase 1 writer cannot ship until these are answered. Filed as
`open_questions` in `registry.json`:

1. **Bad Debt placement** — revenue contra (template `N62`) vs opex
   (template `N106`). UW Output exposes one value; template has two slots.
2. **2nd Person Revenue** — template has dedicated `N67`; Analyzer rolls 2P
   into `Rent Roll Input!V` and does not break it out at UW Output.
3. **Monthly grid** — template `T-12 Analysis!B56:M56` headers
   `Apr-25..Mar-26` invite 12-month bucket paste; UW Export only exposes
   annual. Phase 1 stance: fill col N only, leave B-M blank. Phase 2
   widens the upstream contract.
4. **EBITDA row** — UW Output row 68 has no template target. Add to
   template (request to template author) or drop from writer scope.
5. **Occupied beds** — UW Output row 71 (IL/AL/MC) has no Prop Info target.
6. **`Rent Roll Analysis!A5` date format** — confirm RR period date format
   (yyyy-mm-dd vs Excel date) and which cell receives it (B5 vs D5).
7. **Monthly header cells** — should writer overwrite hardcoded
   `Apr-25..Mar-26` with actual T-12 months from `T12_Period_Date`, or
   leave the placeholder?

### Out of scope (Phase 0)

- No `uw_template_writer.py` — Phase 0 is mapping-only.
- No Streamlit UI changes — no new download button.
- No edits to Analyzer (Track 3) — substrate stays at v0.2.9.
- No commitable copy of the template — `Sample Files/ALF_UW_Template_v4.xlsx`
  remains gitignored. A canonical committable copy under
  `tools/uw_template/assets/` is deferred to Phase 1 once writer mechanics
  are decided.
- No journal entry on the registry's behalf for Tracks 1/2/3.
- `_raw_extraction.json` and `_template_v4_dump.txt` are build artifacts
  used during inspection — left in place for reproducibility but not
  consumed by the writer.

### Versioning

- UWT code version: **v0.1.0** (Phase 0 seed).
- Mapping registry version: **0.1.0** (stamped in `registry.json`).
- Template version mapped: **v4** (filename: `ALF_UW_Template_v4.xlsx`).
- Analyzer substrate mapped against: **v0.2.9**.
