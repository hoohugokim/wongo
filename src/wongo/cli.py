"""wongo CLI — scaffold-phase implementation.

During the uplift (see HANDOFF-wongo-uplift.md) the battle-tested legacy
scripts under legacy/ ARE the engine; this CLI locates the repo checkout,
points profile resolution at the bundled profiles/ tree via QM_SKILLS_DIR,
and delegates. The proper package modules (wongo.engine / wongo.docxpatch /
wongo.profiles) replace this delegation incrementally — behavior is pinned by
tests/ and by byte-comparison against the the reference manuscript manuscript renders.

Scaffold-phase install: `uv tool install --editable ~/workbench/wongo`
(a non-editable wheel install will refuse to run until the engine migration
lands, because legacy/ and profiles/ live outside the package).
"""
from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

COMMANDS = {
    "render": ("render.py", "Render collab- or submission-grade DOCX (main + SI)"),
    "check": ("validate.py", "Run validation checks (word limit, citekeys, crossrefs, figures)"),
    "roundtrip": ("roundtrip.py", "Extract a coauthor DOCX's tracked changes into a merge worksheet"),
}


def repo_root() -> Path:
    """Walk up from this file to the checkout root (scaffold phase only)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "legacy" / "render.py").exists():
            return parent
    raise SystemExit(
        "wongo is installed without its legacy/ engine (scaffold phase needs an "
        "editable install of the repo checkout): uv tool install --editable <repo>"
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="wongo",
        description="wongo (원고) — Quarto manuscript pipeline: verified journal "
        "profiles, submission-grade DOCX, Word-coauthor round-tripping.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (_, help_text) in COMMANDS.items():
        sub.add_parser(name, help=help_text, add_help=False)
    args, passthrough = parser.parse_known_args(argv)

    root = repo_root()
    script = root / "legacy" / COMMANDS[args.command][0]
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script)] + passthrough
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
