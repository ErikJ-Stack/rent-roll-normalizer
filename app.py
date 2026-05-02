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

A single run can produce: standalone Normalized RR workbook + populated
Analyzer with both RR and T12 data, when both required uploads are present.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl
import pandas as pd
import streamlit as st

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
from t12_translator import translate_for_t12
from t12_writer import T12CapacityError, populate_t12
from writer import write_output


# ─────────────────────────────────────────────────────────────────────────────
# Version constants — independent streams per SPEC-T12 §"How the version
# stream relates to Track 1"
# ─────────────────────────────────────────────────────────────────────────────
APP_VERSION = "1.11.0"            # alias for RR_VERSION; kept for back-compat
APP_LAST_UPDATED = "2026-05-01"   # alias for RR_LAST_UPDATED

RR_VERSION = "1.11.0"
RR_LAST_UPDATED = "2026-05-01"

T12_VERSION = "0.1.1"
T12_LAST_UPDATED = "2026-05-02"


# ─────────────────────────────────────────────────────────────────────────────
# Description_Map dropdown options — sourced from the v0.1.4 substrate
# ─────────────────────────────────────────────────────────────────────────────
# Section is bounded; CareType is bounded; Flag has 8 substrate values + blank;
# Label is the existing 54-vocabulary (free-text override allowed but discouraged).
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
    """Pull the existing 54 Labels from the Analyzer's Description_Map for the
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


# ─────────────────────────────────────────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Senior Housing Normalizer (RR + T12)",
    page_icon="🏢",
    layout="wide",
)

# Title row with version badge on the right.
# Version pill shows both versions; per SPEC-T12, T12 portion lights up only
# when T12 actually ran. We render both unconditionally because the constants
# are static and the user appreciates seeing what's available.
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
    "and produces a 6-tab Excel workbook. Optionally upload your ALF Financial "
    "Analyzer plus a raw T12 to receive a populated Analyzer with both data sets."
)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Inputs")

    rr_file = st.file_uploader(
        "Rent Roll (.xlsx) — required",
        type=["xlsx", "xlsm"],
        help="Any senior housing rent roll. Header doesn't need to be on row 1.",
    )

    mapping_file = st.file_uploader(
        "Mapping workbook (.xlsx) — optional",
        type=["xlsx"],
        help=(
            "Override defaults for Apartment_Type_Rules, Bed_Status_Rules, "
            "Payer_Type_Rules, Care_Level_Rules, Care_Bucket_Rules. "
            "Any sheet you omit falls back to built-in defaults."
        ),
    )

    st.divider()
    sheet_override = st.text_input(
        "Sheet name (leave blank to auto-detect)",
        value="",
        help="Defaults to 'Details' if present, otherwise the first sheet.",
    )

    st.divider()
    st.subheader("Property defaults")
    care_type_default = st.selectbox(
        "Property Care Type (applied when source has no Care Type column)",
        options=["(none — flag missing)", "IL", "AL", "MC"],
        index=0,
        help=(
            "If the rent roll has no Care Type / Wing / Building column, every "
            "occupied bed is normally flagged as missing Care Type. Use this "
            "for single-care-setting properties (e.g., a 100% AL building) to "
            "apply one value to all beds. Source values always win — explicit "
            "Care Type columns in the rent roll override this default."
        ),
    )
    if care_type_default.startswith("("):
        care_type_default = ""

    st.divider()
    st.subheader("Analyzer integration (optional)")

    t12_file = st.file_uploader(
        "ALF Financial Analyzer (.xlsx)",
        type=["xlsx"],
        key="t12_uploader",
        help=(
            "Optional. Upload your ALF Financial Analyzer workbook to receive a "
            "populated copy with rent roll data in 'Rent Roll Input' and (if "
            "you also upload a raw T12 below) GL detail in 'T12 Input'."
        ),
    )

    raw_t12_file = st.file_uploader(
        "Raw T12 (.xlsx) — optional",
        type=["xlsx", "xlsm"],
        key="raw_t12_uploader",
        help=(
            "Optional. Upload a raw T12 export from Yardi (Income to Budget) or "
            "MRI (R12MINCS). The app parses it, detects month labels, applies "
            "drop-rules, and writes the GL detail into your Analyzer's "
            "'T12 Input' sheet. Mappings for any UNMATCHED descriptions can be "
            "filled in below before download."
        ),
    )

    auto_detected_date = None
    if rr_file is not None:
        auto_detected_date = detect_period_date(getattr(rr_file, "name", ""))

    period_date_input = st.date_input(
        "Rent Roll Period Date (for Analyzer col S)",
        value=auto_detected_date or dt.date.today(),
        help=(
            "Written to column S of the Analyzer's Rent Roll Input sheet on every "
            "row. Auto-detected from the rent roll filename when possible. "
            "Override if needed."
        ),
    )
    if auto_detected_date:
        st.caption(f"Auto-detected from filename: **{auto_detected_date.isoformat()}**")
    elif rr_file is not None:
        st.caption("Could not auto-detect a date from the filename — set manually.")

    st.divider()
    st.caption(f"RR v{RR_VERSION} · T12 v{T12_VERSION}")


# ─────────────────────────────────────────────────────────────────────────────
# Main — empty state
# ─────────────────────────────────────────────────────────────────────────────
if rr_file is None:
    st.info("Upload a rent roll to begin.")
    with st.expander("What the app does"):
        st.markdown(
            """
            **Track 1 — Rent Roll Normalizer**

            - Detects the header row in the first ~20 rows.
            - Parses parent-apartment / child-bed layouts: apartment rows establish
              context, child rows become normalized beds.
            - Auto-groups care charges by header prefix. Recognized buckets
              (AL, Med Mgmt, Pharmacy) get their own columns; others roll into
              **Other LOC $**.
            - Normalizes apt type, bed status, payer type, and care level.
            - Preserves vacant beds.
            - Exports a 6-tab Excel.

            **Track 2 — T12 Normalizer** *(new in T12 v0.1.0)*

            - Detects T12 format (Yardi `Income to Budget`, MRI `R12MINCS`).
            - Reads month labels from the source and normalizes to `MMM YYYY`.
            - Drops grand-total rows and explicit non-operating lines.
            - Writes GL detail to your Analyzer's `T12 Input` sheet.
            - Surfaces UNMATCHED descriptions for in-app mapping; new mappings
              persist in your downloaded Analyzer.

            **Combined output:** When you upload a rent roll, an Analyzer, and a
            raw T12, you get a single populated Analyzer with both data sets plus
            any new mappings you supplied.
            """
        )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Process — Rent Roll
# ─────────────────────────────────────────────────────────────────────────────
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
        "No bed rows detected. Check that the file has a parent-apartment / child-bed "
        "layout and that 'Bed' (or a similar column) identifies child rows."
    )
    st.stop()

summary    = build_summary(n)
by_type    = build_by_type(n)
exceptions = build_exceptions(n, result.unmapped)


# ─────────────────────────────────────────────────────────────────────────────
# Process — T12 (if uploaded AND Analyzer also uploaded — descmap lives there)
# ─────────────────────────────────────────────────────────────────────────────
t12_parse_result = None
t12_parse_error = None
analyzer_bytes_cached: bytes | None = None
descmap_labels_cached: list[str] = []

# T12 parsing requires the Analyzer because Description_Map (the source of
# truth for matching) lives in the Analyzer. If the user uploaded a raw T12
# but not an Analyzer, we surface an explanatory message rather than parsing
# blind.
if raw_t12_file is not None and t12_file is not None:
    try:
        analyzer_bytes_cached = t12_file.getvalue()
        analyzer_wb_for_descmap = openpyxl.load_workbook(
            pd.io.common.BytesIO(analyzer_bytes_cached), data_only=True
        )
        descmap = read_descmap_descriptions(analyzer_wb_for_descmap)
        descmap_labels_cached = _read_descmap_labels(analyzer_bytes_cached)
        t12_parse_result = parse_t12(raw_t12_file.getvalue(), descmap)
    except UnknownT12FormatError as e:
        t12_parse_error = (
            f"T12 format not recognized: {e}\n\n"
            "Currently supported: Yardi (Income to Budget), MRI (R12MINCS). "
            "Adding a new format requires extending the format-registry in "
            "t12_normalizer.py — see SPEC-T12.md §\"Parser data flow\"."
        )
    except ValueError as e:
        t12_parse_error = f"T12 parse error: {e}"
    except Exception as e:
        t12_parse_error = f"Could not parse T12: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# UNMATCHED matcher form — session-state driven
# ─────────────────────────────────────────────────────────────────────────────
# Resolutions persist across reruns, keyed by description string. When the
# user uploads a different T12 with different unmatched descriptions, the
# unrelated keys naturally fall out of `unresolved`.
if "t12_resolutions" not in st.session_state:
    st.session_state.t12_resolutions = {}

unresolved_descriptions: list[str] = []
if t12_parse_result is not None:
    unresolved_descriptions = [
        d for d in t12_parse_result.unmatched
        if d not in st.session_state.t12_resolutions
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Headline KPIs
# ─────────────────────────────────────────────────────────────────────────────
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
    f"{len(result.care_groups)} care/ancillary column group(s) identified."
)

if result.property_care_type_default:
    default_count = int((n["Care Type Source"] == "Property Default").sum())
    source_count = int((n["Care Type Source"] == "Source").sum())
    st.info(
        f"**Property Care Type default applied: {result.property_care_type_default}** — "
        f"used for {default_count} bed(s) where source had no Care Type. "
        f"{source_count} bed(s) used an explicit source value."
    )


# ─────────────────────────────────────────────────────────────────────────────
# T12 status panel (only when relevant)
# ─────────────────────────────────────────────────────────────────────────────
if raw_t12_file is not None:
    st.divider()
    st.subheader("T12 Normalizer")
    if t12_parse_error is not None:
        st.error(t12_parse_error)
    elif t12_file is None:
        st.info(
            "Raw T12 uploaded, but no Analyzer uploaded. The T12 parser needs "
            "the Analyzer's Description_Map to detect UNMATCHED rows. Upload "
            "your Analyzer in the sidebar."
        )
    elif t12_parse_result is not None:
        ta, tb, tc, td = st.columns(4)
        ta.metric("Format", t12_parse_result.format_name)
        tb.metric("GL Rows Extracted", len(t12_parse_result.gl_rows))
        tc.metric("Period (first month)", t12_parse_result.month_labels[0])
        tc.metric("Period (last month)",  t12_parse_result.month_labels[-1])
        td.metric(
            "UNMATCHED",
            len(t12_parse_result.unmatched),
            help="Descriptions not found in the Analyzer's Description_Map.",
        )

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
                        # Validate that every unresolved row has Label + Section
                        # (CareType defaults to "-", Flag is optional).
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


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
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
        "Filter and sort columns before exporting. Use the three-dot menu on any "
        "column header to sort. Use the search box above the table to filter."
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


# ─────────────────────────────────────────────────────────────────────────────
# Download buttons
# ─────────────────────────────────────────────────────────────────────────────
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
        label=f"⬇️  Download {out_name}",
        data=xlsx_bytes,
        file_name=out_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="dl_rr",
    )

# --- Download 2: Combined Analyzer (RR + T12) ---
with dl_col2:
    st.markdown("**Analyzer with both data**")

    # Gating per SPEC-T12 §"How the analyst uses the app"
    has_analyzer = t12_file is not None
    has_t12 = raw_t12_file is not None
    t12_parsed_ok = t12_parse_result is not None
    all_unmatched_resolved = (
        t12_parsed_ok
        and len([
            d for d in t12_parse_result.unmatched
            if d not in st.session_state.t12_resolutions
        ]) == 0
    )

    can_download = (
        rr_file is not None
        and has_analyzer
        and has_t12
        and t12_parsed_ok
        and all_unmatched_resolved
    )

    if not has_analyzer:
        st.caption("Upload an ALF Financial Analyzer in the sidebar to enable.")
    elif not has_t12:
        st.caption("Upload a raw T12 in the sidebar to enable.")
    elif not t12_parsed_ok:
        st.caption("T12 parse failed — see error above.")
    elif not all_unmatched_resolved:
        n_remaining = len([
            d for d in t12_parse_result.unmatched
            if d not in st.session_state.t12_resolutions
        ])
        st.caption(f"Resolve {n_remaining} UNMATCHED description(s) above to enable.")
    else:
        st.caption(
            f"RR data → `Rent Roll Input!A7+`. "
            f"T12 data → `T12 Input!A12+`. "
            f"Period {period_date_input.isoformat()} written to RR col S."
        )

    if can_download:
        try:
            # Step 1: Write RR data into the user's Analyzer (uses existing
            # t12_writer module; "t12_writer" name is historical — see
            # SPEC-T12 §"Module naming history").
            translated = translate_for_t12(c)
            populated_after_rr = populate_t12(
                analyzer_bytes_cached or t12_file.getvalue(),
                translated,
                period_date_input,
            )

            # Step 2: Append session-state UNMATCHED resolutions (if any) and
            # write T12 GL detail on top of the RR-populated Analyzer.
            new_descmap_entries = list(st.session_state.t12_resolutions.values())
            final_bytes = populate_t12_input(
                populated_after_rr,
                t12_parse_result,
                new_descmap_entries=new_descmap_entries,
                source_filename=getattr(raw_t12_file, "name", "raw_t12.xlsx"),
                t12_version=T12_VERSION,
                t12_last_updated=T12_LAST_UPDATED,
            )

            t12_stem = Path(getattr(t12_file, "name", "Analyzer.xlsx")).stem
            rr_stem = Path(getattr(rr_file, "name", "rent_roll.xlsx")).stem
            combined_out_name = (
                f"{t12_stem} with {rr_stem} + T12 "
                f"{period_date_input.isoformat()}.xlsx"
            )

            st.download_button(
                label=f"⬇️  Download {combined_out_name[:60]}{'…' if len(combined_out_name) > 60 else ''}",
                data=final_bytes,
                file_name=combined_out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_combined",
            )
        except T12CapacityError as e:
            st.error(f"Rent Roll exceeds Analyzer capacity: {e}")
        except T12NormalizerCapacityError as e:
            st.error(f"T12 exceeds Analyzer capacity: {e}")
        except ValueError as e:
            st.error(f"Analyzer / T12 error: {e}")
        except Exception as e:
            st.error(f"Could not produce combined output: {e}")
    else:
        st.button(
            "⬇️  Combined download not yet available",
            disabled=True,
            use_container_width=True,
            key="dl_combined_disabled",
        )
