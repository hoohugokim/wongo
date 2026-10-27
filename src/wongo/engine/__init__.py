"""wongo.engine — the render pipeline.

`render_project()` runs source checks, refuses a submission render on a known
HARD failure BEFORE Quarto runs, renders main (and SI) with Quarto into a staging
folder, post-processes there (wongo.docxpatch correctness fixes, then the house
style from wongo.styles), checks reference-inclusive limits on the staged main
bibliography when required, and only then moves the finished DOCX files into
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
import sys
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
from wongo.errors import (
    GateError,
    InputError,
    OutputError,
    OutputLockedError,
    ToolchainError,
    WongoError,
)
from wongo.textio import read_text, write_text_atomic

EventHandler = Callable[[str, dict], None]
TARGETS = ("collab", "submission")


def set_line_spacing(doc: Document, factor: float) -> None:
    doc.styles["Normal"].paragraph_format.line_spacing = factor


def style_name(cfg: dict, override: str | None = None) -> str:
    """The house style a render uses: an explicit CLI override, then the
    project's, then the environment's, then `default`.

    ``--style`` is an actual one-render override and does not mutate process
    state. Without it, an explicit ``style:`` in ``_journal.yml`` remains
    authoritative over the legacy ``$WONGO_STYLE`` environment fallback.
    """
    return override or cfg.get("style") or os.environ.get("WONGO_STYLE") or "default"


def resolve_style(cfg: dict, override: str | None = None) -> dict:
    """Load the style `style_name` picks."""
    return wstyles.load_style(style_name(cfg, override))


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


@dataclass(frozen=True)
class QuartoRender:
    path: Path
    warnings: list[str]


_UNRESOLVED_CROSSREF = re.compile(r"Unable to resolve crossref", re.IGNORECASE)


def quarto_render(
    project: Path,
    qmd: str,
    out_name: str,
    profile: dict,
    *,
    stage_dir: Path,
    quarto: list[str] | None = None,
    quarto_stdout: int | None = None,
    on_event: EventHandler | None = None,
) -> QuartoRender:
    """Render `qmd` under a temporary name and move the raw DOCX to
    stage_dir/out_name. The deliverable in output/ is not touched.

    Quarto's combined output is returned through diagnostic events. `warnings` lists lines
    that say a cross-reference was not resolved. Quarto still exits 0 for
    those, so the caller has to fail the render itself. `quarto_stdout` is
    retained for callers that used to point Quarto at stderr; the engine
    never prints the captured text.
    """
    del quarto_stdout
    quarto = quarto or toolchain.quarto_command()
    staged_name = f"{STAGE_PREFIX}{out_name}"
    out_dir = quarto_output_dir(project)
    candidates = [d / staged_name for d in (out_dir, project) if d is not None]
    for leftover in candidates:  # never mistake a crashed run's file for this one's
        try:
            leftover.unlink(missing_ok=True)
        except PermissionError as exc:
            raise OutputLockedError(
                f"{leftover.name} in {leftover.parent}, an unfinished file left by an "
                "interrupted render, is open in another program (probably Word). Close it "
                "and render again."
            ) from exc
    cmd = quarto_render_command(quarto, qmd, staged_name, profile)
    try:
        completed = subprocess.run(
            cmd, cwd=project, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
    except BaseException as exc:
        # Quarto may have written its file before failing (a post-render hook,
        # Ctrl-C): never leave an unfinished DOCX next to the deliverables.
        _discard(candidates)
        if isinstance(exc, OSError):
            raise ToolchainError(f"could not run Quarto ({cmd[0]}): {exc}") from exc
        raise
    output = completed.stdout or ""
    if output:
        _emit(on_event, "diagnostic", source="quarto", text=output)
    if completed.returncode != 0:
        _discard(candidates)
        raise ToolchainError(
            f"quarto render failed for {qmd}; fix the reported Quarto error and render again.",
            output=output,
        )
    produced = next((c for c in candidates if c.exists()), None)
    if produced is None:
        looked = ", ".join(str(c.parent) for c in candidates)
        raise ToolchainError(f"quarto render did not produce {staged_name} (looked in {looked})")
    dest = stage_dir / out_name
    shutil.move(str(produced), dest)
    warnings = [line.strip() for line in output.splitlines() if _UNRESOLVED_CROSSREF.search(line)]
    return QuartoRender(dest, warnings)


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


def _discard(paths: list[Path]) -> None:
    """Best-effort removal: cleaning up must never hide the original error."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _roll_back(placed: list[Path], backups: list[tuple[Path, Path]]) -> list[Path]:
    """Undo a partial promotion; return the backups that could not be put back."""
    _discard(placed)
    stranded = []
    for dest, backup in reversed(backups):
        try:
            os.replace(backup, dest)
        except OSError:
            stranded.append(backup)
    return stranded


