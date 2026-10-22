#!/usr/bin/env python3
"""Generate award plaques, OGP-style post/talk cards, and contact button.

Awards are rectangular 表彰盾 (navy frame, acrylic face, metal name plate),
not heraldic heater shields. PTE uses official white-text artwork from
pte-20251104-rgb-nega-1.png (wide) / pte-20251104-rgb-nega-2.png (tall).
"""

from __future__ import annotations

import base64
import html
import re
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PACK = Path("/cursor/stores/self/internal/award-assets")
AWARDS = ROOT / "public" / "images" / "awards"
POSTS = ROOT / "public" / "images" / "posts"
TALKS = ROOT / "public" / "images" / "talks"
CONTACT = ROOT / "public" / "images" / "contact"
README = ROOT / "README.md"

BG = "#0b1026"
PLATE = "#121A2E"
NEON = "#3CB9FC"
MUTED = "#8B949E"
WHITE = "#E6EDF3"
FONT = "Verdana, DejaVu Sans, sans-serif"
STEEL_HI = "#F2F6FA"
STEEL_MID = "#A8B6C4"
STEEL_LO = "#5A6A7A"
STEEL_EDGE = "#2E3A48"
FRAME = "#141C2E"
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CJK_FONT = next(
    path
    for path in (
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        BOLD_FONT,
    )
    if Path(path).exists()
)

PW, PH = 220, 340
FONT_PAD = 1.10
CARD_W, CARD_H = 260, 140
LOGO_MAX_W, LOGO_MAX_H = 148, 56
LOGO_Y = 42
NAME_Y = 128
YEAR_Y = 250


def b64_png_fitted(path: Path, max_w: int, max_h: int) -> tuple[str, int, int]:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), image.width, image.height


def encode_png(image: Image.Image, max_w: int, max_h: int) -> tuple[str, int, int]:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), image.width, image.height


def centered_png(b64: str, width: int, height: int, y: float = LOGO_Y) -> str:
    x = 110 - width / 2
    return (
        f'<image href="data:image/png;base64,{b64}" x="{x:.1f}" y="{y:.1f}" '
        f'width="{width}" height="{height}"/>'
    )


def cb_logo_mono(path: Path) -> tuple[str, int, int]:
    """Drop the navy/black square; keep the wordmark as a single-color white glyph."""
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    image = image.crop((0, int(height * 0.52), int(width * 0.92), height))
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
            if alpha < 24 or luma < 70:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            pixels[x, y] = (230, 237, 243, 255)
    return encode_png(image, LOGO_MAX_W, LOGO_MAX_H)


def text_width(text: str, size: float, bold: bool = True) -> float:
    path = BOLD_FONT if bold else REG_FONT
    font = ImageFont.truetype(path, size)
    return float(font.getlength(text)) * FONT_PAD


def fit_size(text: str, max_width: float, start: float, bold: bool = True) -> float:
    size = float(start)
    while size > 6.5 and text_width(text, size, bold) > max_width:
        size -= 0.5
    return size


def svg_text(
    x: float,
    y: float,
    text: str,
    fill: str,
    size: float,
    bold: bool = True,
) -> str:
    weight = "700" if bold else "400"
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" fill="{fill}" '
        f'font-size="{size:.1f}" font-weight="{weight}" font-family="{FONT}">'
        f"{html.escape(text)}</text>"
    )


def plaque_defs(gid: str) -> str:
    return (
        f"<defs>"
        f'<linearGradient id="frame-{gid}" x1="14" y1="10" x2="206" y2="310" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#1B2740"/>'
        f'<stop offset="0.55" stop-color="{FRAME}"/>'
        f'<stop offset="1" stop-color="#0E1422"/>'
        f"</linearGradient>"
        f'<linearGradient id="glass-{gid}" x1="24" y1="20" x2="196" y2="300" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#18233C"/>'
        f'<stop offset="0.45" stop-color="{BG}"/>'
        f'<stop offset="1" stop-color="#080C16"/>'
        f"</linearGradient>"
        f'<linearGradient id="metal-{gid}" x1="40" y1="0" x2="180" y2="40" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{STEEL_HI}"/>'
        f'<stop offset="0.45" stop-color="{STEEL_MID}"/>'
        f'<stop offset="1" stop-color="{STEEL_LO}"/>'
        f"</linearGradient>"
        f'<linearGradient id="base-{gid}" x1="70" y1="312" x2="150" y2="334" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{STEEL_MID}"/>'
        f'<stop offset="1" stop-color="{STEEL_EDGE}"/>'
        f"</linearGradient>"
        f"</defs>"
    )


