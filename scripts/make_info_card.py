"""
make_info_card.py

Hand-builds a neofetch-style SVG info card: a title bar, then key/value rows
that fade + slide in on a short stagger.

Usage:
    python scripts/make_info_card.py info-card.svg

Set STATIC=1 to emit a frozen (already fully faded-in) frame, useful for
local Quick Look previews where SVG animation doesn't play.
"""

import os
import sys
from pathlib import Path

# --- Edit this content to update the card -----------------------------
USERNAME = "punya@github"
ROWS = [
    ("Role", "Fullstack Developer, Researcher"),
    ("Now", "Building IVISYX, Prepping for ISEF and STS"),
    ("Stack", "Arduino, C++"),
]
# ------------------------------------------------------------------------

WIDTH = 490
TITLE_BAR_H = 34
ROW_H = 34
PADDING_TOP = 16
PADDING_LEFT = 20
FONT_SIZE = 15
LABEL_COLOR = "#39d353"     # green, like a neofetch key
VALUE_COLOR = "#c9d1d9"     # light gray, like a neofetch value
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
ROW_STAGGER = 0.18
FADE_DUR = 0.4


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool) -> str:
    height = TITLE_BAR_H + PADDING_TOP + len(ROWS) * ROW_H + 16

    rows_svg = []
    for i, (label, value) in enumerate(ROWS):
        y = TITLE_BAR_H + PADDING_TOP + i * ROW_H + FONT_SIZE
        begin = i * ROW_STAGGER
        label_esc = escape_xml(label)
        value_esc = escape_xml(value)

        if static:
            # frozen, fully-visible frame -- no animation elements
            rows_svg.append(f"""
    <g>
      <text x="{PADDING_LEFT}" y="{y}" font-weight="bold" fill="{LABEL_COLOR}">{label_esc}</text>
      <text x="{PADDING_LEFT + 90}" y="{y}" fill="{VALUE_COLOR}">{value_esc}</text>
    </g>""")
        else:
            rows_svg.append(f"""
    <g opacity="0" transform="translate(-12,0)">
      <animate attributeName="opacity" from="0" to="1"
               begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze" />
      <animateTransform attributeName="transform" type="translate"
                         from="-12,0" to="0,0"
                         begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze" />
      <text x="{PADDING_LEFT}" y="{y}" font-weight="bold" fill="{LABEL_COLOR}">{label_esc}</text>
      <text x="{PADDING_LEFT + 90}" y="{y}" fill="{VALUE_COLOR}">{value_esc}</text>
    </g>""")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}">
  <style>
    text {{
      font-family: 'Courier New', monospace;
      font-size: {FONT_SIZE}px;
    }}
  </style>
  <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8"
        fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1.5" />

  <!-- title bar -->
  <rect x="0" y="0" width="{WIDTH}" height="{TITLE_BAR_H}" rx="8"
        fill="{BORDER_COLOR}" />
  <rect x="0" y="{TITLE_BAR_H - 8}" width="{WIDTH}" height="8" fill="{BORDER_COLOR}" />
  <circle cx="18" cy="{TITLE_BAR_H / 2}" r="5" fill="#ff5f56" />
  <circle cx="36" cy="{TITLE_BAR_H / 2}" r="5" fill="#ffbd2e" />
  <circle cx="54" cy="{TITLE_BAR_H / 2}" r="5" fill="#27c93f" />
  <text x="{WIDTH / 2}" y="{TITLE_BAR_H / 2 + 5}" text-anchor="middle" fill="#8b949e">{escape_xml(USERNAME)}</text>

{chr(10).join(rows_svg)}
</svg>
"""
    return svg


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_info_card.py output.svg")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    static = os.environ.get("STATIC") == "1"

    svg = build_svg(static)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    main()