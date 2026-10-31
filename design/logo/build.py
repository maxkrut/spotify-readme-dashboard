"""Build editable and outlined Geologica 600 logo proposals, without installing into this repo.

Requires fonttools and uharfbuzz in an external Python environment.
Rasterize comparison.svg with any SVG renderer at 2x for the comparison PNG.
"""
from __future__ import annotations

import io
import argparse
import json
import math
from dataclasses import dataclass
from html import escape
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parent
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--set", default="1", choices=("1", "2", "3", "4", "all"), help="Proposal set to build")
ARGS = PARSER.parse_args()
SUFFIX = "-all" if ARGS.set == "all" else ("" if ARGS.set == "1" else f"-{int(ARGS.set):02d}")
if ARGS.set == "all":
    CONFIG = json.loads((ROOT / "variants.json").read_text(encoding="utf-8"))
    for index in (2, 3, 4):
        CONFIG["variants"].extend(json.loads((ROOT / f"variants-{index:02d}.json").read_text(encoding="utf-8"))["variants"])
    CONFIG["variants"].sort(key=lambda variant: (int(variant["id"][:2]), variant["id"]))
    for variant in CONFIG["variants"]:
        variant["display_id"] = variant["id"].upper()
    CONFIG["board_label"] = "ВСЕ ВАРИАНТЫ / SPOTIFY GREEN #1ED760"
    CONFIG["row_height"] = 112
    CONFIG["board_subtitle"] = "Geologica 600 · высота 48 px · B — дополнительная палитра"
    (ROOT / "variants-all.json").write_text(json.dumps(CONFIG, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    CONFIG = json.loads((ROOT / f"variants{SUFFIX}.json").read_text(encoding="utf-8"))
FONT_PATH = ROOT / "fonts" / "Geologica-variable.ttf"
FONT = instantiateVariableFont(TTFont(FONT_PATH), CONFIG["font"]["axes"], inplace=True)
UPM = FONT["head"].unitsPerEm
GLYPHS = FONT.getGlyphSet()
GLYPH_ORDER = FONT.getGlyphOrder()
font_buffer = io.BytesIO()
FONT.save(font_buffer)
font_buffer.seek(0)
SHAPER = hb.Font(hb.Face(font_buffer.getvalue()))
SHAPER.scale = (UPM, UPM)


def num(value: float) -> str:
    return f"{value:.5f}".rstrip("0").rstrip(".") or "0"


@dataclass
class Word:
    key: str
    text: str
    size: float
    tracking: float = 0
    x: float = 0
    y: float = 0
    angle: float = 0

    def __post_init__(self):
        paths = []
        boxes = []
        buffer = hb.Buffer()
        buffer.add_str(self.text)
        buffer.guess_segment_properties()
        hb.shape(SHAPER, buffer, {"liga": False})
        cursor = 0
        cosine = math.cos(math.radians(self.angle))
        sine = math.sin(math.radians(self.angle))
        scale = self.size / UPM
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
            offset = cursor + position.x_offset
            dx, dy = offset * scale, -position.y_offset * scale
            transform = (scale * cosine, scale * sine, scale * sine, -scale * cosine,
                         dx * cosine - dy * sine, dx * sine + dy * cosine)
            if self.angle == 0:
                # Preserve the original contour rounding for recolored proposals.
                transform = (self.size / UPM, 0, 0, -self.size / UPM,
                             offset * self.size / UPM, -position.y_offset * self.size / UPM)
            glyph = GLYPHS[GLYPH_ORDER[info.codepoint]]
            pen = SVGPathPen(GLYPHS, ntos=num)
            glyph.draw(TransformPen(pen, transform))
            paths.append(pen.getCommands())
            bounds = BoundsPen(GLYPHS)
            glyph.draw(TransformPen(bounds, transform))
            if bounds.bounds:
                boxes.append(bounds.bounds)
            cursor += position.x_advance + self.tracking * UPM
        self.path = " ".join(paths)
        self.bounds = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                       max(b[2] for b in boxes), max(b[3] for b in boxes))

    @property
    def width(self):
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self):
        return self.bounds[3] - self.bounds[1]

    def at(self, left, top):
        self.x = left - self.bounds[0]
        self.y = top - self.bounds[1]
        return self


