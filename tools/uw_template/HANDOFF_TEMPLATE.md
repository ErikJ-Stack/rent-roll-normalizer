# UW Template Handoff — `<YYYY-MM-DD-slug>`

> Copy this file to `handoffs/YYYY-MM-DD-<slug>.md` and fill it in. Add a row
> to [`HANDOFF_TRACKER.md`](HANDOFF_TRACKER.md) at the top of the index table.

---

**Status:** Pending operator
**Template version:** vN → vM *(or "v4 in place" if no version bump)*
**Registry version:** before → after
**Triggered by:** *(BL ticket, chat date, user request, or substrate version)*
**Owner (Claude Code side):** Track 4 chat
**Owner (operator side):** Cowork → Excel

## Summary

*One paragraph. What changed on the Claude Code side, and what does the
operator need to do in the template to keep both sides consistent? Lead with
the why so the operator can sanity-check the request, not just execute it.*

## Template-side changes required

> Each numbered item is one discrete Excel edit. Include the sheet, cell or
> range, and the operation (add column / shift row / change format / etc.).
> Be precise enough that a Cowork session can re-author without re-reading the
> repo.

### 1. `<Sheet>!<cell or range>` — `<one-line operation>`

- **Before:** *(current state in v4 — value, formula, or empty)*
- **After:** *(desired state in v5)*
- **Styling:** *(font, fill, alignment, column width, number format — match
  neighboring cells unless noted)*
- **Data validation / named ranges:** *(if affected)*
- **Why:** *(short — link back to the substrate/parser/writer change that
  surfaced the need)*

### 2. ...

## Mapping updates

> Registry edits coupled to the template changes above. Show the diff as
> before/after pairs against `tools/uw_template/registry.json`. Run
> `python tools/uw_template/build_mapping_artifacts.py` after applying.

- **Concept `<key>`** (e.g. `rr_preleased_date`):
  - Before: `targets.v4 = {...}` *(verbatim relevant subset)*
  - After: `targets.v5 = {...}`
  - Status change: *(e.g. `gap_target` → `mapped`)*
  - Why: *(short)*

- **Registry-level changes:**
  - `registry_version`: `0.X.Y` → `0.X.Z`
  - `analyzer.substrate_version`: *(if changed)*
  - `templates.v5`: *(new block, mirroring `templates.v4` structure)*
  - `open_questions`: *(remove items now answered; add any new ones surfaced)*

## Writer-scope decisions

> Pure prose. Things the operator needs to *decide* (vs. *do in Excel*) that
> shape writer behavior in subsequent Claude Code work. Skip this section
> entirely if all the work is structural.

- **Decision needed:** ...
  - Options: ...
  - Recommendation: ...
  - Implication for writer: ...

## Verification checklist

> What the operator can spot-check after authoring the template, and what
> Claude Code will confirm post-handoff.

**Operator side (in Excel after authoring):**
- [ ] *(e.g. New column header at `<Sheet>!<cell>` renders correctly — bold, navy fill, frozen with surrounding header band.)*
- [ ] ...

**Claude Code side (next chat, on receipt of the updated template):**
- [ ] Drop file at `Sample Files/ALF_UW_Template_v5.xlsx`.
- [ ] Extend `registry.json` `templates.v5 = {...}` block.
- [ ] Update affected concept entries with `targets.v5` keys.
- [ ] Re-run `python tools/uw_template/build_mapping_artifacts.py`.
- [ ] Smoke-test `populate_uw_template(..., template_version='v5')` against the empty + Homestead fixtures.
- [ ] Mark this handoff **Verified** in HANDOFF_TRACKER.md.

## Cross-references

- **Backlog:** `UW-BACKLOG.md` — *(BL ticket if applicable)*
- **Spec:** [`SPEC-UWT.md`](../../SPEC-UWT.md)
- **Changelog:** [`CHANGELOG-UWT.md`](../../CHANGELOG-UWT.md)
- **Authoritative contract:** `Deals/Acquisition/_Template/ALF Templates/Documentation & Maps/2026-05-25-UW-OUTPUT-HANDOFF-CONTRACT.md` *(external)*
- **Registry entries affected:** *(list keys)*
- **Substrate version mapped against:** *(e.g. v0.2.14)*

## Notes for Cowork

*Optional. Anything Cowork specifically needs to know — e.g. don't roundtrip
through Google Sheets / LibreOffice (BL-0018 lesson on lowercase `minifs` /
`_xludf.` prefixes), preserve existing chart objects on the template, etc.*
