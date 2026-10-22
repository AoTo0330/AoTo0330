#!/usr/bin/env python3
"""Generate calm-neon SVG cards for awards, post headers, talks, and contact.

Award names are drawn as white/cyan text so dark-on-light official logos are
never placed directly on navy. Community Builders and Jagu'e'r circle artwork
work on dark and are embedded. PTE 2026 official white-text PNGs were not
available; those shields follow the described 2026 artwork.
"""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AWARDS = ROOT / "public" / "images" / "awards"
POSTS = ROOT / "public" / "images" / "posts"
TALKS = ROOT / "public" / "images" / "talks"
CONTACT = ROOT / "public" / "images" / "contact"

BG = "#0b1026"
NEON = "#3CB9FC"
MUTED = "#8B949E"
WHITE = "#E6EDF3"
STAR = "#FBBC04"
FONT = "Verdana, DejaVu Sans, sans-serif"

W, H = 270, 168


def b64_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def plaque(title: str, inner: str, width: int = W, height: int = H) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f"<title>{title}</title>"
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="8" '
        f'fill="{BG}" stroke="{NEON}" stroke-width="1"/>'
        f"{inner}</svg>\n"
    )


def aws_smile(x: float, y: float, scale: float = 1.0) -> str:
    # Smile from the existing tech-stack AWS mark, kept cyan for the palette.
    return (
        f'<g transform="translate({x},{y}) scale({scale})">'
        '<path fill="#3CB9FC" d="M21.698 16.207c-2.626 1.94-6.442 2.969-9.722 2.969'
        "-4.598 0-8.74-1.7-11.87-4.526-.247-.223-.024-.527.272-.351 3.384 1.963 "
        "7.559 3.153 11.877 3.153 2.914 0 6.114-.607 9.06-1.852.439-.2.814.287.383.607z"
        'M22.792 14.961c-.336-.43-2.22-.207-3.074-.103-.255.032-.295-.192-.063-.36 '
        "1.5-1.053 3.967-.75 4.254-.399.287.36-.08 2.826-1.485 4.007-.215.184-.423.088"
        '-.327-.151.32-.79 1.03-2.57.695-2.994z"/></g>'
    )


def gcp_mark(x: float, y: float, size: float = 36) -> str:
    # Compact 2026-style gradient cloud (official PTE PNGs were not on this VM).
    s = size / 24
    return (
        f'<defs><linearGradient id="gcg" x1="12" y1="2" x2="8" y2="22" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="#EA4335"/>'
        f'<stop offset="0.35" stop-color="#FBBC04"/>'
        f'<stop offset="0.7" stop-color="#34A853"/>'
        f'<stop offset="1" stop-color="#4285F4"/>'
        f"</linearGradient></defs>"
        f'<g transform="translate({x},{y}) scale({s})">'
        '<path fill="url(#gcg)" d="M19 14a5 5 0 0 0-1.1-9.9A7 7 0 0 0 6.1 8.2 '
        '4.5 4.5 0 0 0 6 17h12.5A4.5 4.5 0 0 0 19 14z"/>'
        "</g>"
    )


def star(cx: float, cy: float, r: float = 8) -> str:
    return (
        f'<path fill="{STAR}" transform="translate({cx},{cy}) scale({r / 10})" '
        'd="M0-10 2.4-3.1 9.5-3.1 3.6 1.2 5.9 8.1 0 4.2-5.9 8.1-3.6 1.2-9.5-3.1-2.4-3.1z"/>'
    )


def browser_icon(x: float, y: float) -> str:
    return (
        f'<g transform="translate({x},{y})" fill="none" stroke="{WHITE}" stroke-width="1.4">'
        '<rect x="0" y="0" width="22" height="16" rx="2"/>'
        '<path d="M0 5h22"/>'
        '<circle cx="4" cy="2.6" r="0.7" fill="{WHITE}" stroke="none"/>'
        "</g>"
    ).replace('fill="{WHITE}"', f'fill="{WHITE}"')


