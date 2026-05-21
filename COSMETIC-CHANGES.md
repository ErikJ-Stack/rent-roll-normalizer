# COSMETIC-CHANGES.md

> Tracker for purely **cosmetic / branding** changes to the Streamlit app — color scheme, logo, fonts, layout polish. Functional behavior is unchanged by anything logged here. Newest entry at top.
>
> **Why this is its own tracker:** these changes don't move the RR app version, the T12 code version, or the Analyzer substrate version (those three counters track *functional* streams — see CLAUDE.md). Cosmetic work is visual-only and easy to lose track of in CHANGELOG-RR, so it lives here.

## Brand reference

Source of truth: `Pingkas_Capital_PDF.pdf` brand sheet (logo + palette + typography).

| Token | Hex | RGB | Use |
| --- | --- | --- | --- |
| Navy | `#0E1D41` | 14 / 29 / 65 | App background (canvas) |
| Navy (light) | `#16294D` | — | Sidebar, widget fills, panels |
| Gold | `#BE8F3F` | 190 / 143 / 63 | Buttons, accents, title, links |
| White | `#FFFFFF` | 255 / 255 / 255 | Body text |
| Black | `#000000` | 0 / 0 / 0 | (brand-sheet only; unused in app) |
| Typeface | Trajan Pro 3 Regular | — | Not web-available; headings use a serif stack (Georgia) as a stand-in |

**Logo assets** (rendered from the vector PDF — there are no raster images embedded in the source):

| File | What | Where used |
| --- | --- | --- |
| `assets/pingkas_logo_navy.png` | Gold-on-navy full lockup, background = brand navy (blends seamlessly into the dark theme) | Centered at top of main page + login screen |
| `assets/pingkas_logo_ink.png` | Navy-ink lockup on transparent (for light backgrounds) | Not currently used; kept as a light-background alternative |

To re-render the logos from the brand PDF (if the source art changes):

```
pip install pymupdf
python -c "import fitz; d=fitz.open(r'<path>/Pingkas_Capital_PDF.pdf'); p=d[0]; \
p.get_pixmap(matrix=fitz.Matrix(6,6), clip=fitz.Rect(19.0,100.1,297.8,378.9)).save('assets/pingkas_logo_navy.png')"
```

The inset clip (`19.0, 100.1, 297.8, 378.9`) sits just inside the navy background rectangle to avoid capturing its antialiased edge — otherwise a faint 1px light ring shows around the logo on the navy canvas.

---

## Changes

### 2026-05-21 — Pingkas Capital brand theme + centered logo

Applied the Pingkas Capital brand identity to the Streamlit app.

- **New `.streamlit/config.toml`** — dark theme: `backgroundColor` navy `#0E1D41`, `primaryColor` gold `#BE8F3F`, `secondaryBackgroundColor` navy-light `#16294D`, `textColor` white. (No theme existed before; app used Streamlit defaults.)
- **New `branding.py`** — shared helper used by both the main page and the login gate so they stay consistent. Exposes `render_centered_logo(width_px)` (base64-embedded centered `<img>`) and `inject_brand_css()` (serif display headings via Georgia stack, gold `h1` title, gold buttons with navy labels, gold links).
- **New `assets/pingkas_logo_navy.png` + `assets/pingkas_logo_ink.png`** — extracted/rendered from `Pingkas_Capital_PDF.pdf` (vector → 6× PNG).
- **`app.py`** — calls `inject_brand_css()` after `set_page_config`, renders the centered logo (320px) under the login gate, and recolored the version badge from gray (`#2B2B2B`) to navy-light + gold border.
- **`auth.py`** — login screen now shows the centered logo (260px), brand CSS, and the form in a narrow centered column.

**Scope:** cosmetic only — no parser, writer, normalizer, or substrate logic touched. Verified: `app.py` / `auth.py` / `branding.py` compile; logo asset loads; theme keys valid. Live Streamlit could not be auto-screenshotted (its persistent websocket prevents the preview harness from reaching network-idle; server itself returns HTTP 200 / health OK), so the composed look was verified against a static mockup using the real logo asset and the exact brand CSS values.
