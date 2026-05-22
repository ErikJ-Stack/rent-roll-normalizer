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

# Navy-ink lockup on transparent — used on the WHITE landing/login page.
LOGO_INK_PATH = Path(__file__).parent / "assets" / "pingkas_logo_ink.png"

# Fortis Capital companion mark. Near-black artwork on a white backdrop; the
# viewBox is trimmed to the artwork so there's no surrounding white margin. It
# blends into the white landing page.
FORTIS_LOGO_PATH = Path(__file__).parent / "assets" / "fortis_logo.svg"


@lru_cache(maxsize=4)
def _logo_data_uri(path_str: str) -> str:
    data = Path(path_str).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    mime = "image/svg+xml" if path_str.lower().endswith(".svg") else "image/png"
    return f"data:{mime};base64,{b64}"


# Fraction of each logo box's height occupied by actual artwork, measured
# 2026-05-22. The Pingkas ink lockup nearly fills its canvas vertically; the
# trimmed Fortis SVG fills its box. Matching *artwork height* — not box width —
# is what makes the two marks look balanced side by side.
_PINGKAS_ART_H = 0.979  # pingkas_logo_ink.png
_FORTIS_ART_H = 1.000   # fortis_logo.svg (viewBox trimmed to artwork)


def render_centered_logo(width_px: int = 260) -> None:
    """Render the Pingkas + Fortis logos side by side on the WHITE landing page,
    scaled so their artwork shares a common height (Pingkas box at ``width_px``,
    Fortis matched to it). Uses the navy-ink Pingkas lockup for the white canvas."""
    imgs = []
    if LOGO_INK_PATH.exists():
        imgs.append((_logo_data_uri(str(LOGO_INK_PATH)), "Pingkas Capital", float(width_px)))
    if FORTIS_LOGO_PATH.exists():
        fortis_h = width_px * (_PINGKAS_ART_H / _FORTIS_ART_H)
        imgs.append((_logo_data_uri(str(FORTIS_LOGO_PATH)), "Fortis Capital", fortis_h))
    if not imgs:
        return
    tags = "".join(
        f'<img src="{uri}" alt="{alt}" '
        f'style="height:{h:.0f}px; width:auto; max-width:48%;" />'
        for uri, alt, h in imgs
    )
    # Break out of Streamlit's block container (which is offset right by the
    # sidebar gutter) so the logos are centered against the full viewport.
    st.markdown(
        f"""
        <div style="width:100vw; position:relative; left:50%;
                    transform:translateX(-50%);
                    display:flex; justify-content:center; align-items:center;
                    gap:2rem; padding:1.5rem 1rem 1.25rem;
                    box-sizing:border-box;">
            {tags}
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_landing_css() -> None:
    """White-background theme for the login/landing page. Overrides the global
    navy dark theme (set in .streamlit/config.toml) so the landing page reads as
    a clean white canvas with navy text — the dark theme returns after login."""
    st.markdown(
        f"""
        <style>
        /* White canvas for the landing page. */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: {WHITE} !important;
        }}
        .block-container, [data-testid="stMainBlockContainer"] {{
            padding-top: 1.2rem !important;
        }}
        /* Navy text/headings on white (global theme paints these white/gold). */
        h1, h2, h3 {{
            font-family: Georgia, 'Times New Roman', serif !important;
            color: {NAVY} !important;
            letter-spacing: 0.3px;
        }}
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"], .stCaption, label {{
            color: {NAVY} !important;
        }}
        /* Buttons stay gold-on-navy — reads fine on white. */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
            background-color: {GOLD};
            color: {NAVY};
            border: 1px solid {GOLD};
            font-weight: 600;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {{
            background-color: {NAVY};
            color: {WHITE};
            border: 1px solid {GOLD};
        }}
        a, a:visited {{ color: {GOLD} !important; }}
        </style>
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
