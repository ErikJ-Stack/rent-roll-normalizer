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

# Brand palette (hex) — legacy navy/gold tokens (still used on the white
# landing page button styling and kept for reference).
NAVY = "#0E1D41"
GOLD = "#BE8F3F"
WHITE = "#FFFFFF"
NAVY_LIGHT = "#16294D"

# Cockpit terminal palette (2026-06-12 UI redesign) — keep in sync with
# .streamlit/config.toml [theme]. Graphite surfaces + teal primary accent,
# amber/red for warn/bad states. See COSMETIC-CHANGES.md.
CK_BG = "#101418"        # main canvas
CK_RAIL = "#14181E"      # sidebar / command bar
CK_PANEL = "#1A2027"     # cards, inputs, tiles
CK_BORDER = "#232A33"    # hairline dividers
CK_BORDER_2 = "#2C3540"  # input/button borders
CK_TEXT = "#E6EDF5"      # primary text / values
CK_MUTED = "#9AA7B5"     # secondary text
CK_DIM = "#5E6B7A"       # labels, hints
CK_FAINT = "#3D4854"     # faintest chrome text
CK_TEAL = "#5DCAA5"      # primary accent / ok
CK_TEAL_DK = "#04342C"   # text on teal fills
CK_TEAL_LT = "#9FE1CB"   # ok titles on dark
CK_AMBER = "#EF9F27"     # warn
CK_AMBER_LT = "#FAC775"
CK_RED = "#E24B4A"       # bad
CK_RED_LT = "#F09595"

