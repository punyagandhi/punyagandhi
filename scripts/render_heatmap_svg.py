"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day grid of
rounded, colored boxes -- animated as a diagonal slide-down reveal that
plays once, plus a legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py contrib-heatmap.svg
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PALETTE = [
    "#161b22",  # level 0 -- no contributions
    "#0e4429",  # level 1
    "#006d32",  # level 2
    "#26a641",  # level 3
    "#39d353",  # level 4
    "#69f0a0",  # level 5 -- neon top end
]

BOX_SIZE = 11
BOX_GAP = 3
CELL = BOX_SIZE + BOX_GAP
LEFT_PADDING = 30   # room for day-of-week labels
TOP_PADDING = 20     # room for month labels
LEGEND_H = 24
FOOTER_H = 26

STAGGER_PER_DIAGONAL = 0.025  # seconds between each diagonal wave
BOX_DUR = 0.28

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def weeks_from_days(days: list[dict]) -> list[list[dict | None]]:
    """Group days into a list of weeks, each week a list of 7 day-slots
    (Sun-Sat), aligned to actual weekday so the grid matches GitHub's."""
    if not days:
        return []

    weeks = []
    current_week: list[dict | None] = [None] * 7

    first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    # pad the first week so day-of-week alignment is correct
    start_weekday = (first_date.weekday() + 1) % 7  # convert Mon=0 -> Sun=0

    idx = start_weekday
    for day in days:
        current_week[idx] = day
        idx += 1
        if idx == 7:
            weeks.append(current_week)
            current_week = [None] * 7
            idx = 0

    if any(d is not None for d in current_week):
        weeks.append(current_week)

    return weeks


def month_label_positions(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Return (week_index, month_name) pairs for where a new month starts."""
    labels = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            month = int(day["date"][5:7])
            if month != last_month:
                labels.append((w_idx, MONTH_LABELS[month - 1]))
                last_month = month
            break
    return labels


def build_svg(data: dict) -> str:
    days = data.get("days", [])
    stats = data.get("stats", {})
    username = data.get("username", "")

    weeks = weeks_from_days(days)
    num_weeks = len(weeks)

    grid_width = num_weeks * CELL
    grid_height = 7 * CELL

    width = LEFT_PADDING + grid_width + 10
    height = TOP_PADDING + grid_height + LEGEND_H + FOOTER_H + 10

    boxes_svg = []
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week):
            if day is None:
                continue
            level = max(0, min(day.get("level", 0), len(PALETTE) - 1))
            color = PALETTE[level]
            x = LEFT_PADDING + w_idx * CELL
            y = TOP_PADDING + d_idx * CELL

            # diagonal wave: boxes on the same (week + day) diagonal
            # animate together, sweeping top-left to bottom-right
            diagonal = w_idx + d_idx
            begin = diagonal * STAGGER_PER_DIAGONAL

            count = day.get("count", 0)
            date_str = day.get("date", "")

            boxes_svg.append(f"""
    <rect x="{x}" y="{y}" width="{BOX_SIZE}" height="{BOX_SIZE}" rx="2"
          fill="{color}" opacity="0">
      <title>{count} contributions on {date_str}</title>
      <animate attributeName="opacity" from="0" to="1"
               begin="{begin:.3f}s" dur="{BOX_DUR}s" fill="freeze" />
    </rect>""")

    month_labels_svg = []
    for w_idx, label in month_label_positions(weeks):
        x = LEFT_PADDING + w_idx * CELL
        month_labels_svg.append(
            f'    <text x="{x}" y="{TOP_PADDING - 6}" font-size="11" fill="#8b949e">{label}</text>'
        )

    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    day_labels_svg = []
    for d_idx, label in enumerate(day_labels):
        if not label:
            continue
        y = TOP_PADDING + d_idx * CELL + BOX_SIZE - 1
        day_labels_svg.append(
            f'    <text x="0" y="{y}" font-size="10" fill="#8b949e">{label}</text>'
        )

    legend_y = TOP_PADDING + grid_height + 20
    legend_x = LEFT_PADDING
    legend_svg = [f'    <text x="{legend_x}" y="{legend_y}" font-size="11" fill="#8b949e">Less</text>']
    swatch_x = legend_x + 34
    for i, color in enumerate(PALETTE):
        legend_svg.append(
            f'    <rect x="{swatch_x + i * (BOX_SIZE + 3)}" y="{legend_y - BOX_SIZE + 2}" '
            f'width="{BOX_SIZE}" height="{BOX_SIZE}" rx="2" fill="{color}" />'
        )
    legend_svg.append(
        f'    <text x="{swatch_x + len(PALETTE) * (BOX_SIZE + 3) + 6}" y="{legend_y}" '
        f'font-size="11" fill="#8b949e">More</text>'
    )

    total = stats.get("total_last_year", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = f"{total:,} contributions in the last year   ·   current streak {streak}   ·   longest streak {longest}"
    footer_y = height - 8

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  <style>
    text {{ font-family: 'Courier New', monospace; }}
  </style>
  <rect width="100%" height="100%" fill="none" />

{chr(10).join(month_labels_svg)}
{chr(10).join(day_labels_svg)}
{chr(10).join(boxes_svg)}

{chr(10).join(legend_svg)}

  <text x="{LEFT_PADDING}" y="{footer_y}" font-size="11" fill="#8b949e">{footer_text}</text>
</svg>
"""
    return svg


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/render_heatmap_svg.py output.svg")
        sys.exit(1)

    data_path = Path("data/contributions.json")
    if not data_path.exists():
        print(f"Missing {data_path} -- run fetch_contributions.py first.")
        sys.exit(1)

    data = load_data(data_path)
    svg = build_svg(data)

    output_path = Path(sys.argv[1])
    output_path.write_text(svg, encoding="utf-8")
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    main()