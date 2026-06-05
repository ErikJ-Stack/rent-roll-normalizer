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

        /* ───────────────────────────────────────────────────────────────
           Compact file uploader (Track 5 v0.1.10)
           After a file is selected, lay the small "+" dropzone on the
           left and the file card on the right (horizontal), instead of
           stacking them vertically. Saves ~60px of sidebar space per
           uploader. Uses :has() to scope the side-by-side rule to the
           "file already uploaded" state — the empty-state dropzone keeps
           its wide drag-and-drop UI. Targets stable data-testid
           attributes for version resilience.
           ─────────────────────────────────────────────────────────────── */

        /* Tighten vertical rhythm globally inside file uploaders. */
        [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
            min-height: 56px !important;
            padding: 0.5rem 0.75rem !important;
        }}
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] {{
            padding: 0.15rem !important;
        }}

        /* When a file is present (file-list contains items), make the inner
           wrapper a horizontal flex row: dropzone shrinks to a square + button
           on the left, file list expands on the right. */
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) > section,
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) > div {{
            display: flex !important;
            flex-direction: row !important;
            align-items: stretch !important;
            gap: 0.5rem;
        }}
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section[data-testid="stFileUploaderDropzone"] {{
            flex: 0 0 56px !important;
            width: 56px !important;
            min-width: 56px !important;
            padding: 0 !important;
            justify-content: center;
        }}
        /* Hide the dropzone instructions text when a file is already selected
           (the wide "Drag and drop or browse" copy doesn't fit in 56px). */
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section[data-testid="stFileUploaderDropzone"] > div:not(:has(button)),
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section[data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section[data-testid="stFileUploaderDropzone"] span {{
            display: none !important;
        }}
        /* The file-list pane on the right grows to fill remaining width. */
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) [data-testid="stFileUploaderFileList"],
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) ul {{
            flex: 1 1 auto !important;
            margin: 0 !important;
        }}

        /* ───────────────────────────────────────────────────────────────
           Full-page loading overlay (Track 5 v0.1.8)
           Driven by a custom .t5-overlay element written into a
           module-level st.empty() slot via the _show_loading
           contextmanager in app.py. Lives ABOVE the top-level tabs
           in the DOM, so it's not hidden when the inactive tab's
           subtree has display:none. position:fixed makes it cover
           the whole viewport regardless of slot height.
           ─────────────────────────────────────────────────────────────── */
        .t5-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(10, 22, 44, 0.86);
            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
            z-index: 999999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.6rem;
        }}

        /* Our prominent ring spinner — 90px gold-on-faint-white ring. */
        .t5-overlay-ring {{
            width: 90px;
            height: 90px;
            border: 8px solid rgba(255, 255, 255, 0.12);
            border-top-color: {GOLD};
            border-radius: 50%;
            animation: t5-spinner-rotate 0.9s linear infinite;
            box-shadow: 0 0 24px rgba(190, 143, 63, 0.3);
        }}
        @keyframes t5-spinner-rotate {{
            from {{ transform: rotate(0deg); }}
            to   {{ transform: rotate(360deg); }}
        }}

        /* Overlay label — large, white serif, centered below ring. */
        .t5-overlay-label {{
            color: {WHITE};
            font-size: 1.25rem;
            font-weight: 500;
            letter-spacing: 0.03em;
            text-align: center;
            font-family: Georgia, 'Times New Roman', serif;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
        }}

        /* Determinate variant (MF pipeline): big gold % + a thin progress bar
           below the spinner. The bar width transitions so it slides smoothly
           between discrete server-driven updates. */
        .t5-overlay-pct {{
            color: {GOLD};
            font-size: 2.6rem;
            font-weight: 700;
            font-family: Georgia, 'Times New Roman', serif;
            letter-spacing: 0.02em;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.45);
            margin-top: -0.4rem;
        }}
        .t5-overlay-bar {{
            width: min(360px, 70vw);
            height: 8px;
            background: rgba(255, 255, 255, 0.14);
            border-radius: 999px;
            overflow: hidden;
            margin-top: -0.6rem;
        }}
        .t5-overlay-bar-fill {{
            height: 100%;
            background: {GOLD};
            border-radius: 999px;
            transition: width 0.35s ease;
            box-shadow: 0 0 12px rgba(190, 143, 63, 0.5);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
