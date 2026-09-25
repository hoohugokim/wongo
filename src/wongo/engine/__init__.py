"""wongo.engine — the render pipeline.

`render_project()` runs the checks, refuses a submission render on a HARD
failure BEFORE Quarto runs, renders main (and SI) with Quarto into a staging
folder, post-processes there (wongo.docxpatch correctness fixes, then the house
style from wongo.styles), and only then moves the finished DOCX files into
output/ together. A failure at any step leaves output/ exactly as it was, and
a file held open by Word is reported instead of half-replaced. The function
returns a RenderResult and prints nothing; the CLI owns all output.

Validation checks live in wongo.engine.checks; tracked-changes extraction in
wongo.engine.roundtrip; the tracked diff in wongo.engine.diff.

The SI cover sheet carries title, authors, figure/table counts, and a NUMPAGES
field Word resolves on open (tests in tests/test_engine.py pin it).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm

from wongo import __version__, toolchain
from wongo import styles as wstyles
from wongo.docxpatch import (
    add_line_numbers,
    add_page_numbers,
    patch_theme_fonts,
    remove_line_numbers,
    restart_page_numbering,
    set_fonts,
)
from wongo.errors import GateError, InputError, OutputLockedError, ToolchainError, WongoError
from wongo.textio import read_text, write_text_atomic

EventHandler = Callable[[str, dict], None]
TARGETS = ("collab", "submission")


def set_line_spacing(doc: Document, factor: float) -> None:
    doc.styles["Normal"].paragraph_format.line_spacing = factor


def resolve_style(cfg: dict, override: str | None = None) -> dict:
    """Resolve an explicit CLI override, then project/env/default style.

    ``--style`` is an actual one-render override and does not mutate process
    state. Without it, an explicit ``style:`` in ``_journal.yml`` remains
    authoritative over the legacy ``$WONGO_STYLE`` environment fallback.
    """
    name = (
        override or cfg.get("style") or os.environ.get("WONGO_STYLE") or "default"
    )
    return wstyles.load_style(name)


# ---------------------------------------------------------------------------
# SI cover sheet


def _numpages_field() -> OxmlElement:
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " NUMPAGES ")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    return fld


def prepend_si_cover(doc: Document, profile: dict, counts: dict, meta: dict | None = None) -> None:
    """Cover sheet per journal profile: title, authors, figure/table counts,
    and a page count Word fills in on open (python-docx cannot paginate)."""
    meta = meta or {}
    lines = ["Supporting Information"]
    if meta.get("title"):
        lines.append(str(meta["title"]))
    authors = [
        a.get("name", "") for a in (meta.get("author") or []) if isinstance(a, dict)
    ]
    if authors:
        lines.append(", ".join(n for n in authors if n))
    lines.append(f"Contents: {counts.get('figures', 0)} figures, {counts.get('tables', 0)} tables")

    if not doc.paragraphs:  # SI that opens with a table/figure float
        doc.add_paragraph()
    first = doc.paragraphs[0]
    for text in lines:
        p = first.insert_paragraph_before(text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pages = first.insert_paragraph_before("")
    pages.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pages.add_run("Pages: ")
    pages._p.append(_numpages_field())
    brk = first.insert_paragraph_before("")
    run = brk.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)


# Caption lead of a Quarto crossref float ("Figure\xa01:", "Table S\xa02.").
_FLOAT_LEAD = re.compile(r"^(Figure|Table)[\s\xa0]+S?[\s\xa0]?\d+")


def _float_kind(table) -> str | None:
    """Classify a top-level table by what it holds.

    Quarto wraps every crossref float in a 1x1 outer table, so `doc.tables`
    mixes figure wrappers, table wrappers, and standalone data tables. The
    caption lead inside a wrapper is the semantic identifier; without one,
    a nested table means "table" and a drawing means "figure". A data table
    that merely contains an image is still a table.
    """
    if not (len(table.rows) == 1 and len(table.columns) == 1):
        return "table"
    cell = table.cell(0, 0)
    for para in cell.paragraphs:
        m = _FLOAT_LEAD.match(para.text or "")
        if m:
            return m.group(1).lower()
    if cell.tables:
        return "table"
    if any(True for _ in cell._tc.iter(qn("w:drawing"))):
        return "figure"
    return "table"


def si_item_counts(doc: Document) -> dict[str, int]:
    """Figure and table counts for the SI cover sheet.

    Figures: crossref figure floats plus unwrapped body-level pictures.
    Tables: crossref table floats plus standalone data tables. Pictures
    inside data tables are not figures; figure wrappers are not tables
    (see docs/bugs/si-cover-table-count.md).
    """
    counts = {"figures": 0, "tables": 0}
    for table in doc.tables:
        counts["figures" if _float_kind(table) == "figure" else "tables"] += 1
    for para in doc.paragraphs:
        if any(True for _ in para._p.iter(qn("w:drawing"))):
            counts["figures"] += 1
    return counts


DEFAULT_TOC_ART_LABEL = "For Table of Contents Only"


def insert_toc_art(
    doc: Document,
    image_path: Path,
    width_mm: float | None = None,
    label: str = DEFAULT_TOC_ART_LABEL,
    height_mm: float | None = None,
) -> None:
    """Append the TOC/abstract graphic at the END of the document.

    Per the official ACS "Guidelines for Table of Contents/Abstract
    Graphics" (dated 2024-02-28): the graphic is labeled "For Table of
    Contents Only" and placed on the LAST PAGE of the submitted manuscript
    (it may also be uploaded separately as "Graphics for manuscript").
    Produces, in order: a page break, a centered label paragraph, then a
    centered paragraph containing the image.

    The profile's ``width_mm``/``height_mm`` are MAXIMA of a bounding box
    (ACS: 3.25 in x 1.75 in). The picture is scaled to fit inside that box
    with its aspect ratio preserved; with only ``width_mm`` given the image
    is scaled to that width.
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
    shape = run.add_picture(str(image_path))
    if width_mm and height_mm:
        scale = min(Mm(width_mm) / shape.width, Mm(height_mm) / shape.height)
        shape.width = round(shape.width * scale)
        shape.height = round(shape.height * scale)
    elif width_mm:
        scale = Mm(width_mm) / shape.width
        shape.width = Mm(width_mm)
        shape.height = round(shape.height * scale)