class Rule:
    """A typographic fraction rule; background stays transparent."""
    def __init__(self, key, width, thickness, x, y):
        self.key, self.x, self.y = key, x, y
        self.bounds = (0, 0, width, thickness)
        self.path = f"M0 0H{num(width)}V{num(thickness)}H0Z"
        self.text = ""


def arc_word(key, text, size, radius, center_y, bottom=False):
    """Place unwarped, individually rotated letters on a circular baseline."""
    letters = [Word(key, char, size) for char in text]
    advances = [letter.width + size * .14 for letter in letters]
    total = sum(advances) - size * .14
    cursor = -total / 2
    result = []
    for char, advance, original in zip(text, advances, letters):
        distance = cursor + original.width / 2
        angle = distance / radius
        direction = -1 if bottom else 1
        x = radius * math.sin(angle)
        y = center_y + direction * radius * (1 - math.cos(angle))
        glyph = Word(key, char, size, angle=direction * math.degrees(angle))
        glyph.at(x - glyph.width / 2, y - glyph.height / 2)
        result.append(glyph)
        cursor += advance
    return result


def row(words, gap):
    cursor = 0
    for word in words:
        word.x = cursor - word.bounds[0]
        cursor += word.width + gap
    return cursor - gap


def layout(kind):
    if kind == "inline":
        words = [Word(k, k, 48, -.025) for k in ("spotify", "readme", "dashboard")]
        row(words, 14)
        return words
    if kind == "spotify_hero":
        main = Word("spotify", "spotify", 58, -.035).at(0, 0)
        a = Word("readme", "README", 14, .13)
        b = Word("dashboard", "dashboard", 20, -.02)
        side_height = a.height + 9 + b.height
        top = (main.height - side_height) / 2
        a.at(main.width + 17, top)
        b.at(main.width + 17, top + a.height + 9)
        return [main, a, b]
    if kind == "readme_hero":
        main = Word("readme", "readme", 44, -.045).at(0, 20)
        a = Word("spotify", "SPOTIFY", 12, .18).at(1, 0)
        b = Word("dashboard", "dashboard", 14, .015)
        b.at(main.width + 12, 20 + main.height - b.height)
        return [a, main, b]
    if kind == "two_lines":
        a = Word("spotify", "spotify", 23, -.025)
        b = Word("readme", "readme", 23, -.025)
        top_width = row([a, b], 9)
        top_min = min(a.bounds[1], b.bounds[1])
        top_max = max(a.bounds[3], b.bounds[3])
        c = Word("dashboard", "dashboard", 38, -.04)
        width = max(top_width, c.width)
        for word in [a, b]:
            word.x += (width - top_width) / 2
            word.y = -top_min
        c.at((width - c.width) / 2, top_max - top_min + 7)
        return [a, b, c]
    if kind == "dashboard_hero":
        a = Word("spotify", "spotify", 15, .015)
        b = Word("readme", "readme", 19, -.02)
        c = Word("dashboard", "dashboard", 49, -.04).at(0, 0)
        side_width = max(a.width, b.width)
        side_height = a.height + 6 + b.height
        top = (c.height - side_height) / 2
        a.at(side_width - a.width, top)
        b.at(side_width - b.width, top + a.height + 6)
        c.at(side_width + 17, 0)
        return [a, b, c]
    if kind == "staircase":
        a = Word("spotify", "spotify", 25, -.02).at(0, 0)
        b = Word("readme", "readme", 25, .015).at(22, a.height + 5)
        c = Word("dashboard", "dashboard", 25, -.025).at(44, a.height + b.height + 10)
        return [a, b, c]
    if kind == "spotify_above":
        a = Word("spotify", "spotify", 48, -.04).at(0, 0)
        b = Word("readme", "readme", 17, .035)
        c = Word("dashboard", "dashboard", 17, .035)
        line_width = row([b, c], 12)
        line_top = min(w.bounds[1] for w in (b, c))
        width = max(a.width, line_width)
        a.at((width - a.width) / 2, 0)
        for w in (b, c):
            w.x += (width - line_width) / 2
            w.y = a.height + 8 - line_top
        return [a, b, c]
    if kind == "readme_caps_inline":
        words = [Word("spotify", "spotify", 23, -.01),
                 Word("readme", "README", 48, -.035),
                 Word("dashboard", "dashboard", 23, -.01)]
        row(words, 15)
        return words
    if kind == "readme_caps_above":
        a = Word("readme", "README", 46, .055).at(0, 0)
        b = Word("spotify", "spotify", 18, .015).at(0, a.height + 8)
        c = Word("dashboard", "dashboard", 18, .015)
        c.at(a.width - c.width, a.height + 8)
        return [a, b, c]
    if kind == "equal_width_stack":
        words = [Word(k, k.upper(), 24, .17) for k in ("spotify", "readme", "dashboard")]
        width = max(w.width for w in words)
        words = [Word(w.key, w.text, w.size * width / w.width, w.tracking) for w in words]
        top = 0
        for w in words:
            w.at(0, top)
            top += w.height + 5
        return words
    if kind == "offset_lines":
        a = Word("spotify", "spotify", 40, -.035).at(0, 0)
        b = Word("readme", "readme", 40, -.035).at(a.width * .60, a.height + 2)
        c = Word("dashboard", "dashboard", 15, .015)
        c.at(b.x + b.bounds[2] + 11, b.y + b.bounds[3] - c.height)
        return [a, b, c]
    if kind == "repository_name":
        a = Word("spotify", "spotify/", 19, .025).at(0, 0)
        b = Word("readme", "readme", 37, -.035)
        dash = Word("spotify", "-", 37, -.035)
        c = Word("dashboard", "dashboard", 37, -.035)
        row([b, dash, c], 3)
        line_top = min(w.bounds[1] for w in (b, dash, c))
        for w in (b, dash, c):
            w.y = a.height + 7 - line_top
        return [a, b, dash, c]
    if kind == "vertical_spine":
        b = Word("readme", "readme", 31, -.035).at(0, 0)
        c = Word("dashboard", "dashboard", 31, -.035).at(0, b.height + 7)
        total_height = b.height + 7 + c.height
        a = Word("spotify", "spotify", 17, .025, angle=-90)
        a = Word("spotify", "spotify", a.size * total_height / a.height, .025, angle=-90).at(0, 0)
        b.at(a.width + 10, 0)
        c.at(a.width + 10, b.height + 7)
        return [a, b, c]
    if kind == "fraction":
        a = Word("spotify", "spotify", 29, -.02)
        b = Word("readme", "readme", 29, -.02)
        width = max(a.width, b.width) + 12
        a.at((width - a.width) / 2, 0)
        rule_y = a.height + 5
        rule = Rule("rule", width, 1.8, 0, rule_y)
        b.at((width - b.width) / 2, rule_y + 6.8)
        height = b.y + b.bounds[3]
        c = Word("dashboard", "dashboard", 39, -.035)
        c.at(width + 17, (height - c.height) / 2)
        return [a, rule, b, c]
    if kind == "word_modules":
        chunks = [("spotify", "spot", "ify"), ("readme", "read", "me"),
                  ("dashboard", "dash", "board")]
        pairs = [(Word(k, top, 31, -.035), Word(k, bottom, 31, -.035)) for k, top, bottom in chunks]
        top_height = max(top.height for top, bottom in pairs)
        cursor, words = 0, []
        for top, bottom in pairs:
            top.at(cursor, 0)
            bottom.at(cursor, top_height + 7)
            cursor += max(top.width, bottom.width) + 20
            words.extend([top, bottom])
        return words
    if kind == "orbital":
        main = Word("readme", "readme", 31, -.04)
        main.at(-main.width / 2, 0)
        top = arc_word("spotify", "spotify", 13, 52, -13)
        bottom = arc_word("dashboard", "dashboard", 13, 68, main.height + 13, bottom=True)
        return top + [main] + bottom
    if kind == "initials":
        cursor, words = 0, []
        for key, initial, tail in [("spotify", "S", "potify"), ("readme", "R", "eadme"), ("dashboard", "D", "ashboard")]:
            cap = Word(key, initial, 55, -.03)
            rest = Word("spotify" if key == "spotify" else "detail", tail, 19, -.015)
            cap.x = cursor - cap.bounds[0]
            rest.x = cursor + cap.width + 1.5 - rest.bounds[0]
            cursor = rest.x + rest.bounds[2] + 17
            words.extend([cap, rest])
        return words
    if kind == "inside_dashboard":
        left = Word("dashboard", "dash", 48, -.04).at(0, 0)
        right = Word("dashboard", "board", 48, -.04)
        a = Word("spotify", "spotify", 17, .015)
        b = Word("readme", "readme", 17, .015)
        height = max(left.height, right.height)
        inset_width = max(a.width, b.width)
        inset_height = a.height + b.height + 5
        top = (height - inset_height) / 2
        a.at(left.width + 13 + (inset_width - a.width) / 2, top)
        b.at(left.width + 13 + (inset_width - b.width) / 2, top + a.height + 5)
        right.at(left.width + inset_width + 26, 0)
        return [left, a, b, right]
    raise ValueError(kind)


