# Chat Journal — rent-roll-normalizer

A running log of substantive chat sessions on this repo. One entry per session.
Each entry captures: scope, what shipped, what drifted, and the commit(s) the
session produced. Use this for handoff between chats and for tracing why a
particular commit looks the way it does.

Newest at top.

---

## 2026-07-03 — Cross-track: whole-app efficiency pass (session-cache the ALF pipeline)

**Scope.** User-requested full-codebase review + efficiency improvements
("easy to use interface for underwriting"). Cross-cutting by explicit request.

**What shipped (uncommitted at session end — user to commit).**

- **ALF pipeline session cache (`app.py`) — the headline fix.** The ALF path
  re-ran the ENTIRE pipeline on every Streamlit rerun: RR re-parse, T12
  re-parse (with TWO full openpyxl loads of the 16-sheet Analyzer for the
  Description_Map), `write_output` rebuild, the 3-step combined-Analyzer
  build (3 chained openpyxl load/save round-trips), and the UW Template
  populate. The MF side already had signature-based caching (`_mf_sig`);
  ALF never got it. New `_session_cache(key, sig, compute)` helper +
  signatures over every input (upload `file_id` tokens, parse options,
  period date, scenario, UNMATCHED-resolutions hash). Verified via a new
  AppTest end-to-end smoke (patched `st.file_uploader` injecting the
  Homestead RR + T12 fixtures): first run ~5s, cached rerun **0.1s**, all
  3 downloads produced, no errors, both with and without T12.
- **Single descmap load:** the T12 branch loaded the Analyzer workbook twice
  back-to-back (`read_descmap_descriptions` + `_read_descmap_labels`); now
  one load serves both. `_read_descmap_labels` deleted (dead).
- **Dashboard tab empty-state bug:** `st.stop()` inside the Workspace tab
  halted the script before the Dashboard tab rendered, so it showed BLANK
  when no RR was uploaded (the `if rr_file is None` branch there was
  unreachable). Empty-state/parse-failure messages now written via
  `top_tab_dashboard.info/.warning` before each stop.
- **`dashboard_model.load_description_map`:** cache now keyed by resolved
  path (was a single slot that ignored the `analyzer_path` arg — latent
  stale-cache bug) + `try/finally` around `wb.close()`.
- **`uw_template_writer._load_registry`:** cached on (path, mtime) —
  registry.json no longer re-parsed per populate call. Verified read-only
  downstream (no mutation of the shared dict).
- **MF stale labels:** cockpit chip hardcoded "MF UW MODEL v15" →
  `BUNDLED_MF_MODEL_VERSION`; `model_src` caption hardcoded v15 →
  bundled-file name. `_mf_file_token` renamed `_file_token` (now shared).
- Unused `CONDENSED_COLUMNS` import dropped from app.py.

**Verification.** Full pytest suite 88 passed / 1 skipped; pyflakes clean
(pre-existing nits only); AppTest empty-state smoke (both modes) + e2e smoke
(RR-only and RR+T12) green.

**Phase 2 (same session, user-approved "go ahead"): deal-package flow +
mapping memory.**

- **Deal package row (app.py).** The old "Export" section put the Analyzer
  download AND the whole UW Template populate flow (report, expander,
  statuses) inside the right half of a 2-column split. Restructured: both
  builds now run up front (session-cached, outside any column), then a
  single 3-column row presents **1 · Normalized RR · 2 · Populated
  Analyzer · 3 · Populated UW Template** side by side, each with its gate
  reason or error in place when unavailable. New **deal-package zip**
  download (all three files, ZIP_STORED since xlsx are already zip
  containers) appears when everything is ready; the UW populate report
  moved below the row at full width. Widget keys unchanged (`dl_rr` /
  `dl_combined` / `dl_uw_template` / `dl_combined_disabled`; new
  `dl_uw_disabled`, `dl_zip`). Error scoping improved: Analyzer-build
  exceptions (capacity/AR/ValueError) land in col 2, UW-writer exceptions
  in col 3 — previously one try wrapped both.
- **T12 mapping memory (app.py + .gitignore).** UNMATCHED matcher
  resolutions now persist across sessions in `t12_mapping_memory.json`
  (repo root, gitignored — real GL descriptions; ephemeral on Streamlit
  Cloud redeploys, durable locally). On T12 parse, remembered descriptions
  auto-resolve (surfaced as "🧠 N auto-mapped from memory"), flow into
  `new_descmap_entries` as usual, and the matcher form only shows genuinely
  new descriptions. Saves merge on form submit; load/save are best-effort
  (corrupt/missing file → empty memory, write failure never blocks).
- **Mapping-memory viewer (Advanced expander).** Only place to inspect or
  reset the memory — matters on Streamlit Cloud where there's no shell
  access to the JSON file. Checkbox reveals the remembered-mappings table;
  "Clear memory" deletes the file (does not un-apply this session's
  resolutions). AppTest-verified: renders when memory exists, table shows
  on tick, Clear deletes the file and the controls disappear.

**Verification (phase 2).** Mapping-memory helpers round-trip tested
(merge, invalid-entry drop, corrupt-file recovery); AppTest e2e re-run:
4 download buttons (3 files + zip), zip verified to contain exactly the
three workbooks, cached rerun still 0.1s; empty-state smoke both modes;
full pytest suite 88 passed / 1 skipped.

**Carry-forwards / suggestions surfaced to user (not applied).** Parser-level
micro-optimizations (double `iterrows()` in normalizer/pre_cleaner — now
moot per-rerun since parses are cached); bare-except narrowing in
ar_normalizer/mappings (intentional-looking fallbacks, needs a decision);
`use_container_width` deprecation (removed after 2025-12-31 per Streamlit
warning — sweep when the Cloud runtime version is confirmed); session-state
now holds output bytes (~tens of MB/session — fine for single-operator);
ALF/MF status-taxonomy duplication (deferred until the planned `alf/`+`mf/`
package split); mapping-memory has no in-app viewer/editor yet (delete the
JSON file to reset); a true cross-deploy persistence layer for the memory
would need external storage (gist/S3/DB) — flagged, not built.

---

## 2026-06-29 — Track 4-MF: MF UW Model v25 absorption (MF v0.8.0)

