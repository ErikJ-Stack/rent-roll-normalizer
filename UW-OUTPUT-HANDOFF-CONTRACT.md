# UW Output → ALF UW Template — Handoff Contract

> **Portable doc. Drop this whole file into the Cowork session building the ALF UW Template.**
> It describes exactly what the upstream Analyzer workbook (`ALF_Financial_Analyzer_Only.xlsx`)
> hands off, so the template can be built against a stable contract without access to the source repo.
>
> **Generated from substrate `v0.2.4`** (stamp lives at `Cover!B8`). If that version number changes
> upstream, re-verify this contract — the row map can move.

---

## 1. How the handoff works

The Analyzer is an underwriting workbook. Two feeds (a normalized rent roll and a normalized T12)
flow into input sheets, ~13 analytical sheets reconcile them, and everything rolls up to **two
adjacent output sheets** that are the *only* surface the ALF UW Template should ever read:

| Sheet | What it is | Use it for |
| --- | --- | --- |
| **`UW Output`** | The live, formula-driven UW summary. Every value cell is a formula pointing into `T12 Analytics`. | Reading the structure / row map. Do **not** link a downstream template directly to live formulas — they recalc when the source opens. |
| **`UW Export`** | A **values-only mirror** of `UW Output`, plus a 5-row metadata audit header. | **This is the paste surface.** The template consumes this. |

