"""Draws the monochrome SVG panels for the GitHub profile README.
Run `python gen.py`; it checks the live sites and rewrites everything in assets/."""
import ssl
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "assets"
# onehealth.my is left out: its host (Hostinger CDN) answers 403 to GitHub Actions servers
SITES = [("qa-portfolio", "https://nagisa314.github.io/qa-portfolio/")]
PHT = timezone(timedelta(hours=8))
BG, PANEL, FG, DIM, LINE, DOT = "#0d0d0d", "#141414", "#f2f2f2", "#8a8a8a", "#262626", "#202020"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

CAT = [  # sitting cat; e = eye
    "...#.....#.....",
    "...##...##.....",
    "...#######.....",
    "..#########....",
    "..##e###e##....",
    "..#########....",
    "...#######.....",
    "....#####......",
    "...#######.....",
    "..#########..#.",
    "..#########...#",
    "..#########...#",
    "..#########..#.",
    "..###########..",
    "...##...##.....",
]
WALK = [  # side-view cat facing right, legs drawn per frame
    "........#.#.",
    "#.......###.",
    "#......##.#.",
    ".##########.",
    ".#########..",
]
LEGS = [".#.#...#.#..", "..#.#.#.#..."]
FONT = {  # 5x7 pixel letters
    "K": ["1...1", "1..1.", "1.1..", "11...", "1.1..", "1..1.", "1...1"],
    "R": ["1111.", "1...1", "1...1", "1111.", "1.1..", "1..1.", "1...1"],
    "A": [".111.", "1...1", "1...1", "11111", "1...1", "1...1", "1...1"],
    "V": ["1...1", "1...1", "1...1", "1...1", "1...1", ".1.1.", "..1.."],
    "E": ["11111", "1....", "1....", "1111.", "1....", "1....", "11111"],
    "N": ["1...1", "11..1", "1.1.1", "1..11", "1...1", "1...1", "1...1"],
}


def pixels(rows, x0, y0, s, on="#"):
    """One rect per horizontal run of `on` cells."""
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x] != on:
                x += 1
                continue
            start = x
            while x < len(row) and row[x] == on:
                x += 1
            out.append(f'<rect x="{x0 + start * s}" y="{y0 + y * s}" width="{(x - start) * s}" height="{s}"/>')
    return "".join(out)


def check(url, timeout=15):
    """(passed, detail) for one live site. urllib verifies the https cert by default."""
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nagisa314-readme-check"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = r.status
    except urllib.error.HTTPError as e:  # got an answer, just a bad status
        code = e.code
    except Exception as e:  # dns, timeout, refused, bad cert
        reason = getattr(e, "reason", e)
        if isinstance(reason, ssl.SSLError):
            return False, "https cert invalid"
        return False, "timed out" if isinstance(reason, TimeoutError) else "unreachable"
    detail = f"{code} · {time.monotonic() - start:.1f}s"
    return code < 400, detail + (" · https ok" if code < 400 and url.startswith("https") else "")


def svg(w, h, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f"<style>text{{font-family:{MONO}}}{style}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>"
        # own dark tile so panels look the same on GitHub light and dark themes
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{LINE}"/>'
        f"{body}</svg>"
    )


def typed(cid, text, x, y, begin, size=15, color=FG, tail=""):
    """Text revealed one character at a time: a clip window slides right in char-sized steps."""
    w = round((len(text) + 3) * size * 0.62)  # +3 leaves room for the tail cursor
    n = len(text) + 3
    return (
        f"<style>#{cid} rect{{animation:{cid} {n * 0.045:.2f}s steps({n}) {begin}s both}}"
        f"@keyframes {cid}{{to{{transform:translateX({w}px)}}}}"
        # reduced motion turns the animation off, so park the clip where the text shows
        f"@media (prefers-reduced-motion:reduce){{#{cid} rect{{transform:translateX({w}px)}}}}</style>"
        f'<clipPath id="{cid}"><rect x="{x - w}" y="{y - size}" width="{w}" height="{size * 1.6}"/></clipPath>'
        f'<text clip-path="url(#{cid})" x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(text)}{tail}</text>'
    )


def hero():
    name = "".join(f'<g>{pixels(FONT[c], 260 + i * 42, 70, 7, on="1")}</g>' for i, c in enumerate("KRAVEN"))
    line1 = "i build ai automations for small businesses"
    line2 = "and test them like a qa engineer."
    body = (
        f'<defs><pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
        f'<rect x="8" y="8" width="1.5" height="1.5" fill="{DOT}"/></pattern></defs>'
        '<rect x="1" y="1" width="838" height="278" rx="12" fill="url(#dots)"/>'
        f'<g fill="{FG}" shape-rendering="crispEdges">{pixels(CAT, 60, 66, 10)}{name}</g>'
        f'<g class="eye" shape-rendering="crispEdges">{pixels(CAT, 60, 66, 10, on="e")}</g>'
        + typed("t1", line1, 260, 160, 0.4)
        + typed("t2", line2, 260, 185, 2.6, tail='<tspan class="cur"> _</tspan>')
        + f'<rect class="pulse" x="260" y="219" width="7" height="7" fill="{FG}"/>'
        f'<text x="276" y="226" font-size="12" fill="{DIM}">open for freelance work  ·  cavite, ph  ·  bs it 2026</text>'
    )
    style = (
        f".eye{{fill:{BG};animation:blink 4s step-end infinite}}"
        f"@keyframes blink{{93%{{fill:{FG}}}97%{{fill:{BG}}}}}"
        ".cur{animation:on 1s step-end infinite}@keyframes on{50%{opacity:0}}"
        ".pulse{animation:pulse 2s ease-in-out infinite}@keyframes pulse{50%{opacity:.25}}"
    )
    return svg(840, 280, body, style)