def geometry(words):
    left = min(w.x + w.bounds[0] for w in words)
    top = min(w.y + w.bounds[1] for w in words)
    right = max(w.x + w.bounds[2] for w in words)
    bottom = max(w.y + w.bounds[3] for w in words)
    scale = CONFIG["height"] / (bottom - top)
    return (right - left) * scale, left, top, scale


def logo_groups(words, colors, editable=False):
    width, left, top, scale = geometry(words)
    output = [f'<g transform="scale({num(scale)}) translate({num(-left)} {num(-top)})">']
    for w in words:
        attrs = f'fill="{colors[w.key]}" transform="translate({num(w.x)} {num(w.y)})"'
        if editable and isinstance(w, Word):
            attrs = attrs.replace(f'translate({num(w.x)} {num(w.y)})',
                                  f'translate({num(w.x)} {num(w.y)}) rotate({num(w.angle)})')
            output.append(f'<text {attrs} font-family="Geologica" font-size="{w.size}" '
                          f'font-weight="600" letter-spacing="{num(w.tracking * w.size)}" '
                          f'style="font-variant-ligatures:none">{escape(w.text)}</text>')
        else:
            output.append(f'<path aria-label="{escape(w.text)}" {attrs} d="{w.path}"/>')
    output.append("</g>")
    return "\n".join(output)


