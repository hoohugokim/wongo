"""External toolchain discovery: Quarto, and R for knitr-engine manuscripts.

Resolution follows what a non-technical user's machine actually looks like:

- Installers add Quarto to PATH only for terminals opened AFTER the install,
  so a known install location is tried when PATH has no quarto.
- winget's R installer never touches PATH; Quarto itself finds R through the
  Windows registry (or QUARTO_R), so wongo looks in the same places.
- RStudio and Positron bundle their own Quarto.

Every executable is resolved to a full path before it is run: on Windows,
CreateProcess does not search PATHEXT, so a bare "quarto" can miss a quarto.cmd
that the shell would find.
"""
from __future__ import annotations

import locale
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from wongo.errors import ToolchainError

# Render output is byte-pinned against Quarto 1.10.x (the reference manuscript
# was verified with 1.10.18); other versions work but are untested.
TESTED_QUARTO = "1.10"
R_REQUIRED = ("knitr", "rmarkdown")
R_OPTIONAL = ("jsonlite",)
QUARTO_DOWNLOAD = "https://quarto.org/docs/get-started/"
R_DOWNLOAD = "https://cloud.r-project.org/"


def platform_name() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


INSTALL_HINTS = {
    "quarto": {
        "windows": f"winget install --id Posit.Quarto -e   (or the installer from {QUARTO_DOWNLOAD})",
        "macos": f"brew install --cask quarto   (or the installer from {QUARTO_DOWNLOAD})",
        "linux": f"the .deb or tarball from {QUARTO_DOWNLOAD}",
    },
    "r": {
        "windows": f"winget install --id RProject.R -e   (or the installer from {R_DOWNLOAD})",
        "macos": f"brew install --cask r   (or the installer from {R_DOWNLOAD})",
        "linux": f"your distribution's r-base package (see {R_DOWNLOAD})",
    },
}


def install_hint(tool: str) -> str:
    return INSTALL_HINTS[tool][platform_name()]


@dataclass(frozen=True)
class Tool:
    path: str
    source: str  # WONGO_QUARTO | QUARTO_R | PATH | registry | known location


# ---------------------------------------------------------------------------
# Quarto


def quarto_candidates() -> list[Path]:
    """Known Quarto locations when PATH has none, most specific first."""
    name = platform_name()
    if name == "windows":
        roots = [Path(os.environ.get(v)) for v in ("ProgramFiles", "LOCALAPPDATA")
                 if os.environ.get(v)]
        program_files = roots[0] if roots else Path(r"C:\Program Files")
        local = Path(os.environ["LOCALAPPDATA"]) if os.environ.get("LOCALAPPDATA") else None
        cands = [
            program_files / "Quarto" / "bin" / "quarto.exe",
            program_files / "RStudio" / "resources" / "app" / "bin" / "quarto" / "bin" / "quarto.exe",
            program_files / "Positron" / "resources" / "app" / "quarto" / "bin" / "quarto.exe",
        ]
        if local is not None:
            cands += [
                local / "Programs" / "Quarto" / "bin" / "quarto.exe",
                local / "Programs" / "Positron" / "resources" / "app" / "quarto" / "bin" / "quarto.exe",
            ]
        return cands
    if name == "macos":
        return [Path(p) for p in (
            "/Applications/quarto/bin/quarto",
            "/usr/local/bin/quarto",
            "/opt/homebrew/bin/quarto",
            "/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto",
            "/Applications/Positron.app/Contents/Resources/app/quarto/bin/quarto",
        )]
    return [Path(p) for p in (
        "/opt/quarto/bin/quarto",
        "/usr/local/bin/quarto",
        "/usr/lib/rstudio/resources/app/bin/quarto/bin/quarto",
        "/usr/lib/positron/resources/app/quarto/bin/quarto",
    )]


def find_quarto() -> Tool | None:
    override = os.environ.get("WONGO_QUARTO")
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise ToolchainError(
                f"WONGO_QUARTO is set to {path}, which does not exist. "
                "Point it at the quarto executable or unset it."
            )
        return Tool(str(path), "WONGO_QUARTO")
    found = shutil.which("quarto")
    if found:
        return Tool(found, "PATH")
    for candidate in quarto_candidates():
        if candidate.is_file():
            return Tool(str(candidate), "known location")
    return None


def missing_quarto_message() -> str:
    return (
        f"Quarto was not found. wongo renders with Quarto {TESTED_QUARTO}.x.\n"
        f"  Install it: {install_hint('quarto')}\n"
        "  Then open a NEW terminal window (installers change PATH for new windows only)\n"
        "  and run `wongo doctor`. If Quarto lives somewhere unusual, set WONGO_QUARTO\n"
        "  to the full path of the quarto executable."
    )


def quarto_command() -> list[str]:
    """The argv prefix that runs Quarto; raises ToolchainError with install help."""
    tool = find_quarto()
    if tool is None:
        raise ToolchainError(missing_quarto_message())
    return [tool.path]