# ---------------------------------------------------------------------------
# Quarto invocation + gates


STAGE_PREFIX = ".wongo-stage-"


def quarto_output_dir(project: Path) -> Path | None:
    """The project's Quarto output-dir (from _quarto.yml), if any."""
    config = project / "_quarto.yml"
    if not config.exists():
        return None
    try:
        data = yaml.safe_load(read_text(config)) or {}
    except yaml.YAMLError:
        return None
    out = (data.get("project") or {}).get("output-dir") if isinstance(data, dict) else None
    return project / str(out) if out else None


def quarto_render_command(quarto: list[str], qmd: str, out_name: str, profile: dict) -> list[str]:
    """The quarto argv for one document. Metadata paths use forward slashes:
    Windows backslashes would reach pandoc's YAML metadata parser."""
    cmd = [*quarto, "render", qmd, "--to", "docx", "--output", out_name]
    ref = profile.get("reference_doc")
    if ref:
        cmd += ["-M", f"reference-doc:{(Path(profile['_dir']) / ref).as_posix()}"]
    csl = profile.get("csl")
    if csl:
        cmd += ["-M", f"csl:{(Path(profile['_dir']) / csl).as_posix()}"]
    return cmd


def quarto_render(
    project: Path,
    qmd: str,
    out_name: str,
    profile: dict,
    *,
    stage_dir: Path,
    quarto: list[str] | None = None,
    quarto_stdout: int | None = None,
) -> Path:
    """Render `qmd` under a temporary name and move the raw DOCX to
    stage_dir/out_name. The deliverable in output/ is not touched."""
    quarto = quarto or toolchain.quarto_command()
    staged_name = f"{STAGE_PREFIX}{out_name}"
    out_dir = quarto_output_dir(project)
    candidates = [d / staged_name for d in (out_dir, project) if d is not None]
    for leftover in candidates:  # never mistake a crashed run's file for this one's
        leftover.unlink(missing_ok=True)
    cmd = quarto_render_command(quarto, qmd, staged_name, profile)
    try:
        subprocess.run(cmd, cwd=project, check=True, stdout=quarto_stdout)
    except subprocess.CalledProcessError as exc:
        raise ToolchainError(
            f"quarto render failed for {qmd} (see quarto output above)"
        ) from exc
    except OSError as exc:
        raise ToolchainError(f"could not run Quarto ({cmd[0]}): {exc}") from exc
    produced = next((c for c in candidates if c.exists()), None)
    if produced is None:
        looked = ", ".join(str(c.parent) for c in candidates)
        raise ToolchainError(f"quarto render did not produce {staged_name} (looked in {looked})")
    dest = stage_dir / out_name
    shutil.move(str(produced), dest)
    return dest


