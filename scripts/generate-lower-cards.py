#!/usr/bin/env python3
"""Generate award cards, OGP-style post/talk cards, and tech logos.

Awards are compact framed PNG cards (navy fill, double cyan frame) so GitHub
does not strip embedded images. AWS lockup is the official Wikimedia SVG
(wordmark #252F3E, smile #FF9900). Google Cloud is the official 2026 gradient PNG.
Light-mode twins use a near-white fill and navy text; dark files stay as-is.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PACK = Path("/cursor/stores/self/internal/award-assets")
AWARDS = ROOT / "public" / "images" / "awards"
POSTS = ROOT / "public" / "images" / "posts"
TALKS = ROOT / "public" / "images" / "talks"
TECH = ROOT / "public" / "images" / "tech"
README = ROOT / "README.md"

NEON = "#3CB9FC"
FONT = "Verdana, DejaVu Sans, sans-serif"
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
CJK_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
_CJK_FALLBACKS = (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
)
CJK_FONT = CJK_BOLD if Path(CJK_BOLD).exists() else next(
    path for path in (*_CJK_FALLBACKS, BOLD_FONT) if Path(path).exists()
)
CJK_REG_FONT = CJK_REGULAR if Path(CJK_REGULAR).exists() else next(
    path for path in (*_CJK_FALLBACKS, REG_FONT) if Path(path).exists()
)
CJK_INDEX = 0 if Path(CJK_BOLD).exists() else 0
CJK_REG_INDEX = 0 if Path(CJK_REGULAR).exists() else 0

# 2x PNG. README displays awards at width="160".
PLAQUE_W, PLAQUE_H = 300, 248
PLAQUE_DISPLAY_W = 160
CARD_W, CARD_H = 260, 140
LOGO_MAX_W = 200
LOGO_MAX_H_WIDE = 80
LOGO_MAX_H_SQUARE = 96
LOGO_TOP = 32
PTE_LOGO_BOTTOM = 162
PTE_LOGO_MAX_W = 248
NAME_Y_ONE = 135
NAME_Y_TWO = (122, 148)
YEAR_Y = 186
NAME_SIZE = 24
YEAR_SIZE = 22
FRAME_BOX = (6, 6, PLAQUE_W - 7, PLAQUE_H - 7)
FRAME_RX = 16
FRAME_STROKE = 4
CB_YEARS = "2024\uFF5E現在"
AWS_LOCKUP = TECH / "aws-lockup.svg"
GCP_2026 = TECH / "google-cloud-2026.png"


@dataclass(frozen=True)
class Theme:
    suffix: str
    fill: tuple[int, int, int, int]
    fill_hex: str
    name_text: tuple[int, int, int, int]
    year_text: tuple[int, int, int, int]
    site_text: tuple[int, int, int, int]
    title_text: tuple[int, int, int, int]
    muted_hex: str
    title_hex: str
    aws_wordmark: str
    cb_logo_rgb: tuple[int, int, int]


DARK = Theme(
    suffix="",
    fill=(11, 16, 38, 255),
    fill_hex="#0b1026",
    name_text=(230, 237, 247, 255),
    year_text=(60, 185, 252, 255),
    site_text=(139, 148, 158, 255),
    title_text=(230, 237, 243, 255),
    muted_hex="#8B949E",
    title_hex="#E6EDF3",
    aws_wordmark="#FFFFFF",
    cb_logo_rgb=(230, 237, 243),
)
LIGHT = Theme(
    suffix="-light",
    fill=(246, 248, 250, 255),
    fill_hex="#F6F8FA",
    name_text=(11, 31, 58, 255),
    year_text=(9, 105, 218, 255),
    site_text=(87, 96, 106, 255),
    title_text=(11, 31, 58, 255),
    muted_hex="#57606A",
    title_hex="#0B1F3A",
    aws_wordmark="#252F3E",
    cb_logo_rgb=(11, 31, 58),
)


def themed(path: Path, theme: Theme) -> Path:
    if not theme.suffix:
        return path
    return path.with_name(f"{path.stem}{theme.suffix}{path.suffix}")


def trim_alpha(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def fit_contain(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    image = trim_alpha(image)
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return image


def fit_in_box(image: Image.Image, box_w: int, box_h: int) -> Image.Image:
    fitted = fit_contain(image, box_w, box_h)
    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    canvas.alpha_composite(
        fitted, ((box_w - fitted.width) // 2, (box_h - fitted.height) // 2)
    )
    return canvas


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


def cb_logo_mono(path: Path, rgb: tuple[int, int, int]) -> Image.Image:
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
            pixels[x, y] = (*rgb, 255)
    return trim_alpha(image)


def pte_source(theme: Theme) -> Path:
    name = "pte-20251104-rgb-1.png" if theme.suffix else "pte-20251104-rgb-nega-1.png"
    for folder in (AWARDS, PACK):
        path = folder / name
        if path.exists():
            return path
    return AWARDS / "pte-20251104-rgb-nega-1.png"


def pte_art(theme: Theme) -> Image.Image:
    return Image.open(pte_source(theme)).convert("RGBA")


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill=None,
    outline=None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_frame_shell(draw: ImageDraw.ImageDraw, fill: tuple[int, int, int, int]) -> None:
    rounded_rect(
        draw,
        FRAME_BOX,
        FRAME_RX,
        fill=fill,
        outline=(60, 185, 252, 255),
        width=FRAME_STROKE,
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
    theme: Theme,
    *,
    logo_max_h: int,
    logo_max_w: int = LOGO_MAX_W,
    logo_top: int = LOGO_TOP,
    logo_bottom: int | None = None,
) -> None:
    img = Image.new("RGBA", (PLAQUE_W, PLAQUE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    draw_frame_shell(draw, theme.fill)
    names = name_lines or []
    if logo_bottom is None:
        if not names:
            logo_bottom = PTE_LOGO_BOTTOM
        elif len(names) == 1:
            logo_bottom = NAME_Y_ONE - 7
        else:
            logo_bottom = NAME_Y_TWO[0] - 6
    max_h = min(logo_max_h, max(1, logo_bottom - logo_top))
    fitted = fit_contain(logo, logo_max_w, max_h)
    band_y = logo_top + (logo_bottom - logo_top - fitted.height) // 2
    paste_centered(img, fitted, PLAQUE_W // 2, band_y)
    name_font = ImageFont.truetype(CJK_FONT, NAME_SIZE, index=CJK_INDEX)
    year_font = ImageFont.truetype(CJK_FONT, YEAR_SIZE, index=CJK_INDEX)
    if len(names) == 1:
        draw_centered_text(draw, names[0], NAME_Y_ONE, name_font, theme.name_text)
    else:
        for line, y in zip(names, NAME_Y_TWO):
            draw_centered_text(draw, line, y, name_font, theme.name_text)
    draw_centered_text(draw, years, YEAR_Y, year_font, theme.year_text)
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


def write_cb_card(theme: Theme) -> None:
    write_plaque_png(
        themed(AWARDS / "aws-community-builder.png", theme),
        cb_logo_mono(AWARDS / "aws-community-builders-badge.png", theme.cb_logo_rgb),
        ["Community Builder"],
        CB_YEARS,
        theme,
        logo_max_h=LOGO_MAX_H_WIDE,
    )


def write_aws_allcerts(theme: Theme) -> None:
    write_plaque_png(
        themed(AWARDS / "aws-allcerts.png", theme),
        raster_aws(theme.aws_wordmark),
        ["All Certifications", "Engineer"],
        "2022–2025",
        theme,
        logo_max_h=LOGO_MAX_H_WIDE,
    )


def write_jr_champion(theme: Theme) -> None:
    write_plaque_png(
        themed(AWARDS / "aws-jr-champion-2023.png", theme),
        raster_aws(theme.aws_wordmark),
        ["Japan AWS", "Jr. Champion"],
        "2023",
        theme,
        logo_max_h=LOGO_MAX_H_WIDE,
    )


def write_pte(theme: Theme) -> None:
    write_plaque_png(
        themed(AWARDS / "gcp-pte.png", theme),
        pte_art(theme),
        None,
        "2023–2026",
        theme,
        logo_max_h=PTE_LOGO_BOTTOM - LOGO_TOP,
        logo_max_w=PTE_LOGO_MAX_W,
        logo_top=LOGO_TOP,
        logo_bottom=PTE_LOGO_BOTTOM,
    )


def write_all_cert_holders(theme: Theme) -> None:
    write_plaque_png(
        themed(AWARDS / "gcp-all-cert-holders-2025.png", theme),
        Image.open(GCP_2026),
        ["All Certification", "Holders"],
        "2025",
        theme,
        logo_max_h=LOGO_MAX_H_SQUARE,
    )


def write_jaguer(theme: Theme) -> None:
    # Official Jagu'e'r Award mark from Kento's Drive slide『Jagu'e'r Award 2025』p.14
    write_plaque_png(
        themed(AWARDS / "jaguer.png", theme),
        Image.open(AWARDS / "jaguer-award-logo.png"),
        ["Jagu'e'r Award"],
        "2023–2025",
        theme,
        logo_max_h=LOGO_MAX_H_SQUARE,
    )


def chrome_card(title: str, inner: str, width: int, height: int, theme: Theme) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f"<title>{html.escape(title)}</title>"
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="8" '
        f'fill="{theme.fill_hex}" stroke="{NEON}" stroke-width="1"/>'
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


def write_post_icon(filename: str, label: str, glyph: str, theme: Theme) -> None:
    themed(POSTS / filename, theme).write_text(chrome_card(label, glyph, 56, 56, theme))


def write_talk_icon(theme: Theme) -> None:
    inner = (
        f'<g transform="translate(12,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="4" y="6" width="28" height="20" rx="2"/>'
        '<path d="M10 26h16"/>'
        '<path d="M18 26v6"/>'
        '<circle cx="18" cy="16" r="4"/>'
        "</g>"
    )
    themed(TALKS / "mic.svg", theme).write_text(chrome_card("Talk", inner, 56, 56, theme))


def write_generic_ogp(path: Path, site: str, glyph: str, theme: Theme) -> None:
    inner = (
        glyph.replace("translate(14,16)", "translate(16,18)")
        .replace("translate(14,14)", "translate(16,16)")
        .replace("translate(16,12)", "translate(16,14)")
        + f'<text x="72" y="36" fill="{theme.muted_hex}" font-size="13" font-weight="700" '
        f'font-family="{FONT}">{html.escape(site)}</text>'
        f'<text x="72" y="78" fill="{theme.title_hex}" font-size="14" font-weight="700" '
        f'font-family="{FONT}">Latest post</text>'
    )
    path.write_text(chrome_card(site, inner, CARD_W, CARD_H, theme))


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


def render_ogp_png(out: Path, site: str, title: str, icon_svg: Path, theme: Theme) -> None:
    scale = 2
    width, height = CARD_W * scale, CARD_H * scale
    img = Image.new("RGBA", (width, height), theme.fill)
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
    site_font = ImageFont.truetype(CJK_REG_FONT, 26, index=CJK_REG_INDEX)
    title_font = ImageFont.truetype(CJK_REG_FONT, 28, index=CJK_REG_INDEX)
    draw.text((112, 58), site, fill=theme.site_text, font=site_font, anchor="lm")
    lines = wrap_title(title, title_font, width - 48, max_lines=3)
    y = 108
    for line in lines:
        draw.text((24, y), line, fill=theme.title_text, font=title_font)
        y += 40
    img.save(out, "PNG", optimize=True)


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
        r'<a href="([^"]+)"[^>]*>.*?alt="([^"]*)"',
        match.group(1),
        re.S,
    ):
        items.append((html.unescape(href), html.unescape(alt)))
    return items[:3]


def picture_img(dark_src: str, light_src: str, alt: str, width: int | None = None) -> str:
    width_attr = f' width="{width}"' if width is not None else ""
    return (
        "<picture>"
        f'<source media="(prefers-color-scheme: dark)" srcset="{dark_src}" />'
        f'<source media="(prefers-color-scheme: light)" srcset="{light_src}" />'
        f'<img src="{light_src}"{width_attr} alt="{alt}" />'
        "</picture>"
    )


def marker_html(prefix: str, items: list[tuple[str, str]]) -> str:
    parts = []
    for index, (url, title) in enumerate(items, start=1):
        dark = f"./public/images/posts/{prefix}-{index}.png"
        light = f"./public/images/posts/{prefix}-{index}-light.png"
        alt = html.escape(title, quote=True)
        parts.append(
            f'<a href="{html.escape(url, quote=True)}">'
            f"{picture_img(dark, light, alt, CARD_W)}</a>"
        )
    return "\n".join(parts)


def replace_marker(readme: str, tag: str, inner: str) -> str:
    pattern = rf"(<!-- {re.escape(tag)}:START -->)(.*?)(<!-- {re.escape(tag)}:END -->)"
    return re.sub(pattern, rf"\1\n{inner}\n\3", readme, count=1, flags=re.S)


def write_post_and_talk_cards() -> None:
    readme = README.read_text() if README.exists() else ""
    for tag, (site, icon, generic, seed, prefix, glyph) in POST_SEED.items():
        items = parse_marker_items(readme, tag) or seed
        if items and items[0][1] in {"", "AoToLog post", "Zenn post", "Qiita post"}:
            by_url = {url: title for url, title in seed}
            items = [(url, by_url.get(url, title or site)) for url, title in items]
        for theme in (DARK, LIGHT):
            write_generic_ogp(themed(generic, theme), site, glyph(), theme)
            icon_path = themed(icon, theme)
            for index, (url, title) in enumerate(items, start=1):
                render_ogp_png(
                    themed(POSTS / f"{prefix}-{index}.png", theme),
                    site,
                    title,
                    icon_path,
                    theme,
                )
        if README.exists() and f"<!-- {tag}:START -->" in readme:
            readme = replace_marker(readme, tag, marker_html(prefix, items))

    talk_glyph = (
        f'<g transform="translate(12,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="4" y="6" width="28" height="20" rx="2"/>'
        '<path d="M10 26h16M18 26v6"/>'
        '<circle cx="18" cy="16" r="4"/>'
        "</g>"
    )
    for theme in (DARK, LIGHT):
        write_generic_ogp(themed(TALKS / "card-talk.svg", theme), "Speaker Deck", talk_glyph, theme)
        for index, (url, title) in enumerate(TALKS_SEED, start=1):
            render_ogp_png(
                themed(TALKS / f"talk-{index}.png", theme),
                "Speaker Deck",
                title,
                themed(TALKS / "mic.svg", theme),
                theme,
            )

    if README.exists():
        README.write_text(readme)


def write_award_cards() -> None:
    for theme in (DARK, LIGHT):
        write_cb_card(theme)
        write_aws_allcerts(theme)
        write_jr_champion(theme)
        write_pte(theme)
        write_all_cert_holders(theme)
        write_jaguer(theme)


def main() -> None:
    for folder in (AWARDS, POSTS, TALKS, TECH):
        folder.mkdir(parents=True, exist_ok=True)

    for name in (
        "pte-20251104-rgb-1.png",
        "pte-20251104-rgb-nega-1.png",
        "pte-20251104-rgb-nega-2.png",
        "jaguer-award-logo.png",
    ):
        src = PACK / name
        if src.exists():
            (AWARDS / name).write_bytes(src.read_bytes())

    write_tech_logos()
    write_award_cards()
    for theme in (DARK, LIGHT):
        write_post_icon("icon-aotolog.svg", "AoToLog", aotolog_glyph(), theme)
        write_post_icon("icon-zenn.svg", "Zenn", zenn_glyph(), theme)
        write_post_icon("icon-qiita.svg", "Qiita", qiita_glyph(), theme)
        write_talk_icon(theme)
    write_post_and_talk_cards()
    print("wrote award cards, tech logos, and post/talk cards")


if __name__ == "__main__":
    main()