def stud(cx: float, cy: float) -> str:
    return (
        f'<rect x="{cx - 3.2:.1f}" y="{cy - 3.2:.1f}" width="6.4" height="6.4" rx="0.8" '
        f'fill="{STEEL_MID}" stroke="{STEEL_EDGE}" stroke-width="0.6"/>'
        f'<rect x="{cx - 1.3:.1f}" y="{cy - 1.3:.1f}" width="2.6" height="2.6" '
        f'fill="{STEEL_HI}"/>'
    )


def plaque_shell(gid: str, inner: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" '
        f'viewBox="0 0 {PW} {PH}" role="img">'
        f"<title>{html.escape(title)}</title>"
        f"{plaque_defs(gid)}"
        f'<polygon points="62,318 158,318 170,336 50,336" fill="url(#base-{gid})" '
        f'stroke="{STEEL_EDGE}" stroke-width="0.8"/>'
        f'<rect x="14" y="10" width="192" height="304" rx="4" fill="url(#frame-{gid})" '
        f'stroke="{STEEL_MID}" stroke-width="2"/>'
        f'<rect x="20" y="16" width="180" height="292" rx="2" fill="none" '
        f'stroke="{STEEL_HI}" stroke-width="1.1" opacity="0.85"/>'
        f'<rect x="24" y="20" width="172" height="284" fill="url(#glass-{gid})"/>'
        f'<rect x="24" y="20" width="172" height="40" fill="#FFFFFF" opacity="0.05"/>'
        f"{stud(28, 24)}{stud(192, 24)}{stud(28, 300)}{stud(192, 300)}"
        f"{inner}"
        f"</svg>\n"
    )


def aws_smile(x: float, y: float, scale: float = 1.0) -> str:
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        '<path fill="#3CB9FC" d="M21.698 16.207c-2.626 1.94-6.442 2.969-9.722 2.969'
        "-4.598 0-8.74-1.7-11.87-4.526-.247-.223-.024-.527.272-.351 3.384 1.963 "
        "7.559 3.153 11.877 3.153 2.914 0 6.114-.607 9.06-1.852.439-.2.814.287.383.607z"
        'M22.792 14.961c-.336-.43-2.22-.207-3.074-.103-.255.032-.295-.192-.063-.36 '
        "1.5-1.053 3.967-.75 4.254-.399.287.36-.08 2.826-1.485 4.007-.215.184-.423.088"
        '-.327-.151.32-.79 1.03-2.57.695-2.994z"/></g>'
    )


def gcp_mark(x: float, y: float, size: float = 36, gid: str = "gcg") -> str:
    s = size / 24
    return (
        f"<defs>"
        f'<linearGradient id="{gid}" x1="12" y1="2" x2="8" y2="22" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#EA4335"/>'
        f'<stop offset="0.35" stop-color="#FBBC04"/>'
        f'<stop offset="0.7" stop-color="#34A853"/>'
        f'<stop offset="1" stop-color="#4285F4"/>'
        f"</linearGradient>"
        f"</defs>"
        f'<g transform="translate({x},{y}) scale({s})">'
        f'<path fill="url(#{gid})" d="M19 14a5 5 0 0 0-1.1-9.9A7 7 0 0 0 6.1 8.2 '
        '4.5 4.5 0 0 0 6 17h12.5A4.5 4.5 0 0 0 19 14z"/>'
        "</g>"
    )


