#!/usr/bin/env python3
"""Generate profile cards from public data. Does not invent numbers.

Zenn likes: https://zenn.dev/api/users/aotolog total_liked_count
Qiita contributions: https://qiita.com/aoto0330 HTML "contribution"
Speaker Deck views: https://speakerdeck.com/aoto title="N views" (paginated)
GitHub stats: https://github.com/users/AoTo0330/contributions per year

Zenn article/user APIs have no public view count. Qiita page_views_count is null
without the owner's token — do not add either as a card metric.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "images" / "badges"

ZENN_USER = "aotolog"
QIITA_USER = "aoto0330"
SPEAKERDECK_USER = "aoto"
GITHUB_USER = "AoTo0330"
ZENN_API = f"https://zenn.dev/api/users/{ZENN_USER}"
QIITA_PROFILE = f"https://qiita.com/{QIITA_USER}"
QIITA_ITEMS = f"https://qiita.com/api/v2/users/{QIITA_USER}/items?per_page=1"
SPEAKERDECK_PROFILE = f"https://speakerdeck.com/{SPEAKERDECK_USER}"
GITHUB_CONTRIB = f"https://github.com/users/{GITHUB_USER}/contributions"
USER_AGENT = "AoTo0330-profile-readme-cards/1.0 (https://github.com/AoTo0330/AoTo0330)"

BG = "#0b1026"
NEON = "#3CB9FC"
MUTED = "#8B949E"
FONT = "Verdana, DejaVu Sans, sans-serif"


def fetch(url: str) -> str:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def zenn_likes() -> int:
    data = json.loads(fetch(ZENN_API))
    count = data.get("user", {}).get("total_liked_count")
    if not isinstance(count, int):
        raise RuntimeError(f"Zenn total_liked_count missing from {ZENN_API}")
    return count


def qiita_contributions() -> int:
    html = fetch(QIITA_PROFILE)
    match = re.search(r'"contribution"\s*:\s*(\d+)', html)
    if not match:
        match = re.search(
            r">(\d{1,6})</span>\s*<span[^>]*>\s*Contributions\s*</span>",
            html,
            re.I,
        )
    if not match:
        raise RuntimeError(f"Qiita contribution count missing from {QIITA_PROFILE}")
    return int(match.group(1))


def qiita_views_public() -> int | None:
    """Qiita page_views_count is only returned for the item owner. Public JSON is null."""
    items = json.loads(fetch(QIITA_ITEMS))
    if not items or "page_views_count" not in items[0]:
        return None
    value = items[0]["page_views_count"]
    return value if isinstance(value, int) else None


class _NextLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.next_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        mapping = {k: v for k, v in attrs}
        if mapping.get("rel") == "next" and mapping.get("href"):
            self.next_href = mapping["href"]


def speakerdeck_views() -> tuple[int, int]:
    """Sum public per-deck view counts from title="N views" on paginated profile HTML."""
    url: str | None = SPEAKERDECK_PROFILE
    seen: set[str] = set()
    views: list[int] = []
    while url and url not in seen:
        seen.add(url)
        html = fetch(url)
        found = [int(raw.replace(",", "")) for raw in re.findall(r'title="([\d,]+)\s+views"', html, re.I)]
        if not found:
            raise RuntimeError(f"Speaker Deck view counts missing from {url}")
        views.extend(found)
        parser = _NextLinkParser()
        parser.feed(html)
        if parser.next_href:
            url = urljoin(url, parser.next_href)
        else:
            url = None
        if len(seen) > 20:
            raise RuntimeError("Speaker Deck pagination exceeded 20 pages")
    if not views:
        raise RuntimeError(f"Speaker Deck view counts missing from {SPEAKERDECK_PROFILE}")
    return sum(views), len(views)


def _parse_tip(text: str) -> int:
    compact = re.sub(r"\s+", " ", text).strip()
    if compact.lower().startswith("no contribution"):
        return 0
    match = re.match(r"([\d,]+)\s+contribution", compact, re.I)
    if not match:
        raise RuntimeError(f"GitHub contribution tooltip unreadable: {compact[:80]}")
    return int(match.group(1).replace(",", ""))


def github_year_days(year: int) -> list[tuple[date, int]]:
    html = fetch(f"{GITHUB_CONTRIB}?from={year}-01-01&to={year}-12-31")
    id_date: dict[str, str] = {}
    for match in re.finditer(r"<td\b([^>]*)>", html):
        attrs = match.group(1)
        day_id = re.search(r'\bid="([^"]+)"', attrs)
        day_date = re.search(r'\bdata-date="([^"]+)"', attrs)
        if day_id and day_date and "contribution-day" in day_id.group(1):
            if day_date.group(1).startswith(str(year)):
                id_date[day_id.group(1)] = day_date.group(1)
    id_count: dict[str, int] = {}
    for match in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>(.*?)</tool-tip>', html, re.S):
        if match.group(1) in id_date:
            id_count[match.group(1)] = _parse_tip(match.group(2))
    if len(id_date) < 365:
        raise RuntimeError(f"GitHub contribution calendar incomplete for {year}: {len(id_date)} days")
    missing = [day_id for day_id in id_date if day_id not in id_count]
    if missing:
        raise RuntimeError(f"GitHub contribution tooltips missing for {year}: {len(missing)}")
    return [(date.fromisoformat(id_date[day_id]), id_count[day_id]) for day_id in id_date]


def github_contrib_stats(today: date) -> dict[str, object]:
    days: list[tuple[date, int]] = []
    for year in range(2020, today.year + 1):
        days.extend(github_year_days(year))
    days.sort()
    days = [(day, count) for day, count in days if day <= today]
    if not days:
        raise RuntimeError("GitHub contribution calendar empty")
    first = next(day for day, count in days if count > 0)
    total = sum(count for _, count in days)
    year_total = sum(count for day, count in days if day.year == today.year)

    longest = 0
    longest_start = first
    longest_end = first
    current = 0
    current_start: date | None = None
    for day, count in days:
        if count > 0:
            if current_start is None:
                current_start = day
                current = 1
            else:
                current += 1
            if current > longest:
                longest = current
                longest_start = current_start
                longest_end = day
        else:
            current = 0
            current_start = None
    if longest <= 0:
        raise RuntimeError("GitHub longest streak missing from public calendar")
    return {
        "total": total,
        "first": first,
        "year": today.year,
        "year_total": year_total,
        "longest": longest,
        "longest_start": longest_start,
        "longest_end": longest_end,
        "source": GITHUB_CONTRIB,
    }


def card_svg(*, label: str, value: int, aria: str, glyph: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="230" height="68" role="img" aria-label="{aria}">
  <title>{aria}</title>
  <rect x="1" y="1" width="228" height="66" rx="8" fill="{BG}" stroke="{NEON}" stroke-width="1"/>
  {glyph}
  <text x="58" y="28" fill="{MUTED}" font-size="11" font-family="{FONT}">{label}</text>
  <text x="58" y="54" fill="{NEON}" font-size="24" font-weight="700" font-family="{FONT}">{value}</text>
</svg>
"""


