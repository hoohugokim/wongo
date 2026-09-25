"""Text input/output that behaves the same on Windows, macOS and Linux.

- Source files are UTF-8. A byte-order mark (older Windows Notepad adds one) is
  dropped, so front matter and the first BibTeX entry still parse; a file in
  another encoding (e.g. CP949 from an old Korean editor) is reported with the
  fix instead of a traceback.
- Console output never crashes on Hangul names or em-dashes, even when a
  Korean Windows machine redirects output through its CP949 code page.
- Files wongo rewrites are replaced atomically and keep their line endings.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from wongo.errors import InputError


def read_text(path: Path | str) -> str:
    """Read a UTF-8 text file, dropping a BOM; universal newlines."""
    path = Path(path)
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError(
            f"{path} is not UTF-8 text (invalid byte at position {exc.start}). "
            "Re-save it as UTF-8, e.g. in VS Code: 'Save with Encoding' > UTF-8."
        ) from exc


def detect_newline(raw: bytes) -> str:
    """The line ending a file uses: CRLF if it has any, else LF."""
    return "\r\n" if b"\r\n" in raw else "\n"


def write_text_atomic(path: Path | str, text: str, newline: str = "\n") -> None:
    """Write `text` (LF line endings) via a temporary file in the same folder,
    converting to `newline`, then replace the target in one step."""
    path = Path(path)
    data = text.replace("\r\n", "\n")
    if newline != "\n":
        data = data.replace("\n", newline)
    tmp = path.with_name(f".{path.name}.wongo-tmp")
    tmp.write_bytes(data.encode("utf-8"))
    os.replace(tmp, path)


def configure_stdio() -> None:
    """Make stdout/stderr unable to crash on non-ASCII text.

    An interactive Windows console already uses Unicode. A redirected stream
    falls back to the locale code page (CP949 on Korean Windows), which cannot
    encode an em-dash; it is switched to UTF-8. An explicit PYTHONIOENCODING is
    respected, only made lossy instead of fatal.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        try:
            if os.environ.get("PYTHONIOENCODING"):
                reconfigure(errors="replace")
            elif encoding != "utf8":
                reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # stream already in use in an incompatible way
            continue
