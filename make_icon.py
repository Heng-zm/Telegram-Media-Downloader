#!/usr/bin/env python
"""
make_icon.py - Create a multi-size Windows .ico from a source image (PNG/JPG/SVG via Pillow)
Usage:
  python make_icon.py icon.png  # writes icon.ico in current dir
  python make_icon.py icon.png app.ico

The generated ICO embeds multiple sizes: 16, 24, 32, 48, 64, 128, 256 px.
Requires: Pillow (pip install pillow)
"""
import sys
from pathlib import Path
from typing import List, Tuple

SIZES: List[int] = [16, 24, 32, 48, 64, 128, 256]


def _ensure_pillow():
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        print("Pillow not installed. Install with: pip install pillow", file=sys.stderr)
        sys.exit(1)


def _load_image(src: Path):
    from PIL import Image
    img = Image.open(src)
    if img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")
    return img


def _build_resized_images(img, sizes: List[int]) -> List[Tuple[int, int]]:
    # Pillow's .save(ico, sizes=[...]) handles resizing internally; we just pass sizes
    # Ensure the source is large enough for highest size to preserve quality
    w, h = img.size
    if w < max(sizes) or h < max(sizes):
        print(f"Warning: source image is {w}x{h}, smaller than {max(sizes)}x{max(sizes)}; upscaling may reduce quality.")
    return [(s, s) for s in sizes]


def main(argv: List[str]) -> int:
    _ensure_pillow()
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python make_icon.py <src_image> [out_icon.ico]", file=sys.stderr)
        return 2
    src = Path(argv[1]).resolve()
    if len(argv) == 3:
        out = Path(argv[2]).resolve()
    else:
        out = src.with_suffix('.ico') if src.suffix.lower() != '.ico' else Path('icon.ico').resolve()
    if not src.exists():
        print(f"Source image not found: {src}", file=sys.stderr)
        return 1
    try:
        img = _load_image(src)
        sizes = _build_resized_images(img, SIZES)
        # Important: pass sizes list to embed multiple sizes
        img.save(out, format='ICO', sizes=sizes)
        print(f"Wrote multi-size ICO: {out}")
        print(f"Embedded sizes: {', '.join(str(s) for s in SIZES)} px")
        return 0
    except Exception as e:
        print(f"Error generating ICO: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