def nameplate(lines: list[str], y: float = NAME_Y) -> str:
    height = 22 + 16 * len(lines)
    block = (
        f'<rect x="40" y="{y:.1f}" width="140" height="{height:.1f}" rx="2" '
        f'fill="{STEEL_MID}" stroke="{STEEL_EDGE}" stroke-width="0.7"/>'
        f'<rect x="42" y="{y + 1.2:.1f}" width="136" height="{height - 2.4:.1f}" rx="1.5" '
        f'fill="#D7DEE6"/>'
    )
    parts = [block]
    start_y = y + (28 if len(lines) == 1 else 22)
    for i, line in enumerate(lines):
        size = fit_size(line, 128, 12)
        parts.append(svg_text(110, start_y + i * 16, line, STEEL_EDGE, size))
    return "".join(parts)


def years_plate(years: str, y: float = YEAR_Y) -> str:
    size = fit_size(years, 148, 11)
    return (
        f'<rect x="44" y="{y:.1f}" width="132" height="26" rx="2" fill="{PLATE}" '
        f'stroke="{NEON}" stroke-width="0.9"/>'
        + svg_text(110, y + 18, years, NEON, size)
    )


def aws_wordmark() -> str:
    return (
        f'<text x="110" y="74" text-anchor="middle" fill="{WHITE}" font-size="18" '
        f'font-weight="700" font-family="{FONT}">aws</text>'
        + aws_smile(82, 60, 1.25)
    )


def write_cb_card() -> None:
    png, width, height = cb_logo_mono(AWARDS / "aws-community-builders-badge.png")
    title = "AWS Community Builder - Cloud Operations, 2024–"
    inner = (
        centered_png(png, width, height)
        + nameplate(["Community Builder", "Cloud Operations"])
        + years_plate("2024–")
    )
    (AWARDS / "aws-community-builder.svg").write_text(plaque_shell("cb", inner, title))


def write_aws_allcerts() -> None:
    title = "All Certifications Engineer, 2022–2025"
    inner = (
        aws_wordmark()
        + nameplate(["All Certifications", "Engineer"])
        + years_plate("2022–2025")
    )
    (AWARDS / "aws-allcerts.svg").write_text(plaque_shell("allcerts", inner, title))


def write_jr_champion() -> None:
    title = "2023 Japan AWS Jr. Champion"
    inner = (
        aws_wordmark()
        + nameplate(["Japan AWS", "Jr. Champion"])
        + years_plate("2023")
    )
    (AWARDS / "aws-jr-champion-2023.svg").write_text(plaque_shell("jr", inner, title))


def write_pte() -> None:
    title = "Partner Top Engineer, 2023–2026"
    png, width, height = b64_png_fitted(
        AWARDS / "pte-20251104-rgb-nega-1.png", LOGO_MAX_W, LOGO_MAX_H
    )
    inner = (
        centered_png(png, width, height)
        + nameplate(["Partner Top", "Engineer"])
        + years_plate("2023–2026")
    )
    (AWARDS / "gcp-pte.svg").write_text(plaque_shell("pte", inner, title))


def write_all_cert_holders() -> None:
    title = "Google Cloud Partner All Certification Holders 2025"
    inner = (
        gcp_mark(83, LOGO_Y + 2, 52, "gcg-holders")
        + nameplate(["All Certification", "Holders"])
        + years_plate("2025")
    )
    (AWARDS / "gcp-all-cert-holders-2025.svg").write_text(
        plaque_shell("holders", inner, title)
    )


def write_jaguer() -> None:
    png, width, height = b64_png_fitted(
        AWARDS / "jaguer-circle.png", LOGO_MAX_H, LOGO_MAX_H
    )
    title = "Jagu'e'r Award, 2023–2025"
    inner = (
        centered_png(png, width, height)
        + nameplate(["Jagu'e'r Award"])
        + years_plate("2023–2025")
    )
    (AWARDS / "jaguer.svg").write_text(plaque_shell("jaguer", inner, title))


def chrome_card(title: str, inner: str, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f"<title>{html.escape(title)}</title>"
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="8" '
        f'fill="{BG}" stroke="{NEON}" stroke-width="1"/>'
        f"{inner}</svg>\n"
    )


