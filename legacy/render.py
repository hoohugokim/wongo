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
Fonts: both targets use Cambria (Cambria Math is the MS Word default for math).
Partial-state note: if the SI render fails after the main render already
succeeded, output/main-<target>.docx from this run remains on disk — rerun
after fixing the SI source; the main render is not repeated for you.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import re

import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

import mslib
import validate

# Uplift (HANDOFF step 1): the unconditional OOXML correctness fixes now live
# in wongo.docxpatch; legacy/render.py keeps only orchestration + house look.
# Flipping these imports means every render through this script exercises the
# migrated code, which is what tools/bytecompare.py verifies against baseline.
from wongo.docxpatch import (
    STYLES_TO_FONT,
    _SECT_PR_TAIL,
    _style_by_name,
    _tbl_rescale_grid,
    _tbl_set_borders,
    _tbl_set_width_pct,
    add_line_numbers,
    add_page_numbers,
    dedupe_ppr,
    normalize_ppr_order,
    patch_theme_fonts,
    restart_page_numbering,
    set_fonts,
)

FONTS = {"collab": "Cambria", "submission": "Cambria"}


def set_line_spacing(doc: Document, factor: float) -> None:
    doc.styles["Normal"].paragraph_format.line_spacing = factor


# ---------------------------------------------------------------------------
# HOUSE STYLE (lab preference, venue-neutral). Makes every DOCX product carry
# the page shape, line numbering, double spacing, title-page block and caption
# look of the group's prior Water Research / WR X submissions (see
# manuscript/prev-ref/ in the the reference manuscript project), so coauthors meet a familiar
# page and don't reject the Quarto workflow on looks. Fonts stay whatever
# FONTS says (currently Cambria). Nothing here contradicts verified ES&T
# guidance: line numbers are optional there, spacing is unspecified, and
# "Abstract and Keywords" is an ACS heading. Applied to BOTH targets.
HOUSE_PAGE = {"w": 210, "h": 297, "left": 25, "right": 25, "top": 30, "bottom": 25}
HOUSE_DOUBLE = ("Normal", "Body Text", "First Paragraph", "Abstract")
HOUSE_SINGLE = (  # explicit shield against inheriting Normal's 2.0
    "Compact", "Caption", "Image Caption", "Table Caption", "Footnote Text",
    "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Title", "Author", "Date",
)
HOUSE_JUSTIFY = ("Body Text", "First Paragraph", "Abstract", "Bibliography",
                 "Caption", "Image Caption", "Table Caption",
                 "Heading 1", "Heading 2", "Heading 3", "Heading 4")
HOUSE_HEADING_PT = {"Heading 1": 16, "Heading 2": 13, "Heading 3": 12, "Heading 4": 12}
HOUSE_TITLE_PT = 14


def read_front_matter(project: Path, qmd: str = "index.qmd") -> dict:
    """Parse the leading YAML block of a .qmd (pandoc drops author
    affiliations from the docx entirely, so the title-page rebuild needs the
    source metadata)."""
    lines = (project / qmd).read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i, ln in enumerate(lines[1:], start=1) if ln.strip() == "---")
    except StopIteration:
        return {}
    return yaml.safe_load("\n".join(lines[1:end])) or {}


def apply_page_geometry(doc: Document) -> None:
    for s in doc.sections:
        s.page_width, s.page_height = Mm(HOUSE_PAGE["w"]), Mm(HOUSE_PAGE["h"])
        s.left_margin, s.right_margin = Mm(HOUSE_PAGE["left"]), Mm(HOUSE_PAGE["right"])
        s.top_margin, s.bottom_margin = Mm(HOUSE_PAGE["top"]), Mm(HOUSE_PAGE["bottom"])


def apply_house_spacing_and_alignment(doc: Document) -> None:
    for name in HOUSE_DOUBLE:
        st = _style_by_name(doc, name)
        if st is not None:
            st.paragraph_format.line_spacing = 2.0
    for name in HOUSE_SINGLE:
        st = _style_by_name(doc, name)
        if st is not None:
            st.paragraph_format.line_spacing = 1.0
    for name in HOUSE_JUSTIFY:
        st = _style_by_name(doc, name)
        if st is not None:
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def apply_heading_look(doc: Document) -> None:
    for name, pt in HOUSE_HEADING_PT.items():
        st = _style_by_name(doc, name)
        if st is None:
            continue
        st.font.size = Pt(pt)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)