def _fmt_day(day: date) -> str:
    return f"{day.strftime('%b')} {day.day}"


def github_stats_svg(stats: dict[str, object]) -> str:
    """Restore the demolab streak-stats layout (commit ef91019), with this-year
    contributions in the center ring instead of Current Streak.
    """
    total = int(stats["total"])
    year = int(stats["year"])
    year_total = int(stats["year_total"])
    longest = int(stats["longest"])
    first = stats["first"]
    longest_start = stats["longest_start"]
    longest_end = stats["longest_end"]
    assert isinstance(first, date)
    assert isinstance(longest_start, date)
    assert isinstance(longest_end, date)
    aria = (
        f"GitHub contributions: {total:,} total, {year_total:,} in {year}, "
        f"longest streak {longest} days"
    )
    total_sub = f"{_fmt_day(first)}, {first.year} - Present"
    longest_sub = f"{_fmt_day(longest_start)} - {_fmt_day(longest_end)}"
    font = '"Segoe UI", Ubuntu, sans-serif'
    fire = (
        "M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 "
        "-1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 "
        "-8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 "
        "C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 "
        "15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 "
        "10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="isolation: isolate" viewBox="0 0 495 195" width="495px" height="195px" direction="ltr" role="img" aria-label="{aria}">
  <title>{aria}</title>
  <defs>
    <clipPath id="outer_rectangle"><rect width="495" height="195" rx="4.5"/></clipPath>
    <mask id="mask_out_ring_behind_fire">
      <rect width="495" height="195" fill="white"/>
      <ellipse cx="247.5" cy="32" rx="13" ry="18" fill="black"/>
    </mask>
  </defs>
  <g clip-path="url(#outer_rectangle)">
    <rect stroke="#000000" stroke-opacity="0" fill="{BG}" rx="4.5" x="0.5" y="0.5" width="494" height="194"/>
    <line x1="165" y1="28" x2="165" y2="170" stroke="#16324a" stroke-width="1"/>
    <line x1="330" y1="28" x2="330" y2="170" stroke="#16324a" stroke-width="1"/>
    <text x="82.5" y="80" text-anchor="middle" fill="{NEON}" font-family="{font}" font-weight="700" font-size="28">{total:,}</text>
    <text x="82.5" y="116" text-anchor="middle" fill="{MUTED}" font-family="{font}" font-weight="400" font-size="14">Total Contributions</text>
    <text x="82.5" y="146" text-anchor="middle" fill="{MUTED}" font-family="{font}" font-weight="400" font-size="12">{total_sub}</text>
    <g mask="url(#mask_out_ring_behind_fire)">
      <circle cx="247.5" cy="71" r="40" fill="none" stroke="{NEON}" stroke-width="5"/>
    </g>
    <g transform="translate(247.5, 19.5)">
      <path d="{fire}" fill="{NEON}"/>
    </g>
    <text x="247.5" y="80" text-anchor="middle" fill="{NEON}" font-family="{font}" font-weight="700" font-size="28">{year_total:,}</text>
    <text x="247.5" y="140" text-anchor="middle" fill="{NEON}" font-family="{font}" font-weight="700" font-size="14">{year} Contributions</text>
    <text x="412.5" y="80" text-anchor="middle" fill="{NEON}" font-family="{font}" font-weight="700" font-size="28">{longest}</text>
    <text x="412.5" y="116" text-anchor="middle" fill="{MUTED}" font-family="{font}" font-weight="400" font-size="14">Longest Streak</text>
    <text x="412.5" y="146" text-anchor="middle" fill="{MUTED}" font-family="{font}" font-weight="400" font-size="12">{longest_sub}</text>
  </g>
</svg>
"""


ZENN_GLYPH = """  <g transform="translate(18,22) scale(1.05)">
    <path fill="#8B949E" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>
  </g>"""

QIITA_GLYPH = """  <g transform="translate(18,20) scale(1.15)">
    <path fill="#8B949E" d="M12 0C5.3726 0 0 5.3726 0 12s5.3726 12 12 12c3.3984 0 6.4665-1.413 8.6498-3.6832-.383-.0574-.7746-.2062-1.1466-.4542-.7145-.4763-1.3486-.9263-1.6817-1.674-1.2945 1.3807-3.0532 1.835-5.1822 2.0503-4.311.4359-8.0456-1.4893-8.4979-6.2996-.1922-2.045.2628-3.989 1.1804-5.582l-.5342-2.1009c-.0862-.3652.2498-.7126.6057-.6262l1.8456.448c1.0974-.9012 2.4249-1.49 3.8892-1.638 1.2526-.1267 2.467.0834 3.571.5624l1.7348-1.0494c.3265-.1974.7399.0257.7711.4164l.1 2.4747v.0002c1.334 1.4084 2.2424 3.3319 2.4478 5.516.116 1.2339-.012 2.1776-.339 3.078-.1531.4215-.1992.7778.0776 1.1305.2674.3408.6915 1.0026 1.1644.8917.7107-.1666 1.4718-.1223 1.9422.1715C23.4925 15.9525 24 14.0358 24 12c0-6.6274-5.3726-12-12-12Z"/>
  </g>"""

SPEAKERDECK_GLYPH = """  <g transform="translate(16,22) scale(1.05)">
    <path fill="#8B949E" d="M10.025 13.875H4.687a4.688 4.688 0 0 1 0-9.375h6.227a1.875 1.875 0 0 1 0 3.75H4.592a.937.937 0 1 0 0 1.875h5.337a4.687 4.687 0 1 1 0 9.375H1.875a1.875 1.875 0 0 1 0-3.75h8.15a.938.938 0 0 0 0-1.875zM13.97 19.5a5.635 5.635 0 0 0 2.396-3.75h3.026a.93.93 0 0 0 .921-.938V9.189a.93.93 0 0 0-.921-.938h-5.497c.438-.498.704-1.155.704-1.875s-.266-1.377-.704-1.875h6.418C22.35 4.5 24 6.179 24 8.25v7.5c0 2.071-1.65 3.75-3.687 3.75H13.97z"/>
  </g>"""


def main() -> int:
    likes = zenn_likes()
    contrib = qiita_contributions()
    qiita_views = qiita_views_public()
    deck_views, deck_count = speakerdeck_views()
    stats = github_contrib_stats(date.today())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zenn_path = OUT_DIR / "zenn-likes.svg"
    qiita_path = OUT_DIR / "qiita-contributions.svg"
    deck_path = OUT_DIR / "speakerdeck-views.svg"
    github_path = OUT_DIR / "github-contrib-stats.svg"
    zenn_path.write_text(
        card_svg(label="ZENN LIKES", value=likes, aria=f"Zenn likes: {likes}", glyph=ZENN_GLYPH)
    )
    qiita_path.write_text(
        card_svg(
            label="QIITA CONTRIBUTIONS",
            value=contrib,
            aria=f"Qiita contributions: {contrib}",
            glyph=QIITA_GLYPH,
        )
    )
    deck_path.write_text(
        card_svg(
            label="SPEAKER DECK VIEWS",
            value=deck_views,
            aria=f"Speaker Deck views: {deck_views}",
            glyph=SPEAKERDECK_GLYPH,
        )
    )
    github_path.write_text(github_stats_svg(stats))
    print(f"Wrote {zenn_path} likes={likes} source={ZENN_API}")
    print("Zenn views: not in public user/article API or article HTML; skipped")
    print(f"Wrote {qiita_path} contributions={contrib} source={QIITA_PROFILE}")
    print(
        f"Qiita views: page_views_count={qiita_views!r} from {QIITA_ITEMS} "
        "(null without owner token); skipped"
    )
    print(
        f"Wrote {deck_path} views={deck_views} decks={deck_count} source={SPEAKERDECK_PROFILE} "
        f"(title='N views' on paginated public profile; no official API)"
    )
    print(
        f"Wrote {github_path} total={stats['total']} year={stats['year_total']} "
        f"longest={stats['longest']} source={GITHUB_CONTRIB} "
        "(public contribution calendar tooltips; Current Streak replaced with this year)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
