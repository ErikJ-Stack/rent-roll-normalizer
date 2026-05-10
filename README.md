# Rent Roll Normalizer + T12 Normalizer

A Streamlit app that turns a senior-housing rent roll AND a T12 financial statement (any operator format) into a populated underwriting workbook (the "Analyzer"). Two parallel pipelines write into the same destination workbook; the Analyzer's analytical sheets reconcile both feeds and roll up to UW Output.

**Live app:** <https://rrnormalizer.streamlit.app/>
**Repo:** <https://github.com/ErikJ-Stack/rent-roll-normalizer> (public)
**Stack:** Python · Streamlit · pandas · openpyxl · Streamlit Community Cloud (free tier)

**Current versions:**

| Stream | Version | Last updated |
| --- | --- | --- |
| RR Normalizer (`RR_VERSION`) | v1.14.0 | 2026-05-08 |
| T12 Normalizer (`T12_VERSION`) | v0.2.0 | 2026-05-08 |
| Bundled Analyzer substrate | v0.1.7 | 2026-05-08 |

---

## What it does

Single-click flow: drop in a raw rent roll (and optionally a raw T12), download a populated `Analyzer.xlsx`. Optional standalone normalized RR workbook for analyst review.

### Two pipelines, one workbook

1. **Rent Roll Normalizer (Track 1)** — parses a raw rent roll, normalizes apartment / care / payer / status vocabulary, classifies bed-level rows under their parent apartments (or self-contained one-row-per-unit formats), and writes a flat bed-level table to the Analyzer's `Rent Roll Input` sheet. Also produces a standalone 7-tab normalized workbook for analyst review.
2. **T12 Normalizer (Track 2)** — parses a raw T12 financial statement (Yardi, MRI, or broker-financial-summary format), classifies each GL row against the Analyzer's `Description_Map` Label vocabulary, surfaces UNMATCHED rows for one-click resolution, and writes the monthly trending matrix to `T12 Input`. Optional `annualize partial-year T12` toggle.

The Analyzer (`ALF_Financial_Analyzer_Only.xlsx`) is bundled in the repo and loaded by default — no need to upload one. An "Advanced — override Analyzer template" expander accepts a custom Analyzer for the session if you need to populate an existing deal's workbook.

### What's normalized

- **Apartment type** — Studio / 1BR / 2BR / Companion / Semi-Private / Other
- **Bed status** — Occupied / Vacant / Hold / Notice / Model / Down (NTV → Notice)
- **Payer type** — Private Pay / Medicaid / Medicare / VA Benefit / LTC Insurance / Other (fallback: Private Pay)
- **Care level** — Level 1-5 / Level 6+ (handles word-tier vocabularies like "Basic" and acuity-tier vocabularies like "Comfort Care 1-4")
- **Care type** — IL / AL / MC (priority chain: explicit Care Type column → apartment context → building/unit code → care level value → property default)
- **Care buckets** — Care Level $ / Med Mgmt $ / Pharmacy $ / Other LOC $ (auto-catch — anything unrecognized flows into Other LOC $ so revenue never disappears)

### Verified rent roll formats

| Format | Beds | Notes |
| --- | --- | --- |
| Salem (Oaks) | 50 | Multi-column unit+apartment, Level 1-7 acuity, three care buckets |
| Briar Glen | 79 (71 units, 8 shared) | Single-column unit, two-letter care codes, `*Vacant` resident marker, Recurring Discounts + One-Time Incentives concession sources |
| Oaks at Beaufort | 104 (54 AL + 50 MC) | Mixed AL+MC building, `Horizons` MC wing, `Comfort Care` acuity, two parallel care-level column groups |
| Homestead Pensacola | 176 (62 IL + 62 AL + 52 MC) | Broker-condensed self-contained format with `Unit ID` / `Cottage` / `Area` / `Category` / `BR/BA` headers |

### Verified T12 formats

Yardi general-format · MRI general-format · Broker Financial Summary (Homestead-style with `Historical Performance` banner). Salem · Briar Glen · Homestead Pensacola · March 2026 (Homestead) reference fixtures.

---

## Project layout

