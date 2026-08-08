# Caesar Cipher Font

A cyberpunk–Roman–kawaii web experiment where the **font is the decryption key**.

The HTML source is encrypted with a Caesar cipher (shift +7). A custom web font reverses that shift inside the browser, rendering readable text from scrambled source code. If you `curl` the page, you see pure nonsense. If you open it in a browser, the message appears.

## Live Demo

- **Decrypted page** (uses the cipher font): `docs/index.html`
- **Demo page** (shows raw garbled source + explanation): `docs/demo.html`

## How It Works

1. **Encrypt the text**: Every letter A–Z and a–z is shifted forward by 7 places in the alphabet.
2. **Build the cipher font**: Using `fontTools`, we rewrite the font’s `cmap` table so each character maps to the glyph *7 places behind* it. When the browser sees an encrypted letter, it draws the original letter’s shape.
3. **Serve both**: The HTML contains encrypted text. The browser uses the custom font to decrypt it visually. Anyone without the font file sees only the ciphertext.

## Build

Install dependencies (requires Python ≥3.10):

```bash
uv sync
```

Generate the font and pages:

```bash
uv run python build.py
```

This creates:
- `docs/index.html` — live page with the cipher font
- `docs/demo.html` — demo showing raw encrypted source
- `docs/assets/fonts/caesar-lora.woff2` — the custom cipher font

## GitHub Pages

1. Push this repo to GitHub.
2. Go to **Settings → Pages** and set the source to the `/docs` folder on the main branch.
3. Visit `https://<your-username>.github.io/caesar-font/` for the live page and `/demo.html` for the demo.

## Aesthetic

- **Cyberpunk**: dark base, neon cyan & magenta accents, scanline overlay, grid background
- **Roman**: classical serif body text (Lora), gold/bronze column borders
- **Kawaii**: soft pastel pink/lavender badges, rounded corners, cute glows
- **Readable**: high contrast, clear hierarchy, no clutter

## License

The source code is MIT. The original Lora font is licensed under the SIL Open Font License.

