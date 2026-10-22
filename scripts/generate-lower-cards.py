#!/usr/bin/env python3
"""Generate calm-neon SVG cards: physical award shields, post/talk icons, contact.

Award names sit on a navy engraved plate so dark official logos are never dropped
onto the field. Community Builders and Jagu'e'r circle art work on dark and are
embedded. PTE uses official white-text artwork
(pte-20251104-rgb-nega-1.png / pte-20251104-rgb-nega-2.png).
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PACK = Path("/cursor/stores/self/internal/award-assets")
AWARDS = ROOT / "public" / "images" / "awards"
POSTS = ROOT / "public" / "images" / "posts"
TALKS = ROOT / "public" / "images" / "talks"
CONTACT = ROOT / "public" / "images" / "contact"

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
RIBBON = "#152038"
BOARD = "#101628"
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Every award uses the same canvas so inline GitHub images stay even.
SW, SH = 220, 300
# Verdana is a bit wider than DejaVu; keep a margin so GitHub does not clip.
FONT_PAD = 1.10


def b64_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def b64_png_fitted(path: Path, max_w: int, max_h: int) -> tuple[str, int, int]:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), image.width, image.height


def text_width(text: str, size: float, bold: bool = True) -> float:
    path = BOLD_FONT if bold else REG_FONT
    font = ImageFont.truetype(path, size)
    return float(font.getlength(text)) * FONT_PAD


def fit_size(text: str, max_width: float, start: float, bold: bool = True) -> float:
    size = float(start)
    while size > 6.5 and text_width(text, size, bold) > max_width:
        size -= 0.5
    return size


def heater(cx: float, top: float, width: float, height: float) -> str:
    left = cx - width / 2
    right = cx + width / 2
    bottom = top + height
    return (
        f"M {cx:.1f},{top:.1f} "
        f"C {cx + width * 0.34:.1f},{top:.1f} {right:.1f},{top + 10:.1f} "
        f"{right:.1f},{top + height * 0.18:.1f} "
        f"C {right:.1f},{top + height * 0.52:.1f} {cx + width * 0.28:.1f},"
        f"{top + height * 0.82:.1f} {cx:.1f},{bottom:.1f} "
        f"C {cx - width * 0.28:.1f},{top + height * 0.82:.1f} {left:.1f},"
        f"{top + height * 0.52:.1f} {left:.1f},{top + height * 0.18:.1f} "
        f"C {left:.1f},{top + 10:.1f} {cx - width * 0.34:.1f},{top:.1f} "
        f"{cx:.1f},{top:.1f} Z"
    )


def steel_defs(gid: str) -> str:
    return (
        f"<defs>"
        f'<linearGradient id="rim-{gid}" x1="36" y1="16" x2="184" y2="250" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{STEEL_HI}"/>'
        f'<stop offset="0.28" stop-color="{STEEL_MID}"/>'
        f'<stop offset="0.62" stop-color="{STEEL_LO}"/>'
        f'<stop offset="1" stop-color="{STEEL_EDGE}"/>'
        f"</linearGradient>"
        f'<linearGradient id="bevel-{gid}" x1="50" y1="30" x2="170" y2="210" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#C5D0DA"/>'
        f'<stop offset="0.45" stop-color="#6B7C8C"/>'
        f'<stop offset="1" stop-color="#24303C"/>'
        f"</linearGradient>"
        f'<linearGradient id="enamel-{gid}" x1="64" y1="18" x2="160" y2="230" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#18233C"/>'
        f'<stop offset="0.5" stop-color="{BG}"/>'
        f'<stop offset="1" stop-color="#080C16"/>'
        f"</linearGradient>"
        f'<linearGradient id="base-{gid}" x1="70" y1="250" x2="150" y2="286" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{STEEL_MID}"/>'
        f'<stop offset="1" stop-color="{STEEL_EDGE}"/>'
        f"</linearGradient>"
        f"</defs>"
    )


def screw(cx: float, cy: float) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="3.6" fill="{STEEL_MID}" '
        f'stroke="{STEEL_EDGE}" stroke-width="0.8"/>'
        f'<path d="M{cx - 2.1:.1f},{cy:.1f}h4.2M{cx:.1f},{cy - 2.1:.1f}v4.2" '
        f'stroke="{STEEL_EDGE}" stroke-width="0.7"/>'
    )


def rivet(cx: float, cy: float) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="{STEEL_HI}" '
        f'stroke="{STEEL_EDGE}" stroke-width="0.6"/>'
        f'<circle cx="{cx - 0.4}" cy="{cy - 0.4}" r="0.7" fill="#FFFFFF" opacity="0.55"/>'
    )


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
        f"{text}</text>"
    )


def shield_shell(gid: str, inner: str, title: str) -> str:
    cx, top = 110, 12
    outer = heater(cx, top, 184, 236)
    bevel = heater(cx, top + 5, 170, 224)
    plate = heater(cx, top + 11, 156, 210)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
        f'viewBox="0 0 {SW} {SH}" role="img">'
        f"<title>{title}</title>"
        f"{steel_defs(gid)}"
        f'<rect x="8" y="8" width="204" height="284" rx="8" fill="{BOARD}" '
        f'stroke="{STEEL_LO}" stroke-width="1.2"/>'
        f"{screw(20, 20)}{screw(200, 20)}{screw(20, 280)}{screw(200, 280)}"
        f'<path d="{outer}" fill="url(#rim-{gid})" stroke="{STEEL_EDGE}" stroke-width="1.1"/>'
        f'<path d="{bevel}" fill="url(#bevel-{gid})"/>'
        f'<path d="{plate}" fill="url(#enamel-{gid})" stroke="#3A4A5C" stroke-width="0.8"/>'
        f"{rivet(48, 46)}{rivet(172, 46)}"
        f'<path d="M28 176 L192 176 L182 190 L192 204 L28 204 L38 190 Z" '
        f'fill="{RIBBON}" stroke="{NEON}" stroke-width="1"/>'
        f"{inner}"
        f'<rect x="70" y="252" width="80" height="10" rx="1.5" fill="url(#base-{gid})" '
        f'stroke="{STEEL_EDGE}" stroke-width="0.6"/>'
        f'<rect x="82" y="262" width="56" height="8" rx="1" fill="{STEEL_LO}"/>'
        f'<ellipse cx="110" cy="276" rx="40" ry="5" fill="{STEEL_EDGE}"/>'
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


def nameplate(lines: list[str]) -> str:
    # Engraved plate sits in the wide upper body, above the ribbon.
    block = (
        f'<rect x="52" y="96" width="116" height="44" rx="3" fill="{PLATE}" '
        f'stroke="{STEEL_LO}" stroke-width="0.8"/>'
    )
    parts = [block]
    start_y = 123 if len(lines) == 1 else 112
    for i, line in enumerate(lines):
        size = fit_size(line, 108, 11)
        parts.append(svg_text(110, start_y + i * 14, line, WHITE, size))
    return "".join(parts)


def ribbon_years(years: str) -> str:
    start = 8.5 if years.count("·") >= 3 else 10
    size = fit_size(years, 150, start)
    return svg_text(110, 194, years, NEON, size)


def note_lines(notes: list[str]) -> str:
    parts = []
    for i, line in enumerate(notes):
        size = fit_size(line, 136, 8, bold=False)
        parts.append(svg_text(110, 148 + i * 10, line, MUTED, size, bold=False))
    return "".join(parts)


def write_cb_card() -> None:
    png = b64_png(AWARDS / "aws-community-builders-badge.png")
    title = "AWS Community Builder - Cloud Operations, since 2024"
    inner = (
        f'<image href="data:image/png;base64,{png}" x="78" y="32" width="64" height="64"/>'
        + nameplate(["Community Builder", "Cloud Operations"])
        + ribbon_years("since 2024")
    )
    (AWARDS / "aws-community-builder.svg").write_text(shield_shell("cb", inner, title))


def write_aws_allcerts() -> None:
    title = (
        "Japan All AWS Certifications Engineer 2022 · 2023 · 2024 · 2025 "
        "(2022 APN ALL AWS Certifications Engineer)"
    )
    inner = (
        f'<text x="110" y="54" text-anchor="middle" fill="{WHITE}" font-size="15" '
        f'font-weight="700" font-family="{FONT}">aws</text>'
        + aws_smile(84, 42, 1.2)
        + nameplate(["All Certifications", "Engineer"])
        + note_lines(["2022 APN ALL AWS", "Certifications Engineer"])
        + ribbon_years("2022 · 2023 · 2024 · 2025")
    )
    (AWARDS / "aws-allcerts.svg").write_text(shield_shell("allcerts", inner, title))


def write_jr_champion() -> None:
    title = "2023 Japan AWS Jr. Champion"
    inner = (
        f'<text x="110" y="54" text-anchor="middle" fill="{WHITE}" font-size="15" '
        f'font-weight="700" font-family="{FONT}">aws</text>'
        + aws_smile(84, 42, 1.2)
        + nameplate(["Japan AWS", "Jr. Champion"])
        + ribbon_years("2023")
    )
    (AWARDS / "aws-jr-champion-2023.svg").write_text(shield_shell("jr", inner, title))


def write_pte() -> None:
    title = (
        "Google Cloud Partner Top Engineer 2023 · 2024 · 2025 · 2026 "
        "(2026 Serverless App Development, 2025 General, 2024 Build)"
    )
    # Tall official lockup fits the heater field; wide file is committed beside it.
    png, pw, ph = b64_png_fitted(AWARDS / "pte-20251104-rgb-nega-2.png", 118, 118)
    x = 110 - pw / 2
    inner = (
        f'<image href="data:image/png;base64,{png}" x="{x:.1f}" y="24" '
        f'width="{pw}" height="{ph}"/>'
        + note_lines(["2026 Serverless App Dev", "2025 General · 2024 Build"])
        + ribbon_years("2023 · 2024 · 2025 · 2026")
    )
    (AWARDS / "gcp-pte.svg").write_text(shield_shell("pte", inner, title))


def write_all_cert_holders() -> None:
    title = "Google Cloud Partner All Certification Holders 2025"
    inner = (
        gcp_mark(92, 40, 36, "gcg-holders")
        + nameplate(["All Certification", "Holders"])
        + ribbon_years("2025")
    )
    (AWARDS / "gcp-all-cert-holders-2025.svg").write_text(
        shield_shell("holders", inner, title)
    )


def write_jaguer() -> None:
    png = b64_png(AWARDS / "jaguer-circle.png")
    title = (
        "Jagu'e'r Award 2023 · 2024 · 2025 "
        "(2025 Grand Prize, 2024 Excellent, 2023 Excellent)"
    )
    inner = (
        f'<image href="data:image/png;base64,{png}" x="78" y="30" width="64" height="64"/>'
        + nameplate(["Jagu'e'r Award"])
        + note_lines(["2025 Grand Prize", "2024 Excellent", "2023 Excellent"])
        + ribbon_years("2023 · 2024 · 2025")
    )
    (AWARDS / "jaguer.svg").write_text(shield_shell("jaguer", inner, title))


def plaque(title: str, inner: str, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f"<title>{title}</title>"
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
    (POSTS / filename).write_text(plaque(label, glyph, 56, 56))


def write_talk_icon() -> None:
    inner = (
        f'<g transform="translate(12,12)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="4" y="6" width="28" height="20" rx="2"/>'
        '<path d="M10 26h16"/>'
        '<path d="M18 26v6"/>'
        '<circle cx="18" cy="16" r="4"/>'
        "</g>"
    )
    (TALKS / "mic.svg").write_text(plaque("Talk", inner, 56, 56))


def write_talk_more() -> None:
    inner = (
        f'<text x="160" y="28" text-anchor="middle" fill="{NEON}" font-size="13" '
        f'font-weight="700" font-family="{FONT}">and more on Speaker Deck</text>'
    )
    (TALKS / "more.svg").write_text(plaque("Speaker Deck", inner, 320, 44))


def write_contact() -> None:
    inner = (
        f'<g transform="translate(18,12)" fill="none" stroke="{NEON}" stroke-width="1.6">'
        '<rect x="0" y="2" width="22" height="16" rx="2"/>'
        '<path d="m1 4 10 7 10-7"/>'
        "</g>"
        f'<text x="52" y="28" fill="{NEON}" font-size="14" font-weight="700" '
        f'font-family="{FONT}">aoto@datadoghq.com</text>'
    )
    (CONTACT / "mail.svg").write_text(plaque("aoto@datadoghq.com", inner, 280, 44))


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
    write_talk_more()
    write_contact()
    print("wrote physical shields and post/talk/contact cards")


if __name__ == "__main__":
    main()