def find_toc_art(project: Path) -> Path | None:
    for ext in ("png", "tiff", "tif", "jpg", "jpeg"):
        p = project / "figures" / f"toc-art.{ext}"
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Post-processing


def postprocess_main(
    path: Path,
    profile: dict,
    cfg: dict,
    target: str,
    project: Path,
    style_override: str | None = None,
) -> None:
    doc = Document(str(path))
    if target == "submission":
        if profile.get("line_numbers") is True:
            add_line_numbers(doc)
        if profile.get("spacing") == "double":
            set_line_spacing(doc, 2.0)
        toc = (profile.get("toc_graphic") or {})
        if toc.get("required"):
            art = find_toc_art(project)
            if art is None:
                # Backstop only: render_project() gates this BEFORE
                # quarto_render() runs, so this branch should be unreachable in
                # practice. Message kept aligned with the pre-render gate.
                raise GateError(
                    "Profile requires TOC art but figures/toc-art.{png,tif,tiff,jpg,jpeg} is missing."
                )
            insert_toc_art(
                doc, art, toc.get("width_mm"),
                toc.get("label") or DEFAULT_TOC_ART_LABEL,
                height_mm=toc.get("height_mm"),
            )
    style = resolve_style(cfg, style_override)
    font = _style_font(style)
    if font:
        set_fonts(doc, font)
    wstyles.apply_style(doc, style, wstyles.read_front_matter(project, "index.qmd"))
    if target == "submission" and profile.get("line_numbers") == "forbidden":
        # journal directive beats house taste: e.g. Water Research adds line
        # numbers itself and asks authors not to include them
        remove_line_numbers(doc)
    add_page_numbers(doc)
    doc.save(str(path))
    patch_theme_fonts(path, font, track_changes=(target == "collab"))


def _style_font(style: dict) -> str | None:
    """The house style's font, or None to keep the journal reference-doc
    fonts untouched (``default.yml`` sets ``font: null`` for exactly that)."""
    return style.get("font") or None


def postprocess_si(
    path: Path,
    profile: dict,
    cfg: dict,
    target: str,
    project: Path,
    style_override: str | None = None,
) -> None:
    doc = Document(str(path))
    si = profile.get("si") or {}
    style = resolve_style(cfg, style_override)
    font = _style_font(style)
    if font:
        set_fonts(doc, font)
    # no index.qmd meta for styling: SI keeps its plain author line, no keywords;
    # but the cover sheet DOES want title/authors from the front matter
    meta = wstyles.read_front_matter(project, "index.qmd") if si.get("needs_cover_sheet") else None
    wstyles.apply_style(doc, style)
    if target == "submission" and profile.get("line_numbers") == "forbidden":
        remove_line_numbers(doc)
    counts = si_item_counts(doc)
    if si.get("needs_cover_sheet"):
        prepend_si_cover(doc, profile, counts, meta)
    add_page_numbers(doc, prefix=si.get("page_prefix", "S"))
    restart_page_numbering(doc, start=1)
    doc.save(str(path))
    patch_theme_fonts(path, font, track_changes=(target == "collab"))


