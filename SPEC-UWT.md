# SPEC-UWT.md — ALF UW Template Integration (Track 4)

> Track 4 specification — wiring the Analyzer's `UW Output` / `UW Export` /
> `Rent Roll Input` / `AR & Collections` surfaces into the downstream
> **ALF UW Template** workbook as the last step of the ALF underwriting
> pipeline.
>
> **Status:** Phase 3.7 — **in-Python UW Output evaluator shipped (UWT v0.6.0,
> 2026-05-28); the cache caveat is closed.** The writer no longer depends on
> the Analyzer having been round-tripped through Excel: a new module
> `uw_output_model.py` computes the 62 `uw_output`-system concepts (+ 2
> dependent `derived`) directly from the parsed RR + T12, mirroring T12
> Analytics, and the writer accepts them as a fallback used only when the
> Analyzer's cached cell is blank. See §12 and CHANGELOG-UWT v0.6.0.
> **UWT v0.6.1 (2026-05-28):** dynamic-array repair — the writer now restores
> `xl/metadata.xml` + the per-cell `cm` markers openpyxl drops on save, so the
> template's Section R / S `SORT`/`UNIQUE`/`FILTER` spills survive instead of
> demoting to single-cell CSE arrays (which had collapsed Section R to one
> row). See §13 and CHANGELOG-UWT v0.6.1. Phase 3.6
> (v5 → v5.1 metadata cells) attempted as UWT v0.5.0 on 2026-05-26 and
> **rolled back same-session** due to openpyxl `wb.save()` silently dropping
> `xl/metadata.xml` (dynamic-array `XLDAPR` props the v0.4.3 Section R/S
> spilled-range formulas depend on) and `xl/webextensions/` (Claude-for-Excel
> add-in taskpane). Path forward: operator authors the two cells in Excel via
> Cowork per `tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md`.
> See openpyxl quirk #6 in CLAUDE.md for technical detail.
> **Current code version:** UWT v0.6.0 (registry v0.4.2 unchanged — the
> evaluator is a writer/app addition, no registry change). Earlier: UWT v0.5.3
> (registry v0.4.2 — three concepts moved `mapped → derived` to honor v5.1's
> new K/L/V template formulas; see CHANGELOG-UWT.md). UWT v0.5.2 (registry
> v0.4.1 — 12 new month-header concepts added under path `t12_raw`). Writer
> pastes Analyzer's T12 Input!C11:N11 (actual T-12 period months)
> into T-12 Analysis!C122:N122; auto-cascades to row 56's monthly
> headers via existing `=C122..=N122` formula chain.
> **Target template version:** `v5` (`Sample Files/ALF_UW_Template_v5.xlsx`
> — repo canonical copy mirrored from `Deals/Acquisition/_Template/ALF Templates/`).
> v4 still supported via `template_version='v4'` for backward compat.
> **Analyzer substrate mapped against:** v0.2.14 (unchanged — v5 didn't move
> the substrate; only template-side structure shifted).

---

## 1. Where this fits

Track 4 is the **last downstream consumer** of the Analyzer. The full pipeline
has **three paste paths** into the UW Template:

```
RR (Track 1)  →  ┐
                 ├──→  ALF_Financial_Analyzer_Only.xlsx  (Track 2/3 substrate)
T12 (Track 2) →  ┘     │
AR  (Track 2) →  ──────┤
                       │  ┌── UW Output / UW Export ──── ▶  T-12 Analysis
                       │  ├── Rent Roll Input rows 7+ ── ▶  Rent Roll Analysis 211+
                       │  └── AR & Collections ──────── ▶  Rent Roll Analysis N–Q
                       ▼
                          ALF UW Template  (Track 4 — this spec)
                          (per-deal populated copy)
```

The ALF UW Template is an investor-facing full underwriting workbook (17 sheets,
~5,500 value cells, Scenarios + P&L pro forma + Waterfall + Sensitivity +
Capital Stack + 10-yr returns). The Analyzer surfaces populate three of its
**intake sheets** (`Prop Info`, `T-12 Analysis`, `Rent Roll Analysis`); the
rest of the template runs on its own formulas / analyst input / Scenarios
driver.

**Authoritative handoff doc:** the 2026-05-25 contract
`Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md`.
Maintained outside this repo; the registry mirrors its row map and column
crosswalk.

## 2. Scope

### Phase 1 (current — v0.2.0)

Phase 1 extends the Phase-0 registry with the **Rent Roll** and **AR** paste
paths from the 2026-05-25 handoff contract:

- All 34 `Rent Roll Input` columns crosswalked to their `Rent Roll Analysis`
  row 211+ targets (35 concepts incl. `Preleased Date`). Position-shifts,
  renames, and three source-side `gap_target` items (`K` Care Level tier
  label, `S` Period Date, `AH` Total Ancillary).
- 4 AR-aging concepts as `gap_source` stubs (UW Template cols N–Q, gated on
  future row-level routing from `AR & Collections`).
- Deposit concept at `decided_pending_upstream` — DECIDED 2026-05-25 to land
  in `Rent Roll Input!AI`. Preleased Date (currently at AI per v0.2.13)
  flagged in `open_questions` for relocation.
