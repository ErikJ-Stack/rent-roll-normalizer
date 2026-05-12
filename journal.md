# Chat Journal — rent-roll-normalizer

A running log of substantive chat sessions on this repo. One entry per session.
Each entry captures: scope, what shipped, what drifted, and the commit(s) the
session produced. Use this for handoff between chats and for tracing why a
particular commit looks the way it does.

Newest at top.

---

## 2026-05-12 — Substrate v0.1.11 (Rent Roll Recon row 16 GPR fix)

**Started as:** Track 3 chat. User asked to "complete Track 3" referencing the open carry-forwards (Branch 2 + 3 Lows). I scoped the question (Branch 2 alone vs. bundled), got infrastructure ready (installed `gh` CLI via Homebrew on this Mac and authenticated for the first time — `gh` v2.92.0, scopes `repo, workflow, read:org, gist`, token in macOS Keychain), then user pivoted before Branch 2 design started: opened a question on the Analyzer itself — "Rent Roll Recon row 16 says Gross RR at 100% occupancy is $565k but the market rate total is $809k in Rent Roll Input."

**Stayed as:** Single Track 3 chat. The fix is workbook-only — no RR / T12 code touched.

### Diagnostic phase

Read Rent Roll Recon rows 14-22 from the bundled template Analyzer with formulas, then read the user's populated Homestead Analyzer (Dropbox path) to verify cached values + cross-check what the formulas actually compute.

Findings, row by row:

| Row | A label | H note (intent) | Formula does | Verdict |
|---|---|---|---|---|
| **16** | RR gross contracted base rent / mo | "Gross contracted rates **before concessions**" | `SUMIFS(H, period, E<>Vacant, E<>Eviction, by care)` → Actual Rate × occupied | ❌ Wrong column AND wrong filter |
| 17 | RR effective net base rent / mo (after concessions) | "Actual rate + concessions — compare to T12 collected" | `SUMIFS(H, occupied) + SUMIFS(I, occupied)` | ✅ Correct (concessions negative-signed per SPEC-RR.md L184, so `H + I` nets the discount) |
| 18 | RR effective net rent (×12) | "For direct comparison to T12 annual base rent" | `=E17*12` | ✅ |
| 19 | T12 actual base rent (annualized) | "T12 total base rent from Raw Data" | INDEX/MATCH on `T12 Raw Data!R` ("T12_Total") | ✅ |
| 20 | Gap (RR annualized − T12 actual) | conditional commentary | `=E18-E19` | ✅ |

So the only real bug was row 16. Two issues compounded:

1. **Wrong column.** Formula sums `$H` (Actual Rate) but "gross before concessions" naturally reads as `$G` (Market Rate — the asking rate, what would be charged at 100% occupancy with zero discounting).
2. **Wrong filter.** `E<>Vacant, E<>Eviction` excludes vacant units. For "100% occupancy" you'd want **all** units (vacants still have a populated Market Rate).

Cross-checks against the populated Homestead sample confirmed:
- SUM(G — Market Rate, all 176 rows) = $809,567 ← matches user's $809k expectation
- SUM(H — Actual Rate, occupied) = $565,140 ← matches what current formula returns
- Status counts: 128 Occupied + 5 Notice + 43 Vacant = 176

**Special case noted but not load-bearing:** Homestead has no concession column in source (per SPEC-RR.md L350), so on this property `Row 16 = Row 17` numerically with the old formula — the bug only manifested as the $565k vs $809k label mismatch, not as a row16/row17 discrepancy. Other operators (Salem, Beaufort) would have shown the bug as both a wrong row 16 AND a misleading row16-vs-row17 delta.

### Implementation calls made

