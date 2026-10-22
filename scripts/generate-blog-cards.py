#!/usr/bin/env python3
"""Generate Zenn/Qiita cards from public APIs. Numbers are not invented.

Card look follows aotolog.com PaperMod theme-vars: white/navy, 8px radius,
thin border, #3CB9FC accent only. Glyphs match hugo-aotolog layouts/partials/svg.html.
"""

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


def card_svg(*, label: str, value: int, aria: str, glyph: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="230" height="68" role="img" aria-label="{aria}">
  <title>{aria}</title>
  <style>
    .card {{ fill: #ffffff; stroke: #d3e2ee; }}
    .accent {{ fill: #3cb9fc; }}
    .label {{ fill: #566573; }}
    .value {{ fill: #00203f; }}
    .glyph {{ fill: #00203f; }}
    @media (prefers-color-scheme: dark) {{
      .card {{ fill: #1c2d50; stroke: #3c5073; }}
      .label {{ fill: #adb9ca; }}
      .value {{ fill: #f0f8ff; }}
      .glyph {{ fill: #f0f8ff; }}
    }}
  </style>
  <rect class="card" x="1" y="1" width="228" height="66" rx="8" stroke-width="1"/>
  <rect class="accent" x="1" y="1" width="4" height="66" rx="2"/>
  {glyph}
  <text class="label" x="58" y="28" font-size="11" font-family="Verdana, DejaVu Sans, sans-serif">{label}</text>
  <text class="value" x="58" y="54" font-size="24" font-weight="700" font-family="Verdana, DejaVu Sans, sans-serif">{value}</text>
</svg>
"""


ZENN_GLYPH = """  <g transform="translate(18,22) scale(1.05)">
    <path class="glyph" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>
  </g>"""

QIITA_GLYPH = """  <g transform="translate(18,20) scale(1.15)">
    <path class="glyph" d="M12 0C5.3726 0 0 5.3726 0 12s5.3726 12 12 12c3.3984 0 6.4665-1.413 8.6498-3.6832-.383-.0574-.7746-.2062-1.1466-.4542-.7145-.4763-1.3486-.9263-1.6817-1.674-1.2945 1.3807-3.0532 1.835-5.1822 2.0503-4.311.4359-8.0456-1.4893-8.4979-6.2996-.1922-2.045.2628-3.989 1.1804-5.582l-.5342-2.1009c-.0862-.3652.2498-.7126.6057-.6262l1.8456.448c1.0974-.9012 2.4249-1.49 3.8892-1.638 1.2526-.1267 2.467.0834 3.571.5624l1.7348-1.0494c.3265-.1974.7399.0257.7711.4164l.1 2.4747v.0002c1.334 1.4084 2.2424 3.3319 2.4478 5.516.116 1.2339-.012 2.1776-.339 3.078-.1531.4215-.1992.7778.0776 1.1305.2674.3408.6915 1.0026 1.1644.8917.7107-.1666 1.4718-.1223 1.9422.1715C23.4925 15.9525 24 14.0358 24 12c0-6.6274-5.3726-12-12-12Z"/>
  </g>"""


def main() -> int:
    likes = zenn_likes()
    contrib = qiita_contributions()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zenn_path = OUT_DIR / "zenn-likes.svg"
    qiita_path = OUT_DIR / "qiita-contributions.svg"
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
    print(f"Wrote {zenn_path} likes={likes} source={ZENN_API}")
    print(f"Wrote {qiita_path} contributions={contrib} source={QIITA_PROFILE}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
