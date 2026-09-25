"""Helpers shared by CLI command modules: JSON output and prompt gating.

Every command accepts --json and then prints exactly one JSON object on stdout:
``{"command": ..., "wongo": <version>, "ok": <bool>, ...}``; errors become
``{"ok": false, "error": {"kind": ..., "message": ...}}`` with exit code 1 (2 for
a usage error, 130 for Ctrl-C; kind "internal" is a wongo bug and carries a
"traceback"). The Claude skill and scripts read this instead of parsing prose.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

from wongo import __version__


def to_jsonable(value):
    """Convert dataclasses, paths, dates and containers into JSON types."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    return value


def emit_json(command: str, ok: bool, **payload) -> None:
    body = {"command": command, "wongo": __version__, "ok": ok}
    body.update({k: to_jsonable(v) for k, v in payload.items()})
    print(json.dumps(body, ensure_ascii=False, indent=2))


def is_interactive() -> bool:
    """Whether a person is at a terminal. Prompts must never appear otherwise:
    CI, the byte-compare harness, and the Claude agent have no TTY, and a
    prompt would hang them. WONGO_NO_PROMPT=1 forces non-interactive mode."""
    if os.environ.get("WONGO_NO_PROMPT"):
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def display_path(path: Path) -> Path:
    """`path` relative to the current folder when it lies inside it: shorter to
    read and to paste into the next command."""
    path = Path(path)
    try:
        return path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        return path
