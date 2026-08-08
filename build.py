#!/usr/bin/env python3
"""Build the Caesar cipher font and generate HTML pages."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode

import requests
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

# ─── Configuration ───
SHIFT = 7
FONT_NAME = "Lora"
FONT_URL = "https://fonts.google.com/download?family=Lora"  # Actually a zip
# Better: direct GitHub raw URL for the Regular TTF
LORA_REGULAR_URL = (
    "https://github.com/google/fonts/raw/main/ofl/lora/"
    "Lora%5Bwght%5D.ttf"
)
LORA_STATIC_URL = (
    "https://github.com/google/fonts/raw/main/ofl/lora/"
    "Lora-Regular.ttf"
)

CONTENT = """Welcome to the Caesar Cipher Font.

This page is encrypted in plain sight.
If you view the source of this HTML file, you will see scrambled letters.
But your browser is using a special font that shifts every glyph by seven places in the alphabet.

The font is the key.
Without it, the text is nonsense.
With it, everything becomes readable.

This is a playful demonstration of how presentation and content can be separated.
What you see is not always what you get.
"""

DOCS_DIR = Path(__file__).parent / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
CSS_DIR = ASSETS_DIR / "css"

# ─── Helpers ───


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


def download_font(dest: Path) -> Path:
    """Download Lora-Regular.ttf to *dest*."""
    urls = [
        LORA_STATIC_URL,
        "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            if len(resp.content) < 1024:
                continue
            dest.write_bytes(resp.content)
            print(f"Downloaded font from {url}")
            return dest
        except Exception as e:
            print(f"Failed to download from {url}: {e}")
            continue
    raise RuntimeError("Could not download Lora font")


def build_cipher_font(src_path: Path, dest_path: Path, shift: int) -> None:
    """Create a Caesar-cipher variant of *src_path* and write it to *dest_path*.

    The font applies the *inverse* shift so that encrypted text renders as plaintext.
    """
    font = TTFont(str(src_path))

    # Build a map of current cmap entries: unicode -> glyphName
    cmap_tables = font["cmap"].tables
    unicode_to_glyph = {}
    for table in cmap_tables:
        if table.isUnicode():
            for code, glyph_name in table.cmap.items():
                if code not in unicode_to_glyph:
                    unicode_to_glyph[code] = glyph_name

    # Build the inverse-shifted mapping so the font decrypts the text
    inverse = (-shift) % 26
    new_cmap = {}
    for code in range(0x20, 0x7F):  # Basic ASCII printable
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

    # Replace all cmap tables with a single clean format-4 table
    font["cmap"].tables = []
    cmap4 = CmapSubtable.newSubtable(4)
    cmap4.platformID = 3
    cmap4.platEncID = 1
    cmap4.language = 0
    cmap4.cmap = new_cmap
    font["cmap"].tables.append(cmap4)

    # Also add a format-12 table for full Unicode coverage (keeps same mapping)
    cmap12 = CmapSubtable.newSubtable(12)
    cmap12.platformID = 3
    cmap12.platEncID = 10
    cmap12.language = 0
    cmap12.cmap = new_cmap
    font["cmap"].tables.append(cmap12)

    # Save as WOFF2
    font.flavor = "woff2"
    font.save(str(dest_path))
    print(f"Cipher font saved to {dest_path}")


# ─── CSS ───

STYLE_CSS = """/* ─── Reset & Base ─── */
*,*::before,*::after{box-sizing:border-box;margin:0}
html,body{min-height:100vh}
body{
  background:#0a0a0f;
  color:#e8e6f0;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
}

/* ─── Cyberpunk Grid Overlay ─── */
body::before{
  content:"";
  position:fixed;
  inset:0;
  pointer-events:none;
  z-index:0;
  background-image:
    linear-gradient(rgba(0,240,255,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,240,255,.03) 1px,transparent 1px);
  background-size:40px 40px;
  mask-image:linear-gradient(to bottom,transparent 0%,black 20%,black 80%,transparent 100%);
  -webkit-mask-image:linear-gradient(to bottom,transparent 0%,black 20%,black 80%,transparent 100%);
}

/* ─── Scanlines ─── */
body::after{
  content:"";
  position:fixed;
  inset:0;
  pointer-events:none;
  z-index:1;
  background:repeating-linear-gradient(
    0deg,
    transparent 0px,
    transparent 2px,
    rgba(0,0,0,.15) 2px,
    rgba(0,0,0,.15) 4px
  );
  opacity:.3;
}

/* ─── Typography ─── */
@font-face{
  font-family:"CaesarLora";
  src:url("../fonts/caesar-lora.woff2") format("woff2");
  font-weight:400;
  font-style:normal;
  font-display:swap;
}