- Generator (`build_mapping_artifacts.py`) extended with a Path filter and
  per-path coloured sections. Markdown / HTML / CSV all group by path × category.

### Phase 0 (v0.1.0, 2026-05-23) — shipped:

- The mapping registry (`tools/uw_template/registry.json`) — semantic-key
  registry of source-to-target concepts, decoupled from any single template
  version.
- A generator script (`tools/uw_template/build_mapping_artifacts.py`) that
  emits three artifacts from the registry:
  - `mapping_mindmap.html` — interactive visualizer (filter by status,
    search, switch template versions).
  - `MAPPING_TRACKER.md` — human-readable tracker.
  - `mapping_tracker.csv` — diffable CSV (one row per concept × template
    version).
- This spec doc + `CHANGELOG-UWT.md` + a CLAUDE.md entry for Track 4.

Phases 0 and 1 explicitly **do not** ship:

- A writer module (no code that mutates the template).
- A Streamlit UI button to produce a populated template.
- Any change to the Analyzer (`UW Output`, `UW Export`, `Rent Roll Input`
  cols, `AR & Collections`, named ranges).

Phase 2+ scope is sketched in §7 below.

## 3. Template at a glance — `ALF_UW_Template_v4.xlsx`

17 sheets, 5 named ranges (`Beds`, `EGI`, `Total_LPA_Equity`, `Total_Payroll`,
`Units`). The intake surface — the only sheets the writer will touch — is
three sheets that contain pure literal cells (no formulas):

| Sheet | Cells | Formulas | Literal cells | Role |
|---|---|---|---|---|
| `Prop Info` | 47 | 0 | 47 | Property identifiers, capacity, market data. Some autofillable from Analyzer; most manual. |
| `T-12 Analysis` | 1281 | 0 | 1281 | Layer 3 (rows 55+) is the standardized bucket paste target. Layer 1 (rows 119+) is the operator's raw T-12 paste. Rows 1-54 are formula-free diagnostics (will be wired to Layer 3 by the template author). |
| `Rent Roll Analysis` | 694 | 0 | 694 | Raw rent roll paste + diagnostic sections. Whole sheet runs off the raw RR. |

Downstream consumer sheets (`Scenarios`, `P&L`, `Waterfall`, `Cover`, etc.) are
formula-rich and **out of scope for the writer**.

## 4. Mapping registry shape

The registry is a single JSON file with a stable schema and a per-concept,
multi-version target structure. This is what makes the integration **modular**:
adding template `v5` requires *only* extending `templates` + each concept's
`targets`, never editing the writer or the generator.

```jsonc
{
  "schema": "uw-mapping/v1",
  "registry_version": "0.1.0",
  "analyzer": { "file": "...", "substrate_version": "v0.2.9", ... },
  "templates": {
    "v4": { "file": "...", "intake_sheets": [...], ... },
    // "v5": { ... }       <-- future template version
  },
  "status_legend":   { "mapped": "...", "proposed": "...", ... },
  "category_legend": { "metadata": "...", "revenue": "...", ... },
  "concepts": [
    {
      "key": "egi",
      "label": "Effective Gross Income (EGI)",
      "category": "revenue",
      "source": { "system": "uw_output", "sheet": "UW Output",
                  "row": 12, "column": "E_or_F" },
      "targets": {
        "v4": { "sheet": "T-12 Analysis", "address": "N69",
                "label_at": "A69" }
        // "v5": { ... }
      },
      "status": "mapped",
      "notes": "..."
    }
  ],
  "intake_targets_unmapped": [...],
  "open_questions":          [...]
}
```

### Status values

| Status | Meaning |
|---|---|
| `mapped` | 1:1 mapping confirmed by label match + semantic review. |
| `proposed` | Best-guess mapping; needs user confirmation before writer relies on it. |
| `gap_source` | Template wants data the Analyzer does not currently expose. |
| `gap_target` | UW Output produces a value the template has no row to receive. |
| `header_only` | UW Output row is a visual section separator with no value; writer skips. |
| `manual` | Template field is filled by the analyst by hand / from external research. |
| `derived` | Template cell is computed by formula; writer must not overwrite. |

### Source systems

| `system` | Resolver |
|---|---|
| `uw_output` | Address is `UW Output!{column}{row}`. `column` is `B`/`C`/`D` for IL/AL/MC splits, or `E_or_F` to indicate "T12 Actual OR Normalized" (writer picks at runtime). |
| `uw_export` | Same as `uw_output` but reads the post-offset address on `UW Export` (+8 rows). For Phase 1 writer-side; the registry currently uses `uw_output` semantics for clarity. |
| `named_range` | Resolves via the Analyzer's defined names (`Property_Name`, `RR_Period_Date`, `T12_Period_Date`). |
| `cell` | Direct sheet+address (used for substrate-version cells like `Cover!B8`). |
| `derived` | Writer computes from other mapped values (e.g. `licensed_beds_total = IL + AL + MC`). |

## 5. Rollup at Phase 3 (template v5 default, substrate v0.2.14)

111 concepts across three paths:

