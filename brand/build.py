# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools==4.66.1", "brotli==1.2.0", "uharfbuzz==0.56.2"]
# ///
"""Rebuild Wongo's outlined SVG logos, CSS tokens and PNG exports from local fonts.

Run `uv run brand/build.py` from the repository root. PNG export also requires
the `rsvg-convert` executable (librsvg). Font sources are already bundled;
this script never downloads fonts or changes the manuscript engine. The first
uv run may fetch Python dependencies; cached dependencies permit offline use.
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent
TOKENS = json.loads((ROOT / "tokens.json").read_text(encoding="utf-8"))
COLORS = TOKENS["color"]


def n(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def lettering(filename: str, text: str, axes: dict[str, float]):
    """Shape live font data, preserving kerning, then turn every glyph into paths."""
    font = TTFont(ROOT / "fonts" / filename, recalcTimestamp=False)
    font = instantiateVariableFont(font, axes, inplace=False)
    font.flavor = None
    binary = io.BytesIO()
    font.save(binary)
    face = hb.Face(binary.getvalue())
    shaped_font = hb.Font(face)
    shaped_font.scale = (face.upem, face.upem)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(shaped_font, buffer, {"kern": True})
    glyphs = font.getGlyphSet()
    order = font.getGlyphOrder()
    svg = SVGPathPen(glyphs, ntos=n)
    bounds = BoundsPen(glyphs)
    x = y = 0
    for glyph, position in zip(buffer.glyph_infos, buffer.glyph_positions, strict=True):
        transform = (1, 0, 0, 1, x + position.x_offset, y + position.y_offset)
        glyphs[order[glyph.codepoint]].draw(TransformPen(svg, transform))
        glyphs[order[glyph.codepoint]].draw(TransformPen(bounds, transform))
        x += position.x_advance
        y += position.y_advance
    if bounds.bounds is None:
        raise ValueError(f"No visible glyphs for {text!r}")
    return svg.getCommands(), bounds.bounds, font["OS/2"].sxHeight


def emblem(fill: str | None = None) -> str:
    return "\n".join(
        f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["width"]}" '
        f'height="{r["height"]}" fill="{fill or COLORS[r["color"]]}"/>'
        for r in TOKENS["emblem"]["rectangles"]
    )


def path_at(data: str, bounds, x: float, baseline: float, scale: float, color: str):
    return (
        f'<path fill="{color}" transform="translate({n(x - bounds[0] * scale)} '
        f'{n(baseline)}) scale({n(scale)} {n(-scale)})" d="{data}"/>'
    )


def svg_document(body: str, width: float, height: float, title: str,
                 pad: float | None = None, description: str | None = None):
    if pad is None:
        pad = TOKENS["emblem"]["clear_space"]
    if description is None:
        description = ("Wongo: an abstract two-column manuscript, with a header, annotation "
                       "square, text bars, figure panel and captions. Identity v1.0.0.")
    width, height = width + 2 * pad, height + 2 * pad
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(width)} {n(height)}" '
        f'width="{n(width)}" height="{n(height)}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">{title}</title>\n'
        f'<desc id="desc">{description}</desc>\n'
        f'<g transform="translate({n(pad)} {n(pad)})">\n{body}\n</g>\n</svg>\n'
    )


def make_logos():
    destination = ROOT / "logos"
    destination.mkdir(exist_ok=True)
    type_spec = TOKENS["typography"]["wordmark"]
    layout = TOKENS["lockup"]
    word, wb, x_height = lettering("SourceSerif4-Roman.woff2", "wongo", {
        "wght": type_spec["weight"], "opsz": type_spec["optical_size"],
    })
    korean, kb, _ = lettering("NotoSansKR-Roman.woff2", "원고", {"wght": 400})
    scale = type_spec["x_height"] / x_height
    korean_scale = layout["korean_height"] / (kb[3] - kb[1])
    word_width = (wb[2] - wb[0]) * scale
    word_x = TOKENS["emblem"]["width"] + layout["wordmark_gap"]
    baseline = layout["wordmark_baseline"]
    korean_x = word_x + word_width + layout["korean_gap"]
    # Align the visible Korean bottom with the Latin baseline, not a font metric.
    korean_baseline = baseline + kb[1] * korean_scale
    total_height = max(TOKENS["emblem"]["height"], baseline - wb[1] * scale)
    for suffix, override in [("", None), ("-mono", "#000000"), ("-reverse", COLORS["paper"])]:
        ink = override or COLORS["ink"]
        icon = emblem(override)
        word_path = path_at(word, wb, word_x, baseline, scale, ink)
        korean_path = path_at(korean, kb, korean_x, korean_baseline, korean_scale, ink)
        artwork = {
            "wongo-icon": (icon, TOKENS["emblem"]["width"], TOKENS["emblem"]["height"],
                           "Wongo manuscript-grid emblem"),
            "wongo-lockup-en": (icon + word_path, word_x + word_width, total_height, "wongo"),
            "wongo-lockup": (icon + word_path + korean_path,
                             korean_x + (kb[2] - kb[0]) * korean_scale,
                             total_height, "wongo · 원고"),
            "wongo-wordmark": (path_at(word, wb, 0, wb[3] * scale, scale, ink),
                               word_width, (wb[3] - wb[1]) * scale, "wongo"),
        }
        for name, (body, width, height, title) in artwork.items():
            description = ("Wongo lowercase serif wordmark. Identity v1.0.0."
                           if name == "wongo-wordmark" else None)
            (destination / f"{name}{suffix}.svg").write_text(
                svg_document(body, width, height, title, description=description), encoding="utf-8"
            )
    # Square canvas for browser/app icons. This is the full emblem, not a redesign.
    square = 256
    offset_x = (square - TOKENS["emblem"]["width"]) / 2
    offset_y = (square - TOKENS["emblem"]["height"]) / 2
    icon_body = f'<g transform="translate({n(offset_x)} {n(offset_y)})">' + emblem() + '</g>'
    (destination / "wongo-icon-square.svg").write_text(
        svg_document(icon_body, square, square, "Wongo manuscript-grid emblem", pad=0),
        encoding="utf-8",
    )


def make_css():
    faces = [
        ("Source Serif 4", "SourceSerif4-Roman", "200 900", "normal"),
        ("Source Serif 4", "SourceSerif4-Italic", "200 900", "italic"),
        ("Source Sans 3", "SourceSans3-Roman", "200 900", "normal"),
        ("Source Sans 3", "SourceSans3-Italic", "200 900", "italic"),
        ("Noto Sans KR", "NotoSansKR-Roman", "100 900", "normal"),
        ("Source Code Pro", "SourceCodePro-Roman", "200 900", "normal"),
    ]
    css = ["/* Generated by brand/build.py from tokens.json. */"]
    for family, filename, weight, style in faces:
        css.append(f'@font-face {{ font-family: "{family}"; src: url("fonts/{filename}.woff2") '
                   f'format("woff2"); font-weight: {weight}; font-style: {style}; font-display: swap; }}')
    css.append(":root {")
    css.extend(f"  --wongo-{key}: {value};" for key, value in COLORS.items())
    for key, value in TOKENS["typography"].items():
        if key in {"serif", "sans", "mono"}:
            fallback = "monospace" if key == "mono" else ("serif" if key == "serif" else "sans-serif")
            css.append(f'  --wongo-font-{key}: "{value}", "Noto Sans KR", {fallback};')
    css.extend(f"  --wongo-space-{size}: {size}px;" for size in TOKENS["spacing"]["scale"])
    css.extend([
        f'  --wongo-radius: {TOKENS["shape"]["radius"]};',
        f'  --wongo-rule-width: {TOKENS["shape"]["rule_width_px"]}px;',
        f'  --wongo-body-size: {TOKENS["typography"]["body_size_px"]}px;',
        f'  --wongo-body-leading: {TOKENS["typography"]["body_line_height"]};',
        f'  --wongo-heading-weight: {TOKENS["typography"]["heading_weight"]};',
        f'  --wongo-heading-leading: {TOKENS["typography"]["heading_line_height"]};',
        f'  --wongo-text-max: {TOKENS["layout"]["text_max_ch"]}ch;',
        f'  --wongo-page-max: {TOKENS["layout"]["page_max_px"]}px;',
        f'  --wongo-gutter: {TOKENS["layout"]["gutter_px"]}px;',
        "}",
    ])
    css.append((ROOT / "components.css").read_text(encoding="utf-8"))
    (ROOT / "wongo.css").write_text("\n".join(css) + "\n", encoding="utf-8")


def export_pngs():
    converter = shutil.which("rsvg-convert")
    if converter is None:
        raise RuntimeError("PNG export requires librsvg (rsvg-convert); install it or use --svg-only.")
    for source in sorted((ROOT / "logos").glob("*.svg")):
        width = 512 if "icon" in source.stem else 1600
        subprocess.run([converter, "-w", str(width), "-o", str(source.with_suffix(".png")), str(source)], check=True)
    destination = ROOT / "exports"
    destination.mkdir(exist_ok=True)
    for size in [16, 32, 48, 180, 192, 512]:
        subprocess.run([converter, "-w", str(size), "-o", str(destination / f"wongo-icon-{size}.png"),
                        str(ROOT / "logos/wongo-icon-square.svg")], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg-only", action="store_true", help="Skip PNG export (no librsvg needed).")
    args = parser.parse_args()
    make_logos()
    make_css()
    if not args.svg_only:
        export_pngs()
    print(f"Wongo identity {TOKENS['version']} rebuilt in {ROOT}")


if __name__ == "__main__":
    main()
