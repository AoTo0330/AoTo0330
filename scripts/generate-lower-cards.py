#!/usr/bin/env python3
"""Generate award cards, OGP-style post/talk cards, contact button, and tech logos.

Awards are compact framed PNG cards (navy fill, double cyan frame) so GitHub
does not strip embedded images. AWS lockup is the official Wikimedia SVG
(wordmark #252F3E, smile #FF9900). Google Cloud is the official 2026 gradient PNG.
"""

from __future__ import annotations

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
TECH = ROOT / "public" / "images" / "tech"
README = ROOT / "README.md"

BG = "#0b1026"
PLATE = "#121A2E"
NEON = "#3CB9FC"
MUTED = "#8B949E"
WHITE = "#E6EDF3"
FONT = "Verdana, DejaVu Sans, sans-serif"
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

# 2x PNG; displayed at 150px wide → ~124px tall.
PLAQUE_W, PLAQUE_H = 300, 248
PLAQUE_DISPLAY_W = 150
CARD_W, CARD_H = 260, 140
LOGO_MAX = (188, 68)
NAME_GAP = 8
YEAR_H = 22
NAME_TEXT = (230, 237, 247, 255)
YEAR_TEXT = (60, 185, 252, 255)
NAVY = (11, 16, 38, 255)
CB_YEARS = "2024\uFF5E現在"
AWS_LOCKUP = TECH / "aws-lockup.svg"
GCP_2026 = TECH / "google-cloud-2026.png"


def fit_contain(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return image


def paste_centered(base: Image.Image, overlay: Image.Image, cx: int, y: int) -> None:
    x = int(cx - overlay.width / 2)
    base.alpha_composite(overlay, (x, y))


def raster_aws(wordmark: str, smile: str = "#FF9900", width: int = 640) -> Image.Image:
    svg = AWS_LOCKUP.read_text().replace("#252F3E", wordmark).replace("#FF9900", smile)
    png = cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        output_width=width,
        background_color="transparent",
    )
    return Image.open(BytesIO(png)).convert("RGBA")


def square_icon(image: Image.Image, size: int = 96) -> Image.Image:
    fitted = fit_contain(image, size, size)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(
        fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2)
    )
    return canvas


def cb_logo_mono(path: Path) -> Image.Image:
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
    return fit_contain(image, *LOGO_MAX)


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill=None,
    outline=None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_frame_shell(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((0, 0, PLAQUE_W, PLAQUE_H), fill=NAVY)
    rounded_rect(
        draw,
        (6, 6, PLAQUE_W - 7, PLAQUE_H - 7),
        16,
        fill=None,
        outline=(60, 185, 252, 255),
        width=3,
    )
    rounded_rect(
        draw,
        (16, 16, PLAQUE_W - 17, PLAQUE_H - 17),
        10,
        fill=None,
        outline=(60, 185, 252, 255),
        width=2,
    )


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
) -> int:
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((PLAQUE_W - tw) / 2 - bbox[0], y - bbox[1]),
        text,
        fill=fill,
        font=font,
    )
    return th


def write_plaque_png(
    path: Path,
    logo: Image.Image,
    name_lines: list[str] | None,
    years: str,
    logo_max: tuple[int, int] = LOGO_MAX,
) -> None:
    img = Image.new("RGBA", (PLAQUE_W, PLAQUE_H), NAVY)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_frame_shell(draw)
    name_font = ImageFont.truetype(BOLD_FONT, 18)
    year_latin = ImageFont.truetype(BOLD_FONT, 16)
    year_cjk = ImageFont.truetype(CJK_FONT, 16)
    logo = fit_contain(logo, *logo_max)
    names = name_lines or []
    name_h = 20 * len(names)
    gap_logo = 10 if names else 12
    gap_name = 8 if names else 0
    total = logo.height + gap_logo + gap_name + name_h + YEAR_H
    inner_y, inner_h = 26, 196
    y = int(inner_y + (inner_h - total) / 2)
    paste_centered(img, logo, PLAQUE_W // 2, y)
    y += logo.height + gap_logo
    for line in names:
        draw_centered_text(draw, line, y, name_font, NAME_TEXT)
        y += 20
    y += gap_name
    year_font = year_cjk if any(ord(ch) > 127 for ch in years) else year_latin
    draw_centered_text(draw, years, y, year_font, YEAR_TEXT)
    img.save(path, "PNG", optimize=True)


def write_tech_logos() -> None:
    aws_light = square_icon(raster_aws("#252F3E"), 96)
    aws_dark = square_icon(raster_aws("#FFFFFF"), 96)
    aws_light.save(TECH / "aws.png", "PNG", optimize=True)
    aws_dark.save(TECH / "aws-dark.png", "PNG", optimize=True)
    gcp = square_icon(Image.open(GCP_2026), 96)
    gcp.save(TECH / "google-cloud.png", "PNG", optimize=True)
    dog = (TECH / "datadog.svg").read_text()
    if 'fill="#FFFFFF"' in dog:
        (TECH / "datadog-dark.svg").write_text(dog)
        (TECH / "datadog.svg").write_text(dog.replace('fill="#FFFFFF"', 'fill="#0b1026"'))
    elif 'fill="#0b1026"' in dog:
        (TECH / "datadog-dark.svg").write_text(dog.replace('fill="#0b1026"', 'fill="#FFFFFF"'))


def write_cb_card() -> None:
    write_plaque_png(
        AWARDS / "aws-community-builder.png",
        cb_logo_mono(AWARDS / "aws-community-builders-badge.png"),
        ["Community Builder", "Cloud Operations"],
        CB_YEARS,
    )


def write_aws_allcerts() -> None:
    write_plaque_png(
        AWARDS / "aws-allcerts.png",
        raster_aws("#FFFFFF"),
        ["All Certifications", "Engineer"],
        "2022–2025",
    )


def write_jr_champion() -> None:
    write_plaque_png(
        AWARDS / "aws-jr-champion-2023.png",
        raster_aws("#FFFFFF"),
        ["Japan AWS", "Jr. Champion"],
        "2023",
    )


def write_pte() -> None:
    art = Image.open(AWARDS / "pte-20251104-rgb-nega-1.png")
    write_plaque_png(AWARDS / "gcp-pte.png", art, None, "2023–2026")


def write_all_cert_holders() -> None:
    write_plaque_png(
        AWARDS / "gcp-all-cert-holders-2025.png",
        Image.open(GCP_2026),
        ["All Certification", "Holders"],
        "2025",
    )


def write_jaguer() -> None:
    # Official Jagu'e'r Award mark from Kento's Drive slide『Jagu'e'r Award 2025』p.14
    write_plaque_png(
        AWARDS / "jaguer.png",
        Image.open(AWARDS / "jaguer-award-logo.png"),
        ["Jagu'e'r Award"],
        "2023–2025",
        logo_max=(108, 108),
    )


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
    for folder in (AWARDS, POSTS, TALKS, CONTACT, TECH):
        folder.mkdir(parents=True, exist_ok=True)

    for name in (
        "pte-20251104-rgb-nega-1.png",
        "pte-20251104-rgb-nega-2.png",
        "jaguer-award-logo.png",
    ):
        src = PACK / name
        if src.exists():
            (AWARDS / name).write_bytes(src.read_bytes())

    write_tech_logos()
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
    print("wrote award cards, tech logos, and post/talk cards")


if __name__ == "__main__":
    main()