.cipher{
  font-family:"CaesarLora",serif;
  font-size:1.25rem;
  color:#f0eef5;
  text-shadow:0 0 12px rgba(0,240,255,.25),0 0 2px rgba(0,240,255,.1);
}

h1,h2,h3{
  font-family:system-ui,sans-serif;
  font-weight:700;
  letter-spacing:.05em;
  text-transform:uppercase;
  color:#00f0ff;
  text-shadow:0 0 20px rgba(0,240,255,.4),0 0 4px rgba(0,240,255,.2);
  margin-bottom:1rem;
}

h1{font-size:2.5rem}
h2{font-size:1.75rem;color:#ff00a0;text-shadow:0 0 20px rgba(255,0,160,.4)}

/* ─── Layout ─── */
.container{
  position:relative;
  z-index:2;
  max-width:720px;
  margin:0 auto;
  padding:3rem 1.5rem;
}

.card{
  background:rgba(255,255,255,.03);
  border:1px solid rgba(0,240,255,.15);
  border-radius:18px;
  padding:2rem;
  margin-bottom:2rem;
  backdrop-filter:blur(4px);
  box-shadow:0 8px 32px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.05);
  position:relative;
  overflow:hidden;
}

.card::before{
  content:"";
  position:absolute;
  top:-50%;left:-50%;
  width:200%;height:200%;
  background:radial-gradient(circle,rgba(255,183,197,.06) 0%,transparent 70%);
  pointer-events:none;
}