| Path | Concepts | mapped | gap_target | gap_source | proposed | other |
|---|---|---|---|---|---|---|
| **t12** (UW Output → T-12 Analysis) | 72 | 62 | 2 | 1 | 4 | 3 |
| **rent_roll** (Rent Roll Input → Rent Roll Analysis 211+) | 35 | 33 | 0 | 0 | 0 | 2 *(1 derived + 1 substrate_ready_parser_pending)* |
| **ar** (AR & Collections → Rent Roll Analysis N–Q) | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **111** | **95 (86%)** | **2** | **5** | **4** | **5** |

Phase 3 closed 8 of the 10 v4 `gap_target`s by absorbing the v5 template
changes — only `substrate_version` (Cover stamp, deferred to v5.1) and
`t12_period_date` (no monthly-header concept target) remain.

Labor + non-labor + EGI/EBITDARM are clean 1:1 by label. Rent Roll columns
map cleanly by field name but **column positions do not match 1:1** — the
crosswalk in `registry.json` is the source of truth. Friction concentrates
in:

- **T-12 path:** Bad Debt placement divergence; 2nd-Person breakout missing
  upstream; no EBITDA row in template; capacity (no occupied-beds rows).
- **Rent Roll path:** three template-side gaps (`K` Care Level tier label,
  `S` Period Date, `AH` Total Ancillary) — all v5 template wishlist items;
  Deposit + Preleased AI-column conflict pending resolution.
- **AR path:** all four aging concepts are `gap_source` — requires upstream
  resident-key join in `AR & Collections` before it can move forward.

## 6. Structural mismatches the writer must handle

### T-12 path
1. **Monthly grid vs. annual total.** Template `T-12 Analysis!B56:M56` headers
   `Apr-25..Mar-26` invite a 12-month bucket paste. UW Export only exposes
   annual totals — Phase 2 writer would fill only col N (T-12 Total). Widening
   the Analyzer to expose `Monthly Trending` data via UW Export is a Phase 3
   candidate.
2. **Bad Debt placement.** Template has Bad Debt as a revenue contra-line
   (`T-12 Analysis!N62`, above Net Rent Revenue at `N63`). Analyzer treats
   Bad Debt as an OpEx line (`UW Output` row 57 → template `N106`). Pasting
   to both rows double-counts. Pick one placement before writer ships.
3. **2nd Person Revenue.** Template has dedicated `T-12 Analysis!N67`.
   Analyzer rolls 2P into Rent Roll Input col V and includes it in `Total
   Monthly Rev` but does not surface a 2P annual on UW Output.
4. **EBITDA row.** UW Output row 68 has no template row to land in.
5. **Occupied beds.** UW Output rows 71 (IL/AL/MC occupied) have no template
   target.
6. **Monthly column headers.** Hardcoded `Apr-25..Mar-26` won't match every
   deal's actual T-12 period.
7. **NOI separator.** UW Output row 65 is header-only — writer must skip.

### Rent Roll path
8. **Column position re-mapping.** 34 source cols don't align 1:1 to UW Template
   cols — see registry. Writer **must** map field-by-field, not column-letter.
9. ~~**AI column conflict.**~~ **Resolved 2026-05-25** by substrate v0.2.14 +
   RR v1.18.1: Deposit slot reserved at `Rent Roll Input!AI` (clear-only —
   no parser support yet); Preleased Date relocated to AJ.
10. ~~**`RR_Input_Data` named range is too narrow.**~~ **Resolved 2026-05-25**
    by substrate v0.2.14: range widened from `A7:S606` to `A7:AJ606`.
11. **Formula columns on the UW Template side.** Cols V, X, Y, Z, AA, AB, AS in
    Rent Roll Analysis are derived — writer must NOT overwrite.
12. **AR / AS preserved on re-paste.** Conc Source (AR) and Effective Conc $
    (AS) are analyst-entered; writer must preserve.
13. **Period Date (Analyzer col S).** Per-row in source; the template wants it
    as a single metadata cell in the tab header, not per-row.
14. **Header rows 1–209.** Diagnostic sections formula-derived from the
    paste block — writer must not touch.

### AR path
15. **Per-resident vs. per-payer aggregation.** AR & Collections aggregates by
    payer; UW Template aging cols are per-resident. Resident-key join needs to
    happen upstream before the AR path can move off `gap_source`.

All 15 are tracked as `open_questions` in `registry.json`.

## 7. Phase plan

