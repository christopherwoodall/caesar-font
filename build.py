#!/usr/bin/env python3
"""Build 25 Caesar cipher fonts and the static HTML pages."""

import os
import shutil
import tempfile
from pathlib import Path

import requests
from fontTools.subset import Subsetter, Options
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.varLib import instancer

# ─── Configuration ───
BASE_URL = "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf"
DOCS_DIR = Path(__file__).parent / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
CSS_DIR = ASSETS_DIR / "css"

ASCII_UNICODE = list(range(0x20, 0x7F))  # printable ASCII


def caesar_shift(text: str, shift: int) -> str:
    """Shift ASCII letters by *shift* positions; leave everything else alone."""
    result = []
    for ch in text:
        if "a" <= ch <= "z":
            result.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            result.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            result.append(ch)
    return "".join(result)


def download_font(dest: Path) -> None:
    """Download Lora variable font."""
    resp = requests.get(BASE_URL, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"Downloaded {len(resp.content)} bytes")


def make_static_regular(src: Path, dest: Path) -> None:
    """Extract Regular (wght=400) instance from variable font."""
    font = TTFont(str(src))
    static = instancer.instantiateVariableFont(font, {"wght": 400})
    static.save(str(dest))
    print(f"Static Regular saved to {dest}")


def subset_to_ascii(src: Path, dest: Path) -> None:
    """Subset font to printable ASCII only."""
    opts = Options()
    opts.desubroutinize = True
    opts.hinting = False
    opts.layout_features = ["*"]
    opts.name_IDs = "*"
    opts.name_legacy = True
    opts.obfuscate_names = False
    opts.drop_tables = ["DSIG"]

    font = TTFont(str(src))
    subsetter = Subsetter(options=opts)
    subsetter.populate(unicodes=ASCII_UNICODE)
    subsetter.subset(font)
    font.save(str(dest))
    print(f"Subset font saved to {dest}")


def build_cipher_font(src: Path, dest: Path, shift: int) -> None:
    """Create a Caesar-cipher variant with *inverse* shift so encrypted text reads as plaintext."""
    font = TTFont(str(src))

    cmap_tables = font["cmap"].tables
    unicode_to_glyph = {}
    for table in cmap_tables:
        if table.isUnicode():
            for code, glyph_name in table.cmap.items():
                if code not in unicode_to_glyph:
                    unicode_to_glyph[code] = glyph_name

    inverse = (-shift) % 26
    new_cmap = {}
    for code in ASCII_UNICODE:
        ch = chr(code)
        if "a" <= ch <= "z":
            shifted = chr((ord(ch) - ord("a") + inverse) % 26 + ord("a"))
        elif "A" <= ch <= "Z":
            shifted = chr((ord(ch) - ord("A") + inverse) % 26 + ord("A"))
        else:
            shifted = ch

        src_glyph = unicode_to_glyph.get(ord(shifted))
        if src_glyph is None:
            src_glyph = unicode_to_glyph.get(code, ".notdef")
        new_cmap[code] = src_glyph

    font["cmap"].tables = []
    cmap4 = CmapSubtable.newSubtable(4)
    cmap4.platformID = 3
    cmap4.platEncID = 1
    cmap4.language = 0
    cmap4.cmap = new_cmap
    font["cmap"].tables.append(cmap4)

    cmap12 = CmapSubtable.newSubtable(12)
    cmap12.platformID = 3
    cmap12.platEncID = 10
    cmap12.language = 0
    cmap12.cmap = new_cmap
    font["cmap"].tables.append(cmap12)

    font.flavor = "woff2"
    font.save(str(dest))
    size = dest.stat().st_size
    print(f"  Shift {shift:2d} -> {dest.name} ({size:,} bytes)")


def generate_preview_image(font_path: Path, dest: Path) -> None:
    """Generate a 1200x630 social preview PNG."""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 630
    bg = "#0a0a12"
    cyan = "#00f0ff"
    magenta = "#ff00a0"
    gold = "#c9a227"
    white = "#e8e8f0"
    grid = "#0d1f2d"  # Very subtle grid color

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Load font at different sizes
    try:
        title_font = ImageFont.truetype(str(font_path), 96)
        subtitle_font = ImageFont.truetype(str(font_path), 48)
        detail_font = ImageFont.truetype(str(font_path), 32)
        arrow_font = ImageFont.truetype(str(font_path), 64)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = detail_font = arrow_font = title_font

    # Draw subtle grid lines
    for x in range(0, width, 60):
        draw.line([(x, 0), (x, height)], fill=grid, width=1)
    for y in range(0, height, 60):
        draw.line([(0, y), (width, y)], fill=grid, width=1)

    # Title
    title = "Caesar Cipher Font"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (width - tw) // 2
    ty = 160
    # Glow effect
    for offset in range(10, 0, -2):
        alpha = int(30 - offset * 3)
        glow_color = (0, max(0, 240 - alpha), 255 - alpha)
        draw.text((tx, ty), title, font=title_font, fill=glow_color)
    draw.text((tx, ty), title, font=title_font, fill=cyan)

    # Arrow line: A -> H (example shift)
    arrow_text = "A  ->  H"
    abox = draw.textbbox((0, 0), arrow_text, font=arrow_font)
    aw = abox[2] - abox[0]
    ax = (width - aw) // 2
    ay = ty + th + 50
    draw.text((ax, ay), arrow_text, font=arrow_font, fill=gold)

    # Subtitle
    subtitle = "The font is the key"
    sbbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw = sbbox[2] - sbbox[0]
    sx = (width - sw) // 2
    sy = ay + 90
    draw.text((sx, sy), subtitle, font=subtitle_font, fill=magenta)

    # Detail line
    detail = "Encrypt text in plain sight. The browser reads it. curl sees nonsense."
    dbbox = draw.textbbox((0, 0), detail, font=detail_font)
    dw = dbbox[2] - dbbox[0]
    dx = (width - dw) // 2
    dy = sy + 70
    draw.text((dx, dy), detail, font=detail_font, fill=white)

    img.save(str(dest), "PNG")
    print(f"Preview image saved to {dest} ({dest.stat().st_size:,} bytes)")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    # Only clean fonts, preserve HTML/CSS and preview image
    for f in FONTS_DIR.glob("*.woff2"):
        f.unlink()

    tmp = Path(tempfile.gettempdir())
    raw_var = tmp / "lora-variable.ttf"
    raw_static = tmp / "lora-static.ttf"
    base_subset = FONTS_DIR / "lora-base.woff2"

    download_font(raw_var)
    make_static_regular(raw_var, raw_static)
    subset_to_ascii(raw_static, base_subset)

    print("\nGenerating 25 cipher fonts...")
    for shift in range(1, 26):
        build_cipher_font(base_subset, FONTS_DIR / f"caesar-shift-{shift}.woff2", shift)

    total = sum(f.stat().st_size for f in FONTS_DIR.glob("*.woff2"))
    print(f"\nTotal font assets: {total:,} bytes ({total/1024:.1f} KB)")

    # Generate preview image using the static TTF (better for Pillow)
    print("\nGenerating social preview image...")
    generate_preview_image(raw_static, ASSETS_DIR / "preview.png")

    print("\nBuild complete!")


if __name__ == "__main__":
    main()
