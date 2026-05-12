# Analyzer Optimization — Decisions Log

> **Working doc.** Captures the design decisions made during the optimization effort kicked off 2026-05-07. Decisions graduate into `SPEC-RR.md`, `SPEC-T12.md`, or a future `SPEC-Analyzer.md` once shipped. Read top-to-bottom for the chronology; the Decision Log table is the canonical index.

**Started:** 2026-05-07
**Owner:** Erik J
**Scope:** Optimize the Analyzer substrate (`ALF_Financial_Analyzer_Only.xlsx`) before its outputs are consumed by the downstream full underwriting sheet.
**Lens:** All four — correctness, handoff readiness, analytical coverage, substrate. (See mind map captured in chat.)
**Architectural constraint:** Additive only. New sheets / sections / cells / cell comments / named ranges are in scope. Rewriting existing aggregators (`T12 Raw Data` SUMIFs, `Monthly Trending` INDEX/MATCH, `T12 Analytics` formula chain, `UW Output` formula spine) is out of scope.

---

## Sequencing

Per the kick-off chat (2026-05-07):

1. **Branches 1 + 4** (correctness + substrate) — foundation cleanup, this round.
2. **Branch 3** (analytical coverage) — depth additions, after foundation lands.
3. **Branch 2** (handoff readiness) — designed last, since it depends on what Branch 3 adds to UW Output.

**Refinement after D-12:** Branch 1 splits into workbook side (1.1 + 1.4 — closes this session) and code side (1.2 + 1.3 — Track 2 chat, deferred). See `Cluster B carry-forward` section below.

---

## Clusters within Branches 1 + 4

The 8 sub-cards across Branches 1 + 4 group naturally into 4 work clusters. Sequenced by dependency / quick-win order:

| # | Cluster | Sub-cards | Nature |
| --- | --- | --- | --- |
| A | **Quick bug fixes** | 1.1 (clear known bugs) | Single-cell formula edits. Fastest to ship. |
| B | **Robustness rules** | 1.2 (sign guards), 1.3 (partial-year T12) | Code-side changes (parser / app), mostly Track 2. |
| C | **New diagnostic sheets** | 1.4 (Validation), 4.1 (Workbook map), 4.2 (Diagnostics) | Three potential new sheets — likely consolidates to fewer. |
| D | **Quality-of-life** | 4.3 (named ranges), 4.4 (in-workbook docs) | Additive plumbing + comments. Lands last. |

---

## Open scoping questions (need answers before designing)

These are decisions to make before each cluster gets designed in detail. Listed by cluster.

### Cluster A — Quick bug fixes

**Q-A1 — UW Output R65 NOI definition.** Cell currently empty. NOI sits between Mgmt fee (R64) and EBITDARM (R66). Three valid options:

- (a) NOI = EBITDARM (pre-mgmt-fee operating income). Common in IRR / cap rate contexts.
- (b) NOI = EBITDAR (post-mgmt-fee operating income). Common in lender / DSCR contexts.
- (c) Drop R65 entirely — EBITDARM (R66) and EBITDAR (R67) already cover both ends of the spectrum.

**Q-A2 — UW Output R61 Lease / ground lease.** Cell empty in UW Output. `T12 Analytics!R102` still shows `=0` placeholder (was supposed to get an INDEX/MATCH per substrate v0.1.4 plan but did not land in this bundled file — see F-2 below). Two paths:

- (a) **Fix at the T12 Analytics root** (replace `=0` at R102 with `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`), then fill UW Output R61 to point at it. Borderline — replacing a placeholder vs rewiring an existing formula. Feels additive.
- (b) **Fix only at UW Output R61** — point B-F at T12 Analytics E102/F102 even though those return 0. Leaves the T12 Analytics gap unfixed (still shows 0 even when source has lease data). Cleaner-additive but kicks the can.

**Q-A3 — N501 vs N500 SUMIF range cosmetic mismatch.** Documented in journal 2026-05-06 as a v0.1.5 migration side-effect. Fixing it means touching `T12 Raw Data` SUMIFs — which is rewiring an existing aggregator and out of scope per the architectural constraint.

- **Tentative answer:** defer / skip. Note here and revisit only if a future migration touches that range anyway.

### Cluster B — Robustness rules

(Detail questions deferred until Cluster A ships.)

### Cluster C — New diagnostic sheets

**Q-C1 — One sheet or three?** Sub-cards 1.4 (Validation), 4.1 (Workbook map), 4.2 (Diagnostics) all proposed as new sheets. Significant content overlap (each surfaces "what's going on inside the workbook"). Three options:

- (a) **Three distinct sheets** — one per sub-card. Maximally separated concerns.
- (b) **One consolidated "Workbook Health" sheet** with three sections (Map / Validation / Diagnostics).
- (c) **Two sheets** — `Workbook Map` (static reference: which sheet does what) + `Workbook Health` (dynamic checks: validation + diagnostics combined).

**Q-C2 — Sheet position.** Where do new diagnostic sheet(s) sit?