def chart_icon(x: float, y: float) -> str:
    return (
        f'<g transform="translate({x},{y})" fill="none" stroke="{WHITE}" stroke-width="1.4">'
        '<path d="M2 16V2"/>'
        '<path d="M2 16h16"/>'
        '<path d="M6 12v-4M10 12V6M14 12V8"/>'
        "</g>"
    )


def write_aws_year_card(filename: str, year: str, lines: list[str], title: str) -> None:
    tspans = []
    y = 100
    for i, line in enumerate(lines):
        tspans.append(
            f'<text x="135" y="{y + i * 16}" text-anchor="middle" fill="{WHITE}" '
            f'font-size="12" font-family="{FONT}">{line}</text>'
        )
    inner = (
        f'<text x="135" y="36" text-anchor="middle" fill="{WHITE}" font-size="18" '
        f'font-weight="700" font-family="{FONT}">aws</text>'
        + aws_smile(104, 22, 1.6)
        + f'<text x="135" y="82" text-anchor="middle" fill="{NEON}" font-size="26" '
        f'font-weight="700" font-family="{FONT}">{year}</text>'
        + "".join(tspans)
    )
    (AWARDS / filename).write_text(plaque(title, inner))


def write_cb_card() -> None:
    png = b64_png(AWARDS / "aws-community-builders-badge.png")
    title = "AWS Community Builder - Cloud Operations, since 2024"
    inner = (
        f'<image href="data:image/png;base64,{png}" x="18" y="28" width="88" height="88"/>'
        f'<text x="122" y="62" fill="{WHITE}" font-size="13" font-weight="700" '
        f'font-family="{FONT}">AWS Community</text>'
        f'<text x="122" y="80" fill="{WHITE}" font-size="13" font-weight="700" '
        f'font-family="{FONT}">Builder</text>'
        f'<text x="122" y="104" fill="{MUTED}" font-size="11" font-family="{FONT}">'
        "Cloud Operations</text>"
        f'<text x="122" y="124" fill="{NEON}" font-size="12" font-family="{FONT}">'
        "since 2024</text>"
    )
    (AWARDS / "aws-community-builder.svg").write_text(plaque(title, inner))


def write_jr_champion() -> None:
    title = "2023 Japan AWS Jr. Champion"
    inner = (
        f'<text x="135" y="36" text-anchor="middle" fill="{WHITE}" font-size="18" '
        f'font-weight="700" font-family="{FONT}">aws</text>'
        + aws_smile(104, 22, 1.6)
        + f'<text x="135" y="82" text-anchor="middle" fill="{NEON}" font-size="26" '
        f'font-weight="700" font-family="{FONT}">2023</text>'
        f'<text x="135" y="104" text-anchor="middle" fill="{WHITE}" font-size="12" '
        f'font-family="{FONT}">Japan AWS</text>'
        f'<text x="135" y="128" text-anchor="middle" fill="{WHITE}" font-size="14" '
        f'font-weight="700" font-family="{FONT}">Jr. Champion</text>'
    )
    (AWARDS / "aws-jr-champion-2023.svg").write_text(plaque(title, inner))


def write_pte(filename: str, year: str, track: str | None, title: str) -> None:
    track_svg = ""
    if track:
        track_svg = (
            f'<text x="135" y="150" text-anchor="middle" fill="{MUTED}" font-size="10" '
            f'font-family="{FONT}">{track}</text>'
        )
    inner = (
        gcp_mark(22, 18, 34)
        + star(70, 36, 7)
        + browser_icon(188, 22)
        + chart_icon(218, 22)
        + f'<text x="135" y="78" text-anchor="middle" fill="{MUTED}" font-size="10" '
        f'font-family="{FONT}">GOOGLE CLOUD</text>'
        f'<text x="135" y="100" text-anchor="middle" fill="{WHITE}" font-size="13" '
        f'font-weight="700" font-family="{FONT}">Partner Top Engineer</text>'
        f'<text x="135" y="128" text-anchor="middle" fill="{NEON}" font-size="26" '
        f'font-weight="700" font-family="{FONT}">{year}</text>'
        + track_svg
    )
    (AWARDS / filename).write_text(plaque(title, inner))


