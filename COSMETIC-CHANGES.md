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

### 2026-06-12 — Light/dark cockpit toggle in the top control row

The cockpit now has a light variant, toggled by a **Light** switch beside the
property-type selector. The toggle drives two layers at once: (1) the cockpit
CSS — `inject_cockpit_css(light=...)` carries a full light token set (paper
canvas `#F2F4F6`, white panels, deep-teal accent `#0E8A63`, darkened
amber/red statuses) alongside the dark graphite set; (2) Streamlit's NATIVE
theme via `streamlit.config.set_option` so canvas-rendered surfaces
(st.dataframe grids, Altair charts, widget internals) follow the flip — not
just the custom chrome. The loading overlay stays dark in both modes (it
dims the whole screen); the login page stays dark (pre-auth, no toggle).

- `app.py`: `_set_native_theme()` + `_on_theme_toggle()`; the toggle's
  `on_change` callback flips the native theme BEFORE the rerun's script
  executes, so the new theme rides the next NewSession message. (First
  attempt used an early `st.rerun()` — that reruns before the toggle widget
  is re-instantiated, so Streamlit garbage-collects its pending state and
  the switch snaps back. Documented in the docstring.) Native-theme call is
  wrapped so a future API change degrades to CSS-only theming. Config is
  process-wide, not per-session — acceptable for single-operator usage.
- `branding.py`: `inject_cockpit_css(light: bool = False)` — token sets
  selected per variant; component color tokens (.ck-bar/.ck-chip/.ck-ledger/
  .ck-flag/.ck-user/.t5-tile) all live here now.
- `dashboard_ui.py`: headline-tile styles reduced to layout-only — colors
  moved to branding so tiles follow the toggle.
- `auth.py`: sidebar user chip switched from inline hex styles to the themed
  `.ck-user` class.
- Verified via `streamlit.testing.v1.AppTest` (server-side widget
  simulation): toggle ON → session state True, theme.base=light,
  light CSS injected; toggle OFF → clean revert; zero exceptions. All 27
  dashboard regression tests green.

### 2026-06-12 — Cockpit login page (terminal access panel)