- **Sum `$G` (Market Rate), drop status filter.** Definitive read of the H-note + the user's "100% occupancy" framing. Result aligns with Gross Potential Rent (GPR) — the standard underwriting anchor that sits above Effective Gross Rent.
- **Don't touch row 17.** With concessions negative-signed, the existing `H + I` correctly nets the discount. Filter on `E<>Vacant, E<>Eviction` keeps row 17 comparable to T12 collected. Adding extra changes here would expand blast radius for no benefit.
- **Update label + note to match new behavior.** "Contracted" was misleading once vacants are included → "Gross Potential Rent (Market × all units)." Note explicitly states what row16-vs-row17 measures (vacancy + market-vs-actual gap), so a future reader doesn't have to derive that from formulas.
- **Single migration, not bundled with Branch 2.** Atomic, easy to verify, easy to roll back. Branch 2 + the 3 Low-priority Track 3 carry-forwards remain open for future v0.1.12+.

### Verification

End-to-end against both fixtures:

1. **Template Analyzer** — `Cover!B8 = v0.1.11`, all 13 AZ4 stamped, all 9 verifier checks green. Idempotency confirmed (re-run on the migrated file = no-op).
2. **Populated Homestead Analyzer** — same 9 checks all green. Simulated SUMIFS by care type against actual data:
   - B16 IL: $167,155.63 (62 units)
   - C16 AL: $327,776.35 (62 units)
   - D16 MC: $314,635.03 (52 units)
   - **E16 = $809,567.01** ← matches user's $809k
   - E17 = $565,140.05 (unchanged from prior)
   - **Row 16 − Row 17 = $244,426.97** = clean vacancy + market-vs-actual gap

### Files at session end

- New: `tools/migration/migrate_to_v0111.py` (3 ops, 9-check verify, idempotent — gate checks both `Cover!B8` AND that B16 references `$G`)
- Updated: `ALF_Financial_Analyzer_Only.xlsx` (regenerated v0.1.11)
- Updated: `CHANGELOG-T12.md` (v0.1.11 entry at top)
- Updated: `SPEC-T12.md` (current substrate version line + v0.1.11 history entry)
- Updated: `CLAUDE.md` (last-updated, current substrate version, closed-item note, version-detection bug note widened to mention v0.1.11+ marker possibilities)
- Updated: `OPTIMIZATION-DECISIONS.md` (D-23 decision row appended)
- Updated: `journal.md` (this entry)

### Carry-forwards opened

None new. The original Branch 2 (Handoff readiness) + 3 Low-priority Track 3 items remain open per the v1.16.0 journal entry's carry-forward list.

### Process lessons

1. **The H-column note was the source of truth — and it had been right all along.** The bug existed for at least four substrate versions (v0.1.6 through v0.1.10) because nothing forced a periodic check that formulas matched their own annotations. A future audit pass over every "intent note" cell vs. its row's formula would catch this class of drift cheaply.
2. **Side-by-side template + populated-sample inspection caught the issue in one read.** The template alone can't expose this — you need to see what number the formula produces against real data and compare it to what the label/note implies. Same lesson as the v1.16.0 RR data-capture session.
3. **Single-cell substrate fixes are worth shipping atomically.** This change is smaller than every prior substrate version (3 formulas + 1 label + 1 note) but the migration script + verify-block + spec/changelog/journal updates still earned their weight: full reproducibility, idempotent re-run, immediate readable diff. The friction of doing it "properly" is low once the pattern is established.

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

Per the v0.2.0 retrospective lesson — my first `Write` of `migrate_to_v018.py` and `Edit`s of `OPTIMIZATION-DECISIONS.md` used absolute paths to the main repo (`C:\Users\erikj\Downloads\rent_roll_app\...`) instead of the worktree. Caught immediately when the first migration run failed with "file not found." Recovered via `cp` to the worktree + `git restore` on main. **Same lesson as 2026-05-08: when operating in a worktree, the system-message-provided worktree directory is the only correct root.** Re-confirming for future chats.

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
- **Workdir mistake worth noting**: my Edit/Write/Bash calls used absolute paths to the main repo (`C:\Users\erikj\Downloads\rent_roll_app\...`) instead of the worktree (`...\.claude\worktrees\flamboyant-golick-7205bb\...`). Caught mid-Phase 4. Migrated work back into the worktree via `cp` + `git checkout --` revert on main. **Lesson: always prefer relative paths (or paths rooted at the system-message-stated worktree directory) when operating in a worktree, even when absolute paths look identical to the parent repo.**

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
