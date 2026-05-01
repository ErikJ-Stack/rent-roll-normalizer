# Rent Roll Normalizer

A Streamlit app that turns senior-housing rent rolls (any operator format) into
a normalized, bed-level Excel workbook ready for underwriting analysis.

## What it does

- **Detects the header row** in the first ~20 rows — no need for row 1 to be the header.
- **Parses parent-apartment / child-bed layouts** — apartment rows set context,
  bed rows become normalized records.
- **Groups care/ancillary columns** automatically. Known buckets (AL, Med Mgmt,
  Pharmacy) get their own columns; anything else auto-catches into **Other LOC $**
  so revenue never gets dropped when a new operator format shows up.
- **Normalizes** apartment type, bed status, payer type, and care level through a
  pluggable mapping workbook (defaults included).
- **Preserves vacant beds** so occupancy math stays honest.
- **Exports** a 6-tab Excel:
  - `Condensed_RR` — the 18-column analyst view (Unit #, Room #, Sq Ft, Care Type,
    Status, Apt Type, Market Rate, Actual Rate, Concession $, Concession End Date,
    Care Level, Care Level $, Med Mgmt $, Pharmacy $, Other LOC $, Payer Type,
    Move-in Date, Resident Name).
  - `Normalized_Beds` — full detail with both raw and normalized fields.
  - `RR_Summary` — inventory / occupancy / pricing / revenue / mix KPIs.
  - `RR_By_Type` — counts and revenue by apt type, care type, payer, status.
  - `RR_Exceptions` — vacant-with-name, occupied-no-rate, unmapped values, etc.
  - `Mapping_Reference` — audit trail of how source columns were classified.
  - `Run_Info` — app version, run timestamp, source file, header row found.

## Project layout

```
rent_roll_app/
├── app.py                  # Streamlit UI
├── normalizer.py           # Header detect + parent-child parse + care grouping
├── mappings.py             # Default mapping rules + mapping workbook loader
├── reports.py              # Summary / By_Type / Exceptions builders
├── writer.py               # Excel output writer
├── mapping_template.xlsx   # Editable override template (optional upload)
├── requirements.txt
└── README.md
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Deploy to Streamlit Community Cloud (free)

1. **Put this folder in a GitHub repo** (public or private).
   ```bash
   cd rent_roll_app
   git init && git add . && git commit -m "Initial commit"
   gh repo create rent-roll-normalizer --private --source=. --push
   ```
2. Go to **https://streamlit.io/cloud** and sign in with GitHub.
3. Click **New app**, select your repo, branch `main`, and main file `app.py`.
4. Click **Deploy**. You'll get a URL like `https://rent-roll-normalizer.streamlit.app`.
5. (Optional) Under **Settings → Sharing**, restrict to specific emails so the
   app isn't public.

The app runs on Streamlit's free tier. No server maintenance, no credit card.

## How to extend

- **New operator format?** Usually nothing to change — the header detector and
  care-bucket auto-catch handle most cases. If a new care-charge column shows up
  consistently, add a rule to `Care_Bucket_Rules` in your mapping workbook so it
  gets its own line instead of flowing to Other LOC $.
- **New normalized field?** Add it to `normalizer.py` in the bed-record dict and,
  if it should appear in the condensed view, also in `CONDENSED_COLUMNS` and the
  dict in the condensed builder.
- **New report tab?** Add a builder to `reports.py` and wire it through `app.py`
  and `writer.py`.
- **T-12 intake?** Recommended architecture is a separate module/app with the
  same shape, then a merged "UW Intake" sheet that reconciles RR in-place GPR
  against T-12 collected revenue. Keeps variance visible.
