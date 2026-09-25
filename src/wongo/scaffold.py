"""`wongo scaffold`: start a manuscript project from the packaged template.

The template carries editor tasks (.vscode/tasks.json, used by VS Code and
Positron) and agent instructions (AGENTS.md, CLAUDE.md) so a new project works
with the Claude front door right away. Agent files ship as *.tmpl so this repo's
own agents never read them as instructions. `example=True` adds a small
manuscript that renders out of the box (R + knitr), including a placeholder
TOC graphic sized for ACS journals.
"""
from __future__ import annotations

import shutil
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from wongo.errors import InputError
from wongo.profiles import load_profile, manuscript_type
from wongo.styles import load_style

ASSETS = Path(__file__).resolve().parent / "assets"
TEMPLATE = ASSETS / "scaffold"
EXAMPLE = ASSETS / "scaffold-example"
EXAMPLE_JOURNAL = "est"
TOC_ART_PX = (975, 525)  # 3.25 in x 1.75 in at 300 dpi: the ACS TOC-graphic box


@dataclass
class ScaffoldResult:
    dest: Path
    journal: str | None
    ms_type: str | None
    style: str
    example: bool
    journal_name: str | None = None
    files: list[str] = field(default_factory=list)


def journal_yml(journal: str | None, ms_type: str | None, style: str) -> str:
    """_journal.yml with aligned comments; a comment always has two spaces
    before its '#', or YAML would read it as part of a long value."""
    rows = [
        (f"journal: {journal or chr(34) * 2}", "journal profile slug: `wongo profile list`"),
        (f"ms_type: {ms_type or chr(34) * 2}", "a manuscript type of that profile: "
                                               "`wongo profile show <slug>`"),
        (f"style: {style}", "house look: `wongo style list`"),
        ("blinding: default", "or override per submission"),
    ]
    width = max(24, max(len(entry) for entry, _ in rows) + 2)
    return "".join(f"{entry:<{width}}# {comment}\n" for entry, comment in rows)


def placeholder_toc_art(path: Path) -> None:
    """A plain 975x525 px PNG at 300 dpi (fits the ACS box exactly); replace it
    with real TOC art before submitting."""
    width, height = TOC_ART_PX

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    border, fill = b"\x30\x60\x90", b"\xe8\xf0\xf8"
    rows = []
    for y in range(height):
        if y < 12 or y >= height - 12:
            row = border * width
        else:
            row = border * 12 + fill * (width - 24) + border * 12
        rows.append(b"\x00" + row)
    per_metre = round(300 / 0.0254)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"pHYs", struct.pack(">IIB", per_metre, per_metre, 1))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


def scaffold(dest: Path, *, journal: str | None = None, ms_type: str | None = None,
             style: str | None = None, example: bool = False) -> ScaffoldResult:
    dest = Path(dest).expanduser().resolve()
    if dest.exists() and not dest.is_dir():
        raise InputError(f"{dest} exists and is not a folder")
    if dest.exists() and any(dest.iterdir()):
        raise InputError(f"destination not empty: {dest} (pick a new folder name)")
    if not (TEMPLATE / "_journal.yml").exists():
        raise InputError(f"scaffold template missing next to package: {TEMPLATE}; reinstall wongo")
    if ms_type and not journal and not example:
        raise InputError("--ms-type needs --journal (`wongo profile list` shows the slugs)")

    if example:
        journal = journal or EXAMPLE_JOURNAL
    journal_name = None
    if journal:
        profile = load_profile(journal)
        journal_name = str(profile.get("journal", journal))
        if ms_type:
            manuscript_type(profile, ms_type)
        elif example:
            ms_type = str((profile.get("manuscript_types") or [{}])[0].get("type") or "")
            ms_type = ms_type or None
    style = style or "default"
    load_style(style)

    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True)
    for template in dest.rglob("*.tmpl"):
        template.rename(template.with_suffix(""))
    if example:
        shutil.copytree(EXAMPLE, dest, dirs_exist_ok=True)
        placeholder_toc_art(dest / "figures" / "toc-art.png")
    (dest / "_journal.yml").write_text(journal_yml(journal, ms_type, style), encoding="utf-8")
    files = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
    return ScaffoldResult(dest, journal, ms_type, style, example, journal_name, files)