def write_all_cert_holders() -> None:
    title = "Google Cloud Partner All Certification Holders 2025"
    inner = (
        gcp_mark(22, 18, 34)
        + browser_icon(188, 22)
        + chart_icon(218, 22)
        + f'<text x="135" y="78" text-anchor="middle" fill="{MUTED}" font-size="10" '
        f'font-family="{FONT}">GOOGLE CLOUD</text>'
        f'<text x="135" y="98" text-anchor="middle" fill="{WHITE}" font-size="12" '
        f'font-weight="700" font-family="{FONT}">Partner All Certification</text>'
        f'<text x="135" y="116" text-anchor="middle" fill="{WHITE}" font-size="12" '
        f'font-weight="700" font-family="{FONT}">Holders</text>'
        f'<text x="135" y="144" text-anchor="middle" fill="{NEON}" font-size="24" '
        f'font-weight="700" font-family="{FONT}">2025</text>'
    )
    (AWARDS / "gcp-all-cert-holders-2025.svg").write_text(plaque(title, inner))


def write_jaguer(filename: str, year: str, prize: str, title: str) -> None:
    png = b64_png(AWARDS / "jaguer-circle.png")
    # Laurel sprigs from the 2024 slide (blue branches, small pink cross is in the circle art).
    laurels = (
        f'<g fill="none" stroke="#427BBF" stroke-width="2" stroke-linecap="round">'
        f'<path d="M78 118c-10-14-12-32-6-46"/>'
        f'<path d="M72 92c-6-2-10 2-12 8M74 80c-7-1-11 4-12 10M80 70c-6 0-10 5-10 10"/>'
        f'<path d="M192 118c10-14 12-32 6-46"/>'
        f'<path d="M198 92c6-2 10 2 12 8M196 80c7-1 11 4 12 10M190 70c6 0 10 5 10 10"/>'
        "</g>"
    )
    inner = (
        laurels
        + f'<image href="data:image/png;base64,{png}" x="99" y="14" width="72" height="72"/>'
        f'<text x="135" y="108" text-anchor="middle" fill="{WHITE}" font-size="13" '
        f'font-weight="700" font-family="{FONT}">Jagu\'e\'r Award {year}</text>'
        f'<text x="135" y="132" text-anchor="middle" fill="{NEON}" font-size="14" '
        f'font-weight="700" font-family="{FONT}">{prize}</text>'
    )
    (AWARDS / filename).write_text(plaque(title, inner))


def write_post_header(filename: str, label: str, glyph: str, title: str) -> None:
    inner = (
        glyph
        + f'<text x="58" y="32" fill="{WHITE}" font-size="16" font-weight="700" '
        f'font-family="{FONT}">{label}</text>'
        f'<text x="58" y="50" fill="{MUTED}" font-size="11" font-family="{FONT}">Latest posts</text>'
    )
    (POSTS / filename).write_text(plaque(title, inner, 420, 64))


def zenn_glyph() -> str:
    return (
        '<g transform="translate(18,16) scale(1.15)">'
        f'<path fill="{NEON}" d="M.264 23.771h4.984c.264 0 .498-.147.645-.352L19.614.874c.176-.293-.029-.645-.381-.645h-4.72c-.235 0-.44.117-.557.323L.03 23.361c-.088.176.029.41.234.41zM17.445 23.419l6.479-10.408c.205-.323-.029-.733-.41-.733h-4.691c-.176 0-.352.088-.44.235l-6.655 10.643c.176.264.029.616.352.616h4.779c.234-.001.468-.118.586-.353z"/>'
        "</g>"
    )