| Phase | Deliverables | Status |
|---|---|---|
| **0 — Inspection & T-12 mapping** | Registry, generator, mind-map HTML, tracker MD/CSV, spec, changelog. | ✅ shipped 2026-05-23 (v0.1.0) |
| **1 — Rent Roll + AR mapping** | 35 RR + 4 AR concepts; path-aware generator; Deposit + Preleased AI-conflict logged. | ✅ shipped 2026-05-25 (v0.2.0) |
| **1.5 — AI conflict resolved** | Substrate v0.2.14 — Deposit slot reserved at AI; Preleased Date relocated to AJ; `RR_Input_Data` named range widened. RR v1.18.1 — writer constants updated. UWT registry v0.2.1 — Deposit status `substrate_ready_parser_pending`, Preleased source AJ. | ✅ shipped 2026-05-25 (v0.2.1) |
| **2 — Writer module** | `uw_template_writer.py` — pure function `populate_uw_template(analyzer_bytes, template_bytes, *, scenario='normalized') → (bytes, PopulateReport)`. Registry-driven dispatch on `source.system` (`uw_output`, `rr_input`, `named_range`, `cell`, `derived`). Skips concepts at default skip statuses (gap_*, header_only, derived, manual, *_pending) and hard-coded `_SPECIAL_SKIP_KEYS` (opex_bad_debt_expense duplicate). Structured `PopulateReport` for transparency. `tests/test_uw_template_writer.py` exercises empty + populated fixtures. | ✅ shipped 2026-05-25 (v0.3.0) |
| **3 — UW Template v5 absorbed** | `templates.v5` block added to registry; per-concept `targets.v5` for every concept (inherit v4 unchanged unless v5 shifted/added the target). Writer reads `rent_roll_data_end_row` per template version (v4: 386, v5: 610) and caps the rent_roll stride accordingly. Default `template_version` flipped to `v5`. 7 concepts moved gap_target → mapped (ebitda, opex_total_excl_mgmt, occupied_beds_il/al/mc, rr_care_level_tier_label, rr_preleased_date); 1 moved gap_target → derived (rr_total_ancillary — template owns the `=SUM(AK:AO)` formula at AQ); 2 v4-vs-v5 col shifts (rr_ach AP→AS, rr_market_psf AQ→AT) per contract §16. | ✅ shipped 2026-05-26 (v0.4.0) |
| **6 — T-12 Raw path (BL-0026)** | New `t12_raw` path: Analyzer `T12 Input!A12:N511` → UW Template `T-12 Analysis!A123:N622` (Layer 1). Closes the duplicate-paste step where the analyst manually copies raw operator T-12 into the template after the same data already lives in Analyzer T12 Input. Includes month-header propagation (`T12 Input!C11:N11` → `T-12 Analysis!C122:N122`) which auto-updates the standardized layer's monthly headers via the existing `=C122..=N122` chain at B56:M56. ~35 new concepts; clean additive extension to the modular registry. Open question: should writer populate the template's col P (`→ MAPPING` standardized-bucket label) via Description_Map join, or leave as analyst dropdown? | deferred until Phase 2.5 is fully integrated + sample-run-verified |
| **2.5 — App integration** | Sidebar scenario radio (`normalized` default / `t12_actual`, always visible). UW Template file load mirrors the Analyzer pattern: bundled `assets/ALF_UW_Template_v5.xlsx` is the default (loaded via `_load_uw_template()` helper); override via Advanced expander's "UW Template override" uploader (parallels "Analyzer template override"). Version auto-detection via `_detect_uw_template_version()` probes `Rent Roll Analysis!AP210` ("Care Level Tier") to distinguish v5 from v4. Populate flow runs unconditionally on every Analyzer build (no user upload required). After the existing combined-Analyzer download, the workspace shows: "Using UW Template: <source> (<version>)" caption + 1-line summary + drill-in `PopulateReport` expander (auto-expands on warnings) + per-deal download (`<Property>_UW_Template_<period>_<scenario>.xlsx`). "Cache caveat" info banner conditional on t12-path no_source outcomes — walks analyst through the round-trip-through-Excel workaround. | ✅ shipped 2026-05-26 (v0.4.2, was v0.4.1 with upload-only pattern) |
| **3.5 — Handoff infrastructure** | Establishes the ClaudeCode → Cowork handoff system for template-side changes (inverse of the existing Cowork → ClaudeCode pattern used for AR Collections). `tools/uw_template/HANDOFF_TRACKER.md` (running index), `HANDOFF_TEMPLATE.md` (copy-and-fill blank), `handoffs/` directory with dated briefs, plus the CLAUDE.md Track 4 "Handoff protocol" paragraph. Protocol: Track 4 chats that surface a template-side change produce a brief; operator authors externally in Excel via Cowork; next chat absorbs registry-side and marks Verified. See §11. | ✅ shipped 2026-05-26 in commit `031e24f` (`feat: UWT v0.2.0 → v0.4.0 — Phase 1-3`) — bundled with the Phase 3 v5 absorption; registry/writer/template all carry that commit's state. Augmented later 2026-05-26 with the `Superseded` status legend and 2026-05-26 handoff brief while v0.5.0 was being attempted-then-rolled-back. |
| **3.6 — v5 → v5.1 metadata cells** | Two single-cell additions: substrate version stamp on Cover (closes `gap_target` `substrate_version`) + `Rent Roll Analysis!B5` RR Period date cell (closes `proposed` `rr_period_date`); plus registry-only reclassification of `t12_period_date` `gap_target` → `derived_in_template` (v5 derives `B56:M56` from on-sheet Layer 1 row 122 via `=C122..=N122`). **Attempted same-session via direct openpyxl edits as UWT v0.5.0 and rolled back** — see openpyxl quirk #6 in CLAUDE.md: `wb.save()` silently drops `xl/metadata.xml` (`XLDAPR`/`fDynamic` props the v0.4.3 Section R/S spilled-range formulas depend on) and `xl/webextensions/` (Claude-for-Excel taskpane). Template restored from git `deacc41`; registry / `UWT_VERSION` / artifacts reverted. Path forward: operator authors externally in Excel via Cowork per the active handoff brief, then a future Track 4 chat absorbs registry-side. | ⏳ Pending operator — see `tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md` |
| **3 — Monthly contract widening** | Extend UW Export to expose monthly bucket data from `Monthly Trending`. Writer fills `T-12 Analysis!B56:M68` (income block × 12 months) + later expands to labor/opex monthly. Cross-cutting Track 3 ↔ Track 4. | not started |
| **4 — AR row-level routing** | Upstream substrate change: resident-key join in `AR & Collections` per-resident aging. Once that lands, AR path concepts move off `gap_source`. | not started |
| **5 — Future template versions** | Adding `v5` is an additive change to `registry.json`; the writer reads the version-keyed target. No code change required if labels are stable. | future |