def zenn_glyph() -> str:
    return (
        '<g transform="translate(14,16) scale(1.1)">'
        f'<path fill="{NEON}" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>'
        "</g>"
    )


def qiita_glyph() -> str:
    return (
        '<g transform="translate(14,14) scale(1.15)">'
        f'<path fill="{NEON}" d="M12 0C5.3726 0 0 5.3726 0 12s5.3726 12 12 12c3.3984 0 6.4665-1.413 8.6498-3.6832-.383-.0574-.7746-.2062-1.1466-.4542-.7145-.4763-1.3486-.9263-1.6817-1.674-1.2945 1.3807-3.0532 1.835-5.1822 2.0503-4.311.4359-8.0456-1.4893-8.4979-6.2996-.1922-2.045.2628-3.989 1.1804-5.582l-.5342-2.1009c-.0862-.3652.2498-.7126.6057-.6262l1.8456.448c1.0974-.9012 2.4249-1.49 3.8892-1.638 1.2526-.1267 2.467.0834 3.571.5624l1.7348-1.0494c.3265-.1974.7399.0257.7711.4164l.1 2.4747v.0002c1.334 1.4084 2.2424 3.3319 2.4478 5.516.116 1.2339-.012 2.1776-.339 3.078-.1531.4215-.1992.7778.0776 1.1305.2674.3408.6915 1.0026 1.1644.8917.7107-.1666 1.4718-.1223 1.9422.1715C23.4925 15.9525 24 14.0358 24 12c0-6.6274-5.3726-12-12-12Z"/>'
        "</g>"
    )


def aotolog_glyph() -> str:
    return (
        f'<g transform="translate(16,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="2" y="1" width="20" height="26" rx="3"/>'
        '<path d="M7 8h10M7 13h10M7 18h6"/>'
        "</g>"
    )


def write_post_icon(filename: str, label: str, glyph: str) -> None:
    (POSTS / filename).write_text(chrome_card(label, glyph, 56, 56))


def write_talk_icon() -> None:
    inner = (
        f'<g transform="translate(12,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="4" y="6" width="28" height="20" rx="2"/>'
        '<path d="M10 26h16"/>'
        '<path d="M18 26v6"/>'
        '<circle cx="18" cy="16" r="4"/>'
        "</g>"
    )
    (TALKS / "mic.svg").write_text(chrome_card("Talk", inner, 56, 56))


def write_generic_ogp(path: Path, site: str, glyph: str) -> None:
    inner = (
        glyph.replace("translate(14,16)", "translate(16,18)")
        .replace("translate(14,14)", "translate(16,16)")
        .replace("translate(16,12)", "translate(16,14)")
        + f'<text x="72" y="36" fill="{MUTED}" font-size="13" font-weight="700" '
        f'font-family="{FONT}">{html.escape(site)}</text>'
        f'<text x="72" y="78" fill="{WHITE}" font-size="14" font-weight="700" '
        f'font-family="{FONT}">Latest post</text>'
    )
    path.write_text(chrome_card(site, inner, CARD_W, CARD_H))


