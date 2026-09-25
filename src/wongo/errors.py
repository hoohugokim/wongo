"""User-facing errors, the engine's error channel.

Every error a person running wongo can fix is a WongoError whose message says
what to do. The CLI prints the message and exits 1; library callers (the Claude
skill through --json, tests, any future UI) catch it like any exception.

SystemExit is reserved for the CLI entry point. Raised deep in the engine it
bypasses ``except Exception``, is silently lost in worker threads, and shuts
down asyncio event loops.
"""
from __future__ import annotations


class WongoError(Exception):
    """An actionable error for the person running wongo."""

    kind = "error"


class ConfigError(WongoError):
    """_journal.yml, a journal profile, or a house style is missing or invalid."""

    kind = "config"


class InputError(WongoError):
    """A file or argument given to wongo is missing or unusable."""

    kind = "input"


class GateError(WongoError):
    """A HARD gate refused a submission render."""

    kind = "gate"


class ToolchainError(WongoError):
    """Quarto or R is missing, or failed while rendering."""

    kind = "toolchain"


class OutputLockedError(WongoError):
    """An output file is open in another program (Word locks files on Windows)."""

    kind = "locked"
