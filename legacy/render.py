#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6", "python-docx>=1.1"]
# ///
"""Render a Quarto manuscript to collaboration- or submission-grade DOCX.

Usage: render.py --target {collab|submission} [--project DIR]

Pipeline: validate gate (submission refuses on HARD failures) -> quarto render
with the journal profile's reference-doc/CSL -> python-docx post-processing
driven by profile.yml (line numbers, spacing, fonts, page numbers, TOC art) ->
separate SI render with S-page numbering and cover sheet.
Fonts: both targets use Cambria (Cambria Math is the MS Word default for math),
overridable by the active style profile's `font:` key.
Partial-state note: if the SI render fails after the main render already
succeeded, output/main-<target>.docx from this run remains on disk — rerun
after fixing the SI source; the main render is not repeated for you.

Uplift state (HANDOFF steps 1-2): this script is orchestration glue only —
unconditional OOXML correctness lives in wongo.docxpatch, the data-driven
house look in wongo.styles. tools/bytecompare.py pins behavior against the
pre-migration baseline after every change.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm

import mslib
import validate
from wongo import styles as wstyles
from wongo.docxpatch import (
    add_line_numbers,
    add_page_numbers,
    patch_theme_fonts,
    restart_page_numbering,
    set_fonts,
)

FONTS = {"collab": "Cambria", "submission": "Cambria"}


def set_line_spacing(doc: Document, factor: float) -> None:
    doc.styles["Normal"].paragraph_format.line_spacing = factor


def resolve_style(cfg: dict) -> dict:
    """Style-profile resolution: _journal.yml `style:` key -> $WONGO_STYLE ->
    legacy fallback. The final fallback is `kist-wcr`, NOT `default`, purely as
    a transition measure: the reference manuscript must not gain a style key before ms-r0-sent
    (ground rule 2) yet has always rendered with the house look. Once the CLI
    lands (HANDOFF step 5) the chain becomes journal -> --style -> default."""
    name = cfg.get("style") or os.environ.get("WONGO_STYLE") or "kist-wcr"
    return wstyles.load_style(name)


def prepend_si_cover(doc: Document, cfg: dict, profile: dict, counts: dict) -> None:
    first = doc.paragraphs[0]
    lines = [
        "Supporting Information",
        f"Journal: {profile.get('journal', '')} — {cfg.get('ms_type', '')}",
        f"Contents: {counts.get('figures', 0)} figures, {counts.get('tables', 0)} tables",
        "Pages: (fill from final page count in Word — python-docx cannot paginate)",
    ]
    for text in lines:
        p = first.insert_paragraph_before(text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    brk = first.insert_paragraph_before("")
    run = brk.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)


DEFAULT_TOC_ART_LABEL = "For Table of Contents Only"


def insert_toc_art(
    doc: Document,
    image_path: Path,
    width_mm: float | None = None,
    label: str = DEFAULT_TOC_ART_LABEL,
) -> None:
    """Append the TOC/abstract graphic at the END of the document.

    Per the official ACS "Guidelines for Table of Contents/Abstract
    Graphics" (dated 2024-02-28): the graphic is labeled "For Table of
    Contents Only" and placed on the LAST PAGE of the submitted manuscript
    (it may also be uploaded separately as "Graphics for manuscript").
    Produces, in order: a page break, a centered label paragraph, then a
    centered paragraph containing the image.
    """
    brk = doc.add_paragraph()
    run = brk.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)

    label_p = doc.add_paragraph(label)
    label_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    img_p = doc.add_paragraph()
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = img_p.add_run()
    kwargs = {"width": Mm(width_mm)} if width_mm else {}
    run.add_picture(str(image_path), **kwargs)


def quarto_render(project: Path, qmd: str, out_name: str, profile: dict) -> Path:
    cmd = ["quarto", "render", qmd, "--to", "docx", "--output", out_name]
    ref = profile.get("reference_doc")
    if ref:
        cmd += ["-M", f"reference-doc:{Path(profile['_dir']) / ref}"]
    csl = profile.get("csl")
    if csl:
        cmd += ["-M", f"csl:{Path(profile['_dir']) / csl}"]
    try:
        subprocess.run(cmd, cwd=project, check=True)
    except subprocess.CalledProcessError:
        raise SystemExit(f"quarto render failed for {qmd} (see quarto output above)")
    out_dir = project / "output"
    out_dir.mkdir(exist_ok=True)
    produced = project / out_name          # quarto writes next to the input
    target = out_dir / out_name
    if produced.exists() and produced != target:
        shutil.move(str(produced), target)
    if not target.exists():
        raise SystemExit(f"quarto render did not produce {target}")
    return target


def find_toc_art(project: Path) -> Path | None:
    for ext in ("png", "tiff", "tif", "jpg", "jpeg"):
        p = project / "figures" / f"toc-art.{ext}"
        if p.exists():
            return p
    return None


def postprocess_main(path: Path, profile: dict, cfg: dict, target: str, project: Path) -> None:
    doc = Document(str(path))
    if target == "submission":
        if profile.get("line_numbers"):
            add_line_numbers(doc)
        if profile.get("spacing") == "double":
            set_line_spacing(doc, 2.0)
        toc = (profile.get("toc_graphic") or {})
        if toc.get("required"):
            art = find_toc_art(project)
            if art is None:
                # Backstop only: main() gates this BEFORE quarto_render() runs
                # (see item A in quarto-docx-quirks.md / final-review-fixes),
                # so this branch should be unreachable in practice. Message
                # kept aligned with the pre-render gate's extension list.
                raise SystemExit(
                    "Profile requires TOC art but figures/toc-art.{png,tif,tiff,jpg,jpeg} is missing."
                )
            insert_toc_art(doc, art, toc.get("width_mm"), toc.get("label") or DEFAULT_TOC_ART_LABEL)
    style = resolve_style(cfg)
    font = style.get("font") or FONTS[target]
    set_fonts(doc, font)
    wstyles.apply_style(doc, style, wstyles.read_front_matter(project, "index.qmd"))
    add_page_numbers(doc)
    doc.save(str(path))
    patch_theme_fonts(path, font, track_changes=(target == "collab"))


def postprocess_si(path: Path, profile: dict, cfg: dict, target: str) -> None:
    doc = Document(str(path))
    si = profile.get("si") or {}
    style = resolve_style(cfg)
    font = style.get("font") or FONTS[target]
    set_fonts(doc, font)
    # no meta: SI keeps its plain author line, no keywords
    wstyles.apply_style(doc, style)
    counts = {
        "figures": len(doc.inline_shapes),
        "tables": len(doc.tables),
    }
    if si.get("needs_cover_sheet"):
        prepend_si_cover(doc, cfg, profile, counts)
    add_page_numbers(doc, prefix=si.get("page_prefix", "S"))
    restart_page_numbering(doc, start=1)
    doc.save(str(path))
    patch_theme_fonts(path, font, track_changes=(target == "collab"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True, choices=("collab", "submission"))
    ap.add_argument("--project", default=".")
    args = ap.parse_args()
    project = Path(args.project).resolve()

    cfg = mslib.load_journal_config(project)
    profile = mslib.load_profile(cfg["journal"])
    mslib.manuscript_type(profile, cfg["ms_type"])  # fail fast on bad ms_type

    checks = validate.run_checks(project)
    validate.print_report(checks)
    hard = [c for c in checks if c.level == "HARD" and not c.ok]
    if hard and args.target == "submission":
        raise SystemExit("HARD checks failed — submission render refused (fix, or render --target collab).")

    # Gate BEFORE quarto ever runs: postprocess_main's TOC-art check used to
    # be the only enforcement, but it fires after quarto_render() has already
    # written output/main-submission.docx, leaving a half-processed file that
    # looks like a real deliverable when the run actually failed. Refusing
    # here means no docx is produced at all for this failure mode (backstop
    # check kept in postprocess_main in case this function is ever bypassed).
    if args.target == "submission" and (profile.get("toc_graphic") or {}).get("required"):
        if find_toc_art(project) is None:
            raise SystemExit(
                "Profile requires TOC art but figures/toc-art.{png,tif,tiff,jpg,jpeg} "
                "is missing — submission render refused."
            )

    main_docx = quarto_render(project, "index.qmd", f"main-{args.target}.docx", profile)
    postprocess_main(main_docx, profile, cfg, args.target, project)
    print(f"wrote {main_docx}")

    if (project / "si.qmd").exists():
        si_docx = quarto_render(project, "si.qmd", f"si-{args.target}.docx", profile)
        postprocess_si(si_docx, profile, cfg, args.target)
        print(f"wrote {si_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
