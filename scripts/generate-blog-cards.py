#!/usr/bin/env python3
"""Generate navy + blue/purple/magenta Zenn/Qiita cards from public APIs. Does not invent numbers."""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public" / "images" / "badges"

ZENN_USER = "aotolog"
QIITA_USER = "aoto0330"
ZENN_API = f"https://zenn.dev/api/users/{ZENN_USER}"
QIITA_PROFILE = f"https://qiita.com/{QIITA_USER}"
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
  <rect x="1" y="1" width="228" height="66" rx="14" fill="url(#{gid})" stroke="{NEON}" stroke-width="1.5"/>
  <rect x="1" y="1" width="8" height="66" rx="4" fill="{MAGENTA}"/>
  {glyph}
  <text x="58" y="28" fill="{MUTED}" font-size="11" font-family="Verdana, DejaVu Sans, sans-serif">{label}</text>
  <text x="58" y="54" fill="{NEON}" font-size="24" font-weight="700" font-family="Verdana, DejaVu Sans, sans-serif">{value}</text>
</svg>
"""


ZENN_GLYPH = """  <g transform="translate(18,20) scale(1.15)">
    <path fill="#3CB9FC" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c-.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>
  </g>"""

QIITA_GLYPH = """  <g transform="translate(20,18)">
    <circle cx="14" cy="16" r="14" fill="none" stroke="#3CB9FC" stroke-width="2"/>
    <text x="14" y="22" text-anchor="middle" fill="#3CB9FC" font-size="16" font-weight="700" font-family="Verdana, DejaVu Sans, sans-serif">Q</text>
  </g>"""


def main() -> int:
    likes = zenn_likes()
    contrib = qiita_contributions()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zenn_path = OUT_DIR / "zenn-likes.svg"
    qiita_path = OUT_DIR / "qiita-contributions.svg"
    zenn_path.write_text(
        card_svg(label="ZENN LIKES", value=likes, aria=f"Zenn likes: {likes}", glyph=ZENN_GLYPH, gid="navy-zenn")
    )
    qiita_path.write_text(
        card_svg(
            label="QIITA CONTRIBUTIONS",
            value=contrib,
            aria=f"Qiita contributions: {contrib}",
            glyph=QIITA_GLYPH,
            gid="navy-qiita",
        )
    )
    print(f"Wrote {zenn_path} likes={likes} source={ZENN_API}")
    print(f"Wrote {qiita_path} contributions={contrib} source={QIITA_PROFILE}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
