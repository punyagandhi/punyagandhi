"""
make_ascii_svg.py

Converts a prepped grayscale photo into a self-typing, monochrome ASCII art SVG.

Usage:
    python scripts/make_ascii_svg.py source-prepped.png avi-ascii.svg

Design choices (on purpose):
  - Single gray fill color -- rainbow/per-character coloring reads as noisy.
  - Rows wipe in left-to-right, staggered top to bottom, then freeze
    (prints once, no looping).
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

RAMP = " .`:-=+*cs#%@"  # light (sparse) -> dark (dense); leading space = blank
COLS = 140
ROWS = 74
CHAR_W = 5.2   # px per character cell (monospace-dependent, tune to taste)
CHAR_H = 10.0
FONT_SIZE = 9
FILL_COLOR = "#c9d1d9"          # single light-gray fill
BG_COLOR = "none"                # transparent background
ROW_DURATION = 0.35               # seconds for one row's wipe-in
ROW_STAGGER = 0.045                # seconds between each row starting


def image_to_ascii_grid(path: Path, cols: int, rows: int) -> list[str]:
    img = Image.open(path).convert("L")
    # a touch of blur before downsampling stops single noisy pixels from
    # each becoming their own stray, out-of-place character
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    # aspect correction: character cells are taller than they are wide,
    # so we don't just squash the image to cols x rows directly.
    resized = img.resize((cols, rows), Image.LANCZOS)
    pixels = np.array(resized)

    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = pixels[r, c]  # 0 = black, 255 = white
            # invert so dark pixels -> dense characters
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines: list[str]) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    row_svgs = []
    for i, line in enumerate(lines):
        y = (i + 1) * CHAR_H - 3
        begin = i * ROW_STAGGER
        clip_id = f"clip{i}"
        text_escaped = escape_xml(line)

        row_svgs.append(f"""
    <clipPath id="{clip_id}">
      <rect x="0" y="{y - CHAR_H + 3}" width="0" height="{CHAR_H}">
        <animate attributeName="width" from="0" to="{width}"
                 begin="{begin:.3f}s" dur="{ROW_DURATION}s"
                 fill="freeze" calcMode="linear" />
      </rect>
    </clipPath>""")

    text_elements = []
    for i, line in enumerate(lines):
        y = (i + 1) * CHAR_H - 3
        clip_id = f"clip{i}"
        text_escaped = escape_xml(line)
        text_elements.append(
            f'    <text x="0" y="{y}" clip-path="url(#{clip_id})" '
            f'xml:space="preserve">{text_escaped}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  <defs>{''.join(row_svgs)}
  </defs>
  <style>
    text {{
      font-family: 'Courier New', monospace;
      font-size: {FONT_SIZE}px;
      fill: {FILL_COLOR};
      white-space: pre;
    }}
  </style>
  <rect width="100%" height="100%" fill="{BG_COLOR}" />
{chr(10).join(text_elements)}
</svg>
"""
    return svg


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/make_ascii_svg.py source-prepped.png output.svg")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    print("Building ASCII grid...")
    lines = image_to_ascii_grid(input_path, COLS, ROWS)

    print("Rendering SVG with wipe-in animation...")
    svg = build_svg(lines)

    output_path.write_text(svg, encoding="utf-8")
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    main()