def svg(content, width, height, title, font_style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(width)}" height="{num(height)}" '
            f'viewBox="0 0 {num(width)} {num(height)}" role="img" aria-label="{escape(title)}">\n'
            f'<title>{escape(title)}</title>\n{font_style}{content}\n</svg>\n')


def board_text(text, x, y, size, color, tracking=0):
    word = Word("label", text, size, tracking).at(x, y)
    return f'<path fill="{color}" transform="translate({num(word.x)} {num(word.y)})" d="{word.path}"/>'


def main():
    output = ROOT / "exports"
    editable_dir = ROOT / "editable"
    output.mkdir(exist_ok=True)
    editable_dir.mkdir(exist_ok=True)
    variants = CONFIG["variants"]
    selection_path = ROOT / "selected.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8")) if selection_path.exists() else None
    layouts = {v["id"]: layout(v["layout"]) for v in variants}
    dimensions = []
    for variant in variants:
        words = layouts[variant["id"]]
        width, *_ = geometry(words)
        dimensions.append({"id": variant["id"], "width": round(width, 5), "height": 48})
        for theme in CONFIG["themes"]:
            title = f'Spotify README Dashboard / {variant["id"]} / {theme}'
            filename = f'{variant["id"]}-{theme}.svg'
            content = logo_groups(words, variant["colors"][theme])
            (output / filename).write_text(svg(content, width, 48, title), encoding="utf-8")
            if selection and variant["id"] == selection["variant"]:
                # Integer canvas dimensions allow width-only README markup to retain
                # an exact 48 px height and shrink proportionally on narrow screens.
                selected_width, selected_height = selection["width"], selection["height"]
                if selected_width < width or selected_height != CONFIG["height"]:
                    raise ValueError("Selected logo canvas must contain the unscaled artwork")
                selected_content = f'<g transform="translate({num((selected_width - width) / 2)} 0)">{content}</g>'
                selected_dir = ROOT / selection["output_directory"]
                selected_dir.mkdir(parents=True, exist_ok=True)
                (selected_dir / f'{selection["basename"]}-{theme}.svg').write_text(
                    svg(selected_content, selected_width, selected_height, "Spotify README Dashboard"), encoding="utf-8")
            style = '<style>@font-face{font-family:Geologica;src:url("../fonts/Geologica-variable.ttf");font-weight:100 900}</style>\n'
            content = logo_groups(words, variant["colors"][theme], editable=True)
            (editable_dir / filename).write_text(svg(content, width, 48, title, style), encoding="utf-8")

    # Every logo is embedded at 1:1 CSS size, with no per-variant scale factor.
    column = max(710, math.ceil(max(d["width"] for d in dimensions) + 96))
    header = 148
    row_height = CONFIG.get("row_height", 132)
    height = header + len(variants) * row_height + 52
    parts = []
    for theme_index, (theme, background) in enumerate(CONFIG["themes"].items()):
        offset = theme_index * column
        is_dark = theme == "dark"
        ink = "#E6EDF3" if is_dark else "#1F2328"
        muted = "#9DA7B3" if is_dark else "#59636F"
        rule = "#2B313B" if is_dark else "#DFE3E8"
        parts.append(f'<rect x="{offset}" width="{column}" height="{height}" fill="{background}"/>')
        parts.append(board_text(CONFIG.get("board_label", "SPOTIFY / README / DASHBOARD"), offset + 32, 30, 13, muted, .05))
        parts.append(board_text("Светлая тема" if not is_dark else "Тёмная тема", offset + 32, 64, 29, ink, -.025))
        parts.append(board_text(CONFIG.get("board_subtitle", "Geologica 600 · каждый логотип высотой 48 px"), offset + 32, 111, 12, muted))
        for index, variant in enumerate(variants):
            y = header + index * row_height
            parts.append(f'<path d="M{offset + 32} {y}H{offset + column - 32}" stroke="{rule}"/>')
            parts.append(board_text(f'{variant.get("display_id", variant["id"])}  {variant["name"]}', offset + 32, y + 14, 12, ink))
            words = layouts[variant["id"]]
            width, *_ = geometry(words)
            x = offset + (column - width) / 2
            logo_top = 35 if row_height == 112 else 41
            parts.append(f'<g transform="translate({num(x)} {y + logo_top})">{logo_groups(words, variant["colors"][theme])}</g>')
            parts.append(board_text(variant["note"], offset + 32, y + row_height - 20, 10.5, muted))
        parts.append(board_text("Прозрачные SVG · масштаб 1:1 · одинаковая высота, разная ширина", offset + 32, height - 25, 10, muted))
    parts.append(f'<path d="M{column} 0V{height}" stroke="#626B75" stroke-opacity=".22"/>')
    board = svg("\n".join(parts), column * 2, height,
        "Варианты логотипа: слева светлая тема, справа тёмная; высота каждого 48 px")
    (ROOT / f"comparison{SUFFIX}.svg").write_text(board, encoding="utf-8")
    if ARGS.set == "all":
        page = '''<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spotify README Dashboard — все варианты логотипа</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#eaedf1;color:#202630;font:14px system-ui,sans-serif}
header{position:sticky;top:0;z-index:1;display:flex;gap:16px;flex-wrap:wrap;align-items:center;padding:14px 24px;background:#f8fafc;border-bottom:1px solid #cbd1d9}
header strong{margin-right:auto}button{font:inherit;cursor:pointer;padding:6px 12px;border:1px solid #aeb8c5;border-radius:6px;background:#fff;color:#202630}button:hover{background:#e5edfa}button:focus-visible{outline:3px solid #2768d5;outline-offset:2px}
main{overflow:auto}#sheet{margin:auto;line-height:0}#sheet svg{display:block;width:100%;height:auto}
output{min-width:4ch}header span{color:#566273}
</style>
<header><strong>24 варианта · Spotify #1ED760</strong><span>Высота логотипов при 100%: 48 px</span>
<button id="actual" type="button">Масштаб 100%</button><button id="fit" type="button">По ширине окна</button><output id="zoom" aria-live="polite">100%</output></header>
<main><div id="sheet">BOARD</div></main>
<script>
const width=BOARD_WIDTH;
const sheet=document.getElementById('sheet');
let fitted=false;
function resize(){const size=fitted?Math.min(width,document.documentElement.clientWidth):width;sheet.style.width=size+'px';document.getElementById('zoom').value=Math.round(size/width*100)+'%'}
document.getElementById('actual').onclick=()=>{fitted=false;resize()};
document.getElementById('fit').onclick=()=>{fitted=true;resize()};
window.addEventListener('resize',resize);resize();
</script></html>'''.replace("BOARD_WIDTH", str(column * 2)).replace("BOARD", board)
        (ROOT / "comparison-all.html").write_text(page, encoding="utf-8")
    (ROOT / f"dimensions{SUFFIX}.json").write_text(json.dumps(dimensions, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"comparison": [column * 2, height], "logos": dimensions}, indent=2))


if __name__ == "__main__":
    main()
