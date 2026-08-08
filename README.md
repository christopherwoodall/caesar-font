# Caesar Cipher Font

Type a message, pick a Caesar shift (1–25), and generate a custom cipher font. The HTML source is encrypted with your chosen shift. The custom web font reverses that shift inside the browser, rendering readable text from scrambled source code. If you `curl` the page, you see pure nonsense. If you open it in a browser, the message appears.

## Live Demo

- **Generator** (create your own cipher font): [`christopherwoodall.github.io/caesar-font/`](https://christopherwoodall.github.io/caesar-font/)
- **Demo** (see what `curl` sees): [`christopherwoodall.github.io/caesar-font/demo.html`](https://christopherwoodall.github.io/caesar-font/demo.html)

## Features

- **Interactive generator**: Type text, choose a shift (1–25), or randomize
- **Side-by-side preview**: See your plaintext and the encrypted source next to each other
- **Download the cipher font**: Get a WOFF2 file for your chosen shift
- **Generate a standalone page**: Download a self-contained HTML file with encrypted text and the font embedded as base64
- **Copy encrypted text**: Grab the ciphertext for your own projects

## How It Works

1. **Encrypt the text**: Every letter A–Z and a–z is shifted forward by *N* places in the alphabet.
2. **Build the cipher font**: Using `fontTools`, we rewrite the font’s `cmap` table so each character maps to the glyph *N places behind* it. When the browser sees an encrypted letter, it draws the original letter’s shape.
3. **Serve both**: The HTML contains encrypted text. The browser uses the custom font to decrypt it visually. Anyone without the font file sees only the ciphertext.

## Build

Install dependencies (requires Python ≥3.10):

```bash
uv sync
```

Generate the 25 cipher fonts:

```bash
uv run python build.py
```

This creates 25 subset WOFF2 fonts (shifts 1–25) in `docs/assets/fonts/`. Each font is ~13 KB.

## GitHub Pages

1. Push this repo to GitHub.
2. Go to **Settings → Pages** and set the source to the `/docs` folder on the `main` branch.
3. Visit `https://christopherwoodall.github.io/caesar-font/` for the generator and `/demo.html` for the demo.

## Font Attribution

This project uses **Lora**, a typeface designed by Cyreal and licensed under the [SIL Open Font License 1.1](https://scripts.sil.org/OFL). The original font is available at [Google Fonts](https://fonts.google.com/specimen/Lora).

## License

The source code is MIT. The original Lora font remains under the SIL Open Font License.
