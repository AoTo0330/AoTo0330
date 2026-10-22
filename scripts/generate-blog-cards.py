#!/usr/bin/env python3
"""Generate Zenn/Qiita/Speaker Deck cards from public data. Does not invent numbers.

Card *shape* stays the 80c14b6 rounded thin-border layout (8px radius, left accent).
Colours are the 07dff08 neon palette, not aotolog.com theme-vars.
Zenn/Qiita/Speaker Deck glyphs keep hugo-aotolog svg.html paths.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "images" / "badges"

ZENN_USER = "aotolog"
QIITA_USER = "aoto0330"
SPEAKERDECK_USER = "aoto"
ZENN_API = f"https://zenn.dev/api/users/{ZENN_USER}"
QIITA_PROFILE = f"https://qiita.com/{QIITA_USER}"
SPEAKERDECK_PROFILE = f"https://speakerdeck.com/{SPEAKERDECK_USER}"
USER_AGENT = "AoTo0330-profile-readme-cards/1.0 (https://github.com/AoTo0330/AoTo0330)"

NAVY = "#120052"
NAVY_2 = "#8A2BE2"
NEON = "#3CB9FC"
MAGENTA = "#B537F2"
MUTED = "#C4B5FD"


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


def card_svg(*, label: str, value: int, aria: str, glyph: str, gid: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="230" height="68" role="img" aria-label="{aria}">
  <title>{aria}</title>
  <defs>
    <linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{NAVY}"/>
      <stop offset="55%" stop-color="{NAVY_2}"/>
      <stop offset="100%" stop-color="{MAGENTA}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="228" height="66" rx="8" fill="url(#{gid})" stroke="{NEON}" stroke-width="1.5"/>
  <rect x="1" y="1" width="4" height="66" rx="2" fill="{MAGENTA}"/>
  {glyph}
  <text x="58" y="28" fill="{MUTED}" font-size="11" font-family="Verdana, DejaVu Sans, sans-serif">{label}</text>
  <text x="58" y="54" fill="{NEON}" font-size="24" font-weight="700" font-family="Verdana, DejaVu Sans, sans-serif">{value}</text>
</svg>
"""


ZENN_GLYPH = """  <g transform="translate(18,22) scale(1.05)">
    <path fill="#3CB9FC" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>
  </g>"""

QIITA_GLYPH = """  <g transform="translate(18,20) scale(1.15)">
    <path fill="#3CB9FC" d="M12 0C5.3726 0 0 5.3726 0 12s5.3726 12 12 12c3.3984 0 6.4665-1.413 8.6498-3.6832-.383-.0574-.7746-.2062-1.1466-.4542-.7145-.4763-1.3486-.9263-1.6817-1.674-1.2945 1.3807-3.0532 1.835-5.1822 2.0503-4.311.4359-8.0456-1.4893-8.4979-6.2996-.1922-2.045.2628-3.989 1.1804-5.582l-.5342-2.1009c-.0862-.3652.2498-.7126.6057-.6262l1.8456.448c1.0974-.9012 2.4249-1.49 3.8892-1.638 1.2526-.1267 2.467.0834 3.571.5624l1.7348-1.0494c.3265-.1974.7399.0257.7711.4164l.1 2.4747v.0002c1.334 1.4084 2.2424 3.3319 2.4478 5.516.116 1.2339-.012 2.1776-.339 3.078-.1531.4215-.1992.7778.0776 1.1305.2674.3408.6915 1.0026 1.1644.8917.7107-.1666 1.4718-.1223 1.9422.1715C23.4925 15.9525 24 14.0358 24 12c0-6.6274-5.3726-12-12-12Z"/>
  </g>"""

SPEAKERDECK_GLYPH = """  <g transform="translate(16,22) scale(1.05)">
    <path fill="#3CB9FC" d="M10.025 13.875H4.687a4.688 4.688 0 0 1 0-9.375h6.227a1.875 1.875 0 0 1 0 3.75H4.592a.937.937 0 1 0 0 1.875h5.337a4.687 4.687 0 1 1 0 9.375H1.875a1.875 1.875 0 0 1 0-3.75h8.15a.938.938 0 0 0 0-1.875zM13.97 19.5a5.635 5.635 0 0 0 2.396-3.75h3.026a.93.93 0 0 0 .921-.938V9.189a.93.93 0 0 0-.921-.938h-5.497c.438-.498.704-1.155.704-1.875s-.266-1.377-.704-1.875h6.418C22.35 4.5 24 6.179 24 8.25v7.5c0 2.071-1.65 3.75-3.687 3.75H13.97z"/>
  </g>"""


def main() -> int:
    likes = zenn_likes()
    contrib = qiita_contributions()
    deck_views, deck_count = speakerdeck_views()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zenn_path = OUT_DIR / "zenn-likes.svg"
    qiita_path = OUT_DIR / "qiita-contributions.svg"
    deck_path = OUT_DIR / "speakerdeck-views.svg"
    zenn_path.write_text(
        card_svg(label="ZENN LIKES", value=likes, aria=f"Zenn likes: {likes}", glyph=ZENN_GLYPH, gid="neon-zenn")
    )
    qiita_path.write_text(
        card_svg(
            label="QIITA CONTRIBUTIONS",
            value=contrib,
            aria=f"Qiita contributions: {contrib}",
            glyph=QIITA_GLYPH,
            gid="neon-qiita",
        )
    )
    deck_path.write_text(
        card_svg(
            label="SPEAKER DECK VIEWS",
            value=deck_views,
            aria=f"Speaker Deck views: {deck_views}",
            glyph=SPEAKERDECK_GLYPH,
            gid="neon-speakerdeck",
        )
    )
    print(f"Wrote {zenn_path} likes={likes} source={ZENN_API}")
    print(f"Wrote {qiita_path} contributions={contrib} source={QIITA_PROFILE}")
    print(
        f"Wrote {deck_path} views={deck_views} decks={deck_count} source={SPEAKERDECK_PROFILE} "
        f"(title='N views' on paginated public profile; no official API)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