## 8. Versioning

| Counter | Lives at | Convention |
|---|---|---|
| UWT code version | `SPEC-UWT.md` top + `CHANGELOG-UWT.md` | `v0.X.Y` — bump on writer / generator / registry-schema changes. |
| Mapping registry version | `registry.json` → `registry_version` | `0.X.Y` — bump on content changes (added/removed/restatused concepts). |
| Template version | `registry.json` → `templates.<v>` keys | Free-form (`v4`, `v5`, ...) keyed on the source template's own name. |

- Phase 0 shipped UWT v0.1.0 + registry v0.1.0 + template v4 (substrate v0.2.9).
- Phase 1 shipped UWT v0.2.0 + registry v0.2.0 + template v4 (substrate v0.2.11).
- Phase 1.5 shipped UWT v0.2.1 + registry v0.2.1 + template v4 (substrate v0.2.14) — AI-column conflict resolved (Deposit at AI, Preleased at AJ).
- Phase 2 shipped UWT v0.3.0 + registry v0.2.1 (unchanged) + template v4 (substrate v0.2.14) — writer module + smoke tests.
- Phase 3 shipped UWT v0.4.0 + registry v0.3.0 + template **v5** (substrate v0.2.14) — v5 template absorbed; writer supports v4 + v5 via `templates.{v}` blocks.
- Phase 2.5 ships UWT v0.4.1 + registry v0.3.0 (unchanged) — Streamlit UI integration; populate-UW-Template button reachable from the webapp.
- Phase 2.5 follow-up ships UWT v0.4.2 — bundled-template + override pattern (mirrors Analyzer load); populate runs unconditionally.
- Phase 2.5 patch ships UWT v0.4.3 — fills v5 template's W/X/Y formula columns through row 610, unblocking Section R / Section S diagnostics that depended on those columns.
- Phase 2.5 re-fix ships UWT v0.4.4 — operator's `deacc41` "refresh assets" edit replaced v0.4.3's `W = =AC{r}` with a substring-Notes-parser that fails on real rent rolls (Notes col S doesn't carry unit-type wording). v0.4.4 restores AC reference with occupancy gate, adds IFERROR wrappers on A173/B173, swaps D173 placeholders for real per-unit sq ft via AVERAGEIFS on col T.
- **Phase 4 ships UWT v0.5.1 — v5.1 column restructure absorbed** (skipping v0.5.0 used by rolled-back attempt). Operator authored in Excel: Unit Type inserted at new col D before Status; old W + AC dropped; 18 concepts right-shift (D-V→E-W); 17 concepts left-shift (AD-AV→AC-AU); rr_apt_type retargets AC→D. 36 total rent_roll concept target updates. T-12 / Prop Info / Cover targets unchanged (caught + fixed an absorber bug that initially shifted T-12 cells too).
- **Phase 4 follow-up ships UWT v0.5.2 — T-12 monthly headers + cache caveat UX**. Operator-reported sample-run issue: T-12 data not populated + headers should be actual months/year. Investigation: labels match correctly (no fix needed); T-12 data empty due to cache caveat (openpyxl doesn't compute Analyzer formulas — UX fix shipped: promoted banner from `st.info` to `st.warning` with explicit step-by-step; added callout to Workspace expander); month headers hardcoded (fix shipped: 12 new `t12_raw` scalar concepts paste Analyzer T12 Input!C11:N11 → T-12 Analysis!C122:N122, auto-cascading to row 56). Registry 0.4.0 → 0.4.1. In-Python formula evaluator queued as follow-up to eliminate the cache caveat round-trip entirely.
- **Phase 4 follow-up ships UWT v0.5.3 — v5.1 K/L/V template-formula absorption**. Operator dropped a corrected `ALF_UW_Template_v5.1.xlsx` 2026-05-27 with six new template formulas at Rent Roll Analysis row 211+ (K, L, V, W, AA, AB). Three of those (K, L, V) hit cells the writer was previously paste-targeting. `_absorb_v51_total_formulas.py` reclassified `rr_total_loc`, `rr_total_monthly_rev`, `rr_actual_psf` from `mapped → derived` so the writer skips and the template formulas execute at populate-time. Registry 0.4.1 → 0.4.2. Filename consolidated `v5.1.xlsx → v5.xlsx` per established policy. Smoke test passes — 99 / 2,311 cells on Homestead; all 10 v5.1 template formulas verified intact in output. Carry-forwards (rolled into handoff): A173/B173 IFERROR wrapper stripped in operator's v5.1 source (pre-v0.4.4 baseline regression); Cover G1/H1 substrate stamp + Rent Roll Analysis B5 date cell still pending from 2026-05-26 brief.
- Phase 3.5 ships **handoff infrastructure** (`tools/uw_template/HANDOFF_TRACKER.md` + `HANDOFF_TEMPLATE.md` + `handoffs/`) bundled into commit `031e24f` (UWT v0.2.0 → v0.4.0 ship, earlier 2026-05-26) — no separate UWT version bump for the infrastructure itself. Later-2026-05-26 augmentations during the v0.5.0 attempt: added `Superseded` to the status legend, added the 2026-05-26 handoff brief, marked the older 2026-05-25 brief Superseded.
- Phase 3.6 / UWT v0.5.0 **attempted then rolled back** on 2026-05-26 — direct openpyxl patch of v5 template's two residual `gap_target` cells (substrate version stamp on Cover, RR Analysis Period Date at B5) appeared clean at the Worksheet-object fidelity layer but silently dropped `xl/metadata.xml` (`XLDAPR`/`fDynamic` dynamic-array properties) and `xl/webextensions/` (Claude-for-Excel add-in) at the xlsx-zip-archive layer. Template restored from git `deacc41`, registry reverted v0.3.1 → v0.3.0, UWT_VERSION restored 0.5.0 → 0.4.3. Two patch scripts retained as audit trail (`tools/uw_template/_patch_v5_to_v51_metadata_cells.py` + `_revert_registry_to_v030.py`) — **do not re-run the patch script.** Operator-authored v5.1 (via Cowork → Excel) is the only safe path forward. See CHANGELOG-UWT.md and CLAUDE.md openpyxl quirk #6 for forensics.

## 9. Where things live

```
SPEC-UWT.md                              (this file)
CHANGELOG-UWT.md                         Track 4 changelog (newest at top)
UW-OUTPUT-HANDOFF-CONTRACT.md            Companion contract from the Analyzer
                                         side — the registry's source-of-truth
                                         for what UW Output / UW Export expose.

tools/uw_template/
  registry.json                          The mapping registry (data).
  build_mapping_artifacts.py             Generator — run after editing registry.
  mapping_mindmap.html                   Interactive visualizer (open in browser).
  MAPPING_TRACKER.md                     Human-readable tracker (auto-generated).
  mapping_tracker.csv                    Diffable CSV (auto-generated).
  HANDOFF_TRACKER.md                     Running index of ClaudeCode → Cowork
                                         template-change handoffs (newest at top,
                                         with status: Pending / In progress /
                                         Applied / Verified / Superseded). See §11.
  HANDOFF_TEMPLATE.md                    Copy-and-fill blank for new handoffs.
  handoffs/                              Per-handoff briefs, dated
                                         (YYYY-MM-DD-<slug>.md).
  _raw_extraction.json                   Build artifact — raw label dump used
                                         to author the initial registry. Not
                                         consumed by the writer.
  _template_v4_dump.txt                  Build artifact — full template dump
                                         used during inspection. Reference only.
  _patch_v5_section_r_formulas.py        Audit-trail patch script (v0.4.3 ship).
                                         Idempotent; safe to re-run.
  _patch_v5_to_v51_metadata_cells.py     Audit-trail patch script (v0.5.0
                                         attempted-then-rolled-back). **Do NOT
                                         re-run** without first solving the
                                         XLDAPR-loss problem — see openpyxl quirk
                                         #6 in CLAUDE.md.
  _revert_registry_to_v030.py            Audit-trail revert script (v0.5.0
                                         rollback). Idempotent.

Sample Files/ALF_UW_Template_v4.xlsx     The template itself (gitignored, dropped
                                         by user). Future Phase 1 may add a
                                         committable canonical copy under
                                         tools/uw_template/assets/.
```

## 10. Scope discipline note

This track is downstream of the Analyzer. Track 4 chats:
- **Must not** modify Track 1 (RR normalizer), Track 2 (T12 normalizer), or
  Track 3 (Analyzer substrate) without explicit user authorization for a
  cross-cutting PR.
- **May** propose changes to the UW Output / UW Export surface to close
  `gap_source` items — but those proposals are filed against the Track 3
  backlog (`UW-BACKLOG.md`), not implemented here.

Per the CLAUDE.md scope-discipline convention, if a Track 4 chat pivots toward
upstream substrate work, the assistant should stop and confirm before crossing.

## 11. Handoff protocol (template author lives outside this repo)

**The ALF UW Template is authored externally in Excel** (operator → Cowork →
Excel); Claude Code owns the **registry** ([`registry.json`](tools/uw_template/registry.json))
and the **writer** ([`uw_template_writer.py`](uw_template_writer.py)) — not
the template file. This split exists for two structural reasons:

1. **Fidelity.** openpyxl's `wb.save()` silently drops xlsx zip parts that
   it doesn't model in its Worksheet / Workbook object graph — notably
   `xl/metadata.xml` (`XLDAPR` / `fDynamic` dynamic-array properties that
   `SORT` / `UNIQUE` / `FILTER` / `ANCHORARRAY` spilled-range formulas
   depend on; the v0.4.3 Section R/S patch is built on these) and
   `xl/webextensions/` (Office Add-in taskpane registrations). Author-side
   round-trips through Excel preserve all parts; openpyxl round-trips do
   not. The UWT v0.5.0 attempt on 2026-05-26 demonstrated this; see openpyxl
   quirk #6 in CLAUDE.md.
2. **Ownership.** The template is downstream-consumer surface area
   maintained outside this repo (the canonical operator-managed copy lives
   under `Deals/Acquisition/_Template/ALF Templates/`). The repo holds a
   copy at `assets/` for writer-side testing and at `Sample Files/` (gitignored)
   as an operator working-copy reference, but neither is the system of record.

### When to create a new handoff

Trigger criteria (any one is enough):

- A registry entry gains `gap_target` status (UW Output produces a value
  with no template row/cell to receive it).
- A registry entry's target cell changes (row shifts, column shifts,
  cross-sheet relocation).
- A new substrate column or row needs a corresponding template-side
  surface (e.g. substrate v0.2.13's Preleased exposure surfacing a need
  for a per-row Preleased Date column on the template).
- A writer scope decision needs operator input that depends on template
  structure or layout (e.g. monthly-header overwrite policy).
- A new template version is being prepared (e.g. v5 → v5.1).

If a Track 4 change touches only the writer or registry and implies no
template-side action, no handoff is needed — land the changes, regenerate
`MAPPING_TRACKER.md` / `mapping_tracker.csv` / `mapping_mindmap.html` via
`python tools/uw_template/build_mapping_artifacts.py`, and bump the
appropriate version counter.

### Handoff lifecycle

1. **Author** the brief: copy `tools/uw_template/HANDOFF_TEMPLATE.md` to
   `tools/uw_template/handoffs/YYYY-MM-DD-<slug>.md` and fill it in. Add a
   row to the **top** of the index table in
   `tools/uw_template/HANDOFF_TRACKER.md`. Status starts as **Pending operator**.
2. **Operator picks up** the brief from the tracker. Authors changes in
   Excel directly (or via Cowork). Re-drops the file at
   `assets/ALF_UW_Template_v5.xlsx` (overwriting in place — minor revisions
   reuse the version filename; major revisions get a new `v6.xlsx`).
3. **Next Track 4 chat absorbs**: extends `registry.json` with new
   `templates.v5 = {...}` entries (or per-concept `targets.v5` updates),
   re-runs `build_mapping_artifacts.py`, smoke-tests the writer, and
   updates the handoff's tracker row to **Verified**. Both the brief file
   and the tracker row stay in place as audit trail.

### Status legend (in HANDOFF_TRACKER.md)

- **Pending operator** — handoff produced; waiting for operator Excel work.
- **In progress** — operator has started authoring; not yet dropped back.
- **Applied** — new template file present; registry not yet updated.
- **Verified** — registry updated; writer smoke-tested; handoff closed.
- **Superseded** — handoff no longer the action plan (work shipped via a
  different path, or a newer handoff supersedes its scope). Keep the row
  for audit trail; cross-link to the replacement.

### Mapping updates ride inline

Mapping updates (registry edits) are coupled to template changes and live
**inline in each handoff brief** under a "Mapping updates" section. The
existing artifacts (`MAPPING_TRACKER.md` / `mapping_tracker.csv` /
`mapping_mindmap.html`) remain the source of truth for the full mapping
state and are regenerated after each handoff's registry edits land.

### Inverse direction

This protocol is the **ClaudeCode → Cowork** direction. The inverse pattern
(**Cowork → ClaudeCode**) is the existing one used for design specs
authored upstream — e.g. the AR Collections design handoff at
`2026-05-23-AR-Collections-Spec-Update-to-Cowork.md` (which was actually
the *back-handoff* leg of that exchange). The two patterns coexist:
Cowork-authored specs land here, get decided/reviewed, produce a
back-handoff to Cowork; ClaudeCode-surfaced template needs produce a
handoff brief that operator picks up via Cowork or directly in Excel.

## 12. In-Python UW Output evaluator (`uw_output_model.py`)

**The cache caveat and why it existed.** The writer reads the Analyzer with
`data_only=True` — i.e. it reads *cached* formula values. openpyxl does not
evaluate formulas, so an Analyzer the app just built in memory (via
`populate_rr_input` / `populate_t12_input` / `populate_ar_collections`) has
formula **text** but no cached values. Every `uw_output`-system concept
(reads of `UW Output!{col}{row}`, which are themselves references into
`T12 Analytics`) therefore resolved to `None` → `no_source`, leaving the
populated UW Template's `T-12 Analysis` tab blank. The only workaround was a
manual Excel round-trip (download Analyzer → open → save → re-upload as
override → re-run).

**The fix (UWT v0.6.0).** `uw_output_model.compute_uw_output_values(rr_result,
t12_result, *, scenario)` computes those values directly in pure Python from
the same parsed artifacts the writers consume, and the writer takes them as a
fallback:

```
populate_uw_template(analyzer_bytes, template_bytes, *,
                     computed_values={concept_key: value})
```

The fallback is applied **per concept, only when the Analyzer's cached cell
read is blank**. So an analyst-saved (override) Analyzer with real cached
values always wins; the computed values fill gaps for freshly-built Analyzers.
`PopulateReport.summary['computed_in_python']` counts how many concepts the
fallback filled; `ConceptResult.computed_fallback` flags each one.

**Coverage.** 62 `uw_output`-system concepts + 2 dependent `derived`
(`licensed_beds_total`, `opex_total_incl_mgmt`). The app additionally injects
`property_name` and `rr_period_date` (both already in hand, both blank on a
fresh Analyzer). Remaining `rent_roll`-path `no_source` cells are genuinely
empty source columns, not cache artifacts.

**Why it's faithful to Excel.** `UW Output` is a thin reference layer over
`T12 Analytics`, which (a) sums `T12 Raw Data` per Description_Map Label and
(b) reads `Rent Roll Recon` bed counts. The default **normalized** scenario
(col F) equals the **T12 actual** for every line, because:
- opex / other-revenue: `T12 Analytics F{r} = =E{r}` (col F literally copies
  col E unless an analyst overrides it),
- base rent / LOC: the "stabilized" formula `B20 = B6·B10·B19·12` collapses
  algebraically to the T12 actual when `B10` (target occupancy) `= B8`
  (actual occupancy) — and `B10`'s default formula is literally `=B8`.

Verified empirically: on the Homestead fixture `E16==E20`, `E23==E27`,
`E52==F52`, `E108==F108`. Analyst normalization is an Excel-side override
applied *after* populate; once saved, the cached values exist and win.

**Engine reuse.** The module imports Track 5 `dashboard_model`'s aggregation
primitives (`load_description_map`, `_aggregate_t12`, the `_LABELS_*`
constants) rather than re-implementing them — single source of truth for the
Description_Map label vocabulary and GL-by-label grouping.

**Drift guard.** `tests/test_uw_output_model.py` asserts the engine reproduces
the Homestead fixture's cached `UW Output` to the penny (42 concepts) and that
the writer fallback takes a fresh Analyzer's T-12 `no_source` count from 63 → 2.
If the Analyzer's T12 Analytics formulas change shape, this test fails.

## 13. Dynamic-array repair (`_restore_dynamic_arrays`, UWT v0.6.1)

**The problem.** openpyxl's `wb.save()` silently drops `xl/metadata.xml` (the
XLDAPR `fDynamic="1"` block) and the per-cell `cm="N"` markers that tell Excel
a formula is a *dynamic array* (`SORT`/`UNIQUE`/`FILTER`/`ANCHORARRAY` with
spill) rather than a legacy CSE array. The formula text survives verbatim, but
Excel reads `<f t="array" ref="Z173">=SORT(...)` with no metadata as a
single-cell CSE array → it returns only the top-left value. On the UW Template
this collapsed **Section R** (`Rent Roll Analysis!Z173` driver + `A173:Q173`
spills) and Section S to one row, silently understating the row 180/181 totals
— no `#SPILL!`/`#VALUE!` to signal it. An Excel re-save does *not* recover it.