def restyle_title(doc: Document) -> None:
    for p in doc.paragraphs:
        if p.style.name == "Title":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(HOUSE_TITLE_PT)
            return


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) < 2:
        return name
    return " ".join(f"{p[0]}." for p in parts[:-1]) + " " + parts[-1]


def _compose_affiliation(aff: dict) -> str:
    return ", ".join(
        str(aff[k]) for k in ("name", "address", "country") if aff.get(k)
    )


def rebuild_title_block(doc: Document, meta: dict) -> None:
    """Replace pandoc's one-name-per-line Author paragraphs with the WR-style
    block: one author line with superscript affiliation letters (* marks the
    corresponding author), lettered affiliation lines, then the corresponding
    author's e-mail. All metadata comes from the .qmd YAML."""
    authors = meta.get("author") or []
    if not isinstance(authors, list) or not authors or not isinstance(authors[0], dict):
        return
    paras = doc.paragraphs
    idx = [i for i, p in enumerate(paras) if p.style.name == "Author"]
    if not idx:
        return
    aff_order: list[str] = []
    for a in authors:
        for aff in a.get("affiliations") or []:
            s = _compose_affiliation(aff)
            if s and s not in aff_order:
                aff_order.append(s)
    letters = {s: chr(ord("a") + i) for i, s in enumerate(aff_order)}

    first = paras[idx[0]]
    for r in list(first.runs):
        r._r.getparent().remove(r._r)
    first.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for k, a in enumerate(authors):
        first.add_run(a.get("name", ""))
        sup = ",".join(letters[_compose_affiliation(x)] for x in a.get("affiliations") or [])
        if a.get("corresponding"):
            sup = f"{sup},*" if sup else "*"
        if sup:
            first.add_run(" ")
            sr = first.add_run(sup)
            sr.font.superscript = True
        if k < len(authors) - 1:
            first.add_run(", ")

    anchor = paras[idx[-1] + 1]
    for i in idx[1:]:
        paras[i]._p.getparent().remove(paras[i]._p)

    author_style = first.style
    first.insert_paragraph_before("", style=author_style)  # blank line after the title
    for s in aff_order:
        p = anchor.insert_paragraph_before("", style=author_style)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sr = p.add_run(letters[s])
        sr.font.superscript = True
        p.add_run(" " + s)
    corr = [a for a in authors if a.get("corresponding")] or [
        a for a in authors if a.get("email")
    ]
    if corr:
        label = "* Corresponding author" + ("s" if len(corr) > 1 else "") + ":"
        p = anchor.insert_paragraph_before(label, style=author_style)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        emails = ", ".join(
            f"{a['email']} ({_initials(a.get('name', ''))})" for a in corr if a.get("email")
        )
        p = anchor.insert_paragraph_before("E-mail: " + emails, style=author_style)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    anchor.insert_paragraph_before("", style=author_style)  # blank line before the Abstract


def restyle_abstract_heading(doc: Document) -> None:
    for p in doc.paragraphs:
        if p.style.name == "Abstract Title":
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(12)
            return


def inject_keywords(doc: Document, meta: dict) -> None:
    kws = meta.get("keywords")
    if not kws:
        return
    text = "Keywords: " + (", ".join(map(str, kws)) if isinstance(kws, list) else str(kws))
    abstract_idx = [i for i, p in enumerate(doc.paragraphs) if p.style.name == "Abstract"]
    if not abstract_idx:
        return
    anchor = doc.paragraphs[abstract_idx[-1] + 1]
    style = _style_by_name(doc, "Body Text") or doc.paragraphs[abstract_idx[-1]].style
    p = anchor.insert_paragraph_before(text, style=style)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


# Quarto (1.10.x) wraps every crossref float (figure or kable table) in a 1x1
# outer table; the caption lands INSIDE that cell as a paragraph styled plain
# "Normal" with an NBSP between the word and the number ("Figure\xa01: ...").
# Body-level "Image Caption"/"Table Caption" styles only appear on unlabeled
# floats. Both shapes are handled below. See quarto-docx-quirks.md.
_CAPTION_LEAD = re.compile(r"^((?:Figure|Table)[\s ]+S?[\s ]?\d+)([.:])[\s ]*(.*)$", re.S)
_CAPTION_LEAD_LOOSE = re.compile(r"^((?:Figure|Table)[\s ]+S?[\s ]?\d+)[.:]?[\s ]*(.*)$", re.S)