def _promotion_error(exc: OSError, stranded: list[Path]) -> WongoError:
    name = Path(exc.filename).name if exc.filename else "an output file"
    if stranded:
        kept = ", ".join(f"output/{p.name}" for p in stranded)
        outcome = (f"the previous version is kept as {kept}; rename it back by removing the "
                   "leading dot and the .wongo-bak ending")
    else:
        outcome = "output/ was left unchanged"
    if isinstance(exc, PermissionError):
        return OutputLockedError(
            f"{name} is open in another program (probably Word). Close it and render "
            f"again; {outcome}."
        )
    return OutputError(
        f"could not replace {name} in output/ ({exc.strerror or exc}); {outcome}. If the "
        "project is in OneDrive or another synced folder, pause syncing and render again."
    )


def promote(staged: list[Path], out_dir: Path) -> list[Path]:
    """Move finished files into out_dir as one unit.

    Existing outputs are first renamed to backups; on Windows that rename
    fails while Word holds the file open. Then the staged files move in, and
    the backups go. Any failure or interruption before the end, Ctrl-C
    included, puts the previous files back first.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    backups: list[tuple[Path, Path]] = []
    placed: list[Path] = []
    try:
        for src in staged:
            dest = out_dir / src.name
            if dest.exists():
                backup = out_dir / f".{src.name}.wongo-bak"
                backup.unlink(missing_ok=True)
                os.replace(dest, backup)
                backups.append((dest, backup))
        for src in staged:
            dest = out_dir / src.name
            os.replace(src, dest)
            placed.append(dest)
    except BaseException as exc:
        stranded = _roll_back(placed, backups)
        if isinstance(exc, OSError):
            raise _promotion_error(exc, stranded) from exc
        raise
    _discard([backup for _, backup in backups])
    return placed


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(project: Path) -> list[Path]:
    """Inputs whose change makes an output stale: the .qmd files, the project
    and journal config, the bibliography, and everything under figures/."""
    from wongo.engine.checks import bibliography_paths

    files = [project / n for n in ("index.qmd", "si.qmd", "_quarto.yml", "_journal.yml",
                                 "highlights.md")]
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


def _hash_file(key: str, path: Path) -> str:
    try:
        return _sha256(path)
    except OSError as exc:
        raise InputError(
            f"could not read {key} ({exc.strerror or exc}); if another program has it "
            "open, close it and try again"
        ) from exc


def source_fingerprint(project: Path) -> dict[str, str]:
    """Hashes of the inputs that make an output stale.

    Core manuscript files always count. Declared dependencies, Quarto hook
    scripts, and postprocess scripts count when the project names them. A
    missing declared path stays in the map as ``missing`` so it cannot
    disappear and look fresh.
    """
    from wongo.engine.inputs import EMPTY_DIRECTORY, MISSING, declared_inputs
    from wongo.profiles import load_journal_config

    project = Path(project)
    fingerprint = {}
    for path in source_files(project):
        try:
            key = path.relative_to(project).as_posix()
        except ValueError:
            key = str(path)
        fingerprint[key] = _hash_file(key, path)
    cfg = load_journal_config(project) if (project / "_journal.yml").is_file() else {}
    for item in declared_inputs(project, cfg):
        if item.path is None or not item.path.exists():
            fingerprint[item.key] = MISSING
        elif item.path.is_dir():
            fingerprint[item.key] = EMPTY_DIRECTORY
        else:
            fingerprint[item.key] = _hash_file(item.key, item.path)
    return fingerprint


def install_identity() -> dict:
    """Whether this wongo import is a clean git checkout. Not an input hash."""
    here = Path(__file__).resolve()
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here.parent, check=False, capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
        if root.returncode != 0:
            return {"state": "unknown"}
        checkout = root.stdout.strip()
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout, check=False, capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=checkout, check=False, capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return {"state": "unknown"}
    if commit.returncode != 0:
        return {"state": "unknown"}
    return {
        "state": "dirty" if dirty.stdout.strip() else "clean",
        "commit": commit.stdout.strip(),
    }


def _asset_identity(profile: dict, style: dict) -> dict:
    from wongo.styles import styles_dir

    pdir = Path(profile["_dir"])

    def file_hash(path: Path) -> dict | None:
        if not path.is_file():
            return None
        return {"path": path.as_posix(), "sha256": _hash_file(path.as_posix(), path)}

    identity = {
        "profile": file_hash(pdir / "profile.yml"),
        "style": file_hash(styles_dir() / f"{style.get('_name', 'default')}.yml"),
    }
    if profile.get("csl"):
        identity["csl"] = file_hash(pdir / profile["csl"])
    if profile.get("reference_doc"):
        identity["reference_doc"] = file_hash(pdir / profile["reference_doc"])
    return identity


def build_identity(profile: dict, style: dict) -> dict:
    """Build assets plus install identity; dirty/clean does not affect freshness."""
    return {"source": install_identity(), **_asset_identity(profile, style)}


def read_manifest(project: Path) -> dict:
    path = Path(project) / "output" / MANIFEST_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_manifest(project: Path, target: str, outputs: list[Path], cfg: dict,
                   style_name: str, quarto_version: str | None, *,
                   sources: dict[str, str] | None = None, dest: Path | None = None,
                   identity: dict | None = None, postprocess: list | None = None,
                   checks_failed: list[str] | None = None,
                   style_override: str | None = None, si_references: dict | None = None) -> Path:
    """Record what produced each output (versions, config, source hashes) so
    `wongo status` can tell a fresh output from a stale or hand-edited one.

    `sources` is the fingerprint taken before rendering (default: now); `dest`
    is where to write (default: output/), e.g. a staging folder whose files
    are promoted together with the outputs. `identity` names the profile,
    style, and install that produced the file. `postprocess` records each
    declared script and the output hashes around it. Output hashes are the
    bytes after those scripts and explicit SI-reference resolution.
    """
    path = dest or project / "output" / MANIFEST_NAME
    data = read_manifest(project)
    data["format"] = 1
    entry = {
        "rendered_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "wongo": __version__,
        "quarto": quarto_version,
        "journal": cfg.get("journal"),
        "ms_type": cfg.get("ms_type"),
        "style": style_name,
        "style_override": style_override,
        "outputs": {p.name: _sha256(p) for p in outputs},
        "sources": sources if sources is not None else source_fingerprint(project),
        "checks_failed": list(checks_failed or []),
    }
    if identity is not None:
        entry["identity"] = identity
    if postprocess:
        entry["postprocess"] = postprocess
    if si_references:
        entry["si_references"] = si_references
    data.setdefault("targets", {})[target] = entry
    write_text_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def _run_declared_postprocess(project: Path, cfg: dict, target: str,
                              outputs: list[Path], *,
                              on_event: EventHandler | None = None) -> list[dict]:
    """Run `_journal.yml` postprocess scripts on staged DOCX files.

    Scripts are not shell commands. Python scripts use this interpreter.
    A failure leaves the caller to discard the stage.
    """
    from wongo.engine.inputs import postprocess_paths

    root = Path(project).resolve()
    records = []
    for script in postprocess_paths(root, cfg):
        rel = script.relative_to(root).as_posix()
        if not script.is_file():
            raise InputError(
                f"postprocess script {rel} is missing. "
                "The previous outputs were left unchanged."
            )
        script_hash = _hash_file(rel, script)
        before = {path.name: _hash_file(path.name, path) for path in outputs}
        env = os.environ.copy()
        env["WONGO_POSTPROCESS_TARGET"] = target
        env["WONGO_POSTPROCESS_OUTPUTS"] = os.pathsep.join(str(path) for path in outputs)
        env["WONGO_PROJECT"] = str(root)
        env["PYTHONIOENCODING"] = "utf-8"
        command = [sys.executable, str(script)] if script.suffix.lower() == ".py" else [str(script)]
        try:
            completed = subprocess.run(
                command, cwd=root, check=False, env=env, timeout=120,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            if output:
                _emit(on_event, "diagnostic", source=rel, text=output)
            raise InputError(
                f"postprocess script {rel} timed out after 120 seconds. "
                "The previous outputs were left unchanged. Fix the script and render again.",
                output=output,
            ) from exc
        except OSError as exc:
            raise InputError(
                f"could not run postprocess script {rel} ({exc.strerror or exc}). "
                "The previous outputs were left unchanged."
            ) from exc
        output = completed.stdout or ""
        if output:
            _emit(on_event, "diagnostic", source=rel, text=output)
        if completed.returncode != 0:
            raise InputError(
                f"postprocess script {rel} failed (exit {completed.returncode}). "
                "The previous outputs were left unchanged. Fix the script and render again.",
                output=output,
            )
        for path in outputs:
            try:
                Document(path)
            except Exception as exc:
                raise InputError(
                    f"postprocess script {rel} left {path.name} missing or invalid. "
                    "The previous outputs were left unchanged. Fix the script to preserve "
                    "valid DOCX files and render again."
                ) from exc
        after = {path.name: _hash_file(path.name, path) for path in outputs}
        records.append({
            "path": rel,
            "sha256": script_hash,
            "outputs": {name: {"before": before[name], "after": after[name]} for name in before},
        })
    return records


def _identity_drift(project: Path, entry: dict) -> tuple[list[str], str | None]:
    """Profile and style identity changes. Install dirty/clean is ignored."""
    from wongo.profiles import load_journal_config, load_profile

    recorded = entry.get("identity")
    if not isinstance(recorded, dict) or not isinstance(recorded.get("profile"), dict) \
            or not isinstance(recorded.get("style"), dict):
        return ["profile identity"], (
            "the recorded render does not name profile or style identity"
        )
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    override = entry.get("style_override") if "style_override" in entry else entry.get("style")
    current = _asset_identity(profile, resolve_style(cfg, override))
    changed = []
    for key in ("profile", "style", "csl", "reference_doc"):
        old = recorded.get(key)
        new = current.get(key)
        old_hash = old.get("sha256") if isinstance(old, dict) else None
        new_hash = new.get("sha256") if isinstance(new, dict) else None
        if old_hash != new_hash:
            changed.append(key)
    return changed, None


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

    `on_event(kind, payload)` receives "checks" before rendering and after final
    validation, "diagnostic" for tool output, and "wrote" after promotion.
    `quarto_stdout` is retained for compatibility; tool output is captured.
    Raises WongoError subclasses for every user-fixable failure.
    """
    from wongo.engine.checks import Check, run_checks
    from wongo.profiles import load_journal_config, load_profile, manuscript_type

    if target not in TARGETS:
        raise InputError(f"unknown target {target!r}; use one of: {', '.join(TARGETS)}")
    project = Path(project).resolve()
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    mtype = manuscript_type(profile, cfg["ms_type"])  # fail fast on bad ms_type
    style = resolve_style(cfg, style_override)  # fail fast on an unknown style

    from wongo.engine.inputs import MISSING

    sources = source_fingerprint(project)
    identity = build_identity(profile, style)
    missing = sorted(key for key, digest in sources.items() if digest == MISSING)
    if missing:
        raise InputError(
            "Declared input missing: " + ", ".join(missing) + ". Restore the file "
            "or remove it from _journal.yml dependencies.",
            paths=missing,
        )

    checks = run_checks(project)
    _emit(on_event, "checks", checks=checks)
    hard = [c for c in checks if c.level == "HARD" and not c.ok]
    if any(c.name == "si-references" for c in hard):
        raise GateError("Invalid explicit SI reference configuration; fix the si-references check and render again.",
                        checks=checks)
    if hard and target == "submission":
        raise GateError("HARD checks failed — submission render refused (fix, or render --target collab).",
                        checks=checks)

    # Source/TOC gates run before Quarto; reference words are checked in staging.
    if (
        target == "submission"
        and (profile.get("toc_graphic") or {}).get("required")
        and find_toc_art(project) is None
    ):
        raise GateError(
            "Profile requires TOC art but figures/toc-art.{png,tif,tiff,jpg,jpeg} "
            "is missing — submission render refused.",
            checks=checks,
        )

    def require_unchanged_inputs() -> None:
        try:
            current_profile = load_profile(cfg["journal"], project)
            current_style = resolve_style(cfg, style_override)
            changed = (
                source_fingerprint(project) != sources
                or current_profile != profile
                or current_style != style
                or _asset_identity(current_profile, current_style)
                != {key: value for key, value in identity.items() if key != "source"}
            )
        except WongoError:
            changed = True
        if not changed:
            return
        message = (
            "A source, journal profile, or build asset changed during rendering. "
            "The previous outputs were left unchanged. Finish saving and render again."
        )
        if mtype.get("word_limit_includes_references"):
            failed = [check for check in checks if check.name != "word-limit-references"]
            failed.append(Check(
                "word-limit-references", "HARD", False,
                message + " The reference-inclusive count is unverified.",
            ))
            raise GateError(message, checks=failed)
        raise InputError(message)

    require_unchanged_inputs()
    quarto = toolchain.quarto_command()
    unrenderable = toolchain.unrenderable_path_reason(project)
    if unrenderable:
        raise ToolchainError(unrenderable)
    out_dir = project / "output"
    stage = out_dir / f".stage-{target}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        rendered = quarto_render(project, "index.qmd", f"main-{target}.docx", profile,
                                 stage_dir=stage, quarto=quarto, quarto_stdout=quarto_stdout,
                                 on_event=on_event)
        staged = [rendered.path]
        warnings = list(rendered.warnings)
        postprocess_main(staged[0], profile, cfg, target, project,
                         style_override=style_override)
        if (project / "si.qmd").exists():
            rendered_si = quarto_render(project, "si.qmd", f"si-{target}.docx", profile,
                                        stage_dir=stage, quarto=quarto, quarto_stdout=quarto_stdout,
                                        on_event=on_event)
            warnings.extend(rendered_si.warnings)
            postprocess_si(rendered_si.path, profile, cfg, target, project,
                           style_override=style_override)
            staged.append(rendered_si.path)
        warning_check = None
        if warnings:
            warning_check = Check(
                "crossrefs-rendered", "HARD", False,
                "Quarto exited 0 but could not resolve a cross-reference: "
                + " | ".join(warnings),
                warnings,
            )
        require_unchanged_inputs()
        transforms = _run_declared_postprocess(project, cfg, target, staged, on_event=on_event)
        require_unchanged_inputs()
        from wongo.engine.si_refs import enabled as si_refs_enabled
        from wongo.engine.si_refs import resolve as resolve_si_references

        if len(staged) > 1:
            resolve_si_references(staged[1], None, active=False)
        si_references = resolve_si_references(staged[0], staged[1] if len(staged) > 1 else None,
                                               active=si_refs_enabled(cfg))
        require_unchanged_inputs()
        checks = run_checks(project, rendered_main=staged[0])
        if si_references:
            checks.append(Check(
                "si-references-rendered", "HARD", True,
                f"{len(si_references['references'])} main-to-SI link(s) resolved from final SI bookmarks and captions",
            ))
        if warning_check is not None:
            checks = [c for c in checks if c.name != "crossrefs-rendered"]
            checks.append(warning_check)
        _emit(on_event, "checks", checks=checks)
        if target == "submission" and any(c.level == "HARD" and not c.ok for c in checks):
            if any(c.name == "word-limit-references" and not c.ok for c in checks):
                message = (
                    "HARD checks failed after counting the rendered references — submission "
                    "refused; previous outputs were left unchanged. Fix the reported checks "
                    "or render --target collab to inspect it."
                )
            else:
                message = (
                    "HARD checks failed after rendering — submission refused; previous "
                    "outputs were left unchanged."
                )
            raise GateError(message, checks=checks)
        version = toolchain.tool_version(quarto)
        require_unchanged_inputs()
        failed = [c.name for c in checks if c.level == "HARD" and not c.ok]
        # the manifest is promoted with the outputs, so the two always agree
        staged.append(write_manifest(
            project, target, [p for p in staged if p.suffix == ".docx"], cfg,
            style.get("_name", "default"), version, sources=sources,
            dest=stage / MANIFEST_NAME, identity=identity,
            postprocess=transforms, checks_failed=failed,
            style_override=style_override, si_references=si_references,
        ))
        placed = promote(staged, out_dir)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    outputs = [p for p in placed if p.name != MANIFEST_NAME]
    manifest = out_dir / MANIFEST_NAME
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
    identity_changed, identity_detail = _identity_drift(project, entry)
    if identity_changed:
        result = {"state": "stale", "changed": identity_changed,
                  "rendered_at": entry.get("rendered_at")}
        if identity_detail:
            result["detail"] = identity_detail
        return result
    recorded = entry.get("sources") or {}
    current = source_fingerprint(project)
    changed = sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))
    from wongo.engine.si_refs import enabled as si_refs_enabled
    from wongo.profiles import load_journal_config

    if si_refs_enabled(load_journal_config(project)):
        binding = entry.get("si_references")
        outputs = entry.get("outputs") or {}
        if (not isinstance(binding, dict) or binding.get("schema") != "wongo-si-references/1"
                or not isinstance(binding.get("references"), list)
                or binding.get("main_after") != outputs.get(f"main-{target}.docx")
                or binding.get("si_sha256") != outputs.get(f"si-{target}.docx")):
            changed.append("si reference identity")
    return {"state": "stale" if changed else "fresh", "changed": changed,
            "rendered_at": entry.get("rendered_at")}
