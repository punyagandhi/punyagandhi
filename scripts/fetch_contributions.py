"""
fetch_contributions.py

Scrapes your public GitHub contribution calendar (no API token needed) and
saves the raw days + derived stats to data/contributions.json.

GitHub serves this calendar as plain HTML at:
    https://github.com/users/punyagandhi/contributions
-- the same fragment the profile page itself uses.

Usage:
    python scripts/fetch_contributions.py YOUR_GITHUB_USERNAME
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL_TEMPLATE = "https://github.com/users/punyagandhi/contributions"

# tooltip text looks like "18 contributions on July 20th." or
# "No contributions on July 20th."
COUNT_PATTERN = re.compile(r"^(No|\d+)\s+contributions?", re.IGNORECASE)


def fetch_html(username: str) -> str:
    url = URL_TEMPLATE.format(username=username)
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    cells = soup.select("td.ContributionCalendar-day")

    # tooltips carry the actual count and are linked to a cell via
    # the tooltip's `for` attribute matching the cell's `id`
    tooltip_text_by_id = {}
    for tooltip in soup.select("tool-tip"):
        target_id = tooltip.get("for")
        if target_id:
            tooltip_text_by_id[target_id] = tooltip.get_text(strip=True)

    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue

        level_attr = cell.get("data-level")
        try:
            level = int(level_attr) if level_attr is not None else 0
        except ValueError:
            level = 0

        count = 0
        cell_id = cell.get("id")
        tooltip = tooltip_text_by_id.get(cell_id, "")
        match = COUNT_PATTERN.match(tooltip)
        if match:
            count = 0 if match.group(1).lower() == "no" else int(match.group(1))

        days.append({"date": date_str, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    current_streak = 0
    longest_streak = 0
    running = 0
    best_day = None
    best_count = -1
    monthly_totals = defaultdict(int)
    total = 0

    for day in days:
        count = day["count"] or 0
        total += count
        month_key = day["date"][:7]  # YYYY-MM
        monthly_totals[month_key] += count

        if count > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

        if count > best_count:
            best_count = count
            best_day = day["date"]

    # current streak = trailing run of active days, counting back from today
    for day in reversed(days):
        if (day["count"] or 0) > 0:
            current_streak += 1
        else:
            break

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "best_day_count": best_count if best_count >= 0 else 0,
        "monthly_totals": dict(monthly_totals),
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/fetch_contributions.py YOUR_GITHUB_USERNAME")
        sys.exit(1)

    username = sys.argv[1]
    print(f"Fetching contributions for {username}...")
    html = fetch_html(username)

    print("Parsing days...")
    days = parse_days(html)

    if not days:
        print("Warning: no contribution cells found. GitHub may have changed "
              "its markup -- check the HTML manually.")

    print("Computing stats...")
    stats = compute_stats(days)

    output = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    out_path = Path("data/contributions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(f"Done -> {out_path}")
    print(f"  Total (last year): {stats['total_last_year']}")
    print(f"  Current streak: {stats['current_streak']}")
    print(f"  Longest streak: {stats['longest_streak']}")


if __name__ == "__main__":
    main()