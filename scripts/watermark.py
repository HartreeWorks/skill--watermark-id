#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11", "pillow-heif>=0.20"]
# ///
"""Stamp a tiled diagonal watermark across an identity document.

Images (JPEG, PNG, HEIC, WebP) and PDFs are accepted. PDFs are rasterised
with pdftoppm, so the output is flattened: the watermark cannot be lifted off
by editing the file. Metadata (EXIF, GPS) is dropped from every output.
"""

import argparse
import datetime as dt
import math
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
PDF_DPI = 200

TEMPLATES = {
    "fr": "Copie pour {recipient} · {purpose} · {date} · Toute autre utilisation interdite",
    "en": "Copy for {recipient} · {purpose} · {date} · Not valid for any other use",
}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def stamp(page: Image.Image, text: str, opacity: int) -> Image.Image:
    page = ImageOps.exif_transpose(page).convert("RGB")
    w, h = page.size
    size = max(14, round(min(w, h) / 30))
    font = next((ImageFont.truetype(f, size) for f in FONTS if Path(f).exists()),
                None) or ImageFont.load_default(size)

    # Draw rows on a square canvas big enough to cover the page at any angle,
    # rotate it, then crop the centre back to the page size.
    side = math.ceil(math.hypot(w, h))
    layer = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    line = f"{text}     "
    line_w = draw.textlength(line, font=font)
    row = (line * (math.ceil(side / line_w) + 2))
    step = round(size * 3.2)
    for i, y in enumerate(range(-step, side + step, step)):
        offset = -(i % 2) * line_w / 2
        draw.text((offset, y), row, font=font, fill=(40, 40, 40, opacity),
                  stroke_width=max(1, size // 18), stroke_fill=(255, 255, 255, opacity // 2))
    layer = layer.rotate(30, resample=Image.Resampling.BICUBIC)
    left, top = (side - w) // 2, (side - h) // 2
    layer = layer.crop((left, top, left + w, top + h))

    return Image.alpha_composite(page.convert("RGBA"), layer).convert("RGB")


def pdf_pages(path: Path, tmp: Path) -> list[Image.Image]:
    subprocess.run(["pdftoppm", "-r", str(PDF_DPI), "-png", str(path), str(tmp / "p")], check=True)
    return [Image.open(p) for p in sorted(tmp.glob("p-*.png"))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--recipient", required=True, help="who receives the copy, e.g. 'Example Bank'")
    ap.add_argument("--purpose", required=True, help="why, e.g. 'ouverture contrat assurance vie'")
    ap.add_argument("--lang", choices=TEMPLATES, default="fr")
    ap.add_argument("--date", default=dt.date.today().strftime("%d/%m/%Y"))
    ap.add_argument("--text", help="full watermark text, replacing the template")
    ap.add_argument("--opacity", type=int, default=95, help="0-255 (default 95)")
    ap.add_argument("--output", type=Path, help="default: <input>-watermarked-<recipient>.<ext>")
    args = ap.parse_args()

    src = args.input.expanduser().resolve()
    text = args.text or TEMPLATES[args.lang].format(
        recipient=args.recipient, purpose=args.purpose, date=args.date)
    is_pdf = src.suffix.lower() == ".pdf"
    ext = ".pdf" if is_pdf else (".png" if src.suffix.lower() == ".png" else ".jpg")
    out = args.output or src.with_name(f"{src.stem}-watermarked-{slug(args.recipient)}{ext}")

    with tempfile.TemporaryDirectory() as tmp:
        pages = pdf_pages(src, Path(tmp)) if is_pdf else [Image.open(src)]
        stamped = [stamp(p, text, args.opacity) for p in pages]

    if is_pdf:
        stamped[0].save(out, "PDF", resolution=PDF_DPI, save_all=True, append_images=stamped[1:])
    elif ext == ".png":
        stamped[0].save(out, "PNG")
    else:
        stamped[0].save(out, "JPEG", quality=90)

    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