Follow-up to the cockpit redesign below: the white landing/login page is
replaced by a matching terminal gate. Graphite canvas, centered access panel
(`UW//DECK` wordmark + "UNDERWRITING TERMINAL" + "PINGKAS CAPITAL · FORTIS
CAPITAL" as text chrome), mono inputs, full-width teal **Authenticate**
button, and a "SECURE CHANNEL · SHA-256 AUTH" footer line. The image lockups
(`pingkas_logo_ink.png` / `fortis_logo.svg`) are light-canvas artwork that
doesn't read on graphite, so the firms render as text — re-add a logo only if
a dark-canvas lockup is produced. Auth behavior unchanged (same form keys,
same SHA-256 verify, same logging).

- `branding.py`: new `inject_cockpit_landing_css()` +
  `render_cockpit_login_header()`; `inject_landing_css()` and
  `render_centered_logo()` kept as documented LEGACY (uncalled) for easy
  revert.
- `auth.py`: `require_login()` swaps to the cockpit landing functions; submit
  label `Sign in` → `Authenticate`; sidebar user status restyled from the 👤
  emoji + navy chip to a cockpit chip (`▸ <user>` teal mono on graphite).
- Verified locally end-to-end: cockpit login renders (graphite canvas, teal
  mono wordmark, panel form), authentication succeeds, sidebar chip + sign-out
  render, zero exceptions.

### 2026-06-12 — "Cockpit" terminal UI redesign (graphite/teal, monospace chrome)

Full post-login visual redesign chosen by the operator from three mockup
directions ("Command deck" / "Glide" / "Cockpit" — Cockpit won). Terminal-luxe
aesthetic: graphite surfaces, teal primary accent, JetBrains Mono data chrome,
amber/red status colors. **Visual + layout only — zero pipeline behavior
change** (all uploaders, the scenario radio, the UNMATCHED matcher, both
downloads, and the UW Template populate flow are untouched). The white
landing/login page is unchanged (its `inject_landing_css()` override still
wins). Verified end-to-end locally: login → cockpit shell → populated
dashboard against the Homestead regression fixture; all 27
`tests/test_dashboard_model.py` cases still green.

- `.streamlit/config.toml`: theme navy/gold → graphite/teal
  (`#101418` canvas / `#1A2027` panels / `#5DCAA5` primary / `#E6EDF5` text).
- `branding.py`: new `CK_*` palette constants + `inject_cockpit_css()`,
  layered after `inject_brand_css()` so its rules win. Styles canvas, sidebar
  rail, terminal headings (mono uppercase h2/h3/h5), metric tiles, tabs (teal
  highlight), buttons (teal download CTAs), inputs/uploaders/expanders, and
  re-skins the loading overlay (gold → teal). Defines component classes:
  `.ck-bar` command bar, `.ck-chip` status chips (ok/warn/off), `.ck-panel` +
  `.ck-ledger` live ledger, `.ck-flag` risk-flag cards, `.ck-eyebrow` labels.
- `app.py`: title row + version badge + long caption replaced by the
  **command bar** — `UW//DECK` brand, deal · period readout (auto-derived from
  the RR filename), RR/T12/AR intake status chips, scenario chip, version
  chrome right-aligned. Rendered after the sidebar so chip state is live.
  Sidebar sections renamed `📁 Uploads`/`💵 Underwriting` → `Intake`/
  `Underwriting` (styled as terminal section labels); `⚙️ Advanced` →
  `Advanced`; mode radio labels → `ALF // senior housing` / `MF //
  multifamily`; top tabs → `Dashboard` / `Workspace` (emoji dropped).
- `dashboard_ui.py`: headline tiles restyled as cockpit panels (mono values);
  new `_render_ledger()` — the GPR → vacancy → EGI → labor → non-labor →
  EBITDARM → mgmt fee → EBITDAR waterfall as a monospace table with a
  % -of-EGI column (derives only from fields the model already carries);
  `_render_risk_flags()` swapped from st.success/warning/error banners to
  compact color-coded `.ck-flag` cards; `render_dashboard()` now places the
  live ledger beside the risk-flag column (3:2 split) directly under the
  headline grid.
- Local-dev note: a gitignored `.streamlit/secrets.toml` with a `dev` /
  `cockpit-dev` login was added during verification (delete anytime; cloud
  secrets unaffected). `.claude/launch.json` added for local preview runs.

### 2026-06-05 — MF loading overlay shows a determinate % (1→100)

The MF loading overlay now shows a **gold percentage + a progress bar** instead
of just an indeterminate spinner. The % is *real pipeline progress* — weighted
across the uploaded docs (parse RR / T-12 / AR / OM) plus the slow model build —
so it reflects how much of the whole job is left, not a timer. The spinner still
spins alongside the number.

- `branding.py`: `.t5-overlay-pct` (big gold number) + `.t5-overlay-bar` /
  `.t5-overlay-bar-fill` (the fill `width` transitions, so the bar slides
  smoothly between discrete server updates).
- `app.py`: `_render_overlay_pct(pct, label)` + a `_PipelineProgress` controller
  that weights each stage and drives the overlay; the build stage is weighted
  heaviest (it's the real wait).
- `mf_uw_model_writer.populate_mf_model(..., progress=cb)`: optional callback
  fired at real build milestones (load 15% → T-12 45% → RR 80% → OM 90% →
  saved 100%) so the number counts up *during* the build. **Honest limit:** the
  openpyxl load and save are single opaque calls, so the % steps between
  milestones rather than streaming continuously; the fast file-parses just tick
  the bar forward as each completes. No output/logic change (default `progress`
  is a no-op).

### 2026-06-05 — MF area gets the full-page loading overlay (parity with ALF)

The MF intake flow (`_render_mf_intake`) now shows the same `.t5-overlay`
full-page loading spinner the ALF flow uses, instead of only a small `st.spinner`
on OM extraction. Wrapped each heavy step: parsing the Rent Roll, T-12, and AR
aging; OM extraction; and building the populated MF UW Model — each shows a
labelled overlay ("Parsing rent roll…", "Building MF UW Model…", etc.).

Implementation: the shared `_show_loading()` context manager + its `_overlay_slot`
(previously defined just above the ALF Dashboard/Workspace tabs, so MF — which
`st.stop()`s before that point — couldn't reach it) were **moved up to right
after `inject_brand_css()`**, above the ALF/MF mode dispatch. Both modes now
share one definition; ALF behavior is unchanged. No version-counter move (UX
polish only; parsing/writer logic untouched).

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