**The intended motion** (stated verbatim in the Analyzer's own header cells):
- `UW Output!A1`: *"UW Output — T12 Actuals & Normalized | Copy / Paste to ALF UW Template"*
- `UW Output!A2`: *"…Copy cols E–F and paste-values into ALF UW Template."*
- `UW Export!A2`: *"Copy A9:H79 (or Move-or-Copy → Paste-Special: Values) into the downstream UW template."*

So: the analyst paste-**values** the export block into the template. The template should be built to
receive that block at a known anchor and reference cells by **row label**, not by absolute address
(addresses are stable today but there are no named ranges protecting them — see §6).

---

## 2. Column contract (identical on both sheets)

| Col | Header | Meaning | Template should read? |
| --- | --- | --- | --- |
| **A** | *(label)* | Line-item label / section header | As the row key |
| **B** | `IL` | Independent Living split | Only where populated (see §5) |
| **C** | `AL` | Assisted Living split | Only where populated |
| **D** | `MC` | Memory Care split | Only where populated |
| **E** | `T12 Actual` | Trailing-12-month actual (blended) | **Yes — primary** |
| **F** | `Normalized` | Analyst's stabilized underwriting assumption | **Yes — primary** |
| **G** | `Delta` | `= F − E` (normalization adjustment) | Optional (derivable) |
| **H** | `Analytics Ref` | Provenance note back to `T12 Analytics` | No (audit only) |

**The two columns that matter for underwriting are E (T12 Actual) and F (Normalized).**
B/C/D carry an IL/AL/MC breakout only on a handful of rows.

---

## 3. `UW Output` row map (substrate v0.2.4)

Section headers are navy-filled (`FF2F5597`); subtotals are light-blue (`FFD6E4F0`); the bottom-line
EBITDA family is green (`FFE2EFDA`). "Split?" = whether B/C/D (IL/AL/MC) carry real numbers.

### REVENUE — header row 5
| Row | Label | E/F populated | Split? |
| --- | --- | --- | --- |
| 6 | Base rent (normalized) | ✓ | **Yes** |
| 7 | LOC revenue (normalized) | ✓ | **Yes** |
| 8 | Community / move-in fees | ✓ | no |
| 9 | Concessions & specials | ✓ | no |
| 10 | Respite care | ✓ | no |
| 11 | Other community revenue | ✓ | no |
| **12** | **EGI (normalized)** *(subtotal)* | ✓ | no |

### GPR Revenue Waterfall — header row 14 (purple `FF4A3869`)
| Row | Label | E/F | Notes |
| --- | --- | --- | --- |
| 15 | Gross Potential Rent (GPR) — base rent | ✓ | subtotal-styled |
| 16 | Physical vacancy loss | ✓ | |
| 17 | Physical vacancy rate % | ✓ | percentage, not $ |
| 18 | Loss to lease | ✓ | yellow `FFFFF2CC` (analyst-attention) |
| 19 | Loss to lease as % of GPR | ✓ | yellow, percentage |

### LABOR — header row 21
| Row | Label |
| --- | --- |
| 22 | Care staff labor |
| 23 | Wellness / care coordinators |
| 24 | Contract / agency labor |
| 25 | Activities labor |
| 26 | Dining / food service labor |
| 27 | Maintenance & HK labor |
| 28 | Administrative labor |
| 29 | Bonus wages |
| 30 | Overtime wages |
| 31 | PTO wages |
| 32 | Payroll taxes |
| 33 | Employee benefits |
| 34 | Workers' comp insurance |
| 35 | Employee 401(k) |
| **36** | **Total labor & burden** *(subtotal)* |

*(All labor rows: E/F only, no IL/AL/MC split.)*

### NON-LABOR — header row 37
| Row | Label |
| --- | --- |
| 38 | Food cost |
| 39 | Dining & kitchen supplies |
| 40 | Nursing & care supplies |
| 41 | Recreation supplies |
| 42 | R&M fixed |
| 43 | R&M variable |
| 44 | HK & laundry supplies |
| 45 | Sales, adv. & marketing |
| 46 | Referral fees |
| 47 | Utilities |
| 48 | Telephone / IT |
| 49 | P&C insurance |
| 50 | Auto insurance |
| 51 | Fire / security monitoring |
| 52 | Pest elimination |
| 53 | Real estate taxes |
| 54 | Personal property taxes |
| 55 | Legal expenses |
| 56 | Professional services |
| 57 | Bad debt expense |
| 58 | Permits, licenses & dues |
| 59 | Office, admin & G&A |
| 60 | Other / miscellaneous |
| 61 | Lease / ground lease |
| **62** | **Total non-labor** *(subtotal)* |
| **63** | **Total opex (excl. mgmt)** *(subtotal)* |
| 64 | Management fee |

### Returns / bottom line
| Row | Label | Notes |
| --- | --- | --- |
| **65** | **NOI** | ⚠️ **Visual section separator only — NO value cells.** Do not map. (See §4.) |
| 66 | **EBITDARM** | Green. The real headline operating metric. E=`T12 Analytics!E108`. |
| 67 | EBITDAR | Green. |
| 68 | EBITDA | Green. |

### CAPACITY INPUTS — header row 69
| Row | Label | E/F | Split? |
| --- | --- | --- | --- |
| 70 | Licensed beds (IL / AL / MC / Total) | ✗ (no E/F) | **B/C/D only** |
| 71 | Stabilized occupied beds | ✗ (no E/F) | **B/C/D only** |

`UW Output` ends at row 71.

---

## 4. Gotchas the template MUST handle

1. **Row 65 "NOI" is a header band, not a number.** It's styled identically to other navy section
   separators. EBITDARM (66) / EBITDAR (67) / EBITDA (68) directly below carry the actual bottom-line
   flavors. Do not wire an "NOI" input on the template to row 65 expecting a value.
2. **`"-"` placeholders in B/C/D.** Most opex/labor rows have the literal text `-` in the IL/AL/MC
   columns (a `="-"` formula), meaning *"no per-care split for this line."* Treat any non-numeric
   B/C/D as "not provided," not as zero.
3. **Capacity rows (70–71) have no E/F.** Beds live in B/C/D (IL/AL/MC). If the template wants a total
   bed count, sum B:D, don't read E/F.
4. **`Lease / ground lease` (row 61) currently resolves to `0`** even when source data exists. This is a
   known upstream deferral (a placeholder in `T12 Analytics!R102`). The template should tolerate `$0`
   here and not treat it as a hard zero assumption.
5. **Percentages vs dollars.** Rows 17 and 19 are percentages; everything else in E/F is dollars.
6. **Empty vs zero.** Several cells use `=IF(ref="","",…)` so they return an empty string, not 0, when
   upstream is blank. Paste-Values will carry blanks through — the template's formulas must treat blank
   as missing, not error.

---

## 5. Where the IL / AL / MC split actually exists

Only **4 rows** carry a real per-care breakout in B/C/D:

- Row 6 — Base rent (normalized)
- Row 7 — LOC revenue (normalized)
- Row 70 — Licensed beds
- Row 71 — Stabilized occupied beds

Everywhere else the split columns are `"-"` placeholders. If the ALF UW Template needs a finer
revenue-by-care-type breakdown, that data is **not** on the handoff surface — it would have to be
added upstream first (an Analyzer substrate change), not solved in the template.

---

## 6. `UW Export` — the actual paste surface

`UW Export` spans `A1:AZ79`. Layout:

| Rows | Content |
| --- | --- |
| 1–2 | Title + paste instructions |
| **3–7** | **Metadata audit header** (see below) |
| 8 | (spacer) |
| **9–79** | Values-only mirror of `UW Output` rows 1–71 (offset **+8 rows**) |

**Metadata header (rows 3–7) — carries provenance the template should record:**

| Cell | Field | Source |
| --- | --- | --- |
| `B3` | Property name | `Property_Name` named range → `Cover!B5` |
| `B4` | Rent roll period | `RR_Period_Date` (formatted `yyyy-mm-dd`) |
| `B5` | T12 period | `T12_Period_Date` |
| `B6` | Substrate version | `Cover!B8` |
| `B7` | Generated (open time) | `NOW()` at file open |

**Paste recipe for the analyst:** copy `UW Export!A9:H79`, Paste-Special → Values into the template's
intake block. The +8 offset means **`UW Output` row N == `UW Export` row N+8** (e.g. EBITDARM is
`UW Output!66` = `UW Export!74`).

### Named ranges available upstream (the only stable symbolic anchors)
```
Property_Name     -> Cover!$B$5
RR_Period_Date    -> 'Rent Roll Recon'!$B$2
T12_Period_Date   -> 'T12 Analytics'!$E$2
RR_Input_Data     -> 'Rent Roll Input'!$A$7:$S$606
T12_Input_Data    -> 'T12 Input'!$A$12:$O$511
DescMap_Description, DescMap_Label  (internal mapping; ignore)
```
**There are NO named ranges over any `UW Output` / `UW Export` row or section.** The template binds by
position. If you want robustness, the cleanest upstream fix would be to add semantic anchors
(`UWO_EGI`, `UWO_EBITDARM`, etc.) — flag that as a request, don't hardcode around its absence silently.

---

## 7. Vocabulary the template must match exactly

- **Care types:** `IL` (Independent Living), `AL` (Assisted Living), `MC` (Memory Care). These exact
  two-letter codes are the B/C/D headers. Lookups keyed on care type must use these tokens.
- **Two scenarios per line:** `T12 Actual` (col E) and `Normalized` (col F). The template's
  actual-vs-underwriting columns map 1:1 to E and F respectively.

---

## 8. Integration checklist for the ALF UW Template

- [ ] Build the intake block to receive `UW Export!A9:H79` (71 rows, cols A–H) at a fixed anchor.
- [ ] Key every pull off the **row label in col A**, not a hardcoded address, so an upstream row
      insert doesn't silently misalign the model.
- [ ] Pull underwriting figures from **col F (Normalized)**; keep **col E (T12 Actual)** for the
      actual-vs-UW variance view.
- [ ] Skip row 65 (NOI separator). Use row 66 (EBITDARM) as the headline.
- [ ] Treat non-numeric B/C/D and blank E/F as "not provided," never as 0.
- [ ] Record the metadata header (property, RR period, T12 period, substrate version, generated time)
      on the template so each model instance is traceable to a source vintage.
- [ ] Pin the substrate version this template was built against (currently **v0.2.4**); re-validate the
      row map if the upstream stamp changes.

---

*Source of truth: `ALF_Financial_Analyzer_Only.xlsx`, sheets `UW Output` + `UW Export`, substrate
v0.2.4. Regenerate this contract from the workbook if the substrate version moves.*