def wrap_title(text: str, font: ImageFont.FreeTypeFont, max_width: float, max_lines: int = 3) -> list[str]:
    remaining = " ".join(text.split())
    lines: list[str] = []
    while remaining and len(lines) < max_lines:
        if font.getlength(remaining) <= max_width:
            lines.append(remaining)
            break
        lo, hi = 1, len(remaining)
        cut = 1
        ellipsis = len(lines) == max_lines - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            chunk = remaining[:mid] + ("…" if ellipsis else "")
            if font.getlength(chunk) <= max_width:
                cut = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if ellipsis:
            lines.append(remaining[:cut].rstrip() + "…")
            remaining = ""
            break
        space = remaining.rfind(" ", 0, cut)
        if space >= max(1, cut // 3):
            cut = space
        lines.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return lines


def render_ogp_png(out: Path, site: str, title: str, icon_svg: Path) -> None:
    scale = 2
    width, height = CARD_W * scale, CARD_H * scale
    img = Image.new("RGBA", (width, height), (11, 16, 38, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [3, 3, width - 4, height - 4],
        radius=18,
        outline=(60, 185, 252, 255),
        width=3,
    )
    icon_png = cairosvg.svg2png(url=str(icon_svg), output_width=72, output_height=72)
    icon = Image.open(BytesIO(icon_png)).convert("RGBA")
    img.alpha_composite(icon, (24, 22))
    site_font = ImageFont.truetype(CJK_FONT, 26)
    title_font = ImageFont.truetype(CJK_FONT, 28)
    draw.text((112, 42), site, fill=(139, 148, 158, 255), font=site_font)
    lines = wrap_title(title, title_font, width - 48, max_lines=3)
    y = 108
    for line in lines:
        draw.text((24, y), line, fill=(230, 237, 243, 255), font=title_font)
        y += 40
    img.save(out, "PNG", optimize=True)


def write_contact() -> None:
    inner = (
        f'<g transform="translate(18,12)" fill="none" stroke="{NEON}" stroke-width="1.6">'
        '<rect x="0" y="2" width="22" height="16" rx="2"/>'
        '<path d="m1 4 10 7 10-7"/>'
        "</g>"
        f'<text x="52" y="28" fill="{NEON}" font-size="14" font-weight="700" '
        f'font-family="{FONT}">aoto@datadoghq.com</text>'
    )
    (CONTACT / "mail.svg").write_text(chrome_card("aoto@datadoghq.com", inner, 280, 44))


POST_SEED = {
    "AOTOLOG-POST-LIST": (
        "AoToLog",
        POSTS / "icon-aotolog.svg",
        POSTS / "card-aotolog.svg",
        [
            (
                "https://speakerdeck.com/aoto/designing-ai-agent-experiences-that-enhance-observability",
                "オブザーバビリティを高める AI エージェント体験を考える",
            ),
            (
                "https://www.datadoghq.com/ja/blog/datadog-live-tokyo-2026-recap-agent-observability/",
                "Looking Back at Datadog Live Tokyo 2026 Fireside Chat「AI エージェントを見守る技術 ― 現場から考える Agent Observability」開催レポート",
            ),
            (
                "https://www.datadoghq.com/ja/blog/datadog-live-tokyo-2025-observability-practices-panel/",
                "Looking Back at Datadog Live Tokyo 2025「現場で活きる！Datadog によるオブザーバビリティ実践のリアル」パネルディスカッション開催レポート",
            ),
        ],
        "aotolog",
        aotolog_glyph,
    ),
    "ZENN-POST-LIST": (
        "Zenn",
        POSTS / "icon-zenn.svg",
        POSTS / "card-zenn.svg",
        [
            (
                "https://zenn.dev/datadog/articles/datadog-cr-tf",
                "大規模 Cloud Run 環境を支える Datadog の Terraform 実装",
            ),
            (
                "https://zenn.dev/datadog/articles/bits-ai-sre-intro",
                "あなたの SRE チームを促進させる、Bits AI SRE 偉いところ",
            ),
            (
                "https://zenn.dev/datadog/articles/datadog-gc-logs-dataflow",
                "Datadog に Google Cloud のログをセキュアに送信する",
            ),
        ],
        "zenn",
        zenn_glyph,
    ),
    "QIITA-POST-LIST": (
        "Qiita",
        POSTS / "icon-qiita.svg",
        POSTS / "card-qiita.svg",
        [
            (
                "https://qiita.com/AoTo0330/items/0ce1505b5a1b2d080ad8",
                "Datadog Japan 有志ブログのご紹介",
            ),
            (
                "https://qiita.com/AoTo0330/items/8eb5beef716a3b1eca49",
                "Google Cloud おすすめ学習方法5選【初学者~中級者向け】",
            ),
            (
                "https://qiita.com/AoTo0330/items/36727475de42eab1fa7e",
                "Cloud Run を GKE の代替として利用する",
            ),
        ],
        "qiita",
        qiita_glyph,
    ),
}

TALKS_SEED = [
    (
        "https://speakerdeck.com/aoto/powering-reliable-agentic-ai-with-datadog-observability",
        "頼れる Agentic AI を支える Datadog のオブザーバビリティ",
    ),
    (
        "https://speakerdeck.com/aoto/building-ai-agents-with-ai-agents-by-google-cloud",
        "AI エージェントで AI エージェントを作る！Google Cloudが実現するフルスタックな AI 開発エコシステム",
    ),
    (
        "https://speakerdeck.com/aoto/beyond-the-field-barriers-instrumentation-injection-and-the-future-of-observability",
        "現場の壁を乗り越えて、「計装注入」が拓く オブザーバビリティ",
    ),
]


def parse_marker_items(readme: str, tag: str) -> list[tuple[str, str]]:
    match = re.search(
        rf"<!-- {re.escape(tag)}:START -->(.*?)<!-- {re.escape(tag)}:END -->",
        readme,
        re.S,
    )
    if not match:
        return []
    items = []
    for href, alt in re.findall(
        r'<a href="([^"]+)"[^>]*>\s*<img [^>]*alt="([^"]*)"',
        match.group(1),
    ):
        items.append((html.unescape(href), html.unescape(alt)))
    return items[:3]


def marker_html(prefix: str, items: list[tuple[str, str]]) -> str:
    parts = []
    for index, (url, title) in enumerate(items, start=1):
        src = f"./public/images/posts/{prefix}-{index}.png"
        parts.append(
            f'<a href="{html.escape(url, quote=True)}">'
            f'<img src="{src}" width="{CARD_W}" alt="{html.escape(title, quote=True)}" /></a>'
        )
    return "\n".join(parts)


def replace_marker(readme: str, tag: str, inner: str) -> str:
    pattern = rf"(<!-- {re.escape(tag)}:START -->)(.*?)(<!-- {re.escape(tag)}:END -->)"
    return re.sub(pattern, rf"\1\n{inner}\n\3", readme, count=1, flags=re.S)


def write_post_and_talk_cards() -> None:
    readme = README.read_text() if README.exists() else ""
    for tag, (site, icon, generic, seed, prefix, glyph) in POST_SEED.items():
        write_generic_ogp(generic, site, glyph())
        items = parse_marker_items(readme, tag) or seed
        if items and items[0][1] in {"", "AoToLog post", "Zenn post", "Qiita post"}:
            by_url = {url: title for url, title in seed}
            items = [(url, by_url.get(url, title or site)) for url, title in items]
        for index, (url, title) in enumerate(items, start=1):
            render_ogp_png(POSTS / f"{prefix}-{index}.png", site, title, icon)
        if README.exists() and f"<!-- {tag}:START -->" in readme:
            readme = replace_marker(readme, tag, marker_html(prefix, items))

    write_generic_ogp(TALKS / "card-talk.svg", "Speaker Deck", (
        f'<g transform="translate(12,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="4" y="6" width="28" height="20" rx="2"/>'
        '<path d="M10 26h16M18 26v6"/>'
        '<circle cx="18" cy="16" r="4"/>'
        "</g>"
    ))
    for index, (url, title) in enumerate(TALKS_SEED, start=1):
        render_ogp_png(TALKS / f"talk-{index}.png", "Speaker Deck", title, TALKS / "mic.svg")

    if README.exists():
        README.write_text(readme)


def main() -> None:
    for folder in (AWARDS, POSTS, TALKS, CONTACT):
        folder.mkdir(parents=True, exist_ok=True)

    for name in (
        "pte-20251104-rgb-nega-1.png",
        "pte-20251104-rgb-nega-2.png",
    ):
        src = PACK / name
        if src.exists():
            (AWARDS / name).write_bytes(src.read_bytes())

    write_cb_card()
    write_aws_allcerts()
    write_jr_champion()
    write_pte()
    write_all_cert_holders()
    write_jaguer()
    write_post_icon("icon-aotolog.svg", "AoToLog", aotolog_glyph())
    write_post_icon("icon-zenn.svg", "Zenn", zenn_glyph())
    write_post_icon("icon-qiita.svg", "Qiita", qiita_glyph())
    write_talk_icon()
    write_contact()
    write_post_and_talk_cards()
    print("wrote plaques and post/talk cards")


if __name__ == "__main__":
    main()
