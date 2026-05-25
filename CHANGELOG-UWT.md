# CHANGELOG-UWT — ALF UW Template Integration (Track 4)

Per-release notes for the UW Template integration track. Newest at top.

See [SPEC-UWT.md](SPEC-UWT.md) for the canonical spec; the rollup of pending
work for this track lives in [UW-BACKLOG.md](UW-BACKLOG.md) once items are
opened (none yet — Phase 0 is the seed release).

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