# ---------------------------------------------------------------------------
# Output promotion and manifest


MANIFEST_NAME = ".wongo-manifest.json"


def _restore(backups: list[tuple[Path, Path]]) -> None:
    for dest, backup in reversed(backups):
        os.replace(backup, dest)


def promote(staged: list[Path], out_dir: Path) -> list[Path]:
    """Move finished files into out_dir as one unit.

    Existing outputs are first renamed to backups; on Windows that rename
    fails while Word holds the file open, and everything is put back before
    anything new lands. Then the staged files move in, and the backups go.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    backups: list[tuple[Path, Path]] = []
    try:
        for src in staged:
            dest = out_dir / src.name
            if dest.exists():
                backup = out_dir / f".{src.name}.wongo-bak"
                backup.unlink(missing_ok=True)
                os.replace(dest, backup)
                backups.append((dest, backup))
    except PermissionError as exc:
        _restore(backups)
        name = Path(exc.filename).name if exc.filename else "an output file"
        raise OutputLockedError(
            f"{name} is open in another program (probably Word). Close it and render "
            "again; output/ was left unchanged."
        ) from exc
    placed: list[Path] = []
    try:
        for src in staged:
            dest = out_dir / src.name
            os.replace(src, dest)
            placed.append(dest)
    except OSError:
        for dest in placed:
            dest.unlink(missing_ok=True)
        _restore(backups)
        raise
    for _, backup in backups:
        try:
            backup.unlink()
        except OSError:
            pass
    return placed


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(project: Path) -> list[Path]:
    """Inputs whose change makes an output stale: the .qmd files, the project
    and journal config, the bibliography, and everything under figures/."""
    from wongo.engine.checks import bibliography_paths

    files = [project / n for n in ("index.qmd", "si.qmd", "_quarto.yml", "_journal.yml")]
    index = project / "index.qmd"
    if index.exists():
        try:
            files += bibliography_paths(project, read_text(index))
        except WongoError:
            pass
    figures = project / "figures"
    if figures.is_dir():
        files += sorted(p for p in figures.rglob("*") if p.is_file())
    return [p for p in dict.fromkeys(files) if p.is_file()]


def source_fingerprint(project: Path) -> dict[str, str]:
    fingerprint = {}
    for path in source_files(project):
        try:
            key = path.relative_to(project).as_posix()
        except ValueError:
            key = str(path)
        fingerprint[key] = _sha256(path)
    return fingerprint


def read_manifest(project: Path) -> dict:
    path = Path(project) / "output" / MANIFEST_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_manifest(project: Path, target: str, outputs: list[Path], cfg: dict,
                   style_name: str, quarto_version: str | None) -> Path:
    """Record what produced each output (versions, config, source hashes) so
    `wongo status` can tell a fresh output from a stale or hand-edited one."""
    path = project / "output" / MANIFEST_NAME
    data = read_manifest(project)
    data["format"] = 1
    data.setdefault("targets", {})[target] = {
        "rendered_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "wongo": __version__,
        "quarto": quarto_version,
        "journal": cfg.get("journal"),
        "ms_type": cfg.get("ms_type"),
        "style": style_name,
        "outputs": {p.name: _sha256(p) for p in outputs},
        "sources": source_fingerprint(project),
    }
    write_text_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


# ---------------------------------------------------------------------------
# Orchestration


@dataclass
class RenderResult:
    project: Path
    target: str
    outputs: list[Path]
    checks: list
    manifest: Path
    quarto_version: str | None = None

    @property
    def hard_failures(self) -> list:
        return [c for c in self.checks if c.level == "HARD" and not c.ok]

    @property
    def warnings(self) -> list:
        return [c for c in self.checks if c.level == "WARN" and not c.ok]


def _emit(on_event: EventHandler | None, kind: str, **payload) -> None:
    if on_event is not None:
        on_event(kind, payload)


def render_project(
    project: Path,
    target: str,
    style_override: str | None = None,
    *,
    on_event: EventHandler | None = None,
    quarto_stdout: int | None = None,
) -> RenderResult:
    """Render one manuscript project; see the module docstring.

    `on_event(kind, payload)` receives "checks" (after validation, before any
    rendering) and "wrote" (after the outputs are in place). `quarto_stdout`
    redirects Quarto's stdout (e.g. to fd 2 when stdout must stay JSON).
    Raises WongoError subclasses for every user-fixable failure.
    """
    from wongo.engine.checks import run_checks
    from wongo.profiles import load_journal_config, load_profile, manuscript_type

    if target not in TARGETS:
        raise InputError(f"unknown target {target!r}; use one of: {', '.join(TARGETS)}")
    project = Path(project).resolve()
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    manuscript_type(profile, cfg["ms_type"])  # fail fast on bad ms_type
    style = resolve_style(cfg, style_override)  # fail fast on an unknown style

    checks = run_checks(project)
    _emit(on_event, "checks", checks=checks)
    hard = [c for c in checks if c.level == "HARD" and not c.ok]
    if hard and target == "submission":
        raise GateError("HARD checks failed — submission render refused (fix, or render --target collab).")

    # Gate BEFORE quarto ever runs (backstop kept in postprocess_main).
    if (
        target == "submission"
        and (profile.get("toc_graphic") or {}).get("required")
        and find_toc_art(project) is None
    ):
        raise GateError(
            "Profile requires TOC art but figures/toc-art.{png,tif,tiff,jpg,jpeg} "
            "is missing — submission render refused."
        )

    quarto = toolchain.quarto_command()
    out_dir = project / "output"
    stage = out_dir / f".stage-{target}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        staged = [quarto_render(project, "index.qmd", f"main-{target}.docx", profile,
                                stage_dir=stage, quarto=quarto, quarto_stdout=quarto_stdout)]
        postprocess_main(staged[0], profile, cfg, target, project,
                         style_override=style_override)
        if (project / "si.qmd").exists():
            si_docx = quarto_render(project, "si.qmd", f"si-{target}.docx", profile,
                                    stage_dir=stage, quarto=quarto, quarto_stdout=quarto_stdout)
            postprocess_si(si_docx, profile, cfg, target, project,
                           style_override=style_override)
            staged.append(si_docx)
        outputs = promote(staged, out_dir)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    version = toolchain.tool_version(quarto)
    manifest = write_manifest(project, target, outputs, cfg, style.get("_name", "default"), version)
    _emit(on_event, "wrote", outputs=outputs)
    return RenderResult(project, target, outputs, checks, manifest, version)


def output_freshness(project: Path, target: str) -> dict:
    """State of one target's outputs against the manifest.

    state: missing (no output) | unknown (no manifest entry) | modified (an
    output changed after rendering, e.g. saved over in Word) | stale (sources
    changed since rendering) | fresh.
    """
    project = Path(project).resolve()
    out_dir = project / "output"
    names = [f"main-{target}.docx"] + ([f"si-{target}.docx"] if (project / "si.qmd").exists() else [])
    if not all((out_dir / n).is_file() for n in names):
        return {"state": "missing", "changed": [n for n in names if not (out_dir / n).is_file()]}
    entry = (read_manifest(project).get("targets") or {}).get(target)
    if not entry:
        return {"state": "unknown", "changed": []}
    modified = [n for n, digest in (entry.get("outputs") or {}).items()
                if (out_dir / n).is_file() and _sha256(out_dir / n) != digest]
    if modified:
        return {"state": "modified", "changed": modified}
    recorded = entry.get("sources") or {}
    current = source_fingerprint(project)
    changed = sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))
    return {"state": "stale" if changed else "fresh", "changed": changed,
            "rendered_at": entry.get("rendered_at")}