def _restyle_caption(p, lead: str, rest: str) -> None:
    # NBSPs -> spaces, then close the gap crossref leaves inside "S 1"
    lead = re.sub(r"S\s+(\d)", r"S\1", lead.replace(" ", " ")) + "."
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    br = p.add_run(lead)
    br.font.bold = True
    if rest:
        p.add_run(" " + rest)
    p.paragraph_format.line_spacing = 1.0
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def bold_caption_leads(doc: Document) -> None:
    """WR-family caption look: bold 'Figure 1.' / 'Table S2.' lead, period
    delimiter regardless of what crossref emitted, single-spaced."""
    # body-level caption-styled paragraphs (unlabeled floats)
    for p in doc.paragraphs:
        if p.style.name in ("Caption", "Image Caption", "Table Caption"):
            m = _CAPTION_LEAD_LOOSE.match(p.text)
            if m:
                _restyle_caption(p, m.group(1), m.group(2))
    # captions inside crossref wrapper-table cells: require the [.:] delimiter
    # so prose like "Table 1 shows..." inside a real data cell never matches
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    m = _CAPTION_LEAD.match(p.text)
                    if m:
                        _restyle_caption(p, m.group(1), m.group(3))


def _bold_cells(cells) -> None:
    for cell in cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True


def fix_tables(doc: Document) -> None:
    """WR/booktabs table look. Quarto wraps every crossref float in a 1x1
    outer table; real data tables live nested inside those cells (or stand
    alone in the SI). Wrappers: borderless, rescaled to the full text column.
    Data tables: full width, closed 1pt top and bottom rules (the style's
    header midrule stays), no vertical/inner rules, bold header row and bold
    first (label) column."""
    sec = doc.sections[0]
    text_w = (int(sec.page_width) - int(sec.left_margin) - int(sec.right_margin)) // 635

    def walk(tables, width_dxa):
        for t in tables:
            is_wrapper = len(t.rows) == 1 and len(t.columns) == 1
            _tbl_set_width_pct(t)
            _tbl_rescale_grid(t, width_dxa)
            if is_wrapper:
                _tbl_set_borders(t, top=None, bottom=None)
                for row in t.rows:
                    for cell in row.cells:
                        walk(cell.tables, width_dxa - 216)  # minus cell margins
            else:
                _tbl_set_borders(t, top=8, bottom=8)
                _bold_cells(t.rows[0].cells)
                _bold_cells(row.cells[0] for row in t.rows)
    walk(doc.tables, text_w)


# ---------------------------------------------------------------------------
# HOUSE STYLE (cont.) — paragraph-property correctness passes live in
# wongo.docxpatch (dedupe_ppr, normalize_ppr_order); apply_house_style below
# composes them with the house look.


def apply_house_style(doc: Document, meta: dict | None = None) -> None:
    dedupe_ppr(doc)
    apply_page_geometry(doc)
    add_line_numbers(doc)
    apply_house_spacing_and_alignment(doc)
    apply_heading_look(doc)
    restyle_title(doc)
    if meta:
        rebuild_title_block(doc, meta)
        inject_keywords(doc, meta)
    restyle_abstract_heading(doc)
    bold_caption_leads(doc)
    fix_tables(doc)
    normalize_ppr_order(doc)


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
    set_fonts(doc, FONTS[target])
    apply_house_style(doc, read_front_matter(project, "index.qmd"))
    add_page_numbers(doc)
    doc.save(str(path))
    patch_theme_fonts(path, FONTS[target], track_changes=(target == "collab"))


def postprocess_si(path: Path, profile: dict, cfg: dict, target: str) -> None:
    doc = Document(str(path))
    si = profile.get("si") or {}
    set_fonts(doc, FONTS[target])
    apply_house_style(doc)  # no meta: SI keeps its plain author line, no keywords
    counts = {
        "figures": len(doc.inline_shapes),
        "tables": len(doc.tables),
    }
    if si.get("needs_cover_sheet"):
        prepend_si_cover(doc, cfg, profile, counts)
    add_page_numbers(doc, prefix=si.get("page_prefix", "S"))
    restart_page_numbering(doc, start=1)
    doc.save(str(path))
    patch_theme_fonts(path, FONTS[target], track_changes=(target == "collab"))


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
