"""
Rent Roll Normalization App — Streamlit entry point.

Run locally:
    streamlit run app.py

Deploy to Streamlit Cloud:
    Push this folder to a GitHub repo and connect at https://streamlit.io/cloud

This entry point orchestrates two normalizer modules that share a destination
workbook:
  - RR Normalizer (Track 1, see SPEC-RR.md) — writes to `Rent Roll Input`
  - T12 Normalizer (Track 2, see SPEC-T12.md) — writes to `T12 Input`

Analyzer template loading (v1.12.0):
  - The bundled `ALF_Financial_Analyzer_Only.xlsx` from the repo root is
    loaded silently as the default destination workbook on every run.
  - Users can override via the "Advanced — override Analyzer template"
    expander at the bottom of the sidebar; uploaded files win when present.
  - The bundled file is the canonical source of `Description_Map` for
    UNMATCHED matching. Resolutions are baked into each download but do
    NOT propagate back to the repo; bundled-file edits go through git.

A single run can produce: standalone Normalized RR workbook + populated
Analyzer with both RR and T12 data, when both required uploads are present.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl
import pandas as pd
import streamlit as st

from auth import require_login
from mappings import MappingSet, load_mapping_workbook
from normalizer import CONDENSED_COLUMNS, normalize_rent_roll
from period_date import detect_period_date
from reports import build_by_type, build_exceptions, build_summary
from t12_normalizer import (
    UnknownT12FormatError,
    parse_t12,
    read_descmap_descriptions,
)
from t12_normalizer_writer import (
    T12NormalizerCapacityError,
    populate_t12_input,
)
from analyzer_rr_translator import translate_for_t12
from analyzer_rr_writer import AnalyzerRRCapacityError, populate_rr_input
from writer import write_output


# ---------------------------------------------------------------------------
# Version constants — independent streams per SPEC-T12 §"How the version
# stream relates to Track 1"
# ---------------------------------------------------------------------------
APP_VERSION = "1.14.0"            # alias for RR_VERSION; kept for back-compat
APP_LAST_UPDATED = "2026-05-08"   # alias for RR_LAST_UPDATED

RR_VERSION = "1.17.5"
RR_LAST_UPDATED = "2026-05-15"

T12_VERSION = "0.2.1"
T12_LAST_UPDATED = "2026-05-11"


# ---------------------------------------------------------------------------
# Bundled Analyzer — loaded silently from repo root by default
# ---------------------------------------------------------------------------
BUNDLED_ANALYZER_PATH = Path(__file__).parent / "ALF_Financial_Analyzer_Only.xlsx"


# ---------------------------------------------------------------------------
# Description_Map dropdown options — sourced from the v0.1.5 substrate
# ---------------------------------------------------------------------------
# Section is bounded; CareType is bounded; Flag has 8 substrate values + blank;
# Label is the existing 55-vocabulary as of v0.1.5 (free-text override allowed
# but discouraged — see SPEC-T12 §"Closed Label vocabulary").
DESCMAP_SECTIONS = ["Revenue", "Labor", "Non-Labor", "Excluded"]
DESCMAP_CARETYPES = ["-", "IL", "AL", "MC"]
DESCMAP_FLAGS = [
    "",  # blank/None default
    "Volatile",
    "Normalize to $0",
    "Normalize at stabilization",
    "Stabilize annually",
    "Flag if >5% of wages",
    "Annualize",
    "Verify assessed value",
    "Normalize to 1-2%",
]


def _build_output_name(source_filename: str) -> str:
    """Build output filename: <source_stem> Normalized YYYY-MM-DD.xlsx"""
    import re
    stem = Path(source_filename).stem
    stem = re.sub(r"\s+Normalized\s+\d{4}-\d{2}-\d{2}\s*$", "", stem, flags=re.IGNORECASE)
    today = dt.date.today().isoformat()
    return f"{stem} Normalized {today}.xlsx"


def _read_descmap_labels(analyzer_bytes: bytes) -> list[str]:
    """Pull the existing Labels from the Analyzer's Description_Map for the
    matcher's Label combobox. Falls back to an empty list on any read error.
    """
    try:
        wb = openpyxl.load_workbook(pd.io.common.BytesIO(analyzer_bytes), data_only=True)
        ws = wb["Description_Map"]
        labels: set[str] = set()
        for r in range(5, ws.max_row + 1):
            v = ws.cell(r, 2).value  # col B = Label
            if v and str(v).strip():
                labels.add(str(v).strip())
        return sorted(labels)
    except Exception:
        return []


def _detect_substrate_version(analyzer_bytes: bytes) -> str:
    """Detect the substrate version of an Analyzer.

    Closes UW-BACKLOG BL-0008. The prior implementation (v1.12.0-v1.17.0)
    only knew the v0.1.4 and v0.1.5 Description_Map markers, so any
    Analyzer at v0.1.6 through v0.1.14 reported as `v0.1.5`. This rewrite
    reads `Cover!B8` (the canonical version stamp set by every migration
    since v0.1.4) as the primary source, then falls back to the legacy
    Label-based heuristic for older Analyzers that predate `Cover!B8` or
    for files where that cell has been damaged.

    Strategy:
        1. Try `Cover!B8`. If it matches `vN.N.N` (any leading-zero
           components allowed), return as-is.
        2. Fall back to substrate-distinctive sentinel cells (in order
           from newest to oldest):
             - Rent Roll Input!AH4 contains "Total" + "Ancillary" → v0.2.2+
             - T12 Raw Data!B16 == "Meal Income" → v0.2.1+
             - Workbook contains "UW Export" sheet → v0.2.0+
             - Rent Roll Recon!I87 contains "Actual" + "PSF" → v0.1.14+
             - T12 Analytics!A168 contains "Reconciliation" → v0.1.14+
             - Rent Roll Input!AC4 contains "Meal Plan" → v0.1.13+
             - Rent Roll Recon!A119 contains "M " → v0.1.12+
             - Rent Roll Input!V4 contains "2nd Person" → v0.1.10+
             - Description_Map contains "2nd Person Revenue" Label → v0.1.5+
             - Description_Map contains "Auto Expense" + "Lease / ground lease" → v0.1.4
        3. If nothing matches: `"pre-v0.1.4"`.

    Returns a string like `"v0.1.14"` or `"(unknown)"` on any read error.
    Used for the sidebar caption only — never gates functionality.
    """
    try:
        wb = openpyxl.load_workbook(pd.io.common.BytesIO(analyzer_bytes), data_only=True)

        # 1. Primary: Cover!B8 stamp (canonical since v0.1.4). Pattern
        # widened in v1.17.3 to accept v0.2.x and any future major/minor —
        # the prior `v0\.1\.\d+` regex misreported v0.2.0 / v0.2.1 because
        # only the patch component was variable.
        try:
            cover_b8 = wb["Cover"]["B8"].value
            if isinstance(cover_b8, str):
                import re
                m = re.match(r"^v\d+\.\d+\.\d+$", cover_b8.strip())
                if m:
                    return cover_b8.strip()
        except Exception:
            pass

        # 2. Fallback: substrate-distinctive sentinel cells (newest → oldest)
        try:
            rri = wb["Rent Roll Input"]
            ah4 = rri.cell(4, 34).value
            if isinstance(ah4, str) and "Total" in ah4 and "Ancillary" in ah4:
                return "v0.2.2+"
        except Exception:
            pass
        try:
            trd = wb["T12 Raw Data"]
            b16 = trd.cell(16, 2).value
            if isinstance(b16, str) and b16.strip() == "Meal Income":
                return "v0.2.1+"
        except Exception:
            pass
        try:
            if "UW Export" in wb.sheetnames:
                return "v0.2.0+"
        except Exception:
            pass
        try:
            rr = wb["Rent Roll Recon"]
            i87 = rr.cell(87, 9).value
            if isinstance(i87, str) and "Actual" in i87 and "PSF" in i87:
                return "v0.1.14+"
        except Exception:
            pass
        try:
            ta = wb["T12 Analytics"]
            a168 = ta.cell(168, 1).value
            if isinstance(a168, str) and "Reconciliation" in a168:
                return "v0.1.14+"
        except Exception:
            pass
        try:
            rri = wb["Rent Roll Input"]
            ac4 = rri.cell(4, 29).value
            if isinstance(ac4, str) and "Meal Plan" in ac4:
                return "v0.1.13+"
        except Exception:
            pass
        try:
            rr = wb["Rent Roll Recon"]
            a119 = rr.cell(119, 1).value
            if isinstance(a119, str) and a119.startswith("M "):
                return "v0.1.12+"
        except Exception:
            pass
        try:
            rri = wb["Rent Roll Input"]
            v4 = rri.cell(4, 22).value
            if isinstance(v4, str) and "2nd Person" in v4:
                return "v0.1.10+"
        except Exception:
            pass

        # 3. Legacy Description_Map Label heuristic (pre-v0.1.10 fallback)
        ws = wb["Description_Map"]
        labels: set[str] = set()
        for r in range(5, ws.max_row + 1):
            v = ws.cell(r, 2).value
            if v and str(v).strip():
                labels.add(str(v).strip())
        if "2nd Person Revenue" in labels:
            return "v0.1.5+"
        if "Auto Expense" in labels and "Lease / ground lease" in labels:
            return "v0.1.4"
        return "pre-v0.1.4"
    except Exception:
        return "(unknown)"


def _load_analyzer(uploaded_file) -> tuple[bytes, str, str]:
    """Resolve the Analyzer source — uploaded file wins over bundled default.

    Returns: (analyzer_bytes, source_label, substrate_version)
      - analyzer_bytes: the raw .xlsx bytes
      - source_label: "uploaded: <filename>" or "bundled (repo)"
      - substrate_version: detected version string (e.g., "v0.1.5")

    Raises FileNotFoundError if neither uploaded file nor bundled file exists.
    """
    if uploaded_file is not None:
        b = uploaded_file.getvalue()
        return b, f"uploaded: {getattr(uploaded_file, 'name', 'analyzer.xlsx')}", _detect_substrate_version(b)
    if BUNDLED_ANALYZER_PATH.exists():
        b = BUNDLED_ANALYZER_PATH.read_bytes()
        return b, "bundled (repo)", _detect_substrate_version(b)
    raise FileNotFoundError(
        f"Bundled Analyzer not found at {BUNDLED_ANALYZER_PATH}. "
        "Either restore the file in the repo root or upload a custom Analyzer "
        "via the Advanced expander in the sidebar."
    )


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Senior Housing Normalizer (RR + T12)",
    page_icon="🏢",
    layout="wide",
)

# Password gate — multi-user, SHA-256 hashes from st.secrets["auth"]["users"].
# Successful logins are printed to stdout (visible in Streamlit Cloud logs).
require_login()

# Title row with version badge on the right.
title_col, version_col = st.columns([5, 1])
with title_col:
    st.title("Rent Roll & T12 Normalizer")
with version_col:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 1.2rem;">
            <span style="
                display: inline-block;
                padding: 4px 12px;
                background-color: #2B2B2B;
                color: #FFFFFF;
                border-radius: 12px;
                font-family: 'Calibri', sans-serif;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.3px;
            ">RR v{RR_VERSION} · T12 v{T12_VERSION}</span>
            <div style="
                color: #888888;
                font-size: 11px;
                margin-top: 4px;
                font-family: 'Calibri', sans-serif;
            ">RR updated {RR_LAST_UPDATED} · T12 updated {T12_LAST_UPDATED}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Upload a senior-housing rent roll. The app detects the header, parses "
    "the parent-apartment / child-bed structure, normalizes to one-row-per-bed, "
    "and produces a 6-tab Excel workbook. Optionally upload a raw T12 to "
    "receive a populated Analyzer with both data sets baked in."
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Inputs")

    rr_file = st.file_uploader(
        "Rent Roll (.xlsx) — required",
        type=["xlsx", "xlsm"],
        help="Any senior housing rent roll. Header doesn't need to be on row 1.",
    )

    auto_detected_date = None
    if rr_file is not None:
        auto_detected_date = detect_period_date(getattr(rr_file, "name", ""))

    period_date_input = st.date_input(
        "Rent Roll Period Date",
        value=auto_detected_date or dt.date.today(),
        help=(
            "Written to column S of the Analyzer's Rent Roll Input sheet on "
            "every row. Auto-detected from the rent roll filename when "
            "possible. Override if needed."
        ),
    )
    if auto_detected_date:
        st.caption(f"Auto-detected from filename: **{auto_detected_date.isoformat()}**")
    elif rr_file is not None:
        st.caption("Could not auto-detect a date from the filename — set manually.")

    raw_t12_file = st.file_uploader(
        "Raw T12 (.xlsx) — optional",
        type=["xlsx", "xlsm"],
        key="raw_t12_uploader",
        help=(
            "Optional. Upload a raw T12 export from Yardi (Income to Budget), "
            "MRI (R12MINCS), or a broker Financial Summary (`Historical "
            "Performance` header at A4). The app parses it, detects month "
            "labels, applies drop-rules, and writes the GL detail into the "
            "Analyzer's 'T12 Input' sheet. Mappings for any UNMATCHED "
            "descriptions can be filled in below before download."
        ),
    )

    # Cluster B (T12 v0.2.0): annualize toggle for partial-year T12 files. The
    # parser reads the value below; default OFF surfaces a warning instead of
    # silently scaling. Disabled in UI when no T12 is uploaded.
    annualize_partial_year = st.checkbox(
        "Annualize partial-year T12",
        value=False,
        key="annualize_partial_year",
        disabled=raw_t12_file is None,
        help=(
            "When the uploaded T12 covers fewer than 12 months, multiply every "
            "monthly value by 12/N (where N is months populated). Off by "
            "default — partial-year T12s surface as a warning so you decide "
            "explicitly. Use with caution: assumes flat seasonality."
        ),
    )

    st.divider()
    st.subheader("Property Defaults")
    care_type_default = st.selectbox(
        "Care Type",
        options=["(none — flag missing)", "IL", "AL", "MC"],
        index=0,
        help=(
            "Applied when the rent roll source has no Care Type / Wing / "
            "Building column. For single-care-setting properties (e.g., a "
            "100% AL building) this fills in the Care Type for every bed. "
            "Source values always win — explicit Care Type columns in the "
            "rent roll override this default."
        ),
    )
    if care_type_default.startswith("("):
        care_type_default = ""

    st.divider()
    st.subheader("Optional")
    mapping_file = st.file_uploader(
        "Rent Roll Mapping (.xlsx)",
        type=["xlsx"],
        help=(
            "Override defaults for Apartment_Type_Rules, Bed_Status_Rules, "
            "Payer_Type_Rules, Care_Level_Rules, Care_Bucket_Rules. "
            "Any sheet you omit falls back to built-in defaults."
        ),
    )

    st.divider()
    st.subheader("Output")
    sheet_override = st.text_input(
        "Sheet name (leave blank to auto-detect)",
        value="",
        help="Defaults to 'Details' if present, otherwise the first sheet.",
    )

    st.divider()
    with st.expander("Advanced — override Analyzer template"):
        st.caption(
            "By default the app uses the bundled Analyzer (`ALF_Financial_"
            "Analyzer_Only.xlsx` in the repo root). Upload a custom Analyzer "
            "here to override for this session only — uploads do not modify "
            "the bundled file."
        )
        analyzer_override_file = st.file_uploader(
            "ALF Financial Analyzer (.xlsx)",
            type=["xlsx"],
            key="analyzer_override_uploader",
        )

    st.divider()
    st.caption(f"RR v{RR_VERSION} · T12 v{T12_VERSION}")


# ---------------------------------------------------------------------------
# Resolve Analyzer source — bundled by default, override wins when present
# ---------------------------------------------------------------------------
try:
    analyzer_bytes_cached, analyzer_source_label, analyzer_substrate_ver = _load_analyzer(
        analyzer_override_file
    )
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()


# ---------------------------------------------------------------------------
# Main — empty state
# ---------------------------------------------------------------------------
if rr_file is None:
    st.info(f"Using Analyzer: **{analyzer_source_label}** (substrate {analyzer_substrate_ver}). Upload a rent roll to begin.")
    with st.expander("What the app does"):
        st.markdown(
            """
            **Track 1 — Rent Roll Normalizer**

            - Detects the header row in the first ~20 rows.
            - Parses parent-apartment / child-bed layouts: apartment rows
              establish context, child rows become normalized beds.
            - Auto-groups care charges by header prefix. Recognized buckets
              (AL, Med Mgmt, Pharmacy) get their own columns; others roll
              into **Other LOC $**.
            - Normalizes apt type, bed status, payer type, and care level.
            - Preserves vacant beds.
            - Exports a 6-tab Excel.

            **Track 2 — T12 Normalizer** *(new in T12 v0.1.0)*

            - Detects T12 format (Yardi `Income to Budget`, MRI `R12MINCS`).
            - Reads month labels from the source and normalizes to `MMM YYYY`.
            - Drops grand-total rows and explicit non-operating lines.
            - Writes GL detail to the Analyzer's `T12 Input` sheet.
            - Surfaces UNMATCHED descriptions for in-app mapping; new
              mappings persist in your downloaded Analyzer.

            **Combined output:** When you upload a rent roll plus a raw T12,
            you get a single populated Analyzer with both data sets, plus
            any new mappings you supplied through the matcher form.

            **Analyzer source:** The app uses the bundled Analyzer
            (`ALF_Financial_Analyzer_Only.xlsx`) by default. To use a
            different Analyzer for one session, expand
            "Advanced — override Analyzer template" in the sidebar.
            """
        )
    st.stop()


# ---------------------------------------------------------------------------
# Process — Rent Roll
# ---------------------------------------------------------------------------
try:
    mappings = load_mapping_workbook(mapping_file) if mapping_file else MappingSet()
    result = normalize_rent_roll(
        rr_file,
        sheet_name=sheet_override.strip() or None,
        mappings=mappings,
        property_care_type_default=care_type_default or None,
    )
except Exception as e:
    st.error(f"Failed to process rent roll: {e}")
    st.stop()

n = result.normalized
c = result.condensed

if n.empty:
    st.warning(
        "No bed rows detected. Check that the file has a parent-apartment / "
        "child-bed layout and that 'Bed' (or a similar column) identifies "
        "child rows."
    )
    st.stop()

summary    = build_summary(n)
by_type    = build_by_type(n)
exceptions = build_exceptions(n, result.unmapped)


# ---------------------------------------------------------------------------
# Process — T12 (if uploaded)
# ---------------------------------------------------------------------------
# T12 parsing requires the Analyzer's Description_Map. Since the Analyzer is
# always available now (bundled default + optional override), T12 parsing
# proceeds whenever a raw T12 is uploaded — no Analyzer-upload prerequisite.
t12_parse_result = None
t12_parse_error = None
descmap_labels_cached: list[str] = []

if raw_t12_file is not None:
    try:
        analyzer_wb_for_descmap = openpyxl.load_workbook(
            pd.io.common.BytesIO(analyzer_bytes_cached), data_only=True
        )
        descmap = read_descmap_descriptions(analyzer_wb_for_descmap)
        descmap_labels_cached = _read_descmap_labels(analyzer_bytes_cached)
        t12_parse_result = parse_t12(
            raw_t12_file.getvalue(),
            descmap,
            annualize_partial_year=annualize_partial_year,
        )
    except UnknownT12FormatError as e:
        t12_parse_error = (
            f"T12 format not recognized: {e}\n\n"
            "Currently supported: Yardi (Income to Budget), MRI (R12MINCS), "
            "Broker Financial Summary (`Historical Performance` header at A4). "
            "Adding a new format requires extending the format-registry in "
            "t12_normalizer.py — see SPEC-T12.md §\"Parser data flow\"."
        )
    except ValueError as e:
        t12_parse_error = f"T12 parse error: {e}"
    except Exception as e:
        t12_parse_error = f"Could not parse T12: {e}"


# ---------------------------------------------------------------------------
# UNMATCHED matcher form — session-state driven
# ---------------------------------------------------------------------------
if "t12_resolutions" not in st.session_state:
    st.session_state.t12_resolutions = {}

unresolved_descriptions: list[str] = []
if t12_parse_result is not None:
    unresolved_descriptions = [
        d for d in t12_parse_result.unmatched
        if d not in st.session_state.t12_resolutions
    ]


# ---------------------------------------------------------------------------
# Headline KPIs
# ---------------------------------------------------------------------------
colA, colB, colC, colD, colE = st.columns(5)
total_beds = len(n)
occ_beds = int((n["Status"] == "Occupied").sum())
colA.metric("Total Beds", total_beds)
colB.metric("Occupied", occ_beds)
colC.metric(
    "Bed Occupancy",
    f"{100*occ_beds/total_beds:.1f}%" if total_beds else "0.0%",
)
colD.metric(
    "Avg Actual (occ)",
    f"${n.loc[n['Status']=='Occupied','Actual Rate'].mean():,.0f}" if occ_beds else "$0",
)
colE.metric("In-Place Monthly Rev", f"${n['Total Monthly Revenue'].sum():,.0f}")

st.caption(
    f"Header detected on row {result.header_row_idx + 1} (1-indexed). "
    f"{len(result.care_groups)} care/ancillary column group(s) identified. "
    f"Analyzer: {analyzer_source_label} (substrate {analyzer_substrate_ver})."
)

if result.property_care_type_default:
    default_count = int((n["Care Type Source"] == "Property Default").sum())
    source_count = int((n["Care Type Source"] == "Source").sum())
    st.info(
        f"**Property Care Type default applied: {result.property_care_type_default}** — "
        f"used for {default_count} bed(s) where source had no Care Type. "
        f"{source_count} bed(s) used an explicit source value."
    )


# ---------------------------------------------------------------------------
# T12 status panel (only when relevant)
# ---------------------------------------------------------------------------
if raw_t12_file is not None:
    st.divider()
    st.subheader("T12 Normalizer")
    if t12_parse_error is not None:
        st.error(t12_parse_error)
    elif t12_parse_result is not None:
        # 5-column layout (was 4, with a duplicate-tc bug). Each metric in its
        # own column so all five display.
        ta, tb, tc, td, te = st.columns(5)
        ta.metric("Format", t12_parse_result.format_name)
        tb.metric("GL Rows Extracted", len(t12_parse_result.gl_rows))
        # Use the most-recent populated label as period. Partial-year files may
        # have leading "" labels (padded); skip those when picking display.
        labels = [lbl for lbl in t12_parse_result.month_labels if lbl]
        first_label = labels[0] if labels else "—"
        last_label = labels[-1] if labels else "—"
        tc.metric("Period (first month)", first_label)
        td.metric("Period (last month)", last_label)
        te.metric(
            "UNMATCHED",
            len(t12_parse_result.unmatched),
            help="Descriptions not found in the Analyzer's Description_Map.",
        )

        # Cluster B (B-2): partial-year detection. Surface as a warning when
        # < 12 months are populated. Annualization (if requested in the sidebar)
        # has already been applied by parse_t12; the warning text reflects that.
        if t12_parse_result.populated_months < 12:
            n = t12_parse_result.populated_months
            if t12_parse_result.was_annualized:
                st.warning(
                    f"⚠ T12 is partial-year ({n} months populated). Values were "
                    f"scaled by 12/{n} per the sidebar checkbox. Ratios assume "
                    f"flat seasonality — review against rent roll occupancy."
                )
            else:
                st.warning(
                    f"⚠ T12 is partial-year ({n} months populated). Ratios will "
                    f"be misleading without annualization. Toggle "
                    f"'Annualize partial-year T12' in the sidebar to scale "
                    f"values by 12/{n}, or proceed knowing downstream metrics "
                    f"reflect a {n}-month period."
                )

        # Cluster B (B-1): sign-convention guards. Defensive — none of the
        # current verified fixtures trip these on standard signs.
        for warning in t12_parse_result.sign_warnings:
            st.warning(warning)

        if t12_parse_result.unmatched:
            n_resolved = len(t12_parse_result.unmatched) - len(unresolved_descriptions)
            if unresolved_descriptions:
                st.warning(
                    f"⚠️ {len(unresolved_descriptions)} description(s) need mapping "
                    f"before the combined Analyzer download is enabled. "
                    f"({n_resolved} already resolved this session.)"
                )

                with st.form("unmatched_matcher", clear_on_submit=False):
                    st.markdown(
                        "**Map these descriptions before download.** Mappings "
                        "will be appended to your Analyzer's Description_Map "
                        "and persist for future uploads of the same operator."
                    )
                    new_resolutions: dict[str, dict] = {}

                    for i, desc in enumerate(unresolved_descriptions):
                        st.markdown(f"**{desc}**")
                        c1, c2, c3, c4 = st.columns([3, 2, 1, 2])
                        with c1:
                            label_options = ["(select…)"] + descmap_labels_cached
                            chosen_label = st.selectbox(
                                "Label",
                                options=label_options,
                                key=f"label_{i}",
                                label_visibility="collapsed",
                            )
                        with c2:
                            chosen_section = st.selectbox(
                                "Section",
                                options=["(select…)"] + DESCMAP_SECTIONS,
                                key=f"section_{i}",
                                label_visibility="collapsed",
                            )
                        with c3:
                            chosen_caretype = st.selectbox(
                                "Care",
                                options=DESCMAP_CARETYPES,
                                index=0,
                                key=f"caretype_{i}",
                                label_visibility="collapsed",
                            )
                        with c4:
                            chosen_flag = st.selectbox(
                                "Flag",
                                options=DESCMAP_FLAGS,
                                index=0,
                                key=f"flag_{i}",
                                label_visibility="collapsed",
                            )
                        new_resolutions[desc] = {
                            "description": desc,
                            "label": None if chosen_label == "(select…)" else chosen_label,
                            "section": None if chosen_section == "(select…)" else chosen_section,
                            "caretype": chosen_caretype,
                            "flag": chosen_flag or None,
                        }

                    submitted = st.form_submit_button(
                        "✓ Apply mappings & enable download",
                        use_container_width=True,
                    )
                    if submitted:
                        bad = [
                            d for d, m in new_resolutions.items()
                            if not m["label"] or not m["section"]
                        ]
                        if bad:
                            st.error(
                                f"Each row needs a Label and Section. Missing: "
                                f"{', '.join(bad[:3])}"
                                f"{'…' if len(bad) > 3 else ''}"
                            )
                        else:
                            st.session_state.t12_resolutions.update(new_resolutions)
                            st.rerun()
            else:
                st.success(
                    f"✓ All {len(t12_parse_result.unmatched)} UNMATCHED descriptions "
                    "resolved. Combined Analyzer download is enabled."
                )
        else:
            st.success("✓ Zero UNMATCHED — every description in the T12 already "
                       "maps to a Label.")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
st.divider()
tab_condensed, tab_full, tab_summary, tab_bytype, tab_excep, tab_audit = st.tabs([
    "Condensed RR",
    "Normalized (full)",
    "Summary",
    "By Type",
    "Exceptions",
    "Mapping Audit",
])

with tab_condensed:
    st.subheader("Condensed RR — underwriting view")
    st.caption(
        "Filter and sort columns before exporting. Use the three-dot menu on "
        "any column header to sort. Use the search box above the table to filter."
    )
    st.dataframe(
        c,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Market Rate":   st.column_config.NumberColumn(format="$%.0f"),
            "Actual Rate":   st.column_config.NumberColumn(format="$%.0f"),
            "Concession $":  st.column_config.NumberColumn(format="$%.0f"),
            "Care Level $":  st.column_config.NumberColumn(format="$%.0f"),
            "Med Mgmt $":    st.column_config.NumberColumn(format="$%.0f"),
            "Pharmacy $":    st.column_config.NumberColumn(format="$%.0f"),
            "Other LOC $":   st.column_config.NumberColumn(format="$%.0f"),
        },
    )

with tab_full:
    st.subheader("Normalized_Beds — full detail")
    st.dataframe(n, use_container_width=True, hide_index=True)

with tab_summary:
    st.subheader("RR_Summary — KPIs")
    st.dataframe(summary, use_container_width=True, hide_index=True)

with tab_bytype:
    st.subheader("RR_By_Type — mix analysis")
    st.dataframe(by_type, use_container_width=True, hide_index=True)

with tab_excep:
    st.subheader("RR_Exceptions — rows needing review")
    if exceptions.empty:
        st.success("No exceptions flagged.")
    else:
        st.warning(f"{len(exceptions)} issue(s) flagged.")
        st.dataframe(exceptions, use_container_width=True, hide_index=True)

with tab_audit:
    st.subheader("Mapping_Reference — how source columns were classified")
    st.dataframe(result.mapping_audit, use_container_width=True, hide_index=True)
    with st.expander("Detected source headers"):
        st.write(result.source_headers)
    with st.expander("Unmapped values (add to your mapping workbook to clean up)"):
        st.json(result.unmapped)


# ---------------------------------------------------------------------------
# Download buttons
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Export")

run_meta = {
    "RR Version":          RR_VERSION,
    "RR Last Updated":     RR_LAST_UPDATED,
    "T12 Version":         T12_VERSION,
    "T12 Last Updated":    T12_LAST_UPDATED,
    "Run Timestamp":       dt.datetime.now().isoformat(timespec="seconds"),
    "Source File":         getattr(rr_file, "name", "uploaded"),
    "Mapping File":        getattr(mapping_file, "name", "(defaults only)"),
    "Analyzer Source":     analyzer_source_label,
    "Analyzer Substrate":  analyzer_substrate_ver,
    "Property Care Type Default": result.property_care_type_default or "(none)",
    "Header Row (1-idx)":  result.header_row_idx + 1,
    "Care Groups Detected": len(result.care_groups),
    "Total Beds":          len(n),
    "Occupied Beds":       occ_beds,
    "T12 File":            getattr(raw_t12_file, "name", "(not uploaded)"),
    "T12 Format Detected": t12_parse_result.format_name if t12_parse_result else "(n/a)",
    "T12 GL Rows":         len(t12_parse_result.gl_rows) if t12_parse_result else 0,
}

xlsx_bytes = write_output(
    condensed=c,
    normalized=n,
    mapping_audit=result.mapping_audit,
    summary=summary,
    by_type=by_type,
    exceptions=exceptions,
    run_metadata=run_meta,
)

out_name = _build_output_name(getattr(rr_file, "name", "rent_roll.xlsx"))

dl_col1, dl_col2 = st.columns(2)

# --- Download 1: Standalone Normalized Rent Roll (always available) ---
with dl_col1:
    st.markdown("**Normalized Rent Roll**")
    st.caption("6-tab analyst workbook with formatting.")
    st.download_button(
        label=f"⬇️ Download {out_name}",
        data=xlsx_bytes,
        file_name=out_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="dl_rr",
    )

# --- Download 2: Combined Analyzer (RR + optional T12) ---
with dl_col2:
    st.markdown("**Analyzer with data**")

    # Gating: rent roll always required. T12 is optional. If T12 is uploaded,
    # all UNMATCHED descriptions must be resolved before download.
    has_t12 = raw_t12_file is not None
    t12_parsed_ok = t12_parse_result is not None
    t12_unmatched_remaining = (
        len([
            d for d in t12_parse_result.unmatched
            if d not in st.session_state.t12_resolutions
        ]) if t12_parsed_ok else 0
    )
    t12_blocking = has_t12 and (not t12_parsed_ok or t12_unmatched_remaining > 0)

    can_download = rr_file is not None and not t12_blocking

    if t12_blocking:
        if not t12_parsed_ok:
            st.caption("T12 parse failed — see error above.")
        else:
            st.caption(f"Resolve {t12_unmatched_remaining} UNMATCHED description(s) above to enable.")
    else:
        t12_caption = (
            f"T12 data → `T12 Input!A12+`. " if has_t12 else ""
        )
        st.caption(
            f"RR data → `Rent Roll Input!A7+`. "
            f"{t12_caption}"
            f"Period {period_date_input.isoformat()} written to RR col S."
        )

    if can_download:
        try:
            # Step 1: Write RR data into the resolved Analyzer.
            translated = translate_for_t12(c)
            populated_after_rr = populate_rr_input(
                analyzer_bytes_cached,
                translated,
                period_date_input,
                source_filename=getattr(rr_file, "name", ""),
            )

            # Step 2: If T12 was uploaded, append session-state UNMATCHED
            # resolutions and write GL detail on top of the RR-populated Analyzer.
            if has_t12 and t12_parse_result is not None:
                new_descmap_entries = list(st.session_state.t12_resolutions.values())
                final_bytes = populate_t12_input(
                    populated_after_rr,
                    t12_parse_result,
                    new_descmap_entries=new_descmap_entries,
                    source_filename=getattr(raw_t12_file, "name", "raw_t12.xlsx"),
                    t12_version=T12_VERSION,
                    t12_last_updated=T12_LAST_UPDATED,
                )
            else:
                final_bytes = populated_after_rr

            rr_stem = Path(getattr(rr_file, "name", "rent_roll.xlsx")).stem
            if has_t12:
                t12_stem = Path(getattr(raw_t12_file, "name", "raw_t12.xlsx")).stem
                combined_out_name = (
                    f"Analyzer with {rr_stem} + {t12_stem} "
                    f"{period_date_input.isoformat()}.xlsx"
                )
            else:
                combined_out_name = (
                    f"Analyzer with {rr_stem} "
                    f"{period_date_input.isoformat()}.xlsx"
                )

            st.download_button(
                label=f"⬇️ Download {combined_out_name[:60]}{'…' if len(combined_out_name) > 60 else ''}",
                data=final_bytes,
                file_name=combined_out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_combined",
            )
        except AnalyzerRRCapacityError as e:
            st.error(f"Rent Roll exceeds Analyzer capacity: {e}")
        except T12NormalizerCapacityError as e:
            st.error(f"T12 exceeds Analyzer capacity: {e}")
        except ValueError as e:
            st.error(f"Analyzer / T12 error: {e}")
        except Exception as e:
            st.error(f"Could not produce combined output: {e}")
    else:
        st.button(
            "⬇️ Combined download not yet available",
            disabled=True,
            use_container_width=True,
            key="dl_combined_disabled",
        )