**Scope.** Operator dropped `MF_UW_Model_v25.xlsx` ("update the template for the
mf side"), superseding the v20 absorbed 8 days earlier (PR #63, still open).
Continued on the same `mf-v20-model-absorption` branch.

**What shipped.** Diffed v25 against the v20 baseline cell-by-cell. **All four
writer target sheets are anchor-identical to v20/v15** (T-12 Analysis @106 A–P,
Rent Roll Analysis @273 A–AK / data 273–1772 / footer 1775, Prop Info col A
labels + col B values rows 4–47, Rental Comps @7/8) → **no concept target moved,
no writer logic change.** v25's deltas are on non-target sheets + display layers:
`Dashboard`→`Dash` rename, `Data Refresh` removed (24→23 sheets, several
reordered), RR helper cols trimmed to AL-only (v20's blank AM–AP dropped; AL is
outside the writer's A–AK clear band → preserved), Prop Info trailing cols E/F
dropped. `xl/metadata.xml` preserved (7→7 `cm` via `_restore_dynamic_arrays`).

**New finding (cosmetic):** v25 carries 2 extended (x14) data-validation
dropdowns on `Rent Roll Analysis` that openpyxl can't model and drops on save.
The writer fills those Status/Type cells with real values regardless, so it's an
analyst data-entry aid only — surfaced in the writer's report warning (alongside
comments/add-in/doc-props) and the handoff "notes for operator" (Excel re-save
to recover). No `_restore_data_validations` repair built — proportionate to a
2-dropdown loss; flagged to the user as an offer.

Changes: `assets/MF_UW_Model_v25.xlsx` committed (v15 + v20 retained); `app.py`
`BUNDLED_MF_MODEL_PATH`/`_VERSION` → v25; `mf_uw_model_writer.py` docstring +
report warning repointed; registry 0.3.0 → 0.4.0 via
`tools/mf_uw_template/_absorb_v25.py` (templates.v25 + `targets.v25`
verbatim-inherit ×90 + `primary_template="v25"`); artifacts regenerated (v25
primary); `tests/test_mf_uw_model_writer.py` repointed to v25. Handoff
`tools/mf_uw_template/handoffs/2026-06-29-mf-uwt-v25-absorption.md` (**Verified**).

**Verification.** MF writer + RR/AR suites 10/10 green; `app.py` parses;
end-to-end populate against v25 yields a 23-sheet, reloadable workbook with
`Dash`. The openpyxl DV-extension warning on load is the expected (documented)
x14 DV drop.

**Carry-forwards.** PR #63 (opened for v20) now also carries v25 — retitle/update
to cover v15 → v25. Optional future work: `_restore_data_validations` repair if
the populated model's Status/Type dropdowns matter downstream.

---

## 2026-06-21 — Track 4-MF: MF UW Model v20 absorption (MF v0.7.0)

**Scope.** Operator dropped `MF_UW_Model_v20.xlsx` ("Update the MF template use.
review the mapping also."), jumping the bundled MF model v15 → v20.

**What shipped.** Verified the new file cell-by-cell against the binary (not a
handoff note). **All four writer target sheets are layout-identical to v15** —
T-12 Analysis Layer 1 @106 (A–P), Rent Roll Analysis grid @273 (A–AK, data
273–1772, diagnostic anchors G5/I5/N5/Q5/T5 → `273:1772`, footer @1775), Prop
Info col B (rows 4–47), Rental Comps SUBJECT @7 / anchor @8 — so **no concept
target moved** and the writer needed **no logic change**. v20's deltas are all
display/formula-only: **+`Dashboard` sheet** (idx 1; sheet_count 23→24),
**+ per-row chart-helper formula cols AL–AP** on Rent Roll Analysis (outside the
writer's A–AK / cols-1–37 clear band → preserved), and **+ `xl/metadata.xml`**
(Excel-365 dynamic arrays, 7 `cm` cells; v15 had none). The writer's
`_restore_dynamic_arrays` — a documented no-op on v15 — is now **active** and
preserves them (verified 7→7 `cm` markers; metadata.xml present in output).

Changes: `assets/MF_UW_Model_v20.xlsx` committed (v15 retained for
override/history); `app.py` `BUNDLED_MF_MODEL_PATH` → v20 + new
`BUNDLED_MF_MODEL_VERSION = "v20"`; `mf_uw_model_writer.py` docstring repointed +
the stale "metadata.xml absent → restore is a no-op" note corrected; registry
0.2.0 → 0.3.0 via `tools/mf_uw_template/_absorb_v20.py` (templates.v20 +
`targets.v20` verbatim-inherit ×90; v20 now primary); artifacts regenerated;
`tests/test_mf_uw_model_writer.py` repointed to v20 + new
`test_dynamic_arrays_preserved`. Handoff
`tools/mf_uw_template/handoffs/2026-06-21-mf-uwt-v20-absorption.md` (**Verified**).

**Verification.** MF writer + RR/AR suites 10/10 green (with `xlrd` installed —
the only initial failures were the missing module + a gitignored .xls fixture,
both environmental); T-12 + OM suites unaffected; `app.py` parses; end-to-end
populate against v20 yields a 24-sheet, reloadable workbook with `Dashboard`.

**Carry-forwards.** None blocking. v15 stays committed as the override path. Not
yet committed — `git add` + commit pending (clean tree at session start).

---

## 2026-06-16 — Track 4 + Track 2: UWT v0.11.0 — operator template v11 + Analyzer substrate v0.3.0 (cross-track)

**Scope.** Operator dropped two binaries together — `ALF_UW_Template_v11.xlsx`
and a new `ALF_Financial_Analyzer_Only.xlsx` (substrate v0.3.0) — "update as
needed." No handoff brief; both absorbed after a full binary diff against the
committed v8 template / v0.2.16 bundled analyzer. (Model: opus-4-8.)

**Template v11 (registry 0.7.0 → 0.8.0, bundled default v8 → v11):** all 189 v8
targets verified label-identical; the substantive change is the RR Analysis
paste grid re-anchored **214 → 224** (header 213 → 223) — a new "S. CONCESSIONS
AUDIT" block at rows ~205-211 pushed the grid down 10 rows, and every aggregate
now reads `$224:$623`. `_absorb_v11.py` re-anchors 40 rent_roll targets; the
writer already derives the anchor from the templates block (no writer-logic
edit — same pattern as v8's 211→214). The **v8 >176-bed fill-down quirk is
fixed** (K/L/V/W cover the full band now). Prop Info +4 rows are all manual
market-data (no writer targets). metadata.xml absent but unneeded (573 legacy
CSE arrays, zero spill functions). `_T12_LAYOUT["v11"]` = v8 (T-12 unchanged).
Detection: new v11 stage (A223 "Unit/Bed" / A205 "CONCESSION") ahead of v8.

**Analyzer v0.3.0 (operator-authored wholesale replacement, BL-0021 pattern —
no migration):** a drop-in. UW Output +1 row ("Bad debt" at row 72, bottom —
rows 1-71 unchanged → registry uw_output sources stay correct); T-12 Analytics
+1 col ("Other Care (OTH)" at E — no code reads it by column); Description_Map
424 → 579 GL descriptions (better T12 mapping; named ranges auto-extend).
Write-target sheets layout-compatible; the file ships clean (the 600 "non-empty"
Rent Roll Input rows are formula scaffolding in cols T/U/AH, not deal data).
`ANALYZER_SUBSTRATE_VERSION` 0.2.16 → 0.3.0.

**Verification.** Full pipeline e2e (Homestead RR v2 + March 2026 T12) against
the **new v0.3.0 analyzer → v11 template**: T12 parsed 101 GL rows / **0
unmatched** (expanded Description_Map), paste at **224** (header A223 intact,
spacers empty), 176 beds, NER/Total-Ancillary/EGI/EBITDARM/EBITDAR formulas
preserved, **121 concepts computed in-Python** (evaluator fallback handles the
fresh analyzer), 16 sheets. Tests: +2 (v11 smoke + e2e); v8 tests pinned to
"v8"; empty-analyzer no_source threshold recalibrated for the v0.3.0 scaffolding
(caches structural zeros). **All 8 writer tests + uw_output_model + dashboard +
mf_dashboard green.** (MF pytest suites need pytest — pre-existing, unrelated.)

**Commits.** UWT_VERSION 0.10.0 → 0.11.0. `_absorb_v11.py` retained as audit
trail. Carry-forward: the duplicate legacy header at row 210 (v8 lineage) may
persist in v11 — cosmetic, operator may delete in a future pass.

---

## 2026-06-12 — Track 4: UWT v0.10.0 — operator template v8 absorbed; paste grid re-anchored 211→214 (+ same session: cockpit UI redesign, cross-track)

**Scope.** Operator: "use this as the new updated version template for ALF UW
template" (`Deals/…/ALF Templates/ALF_UW_Template_v8.xlsx`, 2026-06-11,
self-stamped "Template Version 9.0" — registry keys on the filename). No
handoff brief existed; the delta was discovered by full binary diff vs the
committed v6 (1,112 true cell diffs after ArrayFormula-text normalization —
the naive diff shows 1,641 because openpyxl ArrayFormula objects compare by
repr; normalize on `.text`).

**The headline finding — stale paste anchor was a live v6 bug.** Every Rent
Roll Analysis aggregate reads rows **$214:$613**, in v8 AND in the committed
v6 rev2: the operator's true grid is header row **213**, data **214+**. The
writer's hardcoded 211 anchor (plus the v0.9.0 "restore header at 210" fix,
which had treated the missing 210 header as the bug rather than as evidence
the grid had moved) meant beds #1–2 fell outside every diagnostic and bed #3
overwrote the operator's header. Fixed via the v8 absorption: registry
re-anchors 39 rent_roll targets to `…214+`; the writer now derives
`rr_paste_start` + header-preflight row from the registry templates block
(v4–v6 keep 211/210; v8 → 214/213).

**Shipped (UWT 0.9.1 → 0.10.0, registry 0.6.0 → 0.7.0, 196 concepts):**
`tools/uw_template/_absorb_v8.py` (idempotent; templates.v8 block + 39
re-anchored / 149 inherited targets + new derived `rr_ner_amort` AV214+);
bundled template → `assets/ALF_UW_Template_v8.xlsx` (checksum-verbatim copy;
v6 retained for override); `_T12_LAYOUT["v8"]` = v6 rows (all anchor rows
verified cell-identical — EGI N80 / EBITDARM N134 / EBITDAR N135 / EBITDA
N136 / Section I 141 / Section J 194–196); writer default + CLI → v8;
`_detect_uw_template_version` gains a v8 stage (AV210/AV213 "NER") and fixes
a latent bug (v6 probes read pre-rev2 rows A77/A114 → uploaded rev2 files
mis-detected as v5; now A80/A117 first). Tests: +2 (v8 smoke / v8 e2e —
paste at 214, header A213 + spacers 211–212 untouched, AP/AT/AV template
formulas survive); v5/v6 tests pinned; **all 6 writer tests + UW output model
suite green** (Homestead e2e: 89 written / 2,301 cells / 176 rows from 214 /
dynamic arrays restored).

**v8 template content (no writer involvement):** NER $/mo (amort) col AV
(amortizes concessions over the AC174 term input, occupied rows only) + NET
EFFECTIVE / CONCESSIONS and RECENT MOVE-INS blocks (rows 174–191); AT/AU now
template formulas (were analyst-input); T-3/T-1 diagnostics at T-12 Analysis
row 9; Scenarios col-F CHOOSE refactor; Waterfall rebuilt as IRR-hurdle.

**Carry-forwards:** (1) **Template quirk for operator** — K/L/V/W fill-downs
only cover rows 214–389 (176 data rows); deals >176 beds lose Total LOC /
Total Sched / PSF on overflow rows until filled down to 613 (AA/AB cover 345
rows). Recorded in `templates.v8.template_quirks`. (2) The duplicate legacy
header at row 210 is cosmetic — harmless; operator may delete in a future
pass.

**Also this session (cross-track, operator-directed):** the cockpit UI
redesign shipped — see COSMETIC-CHANGES.md 2026-06-12 entries (graphite/teal
terminal theme + command bar + live ledger + cockpit login + light/dark
toggle) — and the prior session's uncommitted UWT v0.9.1 work was committed
(`df08e16`).

---

## 2026-06-08 — Adopt operator's durable Excel-native v6 template binary (Track 4)

**Track:** Track 4 (UWT). Operator: "update and use this ALF Template as the most
current template," pointing at a re-authored
`…/Deals under review/Ai Underwriting/Templates/ALF_UW_Template_v6.xlsx` (Jun 8,
257,925 bytes vs. the committed 221,604). UWT **v0.9.0 → v0.9.1**; registry and
writer unchanged.

**What it was.** The **Excel-native save** the 2026-05-28 v6 handoff follow-up (a)
had been waiting for. The committed `assets/ALF_UW_Template_v6.xlsx` was last
written by openpyxl (the 2026-06-05 B56 patch) → 37-part zip, openpyxl-style
comments, no `webextensions/`. The new file is a **42-part Excel-native binary**:
full `xl/metadata.xml`, `xl/webextensions/` (Claude-for-Excel add-in),
`calcChain.xml`, `sharedStrings.xml`, native `comments1.xml`. So Section R/S
dynamic-array spills now ship from a healthy source rather than a Python-repaired
one.

**Diligence before adopting (verify-canonical-source discipline).**
1. **Preflight** — confirmed current state had moved well past CLAUDE.md's header:
   UWT 0.9.0, registry 0.6.0 (195 concepts), v6 already the bundled default.
2. **Zip-part inventory diff** (openpyxl quirk #6) — new file gains
   metadata/webextensions/calcChain/sharedStrings + Excel-native comments; the
   worksheet byte-size diffs are the expected Excel-vs-openpyxl serialization
   (shared strings vs inlined), not structural.
3. **Sheets / order / defined names** — identical (16 sheets).
4. **Full cell-level value+formula diff across all sheets** — only **10 diffs**,
   all benign operator refinements on **analyst-driven** cells, **none a registry
   target** (checked against all 195 concepts): Scenarios `B13`/`G13`/`E79`/
   `C123:E123` (reference/constant tweaks), Rent Roll Analysis `F9:F12`
   (AVERAGEIFS now `IFERROR`-wrapped). T-12 Analysis and the RR paste grid are
   content-identical.
5. **Prior programmatic fixes present natively** — B56:M56 `=C140..=N140`
   (N56 `T-12 Total`); Section-D rev2 `B22=N83`/`B23=N86`/`B24=N80`; total chain
   N80 (EGI) / N134 (EBITDARM) / N135 (EBITDAR) / N136 (EBITDA).

**Shipped.** Replaced `assets/ALF_UW_Template_v6.xlsx`; bumped `UWT_VERSION`
0.9.0 → 0.9.1 + comment block in `app.py`; CHANGELOG-UWT v0.9.1 entry;
HANDOFF_TRACKER top row (Verified) closing the "re-drop Excel-resaved v6 binary"
carry-forward. **Writer suite green** — all 4 `test_uw_template_writer.py` tests,
identical outcomes to the prior binary (195 concepts; populated-Homestead e2e
89 written / 2,301 cells; `dynamic_arrays_restored: 1`; 176 RR rows from 211).

**Note for future Track-4 chats.** The committed v6 asset is now an
operator-authored Excel-native file — do **not** round-trip it through openpyxl
for authoring (quirk #6 would drop webextensions again). Template-side changes
still go through Excel/Cowork per the handoff protocol.

---

## 2026-06-05 — Retire UW Output divergence whitelists + interim B56 repoint (Track 4 / test)

**Track:** Track 4 (UWT) + test-fixture maintenance. Started as a state-review
("what's open?") that surfaced three loose threads; the user then supplied the
v0.2.16 Homestead Analyzer to close the first one. Shipped as **PR #58** (merged
to main, `e318f31`).

**1. Retired both UW Output divergence whitelists (closes the BL-0028 test
follow-up).** `tests/test_uw_output_model.py` carried `_AUTO_EXPENSE_DIVERGENCE`
(UWT v6 Auto Expense, $6,061.32) and `_REMAP_2P_DIVERGENCE` (substrate v0.2.15
2nd-Person re-map, $32,220.49) — pinned gaps that existed only because the cached
Homestead fixture predated those fixes. The user dropped a **v0.2.16** Analyzer
(Auto Expense non-labor row at T12 Analytics 92), but it was a fresh app-built
file with **no cached formula values** (every `data_only` read = None). Drove
**Excel via PowerShell COM** (`New-Object Excel.Application` → `CalculateFullRebuild`
→ `SaveAs` 51) to recalc + save a computed copy into the gitignored
`Sample Files/Analyzer with … .xlsx` (Dropbox original untouched). With cached
values present, engine == cached **to the penny on all 42 concepts** — both
whitelists + their divergence-check branches deleted; the regression is now a flat
penny-match. EGI $7,001,956.79, EBITDARM $1,761,421.43, EBITDA/NOI $1,411,323.58.
All 5 suites green. (This is the canonical fixture-rebuild procedure for future
substrate bumps: COM-recalc the app-built Analyzer before it can serve as the
cached fixture.)

**2. Found + fixed a cosmetic v6 rev2 B56 mispoint.** State review caught
`T-12 Analysis!B56:M56` (Layer-3 monthly header row) pointing at `=C125..=N125`
(row 125 = "Permits, Licenses & Dues" expense, value 0) instead of the rev2
Layer-1 raw month-header row at **140** (`C140:N140 = Apr-25 … Mar-26`). **Same
openpyxl-quirk-#4 partial-repoint class as v0.7.1's B56 fix** (`=C122`→`=C137`):
v0.7.1 fixed the rev1 instance, but the v6 rev2 "Other Care" restructure shifted
the raw grid +15 rows and the rev2 absorber missed B56:M56. Filed handoff
`handoffs/2026-06-05-uwt-v6-rev2-b56-monthly-header-repoint.md` + tracker row, then
applied the **interim programmatic patch** `_fix_v6_rev2_b56_monthly_headers.py`
(mirrors the rev2 Section-D fix): repoints the 12 cells to `=C140..=N140` on the
committed `assets/ALF_UW_Template_v6.xlsx`, restoring the file's own
`xl/metadata.xml` via `_restore_dynamic_arrays` (faithful — N56="T-12 Total"
untouched, no dynamic-array anchor edited). Idempotent, pre-flight gated on row
140. UWT writer suite green (v6 rev2 default — 195 concepts,
`dynamic_arrays_restored: 1`). **Cosmetic only** — no SUMIFS/total depends on
B56:M56; populated outputs were already numerically correct. Handoff stays
**Pending operator** for the durable Deals-folder Excel re-author (the Windows
session couldn't reach the macOS Deals path).

**Merge side effect (benign).** The PR branch was cut from `mf-cache-result`
rather than `main`, so merging #58 carried the stacked MF PRs **#54–#57** (OM
intake v0.5.0, OneSite/.xls v0.5.1, loading overlay, progress %, cache result)
into `main` as well. All four had `base=main` and are now correctly MERGED — the
intended destination, just delivered via #58's merge. main == origin/main; tests
green.

**Commits (PR #58):** `1409c7a` (whitelist retirement + B56 handoff) · `e53a64c`
(interim B56 repoint patch).

**Still open after this session:** (a) durable B56 re-author in the operator's
Deals-folder v6 (handoff Pending operator); (b) MF redIQ Sortable-RR ancillary
breakouts W–AK (SPEC-MF §2.5, best-effort); (c) BL-0019 persistent audit log
(unchanged); (d) SPEC-MF §2 still says "scoped, not built" — stale, the parser
shipped (one-line doc fix).

---

## 2026-06-05 — MF v0.5.1 — RR: RealPage OneSite format + legacy .xls support (Track 4-MF P1)

**Track:** Track 4-MF (MF RR intake). User dropped two Ascend Brunswick Village
(MF_NC_Leland) deal files — a rent roll `.xls` + a T-12 `.xlsx` — with two
warnings showing (T-12 "161 lines; Layer 1 holds 150 — extra truncated" + the
standard Excel-writer-drops-annotations note). No explicit instruction; the
implied task = populate the MF UW Model for the deal.

**Two findings on investigation:**
1. **T-12 truncation is harmless to NOI.** The Yardi-numbered T-12 parses cleanly
   (161 leaf GL lines, all correctly classified, NOI $2,052,515). The model's
   Layer-1 grid holds 150 rows; the 11 truncated lines (151–161) are *all*
   EXCLUDED below-the-line items — Capital/Renovation, Startup Costs, 6× Lease-Up
   costs, Prior-Year Expenses, Amortization ($81,566) — that never feed the NOI
   SUMIFS. NOI/OpEx complete; only the audit trail of those non-operating lines
   is lost. (Extending Layer-1 capacity is a model-side handoff follow-up.)
2. **The RR was unsupported.** It's a genuine legacy **.xls (OLE2)** that
   `mf_normalizer` couldn't read (openpyxl-only), AND a RealPage **OneSite "RENT
   ROLL DETAIL"** layout the parser didn't recognize (validated against
   redIQ/Hidden-Lakes). Asked the user (AskUserQuestion) → **"Add OneSite + .xls
   support"**.

**Shipped (MF v0.5.1):**
- `mf_normalizer.py`: `_read_grid()` (openpyxl + xlrd, OLE2-sniffed, .xls dates
  converted) replacing `_load_ws`; `_parse_onesite()` / `_is_onesite()` — dedup
  units across lease rows (current + Applicant/Pending), base rent → N (so
  Scheduled GPR isn't fee-inflated), horizontal fee cols → W–AK, pre-leased
  vacants take committed rent from the applicant row into N (M=0), `As of Date:`
  → `period_hint`. Mapping driven by the model's Layer-3 (B26 Market GPR=ΣL×12,
  B27 Scheduled GPR=ΣN×12, status table sums N incl. a Vacant-Leased/Pre-leased
  row → confirmed N = base contracted rent).
- `mf_mappings.py`: `_STATUS_RULES` += NTV→On Notice, Applicant/Pending fallbacks.
- `app.py`: MF RR uploader accepts .xls/.xlsm.
- Tests: `test_onesite_synthetic_xls` (committed synthetic fixture
  `tests/fixtures/mf/onesite_synthetic.xls` + `_build_onesite_synthetic.py`,
  xlwt authoring-only) + `test_rr_onesite_ascend` (skip-if-absent, 334 units).
  Full MF suite green (27 prior + 2 new).
- Docs: CHANGELOG-MF v0.5.1, SPEC-MF §2.2 + version, CLAUDE.md.

**Verified on the deal:** populated MF UW Model — 334 RR units (7,489 cells) +
150 T-12 lines. Market GPR $6.94M, Scheduled GPR $5.22M, ancillary ~$402K/yr,
75.1% physical occupancy, T-12 NOI $2.05M. Output written to the deal's UW/ folder.

**Carry-forward:** T-12/AR MF parsers are still openpyxl-only (.xlsx). Layer-1
T-12 capacity (150 rows) is tight for large Yardi charts of accounts — a model
handoff could extend it, though current truncation is NOI-safe. Not committed yet
(awaiting user go-ahead).

---

## 2026-06-04 — MF v0.5.0 — OM (Offering Memorandum) intake ships (Track 4-MF P3)

**Track:** Track 4-MF. User said "we were working on MF om intake — check local
files." It wasn't: an exhaustive sweep (working tree, stash, all worktrees,
`git fetch --all`, `--diff-filter=A` across all refs) confirmed OM intake had
**never been committed anywhere** — genuinely greenfield. User then supplied
three real OM PDFs and said "use these." (Lesson reinforced: the work that
"already existed" was never in git — this session commits it so it's findable.)

### What shipped

- **`mf_om_extractor.py`** — `parse_mf_om(source, engine="llm"|"basic",
  api_key=) -> MFOMResult`. PyMuPDF text extraction (no OCR needed — all 3 OMs
  are text-based, ~1300+ chars/page). **LLM engine (default):** OM text →
  Claude structured-output tool schema (maximal scope: property facts, market,
  comps, pro-forma) → typed dataclasses. **Basic engine (no-API fallback):**
  deterministic `label\nvalue` scan with plausibility guards (rejects a year
  grabbed as a unit count). Engine is a UI/caller selection per user decision
  ("use Claude API but make this a selection/option").
- **`mf_uw_model_writer.populate_mf_model(..., om=)`** — writes Prop Info
  `B5:B47` (details + market) + Rental Comps `Q8:AD22` (15 comps). RR units/name
  win; `Z`/`AA` eff-rent/$-per-SF formulas + SUBJECT row 7 preserved; bedroom
  counts derive from unit-mix; occupancy → fraction. **Broker pro-forma captured
  but intentionally NOT written** (UW trusts the T-12).
- **`app.py` `_render_mf_intake`** — OM PDF uploader + AI/Basic engine radio +
  API-key field (or `st.secrets`/env); summary metrics + comp-table preview;
  `om=` into populate. `requirements.txt` += `pymupdf`, `anthropic`.
- **Registry → v0.2.0** via `tools/mf_uw_template/_add_om_concepts.py`
  (idempotent): +44 OM concepts (46→90; 63 mapped). OM open-question retired.
- **Docs:** SPEC-MF §3, CHANGELOG-MF MF v0.5.0, CLAUDE.md Track 4-MF row.

### Verification

`tests/test_mf_om_extractor.py` (9) — coercers, LLM JSON→dataclass mapping
(synthetic Ascend-shaped payload), writer integration (cells + formula
preservation + RR-override), basic engine on the 3 real OMs. **36/36 MF tests
green.** Basic engine on real OMs: Blairstone 376u/1988/32.18ac/42bldg/692pk/Leon;
Avana 264u/1985/Prince William; Ascend 334u/2024.

### Not verified / follow-up

- **LLM path not run live** — no `anthropic` SDK / API key in this env. The
  schema, prompt, JSON→dataclass mapping, and writer are verified via a synthetic
  payload; live extraction quality needs an analyst spot-check with a key.
- Image-only/scanned OMs would need an OCR pre-pass (extractor raises a clear
  error on near-empty text).

### Commit

(committed on branch `mf-om-intake` — see PR.)

---

## 2026-05-30 — UWT v0.8.1 — v6 template Section-D income-summary repoint

**Track:** Track 4. Operator dropped a populated Briar Glen UW Template output
("the T12 tab isn't populating properly").

### Diagnosis: Layer-3 data fine, Section D formulas stale

The data tier was fully populated (Base Rent MC $3.75M, labor, non-labor opex,
monthly grid, Section I raw — all correct). The bug was in the **T-12 Analysis
Section D** diagnostic cells: `B22`/`B23`/`B24` (GPR / Net Rent / EGI) read $0
because they still referenced the **v5** income rows `=N58`/`=N63`/`=N69`. In
v5 those were GPR/NetRent/EGI; in v6 the operator's income restructure moved
GPR to the diagnostic sub-block (N80), Net Rent to N83, and EGI up to N77 — so
N58/N63/N69 in v6 are the typically-$0 "Base Rent IL" / "LOC AL" / "Meal
Income" lines. `B25` Economic Occupancy % (B23/B22) read 0 as a consequence.

**Same openpyxl-quirk-#4 partial-repoint as v0.7.1's `B56:M56` miss** — the
operator's repoint pass fixed the EGI chain (B5/B9/B11: N69→N77) but skipped
Section D. Confirmed by diffing the v5 template (N58/N63/N69 = GPR/NetRent/EGI
there → the old refs were correct in v5). **Not a writer/data bug — a blank
template formula bug.**

### What shipped

- **`tools/uw_template/_fix_v6_section_d_refs.py`** — repoints
  `assets/ALF_UW_Template_v6.xlsx` `B22=N80`/`B23=N83`/`B24=N77`, with a
  label pre-flight (asserts N80/N83/N77 carry GPR/NetRent/EGI before editing),
  then re-restores `xl/metadata.xml` + 554 Section R/S `cm` markers from v5
  (openpyxl strips them on save). Mirrors the v0.7.1 fix-script pattern.
  Idempotent; zip 40 parts; sheet count 16; v0.7.1 B56:M56 fix intact.
- **Corrected copy of the operator's output** at
  `Downloads/Briar_Glen_UW_Template_2025-12-31_normalized_FIXED.xlsx` (in-place
  3-cell repoint + metadata restore) — Briar Glen Section D now GPR $5,736,477
  / Net Rent $3,754,025 / EGI $3,859,123.
- Docs: CHANGELOG-UWT v0.8.1, handoff brief
  `2026-05-30-uwt-v6-section-d-income-refs.md` (Verified) + tracker row,
  `UWT_VERSION` 0.8.0 → 0.8.1.

### Verification

Fix-script 11 checks pass; idempotent. End-to-end populate of the fixed
template (Homestead, v6): B22/B23/B24 → =N80/=N83/=N77 resolving to GPR
$9,524,893 / Net Rent $6,951,136 / EGI $6,964,627; 101 concepts / 516 monthly
cells. All 5 suites in `tests/test_uw_output_model.py` green.

### Flagged, not fixed

Section F rows 41/47 (RE Taxes / P&C "T-12 Actual") show $0 + "⚠ not in T-12"
despite the actuals existing in Layer 3 (N117/N112). Those are analyst-input /
pro-forma triangulation cells — literal `0` in v5 too, never auto-pulled. By
design. A future revision could optionally wire `B41=N117`/`B47=N112`, but
that's an operator design call.

---

## 2026-05-30 — Substrate v0.2.16 — T12 Analytics "Auto Expense" non-labor row (BL-0028)

**Track:** Track 3 (substrate). Picked the most actionable open item off
UW-BACKLOG — BL-0028, filed at the end of the 2026-05-29 v0.8.0 cleanup as the
substrate companion to the UWT v0.7.0 engine fix.

### The bug

The Python engine (`dashboard_model._LABELS_NON_LABOR`) had folded `Auto
Expense` into the non-labor opex sum back in UWT v0.7.0, but the **Excel
substrate never got the same fix**. `T12 Raw Data!B63` carries the `Auto
Expense` GL label (so the dollars aggregate), but `T12 Analytics` Section 3's
non-labor block (`A79:A102`, summed at `E103=SUM(E79:E102)`) had no Auto
Expense line — only `Auto insurance` (A91). The dollars fell out of opex →
EBITDARM/EBITDAR/EBITDA (and the Dashboard / UW Output / UW Export layers that
mirror them) overstated NOI by exactly the Auto Expense amount. Engine said one
thing, substrate said another; engine was right.

### Pre-flight made this a clean one-row insert

The risk was the BL-0001 qualified-range-endpoint trap (inserting above the
heavily-referenced EBITDA chain + cap-rate section). A blast-radius scan
de-risked it before any code:
- **187 cross-sheet refs** into T12 Analytics (Dashboard, UW Output ×34, AR ×1)
  are **all single cells** — no range whose endpoint could be mis-shifted.
- **No chart** references T12 Analytics (all 6 Dashboard charts read `Dashboard!`
  cells) — the v0.2.9 chart-link lesson doesn't apply.
- **No data validation** on the affected rows.
- The **only** within-sheet range crossing row 92 is the non-labor
  `SUM(E79:E102)` — which is exactly what we *want* to auto-extend.

So inserting at row 92 (right after Auto insurance, *inside* the SUM range)
lets the endpoint auto-extend `E102→E103` on the shift sweep, capturing both
the new row and the shifted real rows. No manual SUM surgery, no endpoint drift.

### What shipped

- **`tools/migration/migrate_to_v0216.py`** — insert one row at T12 Analytics
  92 (`A92="Auto Expense"`, E92 INDEX/MATCH on `"Auto Expense"`, `F92==E92`,
  `G92==F92-E92`), mirroring A91; full-workbook +1 shift sweep (180 cells on the
  bundled file). Re-uses the verbatim `shift_row_refs_in_formula` /
  `shift_all_formulas` / `shift_merged_cells` utilities from `migrate_to_v021.py`.
  21-check verify, idempotent (gate: `Cover!B8 == v0.2.16` AND `A92 == "Auto
  Expense"`).
- **Bundled `ALF_Financial_Analyzer_Only.xlsx`** migrated in place v0.2.15 →
  v0.2.16 (16 sheets, 16 AZ4 anchors; zip-part inventory identical 39→39).
- **`app.py`** `ANALYZER_SUBSTRATE_VERSION` → `"0.2.16"`.
- Docs: CHANGELOG-T12.md entry, UW-BACKLOG BL-0028 → Shipped, CLAUDE.md Track 2
  table line.

### Verification

No LibreOffice available, so the math was proven the repo-test way — replicate
the formula chain in Python from the populated Homestead fixture's cached
`T12 Raw Data` values (PRE EBITDARM $1,767,482.75 reproduced the fixture's
cached `E108` to the penny → replication validated). Auto Expense =
**$6,061.32**; adding it drops EBITDARM **$1,767,482.75 → $1,761,421.43**
(−$6,061.32), EBITDAR/EBITDA **$1,417,384.90 → $1,411,323.58** (−$6,061.32) —
and $1,411,323.58 ties to the as-reported NOI ($1,411,324), matching the
engine. Applied the migration to the populated fixture end-to-end:
`E104=SUM(E79:E103)` now includes the Auto Expense row at 92; EBITDA chain
re-pointed (`E109=E52-E106`, `E111=E109-E107`, `E114=E111-E113`). All 5 suites
in `tests/test_uw_output_model.py` green before and after the bundled migration.

### Left for next session

The `_AUTO_EXPENSE_DIVERGENCE` whitelist in `tests/test_uw_output_model.py`
**stays** — it can't drop until the gitignored populated Homestead Analyzer
fixture is rebuilt against the fixed substrate (needs Excel to evaluate the
formulas so cached == engine). The substrate fix landing here is the
prerequisite; the rebuild + whitelist drop is the follow-up. (Same story for
the `_REMAP_2P_DIVERGENCE` whitelist vs a v0.2.15-rebuilt fixture.) Only
remaining Pending backlog item: BL-0019 (persistent audit log, Track 1).

---

## 2026-05-29 — UWT v0.8.0 — default template flipped to v6

**Track:** Track 4. Picks up carry-forward item #1 from the 2026-05-28 session
("flip the default template to v6"). Operator gave the go-ahead + pointed at
the Deals-folder v6 copy.

### Not a one-line flip — two writer passes were v5-hardcoded

The 2026-05-28 "what's left" framed the flip as constants + probe + smoke-test.
On inspection it was more: `_finalize_t12_layer3` (authors EBITDAR/EBITDA,
mirrors total formulas across the B–M monthly grid) and `_write_section_i_raw`
(Layer 1 raw paste + Section J reconciliation) were **hardcoded to v5 row
positions** (N63/N69/N85/N111/N116/N117/N118; Section I 123–172) and gated on
`template_version == "v5"`. v6 rebuilt the income section (EGI N69→N77, every
total shifted, raw band +15). A naive constant flip would have silently
regressed v6 on (1) monthly total reconciliation, (2) EBITDAR/EBITDA authoring
(v6 ships N132 as literal `0`, N133 blank — same gap v5 had at N117/N118), and
(3) Section I raw population — **none caught by tests** (there was no v6 writer
test; the journal's "verified end-to-end" was via the absorption script).

Verified the v6 row map cell-by-cell against `assets/ALF_UW_Template_v6.xlsx`
before writing code (per the repo's verify-canonical-source discipline).

### What shipped

- **Writer**: new `_T12_LAYOUT` per-version row map; `_finalize_t12_layer3` +
  `_write_section_i_raw` take the layout; call site gates on
  `_T12_LAYOUT.get(template_version)` (v5 + v6). Default `template_version`
  `'v5'`→`'v6'` (function + CLI). v6 has no v5-style Net Rent monthly line
  (`net_rent_row=None`); income subtotals N61/N65/N77 mirror across B–M instead.
- **App**: bundled path → `assets/ALF_UW_Template_v6.xlsx` (the v0.7.1 repaired
  40-part binary); `BUNDLED_UW_TEMPLATE_VERSION` → `"v6"`. `_detect_uw_template_version`
  made two-stage (v4-vs-v5+ then v5-vs-v6 on T-12 Analysis A77/A114).
- **Side-fix**: the detection stage-1 probe read AP210, but v5.1 moved "Care
  Level Tier" AP→AO — so every v5/v6 upload-override misclassified as v4
  (latent since v5.1; harmless because the bundled default uses the constant,
  not detection — but a v6 upload override would have broken). Now probes AO210
  with AP210 fallback.
- **Tests**: existing two pinned to `template_version="v5"` (regression kept);
  added `test_empty_analyzer_smoke_v6` + `test_populated_analyzer_e2e_v6`.

### Verification

All 4 writer tests + `test_uw_output_model` (5) + `test_dashboard_model` (27)
green. v6 Homestead: EGI `=N61+N65+SUM(N66:N76)`@N77, EBITDARM `=N77-N99-N126`@N131,
EBITDAR `=N131-N128`@N132 (authored), EBITDA `=N132`@N133 (authored), B77 mirror
`=B61+B65+SUM(B66:B76)`; 176 RR rows; dynamic arrays restored. `UWT_VERSION`
0.7.1 → 0.8.0.

### ⏭ Remaining (carry-forward, lower priority)

- **Operator-side:** adopt repaired `assets/ALF_UW_Template_v6.xlsx` into the
  `Deals/.../ALF Templates/` copy (Deals copy was locked/pre-fix at flip time);
  optionally re-add the Claude-for-Excel add-in (webextensions, not restored).
- **Rebuild test fixtures against substrate v0.2.15** to retire the
  known-divergence whitelists. The v6 e2e shows 21 no_source on the old fixture
  (the 14 new by-care income concepts aren't cached in it) — a fixture artifact,
  not a runtime gap (the app passes `computed_values`).
- **Registry `open_questions` housekeeping** (#2 2nd-Person source, #3 monthly
  grid — both now stale).
- **Backlog:** BL-0027 (README) + BL-0019 (audit log) still Pending.

---

## 2026-05-28 (later) — UWT v0.7.0 — v6 template absorbed (T-12 income restructure) + substrate v0.2.15

Long multi-track session. The operator dropped the v6 template + a meticulous release handoff; this session absorbed it Claude-Code-side. Earlier in the same session: RR v1.19.0 was re-implemented from a stale OneDrive view (already shipped as `5fc2a06` — caught via preflight, see "verify-canonical-source"); BL-0026 marked shipped; BL-0027 README modernized; v6 pre-work banked.

### What shipped (5 commits, all pushed)

- `9a51905` **registry → 0.5.0** (`_absorb_v6.py`): `templates.v6` + 70 retargeted T-12 Analysis concepts + 14 new. **Row map verified cell-by-cell against `assets/ALF_UW_Template_v6.xlsx`** before building — caught two template bugs (below).
- `bf3f61a` **engine pt2**: `Auto Expense` → `_LABELS_NON_LABOR` (closes the $6,061 NOI gap — verified = $6,061.32 on Homestead; NOI ties as-reported $1,411,324); 13 new by-care/ancillary keys exposed; known-divergence whitelist.
- `9014642` **substrate v0.2.15** (`migrate_to_v0215.py`): 2nd-Person Description_Map re-map (r127/400/401/402) **+ the E52/F52 EGI-formula companion fix**. The handoff said "EGI unchanged" but the Analyzer's EGI formula didn't sum the "2nd Person Revenue" label — verifying the formula chain caught that the re-map alone would drop $32,220 (r127 Second Person Fee) out of EGI. Migration amends E52/F52 so it's EGI-neutral.
- `3f8e5d0` **formula-preservation + dashboard EGI**: nulled `base_rent_normalized`/`loc_revenue` v6 targets (N61/N65 are template SUM formulas — `loc_revenue` was clobbering N65); dashboard EGI now includes 2nd Person (annual + monthly).
- `<this commit>` **version/docs**: UWT 0.6.4 → 0.7.0; CHANGELOG-UWT + journal + CLAUDE.md; v6 handoff marked Verified.

### Two template bugs found (flagged to operator, default stays v5)

1. **v6 binary is pre-Excel-resave** — 39 zip parts, missing `xl/metadata.xml` + `xl/webextensions/`. Section R/S spills degraded on populated outputs until the operator opens v6 in Excel + saves + re-drops (handoff §9). `BUNDLED_UW_TEMPLATE_VERSION` stays `"v5"`.
2. **`B56:M56` monthly headers still `=C122..=N122`** — raw row moved to 137 (+15); operator's repointing missed the chain (openpyxl quirk #4). Cosmetic; v6.1 fix.

### Verification

All 5 test suites green. EGI ties $7,001,957 (re-map neutral); NOI ties as-reported $1,411,324 (Auto Expense captured). v6 populate verified end-to-end: income rows + Auto Expense N114 + 2nd Person N66 ($32,220) populate; all total/subtotal formulas preserved. Cached-fixture divergences whitelisted (5 keys × $6,061 Auto Expense + 2 keys × $32,220 re-map) — rebuild fixtures against v0.2.15 to retire.

### Update — UWT v0.7.1 (`77a825e`, same session): v6 binary repaired

After the v0.7.0 absorption, the two v6 template bugs were fixed **programmatically** (no operator Excel round-trip needed) via `tools/uw_template/_fix_v6_headers_and_metadata.py`:
- **B56:M56** repointed `=C122..=N122` → `=C137..=N137` (raw header row moved +15).
- **`xl/metadata.xml` + 554 `cm` markers restored** via `_restore_dynamic_arrays`, sourced from `assets/ALF_UW_Template_v5.xlsx` (v5.1 content; Section R/S layout verified identical to v6 first). v6 now 40 parts; Section R/S spills work on the template AND on populated outputs. `assets/ALF_UW_Template_v6.xlsx` is now committed (was untracked). `UWT_VERSION` 0.7.0 → 0.7.1.
- **Not restored:** `xl/webextensions/` (Claude add-in; carries v5's fileId GUID — operator re-adds if used).

### ⏭ What's left for the next session (priority order)

**1. Flip the default template to v6** (the natural next step — binary is now correct, tests green):
- `app.py`: `BUNDLED_UW_TEMPLATE_VERSION = "v5"` → `"v6"`; the `populate_uw_template` default `template_version='v5'` → `'v6'` (and the CLI default in `uw_template_writer.py`).
- Update `_detect_uw_template_version` probe if needed (v6 distinguishing header — e.g. `T-12 Analysis!A77` == EGI, or `A114` == Auto Expense).
- Smoke-test empty + Homestead on v6 as the default; bump `UWT_VERSION` → 0.7.2 (or 0.8.0).
- **Held this session pending operator go-ahead** (user asked only to "fix the two things"). Confirm before flipping — every populated output becomes v6.

**2. Operator-side (outside repo):**
- Adopt the repaired `assets/ALF_UW_Template_v6.xlsx` back into the `Deals/.../ALF Templates/` folder copy (I fixed the repo's binding copy; the Deals/ copy is still pre-fix).
- Optionally open v6 in Excel once to confirm Section R/S spills + re-add the Claude-for-Excel add-in (webextensions).

**3. Rebuild test fixtures against substrate v0.2.15** to retire the known-divergence whitelists:
- `tests/test_uw_output_model.py`: `_AUTO_EXPENSE_DIVERGENCE` (5 keys × $6,061) + `_REMAP_2P_DIVERGENCE` (2 keys × $32,220). Rebuild the populated Homestead Analyzer fixture (`Sample Files/Analyzer with 2026-04-24 Homestead…`) against v0.2.15 so cached == engine, then delete both whitelists.
- `tests/test_dashboard_model.py`: v0.2.11 fixture; the residual $6,061 Auto Expense is within the 0.5% drift tolerance now, but rebuilding against v0.2.15 makes it exact.

**4. Sanity-check the 2nd-person re-map ripple** (lower priority): the re-map moved $32,220 out of base rent. I fixed the three EGI consumers (engine, dashboard, Analyzer E52/F52). Confirm no OTHER base-rent consumers need 2nd-person awareness — e.g. the 2P reconciliation row (`T12 Analytics!r168`, BL-0004) should now show actual 2P on its T12 side (was $0); ADR/RevPOR use `base_rent_total` (correctly excludes 2nd person now); GPR/loss-to-lease diagnostics shifted (expected).

**5. Registry `open_questions` cleanup** (housekeeping): #3 monthly grid (closed by v0.6.2) and #2 2nd-Person source (closed by v0.2.15 re-map) are now stale — drop them in the next registry edit.

**6. Backlog — `UW-BACKLOG.md` Pending:** only **BL-0019** (persistent audit log for password gate, Track 1) remains, user-deferred since 2026-05-19. Fresh Track 1 chat.

---

## 2026-05-28 — UWT v0.6.4 — Section I (Layer 1 — Raw T-12) populated

**Track:** Track 4. Same chat, after v0.6.3 — the 3rd of the operator's 3 requirements.

**Request:** "the summarized Raw data should be inserted in Section I of T-12 Analysis." Section I = raw-T12 paste grid (rows 122–172), previously an empty skeleton with pre-assigned bucket labels in col P.

**Decisions (AskUserQuestion):** rebuild one row per Analyzer label; Account Name = matched GL account names.

**Engine:** `compute_t12_raw_lines(t12_result)` → list of `{label, section, descriptions, monthly[12], total}` grouped by Description_Map label from `T12ParseResult.gl_rows`. Computed in Python (NOT read from the Analyzer T12 Raw Data sheet — its monthly cells are formulas, blank on a fresh Analyzer; cache caveat). Ordered P&L; unmapped lines excluded.

**Writer:** `_write_section_i_raw` + `populate_uw_template(..., raw_t12_lines=)`. Clears skeleton (123–172, A–P), writes one row per label (B=GL names joined, C–N=months, O=total, P=bucket); authors Section J raw-totals reconciliation as SUM formulas. New `summary['section_i_raw_cells']`.

**Bug caught mid-build:** reused Layer-3 `_T12_MONTH_COLS` (B–M) but Section I months are C–N (cols 3–14) → first month overwrote Account Name. Fixed to `range(3,15)`.

**Result:** 44 raw lines (8 rev/36 exp), 663 cells; months tie to total per row; Section J EBITDAR = $1,411,324 (penny-exact as-reported NOI). New test `test_section_i_raw_populated`. `UWT_VERSION` 0.6.3 → 0.6.4. **All 3 operator requirements shipped.**

**Commit:** `feat: UWT v0.6.4 — populate Section I (Layer 1 Raw T-12) from summarized raw lines`.

---

## 2026-05-28 — UWT v0.6.3 — T-12 Analysis totals as live formulas + waterfall sign fix

**Track:** Track 4. Same chat, after v0.6.2. Operator reported math inconsistencies + two requirements (totals as formulas; raw data → Section I) with the attached `Homestead_Village_UW_Template_2026-04-24_normalized.xlsx`.

**Diagnosis (grounded in the attached file + blank template):**
1. Totals were pasted values overwriting the template's live formulas (N63/N69/N85/N111/N114/N115/N116) → didn't tie/recompute; N114 Total Op Ex = 0.
2. Income waterfall didn't subtract losses: Vacancy/Bad Debt pasted positive while the template's additive `N63 = N58+N59+N60+N61+N62` treats them as reductions.

**Decisions (AskUserQuestion):** bad debt reduces EGI (honor template N63); monthly totals mirror formulas across B–M.

**Fix (`uw_template_writer.py`):**
- Skip the 9 Layer-3 total concepts on T-12 Analysis (formulas preserved).
- `_T12_CONTRA_KEYS` (loss_to_lease, physical_vacancy_loss, bad_debt_writeoffs_revenue) negated on write (annual + monthly).
- `_finalize_t12_layer3`: preserve col-N formulas; author N117 (`=N116-N113`) + N118 (`=N117`); mirror each total's col-N formula across B–M; Net Rent monthly = base−conc−baddebt (GPR waterfall has no monthly).

**Result (evaluated):** Net Rent $6,750,961, EGI $6,964,627, Total Non-Labor $2,136,601 (bad debt out of opex); **EBITDARM $1,767,483 / EBITDAR $1,417,385 / EBITDA $1,417,385 unchanged** (bad debt nets out at EBITDARM). Monthly ties to annual to the penny. Tests updated with an N-chain evaluator. `UWT_VERSION` 0.6.2 → 0.6.3.

**Still open:** Section I (Layer 1 — Raw T-12, rows 121+) — next item this session.

**Commit:** `fix: UWT v0.6.3 — T-12 Analysis totals as formulas + income-waterfall sign fix`.

---

## 2026-05-28 — UWT v0.6.2 — T-12 Analysis monthly grid populated (cols B–M)

**Track:** Track 4. Same chat, after v0.6.1.

**Trigger:** Operator screenshot — populated UW Template T-12 Analysis Layer 3 shows the T-12 Total column fully populated (EGI $7,001,957, Total Labor $3,060,543, etc.) but the 12 monthly columns (Apr 2025…Mar 2026) all $0. "I don't see the data in the t12 analysis monthly."

**Diagnosis:** by-design, not a regression. The Phase-2 writer had a locked default "monthly grid annual-only" — write col N (T-12 Total), leave B–M blank. The engine already had monthly data internally (`_aggregate_t12` buckets GL rows month-by-month), so populating the grid was straightforward.

**Layout (confirmed against template):** Layer-3 months = cols B–M (headers `=C122…=N122`), T-12 Total = col N, then O/P/Q. The B–M cells are literal-`0` paste targets (not formulas — even subtotal rows; EGI N69 is a formula but B69–M69 are plain 0s), so each month is pasted explicitly.

**Engine:** new `compute_uw_output_monthly(rr_result, t12_result) → {concept_key: [12 floats]}` — reuses `_aggregate_t12`'s monthly bucketing; covers labor, non-labor opex, base rent/LOC/other-rev, subtotals, EBITDA chain. GPR/vacancy/loss-to-lease omitted (RR projections, no monthly source → rows stay blank). Returns {} with no T12.

**Writer:** `populate_uw_template(..., computed_monthly=None)` + `_write_monthly_grid`; for T-12 Analysis col-N concepts, pastes 12 values to cols B–M. New `summary['monthly_cells_written']`.

**App:** passes `compute_uw_output_monthly(...)`; success caption notes monthly count.

**Verified:** 636 cells (53 concepts × 12); every populated row reconciles to the penny (Base Rent ΣB:M=$6,983,357=N, EGI=$7,001,957=N, Total Labor=$3,060,543=N); GPR blank monthly as designed. New test `test_monthly_grid_reconciles`; all 4 model tests + writer suite green. `UWT_VERSION` 0.6.1 → 0.6.2.

**Not in scope:** cols O (T-3 Annlzd), P (Per Bed/Mo), Q (% of EGI) stay blank — semantics unconfirmed, never populated before (no regression). Follow-up candidate.

**Commit:** `feat: UWT v0.6.2 — populate T-12 Analysis monthly grid (cols B–M)`.

---

## 2026-05-28 — UWT v0.6.1 — dynamic-array repair (Section R/S spills survive the writer)

**Track:** Track 4. Same chat as v0.6.0, immediately after.

**Trigger:** Operator bug report on a populated `Homestead_Village_UW_Template_2026-04-24_normalized.xlsx`: Section R (Unit Type Pricing By Care Level, rows 170–181) shows only ONE row instead of the full Care×UnitType matrix; row 180/181 totals ~10× understated. No spill/value errors — silently wrong.

**Root cause:** openpyxl quirk #6 on the OUTPUT. `wb.save()` drops `xl/metadata.xml` (XLDAPR dynamic-array props) + the per-cell `cm="1"` markers. The template's `Z173 = SORT(UNIQUE(FILTER(...)))` driver and `A173:Q173` spills demote to single-cell legacy CSE arrays → return only the top-left value → Section R collapses. An Excel re-save does NOT fix it (Excel commits to CSE on open). The formula text was always intact; only the dynamic-array marking was lost.

**Fix:** `_restore_dynamic_arrays(output_bytes, template_bytes)` in `uw_template_writer.py` — pure `zipfile`+`re`, no new dependency, called after `wb.save()`. (1) re-injects `xl/metadata.xml` from the template; (2) adds its content-type Override + workbook `sheetMetadata` relationship; (3) re-applies `cm` markers to the exact anchor cells that had them, matched by sheet name (robust to openpyxl rel-id renumbering + `/xl/…` absolute targets), only on cells still holding a formula. No-op when template lacks metadata.xml (v4). try/except → degrades to a warning, never breaks populate. New `summary['dynamic_arrays_restored']`.

**Mid-fix bug caught:** openpyxl writes rel targets as `/xl/worksheets/sheetN.xml` (absolute) vs the template's relative `worksheets/sheetN.xml`. First path-normalization gave `xl/xl/...` (double prefix) → 0 cm injected. Fixed to handle both forms → 557 restored.

**Verified:** 557 cm markers restored (554 RR Analysis + 3 on the 2nd dynamic sheet); Z173/A173/C173/Q173 all carry `cm="1"`; metadata.xml present; zip valid; openpyxl re-loads; writer data intact (EGI $7,001,956.79 @ N69, D211='1 Bedroom', Z173 still ArrayFormula). New `tests/test_uw_output_model.py::test_dynamic_array_metadata_restored`; both UWT suites green. `UWT_VERSION` 0.6.0 → 0.6.1.

**Secondary issue flagged (not fixed):** 128/400 `X211:X610` rows resolve to "" (occupied-filter gate). Most legit vacant; sanity-check that no *occupied* unit is missing Care Level (col C) / Unit Type (col D) — those silently drop from Section R. Data-completeness question, not a writer bug.

**Commit:** `fix: UWT v0.6.1 — restore dynamic-array metadata on output (Section R/S spills)`.

---

## 2026-05-28 — UWT v0.6.0 — in-Python UW Output evaluator (cache caveat CLOSED)

**Track:** Track 4 (UW Template integration). Continuation of the same chat that shipped RR v1.19.0; user direction: *"go with 1"* (build the evaluator) + *"Extend dashboard_model.py pure-Python pattern"*.

**Status:** **SHIPPED.** The single biggest UX friction in the UW Template populate flow is gone.

### The problem (cache caveat)

The writer reads the Analyzer with `data_only=True` — cached formula values. openpyxl doesn't evaluate formulas, so an Analyzer the app builds in-memory has formula *text* but no cached values. Every `uw_output`-system concept (reads of `UW Output!{col}{row}`) resolved to `None` → `no_source`, leaving the populated UW Template's `T-12 Analysis` tab blank unless the operator round-tripped the Analyzer through Excel (download → open → save → re-upload as override). 63 of the t12-path concepts came through blank this way.

### What shipped

- **New module `uw_output_model.py`** — `compute_uw_output_values(rr_result, t12_result, *, scenario) → {concept_key: value}`. Computes 62 `uw_output` + 2 dependent `derived` concepts directly from parsed RR + T12, reusing Track 5 `dashboard_model`'s `load_description_map`, `_aggregate_t12`, `_LABELS_*` (single source of truth for the label vocabulary).
- **Writer** — `populate_uw_template(..., computed_values=None)`. Fallback applied **per concept only when the Analyzer cell is blank** → analyst-saved override Analyzers still win. New `ConceptResult.computed_fallback` + `summary['computed_in_python']`. Backward-compatible (existing smoke test passes, `computed_in_python: 0` on cached fixture).
- **App** — populate flow calls the evaluator + injects `property_name`/`rr_period_date` (both blank on a fresh build); loud cache-caveat `st.warning` replaced by `st.success` + soft `st.info` for the no-T12 case. `UWT_VERSION` 0.5.3 → 0.6.0.
- **Test `tests/test_uw_output_model.py`** (new) — engine reproduces Homestead's cached UW Output to the penny on 42 concepts; writer-fallback e2e takes a fresh Analyzer's t12 `no_source` 63 → 2, N69/N116/N118/N115 all correct.

### Why it's correct (the key insight)

`UW Output` is a thin reference layer over `T12 Analytics`. The default **normalized** scenario == **T12 actual** for every line because (a) opex/other-rev are `F{r}==E{r}` (col F literally copies col E), and (b) base rent/LOC's stabilized formula `B20=B6·B10·B19·12` collapses to the T12 actual when `B10` (target occupancy) `=B8` (its literal default). Verified empirically on Homestead: `E16==E20`, `E23==E27`, `E52==F52`, `E108==F108`. Analyst normalization is an Excel-side override applied *after* populate; once saved, the cached values exist and the writer prefers them.

### Verification numbers

- Engine vs cached fixture: EGI $7,001,956.79, EBITDARM $1,767,482.75, EBITDA $1,417,384.90, GPR $9,524,893.30 — all to the penny, 0 mismatches across 42 concepts.
- Fresh-Analyzer writer fallback: 37 written → 98 written; t12 `no_source` 63 → 2; 61 computed in-Python.

### Residual / not addressed

- 7 `rent_roll`-path `no_source` (pharmacy / meal / scooter / care-level / preleased) are legitimately empty source columns for Homestead, not cache artifacts.
- No new dependency (pure Python). Registry unchanged at v0.4.2.

### Commits

`feat: UWT v0.6.0 — in-Python UW Output evaluator (kills cache caveat)` — `uw_output_model.py`, `uw_template_writer.py`, `app.py`, `tests/test_uw_output_model.py`, SPEC-UWT / CHANGELOG-UWT / CLAUDE.md / journal.

---

## 2026-05-27 (evening) — RR v1.19.0 — River Oaks / SSMG-Yardi format support + Deposit capture

**Track:** Track 1 (RR Normalizer) — cross-track pivot from earlier Track 4 (UWT v0.5.3) work in the same chat. Resumed + shipped 2026-05-28 after a context break.

**Trigger:** User reported `River Oaks Place Lenoir City - April 2026 Rent Roll.xls` (a Senior Solutions Management Group property exported from Yardi) would not parse.

**Status:** **SHIPPED.** Parser + writer working on River Oaks; existing fixtures unaffected; version bumped, changelog written, UWT side re-verified, committed + pushed.

### What shipped (verified via end-to-end pipeline test)

- `xlrd>=2.0.1` added to `requirements.txt`. pandas `ExcelFile` content-sniffs the OLE2 magic bytes and routes legacy `.xls` to xlrd automatically — no `engine=` plumbing. xlrd 2.0+ is `.xls`-only (dropped `.xlsx`), exactly the slot needed.
- `.xls` upload accepted in all three app.py file_uploaders (RR + T12 + AR), with label + help-text updates.
- River Oaks (89 source rows, 26 cols, 3 sheets) parses to **86 beds**: 56 IL · 16 AL · 11 MC · 3 blank (Comm units, intentional). Market Rate $353k, Actual Rate $185k, **Med Mgmt $ $9,400 (from MEDADMIN)**, **Other LOC $ $1,800 (from COMMAPT)**, Balance −$44,697, **Deposit $1,300 (2 rows)**.
- Writer produces 244,990-byte populated Analyzer; `Rent Roll Input!AI4 = "Deposit"`; deposit values land at AI per substrate v0.2.14 slot (`$#,##0.00`).
- **Regression clean:** Homestead re-parses to the same 176 beds (IL 62 / AL 62 / MC 52), Condensed_RR now 32 cols with Deposit blank; Salem / Briar Glen unaffected. New rules don't over-match (`normalize_care_type("RHA")` → IL; `normalize_bed_status("Admin")` → Vacant; zero unmapped on existing fixtures).
- **UWT side re-verified:** `tests/test_uw_template_writer.py` passes — Deposit has no template target so the writer ignores it.

### Files changed (6 files)

| File | What changed |
|---|---|
| `requirements.txt` | `+ xlrd>=2.0.1` |
| `app.py` | Three file_uploader `type=` lists extended with `xls` (RR / T12 / AR) + help-text. `RR_VERSION` `1.18.1` → `1.19.0`, `RR_LAST_UPDATED` → `2026-05-27`. |
| `normalizer.py` | FIELD_PATTERNS extended: `bed_status` (Unit/Lease Status, Lease Status), `resident_full` (bare Name), `market_rate` (Market + Addl.), `actual_rate` (Lease Rent), `move_in`/`move_out` (hyphenated), new `deposit` field. New care_type fallback 4.5 (re-runs normalize_care_type on raw apt_type — catches Yardi Floorplan IL/AL/MC/RHA). `looks_care` extended with `medadmin`/`medmanage`/`commapt`. `CONDENSED_COLUMNS` appends `Deposit` (col 32); bed-record builder + condensed-DataFrame emit it. |
| `mappings.py` | `DEFAULT_BED_STATUS`: `(r"\badmin", "Vacant")` before `\bdown\b`. `DEFAULT_CARE_TYPE`: `(r"\brha\b", "IL")`. `DEFAULT_CARE_BUCKETS`: `medadmin`/`medmanage` → Med Mgmt $. |
| `analyzer_rr_writer.py` | `has_v119_cols` gate; per-row Deposit write to AI via `COL_AI_INDEX = 35`, `$#,##0.00`. AH=34 (Total Ancillary) + AJ=36 (Preleased) protections preserved. |
| `CHANGELOG-RR.md` | New `[1.19.0]` entry at top. |

### Open questions (not blocking — recorded for a future deal)

- **Apt Type for Yardi IL/AL/MC floorplans**: River Oaks's Floorplan column doubles as care type AND apt type. Fallback 4.5 extracts care type correctly but leaves apt_type raw "IL"/"AL"/"MC"; substrate DV expects (Studio / 1 Bedroom / …). Values DV-flag but still write. Left as raw — explicit `("^il$","Studio")` rules would guess and may be wrong. Operator adjusts per-deal.
- **3 rows lost (89 → 86)**: trailing Totals/Note/blank. Acceptable.
- **Comm units (3 rows, no care type)**: community/amenity space; emit with blank care type + $0 rate. Acceptable.
- **Deposit has no UW Template v5 column**: lands in Analyzer AI substrate slot but `rr_deposit` registry concept stays `substrate_ready_parser_pending` — no `Rent Roll Analysis` target. A v5.1 template handoff would surface it downstream. Deferred.
- **A173/B173 IFERROR carry-forward** from earlier Track 4 (UWT v0.5.3) work — still in the next-Cowork-pass bundle.

### Earlier this session (already committed before the RR work)

Track 4: `f7a422d` UWT v0.5.0 attempted-then-rolled-back, `d670bab` prevention docs (preflight + openpyxl quirk #6), `945060b` UWT v0.5.3 (v5.1 K/L/V template-formula absorption). All on `origin/main`.

### Next up

Build the **in-Python formula evaluator** to kill the cache caveat (the biggest UX friction in the UW Template populate flow). Chosen engine approach: extend the `dashboard_model.py` pure-Python pattern (Track 5) so the writer reads computed UW Output values directly from the in-memory Analyzer without an Excel round-trip. Now unblocked — the tree is clean after RR v1.19.0.

---

> **Note (2026-05-14):** journal.md was not updated as substrate moved through v0.1.11 → v0.1.12 → v0.1.13 → v0.1.14 → v0.1.15 → v0.2.0 → v0.2.1 → v0.2.2 (8 releases since the v0.1.10 entry below). Those releases lived in `CHANGELOG-T12.md` and `UW-BACKLOG.md` only. The 2026-05-14 v0.2.3 entry below (BL-0015) is the first journal entry in 3 days. Back-filling the missing ones is on the BL-0014 docket.

---

## 2026-05-26 (afternoon) — Track 4 handoff infrastructure + UWT v0.5.0 attempted & rolled back

User-directed Track 4 session. Two threads:

1. **Augment the ClaudeCode → Cowork handoff system** for template changes. The infrastructure itself (`HANDOFF_TRACKER.md`, `HANDOFF_TEMPLATE.md`, `handoffs/` directory with the original 2026-05-25 brief, CLAUDE.md Track 4 "Handoff protocol" paragraph) was already shipped in commit `031e24f` earlier on 2026-05-26 — this session's chat was framed as "set up a tracker" but the system already existed (my early `ls -la tools/uw_template/` not seeing the files was a OneDrive sync mirage). The actual work this session: new 2026-05-26 handoff brief, Superseded banner on 2026-05-25 brief, `Superseded` status added to tracker legend, tracker index row updates. User: *"create a tracker and md documentation for handoff everytime the ALF UW template is changed through claudecode. I will then use this to update through co-work locally."*
2. **Attempted to ship the v5 → v5.1 residual cells** (`substrate_version` + RR Analysis tab-header Period Date) via direct openpyxl edits after a user-approved fast-path override of the handoff protocol. Failed and rolled back same-session.

### Sequence of mistakes worth recording

1. **Wrote the seed handoff against stale registry state.** First draft of `2026-05-25-uwt-v4-to-v5-template-gaps.md` asked for 10 `gap_target` concepts to be closed in v5 — but UWT v0.4.0 had absorbed v5 hours earlier and 7 of those gap_targets were already closed. The registry on disk was at v0.3.0, but my earlier python read returned v0.2.1 (likely OneDrive sync timing or fs cache). User caught it with *"review again. i've already uploaded template v5."* Marked the brief **Superseded**, kept for audit trail, wrote a fresh `2026-05-26-uwt-v5-to-v51-residual-gaps.md` against actual current state (2 residual gap_targets + writer-scope decisions).

2. **Took the fast-path openpyxl edit despite a just-written protocol saying don't.** User asked *"let's complete the handoff."* Offered three completion paths via `AskUserQuestion`; user chose direct openpyxl edits to `assets/ALF_UW_Template_v5.xlsx`. Logic at the time: two cells above the data band, no charts/formulas/merged ranges nearby, fidelity risk looked near-zero. Wrote `tools/uw_template/_patch_v5_to_v51_metadata_cells.py` (idempotent, with pre/post fidelity diff). Cell-level diff appeared clean — 16 sheets / 240 merged ranges / 5 defined names / 3,417 RRA cells / Section R/S ArrayFormulas preserved verbatim. Bumped registry → v0.3.1, regenerated artifacts, smoke-tested writer (passed: `Cover!H1 ← 'v0.2.4'`, `Rent Roll Analysis!B5 ← 2026-04-24`). Marked the handoff Verified.

3. **The cell-level fidelity diff was necessary but not sufficient.** After cleanup, noticed `assets/ALF_UW_Template_v5.xlsx` shrunk **262,589 → 211,969 bytes (~20%)**. A zip-part inventory diff caught what openpyxl silently dropped on save:
    - **`xl/metadata.xml`** (810 bytes) — `XLDAPR` / `fDynamic="1"` block. This is the dynamic-array properties metadata that tells Excel the v0.4.3 Section R/S formulas (`Z173 SORT(UNIQUE(FILTER(...)))` / `C173 COUNTIFS(...,ANCHORARRAY(Z173))`) are dynamic spills. Without it, Excel demotes the spill to a single cell or renders `#SPILL!` even though every `_xlfn._xlws.SORT` prefix is preserved verbatim in the formula text.
    - **`xl/webextensions/*`** — Claude-for-Excel taskpane add-in registration (`wa200009404` from the Office Add-in store).
    - `xl/sharedStrings.xml` (74 KB) — inlined instead, functionally equivalent.
    - `xl/calcChain.xml` (167 KB) — Excel rebuilds on open.
    - Minor comment/VML drawing path renames.

   **openpyxl has no API to preserve `metadata.xml` or `webextensions/`.** Both are zip parts the library doesn't model in its Worksheet / Workbook object graph. A `wb.load() → wb.save()` round-trip always drops them.

### Rollback

- `assets/ALF_UW_Template_v5.xlsx` restored from git `deacc41` (byte-identical to v0.4.3 ship state).
- Registry reverted v0.3.1 → v0.3.0 via `tools/uw_template/_revert_registry_to_v030.py` (`substrate_version` mapped→gap_target; `rr_period_date` mapped→proposed; `t12_period_date` derived_in_template→gap_target).
- 3 `open_questions` re-opened (#4 A5/B5 format, #7 Cover stamp, #8 RR Analysis tab-header Period Date).
- `UWT_VERSION` restored to `0.4.3`.
- `MAPPING_TRACKER.md` / `mapping_tracker.csv` / `mapping_mindmap.html` regenerated against the reverted registry.
- `CHANGELOG-UWT.md` gained a `v0.5.0 — Attempted then rolled back` entry with full forensics.
- `CLAUDE.md` head paragraph rewritten to narrate the attempt → rollback; openpyxl-quirks section gained a new **quirk #6** documenting `metadata.xml` / `webextensions/` silent drop, with a `zipfile`-based detection snippet.
- `tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md` reverted from Verified back to **Pending operator** with a banner explaining the failed openpyxl attempt.
- Both patch scripts (`_patch_v5_to_v51_metadata_cells.py` + `_revert_registry_to_v030.py`) retained as audit trail. **Do not re-run the patch script** without first solving the XLDAPR-loss problem.

### What stands (handoff infrastructure)

Already in place under `tools/uw_template/` as of commit `031e24f` (earlier 2026-05-26 morning), augmented this session:

- `HANDOFF_TRACKER.md` — *pre-existing*. Augmented this session: added `Superseded` to the status legend; added the new 2026-05-26 row at top; updated the older 2026-05-25 row's Status to Superseded.
- `HANDOFF_TEMPLATE.md` — *pre-existing*, untouched (byte-identical to HEAD).
- `handoffs/2026-05-25-uwt-v4-to-v5-template-gaps.md` — *pre-existing*. Augmented this session: added a Superseded banner at the top explaining work shipped via v0.4.0 hours before the handoff was published.
- `handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md` — **new this session**. Pending operator (with v0.5.0-rollback banner).

CLAUDE.md Track 4 section's "Handoff protocol" paragraph and table rows for the handoff files are *pre-existing in `031e24f`*. My session work on CLAUDE.md was limited to: (a) rewriting the head paragraph (UWT v0.4.3 ships → UWT v0.5.0 attempted/rolled-back narrative), and (b) adding openpyxl quirk #6.

User-level feedback memory `uw-template-handoff-protocol` written this session and indexed in MEMORY.md (this is local to `~/.claude/projects/...`, not in the repo).

### Net state delta vs start-of-session

| | Before | After |
|---|---|---|
| `assets/ALF_UW_Template_v5.xlsx` | v0.4.3 ship state | **unchanged** (restored from git) |
| `tools/uw_template/registry.json` | v0.3.0 | **unchanged** |
| `app.py` `UWT_VERSION` | 0.4.3 | **unchanged** |
| `gap_target` concepts | 2 | 2 (deferred to operator-authored v5.1 per the active handoff brief) |
| `open_questions` | 8 | 8 |
| Handoff infrastructure | shipped in `031e24f` (earlier 2026-05-26) | augmented — new 2026-05-26 brief, Superseded banner on 2026-05-25 brief, Superseded status in tracker legend, tracker index row updates; two patch scripts retained as audit trail |
| `CLAUDE.md` openpyxl quirks | 5 | **6** (added `metadata.xml` / `webextensions/` silent-drop quirk) |

### Lessons

- **Pre-cache registry state before drafting any registry-modifying handoff.** Re-grep `registry_version` from disk; don't trust prior python reads in the same session — OneDrive sync timing can serve stale views.
- **Cell-level openpyxl fidelity diffs are necessary but not sufficient.** Diff the xlsx zip part inventory pre/post before declaring a round-trip safe. `xl/metadata.xml` and `xl/webextensions/` are invisible to Worksheet-object inspection but materially affect Excel behavior.
- **The handoff protocol exists for a reason.** v0.5.0 broke the protocol the same session it was established and proved the protocol's value by failing. Future Track 4 chats should default to the protocol path unless a user-approved exception applies AND a zip-part inventory diff is added to the fidelity check.

### Carry-forwards (next chat)

- **Operator-side:** author the two cells in Excel via Cowork per `tools/uw_template/handoffs/2026-05-26-uwt-v5-to-v51-residual-gaps.md`. Substrate version stamp on Cover (operator's pick of cell — `A1:F1` is the merged title band, so `G1`/`H1` or further right). `Rent Roll Analysis!B5` styled `mm/dd/yyyy`. Re-drop at `assets/ALF_UW_Template_v5.xlsx` (overwriting in place; v5.1 isn't a new file).
- **Next Track 4 chat (after re-drop):** bump registry to v0.3.1, mark the two concepts `mapped` (+ `t12_period_date` → `derived_in_template`), close `open_questions` #4/#7/#8, regenerate artifacts, smoke-test writer, mark handoff **Verified**, bump `UWT_VERSION` 0.4.3 → 0.5.0, replace the rolled-back `v0.5.0` CHANGELOG entry with a proper ship entry.

### Commits

This session did not commit. All changes are in the working tree pending user review.

---

## 2026-05-25 — RR v1.18.0 + Substrate v0.2.13 — Move-out & preleased exposure (BL-0025)

Cross-track session (Track 1 + Track 3), user-authorized at chat start. User: "in the homestead village RR, there are move outs, this isn't captured in the normalizer and not reflected in the analyzer. I need this captured for exposure."

### Diagnosis

Two related gaps surfaced from the Homestead Village v2 RR fixture:

1. **3 "Vacant w/ Prelease" units (A4 / F1 / F2) were silently collapsing to plain `Vacant`** because `\bvacant\b` matched the source label before any prelease rule fired. Rent Roll Recon Section A's Vacant count was overstated by 3, and there was no way to surface that those units were already lined up to fill.
2. **`Move-out Date` had been captured into `Rent Roll Input!W` since substrate v0.1.10 / RR v1.16.0 but no Analyzer formula read it.** No underwriting "exposure" view existed (gross / net of preleased, forward NTV departure timeline).

User chose "Both — full end-to-end exposure pipeline" + "Both point-in-time AND forward NTV buckets" in the scoping question. That nailed the design: parser additions + new Section N on Rent Roll Recon.

### What shipped

- **`mappings.py`** — `DEFAULT_BED_STATUS` gets `(r"\bprelease", "Preleased")` ordered immediately before `\bvacant\b`. Order matters: "Vacant w/ Prelease" must hit Preleased first.
- **`normalizer.py`** — `prelease_date` added to `FIELD_PATTERNS` (matches Homestead's bare `^preleased$` column header). `CONDENSED_COLUMNS` extended to 31 cols. Condensed-DataFrame construction at ~line 1206 also extended (almost missed this on first pass — `Preleased Date` not appearing in df until the explicit dict was updated).
- **`analyzer_rr_writer.py`** — `COL_AI_INDEX = 35` + `SOURCE_COLUMNS_AI = ["Preleased Date"]` + idempotent clear of AI7:AI606. AH=34 reserved for v0.1.13 Total Ancillary $ formula — explicitly NOT cleared.
- **`analyzer_rr_translator.py`** — docstring update only. `Preleased` passes through unchanged.
- **`tools/migration/migrate_to_v0213.py` (new)** — 3 surface ops (DV extension, AI4 header, Section N append) + 17 version stamps. 8-check verify. Idempotent (gate: `Cover!B8 == "v0.2.13"` AND `Rent Roll Recon!A178` starts with "N"). Section N is a pure append at row 178 (max_row was 176 + a blank separator at 177) — no `insert_rows`, avoids the BL-0001 qualified-range-endpoint trap.
- **Section N layout** — N1 (point-in-time, rows 180-189): Occupied / Notice / Vacant / Preleased / Total / Gross (Notice + Vacant) / **Net (Gross − Preleased)** / Net %. N2 (forward NTV, rows 191-198): ≤30d / 31-60d / 61-90d / 91+d / No date or past (residual) / Total Notice sanity. Time windows compute against `Rent Roll Recon!B2` (period dropdown).
- **Bundled `ALF_Financial_Analyzer_Only.xlsx`** — migrated in place v0.2.12 → v0.2.13. Sheet count unchanged at 16; all 16 AZ4 anchors stamped.
- **`app.py`** — `RR_VERSION` 1.17.5 → 1.18.0; `ANALYZER_SUBSTRATE_VERSION` 0.2.11 → 0.2.13 (the constant was lagging — v0.2.12 had shipped without updating it; v0.2.13 corrects both). `RR_LAST_UPDATED` + `ANALYZER_LAST_UPDATED` → 2026-05-25.
- **Docs** — CHANGELOG-RR.md (v1.18.0 entry), CHANGELOG-T12.md (v0.2.13 entry), SPEC-RR.md (current version line + Track 1 version), SPEC-T12.md (substrate pointer), CLAUDE.md (Last updated + Closed-2026-05-25 entry), UW-BACKLOG.md (BL-0025 in Shipped).

### Verification

- **Parser smoke** on Homestead: 176 rows, statuses **128 Occupied / 40 Vacant / 5 Notice / 3 Preleased** (was 128/43/5/0 before — 3 preleased split from Vacant). `Preleased Date` column present in `condensed`; NaN for all 3 Homestead Preleased rows (source's `Preleased` column is empty for those units, as expected).
- **Migration verify** — 8/8 OK (Cover B8 / DV / AI4 / Section N spot-checks / Preleased formula / Net formula / sheet count / 16 AZ4 anchors).
- **End-to-end** — normalize → translate → populate → re-load: 128/40/5/3 status counts hold. Col W populated for 3 NTVs (the 3 dated ones); col AI empty for the 3 Preleased (source has no date — wiring is in place for operators that fill it).
- **Section N evaluation** — openpyxl can't compute formulas, so I wrote a Python-equivalent reproduction of the COUNTIFS logic and verified expected values: **N1 Net exposure 7/18/17 IL/AL/MC = 42 (23.9%)**; **N2 ≤30d 0/3/0 = 3** (Julius Mims, Peggy Salger, Thomas Winterbury — all AL); **No date / past 0/2/0 = 2** (Hedenburg, Stowe). N2 Total Notice = 5 = N1 On notice (sanity).
- **Idempotency** — re-running migration on v0.2.13 output → "Workbook is already at v0.2.13. No-op (will re-save)."

### What drifted / lessons

- **CONDENSED_COLUMNS list and the condensed-DataFrame dict are two places** that need to stay in sync when adding a column. First parser test showed the field absent from `condensed.columns` because only the per-row record dict at line ~1075 was updated; the explicit `condensed = pd.DataFrame({...})` reconstruction at ~line 1206 also needs the new field. Caught quickly. Worth noting for future column adds.
- **`ANALYZER_SUBSTRATE_VERSION` in `app.py` was at `"0.2.11"`** when this session started — v0.2.12 had shipped without bumping the runtime constant. Caught during the version-bump pass; corrected to `"0.2.13"`. Future migration sessions should add a step to verify this constant matches the actual bundled file.

### Files changed

- `mappings.py`
- `normalizer.py`
- `analyzer_rr_translator.py`
- `analyzer_rr_writer.py`
- `app.py`
- `tools/migration/migrate_to_v0213.py` (new)
- `ALF_Financial_Analyzer_Only.xlsx`
- `CLAUDE.md`, `journal.md` (this entry), `SPEC-RR.md`, `SPEC-T12.md`, `CHANGELOG-RR.md`, `CHANGELOG-T12.md`, `UW-BACKLOG.md`

### Carry-forwards

- Live operator RR with populated `Preleased Date` column would let the AI column show non-empty values (Homestead's empty `Preleased` is the only test fixture today).
- If exposure analytics ever need to consider the `Hold`/`Model`/`Down` statuses, Section N's `Total beds` formula uses `A<>""` (any populated unit) — already inclusive. No change needed.

### Commit(s)

Pending — will be created at user request.

---

## 2026-05-25 — Substrate v0.2.12 — Dashboard blended-vs-segment formula fixes (BL-0024)

Track 3 follow-up to yesterday's Track 5 build. Yesterday's `dashboard_model.py` regression test discovered that three xlsx Dashboard headline tiles (B6 OCCUPANCY, F20 ADR, K6 REVPOR) reference segment-specific T12 Analytics cells (`F134` = AL-only, `F140` = MC-only, `F143` = MC-only) while their Dashboard labels say "Normalized community occupancy" / "Blended ADR" / "Normalized RevPOR." A worktree task was spawned to fix the xlsx side; that task's deliverable arrived as patch `0001fixDashboardblendedvssegmentformulamisrefssu.patch` at the repo root and was applied this morning.

A surface-wide audit of Dashboard during patch authoring widened the scope from the 3 headline tiles to **12 cells** sharing the same bug pattern. The 9 additional derivative cells: B8 (status text), C21 (occupancy row), D35 (occupancy card), E55 (gap-to-market delta), G55 (risk flag emoji), H55 (risk flag text), P5 (upper-right blended anchor), K8 (REVPOR status text), F21 (RevPOR detail row).

### What shipped (commit `1c0fecb`)

- `tools/migration/migrate_to_v0212.py` — 12 cell rewrites + 17 version stamps. 5-check + 12-per-cell verify. Idempotent — gate checks `Cover!B8 == "v0.2.12"` AND `Dashboard!B6` does NOT contain substring `"F134"`; each per-cell patch is also self-idempotent.
- Formulas: occupancy cells → `'T12 Analytics'!E11/'T12 Analytics'!E6`; F20 → `'T12 Analytics'!E20/('T12 Analytics'!E11*12)`; REVPOR cells → `('T12 Analytics'!E20+'T12 Analytics'!E27)/('T12 Analytics'!E11*12)`. All wrapped in `IFERROR(...,"—")`. Threshold-comparison shapes (B8/G55/H55) preserve existing ✓/⚠/✗ branches + "— Source not populated" fallback exactly.
- Bundled `ALF_Financial_Analyzer_Only.xlsx` updated in place v0.2.11 → v0.2.12.
- Docs: CHANGELOG-T12.md, CLAUDE.md "Last updated" line + Closed-2026-05-25 section, SPEC-T12.md "Current version" + template-iteration list, UW-BACKLOG.md (BL-0024 moved to Shipped).

### Why inline (not "add rows to T12 Analytics Section 5")

The alternative was to add Blended ADR + Blended RevPOR rows to T12 Analytics Section 5 KPI Dashboard and point Dashboard at them. Inline keeps blast radius to Dashboard only — zero T12 Analytics surface change, no risk of disturbing downstream consumers of T12 Analytics (UW Output, Workbook Health, Pre-Export Gate).

### Cross-pipeline impact

Track 5's `dashboard_model.py` already computes correct blended values. Before v0.2.12, the xlsx Dashboard was the diverging side. After v0.2.12, both surfaces agree:
- OCCUPANCY: xlsx now 72.7% (was 64.5% AL-only) — matches Python
- ADR: xlsx now $4,546 (was $6,802 MC-only) — matches Python
- REVPOR: xlsx now $4,562 (was $6,802 MC-only) — matches Python

### Conflict resolution during `git am`

Patch was authored against a CLAUDE.md state that pre-dated yesterday's T5 v0.1.0 entry. CLAUDE.md's "Last updated" line conflicted. Resolved by leading with v0.2.12 (newest, today) and folding Track 5 into the "Earlier on 2026-05-24" retrospective alongside the text-as-formula hotfix. The patch file is otherwise applied byte-for-byte.

### Verification

- `Cover!B8 == "v0.2.12"` ✓
- 12 / 12 Dashboard cells rewritten; 0 buggy F134/F140/F143 refs remaining
- AR variance tile at K10:L13 unaffected (K11 formula + K13 plain-text footnote both intact from the 2026-05-24 hotfix)
- 6 charts preserved, 75 merged ranges preserved
- Hidden sheet states preserved (AR & Collections, RR_Calc, T12_Calc, Workbook Health)
- Migration idempotency confirmed (re-run on v0.2.12 file → no-op)
- Track 5 regression test: **27 / 27 pass**

### Carry-forwards

- **Track 5 regression fixture rebuild against v0.2.12** — the fixture at `Sample Files/dashboard/regression_v0211.xlsx` is still v0.2.11. Once rebuilt against v0.2.12, the three `test_known_divergence_*` cases (which currently assert divergence between Python's blended values and xlsx's segment-specific values) can flip to equality assertions. Currently passing only because the fixture is stale.
- **Streamlit Cloud reboot + visual smoke** — auto-deploy from `origin/main` lands within ~30-60s; CLAUDE.md "reboot-first rule" recommends a hard reboot from share.streamlit.io before debugging any divergence.
- **Patch file cleanup** — `0001fixDashboardblendedvssegmentformulamisrefssu.patch` at repo root is now applied; deleted in the same session as housekeeping.

### Open backlog after this session

UW-BACKLOG.md Pending: **BL-0019 only** (persistent audit log, Track 1 — unchanged since 2026-05-19, user-deferred to "later").

---

## 2026-05-24 — Track 5 (Webapp Dashboard Surface) v0.1.0 — initial release

User attached a Homestead populated Analyzer and asked: "I want this Dashboard replicated into the webapp after it parses through the data. What's the best approach here for modularity?" Discovery confirmed the attached Dashboard is bit-identical to the bundled v0.2.11 substrate Dashboard (0 cell diffs, same 6 charts, same 442 cells) — the ask is to **surface that data inside the Streamlit UI**, not to populate a different xlsx.

After ruling out Streamlit `st.dialog` modals (too cramped on phone screens, ~700px width cap), user picked: a `📊 Dashboard` tab in the post-parse output, full-width on mobile.

### What shipped

- **`dashboard_model.py`** — pure-Python compute layer. 44-field `DashboardModel` dataclass; `compute_dashboard(rr_result, t12_result, ar_result=None, ...)` mirrors T12 Analytics col-E aggregation (`totals[label] += row.total` over GLRows grouped by Description_Map label). Constants for the 24 non-labor labels, 8 direct-labor labels, 6 payroll-burden labels match the T12 Analytics sheet structure exactly. No Streamlit imports.
- **`dashboard_ui.py`** — Streamlit-only renderer. `render_dashboard(model)` produces mobile-friendly single-scroll layout: `st.metric` tiles in `st.columns(2)` (auto-narrows on phones), `st.dataframe(use_container_width=True, hide_index=True)` for tables, Altair donut + bar charts via `st.altair_chart(use_container_width=True)`, `st.success/warning/error/info` for risk flags.
- **`app.py`** — wraps the existing post-parse Export section in `st.tabs(["📊 Dashboard", "⬇️ Download"])`. Dashboard tab calls `compute_dashboard` + `render_dashboard` (graceful info-banner when T12 absent). Download tab holds the unchanged RR + combined-Analyzer download buttons. New imports: `compute_dashboard`, `render_dashboard`, `derive_property_name` (hoisted to module top).
- **`tests/test_dashboard_model.py`** — 27-case regression suite. Reconstructs `NormalizeResult` + `T12ParseResult` from a populated Analyzer fixture's Rent Roll Input + T12 Input cells, runs `compute_dashboard()`, asserts each metric matches the xlsx's `data_only=True` cached values within tolerance. All 27 pass.
- **`SPEC-T5.md`** + **`CHANGELOG-T5.md`** + **`tests/fixtures/dashboard/README.md`**. CLAUDE.md gets the Track 5 row added to the Workstream tracks table.
- **Last-updated stamp** on CLAUDE.md bumped to 2026-05-24 with the Track 5 summary.

### Why pure Python (and not a formula evaluator)

openpyxl can't evaluate Excel formulas — reading `data_only=True` on a Python-written workbook returns `None` for every formula cell. The Dashboard is a formula-reference layer over T12 Analytics (itself a formula sheet). Three paths considered:

1. Add `formulas` / `pycel` dependency + recalc — heavy on Streamlit Cloud, library quirks across the formula surface, slow.
2. LibreOffice headless subprocess — won't run on Streamlit Cloud.
3. Re-derive metrics in Python ← **chosen**. Bounded scope (~60 metrics), simple arithmetic over parsed objects, zero new dependency, testable.

The regression test against the xlsx fixture is the drift guard in either direction.

### Cross-track work disclosed and authorized

This is a new track (Track 5). It touches `app.py` (Track 1 territory) and adds two new modules. CLAUDE.md scope discipline was raised explicitly: "this is a new workstream — doesn't cleanly fit Tracks 1-4." User authorized as Track 5 and asked to "proceed through work using track 5 as dashboard track."

### Xlsx Dashboard cross-reference bugs discovered (Track 3 follow-up spawned)

Three cells on the bundled v0.2.11 Dashboard reference single-care-type cells in T12 Analytics while being labeled as blended/community values on the Dashboard:

| Dashboard cell | Labeled as | Pulls from | Actual content |
| --- | --- | --- | --- |
| `B6` | "Normalized community occupancy" | `T12 Analytics!F134` (`=C11/C6`) | **AL-only** occupancy |
| `F20` | "Blended ADR / day" | `T12 Analytics!F140` (`=D20/(D11*12)`) | **MC-only** ADR |
| `K6` | "Normalized RevPOR per resident" | `T12 Analytics!F143` (`=(D20+D27)/(D11*12)`) | **MC-only** RevPOR |

Homestead fixture impact: occupancy 64.5% (AL-only, xlsx) vs 72.7% (blended, Python correct); ADR $6,802 (MC-only, xlsx) vs $4,546 (blended, Python correct); RevPOR $6,802 (MC-only, xlsx) vs $4,562 (blended, Python correct). Python is structurally correct; xlsx Dashboard has the cross-reference bug. Regression test has explicit `test_known_divergence_*` cases.

A Track 3 substrate-fix task was **spawned** (worktree chip on user's screen) to rewrite the three Dashboard cells to reference the correct blended cells in T12 Analytics. When that lands, webapp Dashboard tab and downloaded xlsx Dashboard will align.

### Verification

- `python3 -m unittest tests.test_dashboard_model` → **27 / 27 pass**.
- `python3 -c "import ast; ast.parse(open('app.py').read())"` → app.py parses cleanly.
- Manual smoke against the bundled Analyzer + Homestead populated fixture: every metric matches the xlsx within 0.5% relative tolerance except the three known-divergence cells.
- Live deploy verification (Streamlit Community Cloud reboot after push) — pending.

### Carry-forwards

- Streamlit Cloud reboot + visual smoke after push.
- Track 3 spawned task: Dashboard cell B6/F20/K6 cross-reference rewrites (substrate v0.2.12 or whatever the next bump is).
- T5 v0.2.0 follow-ups: lift purchase price input into the UI (currently `None` → cap-rate tiles dim until user opens xlsx and sets `T12 Analytics!E117`); lift AR parse before the Dashboard tab so AR variance is visible immediately (currently AR is parsed at download time only).

---

## 2026-05-24 — Hotfix: text-as-formula bug in v0.2.10/v0.2.11 (sheet2.xml repair)

Short session, started from a user-reported Excel repair dialog: opening the bundled `ALF_Financial_Analyzer_Only.xlsx` produced

> Repair Result to ALF_Financial_Analyzer_Only0.xml
> Removed Records: Formula from /xl/worksheets/sheet2.xml part

### Diagnosis

`sheet2.xml` = Dashboard (per the v0.2.7 sheet order). Inspecting the pre-repair file's sheet2.xml found the corrupted formula at **`Dashboard!K13`** — the v0.2.11 AR variance tile footnote: `"= T12 bad debt − annualized AR write-offs"`. openpyxl's `Cell.value` setter classifies any `str` whose first character is `=` as a formula and writes it into the `<f>` element (with the leading `=` stripped per OOXML spec). When Excel opened the file it tried to parse ` T12 bad debt − annualized AR write-offs` as a formula, failed, and removed it.

The legitimate `K11` AR variance formula (`IF('AR & Collections'!Z1=0, ..., 'AR & Collections'!C56)`) was untouched — Excel kept that one through the repair pass because it's valid Excel.

A whole-workbook re-scan found a **sibling instance** of the same bug at **`AR & Collections!B47`** from `migrate_to_v0210.py` line 442: `"= Implied closing AR"`. Excel didn't fail-repair on this one but would have rendered `#NAME?`. Same bug class, fixed in the same pass.

### What shipped (commits on `main`)

- `53c2484` chore: push Excel-repaired bundled Analyzer (post v0.2.11) — captured the post-repair state of the bundled xlsx (Excel had removed K13's bogus formula); diagnosis deferred to a follow-up commit so the repair dialog stopped firing immediately.
- `24dbafe` fix: text-as-formula bug in v0.2.10/v0.2.11 migrations — patched both migration scripts (drop leading `"= "` from both label strings; added inline + docstring notes), re-wrote `Dashboard!K13` and `AR & Collections!B47` in the bundled file as plain strings (styling preserved on both). Substrate stamp unchanged at v0.2.11.
- (this commit) docs: CLAUDE.md / journal / CHANGELOG-T12 follow-up. Added the 5th openpyxl quirk to the "openpyxl quirks that bite migrations" section in CLAUDE.md.

### Verification

Whole-workbook openpyxl scan after fix: **zero** remaining text-shaped cells classified as formulas. Round-trip confirms K13 and B47 come back as `data_type='s'`, K11 comes back as `data_type='f'`. Diagnostic snippet preserved inline in commit `24dbafe`.

### Carry-forwards

- The bundled-file edits in `53c2484` + `24dbafe` did NOT bump the substrate version stamp (still v0.2.11) — this was a fix to existing v0.2.11 content, not a new substrate revision. If you re-run the migration chain v0.2.4 → v0.2.10 → v0.2.11 from a clean source after pulling these fixes, you'll get the same corrected output the bundled file now has.
- New 5th entry in CLAUDE.md's openpyxl quirks section formalizes the rule: **never start a label string with `=`** when writing via openpyxl. Inline migration-script comments enforce locally; the CLAUDE.md note is the cross-session reminder for future label adds.

### Open backlog after this session

UW-BACKLOG.md Pending: BL-0019 only (persistent audit log, Track 1 — unchanged from the 2026-05-23 session).

---

## 2026-05-23 — AR & Collections module (BL-0023) — substrate v0.2.10 + v0.2.11

Cross-cutting session: ALF underwriting now has a third operator input (AR aging) alongside RR and T12, with end-to-end pipeline from Streamlit upload → parser → writer → populated Analyzer sheet → Dashboard tile.

### What shipped (commits on `main`)

- `e2f26d5` feat: AR module foundation — substrate v0.2.10 + mappings extension
- `05ebf7a` feat: AR aging parser (ar_normalizer.py) + synthetic fixture
- `41db0bd` feat: AR writer + Streamlit upload — wire AR pipeline end-to-end
- `983573c` feat: substrate v0.2.11 — Dashboard AR variance tile + Cover AR version line
- (this commit) docs: finalize AR module — CHANGELOG-T12 / UW-BACKLOG / journal / CLAUDE updates

### Design decisions — Cowork handoff review

User-supplied design handoff (`2026-05-23-AR-Collections-Claude-Code-Handoff.md`) reviewed against codebase. **12 spec issues raised:** terminology (xlsx vs webapp), payer taxonomy (spec's 6 buckets vs Dashboard's 6 vs mappings.py's 5+fallback — three different mental models in tension), impossible sheet position ("after T12 Analytics, before Dashboard" can't be since Dashboard is at index 1), Workbook Health AR-replace claimed additive but actually disruptive, 3 Dashboard tiles requested but only K10:L13 free, missing cell pins, etc. All 12 decided in conversation to fit current webapp flow; handoff-back-to-Cowork block produced for spec Rev 2.

**Key decisions made and shipped:**
- Sheet at index 8 (between Monthly Trending and UW Output)
- AR fully optional (default = no AR file → AR sheet hidden, Z1=0, all integrations inert)
- Workbook Health B43 wrapped in IF guard — RR fallback preserved bit-for-bit
- P5 gate inserted at row 52, summary moved to row 53 (verified zero external refs to WH!B52)
- Only ONE Dashboard tile (variance flag at K10:L13); DSO + %aged 90+ live on AR tab
- 7 payer rows on AR §3 (matches mappings.py normalization targets, not spec's 6)
- mappings.py `PAYER_FALLBACK` unchanged ("Private Pay") — AR uses per-instance `"Self-Pay + Other"` via `MappingSet(payer_fallback=...)`

### Bundled file state

Forward-applied v0.2.4 → v0.2.10 → v0.2.11 directly (per BL-0021 carry-forward; bundled still skips v0.2.5-v0.2.9 substrate features — those are chain-only). Bundled now at v0.2.11. `ANALYZER_SUBSTRATE_VERSION` in `app.py` was stale at "0.2.4" — bumped to "0.2.11" along with the v0.2.11 commit.

### Live operator AR sample — PENDING

Built against synthetic only (`tests/fixtures/ar/ar_synthetic_v01.xlsx`: 12 residents × 14 cols, exercises all 7 payer buckets including the new Managed Care via "Medicare Advantage" / "MCO" / "UHC MA Plan" rows). When a real operator AR aging file lands (in `Sample Files/` per the T12 convention — gitignored), the fuzzy header rules will need expansion to absorb operator-specific naming variations. Documented in `tests/fixtures/ar/README.md`.

### Carry-forwards

- AR↔RR row-level join for §5 C62/C63 flags (resident-in-90+-with-concession, vacant-with-non-zero-AR) — needs ar_writer extension to read Rent Roll Input from the same workbook. Stubbed to 0 for now.
- Live operator sample triage + fuzzy-rule expansion (per above).
- Standalone CHANGELOG-AR.md (deferred until live-sample work matures; consolidated into CHANGELOG-T12.md under v0.2.10/v0.2.11 for now).

### Open backlog after this session

UW-BACKLOG.md Pending: BL-0019 only (persistent audit log, Track 1 — still deferred from before this session).

---

## 2026-05-20 — Substrate v0.2.8 (Cover!B5 resolver, BL-0022) + MF product-line Phase 0

Two distinct pieces this session, both shipped/built off a freshly-pulled `origin/main`.

### Part 1 — Substrate v0.2.8 (Track 3, shipped + pushed)

**Cautionary tale up front:** session started ~10 commits behind `origin/main`. First pass built v0.2.5 (Section M6) + a bundled v0.2.6 (Cover!B5 + Dashboard anchors) + doc renames + BL-0018/0019 — *all of which collided with work already on origin* (BL-0012 shipped as v0.2.5 by another session; BL-0016/0017 as v0.2.6; BL-0018 Dashboard redesign as v0.2.7; BL-0019/0020/0021 used). Discarded the entire first pass via `git restore`, pulled, and rebuilt only the genuinely-new piece. **Lesson saved to memory: when session-start gitStatus says "behind by N," fetch + inspect upstream BEFORE planning.**

**What shipped (commit `7af8e0e`):** substrate **v0.2.8 / BL-0022** — `Cover!B5` rewired from a static manual-entry cell to a 2-priority property-name resolver (`Rent Roll Input!A3` → `T12 Input!A10` → ""). RR/T12 writers had been stamping those inputs since 2026-05-11, and `T12 Analytics!B2` resolved via path 1, but Cover itself stayed blank — leaving `Dashboard!B2` title, `UW Export!B3`, `Workbook Health!B27`/`C27`/`B49` all reading "missing"/"(not set)". v0.2.8 fixes Cover; the 5 consumers cascade. `Cover!A19` docstring updated. Defensive skip preserves user-typed B5 text. Migration `migrate_to_v028.py` (4 ops, 10-check verify, idempotent). Bundled file stays at v0.2.4 per BL-0021. Chain-tested v0.2.4 → v0.2.8 clean. Docs: CHANGELOG-T12 / SPEC-T12 / CLAUDE / UW-BACKLOG.

### Part 2 — MF (multifamily) product line, Phase 0 (Track 1, built this session)

**New product dimension.** The whole stack to date is ALF (senior housing). User wants a parallel **MF (multifamily)** pipeline: `login + ALF/MF selector → MF intake mapping of RR/T12/AR/OM (comps + property info) → MF Analyzer (to be built) → UW Template`. Scoped as a multi-phase program; building **Phase 0** first.

**Sample data:** `MF Docs/` (property *Hidden Lakes*, 143-unit, ~46% occupied). Four files inspected — RR ("Rent Roll - Cim", units/floorplans/lease/rent), T12 ("PSI T-12", account#+name+12mo, shaped like the ALF Yardi T12), AR ("Resident Aged Receivables", aging buckets per unit), and a Sortable-RR with a Floor Plan summary tab. No OM sample yet.

**Phase 0 scope (this session):** the ALF/MF mode switch + access seam, MF stubbed.
- `auth.py` — added `APP_MODES = ("ALF","MF")` + `allowed_modes(username)` returning **both modes for everyone** (Phase 0), with a fully-documented seam for future per-user `[auth.access]` secrets gating. When that lands, `allowed_modes` is the ONLY function that changes — app.py already auto-routes + hides the selector when one mode is returned.
- `app.py` — captured `username` from `require_login()` (was discarded); added an ALF/MF `st.radio` right after login; `st.stop()` into `_render_mf_placeholder()` for MF; ALF falls through to the existing pipeline **completely unchanged**. Browser tab `page_title` aligned to the new "Underwriting Intake" branding (was "Senior Housing Normalizer (RR + T12)").
- MF placeholder renders the planned 4-step pipeline as a roadmap ("coming soon").

**Integrated on top of the Pingkas Capital branding commits.** Phase 0 was built before pulling, then origin moved 4 commits ahead (Pingkas brand theme, centered logo, "Underwriting Intake" title, Analyzer-version badge — `branding.py`, `.streamlit/config.toml`, `assets/`). Stashed → fast-forward pulled → popped: only `app.py` conflicted (one import line — kept both `allowed_modes` and `branding` imports). Reordered so `render_centered_logo()` runs **before** the mode selector — the brand logo shows at the top in **both** ALF and MF modes, with the selector beneath it.

**Access-control decision (answering user's Q):** single app + radio selector (not multipage), gated per-user via a future `[auth.access]` secrets table. Per user direction, Phase 0 grants **both modes to all logged-in users**; the per-user access-type restriction is deferred to a later authenticator change. Seam is in place.

**Verified:** `py_compile` clean on `app.py` + `auth.py`; no conflict markers anywhere; `allowed_modes` + both branding helpers coexist; logo-before-selector ordering confirmed; ALF pipeline below the branch untouched.

**Next phases (not started):** Phase 1 = MF RR normalizer → standalone MF workbook (design against Hidden Lakes RR). Phase 2 = MF T12 + AR intake. Phase 3 = OM/comps. Phase 4 = MF Analyzer + UW Template.

---

## 2026-05-16 — Substrate v0.2.4 (Investment Dashboard) + (separately) Streamlit password gate

**Started as:** Track 1 chat to add a password gate to the Streamlit app — multi-user, SHA-256 hashes in `st.secrets["auth"]["users"]`, login events printed to stdout for Cloud-log audit trail. Built `auth.py`, wired it into `app.py` immediately after `st.set_page_config()`, added `tools/hash_password.py` CLI helper, added `.gitignore` entry for `.streamlit/secrets.toml`. Shipped as [PR #28](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/28) — `claude/relaxed-moser-309127` branch — still open at time of this entry.

**Pivoted to (with user authorization, fresh branch off origin/main):** Track 3 substrate work — add a new `Investment Dashboard` sheet to the bundled Analyzer, sourced from a Beaufort populated sample the user pointed at (`Sample Files/Analyzer with Beaufort Rent Roll 1.31.26 + Beaufort T-12 1.31.26 2026-01-31.xlsx`). Explicit cross-track confirmation per the CLAUDE.md scope-discipline convention.

### Scope (substrate v0.2.4)

**Single op: add `Investment Dashboard` at workbook index 1.** 97 rows × 7 cols (B2:H98), 335 styled cells. Pure formula-reference layer over `T12 Analytics` + `Rent Roll Recon`. No existing-data mutation; no row inserts; no named-range additions; no formula on any other sheet changes. Sheet count 14 → 15. Seven sections: AT-A-GLANCE T12 ACTUAL (rows 7-9), Occupancy & Capacity (11-17), Revenue & Rate Performance (19-28), Margin & Cost Structure (30-46), Valuation & Acquisition (48-57), Payer Mix (59-68), AL Care Level Distribution (70-81), plus a Key Risks & Normalization Callouts table (85-94, 🔴🟠🟢 flagged).

**Approach decision:** rather than encode the dashboard's 335 styled cells programmatically (would balloon the migration ~10×), extracted the source sheet once into a committed template asset at `tools/migration/v024_assets/investment_dashboard_template.xlsx`. Migration copies it cell-by-cell at runtime, preserving fonts / fills / borders / alignment / number formats / protections. Template asset becomes a permanent fixture in the repo; future style edits go through Excel/LibreOffice on that file, not through code. Trade-off noted in SPEC-T12.md and CHANGELOG-T12.md.

**Pre-flight cross-checks** against the destination Analyzer's referenced cells: 56 distinct `T12 Analytics` references — 55 resolve to populated cells, 1 expected blank (`T12 Analytics!E117` Purchase Price, manual analyst input). 27 distinct `Rent Roll Recon` references — all resolve. No dangling references after migration.

### Deliverables

- `tools/migration/migrate_to_v024.py` (280 lines, idempotent with the dual-gate `Cover!B8 == v0.2.4 AND Investment Dashboard at sheetnames[1]`, 11-check verification).
- `tools/migration/v024_assets/investment_dashboard_template.xlsx` (new — single-sheet template).
- `ALF_Financial_Analyzer_Only.xlsx` regenerated to v0.2.4 (sheet count 14 → 15, all 15 AZ4 anchors stamped, Cover!B8 stamped).
- SPEC-T12.md current-version line bumped + v0.2.4 entry added to history.
- CHANGELOG-T12.md v0.2.4 entry inserted above v0.2.3 (newest at top).
- CLAUDE.md last-updated line, current substrate version table cell, and new closed carry-forward entry.

### Worktree topology

- `claude/relaxed-moser-309127` — PR #28 (password gate, Track 1) — held intentionally on its own branch.
- `claude/investment-dashboard-substrate-v024` — new worktree off `origin/main` (commit `e6c5279`) for this entry. Independent PR so password gate + dashboard can merge in either order.

### Scope-discipline note

Same chat session served two tracks (Track 1 password gate, then Track 3 dashboard), but each got its own branch off main, each got its own PR, and the cross-track pivot was explicitly confirmed with the user before proceeding. CLAUDE.md "one track at a time" preserved at the PR level, not at the chat level — which matches the precedent set by the 2026-05-15 RR v1.17.5 BL-0011 + BL-0013 + BL-0014 cross-cutting tidy-up entry below.

### Carry-forwards opened

- None substrate-side at v0.2.4.
- The Beaufort sample file lives in `Sample Files/` (gitignored). Future style updates to the Investment Dashboard go through the template asset, not the sample — the sample is property-specific data and stays out of the repo.

---

## 2026-05-15 — RR v1.17.5 (UW-BACKLOG BL-0011 + BL-0013 + BL-0014 tidy-up)

**Started as:** Continuation of the 2026-05-14 chat that shipped substrate v0.2.3 (BL-0015) in PR #24. After PR #24 was opened (still pending merge as of this entry), user asked "what's left open?" then authorized "proceed with BL-0011 + BL-0013 + BL-0014" as a single bundled tidy-up PR.

**Stayed as:** Cross-track docs + refactor chat by explicit user authorization. BL-0011 is Track 1 (RR code), BL-0013 is cross-cutting (README), BL-0014 is Track 3-adjacent (CLAUDE.md). Branched off `origin/main` (not off PR #24's branch) so this PR can merge independently of #24 in either order.

### Scope

**BL-0011 — Function/class renames on `analyzer_rr_writer.py`** (Track 1 refactor, no behavioral change):
- `populate_t12()` → `populate_rr_input()` (function correctly populates Rent Roll Input, not T12 Input)
- `T12CapacityError` → `AnalyzerRRCapacityError` (exception class matches the file rename done 2026-05-10)
- Took the opportunity to also rename the function-body parameter `t12_bytes` → `analyzer_bytes` and clean up two inline "T12 workbook" → "Analyzer workbook" mentions, since the same misnomer rationale applies inside the function too.
- Updated callers in `app.py` (1 import, 1 call site, 1 except clause).
- Live docs updated: `CLAUDE.md` "Module naming gotcha" table cell + `SPEC-T12.md` module-naming-history paragraph.
- Historical CHANGELOG / journal references to the old names left intact (records of what shipped at past versions — same convention as the 2026-05-10 file rename).

**BL-0013 — README modernization** (targeted updates, NOT a full rewrite):
The README had been substantially modernized since the BL ticket was opened — dual-pipeline framing and T12 coverage were already in place. Actual updates needed were narrower:
- Versions table bumped to RR v1.17.5 / 2026-05-15.
- Data-capture coverage section refreshed from "RR v1.16.0 + substrate v0.1.10 (cols A-AB)" to "RR v1.17.4 + substrate v0.2.2 (cols A-AH)" — adds the v0.1.13 per-fee ancillary cols (AC-AG), the v0.2.2 Total Ancillary rollup (AH), the v0.2.1 5 finer T12 Labels closing the per-fee attribution gap on Section M, and the v1.17.4 parser-side Notes-rerouter.
- Analyzer-at-a-glance reframed as "Track 3 four-branch roadmap fully closed at substrate v0.2.0" with Section M, UW Export sheet, and Pre-Export Gate descriptions.
- Versioning section: substrate convention `v0.1.N` → `v0.X.Y`.
- UW-BACKLOG.md mention added in two places (Versioning section + Further Reading table).

**BL-0014 — CLAUDE.md hygiene** (two parts):
- **Open carry-forwards section**: header date refreshed; entire "Medium priority" + "Low priority" sub-sections removed (they were stale by weeks — Branch 2 / version-detection bug both shipped). Replaced with a single sentence pointing at UW-BACKLOG.md as the source of truth.
- **openpyxl quirk #4**: expanded with the qualified-range-endpoint trap from BL-0001's migration. Documents both the failure mode (`T12_Calc!$N$1:$N$500`'s endpoint mis-caught by the unqualified-ref regex and shifted on row inserts) and the canonical fix (capture template formulas AFTER the shift sweep). Section heading bumped from "Three" to "Four" since the quirk is now substantive.

### Implementation calls made

- **Branch off `origin/main`, not off PR #24's branch.** PR #24 hadn't merged yet at session start. Branching off main keeps this PR independent — user can merge in either order. Some doc files (CLAUDE.md, journal.md) will conflict trivially with #24 if #24 merges first; that's a known mechanical rebase, not a design issue.
- **Bundle as a single PR despite cross-track scope.** User explicitly authorized "BL-0011 + BL-0013 + BL-0014" as one tidy-up PR. Coherent change set: docs/refactor maintenance, no behavioral risk, no substrate change. Same precedent as the 2026-05-11 multi-track session (where user said "Perform all tracks").
- **Leave `translate_for_t12()` alone.** It's the last `t12_*` symbol on the Track 1 side, but `for_t12` reads as "for the destination workbook" rather than "for T12 data" — and renaming it would touch every caller of the translator. CLAUDE.md note records this decision so a future chat doesn't re-litigate.
- **Don't back-fill v0.1.11 → v0.2.2 journal entries.** I noted this gap in my BL-0015 journal entry as an observation. BL-0014's formal scope doesn't include it (the description only mentions the carry-forwards section + openpyxl quirk #4). Doing it now would expand scope and require chat archaeology against 8 missed releases. Leaving it as an open observation, not formally backlogged. The journal.md "Note 2026-05-14" I added in the v0.2.3 PR already flags the gap for any future reader.
- **Don't rewrite historical CHANGELOG / journal references.** Same convention as the 2026-05-10 file rename — historical entries are records of what shipped at past versions; renaming would falsify history. Live docs (CLAUDE.md gotcha table, SPEC-T12.md naming paragraph) get updated; everything else stays.

### Verification

- `python3 -c "import analyzer_rr_writer"` — module imports cleanly with new symbols (`populate_rr_input`, `AnalyzerRRCapacityError`); old symbols (`populate_t12`, `T12CapacityError`) confirmed removed via `assert not hasattr(...)`.
- `python3 -c "import ast; ast.parse(open('app.py').read())"` — app.py parses cleanly.
- `grep -rn "populate_t12\b\|T12CapacityError" --include="*.py"` (excluding `populate_t12_input` which is the legitimate Track 2 partner) — zero remaining live references in code; the only mentions are in CHANGELOG / journal historical entries (intentional).
- README.md and CLAUDE.md edits visually inspected; no broken markdown.

### Files at session end

- `analyzer_rr_writer.py` — function/class/parameter renames + docstring updates
- `app.py` — import + call site + except clause + RR_VERSION 1.17.4 → 1.17.5 + RR_LAST_UPDATED → 2026-05-15
- `README.md` — targeted updates per BL-0013
- `CLAUDE.md` — Module naming gotcha + Open carry-forwards section condensed + openpyxl quirk #4 expansion
- `SPEC-T12.md` — module-naming-history paragraph
- `UW-BACKLOG.md` — BL-0011 / BL-0013 / BL-0014 moved from Pending to Shipped (one-paragraph summaries each)
- `CHANGELOG-RR.md` — new `[1.17.5] — 2026-05-15` entry at top
- `journal.md` — this entry

### Carry-forwards opened

None new. UW-BACKLOG Pending shrinks from 4 items to 1: only BL-0012 (Misc/Diabetes credit reconciliation) remains, and that's conditional on observing the same negative-residual pattern in a non-Homestead deal — may stay deferred indefinitely.

### Process lessons

1. **The BL ticket descriptions can be stale themselves.** BL-0013's description claimed the README was "RR-Normalizer-only project" — but reading the actual file showed it had been substantially modernized since the ticket was opened. The right work was a targeted update of 4-5 sections, not a full rewrite. Lesson: read the current state before trusting a backlog ticket's description; tickets age.
2. **Bundling refactor + docs in one PR works well when there's no behavioral risk.** All three BLs are zero-runtime-risk: BL-0011 is symbol renames with import + call-site updates, BL-0013/14 are pure docs. Bundling kept context together (the same chat reviews CLAUDE.md gotcha, README, and the renamed file) and reduced PR overhead. Wouldn't bundle if any one item touched substrate or parser logic.
3. **The "preserved as historical artifact" note becomes a debt that compounds.** When BL-0010 shipped the file rename on 2026-05-14, leaving `populate_t12()` and `T12CapacityError` as artifacts felt surgical. By BL-0011 today (one day later), the artifact rationale already needed updating ("could be renamed to X in a follow-up" → "renamed to X on Y"). Each artifact adds a maintenance footnote. Better to bundle the full rename when scope allows; deferring just moves text-editing cost forward.

---

## 2026-05-14 — Substrate v0.2.3 (Rent Roll Recon row 16 GPR fix · BL-0015)

**Started as:** Continuation of the 2026-05-12 chat that shipped (or thought it shipped) substrate v0.1.11 in PR #12 — the Rent Roll Recon row 16 GPR realignment. User asked for "review current status" two days after the PR was opened. Local branch was 23 commits behind origin/main, and PR #12 was still open + conflicting because main had moved through v0.1.12 → v0.2.2 (with v0.1.11 substrate number reused for an unrelated chart-axis fix at `tools/migration/migrate_to_v0111.py`).

**Stayed as:** Track 3 chat. The fix is workbook-only — no RR / T12 code touched. User authorized close-and-re-implement after the status review.

### Status review findings

Verified directly against `origin/main` that the row 16 bug from 2026-05-12 was still present in production:
- `Cover!B8 = v0.2.2`
- `A16 = "RR gross contracted base rent / mo"` (old label)
- `B16` still `SUMIFS($H, ..., E<>Vacant, E<>Eviction, ...)` (old formula)
- `H16 = "Gross contracted rates before concessions"` (old note)

Meanwhile main had shipped substantial work I needed to absorb before re-implementing:
- **Branch 2 — Handoff readiness** (BL-0009) shipped at substrate v0.2.0 with a new `UW Export` sheet → `ANCHOR_SHEETS` is now 14 sheets (was 13)
- **`t12_translator.py` → `analyzer_rr_translator.py` rename** (BL-0010, RR v1.17.2)
- **`UW-BACKLOG.md` system formalized** with `BL-NNNN` IDs (this superseded the ad-hoc "carry-forwards" lists I was working from)
- **Rent Roll Input cols A→AH** (was A→AB in v0.1.10) — but col G (Market Rate) at the same position, so the fix targets unchanged
- **Section M added at Rent Roll Recon rows 121-167** — well below row 16, no collision

Several of my originally-listed open carry-forwards from the v1.16.0 journal entry had been closed: Branch 2 → BL-0009, translator rename → BL-0010, version-detection → BL-0008, 2P recon row → BL-0004, Workbook Health AR → BL-0005, PSF stats → BL-0006.

### Re-implementation calls made

- **Same fix, new substrate number.** The v0.1.11 → v0.2.3 transition is a number bump only — formula, label, and note text identical to the 2026-05-12 implementation. Numerical result on Homestead populated identical too: $565,140 → **$809,567** (E16), row 17 unchanged at $565,140, gap = $244,427.
- **`ANCHOR_SHEETS` extended to 14.** Added `UW Export` (from BL-0009 / v0.2.0) so the AZ4 stamp covers it.
- **Idempotency gate keyed on `$G$7:$G$606` in B16.** Same shape as v0.1.11 gate — version stamp + structural marker — but the marker is now the new column reference rather than a chart-axis state.
- **PR #12 closed unmerged with replacement pointer.** Comment links to the new PR. Migration script numbering convention has shifted (`migrate_to_v0NN.py` → `migrate_to_v0NN.py` with 3 digits compressed; new is `migrate_to_v023.py`) and the v0.1.11 number is permanently reused on main for the chart-axis patch.
- **journal.md sees its first new entry in 3 days.** Back-filling v0.1.11 → v0.2.2 entries deferred to BL-0014 (CLAUDE.md hygiene).

### Verification

End-to-end on both fixtures:

1. **Bundled template Analyzer** — `Cover!B8 = v0.2.3`, all 14 AZ4 stamped, all 9 verifier checks green. Idempotency confirmed (re-run on the migrated file = no-op).
2. **Populated Homestead Analyzer** (Dropbox; latest copy at `Analyzer with 2026-04-24 Homestead Village Rent Roll v2 + March 2026 T12 2026-04-24.xlsx`, no longer the `(1)` variant from 2026-05-12) — same 9 checks green. Simulated SUMIFS by care type against actual data:
   - B16 IL: $167,155.63 (62 units)
   - C16 AL: $327,776.35 (62 units)
   - D16 MC: $314,635.03 (52 units)
   - **E16 = $809,567.01** ← matches user's $809k expectation
   - Row 16 − Row 17 = **$244,426.97** = vacancy + market-vs-actual gap

### Infrastructure side-effect

`gh` CLI from 2026-05-12 install (Homebrew, v2.92.0, authenticated as `ErikJ-Stack`) reused for PR creation + PR #12 close. No new infrastructure work this session.

### Files at session end

- New: `tools/migration/migrate_to_v023.py` (3 ops, 9-check verify, idempotent — gate checks both `Cover!B8` AND that B16 references `$G`)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (regenerated v0.2.3)
- Updated: `UW-BACKLOG.md` (BL-0015 added to Shipped section)
- Updated: `CHANGELOG-T12.md` (v0.2.3 entry at top with cross-reference to PR #12 history)
- Updated: `SPEC-T12.md` (current substrate version line + v0.2.3 history entry)
- Updated: `CLAUDE.md` (last-updated, current substrate version, new "Closed 2026-05-14" entry, "post-substrate v0.2.3" version-stamp on the carry-forwards section)
- Updated: `journal.md` (this entry + the 3-day-gap note above)

### Carry-forwards opened

None new. The remaining UW-BACKLOG pending items are unchanged: BL-0011 (function/class renames), BL-0012 (Misc/Diabetes credit recon), BL-0013 (README modernization), BL-0014 (CLAUDE.md hygiene + journal.md back-fill).

### Process lessons

1. **A PR that doesn't merge for 2 days against an active main is a dead PR.** Main moved 23 commits past PR #12 in two days. The v0.1.11 substrate number was reused on main for an unrelated patch, structurally guaranteeing the original PR could never merge cleanly. Lesson: when a one-shot substrate-version-number PR is opened, follow up within hours; if it can't be reviewed promptly, withdraw it explicitly so the version number is freed for other work.
2. **The UW-BACKLOG system would have caught this earlier.** If the original 2026-05-12 work had been logged as a `BL-NNNN` item before opening the PR, the next chat would have seen it as "Pending" while main moved forward, and either picked it up or explicitly deferred. The ad-hoc "carry-forwards in CLAUDE.md" approach we used at v0.1.11 didn't survive the cadence.
3. **Re-implementing a known-good fix against a moved-target main is cheap when the fix is single-cell.** Total turnaround on the re-implementation today was minutes — formula, label, and note all copy-pasted from the v0.1.11 implementation; only the version constants and `ANCHOR_SHEETS` list needed editing. If the original fix had been larger / more interleaved with surrounding state, a 2-day gap on main would have made it expensive to revive.

---

## 2026-05-11 — RR v1.16.0 + Substrate v0.1.10 (Data-capture expansion)

**Started as:** Continuation of the same 2026-05-11 session that shipped substrate v0.1.8 (Branch 3) → v0.1.9 (xludf fix) → RR v1.15.0 (property name stamp). User opened the v0.1.9 populated Analyzer in Excel after running their Homestead RR through the pipeline, noticed `Rent Roll Input` was missing 2nd Person Rent and other charges they could see in the source, and asked: "what other relevant information isn't being outputted... what are the other recommended changes to capture all data and transferred properly for future full UW".

**Stayed as:** A multi-track chat by explicit user authorization ("Perform all tracks") after I proposed a 3-tier plan and offered to ship Tier 1.1 only. User overrode and asked for full coverage.

**Scope:**
- Track 1 (Tier 1.1) → RR v1.15.1: widen `looks_care` heuristic to catch Pet / H/K / Laundry / Misc. / Diabetes; widen `move_in` / `move_out` patterns for Rent Start / Rent End / MoveOut Date headers
- Track 1 (Tier 1.2 + Tier 2 + Tier 3) → RR v1.16.0: 7 new resident-level fields (2nd Person Rent, Move-out Date, Balance, Notes, Market PSF, Actual PSF, ACH) captured by parser + flowed through Condensed_RR / Normalized_Beds / translator / analyzer_rr_writer
- Track 3 → substrate v0.1.10: new column headers at Rent Roll Input!V4:AB4 + extended Total Monthly Rev formula (U7:U606) to include +V (2nd Person Rent)

### Diagnostic phase

Loaded the source Homestead RR (`2026-04-24 Homestead Village Rent Roll v2.xlsx`) and the user's downloaded populated Analyzer side by side. Source has 33 columns of per-resident data; output Condensed_RR has 18. The auto-catch-into-Other-LOC heuristic at `normalizer.py:251-256` gated on a narrow keyword list (`"care charge"`, `"med mgmt"`, `"pharmacy"`, `"level of care"`, `"ancillary"`, `"service charge"`, `"other charge"`). Homestead's column names (`Pet`, `H/K`, `Laundry`, `Misc.`, `Diabetes`, `SP`) didn't contain any of those keywords, so every charge was silently dropped. Verified across 12 occupied IL residents — every single one had populated charges that didn't make it to the output. **Sandra & Darryl Owens (A14) most dramatic case: $750/mo of revenue ($650 SP + $100 H/K) entirely missing.**

### Design phase

Researched what UW needs vs what the RR captures. Produced a 3-tier recommendation:
- Tier 1.1 (must) — keyword widening to recover existing-bucket revenue
- Tier 1.2 (must) — dedicated 2nd Person Rent column (housing revenue, separate from care-LOC, aligns with T12 substrate v0.1.5 `2nd Person Revenue` Label)
- Tier 2 (should) — Move-out Date / Balance / Notes
- Tier 3 (nice) — PSF rates / ACH / Rent Start pattern

User authorized all tiers. Bundled as two commits in one PR:

### Implementation calls made

- **SP (Second Person) gets its own column, not Other LOC $.** Industry distinction: 2P is incremental housing revenue tied to the apartment, not a per-resident care charge. The T12 substrate has had a dedicated `2nd Person Revenue` Label since v0.1.5 but RR had no counterpart — Rent Roll Recon couldn't reconcile 2P. Dedicated column closes that gap. SP intentionally excluded from the v1.15.1 keyword expansion to avoid bundling it into Other LOC where it would be indistinguishable from Pet/Laundry/Misc.
- **New columns append at V-AB, not insert.** Existing 18 cols (A-R) + Period Date (S) + Total LOC $ (T) + Total Monthly Rev (U) all keep their positions. This is the same lesson the v0.1.8 Branch 3 work captured (append not insert) — every Rent Roll Recon formula references specific column letters, shifting them would force a workbook-wide regex sweep.
- **Move-out Date already in `Normalized_Beds`** (col R) but dropped from Condensed_RR. The `bed_rows` dict already captured it via line 841 of normalizer.py; just needed adding to the Condensed_RR builder. Easy win — no parser change.
- **TMR formula extension** (U7:U606) added `+IFERROR(V{r},0)` to include 2nd Person Rent. Without this, V would have been populated by the writer but never flowed into downstream aggregators reading U.
- **`_normalize_flag()` helper** for ACH — source convention varies (`"X"` / `"Yes"` / `1` / `True` all mean enrolled). One helper, predictable output (`"X"` or `""`).
- **PSF rates captured separately** rather than computed downstream. Derivable from rate ÷ sqft but having them explicit in the source makes the RR fully self-describing and reduces formula complexity in any downstream UW model that wants $-per-sqft analysis.

### Verification

End-to-end smoke against Homestead fixture:
1. `normalize_rent_roll()` → 176 rows, 25 cols (was 18), 4 couples with non-zero 2P rent ($650/$725/$800).
2. `translate_for_t12()` → 25 cols preserved (translator passes through unrecognized cols unchanged).
3. `populate_t12()` against v0.1.10 Analyzer → Rent Roll Input cols A-AB populated:
   - A3: "Homestead Village" (property name from v1.15.0 stamp)
   - V19 (Sandra & Darryl Owens 2P): $650
   - O19 (Owens Other LOC, H/K only): $100
   - Y19 (Owens Notes): "HK $100 eff 3/1- sec occ $650" ← confirms the $650 SP value
   - U19 (Owens TMR formula): `=IFERROR(H19+IFERROR(I19,0)+T19+IFERROR(V19,0),0)` ← extended correctly
   - Cover!B8: v0.1.10
4. 5-check substrate migration verifier all green, idempotent.

### Files at session end

- Updated: `normalizer.py` (FIELD_PATTERNS + `_normalize_flag` + bed-row extension + CONDENSED_COLUMNS extension), `analyzer_rr_writer.py` (SOURCE_COLUMNS_V_TO_AB + extended writer body), `app.py` (RR_VERSION 1.15.0 → 1.16.0)
- New: `tools/migration/migrate_to_v0110.py` (3 ops, 5-check verify, idempotent)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (regenerated v0.1.10)
- Updated: `CHANGELOG-RR.md` (v1.15.1 + v1.16.0 entries), `CHANGELOG-T12.md` (substrate v0.1.10 entry), `SPEC-RR.md`, `SPEC-T12.md`, `CLAUDE.md`, `README.md`, this journal entry

### Carry-forwards opened

- **Rent Roll Recon section K (IL deep-dive at rows 86-100) could surface PSF stats** now that the substrate carries them. Small future v0.1.11. Track 3.
- **T12 Analytics 2P revenue reconciliation row.** Compare `SUM('Rent Roll Input'!V) × 12` (RR-projected 2P annualized) against `T12 Raw Data!2nd Person Revenue` (T12 actual). Closes the 2P side of Rent Roll Recon. Track 3.
- **Workbook Health balance aggregation** — total outstanding AR as a validation. Track 3.

None are blocking. With this commit, the RR side captures every meaningful per-resident field from the Homestead fixture.

### Process lessons

1. **Tying out source to output side-by-side caught a systemic bug.** The keyword-list approach in `looks_care` was originally written for the Salem / Briar Glen formats; Homestead's broker-style headers don't match the same vocabulary. Without a comparison harness it's invisible from the parser side alone.
2. **2P-rent-as-housing-revenue (not care-LOC)** is a small distinction with big downstream implications. Substrate v0.1.5 made the right call adding a dedicated `2nd Person Revenue` Label for the T12 side; this round just brings the RR side into alignment.
3. **Append-don't-insert at column-extension boundaries** is consistent with the row-extension lesson from v0.1.8. Both are about preserving cell-coordinate stability for downstream formulas.

---

## 2026-05-11 — Substrate v0.1.8 (Branch 3 — Analytical coverage)

> **Refinement after first-pass commit `096fbb3`:** User clarified that the property name should land at `Rent Roll Input!A3` and `T12 Input!A10` as single-cell values (no separate `Property name:` labels). First pass had placed labels at A3 (RR) and A2 (T12) with empty B-cells (B3 / B2) as the value targets. Refined in follow-up commit on the same branch — migration now clears the leftover labels, reserves A3 / A10 as the writer/analyst value cells, and rewires `T12 Analytics!B2` to read `RR Input!A3 → T12 Input!A10 → Property_Name`. `is_already_v018()` gate extended to also verify the corrected B2 formula text, so the migration re-runs cleanly on first-pass files. Track 1/2 writer follow-ups now target A3 / A10 instead of B3 / B2.

> **Post-merge bug fix → substrate v0.1.9 (PR #8):** User opened the populated v0.1.8 Analyzer in Excel and reported that `Rent Roll Recon!B2` neither auto-populated the latest period nor offered a working dropdown. Investigation: RR_Calc!A2:A13 (the dropdown source AND the LOOKUP target the v0.1.8 design depended on) was pre-populated with `_xludf.minifs(...)` formulas — a Google Sheets / LibreOffice UDF prefix that Excel doesn't recognize → every cell resolved to `#NAME?` → the `IFERROR(..., "")` wrapper returned `""` → my v0.1.8 LOOKUP-via-RR_Calc found no numeric to return. Pre-existing flaw I should have caught when designing v0.1.8 (analogous to the v0.1.6 H20 `_xlfn._LONGTEXT` artifact). **Fix in v0.1.9:** (a) drop `_xludf.` prefix from 12 RR_Calc cells (native MINIFS works fine); (b) rewrite Rent Roll Recon!B2 to `=IF(MAX('Rent Roll Input'!$S$7:$S$606)>0, MAX(...), "")` — direct dependency on Input!S, no transitive RR_Calc dependency. Belt-and-suspenders. `migrate_to_v019.py` (3 ops, 6-check verify, idempotent — gate checks both version stamp AND zero `_xludf` remaining). **Lesson:** when designing formulas that depend on existing aggregators, verify those aggregators actually evaluate in Excel before locking the design — don't trust the formula text alone.

**Started as:** Track 3 chat. User opened a fresh session, asked me to pull main locally first, then framed the work per CLAUDE.md as workbook-only edits to the Analyzer. Specific asks: (a) T12 Analytics B2/E2 auto-population, (b) visuals on T12 Analytics starting column K with research-grounded recommendations, (c) Rent Roll Recon B2 auto-default to latest period as a dropdown, (d) IL + MC level study sections paralleling the existing AL Care Level section (row 57:67). User explicitly asked for samples + research before implementation.

**Stayed as:** A Track 3 chat throughout. Worked in git worktree `claude/eloquent-euler-d15713`. No edits to Track 1 (`writer.py`, `normalizer.py`, `mappings.py`, `pre_cleaner.py`) or Track 2 (`t12_normalizer.py`, `t12_normalizer_writer.py`, `analyzer_rr_writer.py`, `app.py`) code. Cross-track follow-ups for property-name writer stamps explicitly flagged + deferred per the one-track-at-a-time principle.

### Frame

Loaded `ALF_Financial_Analyzer_Only.xlsx` from the worktree and dumped every cell that would be touched: T12 Analytics B2/E2 + their downstream readers, T12 Analytics K-area (verified empty), Rent Roll Recon section H (rows 57-67, existing AL Care Level), data validations (none on Rent Roll Recon), Rent Roll Input header layout, T12 Input header layout, RR_Calc period dropdown source, T12 Raw Data column structure. Three grounding findings surfaced that materially affected the design:

1. **No property-name source exists in either input sheet.** Neither RR Input nor T12 Input has a property cell — only Cover!B5 carries it (manual). "Auto-extract from RR or T12" was a cross-track ask. Resolution: add input-sheet attachment cells (Track 3) now; defer the writer-side stamps to separate Track 1/2 chats.
2. **CLAUDE.md F-8 stale.** F-8 claimed Rent Roll Recon B2 was a dropdown driven by `RR_Calc!B2:B13`. Reality: no data validation existed; period dates live in `RR_Calc!A2:A13` (column A, not B), with B2:B13 holding label strings ("Period 1", "Period 2", ...). Designed B2 from scratch as a formula + new DV.
3. **AL Care Level doesn't translate 1:1 to IL/MC.** IL has no care levels by industry definition (researched CBRE / NIC MAP / Senior Housing News — IL is base-rent-only, K column empty for IL residents). MC has three dominant patterns: flat-rate, tiered 2-3 level, fee-for-service. A literal copy of section H to IL and MC would be wrong. Designed IL section as unit-type mix + sqft + rate dispersion (research-grounded), and MC section as auto-detect of flat/tiered/FFS.

Did web research on senior-housing UW visuals (CBRE Investor Survey H2 2025, NIC MAP, Cushman & Wakefield, Senior Housing News). Five standard visuals emerge: occupancy by care type, rate dispersion, payer mix, T12 revenue trend, acuity mix. Locked all 5 per user instruction ("use the optional 5th").

### Implementation calls made

- **Append-only for new Rent Roll Recon sections.** Originally proposed inserting between current rows 67 and 69 (between section H and section I). Per CLAUDE.md openpyxl quirk #4, `insert_rows()` shifts cells but not formula text — would require a full-sheet regex sweep on Rent Roll Recon plus named-range fixups. Switched to append at rows 86-117 (current max_row=84). Dependency scan confirmed no external sheet references rows 69-84, so the visual-order tradeoff (Ancillary 69-75 sits above the new IL/MC deep-dive) is the only downside. Logged as D-20.
- **Property-name source cells differ per sheet.** RR Input row 2 already holds v0.1.5 paste-instructions ("One row per resident per period..."); can't clobber. Used RR Input row 3 (verified empty) instead. T12 Input row 2 was empty, used that. Single-formula consumer at T12 Analytics B2 references `Rent Roll Input!B3` and `T12 Input!B2`. First migration run caught the mismatch via the verification block (RR Input A2 label check failed); fixed in one edit.
- **V4 monthly revenue source.** First draft used `INDEX/MATCH("Total revenue",'T12 Raw Data'!A:A,0)` — wrong: column A is `Section` (Revenue / Expense / etc.), not a Label list. There's no "Total revenue" row. Corrected to `SUMIFS('T12 Raw Data'!F:Q, A:A, "Revenue")` — sums all Revenue-section rows per month. Confirmed clean via re-run.
- **Conditional notes vs cell comments.** User asked for "popup notes, or maybe conditional notes depending on data." Picked conditional formula-driven notes (D-18). Popup comments don't react to data; conditional formulas surface only when relevant (e.g. Medicaid > 30% triggers reimbursement-risk note, otherwise shows ✓). Five notes installed at K15/K30/P15/P30/K45.
- **MC pattern detector simplification.** Originally proposed a SUMPRODUCT-based distinct-count formula directly in B103; turned out too brittle (full-column ranges + COUNTIFS array trick interactions). Switched to a simpler `COUNTIF(B106:B109,">0")` approach — count how many of the four tier rows have non-zero count, classify by that. Rows 106-109 do the heavy lifting via substring matching on K-column values.

### Workdir foot-gun (caught early)

Per the v0.2.0 retrospective lesson — my first `Write` of `migrate_to_v018.py` and `Edit`s of `OPTIMIZATION-DECISIONS.md` used absolute paths to the main repo root instead of the worktree. Caught immediately when the first migration run failed with "file not found." Recovered via `cp` to the worktree + `git restore` on main. **Same lesson as 2026-05-08: when operating in a worktree, the system-message-provided worktree directory is the only correct root.** Re-confirming for future chats.

### What shipped

**Substrate template** v0.1.7 → v0.1.8 (workbook only).

Migration script `tools/migration/migrate_to_v018.py`:
- 10 operations: input property cells, T12 Analytics B2 + E2 formulas, helper rate-bucket block, 5 charts, 5 conditional notes, Rent Roll Recon B2 default + DV, IL section K, MC section L, version stamps.
- 17 verification checks at the end. All pass on first clean run.
- Idempotency gate via `is_already_v018()`. Re-run on v0.1.8 file is a no-op.

Cell scan over all 13 sheets confirms zero formula error strings (`#NAME?` / `#REF!` / `#VALUE!` / `#DIV/0!`) introduced. Output workbook 178,451 bytes vs source 170,441 — +8KB delta for the 5 chart objects and new sections.

`OPTIMIZATION-DECISIONS.md`: Added entire "Branch 3 — Analytical coverage" section with Clusters B3.1-B3.5, discovered facts F-9 through F-15, design tables for each cluster, decisions D-15 through D-22 (also appended to the canonical Decision Log table), implementation packaging, open carry-forwards.

`SPEC-T12.md`: Current Template substrate version bumped 0.1.7 → 0.1.8. New "Template v0.1.8" entry in substrate history with full prose describing each component.

`CHANGELOG-T12.md`: New `[Substrate template v0.1.8] — 2026-05-11` entry at top.

`CLAUDE.md`: Last-updated date, current substrate version, new "Closed 2026-05-11" section, new Track 1/2 follow-up carry-forwards under Medium priority, v0.1.8 added to the version-detection-bug note.

### Discovered facts worth carrying forward

- **F-8 was stale.** Rent Roll Recon B2 had no DV at the start of this session — the historical "dropdown driven by RR_Calc!B2:B13" claim was wrong on two counts (no DV, and B2:B13 is the label column, not the date column). Corrected by writing fresh behavior. Future chats checking F-8 should now read it as "Rent Roll Recon B2 holds a LOOKUP formula for latest date, with a DV dropdown sourced from RR_Calc!A2:A13 — analyst override replaces the formula with a static value (Excel default)."
- **T12 Raw Data column map.** A=Section, B=Label, C=Care, D=Flag, E=Matched Descriptions, F-Q=M01..M12, R=T12_Total. Several aggregation formulas elsewhere reference column R (T12_Total) and column B (Label) — the new V4 helper at T12 Analytics K54:V54 introduces the first SUMIFS over column A (Section). Pattern is general — any "all revenue per month" or "all expense per month" query can use the same shape against `T12 Raw Data!$A:$A`.
- **MC pricing patterns are real.** Per research, the three patterns (flat-rate / tiered / FFS) genuinely vary across operators. The L-section pattern detector handles all three. Worth noting if Track 2 ever wants to surface this signal in `app.py` status panels or in `t12_normalizer.py` warnings.

### Carry-forwards opened

- **Track 1 RR writer follow-up** — modify `writer.py` to stamp `Rent Roll Input!B3` with the parsed property name (from source RR file metadata or filename stem). Until shipped, B3 is analyst-paste only. Surface area: `writer.py` only.
- **Track 2 T12 writer follow-up** — same shape for `t12_normalizer_writer.py` → `T12 Input!B2`. Until shipped, B2 is analyst-paste only.
- **Branch 2 — Handoff readiness** remains the next open Track 3 workstream per OPTIMIZATION-DECISIONS.md sequencing.

### Process lessons from this session

1. **Web research before designing was worth it.** Without the CBRE / NIC MAP / Senior Housing News reads, I would have likely (a) defaulted to copying section H's care-level shape into IL where care levels don't exist, (b) missed the MC pricing-pattern variance, (c) picked a less industry-standard visual set. The Branch 3 design lines up with what underwriters actually expect, not what would have been a clean Excel exercise.
2. **Pre-grounding via cell inspection caught two design errors before code.** F-8 staleness and the property-name source-cell absence both would have produced runtime issues or user confusion. Inspecting first, designing second, coding third paid off.
3. **17-check verification block + idempotency gate** caught one bug (V4 helper using wrong column lookup) and one design-mismatch (RR Input A2 vs A3) on the first migration runs. Cheap to write, expensive to skip. Same lesson as the v0.1.6 / v0.1.7 retrospectives.

### Commits this session

(To be filled in at commit time.)

### Files at session end

- New: `tools/migration/migrate_to_v018.py`
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (regenerated v0.1.8)
- Updated: `OPTIMIZATION-DECISIONS.md` (Branch 3 design appended)
- Updated: `SPEC-T12.md` (current version line + v0.1.8 history entry)
- Updated: `CHANGELOG-T12.md` (new top entry)
- Updated: `CLAUDE.md` (last-updated, substrate version, carry-forwards)
- Updated: `journal.md` (this entry)

---

## 2026-05-10 — Doc cleanup + `t12_writer.py` → `analyzer_rr_writer.py` rename

Follow-up session after the v1.14.0 + README ship. Closed three v1.14.0 carry-forwards plus the "newly identified" rename one (which was raised AND staffed in the same session — the user said "go ahead" mid-flight).

**Smoke test closed.** User confirmed Salem / Briar Glen / Oaks at Beaufort all parse cleanly under v1.14.0 (`bed_status` self-contained signal didn't regress them — the keyword gate works as intended; `*Vacant` resident markers continue through the existing resident-name path on Briar Glen, and Salem's parent-child structure is unaffected because the new signal only fires on rows with `unit/apt` info AND a recognized status keyword).

**`t12_*` "duplicate" investigation — false alarm.** PR #4 review surfaced what looked like a duplicate `t12_writer.py` vs `t12_normalizer_writer.py`. Read both files + grepped `app.py` for usage. Confirmed: four `t12_*` files exist and all four are imported and called by `app.py` at distinct sites (lines 46-51 imports, 795-806 orchestration). The `t12_` prefix originally meant "operates on the T12-shaped destination workbook" (which is now the Analyzer), not "operates on T12 data." No deletes.

**CLAUDE.md "Naming history" note rewritten.** The old note claimed `t12_translator.py` was renamed to `t12_normalizer.py` — that's flatly wrong (both files exist, with distinct functions, both wired into `app.py`). Replaced with a "Module naming gotcha" table that lists all four files and their roles, plus the line-number pointers into `app.py` so the next chat tempted to delete one as "duplicate" can verify in one grep.

**`t12_writer.py` → `analyzer_rr_writer.py` rename.** Initially flagged as a deferred carry-forward; user said "go ahead" so it shipped in this same PR. Surface area:
- `git mv t12_writer.py analyzer_rr_writer.py` — preserves git history.
- Updated docstring header inside the file (was "T12 Writer" → "Analyzer RR Writer", added explicit naming-history paragraph).
- Updated import in `app.py:51`: `from t12_writer import ...` → `from analyzer_rr_writer import ...`.
- Updated cross-reference in `t12_normalizer_writer.py` docstring (the disambiguation note that referenced `t12_writer.py`).
- Updated live doc references: `CLAUDE.md` (Track 2 Code list — also corrected a separate pre-existing bug where `t12_writer.py` was wrongly listed under Track 2 even though it's RR-side; gotcha table; example line), `README.md` (project layout — also corrected a separate pre-existing bug where `t12_writer.py` was described as "T12 → Analyzer paste (T12 Input sheet)" which was the wrong file's role), `SPEC-RR.md` (file inventory entry), `SPEC-T12.md` (3 references: file inventory description, "future rename" deferred note now resolved, "same pattern as" cross-reference).
- **Did NOT change:** historical CHANGELOG-RR.md / CHANGELOG-T12.md / older journal entries — those are records of what shipped at past versions; renaming would falsify history.
- **Did NOT change:** the `T12CapacityError` exception name. Preserved to keep the rename surgical. Could be renamed to `AnalyzerRRCapacityError` in a follow-up — surface area is just `app.py:51` (the import) and the class definition. Documented as a follow-up in CLAUDE.md and in the new file's docstring.
- **Did NOT change:** `t12_translator.py`. Companion Track 1 file — translates Condensed_RR vocabulary into Analyzer data-validation vocabulary. Same renaming logic would apply (`analyzer_rr_translator.py`), but the user only asked for the writer; flagged as a candidate follow-up in CLAUDE.md / SPEC-T12.md.

Verification: re-ran the Homestead smoke test (the same `_smoke.py` harness pattern from the v1.14.0 ship) after the rename — 176 rows out, IL=62/AL=62/MC=52, 0 unmapped. App imports clean, no behavioral change.

### Files changed

- `t12_writer.py` → `analyzer_rr_writer.py` (rename via `git mv`, plus docstring update)
- `app.py` — import path updated
- `t12_normalizer_writer.py` — docstring cross-reference updated
- `CLAUDE.md` — "Module naming gotcha" table updated; pre-existing Track 2 Code list bug fixed
- `README.md` — project layout updated; pre-existing module-role-comment bug fixed
- `SPEC-RR.md` — file inventory entry updated
- `SPEC-T12.md` — 3 references updated; "future rename" deferred note now resolved
- `journal.md` — this entry

### Carry-forwards still open

- **Hold/Prelease distinction** for `Vacant w/ Prelease` rows. Currently both VACANT and Vacant w/ Prelease → Vacant. Defensible as-is.
- **Substrate version-detection cosmetic bug.** `_detect_substrate_version()` returns `v0.1.5` for any v0.1.5+ substrate because newer substrates don't add new Labels in Description_Map column B. Worth widening the marker list when the bundle next changes Label vocabulary.
- **`t12_translator.py` → `analyzer_rr_translator.py` rename** — companion to the writer rename done here. Wait for a triggering reason.
- **`T12CapacityError` → `AnalyzerRRCapacityError`** — exception class rename for consistency with the file rename done here. Surface is one import + one class definition. Wait for a triggering reason.
- **Track 3 — Analytical coverage** (Branch 3 per `OPTIMIZATION-DECISIONS.md`).
- **Track 3 — Handoff readiness** (Branch 2, after Branch 3).

---

## 2026-05-08 — RR v1.14.0 (Homestead-style broker-condensed format)

**Started as:** Track 1 chat. User flagged that the Homestead Village Pensacola rent roll parsed incompletely — they shared the source RR (`2026-04-24 Homestead Village Rent Roll v2.xlsx`) and the populated Analyzer (`Analyzer with 2026-04-24 Homestead Village Rent Roll v2 + March 2026 T12 2026-04-24.xlsx`) and asked for a diagnosis.

**Stayed as:** A Track 1 chat throughout. Worked in git worktree `claude/infallible-grothendieck-b542dd`. T12-side files (`t12_normalizer.py`, `t12_writer.py`, T12 sections of `app.py`, the Analyzer substrate, migration scripts) untouched.

### Frame

Diagnosed the incomplete parse first. Loaded both files with openpyxl, dumped the source headers (row 6: `Unit ID`, `Cottage`, `Unit`, `Area`, `Category`, `BR/BA`, `Market / Mo 2026`, `Market PSF`, `Actual / Mo 2026`, `Actual PSF`, `Status`, `Resident`, ...) and walked the populated `Rent Roll Input` sheet (136 rows out of expected 176; columns 3-8 (Sq Ft, Care Type, Apt Type, Market, Actual) blank for every row; every Status read `Occupied`). Cross-checked against `normalizer.py` FIELD_PATTERNS — none of Homestead's column headers matched any pattern. The 40-unit gap traced to `_row_is_self_contained_unit()` requiring a resident name; truly-vacant Homestead rows (no resident) were silently dropped. The "everything is Occupied" came from the inference fallback at `normalizer.py:608-611` when no `bed_status` column is mapped.

User chose path **(a) extend FIELD_PATTERNS** + **(b) pre-cleaner pass for the format-specific chrome** + RR version bump + MD updates.

### Implementation calls made

- **First-wins build loop preserved.** Already in the code (`normalizer.py:507`: `if field and field not in field_map`). Adding `^unit\s*id$` as the first `unit` pattern lets Homestead's unique `Unit ID` win over the generic `^unit$` pattern, and the per-cottage `Unit` column falls through unmapped — keeping `unit_id` set to the unique `A1`/`B1`/etc. value rather than overwriting it with the per-cottage `1`. No refactor needed.
- **Bed_status as a self-contained signal**, gated on recognized status keywords. The original `_row_is_self_contained_unit()` required a resident name. Adding bed_status unconditionally would emit garbage for the Homestead end-of-sheet pricing-summary table where the Status column happens to hold "Monthly Total" or numeric subtotals. The keyword gate (`occupied`, `vacant`, `notice`, `hold`, `ntv`, etc. — same vocabulary as `mappings.py` `DEFAULT_BED_STATUS`) accepts real status values and rejects garbage.
- **Pre-cleaner cut at `avg area`.** The Homestead pricing-summary block follows the unit list with a fresh `Unit ID` / `# Units` / `Avg Area` header at row 190, then per-cottage subtotals (`A`, `B`, `H`, `G`, `V`), then `IL Subtotal` / `AL Subtotal` / `MC Subtotal` / `Total` / `Double-Check`. Added `il subtotal` / `al subtotal` / `mc subtotal` / `double-check` / `avg area` to `_TOTALS_SIGNALS`. The first match (`avg area` on row 190) cuts the entire block in one shot — no need for state-tracking logic across the per-cottage rows that fall between the second header and the first subtotal.
- **NTV → Notice rule** ordered BEFORE `\boccupied\b` in `DEFAULT_BED_STATUS`. Homestead reports `Occ w/ NTV` for residents on notice; without the explicit rule it would have fallen through unmapped (the substring `Occ` doesn't match `\boccupied\b` because of the word boundary). Mapped to `Notice` because the bed-status taxonomy collapses "occupied but on notice" to `Notice`.
- **Did not add a Hold/Prelease distinction.** Source has both `VACANT` and `Vacant w/ Prelease`. Both currently resolve to `Vacant` via `\bvacant\b`. The Hold semantic (preleased / reserved) is defensible but the user didn't ask for it; keeping behavior conservative. Easy follow-up if needed.

### What shipped

**Parser (RR v1.13.0 → v1.14.0)** — `normalizer.py`:
- FIELD_PATTERNS additions for Homestead headers (unit, apt_type, market_rate, actual_rate, bed_status, sqft, care_type).
- `_row_is_self_contained_unit()` accepts `bed_status` as a second signal alongside resident name, gated on the value matching a recognized status keyword.

**Mappings** — `mappings.py`:
- `\bstu\b` → `Studio` (DEFAULT_APT_TYPE).
- `\bntv\b` → `Notice` (DEFAULT_BED_STATUS, ordered before `\boccupied\b`).

**Pre-cleaner** — `pre_cleaner.py`:
- `errors!!!` and `current date:` added to `_BANNER_PREFIXES` (Homestead row-2 chrome).
- `il subtotal` / `al subtotal` / `mc subtotal` / `double-check` / `avg area` added to `_TOTALS_SIGNALS` (Homestead end-of-sheet pricing-summary block).

**App** — `app.py`:
- Version bump RR v1.13.0 → v1.14.0; `RR_LAST_UPDATED` 2026-05-07 → 2026-05-08.

### Verification

Spot-built a throwaway harness (`_verify_homestead.py`, deleted after use — not part of repo) that called `normalize_rent_roll()` on the Homestead source and dumped row count, status/care-type/apt-type breakdowns, sample rows, and unmapped-value summary. Final state: **176 rows out (matches source unit count exactly), Care Type IL=62 / AL=62 / MC=52 (matches source pricing-summary subtotals exactly), Status 128 Occupied + 43 Vacant + 5 Notice = 176, zero unmapped across all five tracked categories**. Spot-checked rows A1, A4 (preleased vacant — resident `Q Puckett`, status `Vacant`), A5 (true vacant, no resident), A7, V9, E1, E3 (NTV → Notice), K20 against the source — all match.

No automated regression coverage in the repo (`Sample Files/` is gitignored, no `tests/` dir). Salem / Briar Glen / Oaks at Beaufort were not re-run; the new patterns shouldn't intersect their header vocabulary and the bed_status fallback only kicks in when no resident signal is present (Briar Glen's `*Vacant` resident marker continues to flow through the existing resident-path with the inline status strip at lines 602-607). Worth a smoke test on the next run of any Salem/Briar/Beaufort file.

### Doc / metadata updates

- `CHANGELOG-RR.md` — new `[1.14.0]` entry at top.
- `SPEC-RR.md` — `Current version` line, version-stream summary, "Self-contained row detection" section (now mentions bed_status alternate signal), Verified formats table (added Homestead Pensacola row).
- `CLAUDE.md` — `Last updated`, RR current version (v1.12.0 → v1.14.0; the doc was stale on this — v1.13.0 was on main from the 2026-05-07 Memory Care work), removed the "hanging branch" carry-forward note about `claude/mystifying-wu-33a0f6` (commit `667fd67` IS on main per `git log`).
- `journal.md` — this entry.

### Carry-forwards

- **Smoke-test Salem / Briar Glen / Oaks at Beaufort** on the next run of any of those files. No regression suspected, but the bed_status self-contained signal is the kind of change worth a real-fixture sanity check.
- **`README.md`** still has the RR-only framing and doesn't mention the Homestead format. Same low-pri carry-forward as flagged in CLAUDE.md.
- **Hold/Prelease distinction** for `Vacant w/ Prelease` rows. Currently resolves to `Vacant`. Defensible but a `Hold` mapping would be more semantically precise. User didn't ask; leaving for follow-up.

### Commits produced

(To be filled in at commit time.)

---

## 2026-05-08 — T12 v0.2.0 + Substrate v0.1.7 (BrokerFinancialSummaryFormat + Cluster B + R102 close-out)

**Started as:** Track 2 chat with handoff doc `HANDOFF-T12-v0.2.0.md` specifying five phases: parser code, verification harness, app.py wiring, substrate migration, docs. Three carry-forwards rolled in together — `BrokerFinancialSummaryFormat` (high-pri from journal 2026-05-06 + 2026-05-07), Cluster B sign/partial-year (medium-pri from D-12), and `T12 Analytics!R102` lease formula (medium-pri from F-2 / A-5).

**Stayed as:** A T12 chat throughout. Worked in git worktree `claude/flamboyant-golick-7205bb`. RR-side files (`normalizer.py`, `mappings.py`, `pre_cleaner.py`, `period_date.py`, `reports.py`, `writer.py`, `mapping_template.xlsx`) untouched.

### Frame

Five phases per handoff. Loaded existing parser, app, migration template, optimization decisions, both changelogs. Spent the first part grounding broker-format file structure (Homestead Summary's 39-datetime row 4 across CY/T12/T6M/T2M/T1M sections vs March_2026's clean 12 contiguous monthlies) and inspecting the populated_analyzer for the Description_Map vocabulary precedent that v0.1.5 Option-C work established.

The handoff was tightly specified — most design decisions were locked. Main implementation calls made during the session:
- **"Rightmost contiguous monotonic monthly run" algorithm** for broker column selection — the handoff's "rightmost 12 datetimes" rule didn't survive Homestead Summary's repeated period-end dates (Mar 2026 appears at cols 39, 40, 49, 50, 56, 59, 60). Reformulated to "rightmost contiguous run where each cell is exactly 1 col AND 1 month after the previous." Picks AB:AM cleanly.
- **Always-prefix banner rule** with subtotal-pop and top-level-Revenues no-prefix exception. After studying the populated_analyzer's mixed prefixed/unprefixed entries, settled on: parser always prefixes when current banner is a sub-banner of the top-level "Revenues" banner; pops back on Subtotal,; and does not prefix when current_banner == top_banner. Matches populated_analyzer's structure (siblings like `Concessions`, `Respite Revenue`, `Move-In Fees` come out unprefixed under top-level Revenues; sub-section rows like `Direct Care | Payroll - Wages` carry the banner).
- **Post-P&L cutoff**. Initial parser run produced 132 rows including Wages Analysis ratios and Non-Operating items. Added `TERMINATE_BANNER_RE = "non-?operating|wages\s+analysis|payroll\s+summary"` to stop extraction when those banners hit. Drops to 101 rows, matching the populated_analyzer's count exactly.
- **Sign-warning narrowing**. First implementation flagged `Bad Debt` and `Vacancy` / `L2L` because those keywords are sometimes negative-sign-convention. But broker format reports Bad Debt as a positive expense ($37,329.31), and substrate v0.1.4's Monthly Trending R10/R11 already handles either-sign Vacancy/L2L. Reduced guard set to just `CONCESSION` (suffix-aware to avoid false positives from banners like `Management Fee & Bad Debt`). All four fixtures emit zero sign warnings.
- **Cluster B annualization API**. `parse_t12(..., annualize_partial_year=False)` keyword. App owns the toggle (sidebar checkbox), parser does the math. `T12ParseResult.was_annualized` flag for UI labeling.

### What shipped

**Parser (T12 v0.1.1 → v0.2.0)** — `t12_normalizer.py`:

- `BrokerFinancialSummaryFormat` class (~150 lines including its dedicated rightmost-monthly-run helper). Detects `Historical Performance` at A4. `extract()` walks body with a banner-stack, applies pre-financial preamble drop (skip until Revenues banner), post-P&L cutoff (stop at Non-Operating / Wages Analysis / Payroll Summary), drop rules (no-$, grand-total now extended with `Subtotal,`, explicit-list now including `NOI on Statement` / `Check`). Banner prefix applied conditionally (no-prefix when at top-level).
- `_check_sign_convention()`, `_count_populated_months()`, `_annualize_rows()` — Cluster B helpers.
- `T12ParseResult` extended with `sign_warnings`, `populated_months`, `was_annualized` (default-valued, backwards-compatible).
- `parse_t12()` accepts `annualize_partial_year: bool = False`.
- `GRAND_TOTAL_PREFIXES` += `SUBTOTAL,` / `SUBTOTAL `; `EXPLICIT_DROP_LIST` += `NOI on Statement` / `Check`.

**App (RR v1.13.0, T12 v0.1.1 → v0.2.0)** — `app.py`:

- `T12_VERSION = "0.2.0"`, `T12_LAST_UPDATED = "2026-05-08"`.
- Sidebar: "Annualize partial-year T12" checkbox (disabled until raw T12 uploaded). Help text on T12 uploader extended to mention Broker Financial Summary.
- `parse_t12()` call wires the `annualize_partial_year` kwarg.
- T12 status panel: partial-year warning when `populated_months < 12` (different message based on whether annualized); sign-warning loop displays each `T12ParseResult.sign_warnings` entry. Period labels tolerate partial-year padded-empty entries by skipping them in display.
- `UnknownT12FormatError` message extended to include broker format in supported-list.

**Verification harness** — `tools/verify_t12_v020.py`:

Parser-side end-to-end checks for all four fixtures. Asserts: format detection, GL row count, populated months, sign warnings, source $ (deterministic ±$0.01), implied NOI for broker (revenue-keyword subset minus expense subset). Prints a per-fixture report and exits 0/1. ASCII status markers (Windows console default cp1252 doesn't render ✓/✗). Substrate-level EGI / EBITDARM unchanged from v0.1.6 — workbook formulas untouched, source $ matching v0.1.1 figures implies downstream values still hold; manual interactive check via Streamlit covers this.

**Substrate (v0.1.6 → v0.1.7)** — `tools/migration/migrate_to_v017.py`:

Five operations, idempotent:
1. T12 Analytics E102 = `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`; F102 = `=E102` — closes A-5 / R102 carry-forward from v0.1.6.
2. Sweep 636 SUMIFS in T12 Raw Data from `T12_Calc!$X$1:$X$501` → `$X$1:$X$500` (cosmetic, T12_Calc has 500 data rows).
3. Workbook Health row 30 (formerly blank gutter): V8 partial-year T12 row, `=COUNTA('T12 Input'!C11:N11)` paired with ✓/⚠.
4. Append 99 prefixed Description_Map entries (Homestead vocabulary) — all derive their Label from suffix-lookups against the populated_analyzer's v0.1.5 Option-C work, mapping mechanically to the existing 54-Label closed vocabulary. Idempotent: skips entries whose key already exists.
5. Stamp `Cover!B8` and all 13 sheets' `AZ4` to `v0.1.7`.

7 verification checks at the end. Both Homestead and March_2026 fixtures parse with **0 UNMATCHED** at v0.1.7. Description_Map row count grows 311 → 410.

**Docs** — SPEC-T12.md (current-version line, Verified formats table, Template substrate v0.1.7 entry, new Cluster B subsection in Parser data flow), CHANGELOG-T12.md ([0.2.0] + [Substrate template v0.1.7] entries at top), CLAUDE.md (version lines, last-updated date, "Closed in this session" carry-forward section), this journal entry.

### Discovered facts worth carrying forward

- **Homestead Summary has 39 datetime cells in row 4**, distributed across multiple time-window sections (CY 2022-2025 + T12 monthly + T6M monthly + T2M + T1M) plus their period-end "Ending" total columns. The "rightmost 12 datetime cells" naive interpretation includes duplicate Mar 2026 cells from the totals/annualized columns. Right algorithm is **"rightmost contiguous run where each cell is exactly 1 col AND 1 month after the previous"** — robust to multi-section dashboards.
- **Broker T12 published NOI is reported twice in the source**: once as `Total Net Operating Income` (caught by `TOTAL ` drop prefix) and once as `NOI on Statement` (added to EXPLICIT_DROP_LIST). Without the latter the parser would emit a synthetic GL row at the broker's NOI value, polluting downstream aggregation.
- **The populated_analyzer's mixed prefixed/unprefixed Description_Map** (17 prefixed + 42 unprefixed Homestead entries from Option C) reflects a Label-aware judgment: prefix only when banner determines Label (`Payroll - Wages` → 8 different Labels by department). The parser can't make that judgment without descmap input. Resolution: parser always prefixes for broker; substrate carries prefixed entries for everything (mechanical doubling for "same Label regardless of banner" descriptions). All 99 Phase-4 entries derived from suffix lookups are mechanical and lossless.
- **Workdir mistake worth noting**: my Edit/Write/Bash calls used absolute paths to the main repo root instead of the worktree (`...\.claude\worktrees\flamboyant-golick-7205bb\...`). Caught mid-Phase 4. Migrated work back into the worktree via `cp` + `git checkout --` revert on main. **Lesson: always prefer relative paths (or paths rooted at the system-message-stated worktree directory) when operating in a worktree, even when absolute paths look identical to the parent repo.**

### Process lessons from this session

1. **Reading the populated_analyzer first paid off.** Before writing the parser, I inspected the destination state — what descriptions were prefixed, what was unprefixed, what UNMATCHED count was achievable, and what Label vocabulary already existed. That investigation determined the parser's banner-prefix rule, the post-P&L cutoff, and the Phase 4 substrate scope. Without it, the parser would have produced 132 rows with confusingly-prefixed siblings, and Phase 4 substrate would have been guesswork.
2. **Smoke-testing after every parser change kept iterations short.** First run produced 132 GL rows (with `Wages Analysis` ratios + `NOI on Statement`). Inspecting the source and populated_analyzer at the same time made the cutoff design self-evident. Second run produced 101 — the populated_analyzer's count to the row.
3. **The verification harness paid for itself**. Running it after copying files into the worktree confirmed nothing got lost in transit. Running it after migration confirmed 0 UNMATCHED on all four fixtures, end-to-end. Cheap to write, expensive to skip.
4. **Per the v0.1.6 retrospective, idempotent migration verification blocks earn their weight.** `migrate_to_v017.py`'s 7-check verifier ran clean on first try, but the value of having it isn't catching bugs you don't introduce — it's establishing that the destination state is what the script claims, in 7 boolean assertions printed inline with the migration log. Worth more than its line count every time the substrate ships.

### Commits this session

Shipped via PR [#1](https://github.com/ErikJ-Stack/rent-roll-normalizer/pull/1) (merged 2026-05-08 19:48 UTC, merge commit `03f9df1`):

- `555f4e4` — `T12 v0.1.1 -> v0.2.0: BrokerFinancialSummaryFormat + Cluster B` *(parser code + tools/verify_t12_v020.py)*
- `0649ae5` — `app.py: T12 v0.2.0 wiring (partial-year toggle, sign warnings, broker)` *(app.py only — no RR Track 1 code touched; RR_VERSION unchanged at 1.13.0)*
- `36e1659` — `Substrate v0.1.6 -> v0.1.7: R102 lease, $501 sweep, Homestead descmap, V8 row` *(migrate_to_v017.py + bundled Analyzer regen + docs)*
- `6037671` — `verify_t12_v020: switch fixture paths to repo-root Sample Files/` *(post-PR-open follow-up after the user staged Sample Files; .gitignore updated)*

Three-commit split (parser / app / substrate+docs) plus the late-arriving Sample Files path swap. Each commit is a coherent unit, picked over the handoff's "single commit" alternative for cleaner per-track separation in main's history.

### Files at session end

- New: `tools/migration/migrate_to_v017.py`
- New: `tools/verify_t12_v020.py`
- New convention: `Sample Files/` directory at repo root for local-only T12 fixtures (gitignored — files contain real property financials and must not be published). The four fixtures: `Salem Road T-12 1.31.26.xlsx`, `Briar Glen T12 P&L Statement_2025.12.xlsx`, `2026-03 Homestead Village Pensacola Financial Summary.xlsx`, `Homestead - March 2026 T12.xlsx`.
- Updated: `.gitignore` (added `Sample Files/`)
- Updated: `t12_normalizer.py` (BrokerFinancialSummaryFormat + Cluster B helpers + parse_t12 signature)
- Updated: `app.py` (T12_VERSION 0.2.0; sidebar annualize checkbox; T12 status panel partial-year + sign warnings)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (substrate v0.1.7, regenerated via `migrate_to_v017.py`; Description_Map 311 → 410 entries)
- Updated: `SPEC-T12.md` (current-version line, Verified formats, Template substrate v0.1.7, Cluster B subsection)
- Updated: `CHANGELOG-T12.md` ([0.2.0] + [Substrate template v0.1.7] entries at top)
- Updated: `CLAUDE.md` (version lines, last-updated, "Closed 2026-05-08" carry-forward section)
- Updated: `journal.md` (this entry)
- Untouched: `SPEC-RR.md`, `CHANGELOG-RR.md`, `normalizer.py`, `mappings.py`, `pre_cleaner.py`, `period_date.py`, `reports.py`, `writer.py`, `mapping_template.xlsx`, `README.md`

### Known follow-ups for future chats

- **Branch 3 (Analytical coverage)** — sensitivities, scenarios, debt + returns, IL/AL/MC expense splits. Per OPTIMIZATION-DECISIONS.md sequencing. **Track 3 chat.** Largest open carry-forward.
- **Branch 2 (Handoff readiness)** — pre-export gate, UW Export sheet (values-only mirror), metadata header, source trail. **Track 3 chat, after Branch 3.**
- **README.md** — still RR-only framing per prior journal notes. Independent task; bumps about every other commit on the deferred list.
- **Substrate version-detection cosmetic**. App's `_detect_substrate_version()` returns `v0.1.5` for any v0.1.5+ bundle (its marker is the `2nd Person Revenue` Label that v0.1.5 added; v0.1.6 / v0.1.7 don't add Labels). Cosmetic; widen the marker list when the next bundle change adds a Label.
- **Format #4 (RealPage / AppFolio / etc.)** — when sample arrives. Format-registry pattern keeps this small.
- **`claude/mystifying-wu-33a0f6` branch** — Memory Care detection (Oaks at Beaufort) commit `667fd67` parked there; either close out or merge. Independent of this session.

### Verified end-to-end at session close

| Fixture | Format | GL rows | UNMATCHED | Months | Reconciliation |
| --- | --- | ---: | ---: | ---: | --- |
| Salem | Yardi (Income to Budget) | 73 | 0 | 12 | source = $4,249,047.98 (matches v0.1.1) |
| Briar Glen | MRI R12MINCS | 91 | 0 | 12 | source = $8,306,657.64 (matches v0.1.0) |
| Homestead Pensacola | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 (broker NOI to the penny) |
| March 2026 | Broker Financial Summary | 101 | 0 | 12 | implied NOI = $1,411,323.58 |

Migration `migrate_to_v017.py` ran clean on `ALF_Financial_Analyzer_Only.xlsx` (v0.1.6 → v0.1.7) — all 7 verification checks pass, idempotent re-run is a no-op. Description_Map row count: 311 → 410.

---

## 2026-05-07 — T12 Substrate v0.1.6 (Analyzer optimization, Branches 1+4)

**Started as:** "Optimize the analyzer before it goes into the full underwriting sheet." Read SPEC-RR, SPEC-T12, both changelogs, README, and the prior journal entry. Walked the bundled `ALF_Financial_Analyzer_Only.xlsx` to ground the work.

**Stayed as:** A T12 chat throughout. The architectural constraint set up front ("additive only — new sheets / sections / cells / named ranges OK; existing aggregators untouched") held cleanly. RR-side files not touched.

### Frame

Drew a 4-branch optimization mind map: correctness, handoff readiness, analytical coverage, substrate. User picked Branches 1 + 4 first (foundation), then 3 (depth), then 2 (handoff). Spun up `OPTIMIZATION-DECISIONS.md` in the chat as the running decisions log per "if context is going to thin, recommend an MD" preference. Net 14 decisions logged, 8 "discovered facts" sections from grounding investigation.

The journal's "one track at a time" lesson from 2026-05-06 informed an explicit boundary call mid-design: Cluster B (sign guards + partial-year T12) was identified as code-side work and deferred to a future Track 2 chat (D-12) rather than crossing tracks within this session.

### What shipped

**Substrate v0.1.5 → v0.1.6.** All workbook-side. Built and validated end-to-end inside this chat:

- **`tools/migration/migrate_to_v016.py`** — idempotent migration script, ~500 lines. Operates in order: add Cover (front) → Cluster A formula fixes → add Workbook Health (back, hidden) → populate AZ1:AZ5 anchors on all 13 sheets → add 5 named ranges → wire `T12 Analytics!B2` to `=Property_Name` → add 5 cell comments → run 11 verification checks. Smoke-tested on the actual bundled Analyzer, then LibreOffice-recalc'd to confirm 0 formula errors across all 13 sheets.

- **Cluster A — Correctness fixes (4 ships):**
  - `Rent Roll Recon!H20` chunked-literals rewrite. The `_xlfn._LONGTEXT` artifact was the headline bug — caused by Excel's per-literal 255-char cap blowing up the 5-item investigation lists in cases 3 and 4 of the diagnostic. New formula has 6 literals max-255-chars, joined with `&`. Total formula 1068 chars; round-trips clean through openpyxl with no `_xlfn._LONGTEXT` and resolves to the right diagnostic message on a populated workbook.
  - `UW Output!R29` (Bonus wages) sibling-pattern fill against `T12 Analytics!E64`/`F64`.
  - `UW Output!R57` (Bad debt expense) sibling-pattern fill against `T12 Analytics!E98`/`F98`.
  - `UW Output!R61` (Lease / ground lease) — paper-over fill per D-04. Points at `T12 Analytics!E102`/`F102` even though those still return `=0`. Indent fixed (0.0 → 1.0) to match siblings R60 / R62.

- **Cluster C — Workbook Health (1 new sheet):**
  - Hidden, last position. Three sections: Workbook Map (formula-driven, 13 rows pulling from per-sheet `AZ1:AZ5`), Validation (7 live $ checks with ✓/⚠ status, ±$1 leakage tolerance per D-08), Diagnostics (capacity utilization from existing UW Output cells, 3 version pills from Cover, last-open timestamp).

- **Cluster D — Cover + supporting work:**
  - Cover sheet (first tab, visible). 4 blocks: Property / Versions / Links / About. Property name at B5 is the canonical home of the new `Property_Name` named range.
  - Anchor cells `AZ1:AZ5` populated on all 13 sheets — predictable location, verified empty pre-migration on every existing sheet (rightmost data column on any sheet is U; AZ is column 52).
  - 5 named ranges: `RR_Period_Date`, `T12_Period_Date`, `RR_Input_Data`, `T12_Input_Data`, `Property_Name`. Joins existing `DescMap_Description` and `DescMap_Label`.
  - `T12 Analytics!B2` (was empty) wired to `=Property_Name`.
  - 5 light cell comments on the hardest-to-decode formulas: `Monthly Trending!B5` (T12 rollup INDEX/MATCH pattern), `T12 Analytics!E37` (GPR), `T12 Analytics!E52` (EGI), `T12 Analytics!E110` (EBITDAR after mgmt fee), `Rent Roll Recon!H20` (RR↔T12 gap diagnostic).

### Discovered facts worth carrying forward

Logged in `OPTIMIZATION-DECISIONS.md` as F-1 through F-8. Highlights:

- **`Rent Roll Recon!H20 _xlfn._LONGTEXT` root cause** (F-1) — Excel's per-literal 255-char cap, not a missing function or anything more exotic. The fix is mechanical once you see it.
- **UW Output R65 was misclassified as a bug initially** (D-03) — turned out to be a visual section separator (bold + navy `FF2F5597` fill, identical to R69). Correct call after inspecting the formatting was to drop it from the bug list, not invent an NOI definition.
- **The bundled Analyzer was missing the Cover sheet** that `SPEC-RR.md` lists as part of the expected structure (F-3). Spec was right; bundle had drifted. Now fixed.
- **`T12 Analytics!R102` is still `=0`** (F-2 / A-5) — was supposed to get an INDEX/MATCH per the v0.1.4 substrate plan, but never landed. Logged as deferred for v0.1.7+; it's the only reason `UW Output!R61 Lease` will display `$0` after this migration.

### Process lessons from this session

1. **Showing trumps explaining when a question lands wrong.** When the user asked "where is H20?" instead of picking a fix path, the right move was to draw the spreadsheet grid showing exactly which cell was broken and what its four output cases are, before re-asking. Worked. Also worth doing the same when "what's a named range?" landed — minimal Excel literacy assumption is safer than maximal.
2. **Verifying anchor location empirically before committing the convention.** The `AZ1:AZ5` choice was checked against every sheet's `max_column` before being proposed; otherwise it could have collided with one of the analytical sheets that legitimately uses high column letters.
3. **The migration script's verification block is worth its weight.** 11 boolean checks at the end of `migrate_to_v016.py` caught the AZ5-empty-string-renders-as-0 issue immediately on first run — fix took one minute. Without the verification, that would have shown up as a cosmetic bug an analyst spotted later.

### Commits this session

To produce after pulling the migration script and docs into the repo:

- `<hash>` — `Substrate v0.1.5 -> v0.1.6: Cover + Workbook Health, named ranges, H20 fix, UW Output gaps, anchor cells, light comments`

(One commit covers everything. Alternative: split into "Cluster A bug fixes" + "Clusters C/D new sheets and convention" + "Cell comments and named ranges" if granular history is preferred — three commits, same diff total.)

### Files at session end

- New: `tools/migration/migrate_to_v016.py`
- New: `OPTIMIZATION-DECISIONS.md` (carry-forward decision log; lives at repo root)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (substrate v0.1.6, regenerated by running the migration on the v0.1.5 file). **Filename unchanged** — `app.py` v1.12.0 references this exact path in `_load_analyzer()`. The chat-output `analyzer_v016.xlsx` was a within-chat naming artifact only; final filename in the repo is `ALF_Financial_Analyzer_Only.xlsx`.
- Updated: `SPEC-T12.md` (current-version bump + new v0.1.6 entry in Template substrate section)
- Updated: `CHANGELOG-T12.md` (new `[Substrate template v0.1.6]` entry at top)
- Untouched: `SPEC-RR.md`, `CHANGELOG-RR.md`, `app.py`, `t12_normalizer.py`, `README.md`

### Known follow-ups for future chats

- **Cluster B (Track 2 chat)** — sign-convention guards + partial-year T12 handling. Code-side work in `t12_normalizer.py` and `app.py`. Should reference `OPTIMIZATION-DECISIONS.md` D-12 boundary as the carry-forward pointer.
- **Branch 3 (Analytical coverage)** — sensitivities, scenarios, debt/returns, IL/AL/MC expense splits. The next optimization round per the mind map sequencing.
- **Branch 2 (Handoff readiness)** — designed last, since it depends on what Branch 3 adds to UW Output.
- **`T12 Analytics!R102` lease formula fix** (substrate v0.1.7) — small, scoped, eligible to bundle with whatever other aggregator work earns its keep next.
- **README.md** — still RR-only framing per the prior journal note. Independent task.

---

## 2026-05-06 — T12 Substrate v0.1.5 (Homestead Pensacola) + RR v1.12.0 (scope drift)

**Started as:** T12 chat. Read SPEC-T12.md + CHANGELOG-T12.md. Task: process the Homestead Pensacola broker financial summary file as a one-off.

**Ended as:** A cross-track session that also produced an RR v1.12.0 release.

**Scope discipline note:** This was a T12 chat. The RR-side work that landed mid-session (`app.py` v1.12.0, `CHANGELOG-RR.md`, `SPEC-RR.md` rewrite) was scope creep — should have been a separate RR chat per the "one track at a time" principle in `SPEC-T12.md`. The inflection point was the user's question about default-vs-uploaded Analyzer behavior in the app, which is RR territory. Should have been flagged with "this is RR scope — fresh chat, or proceed knowing we're crossing tracks?" and wasn't. After this session, `SPEC-T12.md` got a new line in the maintenance protocol making the rule explicit: T12 chats stop and confirm before touching RR files.

### What shipped

**T12 work (in scope):**

- **Homestead Pensacola broker file** (`2026-03_Homestead_Village_Pensacola_Financial_Summary.xlsx`) processed via Option C — one-off paste validation now, with v0.2.0 to ship a `BrokerFinancialSummaryFormat` class once mapping logic is proven.
- **60 new Description_Map entries** validated against Homestead. 21 are prefixed (`[Section] | [Description]` for ambiguous descriptions like `Payroll - Wages` which appears in 8 different departments). Three Second Persons rows initially mapped to Base rent — IL/AL/MC.
- **Substrate template v0.1.5** — added new revenue Label `2nd Person Revenue` so per-bed base rate calculations (Base rent ÷ ADC) stay clean. Inserted as a new row in `Monthly Trending` (R19) and `T12 Raw Data` (R15), with the EGI formula at the post-shift R21 rewritten to include the new R19 in the sum without disturbing R8 (Total base rent). Closed Label vocabulary grows from 54 → 55.
- **`tools/migration/migrate_to_v015.py`** — idempotent migration script. Three openpyxl quirks debugged during build: (1) `insert_rows()` shifts cells but not formula text — required full-workbook regex sweep across 833 formulas; (2) regex lookbehind originally excluded colons, breaking range endpoint refs like `F15:Q15`; (3) `insert_rows()` doesn't shift merged-cell range definitions, and using `unmerge_cells()` to fix it wipes displaced cell content — solution: `mr.shift(row_shift=delta)` to mutate bounds in-place.
- **End-to-end verification** on Homestead Pensacola: GL rows 101 / UNMATCHED 0 / Source $→Operating $ leakage $0.00 / EBITDAR $1,411,323.58 = broker NOI to the penny. R8 Total base rent $6,951,136.46 (clean, no Second Persons). R19 2nd Person Revenue $32,220.49 (NEW, isolated).
- **CHANGELOG-T12.md `[Substrate template v0.1.5]`** entry added documenting the change, the three openpyxl quirks, and the verification numbers.
- **SPEC-T12.md** updated: current version line bumped to "Template substrate at v0.1.5", v0.1.5 added to the Template substrate section.

**RR work (out of scope for a T12 chat — should have been a separate session):**

- **`app.py` v1.11.0 → v1.12.0**:
  - Bundled `ALF_Financial_Analyzer_Only.xlsx` loaded silently as default destination workbook (was: required upload)
  - "Advanced — override Analyzer template" expander at sidebar bottom for session-only overrides
  - Sidebar reorganized: Inputs (Rent Roll → Period Date → Raw T12) → Property Defaults → Optional → Output → Advanced
  - T12 parsing no longer requires uploaded Analyzer (bundled descmap is canonical)
  - Combined download produces populated Analyzer from RR alone (T12 optional)
  - Bug fix: T12 status panel had duplicate `tc.metric()` calls — first month metric was being overwritten by last month metric. 4-col → 5-col layout, all five metrics now display.
  - New helpers: `_detect_substrate_version()`, `_load_analyzer()`
- **`CHANGELOG.md` → `CHANGELOG-RR.md`** (rename via `git mv` for symmetry with `CHANGELOG-T12.md`)
- **`SPEC.md` → `SPEC-RR.md`** (rename + full content rewrite to bring it from v1.9.0 state up to v1.12.0 + Analyzer-source section + versioning convention guidance + doc rename history)
- **`CHANGELOG-RR.md` `[1.12.0]`** entry added documenting the RR v1.12.0 changes
- **`CHANGELOG-RR.md` `[T12 Normalizer cross-reference]`** entry added pointing readers to `CHANGELOG-T12.md` for the parallel T12 stream that landed during the v1.10.0–v1.12.0 window

### Commits produced this session

- `18f55bc` — `Substrate v0.1.4 -> v0.1.5: add '2nd Person Revenue' Label` *(T12 — in scope)*
- `be3b134` — `Analyzer: <describe your edit in 1 line>` — User edited the bundled Analyzer's `Rent Roll Recon!B2` dropdown for Period Selection mid-chat. Commit message used the literal placeholder text from a workflow example I'd given earlier; not corrected to avoid the rebase + force-push complexity. Real description: "Minor Dropdown data change: Rent Roll Recon B2 Dropdown for Period Selection". *(Cosmetic Analyzer edit — borderline, technically substrate territory but contains zero substrate-version-affecting changes)*
- `2331b32` — `RR v1.11.0 -> v1.12.0: bundled Analyzer default, sidebar reorg, T12 panel bug fix` *(RR — out of scope for this T12 chat)*

### Files at session end

- T12 docs: `SPEC-T12.md` and `CHANGELOG-T12.md` reflect substrate v0.1.5
- RR docs: `SPEC-RR.md` and `CHANGELOG-RR.md` reflect app v1.12.0 (renamed from `SPEC.md` / `CHANGELOG.md`)
- Bundled Analyzer: `ALF_Financial_Analyzer_Only.xlsx` at substrate v0.1.5, plus the `be3b134` cosmetic dropdown edit
- Migration script: `tools/migration/migrate_to_v015.py`
- README.md: untouched (still RR-only framing — reflects pre-T12 era)

### Known follow-ups (NOT for this chat — for future sessions)

- **README.md is stale.** Still describes the project as RR-only. Doesn't mention T12 normalizer, doesn't mention the bundled Analyzer flow, doesn't link to SPEC-T12.md or CHANGELOG-T12.md. Worth a separate pass — could be a cross-cutting chat or could be split as a small RR-side update.
- **`be3b134` commit message** is the literal placeholder text. If polish matters more than chat-time-spent, fix later via interactive rebase + force-push.
- **v0.2.0 BrokerFinancialSummaryFormat class** (per Option C plan) — promote Homestead's mapping logic into `t12_normalizer.py` as a third format alongside Yardi and MRI. Separate T12 chat.
- **Pre-existing `Rent Roll Recon!H20` `#NAME?`** in populated outputs — substrate-level issue noted in CHANGELOG-T12 [0.1.0]. Not introduced this session.
- **T12 Raw Data SUMIF range** slightly extended during v0.1.5 migration — some shifted rows now reference `T12_Calc!$N$1:$N$501` instead of `$N$1:$N$500`. Harmless (T12_Calc has 500 data rows so row 501 reads empty), but cosmetically inconsistent. Worth tightening if a future migration script touches T12 Raw Data rows.

### Process lessons

1. **Stop at the boundary.** When the user shifts topic from T12 to RR (or vice versa), the right move is to ask: "We're now in [other track] territory. Fresh chat, or proceed knowing we're cross-cutting?" Continuing without flagging it produces sessions like this one that have to be retroactively split in journal entries.
2. **The `be3b134` placeholder commit** is a small symptom of the same disease — a maintenance workflow example was given conversationally, the user followed it literally, and there was no checkpoint to confirm the placeholder was meant to be replaced. Conversational examples should label placeholder text as `<REPLACE THIS>` or similar.
3. **Reading the actual repo before assuming structure** would have saved several rounds of confusion about doc filenames (`CHANGELOG.md` vs `CHANGELOG-RR.md` etc.). Default to `web_fetch` early when working with a repo, not late.

### Verified end-to-end at session close

- v0.1.5 substrate validates clean: 0 errors, 10,953 formulas
- Homestead populated Analyzer ties to broker NOI: $1,411,323.58 to the penny
- v1.12.0 app shipped to origin/main, deployed to Streamlit Cloud at https://rrnormalizer.streamlit.app/

---