def tool_version(cmd: list[str], args: tuple[str, ...] = ("--version",),
                 timeout: float = 60) -> str | None:
    """First dotted version number a tool prints, or None if it cannot run."""
    try:
        done = subprocess.run([*cmd, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    match = re.search(r"\d+\.\d+(?:\.\d+)?", done.stdout + done.stderr)
    return match.group(0) if match else None


def windows_codepage() -> str | None:
    """The ANSI code page Windows programs use for file names (Quarto's Lua
    filters convert paths to it), or None off Windows."""
    if platform_name() != "windows":
        return None
    return locale.getencoding()


def unrenderable_path_reason(path: Path) -> str | None:
    """Why Quarto cannot render in `path` on this Windows machine, or None.

    Quarto 1.10's Lua filters convert paths to the ANSI code page before
    opening files; a character outside it (e.g. Hangul on a Western-locale
    Windows, where the code page is cp1252) crashes the render with a Lua
    traceback. Korean Windows (cp949) and the system-wide UTF-8 option are
    fine."""
    codepage = windows_codepage()
    if not codepage or codepage.lower().replace("-", "") in ("utf8", "cp65001"):
        return None
    text = str(path)
    try:
        text.encode(codepage)
    except UnicodeEncodeError as exc:
        return (
            f"Quarto on Windows cannot render inside a folder whose path has characters "
            f"your system code page ({codepage}) cannot represent (here: {text[exc.start:exc.end]!r}):\n"
            f"  {text}\n"
            "  Move or rename the project folder to use only English letters, digits, '-' and '_'\n"
            "  (e.g. C:\\papers\\wetland-study), or turn on 'Beta: Use Unicode UTF-8 for worldwide\n"
            "  language support' in Windows Settings > Time & language > Language & region >\n"
            "  Administrative language settings, then restart."
        )
    except LookupError:
        return None
    return None


def quarto_version_tested(version: str | None) -> bool:
    return bool(version) and (version == TESTED_QUARTO or version.startswith(TESTED_QUARTO + "."))


# ---------------------------------------------------------------------------
# R


def _windows_registry_r_homes() -> list[Path]:  # pragma: no cover - Windows only
    try:
        import winreg
    except ImportError:
        return []
    homes = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for key in (r"SOFTWARE\R-core\R", r"SOFTWARE\R-core\R64"):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    value, _ = winreg.QueryValueEx(handle, "InstallPath")
                    homes.append(Path(value))
            except OSError:
                continue
    return homes


def _version_key(path: Path) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", path.name)) or (0,)


def rscript_candidates() -> list[Tool]:
    """Where Quarto would find R, in the order it looks."""
    exe = "Rscript.exe" if platform_name() == "windows" else "Rscript"
    cands: list[Tool] = []
    quarto_r = os.environ.get("QUARTO_R")
    if quarto_r:
        base = Path(quarto_r).expanduser()
        for p in (base, base / exe, base / "bin" / exe):
            cands.append(Tool(str(p), "QUARTO_R"))
    found = shutil.which("Rscript")
    if found:
        cands.append(Tool(found, "PATH"))
    name = platform_name()
    if name == "windows":
        for home in _windows_registry_r_homes():
            for p in (home / "bin" / exe, home / "bin" / "x64" / exe):
                cands.append(Tool(str(p), "registry"))
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        for home in sorted((program_files / "R").glob("R-*"), key=_version_key, reverse=True):
            cands.append(Tool(str(home / "bin" / exe), "known location"))
    elif name == "macos":
        for p in ("/Library/Frameworks/R.framework/Resources/bin/Rscript",
                  "/opt/homebrew/bin/Rscript", "/usr/local/bin/Rscript"):
            cands.append(Tool(p, "known location"))
    else:
        cands.append(Tool("/usr/bin/Rscript", "known location"))
    return cands


def find_rscript() -> Tool | None:
    for tool in rscript_candidates():
        if Path(tool.path).is_file():
            return tool
    return None


_R_PROBE = (
    "cat('R', as.character(getRversion()), '\\n'); "
    "for (p in c({pkgs})) cat(p, if (requireNamespace(p, quietly = TRUE)) "
    "as.character(utils::packageVersion(p)) else 'MISSING', '\\n')"
)


@dataclass
class RReport:
    version: str | None
    packages: dict[str, str | None] = field(default_factory=dict)  # name -> version or None


def probe_r(rscript: Tool, timeout: float = 120) -> RReport:
    """R's version and which knitr-related packages it can load."""
    pkgs = ", ".join(f"'{p}'" for p in (*R_REQUIRED, *R_OPTIONAL))
    try:
        done = subprocess.run([rscript.path, "-e", _R_PROBE.replace("{pkgs}", pkgs)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return RReport(version=None)
    report = RReport(version=None)
    for line in done.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "R":
            report.version = parts[1]
        elif len(parts) >= 2 and parts[0] in (*R_REQUIRED, *R_OPTIONAL):
            report.packages[parts[0]] = None if parts[1] == "MISSING" else parts[1]
    return report