/* ─── Roman Column Accents ─── */
.card.roman{
  border-left:4px solid #c9a227;
  border-image:linear-gradient(to bottom,#c9a227,#ff00a0) 1;
}

/* ─── Kawaii Badges ─── */
.badge{
  display:inline-block;
  background:linear-gradient(135deg,#ffb7c5,#d8b4fe);
  color:#0a0a0f;
  font-size:.75rem;
  font-weight:700;
  padding:.25rem .75rem;
  border-radius:999px;
  margin-bottom:1rem;
  text-shadow:none;
  box-shadow:0 2px 8px rgba(255,183,197,.3);
}

/* ─── Code / Pre ─── */
pre,code{
  font-family:"SF Mono",Monaco,Inconsolata,"Fira Code",monospace;
  font-size:.9rem;
}

pre{
  background:rgba(0,0,0,.4);
  border:1px solid rgba(255,0,160,.2);
  border-radius:12px;
  padding:1rem;
  overflow-x:auto;
  color:#ffb7c5;
  box-shadow:inset 0 0 20px rgba(255,0,160,.05);
}

/* ─── Links ─── */
a{
  color:#00f0ff;
  text-decoration:none;
  border-bottom:1px solid rgba(0,240,255,.3);
  transition:all .2s;
}
a:hover{
  color:#ffb7c5;
  border-bottom-color:#ffb7c5;
  text-shadow:0 0 12px rgba(255,183,197,.4);
}

/* ─── Buttons ─── */
.btn{
  display:inline-block;
  background:linear-gradient(135deg,#00f0ff,#ff00a0);
  color:#0a0a0f;
  font-weight:700;
  padding:.75rem 1.5rem;
  border-radius:12px;
  border:none;
  cursor:pointer;
  text-shadow:none;
  box-shadow:0 4px 16px rgba(0,240,255,.3);
  transition:transform .15s,box-shadow .15s;
}
.btn:hover{
  transform:translateY(-2px);
  box-shadow:0 6px 24px rgba(0,240,255,.4);
}

/* ─── Toggle ─── */
.raw-mode .cipher{
  font-family:monospace;
  color:#ff00a0;
  text-shadow:0 0 12px rgba(255,0,160,.4);
}

/* ─── Footer ─── */
footer{
  text-align:center;
  padding:2rem 0;
  font-size:.8rem;
  color:rgba(232,230,240,.4);
}

/* ─── Responsive ─── */
@media(max-width:600px){
  h1{font-size:1.75rem}
  .cipher{font-size:1.1rem}
  .card{padding:1.5rem}
}
"""


# ─── HTML Templates ───

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caesar Cipher Font — Live</title>
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<div class="container">
  <div class="card roman">
    <span class="badge">🔐 Live Decryption</span>
    <h1>Caesar Cipher Font</h1>
    <p class="cipher">
{encrypted_content}
    </p>
    <button class="btn" onclick="document.body.classList.toggle('raw-mode')">Toggle Raw Source</button>
    <p style="margin-top:1rem;font-size:.85rem;color:rgba(232,230,240,.6)">
      Try <code>curl {page_url}</code> and compare what you see.
    </p>
  </div>
  <div class="card">
    <span class="badge">ℹ️ How It Works</span>
    <h2>The Mechanism</h2>
    <p class="cipher">
{encrypted_explanation_1}
    </p>
    <p class="cipher">
{encrypted_explanation_2}
    </p>
  </div>
  <footer>
    <p>Made with 💜 and a little bit of glyph trickery.</p>
  </footer>
</div>
</body>
</html>
"""

DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caesar Cipher Font — Demo</title>
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<div class="container">
  <div class="card">
    <span class="badge">👀 What curl sees</span>
    <h1>Encrypted Source</h1>
    <p style="color:rgba(232,230,240,.7);margin-bottom:1rem">
      This is the raw HTML source. No special font is loaded here. Every letter you see below is literally what is stored in the file.
    </p>
    <pre><code>{encrypted_content_escaped}</code></pre>
  </div>
  <div class="card roman">
    <span class="badge">🛠️ Try it yourself</span>
    <h2>Curl Command</h2>
    <pre><code>curl -s {page_url} | grep -A 20 '&lt;p class="cipher"&gt;'</code></pre>
    <p style="color:rgba(232,230,240,.7);margin-top:1rem">
      The output will look exactly like the encrypted text above. The browser on the <a href="index.html">live page</a> uses a custom font to map those scrambled letters back into readable glyphs.
    </p>
  </div>
  <div class="card">
    <span class="badge">📖 Explanation</span>
    <h2>Why This Works</h2>
    <p>
      Web fonts are powerful. A font file contains a table that maps Unicode characters to glyph outlines. By editing that table, we can say: "when the browser sees the letter <code>A</code>, draw the shape of <code>H</code> instead." We do this for every letter, shifting by a fixed amount.
    </p>
    <p>
      The HTML contains the shifted text. The font contains the reverse shift. Together they cancel out, revealing the hidden message. The source remains encrypted for anyone who does not have the font file.
    </p>
  </div>
  <footer>
    <p><a href="index.html">← View the live decrypted page</a></p>
  </footer>
</div>
</body>
</html>
"""


EXPLANATION_1 = """The HTML source of this page contains encrypted text. Every letter has been shifted forward by seven places in the alphabet. The browser is loading a custom font that shifts every glyph backward by the same amount. The result is readable text created from an unreadable source."""

EXPLANATION_2 = """The font is the decryption key. Without it, the page is pure nonsense. With it, the message appears as if by magic. This is steganography through typography."""


# ─── Main ───


def main() -> None:
    # Clean and create directories
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    FONTS_DIR.mkdir(parents=True)
    CSS_DIR.mkdir(parents=True)

    # Download font
    raw_font = Path(tempfile.gettempdir()) / "lora-regular.ttf"
    download_font(raw_font)

    # Build cipher font (inverse shift so the font decrypts)
    cipher_font = FONTS_DIR / "caesar-lora.woff2"
    build_cipher_font(raw_font, cipher_font, SHIFT)

    # Write CSS
    (CSS_DIR / "style.css").write_text(STYLE_CSS, encoding="utf-8")

    # Encrypt content
    encrypted = caesar_shift(CONTENT, SHIFT)
    encrypted_lines = ["      " + line for line in encrypted.splitlines()]
    encrypted_for_html = "\n".join(encrypted_lines)
    encrypted_escaped = (
        encrypted.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    # Encrypt explanations for the live page
    encrypted_explanation_1 = caesar_shift(EXPLANATION_1, SHIFT)
    encrypted_explanation_1_lines = ["      " + line for line in encrypted_explanation_1.splitlines()]
    encrypted_explanation_1_html = "\n".join(encrypted_explanation_1_lines)

    encrypted_explanation_2 = caesar_shift(EXPLANATION_2, SHIFT)
    encrypted_explanation_2_lines = ["      " + line for line in encrypted_explanation_2.splitlines()]
    encrypted_explanation_2_html = "\n".join(encrypted_explanation_2_lines)

    page_url = "https://your-username.github.io/caesar-font/index.html"
    # For local testing, use relative paths; GitHub Pages URL can be updated later

    # Write pages
    index = INDEX_HTML.format(
        encrypted_content=encrypted_for_html,
        encrypted_explanation_1=encrypted_explanation_1_html,
        encrypted_explanation_2=encrypted_explanation_2_html,
        page_url=page_url,
    )
    demo = DEMO_HTML.format(
        encrypted_content_escaped=encrypted_escaped,
        page_url=page_url,
    )

    (DOCS_DIR / "index.html").write_text(index, encoding="utf-8")
    (DOCS_DIR / "demo.html").write_text(demo, encoding="utf-8")

    print("Build complete!")
    print(f"  → {DOCS_DIR / 'index.html'}")
    print(f"  → {DOCS_DIR / 'demo.html'}")
    print(f"  → {cipher_font}")


if __name__ == "__main__":
    main()