def pipeline(results, checked_at):
    """results: [(site, passed, detail)] from check()."""
    steps = [
        ("fetch", "qa tester · bs it graduate · cavite, ph"),
        ("decide", "automate the boring parts of small businesses"),
        ("deliver", "site-doctor · qa-portfolio · one health"),
        ("schedule", "open for freelance work"),
    ]

    def row(mark, name, detail):
        return (
            f'<tspan x="28">{mark}</tspan><tspan x="56" font-weight="700">{escape(name)}</tspan>'
            f'<tspan x="200" fill="{DIM}">{escape(detail)}</tspan>'
        )

    passed = sum(ok for _, ok, _ in results)
    failed = len(results) - passed
    if not results:
        status = "no checks run"
    elif not failed:
        status = "all checks passing"
    else:
        status = f"{failed} check{'s' * (failed > 1)} failing"
    lines = [f'<tspan fill="{DIM}">$</tspan> kraven run']
    lines += [row("✓", n, d) for n, d in steps]
    lines.append(f'<tspan fill="{DIM}">$</tspan> kraven check --live')
    lines += [row("✓" if ok else "✗", site, detail) for site, ok, detail in results]
    lines.append(
        f'{status}<tspan fill="{DIM}">  ·  {passed}/{len(results)}  ·  checked {checked_at.strftime("%d %b, %H:%M").lower()} pht</tspan>'
        '<tspan class="cur"> _</tspan>'
    )
    text = "".join(
        f'<text class="l" style="animation-delay:{0.4 + i * 0.45:.2f}s" x="28" y="{80 + i * 28}" '
        f'font-size="14" fill="{FG}">{t}</text>'
        for i, t in enumerate(lines)
    )
    bar = (
        f'<path d="M1 36V13A12 12 0 0 1 13 1H827A12 12 0 0 1 839 13V36Z" fill="{PANEL}"/>'
        f'<line x1="1" y1="36" x2="839" y2="36" stroke="{LINE}"/>'
        + "".join(f'<circle cx="{x}" cy="18.5" r="5" fill="#3a3a3a"/>' for x in (24, 42, 60))
        + f'<text x="420" y="23" font-size="12" fill="{DIM}" text-anchor="middle">kraven — run</text>'
    )
    style = (
        ".l{animation:in .3s ease-out both}@keyframes in{from{opacity:0}}"
        ".cur{animation:on 1s step-end infinite}@keyframes on{50%{opacity:0}}"
    )
    return svg(840, 80 + len(lines) * 28, bar + text, style)


def card(title, desc, tag, linked=True):
    body = (
        f'<text x="22" y="42" font-size="16" font-weight="700" fill="{FG}">{escape(title)}</text>'
        + (f'<text x="248" y="42" font-size="16" fill="{DIM}" text-anchor="end">↗</text>' if linked else "")
        + "".join(
            f'<text x="22" y="{72 + i * 20}" font-size="13" fill="{DIM}">{escape(d)}</text>' for i, d in enumerate(desc)
        )
        + f'<rect x="22" y="111" width="7" height="7" fill="{FG}"/>'
        f'<text x="36" y="118" font-size="12" fill="{DIM}">{escape(tag)}</text>'
    )
    return svg(270, 140, body)


def footer():
    frames = "".join(
        f'<g class="f{i}">{pixels(WALK + [legs], 0, 20, 4)}</g>' for i, legs in enumerate(LEGS)
    )
    body = (
        f'<line x1="20" y1="44.5" x2="820" y2="44.5" stroke="{LINE}"/>'
        f'<g class="walk" fill="{FG}" shape-rendering="crispEdges">{frames}</g>'
    )
    style = (
        ".walk{animation:walk 16s linear infinite}@keyframes walk{from{transform:translateX(-40px)}to{transform:translateX(860px)}}"
        ".f0{animation:f0 .5s step-end infinite}.f1{animation:f1 .5s step-end infinite}"
        "@keyframes f0{50%{opacity:0}}@keyframes f1{0%{opacity:0}50%{opacity:1}}"
    )
    return svg(840, 56, body, style)


def panels(results, checked_at):
    return {
        "hero.svg": hero(),
        "pipeline.svg": pipeline(results, checked_at),
        "card-site-doctor.svg": card("site-doctor", ["website health check", "for small businesses"], "python", linked=False),  # repo is private
        "card-qa-portfolio.svg": card("qa-portfolio", ["test cases, bug reports", "and qa write-ups"], "html · qa"),
        "card-one-health.svg": card("one health", ["immunization & prenatal", "records · capstone"], "laravel · react"),
        "footer.svg": footer(),
    }


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    results = []
    for site, url in SITES:
        try:
            results.append((site, *check(url)))
        except Exception:  # one broken check must not stop the other panels from being written
            results.append((site, False, "check error"))
    for name, data in panels(results, datetime.now(PHT)).items():
        ET.fromstring(data)  # self-check: well-formed XML
        assert "href" not in data and "url(http" not in data, f"{name}: GitHub blocks external refs in SVG images"
        (OUT / name).write_text(data, encoding="utf-8")
        print(f"{name:24} {len(data):6} bytes")