```
rent_roll_app/
├── app.py                              # Streamlit UI shell, sidebar, version constants, pipeline orchestration
│
├── normalizer.py                       # RR header detection + parent-child parse + care grouping
├── mappings.py                         # RR mapping rules + mapping workbook loader
├── pre_cleaner.py                      # RR pre-parse: strip banners, totals blocks, format-specific chrome
├── period_date.py                      # RR period-date detection from filename / sidebar
├── reports.py                          # RR Summary / By_Type / Exceptions builders
├── writer.py                           # RR Excel output writer (standalone normalized workbook)
│
├── t12_normalizer.py                   # T12 format registry + extractors (Yardi / MRI / BrokerFinancialSummary)
├── t12_writer.py                       # T12 → Analyzer paste (T12 Input sheet)
├── t12_normalizer_writer.py            # T12 standalone normalized workbook writer
├── t12_translator.py                   # RR → T12 vocabulary translator (translates Condensed_RR values into the T12 intake workbook's data-validation vocabulary; standalone RR output is unchanged)
│
├── ALF_Financial_Analyzer_Only.xlsx    # Bundled Analyzer template (substrate v0.1.7)
├── mapping_template.xlsx               # Editable RR mapping override template (optional sidebar upload)
│
├── tools/
│   ├── verify_t12_v020.py              # T12 parser-side verification harness (4 reference fixtures)
│   └── migration/
│       ├── migrate_analyzer.py         # General Analyzer migration entry point
│       ├── migrate_to_v015.py          # Substrate v0.1.4 → v0.1.5 migration
│       ├── migrate_to_v016.py          # Substrate v0.1.5 → v0.1.6 migration
│       ├── migrate_to_v017.py          # Substrate v0.1.6 → v0.1.7 migration
│       └── verify_e2e.py               # End-to-end Analyzer verification
│
├── CLAUDE.md                           # Onboarding doc for any Claude session — read first
├── SPEC-RR.md                          # Track 1 spec (RR Normalizer)
├── SPEC-T12.md                         # Track 2 spec (T12 Normalizer)
├── CHANGELOG-RR.md                     # RR per-version notes (newest at top)
├── CHANGELOG-T12.md                    # T12 per-version notes (newest at top)
├── OPTIMIZATION-DECISIONS.md           # Track 3 (Analyzer-only) decisions log
├── journal.md                          # Per-chat session log (newest at top)
│
├── requirements.txt
└── README.md
```

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>.

A local-only `Sample Files/` directory at the repo root is gitignored — drop the four canonical T12 fixtures (Salem / Briar Glen / Homestead Pensacola Financial Summary / Homestead - March 2026 T12) there before running `python tools/verify_t12_v020.py`. The Sample Files are real property financials and must not be committed.

---

## Deploy

The live app at <https://rrnormalizer.streamlit.app/> auto-rebuilds from `origin/main` on every push (~30-60 second lag). Standard loop:

1. Edit files locally
2. `git add . && git commit -m "..." && git push`
3. Streamlit Cloud auto-rebuilds
4. Hard-refresh the app URL with `Ctrl+Shift+R`

**Reboot-first rule:** if the live app's behavior diverges from a verified local run on the same file, assume stale module cache and reboot from share.streamlit.io before debugging.

---

## How to extend

### New rent roll format

Most new operator formats Just Work — the header detector and care-bucket auto-catch handle them. When they don't:

- **Unrecognized headers?** Add patterns to `FIELD_PATTERNS` in `normalizer.py`. The build loop is first-wins, so put more-specific patterns earlier in each field's pattern list.
- **Format-specific chrome at the top or summary blocks at the bottom?** Add to `_BANNER_PREFIXES` or `_TOTALS_SIGNALS` in `pre_cleaner.py`. The first totals-signal hit cuts everything from there to the end of the sheet.
- **Unrecognized status / payer / care-level / apt-type values?** Add a rule to the relevant `DEFAULT_*` list in `mappings.py`, OR upload a custom mapping workbook through the sidebar (overrides defaults for the session).
- **Self-contained one-row-per-unit format?** `_row_is_self_contained_unit()` in `normalizer.py` accepts either a resident name or a recognized bed_status keyword as the qualifying signal.

### New T12 format

Add a new `*Format` class to `t12_normalizer.py` next to `YardiGeneralFormat`, `MRIGeneralFormat`, and `BrokerFinancialSummaryFormat`. Each class implements `detect()` (returns True if this format matches the workbook) and `extract()` (returns the GL rows + monthly columns). Register the class in `FORMATS`. See `SPEC-T12.md` "How to add a new format" for detail.

### New Analyzer substrate version

Substrate edits (new Labels, formula changes, row inserts, named-range changes) are a Track 3 / Track 2 deliverable, NOT a Track 1 (RR-side) one. Required deliverables:

1. New entry in `CHANGELOG-T12.md` `[Substrate template vX.Y.Z]` section
2. Migration script at `tools/migration/migrate_to_vXYZ.py` — must be idempotent, with a verification block at the end
3. Update `Cover!B8` and every sheet's `AZ4` anchor cell to the new version
4. Bump bundled `ALF_Financial_Analyzer_Only.xlsx` and update SPEC-RR.md / SPEC-T12.md / CLAUDE.md current-version lines

---

## Versioning

Three independent counters: RR app version (`v1.X.Y`), T12 code version (`v0.X.Y`), Analyzer substrate version (`v0.1.N`). Each version stream has its own changelog. Substrate version is stamped on `Cover!B8` and every sheet's `AZ4` anchor cell.

When making a code change in a chat, add an entry to the relevant `CHANGELOG-*.md` in the same commit. See `CLAUDE.md` for the full session-handoff conventions.

---

## Further reading

| Doc | Purpose |
| --- | --- |
| `CLAUDE.md` | Onboarding for any Claude (chat or Claude Code) session — read first |
| `SPEC-RR.md` | Track 1 source of truth: RR parser, writer, sidebar, period-date detection |
| `SPEC-T12.md` | Track 2 source of truth: T12 format registry, writer, Description_Map lookup, UNMATCHED matcher |
| `CHANGELOG-RR.md` / `CHANGELOG-T12.md` | Per-release notes, newest at top |
| `OPTIMIZATION-DECISIONS.md` | Track 3 (Analyzer-only) decisions and roadmap |
| `journal.md` | Per-chat session log — read the top entry before starting a new chat |
