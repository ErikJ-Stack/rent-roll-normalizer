# SPEC-UWT.md — ALF UW Template Integration (Track 4)

> Track 4 specification — wiring the Analyzer's `UW Output` / `UW Export` surface
> into the downstream **ALF UW Template** workbook as the last step of the
> ALF underwriting pipeline.
>
> **Status:** Phase 0 (inspection + mapping registry only — no writer yet).
> **Current code version:** UWT v0.1.0 (this doc + mapping registry only).
> **Target template version:** `v4` (`Sample Files/ALF_UW_Template_v4.xlsx`).
> **Analyzer substrate this is mapped against:** v0.2.9.

---

## 1. Where this fits

Track 4 is the **last downstream consumer** of the Analyzer. The full pipeline:

```
RR (Track 1)  →  ┐
                 ├──→  ALF_Financial_Analyzer_Only.xlsx  (Track 2/3 substrate)
T12 (Track 2) →  ┘                │
                                  │  UW Output  →  UW Export (values mirror)
                                  ▼
                          ALF UW Template  (Track 4 — this spec)
                          (per-deal populated copy)
```

The ALF UW Template is an investor-facing full underwriting workbook (17 sheets,
~5,500 value cells, Scenarios + P&L pro forma + Waterfall + Sensitivity +
Capital Stack + 10-yr returns). The Analyzer's UW Output surface populates a
small subset of its **intake sheets**; the rest of the template runs on its own
formulas / analyst input / Scenarios driver.

## 2. Scope (Phase 0)

Phase 0 ships:

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

Phase 0 explicitly **does not** ship:

- A writer module (no code that mutates the template).
- A Streamlit UI button to produce a populated template.
- Any change to the Analyzer (`UW Output`, `UW Export`, named ranges).

Phase 1+ scope is sketched in §7 below.

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

## 5. Rollup at Phase 0 (template v4, substrate v0.2.9)

72 concepts, six categories:

| Category | Concepts | Mapped | Other |
|---|---|---|---|
| metadata | 4 | 1 | 1 proposed, 2 gap_target |
| capacity | 7 | 4 | 3 gap_target |
| revenue | 9 | 7 | 1 proposed, 1 gap_source |
| waterfall | 5 | 3 | 2 derived |
| labor | 15 | 15 | — |
| nonlabor | 26 | 25 | 1 proposed |
| mgmt_noi | 6 | 3 | 1 proposed, 1 gap_target, 1 header_only |
| **Total** | **72** | **57 (79%)** | **15** |

Labor + non-labor + EGI/EBITDARM are clean 1:1 by label. Friction concentrates
in metadata (no template version stamp), capacity (template has no
occupied-beds rows), revenue (Bad Debt placement divergence; 2nd Person
breakout missing upstream), and mgmt_noi (no EBITDA row in template).

## 6. Structural mismatches the writer must handle

1. **Monthly grid vs. annual total.** Template `T-12 Analysis!B56:M56` headers
   `Apr-25..Mar-26` invite a 12-month bucket paste. UW Export only exposes
   annual totals — Phase 1 writer fills only col N (T-12 Total). Widening
   the Analyzer to expose `Monthly Trending` data via UW Export is a Phase 2
   candidate.

2. **Bad Debt placement.** Template has Bad Debt as a revenue contra-line
   (`T-12 Analysis!N62`, above Net Rent Revenue at `N63`). Analyzer treats
   Bad Debt as an OpEx line (`UW Output` row 57 → template `N106`). Pasting
   the same value to both rows double-counts. Open question — pick one
   placement before writer ships.

3. **2nd Person Revenue.** Template has dedicated `T-12 Analysis!N67`.
   Analyzer rolls 2P into Rent Roll Input col V and includes it in `Total
   Monthly Rev` but does not surface a 2P annual on UW Output.

4. **EBITDA row.** UW Output row 68 has no template row to land in.

5. **Occupied beds.** UW Output rows 71 (IL/AL/MC occupied) have no template
   target — template computes occupancy from the raw RR paste.

6. **Monthly column headers.** Hardcoded `Apr-25..Mar-26` in the template
   probably won't match the actual T-12 period for an arbitrary deal. Writer
   either rewrites the header row or leaves a known disclaimer.

7. **NOI separator.** UW Output row 65 is header-only (no value); writer
   must skip — same gotcha as `UW-OUTPUT-HANDOFF-CONTRACT.md §4(1)`.

These are tracked as `open_questions` in `registry.json` so they don't get
lost between phases.

## 7. Phase plan

| Phase | Deliverables |
|---|---|
| **0 — Inspection & mapping** (this PR) | Registry, generator, mind-map HTML, tracker MD/CSV, this spec, changelog. |
| **1 — Writer module** | `uw_template_writer.py` with `populate_template(analyzer_bytes, template_bytes) → populated_bytes`. Uses the registry to resolve concept → target address for the active template version. Open questions in §6 must be answered first. |
| **1.5 — App integration** | New download button in `app.py` ("Download populated UW Template"). Per-deal output naming convention. Phase 0 carry-forwards translated into Phase 1 acceptance criteria. |
| **2 — Monthly contract widening** | Extend UW Export to expose monthly bucket data from Monthly Trending. Writer fills `T-12 Analysis!B56:M68` (income block × 12 months) + later expands to labor/opex monthly. Requires a substrate version bump on the Analyzer side (Track 3 ↔ Track 4 cross-cutting). |
| **3 — Rent Roll Analysis automation** | Writer populates the raw RR block on `Rent Roll Analysis` from `RR_Input_Data` (named range) instead of analyst paste. |
| **4 — Future template versions** | Adding `v5` is an additive change to `registry.json`; the writer reads the version-keyed target. No code change required if labels are stable. |

## 8. Versioning

| Counter | Lives at | Convention |
|---|---|---|
| UWT code version | `SPEC-UWT.md` top + `CHANGELOG-UWT.md` | `v0.X.Y` — bump on writer / generator / registry-schema changes. |
| Mapping registry version | `registry.json` → `registry_version` | `0.X.Y` — bump on content changes (added/removed/restatused concepts). |
| Template version | `registry.json` → `templates.<v>` keys | Free-form (`v4`, `v5`, ...) keyed on the source template's own name. |

Phase 0 ships UWT v0.1.0 + registry v0.1.0 + template v4.

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
  MAPPING_TRACKER.md                     Human-readable tracker.
  mapping_tracker.csv                    Diffable CSV.
  _raw_extraction.json                   Build artifact — raw label dump used
                                         to author the initial registry. Not
                                         consumed by the writer.
  _template_v4_dump.txt                  Build artifact — full template dump
                                         used during inspection. Reference only.

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