# Monospace stack for the terminal aesthetic (JetBrains Mono loaded via
# Google Fonts @import inside inject_cockpit_css).
CK_MONO = "'JetBrains Mono', ui-monospace, 'Cascadia Code', Consolas, 'SF Mono', monospace"

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
    """LEGACY (pre-2026-06-12 white landing) — superseded by
    render_cockpit_login_header(). Kept for easy revert; no longer called.

    Render the Pingkas + Fortis logos side by side on the WHITE landing page,
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


def inject_cockpit_landing_css() -> None:
    """Cockpit terminal theme for the login/landing page (2026-06-12 UI
    redesign). Graphite canvas, centered access panel, mono inputs, teal
    authenticate button. Replaces the white landing (`inject_landing_css`,
    kept below as legacy) — the image lockups are navy-on-white artwork that
    doesn't read on a dark canvas, so the firms render as text chrome via
    `render_cockpit_login_header()` instead."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background: {CK_BG} !important;
        }}
        .block-container, [data-testid="stMainBlockContainer"] {{
            padding-top: 4.5rem !important;
        }}

        /* Access panel — the login form card. */
        [data-testid="stForm"] {{
            background: {CK_RAIL};
            border: 1px solid {CK_BORDER} !important;
            border-radius: 12px;
            padding: 1.6rem 1.6rem 1.2rem;
        }}
        [data-testid="stForm"] label p {{
            font-family: {CK_MONO} !important;
            font-size: 0.68rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: {CK_DIM} !important;
        }}
        [data-testid="stForm"] input {{
            font-family: {CK_MONO};
            color: {CK_TEXT};
        }}
        [data-testid="stForm"] [data-testid="stTextInputRootElement"],
        [data-testid="stForm"] [data-baseweb="input"] {{
            background: {CK_PANEL} !important;
            border-color: {CK_BORDER_2} !important;
        }}
        .stFormSubmitButton > button {{
            width: 100%;
            background-color: {CK_TEAL};
            color: {CK_TEAL_DK};
            border: 1px solid {CK_TEAL};
            font-family: {CK_MONO};
            font-weight: 700;
            letter-spacing: 0.08em;
        }}
        .stFormSubmitButton > button:hover {{
            background-color: {CK_TEAL_LT};
            color: {CK_TEAL_DK};
            border: 1px solid {CK_TEAL_LT};
        }}

        /* Wordmark header above the panel. */
        .ckl-head {{
            text-align: center;
            font-family: {CK_MONO};
            margin: 0 0 1.6rem;
        }}
        .ckl-brand {{
            color: {CK_TEAL};
            font-size: 1.7rem;
            font-weight: 700;
            letter-spacing: 0.12em;
        }}
        .ckl-sub {{
            color: {CK_MUTED};
            font-size: 0.72rem;
            letter-spacing: 0.34em;
            margin-top: 0.5rem;
        }}
        .ckl-firms {{
            color: {CK_DIM};
            font-size: 0.66rem;
            letter-spacing: 0.18em;
            margin-top: 0.9rem;
        }}
        .ckl-foot {{
            text-align: center;
            font-family: {CK_MONO};
            color: {CK_FAINT};
            font-size: 0.62rem;
            letter-spacing: 0.14em;
            margin-top: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cockpit_login_header() -> None:
    """Wordmark block above the cockpit login panel — UW//DECK brand, terminal
    subtitle, and the two firms as text chrome (image lockups are light-canvas
    artwork; see inject_cockpit_landing_css)."""
    st.markdown(
        """
        <div class="ckl-head">
            <div class="ckl-brand">UW//DECK</div>
            <div class="ckl-sub">UNDERWRITING TERMINAL</div>
            <div class="ckl-firms">PINGKAS CAPITAL · FORTIS CAPITAL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_landing_css() -> None:
    """LEGACY (pre-2026-06-12 white landing) — superseded by
    inject_cockpit_landing_css(). Kept for easy revert; no longer called.

    White-background theme for the login/landing page. Overrides the global
    dark theme (set in .streamlit/config.toml) so the landing page reads as
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


def inject_cockpit_css() -> None:
    """Cockpit terminal theme (2026-06-12 UI redesign) — layered AFTER
    inject_brand_css() so its rules win. Graphite surfaces, teal accent,
    monospace data chrome. Also restyles the shared loading overlay and
    defines the command-bar (.ck-bar), status-chip (.ck-chip), live-ledger
    (.ck-ledger), and risk-flag (.ck-flag) component classes used by app.py
    and dashboard_ui.py."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

        /* ── Canvas ─────────────────────────────────────────────────── */
        .stApp, [data-testid="stAppViewContainer"] {{
            background: {CK_BG} !important;
        }}
        [data-testid="stHeader"] {{ background: {CK_BG} !important; }}

        /* Clear Streamlit's floating header. inject_brand_css() pulls the
           main container up to 1.2rem (right for the old big-title layout),
           but the cockpit's first element is the compact mode selector —
           at 1.2rem it slides under the header toolbar and gets clipped. */
        .block-container, [data-testid="stMainBlockContainer"] {{
            padding-top: 3.6rem !important;
        }}
        [data-testid="stSidebar"] {{
            background: {CK_RAIL} !important;
            border-right: 1px solid {CK_BORDER};
        }}

        /* ── Typography — terminal headings ─────────────────────────── */
        h1 {{
            font-family: {CK_MONO} !important;
            color: {CK_TEXT} !important;
            font-size: 1.3rem !important;
            letter-spacing: 0.04em;
            font-weight: 600 !important;
        }}
        h2, h3 {{
            font-family: {CK_MONO} !important;
            color: {CK_DIM} !important;
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 600 !important;
        }}
        h5 {{
            font-family: {CK_MONO} !important;
            color: {CK_DIM} !important;
            font-size: 0.72rem !important;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 600 !important;
        }}
        a, a:visited {{ color: {CK_TEAL} !important; }}

        /* ── Metric tiles ────────────────────────────────────────────── */
        [data-testid="stMetric"] {{
            background: {CK_PANEL};
            border: 1px solid {CK_BORDER};
            border-radius: 8px;
            padding: 10px 14px;
        }}
        [data-testid="stMetricLabel"] p {{
            font-family: {CK_MONO} !important;
            font-size: 0.68rem !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {CK_DIM} !important;
        }}
        [data-testid="stMetricValue"] {{
            font-family: {CK_MONO} !important;
            color: {CK_TEXT} !important;
        }}

        /* ── Tabs — terminal rail ───────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid {CK_BORDER};
        }}
        .stTabs [data-baseweb="tab"] {{
            font-family: {CK_MONO};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: {CK_DIM};
        }}
        .stTabs [aria-selected="true"] {{ color: {CK_TEAL} !important; }}
        .stTabs [data-baseweb="tab-highlight"] {{ background-color: {CK_TEAL} !important; }}

        /* ── Buttons ────────────────────────────────────────────────── */
        .stButton > button, .stFormSubmitButton > button {{
            background-color: {CK_PANEL};
            color: {CK_MUTED};
            border: 1px solid {CK_BORDER_2};
            font-family: {CK_MONO};
            font-weight: 600;
            letter-spacing: 0.04em;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            background-color: {CK_PANEL};
            color: {CK_TEAL};
            border: 1px solid {CK_TEAL};
        }}
        .stDownloadButton > button {{
            background-color: {CK_TEAL};
            color: {CK_TEAL_DK};
            border: 1px solid {CK_TEAL};
            font-family: {CK_MONO};
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        .stDownloadButton > button:hover {{
            background-color: {CK_TEAL_LT};
            color: {CK_TEAL_DK};
            border: 1px solid {CK_TEAL_LT};
        }}

        /* ── Inputs / uploaders / expanders ─────────────────────────── */
        [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {{
            background: {CK_PANEL} !important;
            border: 1px dashed {CK_BORDER_2} !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stNumberInput"] input {{
            font-family: {CK_MONO};
        }}
        [data-testid="stExpander"] details {{
            background: {CK_RAIL};
            border: 1px solid {CK_BORDER} !important;
            border-radius: 8px;
        }}
        hr {{ border-color: {CK_BORDER} !important; }}

        /* ── Loading overlay — re-skin brand navy/gold → graphite/teal ─ */
        .t5-overlay {{ background: rgba(13, 17, 21, 0.88); }}
        .t5-overlay-ring {{
            border-top-color: {CK_TEAL};
            box-shadow: 0 0 24px rgba(93, 202, 165, 0.25);
        }}
        .t5-overlay-label {{ font-family: {CK_MONO}; font-size: 1.05rem; }}
        .t5-overlay-pct {{ color: {CK_TEAL}; font-family: {CK_MONO}; }}
        .t5-overlay-bar-fill {{
            background: {CK_TEAL};
            box-shadow: 0 0 12px rgba(93, 202, 165, 0.5);
        }}

        /* ── Command bar ────────────────────────────────────────────── */
        .ck-bar {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            background: {CK_RAIL};
            border: 1px solid {CK_BORDER};
            border-radius: 10px;
            padding: 10px 16px;
            margin: 0 0 12px;
            font-family: {CK_MONO};
        }}
        .ck-brand {{
            color: {CK_TEAL};
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.08em;
        }}
        .ck-deal {{
            color: {CK_TEXT};
            font-size: 0.82rem;
            letter-spacing: 0.05em;
            flex: 0 1 auto;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .ck-chip {{
            font-size: 0.68rem;
            letter-spacing: 0.06em;
            padding: 3px 10px;
            border-radius: 6px;
            border: 1px solid {CK_BORDER_2};
            white-space: nowrap;
        }}
        .ck-chip.ok {{
            color: {CK_TEAL};
            border-color: rgba(93, 202, 165, 0.45);
            background: rgba(93, 202, 165, 0.08);
        }}
        .ck-chip.warn {{
            color: {CK_AMBER};
            border-color: rgba(239, 159, 39, 0.45);
            background: rgba(239, 159, 39, 0.08);
        }}
        .ck-chip.off {{ color: {CK_DIM}; }}
        .ck-ver {{
            margin-left: auto;
            color: {CK_FAINT};
            font-size: 0.66rem;
            letter-spacing: 0.05em;
            text-align: right;
        }}

        /* ── Live ledger ────────────────────────────────────────────── */
        .ck-ledger {{
            width: 100%;
            border-collapse: collapse;
            font-family: {CK_MONO};
            font-size: 0.85rem;
        }}
        .ck-ledger td {{ padding: 5px 0; }}
        .ck-ledger .lbl {{ color: {CK_MUTED}; }}
        .ck-ledger .val {{ color: {CK_TEXT}; text-align: right; }}
        .ck-ledger .pct {{ color: {CK_DIM}; text-align: right; width: 84px; }}
        .ck-ledger tr.total td {{ border-top: 1px solid {CK_BORDER}; }}
        .ck-ledger tr.total .lbl {{ color: {CK_TEXT}; }}
        .ck-ledger .neg {{ color: {CK_RED_LT}; }}
        .ck-ledger .pos {{ color: {CK_TEAL}; font-weight: 600; }}
        .ck-panel {{
            background: {CK_PANEL};
            border: 1px solid {CK_BORDER};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        .ck-eyebrow {{
            font-family: {CK_MONO};
            font-size: 0.66rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: {CK_DIM};
            margin: 0 0 8px;
        }}

        /* ── Risk flag cards ────────────────────────────────────────── */
        .ck-flag {{
            background: {CK_PANEL};
            border-left: 3px solid {CK_FAINT};
            padding: 8px 12px;
            margin-bottom: 8px;
            font-family: {CK_MONO};
        }}
        .ck-flag .t {{ font-size: 0.78rem; font-weight: 600; color: {CK_MUTED}; }}
        .ck-flag .d {{ font-size: 0.7rem; color: {CK_DIM}; margin-top: 2px; }}
        .ck-flag.ok   {{ border-left-color: {CK_TEAL}; }}
        .ck-flag.ok .t   {{ color: {CK_TEAL_LT}; }}
        .ck-flag.warn {{ border-left-color: {CK_AMBER}; }}
        .ck-flag.warn .t {{ color: {CK_AMBER_LT}; }}
        .ck-flag.bad  {{ border-left-color: {CK_RED}; }}
        .ck-flag.bad .t  {{ color: {CK_RED_LT}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
