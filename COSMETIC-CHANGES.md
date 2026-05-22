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
| `assets/fortis_logo.svg` | Fortis Capital mark, white-filtered square SVG (self-contained, embeds a PNG) | Shown side-by-side with Pingkas at top of main page + login screen |

To re-render the logos from the brand PDF (if the source art changes):

```
pip install pymupdf
python -c "import fitz; d=fitz.open(r'<path>/Pingkas_Capital_PDF.pdf'); p=d[0]; \
p.get_pixmap(matrix=fitz.Matrix(6,6), clip=fitz.Rect(19.0,100.1,297.8,378.9)).save('assets/pingkas_logo_navy.png')"
```

The inset clip (`19.0, 100.1, 297.8, 378.9`) sits just inside the navy background rectangle to avoid capturing its antialiased edge — otherwise a faint 1px light ring shows around the logo on the navy canvas.

---

## Changes

### 2026-05-22 — White landing page; trimmed Fortis logo; logos login-only

Refined the dual-logo treatment from earlier today: the **login/landing page is now white** with both logos, and the logos are **removed from the post-login app** (which keeps the navy dark theme).

- **`assets/fortis_logo.svg`** — viewBox trimmed from `0 0 1125 1124.99995` to `112.5 236.8 900 651.7` (and `width`/`height` to `900`/`651.7`). The artwork is near-black and edge-to-edge inside the embedded PNG; all the "excess white space" was the SVG's white background rects extending past the image. Trimming removes 100% of that margin. The remaining white *behind* the artwork now blends into the white landing page.
- **`branding.py`** — `render_centered_logo()` now targets the white landing canvas: Pingkas switches from `pingkas_logo_navy.png` to `pingkas_logo_ink.png` (navy ink on transparent, visible on white). Height-match constants updated to the new assets (`_PINGKAS_ART_H = 0.979`, `_FORTIS_ART_H = 1.000`); at `width_px=260` both compute to a 254.5px artwork height. New `inject_landing_css()` paints `.stApp`/header white and recolors headings, captions, labels, and body text to navy (the global navy dark theme would otherwise render them white-on-white). Buttons stay gold. Default `width_px` lowered 300 → 260.
- **`auth.py`** — login gate calls `inject_landing_css()` instead of `inject_brand_css()`; logo render unchanged at 260px.
- **`app.py`** — removed the post-login `render_centered_logo(width_px=320)` call (and the now-unused import). The app reverts to the navy dark theme with no logos; the mode selector is the first element.

**Scope:** cosmetic only — no parser, writer, normalizer, or substrate logic touched. Verified: `branding.py` / `auth.py` / `app.py` compile; ink + trimmed-Fortis assets resolve; artwork heights match (254.5px at 260). Live Streamlit not auto-screenshotted (websocket blocks the preview harness); composed landing look verified via `logo_preview.html` on a white canvas with the real assets.

### 2026-05-22 — Fortis Capital companion logo (side-by-side)

Added the Fortis Capital mark beside the Pingkas Capital logo at the top of the main page and the login screen.

- **New `assets/fortis_logo.svg`** — copied from `Fortis Capital (1500 x 1500 px).svg` (self-contained square SVG; embeds a white-filtered PNG so it sits cleanly on the navy canvas).
- **`branding.py`** — `_logo_data_uri()` now picks the MIME type by extension (`image/svg+xml` for `.svg`, else `image/png`). `render_centered_logo()` renders both logos in a centered flex row, sized so their **artwork heights match** rather than their canvas widths. Both source files are square canvases (Pingkas 1673×1674, Fortis 1125 viewBox), but the artwork inside differs: Pingkas is a square stacked lockup filling ~61% W × ~67% H with generous padding, while Fortis is a wide, short wordmark filling ~79% W × ~56% H. Equal width therefore looked unbalanced. Measured artwork-height fractions (`_PINGKAS_ART_H = 0.665`, `_FORTIS_ART_H = 0.560`) drive the scale: Pingkas renders at the caller's `width_px`, Fortis box is scaled up by `0.665/0.560 ≈ 1.19×` so both marks share a common artwork height. Imgs now sized by `height` (`width:auto`, `max-width:48%`). Each logo renders only if its asset exists, so a missing file degrades gracefully.

**Scope:** cosmetic only — no parser, writer, normalizer, or substrate logic touched. Verified: `branding.py` compiles; both assets resolve to data URIs with correct MIME prefixes (`image/svg+xml` / `image/png`); at the main-page `width_px=320` both logos compute to an identical 212.8px artwork height.

### 2026-05-21 — Pingkas Capital brand theme + centered logo

Applied the Pingkas Capital brand identity to the Streamlit app.

- **New `.streamlit/config.toml`** — dark theme: `backgroundColor` navy `#0E1D41`, `primaryColor` gold `#BE8F3F`, `secondaryBackgroundColor` navy-light `#16294D`, `textColor` white. (No theme existed before; app used Streamlit defaults.)
- **New `branding.py`** — shared helper used by both the main page and the login gate so they stay consistent. Exposes `render_centered_logo(width_px)` (base64-embedded centered `<img>`) and `inject_brand_css()` (serif display headings via Georgia stack, gold `h1` title, gold buttons with navy labels, gold links).
- **New `assets/pingkas_logo_navy.png` + `assets/pingkas_logo_ink.png`** — extracted/rendered from `Pingkas_Capital_PDF.pdf` (vector → 6× PNG).
- **`app.py`** — calls `inject_brand_css()` after `set_page_config`, renders the centered logo (320px) under the login gate, and recolored the version badge from gray (`#2B2B2B`) to navy-light + gold border.
- **`auth.py`** — login screen now shows the centered logo (260px), brand CSS, and the form in a narrow centered column.

**Scope:** cosmetic only — no parser, writer, normalizer, or substrate logic touched. Verified: `app.py` / `auth.py` / `branding.py` compile; logo asset loads; theme keys valid. Live Streamlit could not be auto-screenshotted (its persistent websocket prevents the preview harness from reaching network-idle; server itself returns HTTP 200 / health OK), so the composed look was verified against a static mockup using the real logo asset and the exact brand CSS values.