def qiita_glyph() -> str:
    return (
        '<g transform="translate(16,14) scale(1.2)">'
        f'<path fill="{NEON}" d="M12 0C5.3726 0 0 5.3726 0 12s5.3726 12 12 12c3.3984 0 6.4665-1.413 8.6498-3.6832-.383-.0574-.7746-.2062-1.1466-.4542-.7145-.4763-1.3486-.9263-1.6817-1.674-1.2945 1.3807-3.0532 1.835-5.1822 2.0503-4.311.4359-8.0456-1.4893-8.4979-6.2996-.1922-2.045.2628-3.989 1.1804-5.582l-.5342-2.1009c-.0862-.3652.2498-.7126.6057-.6262l1.8456.448c1.0974-.9012 2.4249-1.49 3.8892-1.638 1.2526-.1267 2.467.0834 3.571.5624l1.7348-1.0494c.3265-.1974.7399.0257.7711.4164l.1 2.4747v.0002c1.334 1.4084 2.2424 3.3319 2.4478 5.516.116 1.2339-.012 2.1776-.339 3.078-.1531.4215-.1992.7778.0776 1.1305.2674.3408.6915 1.0026 1.1644.8917.7107-.1666 1.4718-.1223 1.9422.1715C23.4925 15.9525 24 14.0358 24 12c0-6.6274-5.3726-12-12-12Z"/>'
        "</g>"
    )


def aotolog_glyph() -> str:
    return (
        f'<g transform="translate(18,16)" fill="none" stroke="{NEON}" stroke-width="1.8">'
        '<rect x="2" y="1" width="22" height="28" rx="3"/>'
        '<path d="M8 9h10M8 14h10M8 19h6"/>'
        "</g>"
    )


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


def write_bullet() -> None:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10">'
        f'<circle cx="5" cy="5" r="3" fill="{NEON}"/></svg>\n'
    )
    (POSTS / "bullet.svg").write_text(svg)


def main() -> None:
    for folder in (AWARDS, POSTS, TALKS, CONTACT):
        folder.mkdir(parents=True, exist_ok=True)

    write_cb_card()
    write_aws_year_card(
        "aws-allcerts-2025.svg",
        "2025",
        ["Japan All AWS", "Certifications Engineer"],
        "2025 Japan All AWS Certifications Engineer",
    )
    write_aws_year_card(
        "aws-allcerts-2024.svg",
        "2024",
        ["Japan All AWS", "Certifications Engineer"],
        "2024 Japan AWS All Certifications Engineer",
    )
    write_aws_year_card(
        "aws-allcerts-2023.svg",
        "2023",
        ["Japan All AWS", "Certifications Engineer"],
        "2023 Japan AWS All Certifications Engineer",
    )
    write_aws_year_card(
        "aws-allcerts-2022.svg",
        "2022",
        ["APN ALL AWS", "Certifications Engineer"],
        "2022 APN ALL AWS Certifications Engineer",
    )
    write_jr_champion()
    write_pte(
        "gcp-pte-2026.svg",
        "2026",
        "Serverless App Development",
        "Google Cloud Partner Top Engineer 2026(Serverless App Development)",
    )
    write_pte(
        "gcp-pte-2025.svg",
        "2025",
        "General",
        "Google Cloud Partner Top Engineer 2025(General)",
    )
    write_pte(
        "gcp-pte-2024.svg",
        "2024",
        "Build",
        "Google Cloud Partner Top Engineer 2024(Build)",
    )
    write_pte(
        "gcp-pte-2023.svg",
        "2023",
        None,
        "Google Cloud Partner Top Engineer 2023",
    )
    write_all_cert_holders()
    write_jaguer(
        "jaguer-2025.svg",
        "2025",
        "Grand Prize",
        "Jagu'e'r Award 2025 - Grand Prize",
    )
    write_jaguer(
        "jaguer-2024.svg",
        "2024",
        "Excellent Award",
        "Jagu'e'r Award 2024 - Excellent Award",
    )
    write_jaguer(
        "jaguer-2023.svg",
        "2023",
        "Excellent Award",
        "Jagu'e'r Award 2023 - Excellent Award",
    )
    write_post_header("header-aotolog.svg", "AoToLog", aotolog_glyph(), "AoToLog")
    write_post_header("header-zenn.svg", "Zenn", zenn_glyph(), "Zenn")
    write_post_header("header-qiita.svg", "Qiita", qiita_glyph(), "Qiita")
    write_bullet()
    write_talk_icon()
    write_talk_more()
    write_contact()
    print("wrote award/post/talk/contact cards")


if __name__ == "__main__":
    main()