- (a) Front of workbook (first tab — analyst sees them on open)
- (b) Back of workbook (after UW Output — out of the analyst's working flow)
- (c) Hidden by default (un-hide when needed for debugging)

### Cluster D — Quality-of-life

**Q-D1 — Cover sheet.** `SPEC-RR.md` describes a Cover sheet for version metadata, but the bundled file does not contain one (see F-3). Decisions:

- Add a Cover sheet (yes / no)
- If yes, what does it carry — substrate version, RR / T12 version pills, "what this workbook is" intro text, contact / repo URL

**Q-D2 — Named-range scope.** What additive named ranges earn their place?

- `RR_Input_Data` → `Rent Roll Input!A7:S606`
- `T12_Input_Data` → `T12 Input!A12:O511`
- `RR_Period_Date` → `Rent Roll Recon!B2`
- More? (e.g. semantic anchors for UW Output sections — `UWO_Revenue`, `UWO_Labor`, `UWO_NonLabor`, `UWO_Returns`)

---

## Discovered facts (from grounding investigation 2026-05-07)

These came out of looking at the actual workbook before designing. They inform the open questions above.

### F-1 — H20 #NAME? root cause identified

The formula at `Rent Roll Recon!H20` contains `_xlfn._LONGTEXT(...)` wrapping help-text strings that exceed Excel's 255-character-per-literal limit. `_xlfn.` is Excel's prefix for newer functions; `_LONGTEXT` is not a real function — it is an artifact of how the formula was serialized when over-long string literals were embedded. Excel does not recognize it on parse → #NAME? error visible in every populated workbook.

**Fix paths** (to choose from during Cluster A design):

- (i) Break each long help-text string into multiple sub-255-char chunks concatenated with `&`. Same formula shape, same visible behaviour, just spelled out.
- (ii) Move the five diagnostic text variants into a small lookup table (e.g. a hidden helper `RR_Recon_HelpText` with rows for `aligned / within 2% / T12 higher / RR higher` and a chooser cell), and have H20 do a small INDEX/MATCH against it. Cleanest separation of formula logic from copy.
- (iii) Drastically shorten the help text — drop the numbered investigation lists, keep only the headline diagnosis. Loses analyst guidance.

### F-2 — UW Output bug-row inventory verified

| UW row | Label | What's missing | Source row in T12 Analytics | Status |
| --- | --- | --- | --- | --- |
| R29 | Bonus wages | E29 + F29 empty (siblings R28, R30 have formulas) | E64 / F64 — populated | **Bug — fill** |
| R57 | Bad debt expense | E57 + F57 empty (siblings R56, R58 have formulas) | E98 / F98 — populated | **Bug — fill** |
| R61 | Lease / ground lease | All B-G empty | E102 / F102 — currently `=0` placeholder | **Bug — paper-over fill** (D-04) |
| ~~R65~~ | ~~NOI~~ | ~~All B-G empty~~ | ~~No "NOI" row exists in T12 Analytics~~ | **Not a bug** — visual section separator (D-03) |

R29 and R57 are clean fills against the sibling pattern (see F-5). R61 follows the same pattern but additionally needs `G61=F61-E61` (currently empty, unlike its siblings).

### F-5 — Sibling-row formula pattern in UW Output

Confirmed by inspecting R28 / R30 (around R29) and R56 / R58 (around R57). All non-subtotal data rows in UW Output follow the same shape:

| Col | Value | Notes |
| --- | --- | --- |
| B–D | literal `"-"` (string dash) | Forecast period columns — not yet populated |
| E | `='T12 Analytics'!E{src}` | Current-period source |
| F | `='T12 Analytics'!F{src}` | Prior-period source |
| G | `=F{row}-E{row}` | Variance |

This means the fills for R29 / R57 / R61 are mechanical — no design judgement required.

### F-6 — R61 indent anomaly (cosmetic)

`Rent Roll Recon` siblings R60 (Other / miscellaneous) and R62 (Total non-labor) carry `indent=1.0` on column A. R61 (Lease / ground lease) is `indent=0.0`. Reads inconsistent with the rest of the non-labor section. Trivial cosmetic fix: set R61 indent to 1.0 while filling its formulas.

### F-7 — What H20 actually is (location, purpose, current behavior)

**Location:** `Rent Roll Recon!H20`. The sheet is laid out with column A = metric label, column E = total dollar value, column H = "Flag / Note" — the analyst-facing interpretation column.

**What H20 does:** Row 20 is the gap row. `E20=E18-E19` (RR-implied annualized rent minus T12 actual). H20 is supposed to interpret that dollar gap as a plain-English message that tells the analyst whether to worry, and if so, what to investigate.

**The four output cases:**
1. Gap = $0 → "Gap = $0 — RR and T12 are perfectly aligned."
2. |Gap| ≤ 2% of T12 → "Gap = $X (X%) — within 2%, normal timing variance: …"
3. Gap < 0 (T12 higher) → "⚠ Gap = … T12 collected MORE than RR projects. Investigate: (1)…(5)…"
4. Gap > 0 (RR higher) → "⚠ Gap = … RR projects MORE than T12 collected. Investigate: (1)…(5)…"

**Why it's broken:** The 5-item investigation lists in cases 3 and 4 are each a single string literal over 255 characters. Excel's per-literal limit is 255 chars, so when the formula was written/serialized, the over-long literals got wrapped in `_xlfn._LONGTEXT(...)` — a marker for "this string needs special handling" that Excel does not recognize on parse. Result: every populated workbook shows `#NAME?` in H20. The cell never delivered its diagnostic value to any analyst.

### F-8 — Property + period cell locations (verified 2026-05-07)

| Field | Label cell | Value cell | Currently |
| --- | --- | --- | --- |
| Property name | `T12 Analytics!A2` | `T12 Analytics!B2` | empty (manual entry expected) |
| T12 period ending | `T12 Analytics!D2` | `T12 Analytics!E2` | empty (manual entry expected) |
| Basis (cash / accrual) | `T12 Analytics!G2` | `T12 Analytics!H2` | populated: `ACCRUAL` |
| RR period (selected) | `Rent Roll Recon!A2` ("Select period:") | `Rent Roll Recon!B2` | dropdown driven by `RR_Calc!B2:B13` |

Per D-14, `Property_Name` will live canonically at `Cover!B5` (new), and `T12 Analytics!B2` will become `=Property_Name` (additive — fills a currently empty cell).

### F-3 — Cover sheet absent

`SPEC-RR.md` lists a `Cover` sheet ("version metadata") in the expected structure. The bundled `ALF_Financial_Analyzer_Only.xlsx` does not contain one. Either it was never created, or it was removed by an earlier edit and the spec was not updated. No substrate version is currently visible anywhere in the workbook to a manual analyst opening the file. (Q-D1.)

### F-4 — Named ranges currently defined

Only two named ranges exist in the workbook:

- `DescMap_Description` → dynamic range over `Description_Map!$A$5:...`
- `DescMap_Label` → dynamic range over `Description_Map!$B$5:...`

Both serve the T12 Path B helper. No named ranges exist for `Rent Roll Input`, `T12 Input`, period date, or any UW Output section. (Q-D2.)

---

## Decision Log

Decisions land here once made. Format: append-only, newest at the bottom.

| ID | Date | Cluster | Question | Decision | Rationale |
| --- | --- | --- | --- | --- | --- |
| D-01 | 2026-05-07 | (meta) | Sequencing | Branches 1 + 4 → 3 → 2 | User directive at kick-off. Foundation before depth before handoff. |
| D-02 | 2026-05-07 | (meta) | Architectural freedom | New sheets / sections OK; existing aggregators untouched | User pick from mind-map scoping question. |
| D-03 | 2026-05-07 | A | Q-A1 — UW Output R65 NOI definition | **R65 is a visual section separator, not a calculated row.** Drop from bug list. | Confirmed via formatting inspection: bold + fill `FF2F5597`, identical to R69 'CAPACITY INPUTS'. EBITDARM (R66) / EBITDAR (R67) / EBITDA (R68) directly below carry the actual NOI flavors. |
| D-04 | 2026-05-07 | A | Q-A2 — Lease / ground lease gap fix | **Paper over.** Fill UW Output R61 with formulas pointing at T12 Analytics E102/F102 even though those currently return `=0`. Log T12 Analytics R102 as a separate deferred bug. | Cleanest-additive: doesn't replace any existing formula. Trade-off accepted: R61 will display `$0` until the deferred T12 Analytics fix lands. |
| D-05 | 2026-05-07 | C | Q-C1 — New diagnostic sheets count | **One consolidated `Workbook Health` sheet** with three sections: Map / Validation / Diagnostics. | Strong content overlap across the three original sub-cards. One tab keeps the toolbar uncluttered and lets the analyst scan all health signals in one scroll. |
| D-06 | 2026-05-07 | C | Q-C2 — Workbook Health sheet position | **Hidden by default**, un-hide when debugging. | Out of the analyst's working flow. Still accessible via right-click → Unhide. Keeps the visible-sheet count lean. |
| D-07 | 2026-05-07 | C | Q-C3 — Workbook Map: static or formula-driven? | **Formula-driven from per-sheet anchor cells.** | Map row content stays in sync without manual maintenance. Trade-off: requires defining a per-sheet anchor-cell convention and back-filling existing sheets. |
| D-08 | 2026-05-07 | C | Q-C4 — Validation tolerance | **±$1 rounding tolerance** on Source $ → Operating $ leakage. | Catches real leakage while absorbing cent-level FP drift from Excel arithmetic. |
| D-09 | 2026-05-07 | A | Q-A4 — H20 #NAME? fix path | **(i) Chunk literals.** Replace each `_xlfn._LONGTEXT("A","B")` with `"A"&"B"`. Single-cell rewrite, all 4 messages preserved. | Smallest possible footprint. The "decide message vs render message" separation that path (ii) would buy doesn't earn its weight given how rarely the diagnostic copy will change. |
| D-10 | 2026-05-07 | C | Q-C5 — Anchor cell convention | **`AZ1:AZ5`, 5 fields** (purpose / category / visibility / version / notes). | Verified empty on all 11 existing sheets. Predictable location, no INDIRECT() needed. 5 fields = enough for the Map section to be useful, not so many that anchor maintenance becomes a chore. |
| D-11 | 2026-05-07 | D | Q-D1 — Cover sheet | **Add Cover sheet** with substrate version, RR/T12 version pills, repo URL, what-this-is intro. | Single landing tab. Versions live in one canonical spot that other sheets (Workbook Health Diagnostics) can read from. |
| D-12 | 2026-05-07 | (meta) | Q-B-defer — Cluster B handling | **Defer to its own Track 2 chat.** Branch 1 partially closes this session; sub-cards 1.2 (sign guards) + 1.3 (partial-year T12) ship later. | Honors "one track at a time" principle from journal 2026-05-06. Cluster B is code-side; bundling it would re-create the cross-track scope problem. |
| D-13 | 2026-05-07 | D | Q-D3 — Cell-comment scope | **(a) Light.** Comments on 4-5 hardest-to-decode formulas only: T12 Raw Data SUMIFS pattern, T12 Analytics core formulas, EGI calc, EBITDAR calc, H20 diagnostic chain. | Light coverage on the cells where a future analyst (or future Erik) is most likely to ask "what does this do?". Heavier coverage shifts to `SPEC-Analyzer.md` when that doc spins up. |
| D-14 | 2026-05-07 | D | Q-D2 — Named ranges to add | **5 names:** `RR_Period_Date`, `T12_Period_Date`, `RR_Input_Data`, `T12_Input_Data`, `Property_Name`. | `Property_Name` lives at `Cover!B5` (new); `T12 Analytics!B2` (currently empty) gets `=Property_Name` so the property name is entered once and propagates. Other four point at existing cells. |
| D-15 | 2026-05-11 | B3.1 | Property name source-of-truth | **A2 — input-sheet source cells + 3-priority formula.** RR Input B2 → T12 Input B2 → Cover B5 fallback. | Trivial workbook delta; clean attachment point for future Track 1/2 writer changes. |
| D-16 | 2026-05-11 | B3.1 | T12 period-end derivation | **`LOOKUP(2,1/(...<>""))` rightmost-populated** on T12 Input C11:N11. | Partial-year safe. No upstream writer change needed. |
| D-17 | 2026-05-11 | B3.2 | Visual placement + count | **5 charts on T12 Analytics K1:V44** (2×2 grid + conditional acuity donut). Hidden helper at K46:V53. | Senior-housing UW standard visual set per CBRE / NIC MAP. One-tab simplicity. |
| D-18 | 2026-05-11 | B3.2 | Note style for visuals | **Conditional formula-driven notes**, not openpyxl cell comments. | Live notes update with data; popup comments don't. |
| D-19 | 2026-05-11 | B3.3 | Rent Roll Recon B2 default | **`LOOKUP(9.99E+307,...)` default + DV from RR_Calc!A2:A13.** | Auto-latest with override. F-8 docstring updated accordingly. |
| D-20 | 2026-05-11 | B3.4 | IL deep-dive position | **Append rows 86-100 on Rent Roll Recon.** Includes sqft analysis. | Avoids openpyxl `insert_rows()` quirk. Verified no external refs to rows 69-84. |
| D-21 | 2026-05-11 | B3.5 | MC deep-dive pattern handling | **Auto-detect flat/tiered/FFS** via distinct-count of K column. Substring tier mapping. | Handles all three industry pricing structures. |
| D-22 | 2026-05-11 | (meta) | Track scoping for cross-cutting plumbing | **Workbook = Track 3 (this session).** RR writer stamp = Track 1 follow-up. T12 writer stamp = Track 2 follow-up. Both deferred. | Honors one-track-at-a-time. |
| D-23 | 2026-05-12 | (Cluster A — late) | Rent Roll Recon row 16 — formula vs intent mismatch | **Rewrite B16/C16/D16 to sum Market Rate (`'Rent Roll Input'!$G`) over all units (no status filter), by care type.** Was summing Actual Rate (`$H`) over occupied. Update A16 label to "RR Gross Potential Rent / mo  (Market × all units)" and rewrite H16 note to state GPR semantics. | The H-column note already specified "gross before concessions" intent; the formula didn't match. New behavior gives the underwriting-standard Gross Potential Rent anchor (Homestead: $809k vs the prior $565k). Row 17 was already correct (`H + I` works because concessions are negative-signed) and is left untouched — preserves the row16-vs-row17 reading as "vacancy + market-vs-actual gap." |

---

## Cluster A — Concrete design

All decisions resolved except the H20 fix path (Q-A4 below). Edits, ordered for diff readability:

**A-1. Fill UW Output R29 (Bonus wages)**
- `B29:D29` ← `"-"` (literal)
- `E29` ← `='T12 Analytics'!E64`
- `F29` ← `='T12 Analytics'!F64`
- `G29` unchanged (already `=F29-E29`)

**A-2. Fill UW Output R57 (Bad debt expense)**
- `B57:D57` ← `"-"`
- `E57` ← `='T12 Analytics'!E98`
- `F57` ← `='T12 Analytics'!F98`
- `G57` unchanged (already `=F57-E57`)

**A-3. Fill UW Output R61 (Lease / ground lease) — paper over per D-04**
- `B61:D61` ← `"-"`
- `E61` ← `='T12 Analytics'!E102` _(currently displays `0`; will resolve when deferred bug A-5 lands)_
- `F61` ← `='T12 Analytics'!F102`
- `G61` ← `=F61-E61` _(NEW — currently empty)_
- `A61` indent ← `1.0` _(cosmetic, per F-6)_

**A-4. Fix `Rent Roll Recon!H20` `_xlfn._LONGTEXT` #NAME? error**

Per D-09, replace each `_xlfn._LONGTEXT("A","B")` with `"A"&"B"`. Per-literal verification: 6 string literals total, max length = 255 chars (cases 3a + 4a sit exactly at Excel's limit but are valid). Total formula = 1068 chars. Round-trips clean through openpyxl with no `_xlfn._LONGTEXT` artifact.

Corrected formula for `Rent Roll Recon!H20`:

```
=IF(E20=0,"Gap = $0 — RR and T12 are perfectly aligned.",IF(ABS(E20/E19)<=0.02,"Gap = "&TEXT(E20,"$#,##0")&" ("&TEXT(E20/E19,"0.0%")&") — within 2%, normal timing variance: partial-month move-ins/outs or rounding.",IF(E20<0,"⚠ Gap = "&TEXT(E20,"$#,##0")&" ("&TEXT(E20/E19,"0.0%")&"). T12 collected MORE than RR projects. Investigate: (1) Occ was higher earlier in T12 — property trending down; (2) Rates were higher in prior months — compression or new concessions; (3) Active concessions are newer than T12 average — not in full T12; ("&"4) Partial-month collections in T12 for move-ins/outs; (5) One-time adjustments or reversals in T12 income statement.","⚠ Gap = "&TEXT(E20,"$#,##0")&" ("&TEXT(E20/E19,"0.0%")&"). RR projects MORE than T12 collected. Investigate: (1) Occupancy has improved during T12 — positive trend; (2) Rates were raised mid-T12 — RR reflects new higher rates; (3) Bad debt or uncollected rent in T12 not visible in RR; (4) Notice residents bill"&"ed but not yet collected; (5) One-time credits or refunds in T12 reduced collected revenue.")))
```

**A-5. Deferred bug — `T12 Analytics!R102` placeholder**
Replace `=0` with `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)` per the v0.1.4 plan. **Out of scope for this round** (rewiring an existing aggregator). Logged here so it doesn't disappear; revisit when ready to do a substrate v0.1.6.

---

### ✓ Cluster A — Ready to ship

| Edit | Cell(s) | Status |
| --- | --- | --- |
| A-1 | `UW Output!B29:F29` | Fully spec'd |
| A-2 | `UW Output!B57:F57` | Fully spec'd |
| A-3 | `UW Output!B61:G61` + indent | Fully spec'd |
| A-4 | `Rent Roll Recon!H20` | Fully spec'd, formula verified |
| A-5 | `T12 Analytics!R102` | **Deferred** — substrate v0.1.6 |

Implementation packaging deferred until full Branches 1 + 4 spec is locked (so all sheet edits can ship in one migration script + Analyzer version bump).

---

## Cluster C — Workbook Health sheet design

Per D-05 / D-06 / D-07 / D-08: one sheet, three sections, hidden by default, Map section formula-driven from per-sheet anchor cells, Validation uses ±$1 tolerance.

### Sheet shape

- **Name:** `Workbook Health`
- **Visibility:** hidden (D-06)
- **Position:** last sheet in workbook (after `T12_Calc`)
- **Section headers:** match the existing navy `FF2F5597` bold-fill convention from `UW Output!R65` / `R69`

| Section | Purpose |
| --- | --- |
| 1 — WORKBOOK MAP | one row per sheet; name, purpose, category, visibility, version, notes — pulled from per-sheet anchor cells |
| 2 — VALIDATION | live $ checks with ✓ / ⚠ / ✗ status |
| 3 — DIAGNOSTICS | per-sheet formula-error counts, capacity utilization, version + timestamp pills |

### Anchor cell convention (proposal — see Q-C5)

Each sheet exposes 5 anchor cells in `AZ1:AZ5`. Verified empty on every existing sheet (rightmost data column on any sheet is U; AZ is column 52 — well clear of any analyst's working area).

| Cell | Field | Type | Example |
| --- | --- | --- | --- |
| `AZ1` | Sheet purpose | static text | "RR data input — paste normalized rent roll here" |
| `AZ2` | Sheet category | static enum | `input` / `aggregator` / `output` / `reference` / `health` |
| `AZ3` | Visibility intent | static enum | `visible` / `hidden` |
| `AZ4` | Substrate version stamp | static text | `v0.1.5` |
| `AZ5` | Notes | static text | optional one-liner |

The Workbook Map section renders each row by reading these via direct refs:

```
| A: Sheet name (manual) | B: =Sheet!AZ1 | C: =Sheet!AZ2 | D: =Sheet!AZ3 | E: =Sheet!AZ4 | F: =Sheet!AZ5 |
```

One-time setup cost: 11 sheets × 5 cells = 55 small additions to populate.

### Validation section — check list

| # | Check | Formula sketch | Threshold |
| --- | --- | --- | --- |
| V1 | Source $ → Operating $ leakage | `=ABS(SUMIF(Description_Map!A:A,"<>UNMATCHED",...) - operating_total)` | ≤ $1 → ✓ (D-08) |
| V2 | UNMATCHED row count | count of "UNMATCHED" labels in `Description_Map` | 0 → ✓ |
| V3 | RR period date populated | `=ISNUMBER('Rent Roll Recon'!B2)` | TRUE → ✓ |
| V4 | T12 period dates populated | check T12 Input header dates | TRUE → ✓ |
| V5 | Description_Map coverage | (mapped / total) per Label | < 100% → ⚠ |
| V6 | Capacity inputs filled | `UW Output!R70:R72` numeric | all → ✓ |

### Diagnostics section — content

| # | Diagnostic | Source |
| --- | --- | --- |
| G1 | Per-sheet formula error counts | counts of `#NAME?`, `#REF!`, `#VALUE!`, `#DIV/0!` per sheet |
| G2 | Capacity utilization (IL / AL / MC / Total) | occupied beds / licensed beds |
| G3 | Last-open timestamp | `=TEXT(NOW(),"yyyy-mm-dd hh:mm")` (volatile but acceptable on a hidden sheet) |
| G4 | Substrate version pill | reads from a fixed cell on this sheet |
| G5 | RR app version pill | reads from Cover (if added per Q-D1) else static |
| G6 | T12 normalizer version pill | reads from Cover (if added) else static |

---

## Cluster D — Cover sheet + supporting work

Per D-11.

### Cover sheet

- **Name:** `Cover`
- **Position:** first tab in workbook
- **Visibility:** visible

| Block | Rows | Content |
| --- | --- | --- |
| Title | A1 | "ALF Financial Analyzer" (large, bold) |
| Subtitle | A2 | "Senior-housing underwriting workbook — RR + T12 reconciliation, UW-ready output" |
| Property header | A4 | "Property" (navy section header) |
| Property name | A5 / B5 | "Property name" / `[user input — also referenced as named range Property_Name]` |
| Versions header | A7 | "Versions" (navy section header) |
| Substrate template | A8 / B8 | "Substrate template" / `v0.1.6` |
| RR Normalizer | A9 / B9 | "Rent Roll Normalizer (app)" / `v1.12.0` |
| T12 Normalizer | A10 / B10 | "T12 Normalizer" / `v0.1.0` |
| Links header | A12 | "Links" (navy section header) |
| Repo | A13 / B13 | "GitHub" / hyperlink |
| Streamlit | A14 / B14 | "App URL" / `https://rrnormalizer.streamlit.app/` |
| About header | A16 | "About" (navy section header) |
| About prose | A17 → | 2-3 short paragraphs: what this workbook is, what each visible tab does at a glance, where to find diagnostics (`Workbook Health` is hidden — un-hide via right-click) |

`Workbook Health!Diagnostics` reads version pills from `Cover!B8` / `B9` / `B10`.
`T12 Analytics!B2` becomes `=Property_Name` (currently empty cell, additive fill).

### Per-sheet anchor population (D-10 convention applied)

13 sheets total after this round (11 existing + 2 new). Each gets `AZ1:AZ5` populated:

| Sheet | AZ1 (purpose) | AZ2 (category) | AZ3 (visibility) | AZ4 (version) |
| --- | --- | --- | --- | --- |
| Cover (NEW) | Workbook landing — versions, links, orientation | reference | visible | v0.1.5 |
| T12 Analytics | Per-Label T12 aggregation; main feed for UW Output | aggregator | visible | v0.1.5 |
| T12 Input | T12 raw paste area (MRI / Yardi / normalizer output) | input | visible | v0.1.5 |
| T12 Raw Data | Description→Label rollup with monthly trending | aggregator | visible | v0.1.5 |
| Rent Roll Input | RR normalized output paste area | input | visible | v0.1.5 |
| Rent Roll Recon | RR ↔ T12 reconciliation diagnostic | aggregator | visible | v0.1.5 |
| Monthly Trending | Per-Label monthly summary by Group | aggregator | visible | v0.1.5 |
| UW Output | Final UW-ready summary; copy to downstream sheet | output | visible | v0.1.5 |
| Mapping Review | Description_Map review for UNMATCHED descriptions | reference | visible | v0.1.5 |
| Description_Map | Canonical Description→Label vocabulary | reference | visible | v0.1.5 |
| RR_Calc | RR helper calculations | reference | hidden | v0.1.5 |
| T12_Calc | T12 helper calculations | reference | hidden | v0.1.5 |
| Workbook Health (NEW) | Map / Validation / Diagnostics | health | hidden | v0.1.5 |

AZ5 (notes) left empty by default; populated only if useful for a given sheet.

---

## Open questions — Clusters B / C / D

Surfaced now so they can be answered in batch and the design pages below can fill in.

### Q-A4 — RESOLVED (D-09): chunk literals.
### Q-C2 — RESOLVED (D-06): hidden by default.
### Q-C3 — RESOLVED (D-07): formula-driven from per-sheet anchor cells.
### Q-C4 — RESOLVED (D-08): ±$1 rounding tolerance.
### Q-C5 — RESOLVED (D-10): AZ1:AZ5, 5 fields.
### Q-D1 — RESOLVED (D-11): Cover sheet added.
### Q-B-defer — RESOLVED (D-12): Cluster B deferred to separate Track 2 chat.

### Q-D3 — RESOLVED (D-13): Light coverage.
### Q-D2 — RESOLVED (D-14): 5 names — RR_Period_Date, T12_Period_Date, RR_Input_Data, T12_Input_Data, Property_Name.

---

## Named-range definitions (per D-14)

| Name | Target | Notes |
| --- | --- | --- |
| `RR_Period_Date` | `Rent Roll Recon!B2` | Existing dropdown cell driven by `RR_Calc!B2:B13`. |
| `T12_Period_Date` | `T12 Analytics!E2` | Currently empty; fills via T12 normalizer or manual entry. |
| `RR_Input_Data` | `Rent Roll Input!A7:S606` | Static for now; future row-count growth = update name def once. |
| `T12_Input_Data` | `T12 Input!A12:O511` | Same as above for T12. |
| `Property_Name` | `Cover!B5` | NEW canonical home. `T12 Analytics!B2` will be `=Property_Name`. |

Existing named ranges retained as-is: `DescMap_Description`, `DescMap_Label`.

---

## ✓ Design close-out — what ships in substrate v0.1.6

All in-scope design questions resolved. The full content of substrate v0.1.6:

### Workbook structural changes

| Cluster | Item | Detail |
| --- | --- | --- |
| A | UW Output R29 / R57 / R61 fills | Mechanical sibling-pattern, no judgement |
| A | UW Output R61 indent fix | 0.0 → 1.0 (cosmetic) |
| A | Rent Roll Recon H20 chunked rewrite | Verified: 6 literals, max 255 chars, 1068-char total |
| C | Add `Workbook Health` sheet | Hidden, last position, 3 sections |
| D | Add `Cover` sheet | First tab, visible, 4 blocks (Property / Versions / Links / About) |
| D | Populate `AZ1:AZ5` anchor cells on all 13 sheets | 5 fields × 13 sheets = 65 cells |
| D | Add 5 named ranges | Plus `T12 Analytics!B2 = =Property_Name` (additive fill) |
| D | Cell comments (light) | T12 Raw Data SUMIFS pattern, T12 Analytics core, EGI calc, EBITDAR calc, H20 chain |

### Out of this round (logged) — ALL CLOSED 2026-05-08

| Item | Status | Resolution |
| --- | --- | --- |
| T12 Analytics R102 lease formula (A-5) | ✓ **Closed** | Substrate v0.1.7 (commit `36e1659`). E102 now `=IFERROR(INDEX('T12 Raw Data'!R:R,MATCH("Lease / ground lease",'T12 Raw Data'!B:B,0)),0)`; F102 = `=E102`. |
| T12 Raw Data N501 vs N500 SUMIFS range mismatch | ✓ **Closed** | Substrate v0.1.7 — swept 636 cells from `:$X$501` → `:$X$500`. |
| Cluster B (sign guards, partial-year T12) | ✓ **Closed** | T12 v0.2.0 (commit `555f4e4`). `_check_sign_convention` (CONCESSION-only, suffix-aware), `_count_populated_months`, `parse_t12(..., annualize_partial_year=False)`. App wires the sidebar checkbox + status-panel warnings. |

---

## Implementation packaging

### Migration script

`tools/migration/migrate_to_v016.py` — analogous to the existing `migrate_to_v015.py`. Operations in order:

1. Add new sheet `Cover` at position 0 (first tab); populate Title / Property block / Versions / Links / About
2. Add new sheet `Workbook Health` at last position, set `state='hidden'`; populate three sections
3. Populate `AZ1:AZ5` anchor cells on all 13 sheets per the population table
4. Add 5 named ranges via `wb.defined_names`
5. Set `T12 Analytics!B2 = =Property_Name`
6. Fill UW Output R29 / R57 / R61 + R61 indent
7. Replace Rent Roll Recon H20 formula with chunked-literal version
8. Add cell comments (light scope per D-13)
9. Verification block: 0 formula errors, all named ranges resolve, AZ anchors populated on all 13 sheets

The script should:
- Run cleanly against an empty v0.1.5 template (produces an empty v0.1.6 template)
- Run cleanly against a populated v0.1.5 workbook (preserves data, applies structural changes)
- Be idempotent — re-running on a v0.1.6 file is a no-op or skips already-applied changes

### Documentation updates

| Doc | Change |
| --- | --- |
| `SPEC-T12.md` | Bump current-version line to v0.1.6; add v0.1.6 entry to Template substrate section |
| `CHANGELOG-T12.md` | Add `[Substrate template v0.1.6]` entry covering all the above |
| `SPEC-RR.md` | Note: Cover sheet now exists (was listed in expected structure but absent from bundle) — no other change |
| `CHANGELOG-RR.md` | No entry needed (app code unchanged; only the bundled Analyzer changes) |
| `journal.md` | New entry for this session — design-only, all clusters except B; reference this MD |
| `README.md` | Out of scope for this session (per existing journal follow-up note) |
| New: `OPTIMIZATION-DECISIONS.md` | This file — committed to repo as the decision provenance |

### Version bumps

- Substrate template: `v0.1.5 → v0.1.6`
- Bundled Analyzer file: regenerated by running `migrate_to_v016.py` against the existing `ALF_Financial_Analyzer_Only.xlsx`
- RR app version: no change (app code untouched; new bundled Analyzer just drops in)
- T12 normalizer version: no change

---

## Cluster B — CLOSED 2026-05-08 (T12 v0.2.0, commit `555f4e4`)

Originally deferred per D-12 to a separate Track 2 chat to honor the one-track-at-a-time principle. That chat happened on 2026-05-08 and shipped both items as part of the T12 v0.2.0 release. Implementation deltas vs. the original plan:

**B-1. Sign-convention guards** — shipped as `_check_sign_convention(gl_rows)` in `t12_normalizer.py`. **Narrower than originally scoped:** the guard fires only on `CONCESSION` (the universally-negative line item), not on Vacancy / L2L / Bad Debt. Those three are operator-discretionary signs (contra-revenue vs. expense) and the substrate's Monthly Trending R10/R11 already absorbs either polarity. Bad Debt as positive expense is the broker convention. Suffix-only matching (`row.description.split(" | ")[-1]`) avoids false positives when a banner like `Management Fee & Bad Debt` happens to contain a guarded keyword. No per-format `is_negative_expense` slot was added — wasn't needed for any of the four verified fixtures.

**B-2. Partial-year T12 handling** — shipped as `_count_populated_months(gl_rows)` + optional `parse_t12(..., annualize_partial_year=False)` kwarg in `t12_normalizer.py`. App.py wires a sidebar checkbox (disabled until a T12 is uploaded) and surfaces a partial-year warning in the T12 status panel when `populated_months < 12`. Workbook Health gets a V8 partial-year row at substrate v0.1.7 (`=COUNTA('T12 Input'!C11:N11)` paired with ✓/⚠ — see commit `36e1659`).

Verification covers all four reference fixtures via `tools/verify_t12_v020.py`. None trip sign warnings on standard signs (the guard is genuinely defensive, not actively used by any current fixture).

---

## Branch 3 — Analytical coverage (substrate v0.1.7 → v0.1.8)

Kicked off 2026-05-11. Workstream goal: bring underwriter-grade analytical depth into the Analyzer before Branch 2 (handoff readiness) wraps. Architecturally additive — new chart objects, new conditional-note cells, new appended sections on `Rent Roll Recon`, new formulas in currently-empty `T12 Analytics!B2` / `E2` / `K1:V44`. Existing aggregator formulas (`T12 Raw Data` SUMIFs, `Monthly Trending` INDEX/MATCH, `T12 Analytics` revenue/expense spine, `UW Output` spine) remain untouched.

### Discovered facts (from 2026-05-11 grounding inspection)

**F-9 — Property name has no source-of-truth in input sheets.**
Neither `Rent Roll Input` nor `T12 Input` currently stores the property name. Both sheets start at row 1 with paste-instructions; data fills the bodies. The only canonical home is `Cover!B5` (manual entry, named `Property_Name`). For "auto-populate from RR or T12" to be meaningful, the input sheets need reserved value cells the user (or eventually the writer code) can fill. Workbook-only fix per user refinement: reserve **`Rent Roll Input!A3`** and **`T12 Input!A10`** as single-cell value targets (no separate labels — the cell location itself is documented in SPEC + writer follow-ups). Track 1 + Track 2 writer follow-ups stamp these cells programmatically (deferred).

**F-10 — T12 Input C11:N11 holds 12 monthly date headers (post substrate v0.1.7).**
Cluster B partial-year work shipped C11:N11 as the monthly-header anchor (`=COUNTA('T12 Input'!C11:N11)` drives Workbook Health V8). The rightmost populated cell in that range = T12 period ending. No upstream change needed — workbook can derive E2 directly.

**F-11 — Rent Roll Recon B2 currently has no data validation.**
CLAUDE.md F-8 claim of "dropdown driven by `RR_Calc!B2:B13`" is stale on two counts: (a) no DV exists on `Rent Roll Recon` today; (b) the period list lives in `RR_Calc!A2:A13` (date column), with `B2:B13` holding label strings ("Period 1", "Period 2", ...). The MINIFS sort is ascending, so the largest numeric in the range = latest period.

**F-12 — Rent Roll Recon current max_row = 84.**
Existing layout: Sections A-F (rows 6-47) + ARPR rows 50-55 + AL Care Level rows 57-67 + Ancillary rows 69-75 + Concession check rows 78-82. No external sheet references rows 69-84 (verified via dependency scan). Safe to append new sections at rows 86+ without `insert_rows()` risk.

**F-13 — No charts exist anywhere in the workbook.**
Wide-open canvas at `T12 Analytics!K1:V44` (max_col currently 52 from AZ anchors; data ends at H). Chart objects render on top of cells, not into them, so they don't conflict with the AZ4 anchor.

**F-14 — IL has no care-level concept by industry definition.**
Per CBRE / NIC MAP / industry research, IL is base-rent-only — `Rent Roll Input!K` (Care Level) is empty for IL residents. Right IL deep-dive metrics: unit-type mix, sqft, rate dispersion (and its CV).

**F-15 — MC pricing has three dominant patterns** (per industry research):
- **Flat-rate** all-inclusive (no per-level upcharge)
- **Tiered** 2-3 level (typically Basic / Moderate / Advanced or numeric tiers)
- **Fee-for-service** hour-package based (many distinct values)

`Rent Roll Input!K` populated for MC residents iff the property uses tiered/FFS. Distinct-count of MC K values is the pattern signal: 0 → flat-rate, 1-3 → tiered, 4+ → FFS.

### Cluster B3.1 — Property name + period date plumbing

**B3.1-a. Reserve property-name source cells on input sheets.** (Refined 2026-05-11 per user spec — single-cell value, no separate label.)
- `Rent Roll Input!A3` — single cell holding the property name VALUE (writer-populated; analyst-paste OK). The v0.1.5 paste-instructions string at A2 stays untouched.
- `T12 Input!A10` — single cell holding the property name VALUE (writer-populated; analyst-paste OK). Row 10 sits between the layout-description text at A9 and the column headers at A11 — a natural free slot.

These cells are blank by default. Future writer follow-ups stamp them on extraction:
- **Track 1:** `writer.py` populates `Rent Roll Input!A3` with the property name parsed from the source RR (filename stem or detected metadata).
- **Track 2:** `t12_normalizer_writer.py` populates `T12 Input!A10` with the property name parsed from the source T12.

Until those land, the cells are analyst-paste; the analyst types once and T12 Analytics!B2 picks it up via the 3-priority formula below.

**B3.1-b. T12 Analytics B2 formula — priority RR → T12 → Cover.**

```excel
B2 = =IFERROR(IF(LEN(TRIM('Rent Roll Input'!A3))>0,'Rent Roll Input'!A3,IF(LEN(TRIM('T12 Input'!A10))>0,'T12 Input'!A10,Property_Name)),Property_Name)
```

Falls back through three sources. `Property_Name` named range continues to point at `Cover!B5`. Workbook Health row 27 (Property_Name validation) keeps working because the named range definition is unchanged.

**B3.1-c. T12 Analytics E2 formula — rightmost populated T12 month.**

```excel
E2 = =IFERROR(LOOKUP(2,1/('T12 Input'!$C$11:$N$11<>""),'T12 Input'!$C$11:$N$11),"")
```

`LOOKUP(2,1/(...))` is the canonical Excel idiom for "last non-empty value." Tolerates partial-year T12s. Number-formatted as `mmm yyyy`. Named range `T12_Period_Date` already points here; Workbook Health row 26 auto-validates.

### Cluster B3.2 — Property snapshot visuals on T12 Analytics

Layout `K1:V44` on `T12 Analytics`. Charts are openpyxl `BarChart` / `LineChart` / `DoughnutChart` objects anchored to cells. Conditional notes are formula cells below each chart that render context-dependent guidance.

| Visual | Anchor | Source data | Conditional note (cell directly below) |
| --- | --- | --- | --- |
| **V1 — Occupancy by Care Type** (stacked column) | `K1:O14` | Rent Roll Recon B8:D11 (Occupied/Vacant/Notice/Eviction × IL/AL/MC) | `K15`: flags if any care type < 85% occ |
| **V2 — Rate Dispersion** (histogram, IL/AL/MC three-series) | `K16:O29` | computed in helper rows K46:V53 (hidden) — 5 buckets $0-2k / 2-4k / 4-6k / 6-8k / 8k+ | `K30`: flags if IL rate CV > 25% (legacy in-place rates) |
| **V3 — Payer Mix** (doughnut, % of total monthly rev) | `P1:T14` | Rent Roll Recon H40:H46 | `P15`: flags if Medicaid share > 30% (reimbursement risk) or Managed Care > 25% (rate-cap risk) |
| **V4 — T12 Revenue Trend** (line, 12 months) | `P16:T29` | `T12 Raw Data` total operating rev row, monthly cols | `P30`: flags trajectory (latest 3-mo avg vs prior 3-mo avg) |
| **V5 — Acuity Mix** (doughnut, AL Care Levels) | `K31:O44` | Rent Roll Recon D59:D66 | `K45`: flags if D67=0 ("Property is flat-rate AL — no acuity data") OR skew-flag if top tier > 50% of charges |

**Chart styling convention:** match existing navy `FF2F5597` for chart titles. Series colors: IL = `FF4472C4` (light blue), AL = `FF2F5597` (navy), MC = `FFC65911` (orange). Consistent with how `UW Output` section headers and the existing Workbook Health badges already color.

**Hidden helper block at K46:V53** holds the rate-bucket counts for V2 (openpyxl can't compute histogram bins natively — pre-compute via COUNTIFS into helper cells, then chart references the helpers). Cell content visible via Workbook Health → Unhide if needed for debug.

### Cluster B3.3 — Rent Roll Recon B2 latest-date default + DV

**B3.3-a. B2 formula default:**

```excel
B2 = =IFERROR(LOOKUP(9.99E+307,'RR_Calc'!$A$2:$A$13),"")
```

`9.99E+307` is the largest finite double — `LOOKUP` returns the last numeric value ≤ that, which is the largest date in the ascending-sorted list. Robust to empty rows (returns the last populated).

**B3.3-b. Data validation on B2:**

```
type=list, formula1='RR_Calc!$A$2:$A$13'
```

Analyst can override via dropdown. When they pick a date, the formula is replaced by the static value — standard Excel behavior. Re-running the migration restores the default formula. Logged as expected idempotency side effect.

### Cluster B3.4 — IL Unit-Type Mix & Rate Dispersion (Rent Roll Recon section K)

Append at rows 86-100. Sources from `Rent Roll Input` filtered to `Care Type = IL` and `Status <> Vacant / Eviction`. Columns: F (Apt Type), C (Sq Ft), H (Actual Rate).

```
Row 86: K · IL UNIT-TYPE MIX, SIZE & RATE DISPERSION                       (purple section header — FF4A3869, matching H/I/J)
Row 87: Unit Type | Count | % of IL | Avg Rate | Min Rate | Max Rate | Avg Sq Ft | $/Sq Ft
Row 88: Studio
Row 89: 1 Bedroom
Row 90: 2 Bedroom
Row 91: Cottage / Villa
Row 92: Other
Row 93: Total IL occupied | sum | 100% | weighted-avg | (range) | (range) | weighted-avg | weighted-avg
Row 94: (blank)
Row 95: Rate spread (max − min)
Row 96: Rate CV (stdev ÷ avg)  [⚠ if >25%]
Row 97: Avg sq ft (IL)
Row 98: Sq ft range (min — max)
Row 99: $/sq ft (IL avg rate ÷ avg sq ft)
Row 100: Note cell — conditional context message
```

Formulas use `COUNTIFS` / `AVERAGEIFS` / `MINIFS` / `MAXIFS` / `STDEV.S` against `Rent Roll Input!$F$7:$F$606` (Apt Type), `$C$7:$C$606` (Sq Ft), `$H$7:$H$606` (Actual Rate), with the same `$S$7:$S$606=$B$2` period filter and `$D$7:$D$606="IL"` care-type filter that the existing IL columns use.

CV flag in B96: `=IFERROR(IF(STDEV.S(...)/AVERAGEIFS(...)>0.25,"⚠ Wide rate spread — possible legacy in-place rates","✓ Tight"),"-")`

Conditional note at A100: `=IF(B93=0,"No IL units in selected period",IF(<CV-high>,"⚠ IL rate dispersion CV "&TEXT(B96,"0.0%")&" — investigate legacy rates","IL rate dispersion within normal band"))`

### Cluster B3.5 — MC Care Structure auto-detect (Rent Roll Recon section L)

Append at rows 102-117. Sources from `Rent Roll Input` filtered to `Care Type = MC` and `Status <> Vacant / Eviction`. Auto-detect pattern from distinct-count of K values.

```
Row 102: L · MC CARE STRUCTURE  (auto-detected pattern)                    (purple section header — FF4A3869)
Row 103: MC Care Pattern detected:   [auto-formula]
Row 104: (blank)
Row 105: Tier | Count | % of MC | Avg $/mo | Total $/mo
Row 106: Tier 1 / Basic
Row 107: Tier 2 / Moderate
Row 108: Tier 3 / Advanced
Row 109: Other / FFS
Row 110: Total MC occupied | sum | 100% | weighted-avg | sum
Row 111: (blank)
Row 112: MC base rent / resident                  (avg)
Row 113: MC care charge / resident                (avg)
Row 114: Care charge ÷ base rent ratio            [⚠ if >30%]
Row 115: Total MC monthly revenue
Row 116: (blank)
Row 117: Note cell — pattern-specific conditional message
```

Pattern detector at B103:
```excel
=IFERROR(
  IF(SUMPRODUCT((COUNTIF('Rent Roll Input'!$K$7:$K$606,'Rent Roll Input'!$K$7:$K$606)>0)*('Rent Roll Input'!$D$7:$D$606="MC")*('Rent Roll Input'!$S$7:$S$606=$B$2)*('Rent Roll Input'!$E$7:$E$606<>"Vacant")*('Rent Roll Input'!$E$7:$E$606<>"Eviction"))=0,"Flat-rate (no care levels recorded)",
  IF(<distinct-count>=1,"Flat-rate (single tier)",
  IF(<distinct-count><=3,"Tiered acuity (" & <distinct-count> & " levels)",
  "Fee-for-service (" & <distinct-count> & " distinct charges)"))),
"-")
```

(Distinct-count computed via `SUMPRODUCT((COUNTIFS(...)>0)/COUNTIFS(...))` idiom; full formula assembled in the migration script.)

Tier mapping for rows 106-108: explicit substring matches on K column (`"Basic"`, `"Tier 1"`, `"Level 1"` → Basic; `"Moderate"`, `"Tier 2"`, `"Level 2-3"` → Moderate; etc.). Row 109 "Other" catches anything unmatched.

Conditional note at A117: text varies by detected pattern. Flat-rate → "Flat-rate MC. Tier analysis not applicable; see base rent only." Tiered → "Tiered MC. Verify per-tier staffing model supports the implied acuity mix." FFS → "Fee-for-service MC. Charges vary per resident — review individual care plans for sustainability."

### Decision Log additions (Branch 3)

| ID | Date | Cluster | Question | Decision | Rationale |
| --- | --- | --- | --- | --- | --- |
| D-15 | 2026-05-11 | B3.1 | Q-B3.1 — Property name source-of-truth | **Option A2 (refined): single-cell value targets at `Rent Roll Input!A3` and `T12 Input!A10` + 3-priority formula on T12 Analytics B2** (RR → T12 → Cover). No separate label cells (cell location documented in SPEC). Track 1/2 writer follow-ups deferred. | Trivial workbook delta now; clean attachment point for future writer changes. Manual-paste behavior interim. Initial v0.1.8 first pass placed labels at A2/A3 with B-cells as values; refined 2026-05-11 to single-cell-value form per user spec. |
| D-16 | 2026-05-11 | B3.1 | Q-B3.1 — T12 period end derivation | **`LOOKUP(2,1/(...<>""))` on T12 Input C11:N11.** Number-format `mmm yyyy`. | Partial-year safe. No upstream writer change needed — substrate v0.1.7 already populates C11:N11. |
| D-17 | 2026-05-11 | B3.2 | Q-B3.2 — Visual count and placement | **5 charts on `T12 Analytics` K1:V44** in 2×2 grid + acuity donut at K31:O44. Hidden helper block at K46:V53 for rate-bucket counts. | Industry-standard senior-housing UW visual set (per CBRE / NIC MAP research). Keeps everything on one tab. |
| D-18 | 2026-05-11 | B3.2 | Q-B3.2 — Note style | **Conditional formula-driven notes**, not openpyxl cell comments. One note cell directly below each chart, formula-driven from underlying data. | Conditional notes update with the data; popup comments are static. Future analyst always sees current-state guidance. |
| D-19 | 2026-05-11 | B3.3 | Q-B3.3 — Rent Roll Recon B2 default | **Formula `=LOOKUP(9.99E+307,RR_Calc!A2:A13)`** + data validation list on same cell. | "Auto-populate latest, but allow override" pattern. F-8 docstring will be corrected to reflect the new behavior. |
| D-20 | 2026-05-11 | B3.4 | Q-B3.4 — IL deep-dive position | **Append at rows 86-100** (after current max_row=84). Includes sqft analysis per user instruction. | Avoids openpyxl `insert_rows()` formula-text quirk. Dependency scan confirmed no external sheet references current rows 69-84 — append is safe. |
| D-21 | 2026-05-11 | B3.5 | Q-B3.5 — MC deep-dive pattern handling | **Auto-detect flat/tiered/FFS** via distinct-count of MC K-column values. Tier-mapping by substring match. | Handles all three industry pricing structures. Pattern-specific conditional note guides the analyst. |
| D-22 | 2026-05-11 | (meta) | Q-track — Cross-track plumbing follow-ups | **Workbook change is Track 3.** RR writer (`writer.py`) stamp of `Rent Roll Input!A3` is a **Track 1 follow-up**; T12 writer (`t12_normalizer_writer.py`) stamp of `T12 Input!A10` is a **Track 2 follow-up**. Both deferred. | Honors one-track-at-a-time. Until follow-ups land, A3 / A10 of input sheets are analyst-paste; T12 Analytics B2 falls back to Cover!B5 as before. |
| D-23 | 2026-05-11 | (post-ship bug fix) | v0.1.8 `Rent Roll Recon!B2` period dropdown empty in Excel | **Substrate v0.1.9:** Drop `_xludf.` prefix from 12 cells in RR_Calc!A2:A13 (Excel doesn't recognize the Google-Sheets / LibreOffice UDF prefix); replace the v0.1.8 LOOKUP-against-RR_Calc on Rent Roll Recon!B2 with `=IF(MAX('Rent Roll Input'!$S$7:$S$606)>0, MAX(...), "")` — direct dependency on Input!S, no transitive RR_Calc dependency. | Pre-existing bug, surfaced when user opened a populated v0.1.8 Analyzer. Cluster A-style correctness fix analogous to v0.1.6 H20 `_xlfn._LONGTEXT` repair. F-11 docstring stale on second count — the v0.1.8 LOOKUP-via-RR_Calc design assumed RR_Calc evaluated, which it didn't in Excel. Future B2 changes should read direct from Input!S, not via RR_Calc. |

### ✓ Branch 3 — Design close-out (substrate v0.1.7 → v0.1.8)

| Change | Cell(s) | Status |
| --- | --- | --- |
| Reserve `Rent Roll Input!A3` as property-name value cell | input sheet | Spec'd |
| Reserve `T12 Input!A10` as property-name value cell | input sheet | Spec'd |
| T12 Analytics B2 — 3-priority formula | 1 cell | Spec'd |
| T12 Analytics E2 — rightmost month formula | 1 cell | Spec'd |
| T12 Analytics K1:V44 — 5 charts + 5 conditional note cells | new objects | Spec'd |
| T12 Analytics K46:V53 — hidden helper rate buckets | helper block | Spec'd |
| Rent Roll Recon B2 — default formula + DV | 1 cell + 1 DV | Spec'd |
| Rent Roll Recon rows 86-100 — IL section | append | Spec'd |
| Rent Roll Recon rows 102-117 — MC section | append | Spec'd |
| Stamp `Cover!B8` and 13× AZ4 to `v0.1.8` | version pills | Spec'd |
| Update Workbook Health version refs | Diagnostics section | Spec'd |

### Branch 3 — Implementation packaging

**Migration script:** `tools/migration/migrate_to_v018.py` — operations in order:

1. Reserve `Rent Roll Input!A3` as property-name value cell (clears v0.1.8-first-pass label if present)
2. Reserve `T12 Input!A10` as property-name value cell (clears v0.1.8-first-pass label at A2 if present)
3. Rewrite `T12 Analytics!B2` with 3-priority formula
4. Set `T12 Analytics!E2` formula + `mmm yyyy` number format
5. Add 5 chart objects + 5 conditional-note cells on `T12 Analytics`
6. Add hidden helper rate-bucket block at `T12 Analytics!K46:V53`
7. Set `Rent Roll Recon!B2` formula + data validation
8. Write Rent Roll Recon rows 86-100 (IL section)
9. Write Rent Roll Recon rows 102-117 (MC section)
10. Stamp `Cover!B8` = `v0.1.8`; stamp all 13× AZ4 anchors to `v0.1.8`
11. Verification block: 0 formula errors, all named ranges resolve, all 13 AZ4 stamped, 5 chart objects present, RR Input + T12 Input source cells created, B2/E2 formulas present, IL section row 93 sums match section A row 7 IL count (cross-check), MC section row 110 sums match section A row 7 MC count

**Idempotency rule:** every operation gates on a state-check first (cell content / chart presence / version stamp). Re-running produces identical workbook.

### Branch 3 — Open carry-forwards after this ships

- **Track 1 RR writer follow-up** — modify `writer.py` to stamp `Rent Roll Input!A3` with the property name parsed from the source RR (source path stem or detected metadata). Until this lands, the cell is analyst-paste.
- **Track 2 T12 writer follow-up** — modify `t12_normalizer_writer.py` to stamp `T12 Input!A10` with the property name parsed from the T12 source. Until this lands, the cell is analyst-paste.
- **Branch 2 — Handoff readiness** still open per the original Track 3 roadmap (UW Export mirror, pre-export gate, metadata header).

---

## Out-of-scope reminders (carry forward)

These are explicitly NOT being touched in this optimization effort, regardless of how tempting:

- Rewriting `T12 Raw Data` SUMIFs (51 labels × 12 months = 612 formulas)
- Rewriting `Monthly Trending` INDEX/MATCH chain
- Rewriting the `T12 Analytics` formula spine
- Rewriting the `UW Output` formula spine (filling in missing cells per F-2 is additive and OK; replacing existing formulas is not)
- Replacing `R:R` full-column refs in `T12 Analytics` with bounded refs (rewiring)
- Multi-property splitter
- RR-side parser changes (Track 1) — out of scope unless explicitly cross-cutting
- Comparable-property benchmarking, capex / replacement-reserve schedules, multi-year IRR — these belong in the downstream full underwriting sheet, not here

---

## Pointers

- **Mind map** of the broader optimization landscape — kick-off chat 2026-05-07, SVG artifact.
- **Specs being updated** by decisions made here — `SPEC-RR.md` (RR-side) and `SPEC-T12.md` (T12-side) per the maintenance protocol.
- **Future Track 3 doc spinout** — `SPEC-Analyzer.md` / `CHANGELOG-Analyzer.md` once code-side reconciliation work earns its own track per `SPEC-T12.md` "What's next after v0.1.0".
