"""
make_cockpit_logos.py — derive dark-canvas logo assets for the cockpit login
page (2026-06-12 redesign follow-up).

The committed brand assets are light-canvas artwork:
  - assets/pingkas_logo_navy.png  — gold lockup on solid brand-navy (#0E1D41)
  - assets/fortis_logo.svg        — embeds a PNG of white artwork on black,
                                    color-matrix-filtered for the white page

This script derives two transparent-background versions that read on the
graphite cockpit canvas:

  - assets/pingkas_logo_gold.png  — navy unmixed to transparent; every pixel
    is re-expressed as (gold, alpha) where alpha is the pixel's distance from
    navy along the navy→gold line, so anti-aliased edges feather cleanly.
  - assets/fortis_logo_light.png  — alpha = source luminance, RGB = soft
    white (#E6EDF5), from the SVG's embedded PNG.

Both outputs are trimmed to their artwork bounding box. Re-run any time the
source assets change:  python tools/make_cockpit_logos.py
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"

NAVY = (14, 29, 65)
GOLD = (189, 143, 62)
SOFT_WHITE = (230, 237, 245)  # cockpit CK_TEXT


def _trim(img: Image.Image, pad: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.width, right + pad)
    bottom = min(img.height, bottom + pad)
    return img.crop((left, top, right, bottom))


def make_pingkas_gold() -> None:
    src = Image.open(ASSETS / "pingkas_logo_navy.png").convert("RGBA")
    px = src.load()
    out = Image.new("RGBA", src.size)
    po = out.load()
    # Unit vector navy→gold and its length, for projecting each pixel onto
    # the navy↔gold mix line. Pure navy → alpha 0; pure gold → alpha 255.
    dn = tuple(g - n for g, n in zip(GOLD, NAVY))
    norm2 = sum(d * d for d in dn)
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            t = sum((c - n) * d for c, n, d in zip((r, g, b), NAVY, dn)) / norm2
            t = max(0.0, min(1.0, t))
            po[x, y] = (*GOLD, int(round(t * (a / 255) * 255)))
    out = _trim(out)
    out.save(ASSETS / "pingkas_logo_gold.png")
    print(f"pingkas_logo_gold.png  {out.size}")


def make_fortis_light() -> None:
    svg = (ASSETS / "fortis_logo.svg").read_text(encoding="utf-8")
    m = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", svg)
    if not m:
        raise SystemExit("fortis_logo.svg has no embedded PNG")
    src = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGBA")
    px = src.load()
    out = Image.new("RGBA", src.size)
    po = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            po[x, y] = (*SOFT_WHITE, int(round(luma * (a / 255))))
    out = _trim(out)
    out.save(ASSETS / "fortis_logo_light.png")
    print(f"fortis_logo_light.png  {out.size}")


if __name__ == "__main__":
    make_pingkas_gold()
    make_fortis_light()
