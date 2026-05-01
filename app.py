"""
Rent Roll Normalization App — Streamlit entry point.

Run locally:
    streamlit run app.py

Deploy to Streamlit Cloud:
    Push this folder to a GitHub repo and connect at https://streamlit.io/cloud
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

from mappings import MappingSet, load_mapping_workbook
from normalizer import CONDENSED_COLUMNS, normalize_rent_roll
from period_date import detect_period_date
from reports import build_by_type, build_exceptions, build_summary
from t12_translator import translate_for_t12
from t12_writer import T12CapacityError, populate_t12
from writer import write_output


APP_VERSION = "1.10.0"
APP_LAST_UPDATED = "2026-04-30"


def _build_output_name(source_filename: str) -> str:
    """Build output filename: <source_stem> Normalized YYYY-MM-DD.xlsx

    Strips the original extension (handles .xlsx and .xlsm).
    If a previous "Normalized YYYY-MM-DD" suffix is already present in the
    source name (e.g. user re-runs an already-normalized file), it's stripped
    so we don't end up with stacked suffixes like "...Normalized 2026-04-26 Normalized 2026-04-27".
    """
    import re
    stem = Path(source_filename).stem  # drops the extension
    # Strip any pre-existing " Normalized YYYY-MM-DD" suffix (case-insensitive)
    stem = re.sub(r"\s+Normalized\s+\d{4}-\d{2}-\d{2}\s*$", "", stem, flags=re.IGNORECASE)
    today = dt.date.today().isoformat()  # YYYY-MM-DD
    return f"{stem} Normalized {today}.xlsx"


# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Rent Roll Normalizer",
    page_icon="🏢",
    layout="wide",
)

# Title row with version badge on the right
title_col, version_col = st.columns([5, 1])
with title_col:
    st.title("Rent Roll Normalizer")
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
            ">v{APP_VERSION}</span>
            <div style="
                color: #888888;
                font-size: 11px;
                margin-top: 4px;
                font-family: 'Calibri', sans-serif;
            ">Updated {APP_LAST_UPDATED}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Upload a senior-housing rent roll. The app detects the header, parses the "
    "parent-apartment / child-bed structure, normalizes to one-row-per-bed, and "
    "produces a 6-tab Excel workbook. Monthly care/ancillary columns not "
    "explicitly recognized are auto-summed into **Other LOC $** so no revenue "
    "goes missing across operator formats."
)

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("Inputs")
    rr_file = st.file_uploader(
        "Rent Roll (.xlsx)",
        type=["xlsx", "xlsm"],
        help="Any senior housing rent roll. Header doesn't need to be on row 1.",
    )
    mapping_file = st.file_uploader(
        "Mapping workbook (.xlsx) — optional",
        type=["xlsx"],
        help=(
            "Override defaults for Apartment_Type_Rules, Bed_Status_Rules, "
            "Payer_Type_Rules, Care_Level_Rules, Care_Bucket_Rules. "
            "Any sheet you omit falls back to the built-in defaults."
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
        care_type_default = ""  # treat "(none)" as no default
    st.divider()

    st.subheader("T12 integration (optional)")
    t12_file = st.file_uploader(
        "T12 Intake Template (.xlsx)",
        type=["xlsx"],
        key="t12_uploader",
        help=(
            "Optional. Upload your T12 intake workbook to receive a second "
            "output file with the rent roll auto-populated into its "
            "'Rent Roll Input' sheet starting at row 7. The T12's other tabs, "
            "formulas, and data validations are left untouched."
        ),
    )

    # Period Date — auto-detect from filename, allow manual override
    auto_detected_date = None
    if rr_file is not None:
        auto_detected_date = detect_period_date(getattr(rr_file, "name", ""))

    period_date_input = st.date_input(
        "Rent Roll Period Date (for T12 col S)",
        value=auto_detected_date or dt.date.today(),
        help=(
            "Written to column S of the T12's Rent Roll Input sheet on every "
            "row. Auto-detected from the rent roll filename when possible. "
            "Override if needed."
        ),
    )
    if auto_detected_date:
        st.caption(f"Auto-detected from filename: **{auto_detected_date.isoformat()}**")
    else:
        if rr_file is not None:
            st.caption("Could not auto-detect a date from the filename — set manually.")

    st.divider()
    st.caption(f"App version: {APP_VERSION}")

# --- Main ------------------------------------------------------------------
if rr_file is None:
    st.info("Upload a rent roll to begin.")
    with st.expander("What the app does"):
        st.markdown(
            """
            - **Detects the header row** in the first ~20 rows by scoring against known
              rent-roll column signatures (Unit / Apartment / Bed / Resident / ...).
            - **Parses parent-apartment / child-bed layouts**: apartment rows establish
              context (unit, apt type, market rate), child rows become normalized beds.
            - **Auto-groups care charges** by header prefix. Recognized buckets (AL, Med
              Mgmt, Pharmacy) get their own columns. Everything else rolls into
              **Other LOC $**.
            - **Normalizes** apt type, bed status, payer type, and care level against
              editable mapping rules; falls back to `Private Pay` when payer is blank.
            - **Preserves vacant beds** so occupancy and availability math stays honest.
            - **Exports** a 6-tab Excel: Condensed_RR, Normalized_Beds, RR_Summary,
              RR_By_Type, RR_Exceptions, Mapping_Reference, plus a Run_Info tab.
            """
        )
    st.stop()

# --- Process ---------------------------------------------------------------
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

summary   = build_summary(n)
by_type   = build_by_type(n)
exceptions = build_exceptions(n, result.unmapped)

# --- Headline KPIs ---------------------------------------------------------
colA, colB, colC, colD, colE = st.columns(5)
total_beds = len(n)
occ_beds = int((n["Status"] == "Occupied").sum())
colA.metric("Total Beds", total_beds)
colB.metric("Occupied", occ_beds)
colC.metric("Bed Occupancy", f"{100*occ_beds/total_beds:.1f}%" if total_beds else "0.0%")
colD.metric("Avg Actual (occ)", f"${n.loc[n['Status']=='Occupied','Actual Rate'].mean():,.0f}"
            if occ_beds else "$0")
colE.metric("In-Place Monthly Rev", f"${n['Total Monthly Revenue'].sum():,.0f}")

st.caption(
    f"Header detected on row {result.header_row_idx + 1} "
    f"(1-indexed). {len(result.care_groups)} care/ancillary column group(s) identified."
)

if result.property_care_type_default:
    default_count = int((n["Care Type Source"] == "Property Default").sum())
    source_count = int((n["Care Type Source"] == "Source").sum())
    st.info(
        f"**Property Care Type default applied: {result.property_care_type_default}** — "
        f"used for {default_count} bed(s) where source had no Care Type. "
        f"{source_count} bed(s) used an explicit source value."
    )

# --- Tabs ------------------------------------------------------------------
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
    st.caption("Filter and sort columns before exporting. Use the three-dot menu on any "
               "column header to sort. Use the search box above the table to filter.")
    st.dataframe(
        c,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Market Rate":      st.column_config.NumberColumn(format="$%.0f"),
            "Actual Rate":      st.column_config.NumberColumn(format="$%.0f"),
            "Concession $":     st.column_config.NumberColumn(format="$%.0f"),
            "Care Level $":  st.column_config.NumberColumn(format="$%.0f"),
            "Med Mgmt $":       st.column_config.NumberColumn(format="$%.0f"),
            "Pharmacy $":       st.column_config.NumberColumn(format="$%.0f"),
            "Other LOC $":      st.column_config.NumberColumn(format="$%.0f"),
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

# --- Download --------------------------------------------------------------
st.divider()
st.subheader("Export")

run_meta = {
    "App Version":          APP_VERSION,
    "App Last Updated":     APP_LAST_UPDATED,
    "Run Timestamp":        dt.datetime.now().isoformat(timespec="seconds"),
    "Source File":          getattr(rr_file, "name", "uploaded"),
    "Mapping File":         getattr(mapping_file, "name", "(defaults only)"),
    "Property Care Type Default": result.property_care_type_default or "(none)",
    "Header Row (1-idx)":   result.header_row_idx + 1,
    "Care Groups Detected": len(result.care_groups),
    "Total Beds":           len(n),
    "Occupied Beds":        occ_beds,
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

with dl_col2:
    st.markdown("**T12 with Rent Roll**")
    if t12_file is None:
        st.caption("Upload a T12 intake template in the sidebar to enable.")
        st.button(
            "⬇️  T12 not uploaded",
            disabled=True,
            use_container_width=True,
            key="dl_t12_disabled",
        )
    else:
        st.caption(
            f"Period **{period_date_input.isoformat()}** written to col S "
            f"on every populated row."
        )
        try:
            translated = translate_for_t12(c)
            t12_bytes_in = t12_file.getvalue()
            t12_populated_bytes = populate_t12(
                t12_bytes_in,
                translated,
                period_date_input,
            )
            t12_stem = Path(getattr(t12_file, "name", "T12.xlsx")).stem
            rr_stem = Path(getattr(rr_file, "name", "rent_roll.xlsx")).stem
            t12_out_name = (
                f"{t12_stem} with {rr_stem} "
                f"{period_date_input.isoformat()}.xlsx"
            )
            st.download_button(
                label=f"⬇️  Download {t12_out_name[:60]}{'...' if len(t12_out_name) > 60 else ''}",
                data=t12_populated_bytes,
                file_name=t12_out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_t12",
            )
        except T12CapacityError as e:
            st.error(f"T12 capacity exceeded: {e}")
        except ValueError as e:
            st.error(f"T12 error: {e}")
        except Exception as e:
            st.error(f"Could not populate T12: {e}")