**The fix.** After `wb.save()`, `populate_uw_template` calls
`_restore_dynamic_arrays(output_bytes, template_bytes)` — a pure
`zipfile` + `re` post-processor (no lxml/new dependency) that:

1. Re-injects `xl/metadata.xml` verbatim from the original template.
2. Adds its content-type `Override` and a workbook `sheetMetadata`
   relationship (unique rId).
3. Re-applies the `cm="N"` markers to the exact anchor cells that carried them
   in the template, matched **by sheet name** (robust to openpyxl rel-id
   renumbering and `/xl/…` absolute-path targets) and only on cells that still
   hold a formula (`<f`).

It's faithful by construction — the writer never edits the dynamic-array
anchor cells, so restoring the template's original `cm` set to the
writer-untouched cells reproduces the working state. No-op when the template
has no `xl/metadata.xml` (v4 / non-dynamic workbooks). Wrapped in try/except so
a repair failure degrades to a warning, never breaks the populate;
`report.summary['dynamic_arrays_restored']` flags success.

**Drift guard.** `tests/test_uw_output_model.py::test_dynamic_array_metadata_restored`
asserts the repair flag, `xl/metadata.xml` presence, ~557 `cm` markers
restored, and `Z173` carrying `cm` in the output.

**Why not the operator Excel-resave workaround.** Prior to v0.6.1 the standing
guidance (CLAUDE.md openpyxl quirk #6) was "open the populated file in Excel +
re-save." That recovers a *repair-clean* file but does **not** restore
dynamic-array semantics — Excel commits to the CSE interpretation on open. The
in-Python repair is the structural fix; the manual workaround is retired for
the UW Template output.
