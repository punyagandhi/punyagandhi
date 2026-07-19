"""
make_info_card.py

Hand-builds a neofetch-style SVG info card: a neon-purple terminal panel
with a falling-binary background effect, title bar, then key/value rows
that fade + slide in on a short stagger.

Usage:
    python scripts/make_info_card.py info-card.svg

Set STATIC=1 to emit a frozen (already fully faded-in) frame, useful for
local Quick Look previews where SVG animation doesn't play.
"""

import os
import random
import sys
from pathlib import Path

# --- Edit this content to update the card -----------------------------
USERNAME = "punya@github"
ROWS = [
    ("Role", "Fullstack Developer, AI Builder, Researcher"),
    ("Now", "Scaling IVISYX, ISEF & STS Prep, IEEE etc. Prep"),
    ("Stack", "Arduino, C++, Python, JS, React, Git, LaTeX, Linux"),
]
# ------------------------------------------------------------------------

WIDTH = 660
TITLE_BAR_H = 34
ROW_H = 40
PADDING_TOP = 26
PADDING_LEFT = 28
FONT_SIZE = 16

# neon purple palette
LABEL_COLOR = "#d896ff"
VALUE_COLOR = "#e6d1ff"
BG_TOP_COLOR = "#1a0b2e"
BG_BOTTOM_COLOR = "#0a0414"
BORDER_COLOR = "#9d4edd"
TITLE_BAR_COLOR = "#2d1b4e"
GLOW_COLOR = "#c77dff"

ROW_STAGGER = 0.2
FADE_DUR = 0.45

# --- falling binary background settings ---
RAIN_COLUMN_COUNT = 14
RAIN_CHARS_PER_COLUMN = 26
RAIN_FONT_SIZE = 13
RAIN_MIN_DURATION = 4.0
RAIN_MAX_DURATION = 9.0
RAIN_OPACITY = 0.16
RAIN_CHARSET = "01αβΔ$*#@&%§"

random.seed(7)  # stable output between runs, not re-randomized every build


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rain_columns(width: int, height: int) -> str:
    """A grid of columns of falling 0/1 characters, looping continuously
    behind the card content -- purely decorative, low-opacity so it
    doesn't fight with the readable text in front of it."""
    col_spacing = width / RAIN_COLUMN_COUNT
    columns = []

    for i in range(RAIN_COLUMN_COUNT):
        x = int(i * col_spacing + col_spacing / 2)
        duration = round(random.uniform(RAIN_MIN_DURATION, RAIN_MAX_DURATION), 2)
        delay = round(random.uniform(0, duration), 2)

        digits = "".join(random.choice(RAIN_CHARSET) for _ in range(RAIN_CHARS_PER_COLUMN))
        tspans = "".join(
            f'<tspan x="{x}" dy="{RAIN_FONT_SIZE + 4}">{escape_xml(d)}</tspan>'
            for d in digits
        )

        columns.append(
            f'    <text class="rain-col" x="{x}" y="-{RAIN_CHARS_PER_COLUMN * (RAIN_FONT_SIZE + 4)}" '
            f'style="animation-duration:{duration}s; animation-delay:-{delay}s;" '
            f'font-size="{RAIN_FONT_SIZE}" fill="{GLOW_COLOR}" opacity="{RAIN_OPACITY}">'
            f'{tspans}</text>'
        )

    return "\n".join(columns)


def build_svg(static: bool) -> str:
    height = TITLE_BAR_H + PADDING_TOP + len(ROWS) * ROW_H + 26

    rows_svg = []
    for i, (label, value) in enumerate(ROWS):
        y = TITLE_BAR_H + PADDING_TOP + i * ROW_H + FONT_SIZE
        begin = i * ROW_STAGGER
        label_esc = escape_xml(label)
        value_esc = escape_xml(value)

        if static:
            rows_svg.append(f"""
    <g>
      <text x="{PADDING_LEFT}" y="{y}" font-weight="bold" fill="{LABEL_COLOR}" filter="url(#neonGlow)">{label_esc}</text>
      <text x="{PADDING_LEFT + 110}" y="{y}" fill="{VALUE_COLOR}">{value_esc}</text>
    </g>""")
        else:
            rows_svg.append(f"""
    <g opacity="0" transform="translate(-12,0)">
      <animate attributeName="opacity" from="0" to="1"
               begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze" />
      <animateTransform attributeName="transform" type="translate"
                         from="-12,0" to="0,0"
                         begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze" />
      <text x="{PADDING_LEFT}" y="{y}" font-weight="bold" fill="{LABEL_COLOR}" filter="url(#neonGlow)">{label_esc}</text>
      <text x="{PADDING_LEFT + 110}" y="{y}" fill="{VALUE_COLOR}">{value_esc}</text>
    </g>""")

    rain_svg = build_rain_columns(WIDTH, height)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}">
  <defs>
    <linearGradient id="cardBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{BG_TOP_COLOR}" />
      <stop offset="100%" stop-color="{BG_BOTTOM_COLOR}" />
    </linearGradient>

    <filter id="neonGlow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="2.2" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <clipPath id="cardClip">
      <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="10" />
    </clipPath>
  </defs>

  <style>
    text {{
      font-family: 'Courier New', monospace;
      font-size: {FONT_SIZE}px;
    }}
    .rain-col {{
      animation-name: fall;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
    }}
    @keyframes fall {{
      from {{ transform: translateY(0); }}
      to   {{ transform: translateY({height + RAIN_CHARS_PER_COLUMN * (RAIN_FONT_SIZE + 4)}px); }}
    }}
  </style>

  <g clip-path="url(#cardClip)">
    <rect x="0" y="0" width="{WIDTH}" height="{height}" fill="url(#cardBg)" />

    <!-- falling binary background effect -->
{rain_svg}

    <!-- title bar -->
    <rect x="0" y="0" width="{WIDTH}" height="{TITLE_BAR_H}" fill="{TITLE_BAR_COLOR}" />
    <circle cx="18" cy="{TITLE_BAR_H / 2}" r="5" fill="#ff5f56" />
    <circle cx="36" cy="{TITLE_BAR_H / 2}" r="5" fill="#ffbd2e" />
    <circle cx="54" cy="{TITLE_BAR_H / 2}" r="5" fill="#27c93f" />
    <text x="{WIDTH / 2}" y="{TITLE_BAR_H / 2 + 5}" text-anchor="middle" fill="{LABEL_COLOR}" filter="url(#neonGlow)">{escape_xml(USERNAME)}</text>

{chr(10).join(rows_svg)}
  </g>

  <!-- outer neon border, drawn last so it sits on top of the clipped content -->
  <rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="10"
        fill="none" stroke="{BORDER_COLOR}" stroke-width="2" filter="url(#neonGlow)" />
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