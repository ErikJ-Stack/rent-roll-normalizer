"""
Pingkas Capital brand assets for the Streamlit app — centralized so the main
app page and the login gate stay visually consistent.

Palette and logo are sourced from the brand sheet (Pingkas_Capital_PDF.pdf).
See COSMETIC-CHANGES.md for the change history.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

# Brand palette (hex) — keep in sync with .streamlit/config.toml [theme].
NAVY = "#0E1D41"
GOLD = "#BE8F3F"
WHITE = "#FFFFFF"
NAVY_LIGHT = "#16294D"

# Gold-on-navy lockup; its background is brand navy so it blends seamlessly
# into the dark theme canvas.
LOGO_PATH = Path(__file__).parent / "assets" / "pingkas_logo_navy.png"


@lru_cache(maxsize=4)
def _logo_data_uri(path_str: str) -> str:
    data = Path(path_str).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def render_centered_logo(width_px: int = 300) -> None:
    """Render the Pingkas Capital logo centered on the page."""
    if not LOGO_PATH.exists():
        return
    uri = _logo_data_uri(str(LOGO_PATH))
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin: 0 0 1.25rem 0;">
            <img src="{uri}" alt="Pingkas Capital"
                 style="width:{width_px}px; max-width:70%; height:auto;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_brand_css() -> None:
    """Inject brand CSS that the config.toml theme can't reach — serif display
    headings, gold title accent, and button polish."""
    st.markdown(
        f"""
        <style>
        /* Pull the main content up toward the top edge — Streamlit's default
           block-container top padding leaves a large empty band above the logo. */
        .block-container, [data-testid="stMainBlockContainer"] {{
            padding-top: 1.2rem !important;
        }}

        /* Elegant serif display for titles/headers (evokes Trajan Pro). */
        h1, h2, h3 {{
            font-family: Georgia, 'Times New Roman', serif !important;
            letter-spacing: 0.3px;
        }}
        h1 {{ color: {GOLD} !important; }}
        h2, h3 {{ color: {WHITE} !important; }}

        /* Buttons: gold fill, navy label. */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
            background-color: {GOLD};
            color: {NAVY};
            border: 1px solid {GOLD};
            font-weight: 600;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {{
            background-color: {WHITE};
            color: {NAVY};
            border: 1px solid {GOLD};
        }}

        /* Links in brand gold. */
        a, a:visited {{ color: {GOLD} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
