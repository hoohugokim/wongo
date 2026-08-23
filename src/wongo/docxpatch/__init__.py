"""wongo.docxpatch — unconditional OOXML correctness fixes.

Migrated verbatim from legacy/render.py per HANDOFF-wongo-uplift.md step 1.
Everything in this module is ENGINE behavior (ground rule 3): it fixes
Quarto 1.10 / pandoc 3.x output pathologies that would otherwise ship a
wrong-looking manuscript. None of it is house taste — the KIST-WCR look
lives in style profiles (wongo.styles). Each fix is pinned by a regression
test in tests/test_docxpatch.py and documented in docs/docx-quirks.md.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# Styles whose font wongo controls directly. pandoc's reference-doc machinery
# leaves several of these resolving through the document theme (see
# patch_theme_fonts), so literal fonts AND theme attributes must both be set.
STYLES_TO_FONT = (
    "Normal", "Title", "Subtitle", "Author", "Date", "Abstract", "Abstract Title",
    "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6",
    "Caption", "Image Caption", "Table Caption", "First Paragraph", "Body Text",
    "Bibliography", "Compact", "Captioned Figure", "Block Text",
)


# CT_SectPr child sequence per ECMA-376: ... lnNumType, pgNumType, then these.
# w:lnNumType's successors are therefore ("w:pgNumType",) + _SECT_PR_TAIL;
# w:pgNumType's are _SECT_PR_TAIL. See docx-quirks for why plain .append()
# corrupts real journal templates.
_SECT_PR_TAIL = (
    "w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
    "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
    "w:printerSettings", "w:sectPrChange",
)


def add_line_numbers(doc: Document) -> None:
    for section in doc.sections:
        sect_pr = section._sectPr
        ln = sect_pr.find(qn("w:lnNumType"))
        if ln is None:
            ln = OxmlElement("w:lnNumType")
            sect_pr.insert_element_before(ln, *(("w:pgNumType",) + _SECT_PR_TAIL))
        ln.set(qn("w:countBy"), "1")
        ln.set(qn("w:restart"), "continuous")


def _style_by_name(doc: Document, style_name: str):
    """Find a style by its exact UI name.

    Deliberately avoids ``doc.styles[style_name]``: python-docx's dict-style
    lookup applies a "BabelFish" UI<->internal name translation (e.g.
    "Caption" -> "caption") before matching by name, and only falls back to a
    *deprecated* style-id match if that fails. Quarto/pandoc's default
    reference.docx stores the built-in Caption style's internal XML name as
    "Caption" (capitalized) rather than Word's own "caption" (lowercase), so
    the translated lookup misses and every call silently takes the
    deprecated path, emitting a UserWarning today and liable to raise
    KeyError once python-docx removes that fallback. Iterating styles and
    comparing `.name` directly sidesteps the translation entirely.
    """
    for style in doc.styles:
        if style.name == style_name:
            return style
    return None


def set_fonts(doc: Document, name: str) -> None:
    for style_name in STYLES_TO_FONT:
        style = _style_by_name(doc, style_name)
        if style is None:
            continue
        style.font.name = name
        rfonts = style.element.get_or_add_rPr().get_or_add_rFonts()
        rfonts.set(qn("w:eastAsia"), name)
        rfonts.set(qn("w:cs"), name)
        # OOXML precedence trap: a w:asciiTheme/w:hAnsiTheme attribute BEATS the
        # literal w:ascii/w:hAnsi on the same rFonts, so pandoc's theme-linked
        # heading styles keep rendering in the document theme's font (Aptos in
        # current Word) no matter what font.name is set to. Strip the theme
        # attributes so the literal font wins. See docx-quirks.
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]


def _rewrite_package(path: Path, transform) -> None:
    """One zip read/transform/write pass over a .docx (it's just a zip).

    `transform` receives the dict {archive-name: bytes} and mutates it in
    place; returning early leaves the package untouched on disk apart from
    recompression. Splitting patch_theme_fonts/patch_compat_mode into public
    functions while sharing this helper keeps the single-pass behavior the
    engine relies on (HANDOFF step 1)."""
    with zipfile.ZipFile(str(path)) as z:
        items = {n: z.read(n) for n in z.namelist()}
    transform(items)
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(str(tmp), "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in items.items():
            z.writestr(n, data)
    tmp.replace(path)


def patch_theme_fonts(path: Path, name: str, track_changes: bool = False) -> None:
    """Zip-level fixes python-docx can't do: (1) rewrite the document theme's
    typefaces so anything resolving through the theme lands on the same font
    instead of Word's Aptos default; (2) stamp compatibilityMode 15 into
    settings.xml — pandoc emits NO compatSetting at all, so Word opens every
    render in Compatibility Mode and applies legacy layout rules (pct table
    widths and in-cell justification misbehave); (3) when track_changes is
    True (collab target only — NEVER submission), plant <w:trackChanges/> so
    the document OPENS with Track Changes already on: coauthors start editing
    and every edit is captured without anyone remembering the toggle. It is a
    default, not a lock — a reviewer can still switch it off; we deliberately
    skip documentProtection (password-hash lock) as hostile to coauthors.
    See docx-quirks."""
    patch_document_package(path, font=name, track_changes=track_changes)


def patch_compat_mode(path: Path) -> None:
    """Standalone form of patch_theme_fonts' compatibilityMode stamping:
    write compatibilityMode 15 into settings.xml (inserting <w:compat> if
    absent, upgrading an existing value < 15 in place — python-docx's own
    template ships 14, which ALSO opens in Compatibility Mode). Unlike the
    combined path there is no theme1.xml presence guard: compat stamping is
    valuable for any pandoc-produced package."""
    def transform(items: dict[str, bytes]) -> None:
        settings = items.get("word/settings.xml", b"").decode("utf-8")
        if not settings:
            return
        if "compatibilityMode" in settings:
            # present but possibly < 15 (python-docx's own template ships 14,
            # which ALSO opens in Compatibility Mode) — upgrade in place
            settings = re.sub(
                r'<w:compatSetting[^>]*w:name="compatibilityMode"[^>]*/>',
                lambda m: re.sub(r'w:val="\d+"', 'w:val="15"', m.group(0)),
                settings,
            )
        else:
            compat = ('<w:compat><w:compatSetting w:name="compatibilityMode" '
                      'w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>')
            if "<w:rsids" in settings:
                settings = settings.replace("<w:rsids", compat + "<w:rsids", 1)
            else:
                settings = settings.replace("</w:settings>", compat + "</w:settings>", 1)
        items["word/settings.xml"] = settings.encode("utf-8")

    _rewrite_package(path, transform)


def patch_document_package(
    path: Path,
    font: str | None = None,
    track_changes: bool = False,
    compat: bool = True,
) -> None:
    """The engine's combined single-pass zip fixer — byte-identical to the
    original monolithic patch_theme_fonts, including its semantics:

    - everything is skipped when the package has no word/theme/theme1.xml
      (the historical early-return: such packages got no compat stamp either);
    - order of operations: theme fonts -> compat mode -> track changes flag.

    Public split functions (patch_compat_mode) exist for targeted use; the
    render pipeline calls THIS."""
    def transform(items: dict[str, bytes]) -> None:
        if "word/theme/theme1.xml" not in items:
            return
        if font is not None:
            theme = items["word/theme/theme1.xml"].decode("utf-8")
            theme = re.sub(
                r'(<a:(?:latin|ea|cs)\s+typeface=")[^"]*(")',
                lambda m: m.group(1) + font + m.group(2),
                theme,
            )
            items["word/theme/theme1.xml"] = theme.encode("utf-8")
        settings = items.get("word/settings.xml", b"").decode("utf-8")
        if settings and "compatibilityMode" not in settings:
            compat_el = ('<w:compat><w:compatSetting w:name="compatibilityMode" '
                         'w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>')
            if "<w:rsids" in settings:
                settings = settings.replace("<w:rsids", compat_el + "<w:rsids", 1)
            else:
                settings = settings.replace("</w:settings>", compat_el + "</w:settings>", 1)
            items["word/settings.xml"] = settings.encode("utf-8")
        elif settings:
            # present but possibly < 15 (python-docx's own template ships 14, which
            # ALSO opens in Compatibility Mode) — upgrade in place
            settings = re.sub(
                r'<w:compatSetting[^>]*w:name="compatibilityMode"[^>]*/>',
                lambda m: re.sub(r'w:val="\d+"', 'w:val="15"', m.group(0)),
                settings,
            )
            items["word/settings.xml"] = settings.encode("utf-8")
        settings = items.get("word/settings.xml", b"").decode("utf-8")
        if track_changes and settings and "<w:trackChanges" not in settings:
            # CT_Settings order: trackChanges precedes doNotTrackMoves and
            # defaultTabStop — anchor on whichever exists (pandoc has both).
            el = "<w:trackChanges/>"
            for anchor in ("<w:doNotTrackMoves", "<w:defaultTabStop"):
                if anchor in settings:
                    settings = settings.replace(anchor, el + anchor, 1)
                    break
            else:
                settings = re.sub(r"(<w:settings[^>]*>)", r"\1" + el, settings, count=1)
            items["word/settings.xml"] = settings.encode("utf-8")

    _rewrite_package(path, transform)


def dedupe_ppr(doc: Document) -> None:
    """Quarto 1.10's docx writer emits a SECOND <w:pPr> on crossref float
    caption paragraphs (and possibly others). That is invalid OOXML: python-docx
    reads/edits the FIRST pPr while Word honors the LAST, so alignment/spacing
    set through python-docx silently never renders. Merge duplicates into one
    pPr (later wins per property, matching what Word displayed), with pStyle
    reordered first as CT_PPr requires. Must run BEFORE any restyling."""
    for para in doc.element.body.iter(qn("w:p")):
        pprs = [c for c in para if c.tag == qn("w:pPr")]
        if len(pprs) < 2:
            continue
        base = pprs[0]
        for extra in pprs[1:]:
            for child in list(extra):
                prev = base.find(child.tag)
                if prev is not None:
                    base.remove(prev)
                base.append(child)
            para.remove(extra)
        st = base.find(qn("w:pStyle"))
        if st is not None:
            base.remove(st)
            base.insert(0, st)


# CT_PPr child sequence per ECMA-376 §17.3.1.26 — Word DISCARDS properties that
# appear out of this order (observed: a jc placed before spacing renders as if
# absent, so "justified" captions stayed left-aligned through two prior fixes).
_PPR_ORDER = (
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
    "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
    "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
    "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr",
    "pPrChange",
)


def normalize_ppr_order(doc: Document) -> None:
    """Re-sort every paragraph's pPr children into the CT_PPr schema sequence.
    Run LAST, after every pass that touches paragraph properties: dedupe_ppr's
    merge and raw appends can leave children out of order, and an out-of-order
    property is silently dead in Word."""
    rank = {qn(f"w:{name}"): i for i, name in enumerate(_PPR_ORDER)}
    for ppr in doc.element.body.iter(qn("w:pPr")):
        children = list(ppr)
        if len(children) < 2:
            continue
        ordered = sorted(children, key=lambda c: rank.get(c.tag, len(rank)))
        if ordered != children:
            for c in children:
                ppr.remove(c)
            for c in ordered:
                ppr.append(c)


def _tbl_set_width_pct(tbl, pct: int = 5000) -> None:
    tblPr = tbl._tbl.tblPr
    for el in tblPr.findall(qn("w:tblW")):
        tblPr.remove(el)
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), str(pct))
    w.set(qn("w:type"), "pct")
    ts = tblPr.find(qn("w:tblStyle"))
    tblPr.insert(list(tblPr).index(ts) + 1 if ts is not None else 0, w)


def _tbl_set_borders(tbl, top: int | None, bottom: int | None) -> None:
    """Explicit instance-level tblBorders: top/bottom single rules (sz in
    eighths of a point) or none; left/right/inside always none. The Table
    style's conditional firstRow bottom rule (the header midrule) survives,
    because cell-level conditional formatting outranks table-level borders."""
    tblPr = tbl._tbl.tblPr
    for el in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(el)
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", top), ("left", None), ("bottom", bottom),
                     ("right", None), ("insideH", None), ("insideV", None)):
        e = OxmlElement(f"w:{edge}")
        if sz:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(sz))
            e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "auto")
        else:
            e.set(qn("w:val"), "none")
        borders.append(e)
    anchor = tblPr.find(qn("w:tblW"))
    tblPr.insert(list(tblPr).index(anchor) + 1 if anchor is not None else 0, borders)


def _tbl_rescale_grid(t, width_dxa: int) -> None:
    """Rescale tblGrid columns (and per-cell tcW) proportionally so they sum
    to width_dxa. Pandoc hard-codes grids for its Letter-width reference doc
    (7920 dxa), so on our A4/25 mm page every table stops ~2 cm short of the
    right margin — and in-cell caption justification then LOOKS left-aligned
    because the cell itself is narrow."""
    grid = t._tbl.find(qn("w:tblGrid"))
    if grid is None:
        return
    cols = grid.findall(qn("w:gridCol"))
    widths = [int(c.get(qn("w:w")) or 0) for c in cols]
    total = sum(widths)
    if not total:
        return
    scaled = [max(1, round(w * width_dxa / total)) for w in widths]
    scaled[-1] += width_dxa - sum(scaled)  # rounding remainder to last col
    for c, w in zip(cols, scaled):
        c.set(qn("w:w"), str(w))
    for row in t.rows:
        for cell, w in zip(row.cells, scaled):
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.insert(0, tcW)
            tcW.set(qn("w:w"), str(w))
            tcW.set(qn("w:type"), "dxa")


def _page_field() -> OxmlElement:
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " PAGE ")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    return fld


def add_page_numbers(doc: Document, prefix: str = "") -> None:
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        para = footer.paragraphs[0]
        for run in list(para.runs):
            run._r.getparent().remove(run._r)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if prefix:
            para.add_run(prefix)
        para._p.append(_page_field())


def restart_page_numbering(doc: Document, start: int = 1) -> None:
    sect_pr = doc.sections[0]._sectPr
    pg = sect_pr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        sect_pr.insert_element_before(pg, *_SECT_PR_TAIL)
    pg.set(qn("w:start"), str(start))
