"""`wongo doctor`: is this computer (and this project) ready to render?

Each finding is a Check (HARD = must fix before rendering, WARN = may cause
trouble). The findings name the exact fix for the platform they run on, since
the people most likely to run this are new to the toolchain.
"""
from __future__ import annotations

import locale
import os
import platform
import shutil
import sys
from pathlib import Path

import yaml

from wongo import __version__, toolchain
from wongo.engine.checks import Check
from wongo.errors import WongoError
from wongo.textio import read_text

R_UTF8_VERSION = (4, 2)  # R on Windows uses UTF-8 natively from 4.2 (UCRT)


def _version_tuple(text: str | None) -> tuple[int, ...]:
    if not text:
        return ()
    return tuple(int(p) for p in text.split(".") if p.isdigit())


def _project_engine(project: Path) -> str | None:
    config = project / "_quarto.yml"
    if not config.exists():
        return None
    try:
        data = yaml.safe_load(read_text(config)) or {}
    except (yaml.YAMLError, WongoError):
        return None
    return data.get("engine") if isinstance(data, dict) else None


def _render_hooks(project: Path) -> list[str]:
    config = project / "_quarto.yml"
    try:
        data = yaml.safe_load(read_text(config)) or {}
    except (OSError, yaml.YAMLError, WongoError):
        return []
    hooks = []
    section = (data.get("project") or {}) if isinstance(data, dict) else {}
    for key in ("pre-render", "post-render"):
        value = section.get(key) or []
        hooks += [str(v) for v in (value if isinstance(value, list) else [value])]
    return hooks


def quarto_checks() -> list[Check]:
    try:
        tool = toolchain.find_quarto()
    except WongoError as exc:
        return [Check("quarto", "HARD", False, str(exc))]
    if tool is None:
        return [Check("quarto", "HARD", False, toolchain.missing_quarto_message())]
    version = toolchain.tool_version([tool.path])
    checks = [Check("quarto", "HARD", version is not None,
                    f"Quarto {version} at {tool.path}" if version
                    else f"{tool.path} was found but did not run; reinstall Quarto: "
                         f"{toolchain.install_hint('quarto')}")]
    if version and not toolchain.quarto_version_tested(version):
        checks.append(Check(
            "quarto-version", "WARN", False,
            f"Quarto {version} is untested; wongo's output is verified with "
            f"{toolchain.TESTED_QUARTO}.x (renders usually work, but compare before submitting)",
        ))
    if tool.source == "known location":
        checks.append(Check(
            "quarto-path", "WARN", False,
            f"Quarto is not on PATH (found at {tool.path}); wongo will use it, but open a new "
            "terminal after installing, or set WONGO_QUARTO to that path",
        ))
    return checks


def r_checks(required: bool) -> list[Check]:
    level = "HARD" if required else "WARN"
    tool = toolchain.find_rscript()
    if tool is None:
        return [Check("r", level, False,
                      f"R was not found (needed for knitr manuscripts). Install: "
                      f"{toolchain.install_hint('r')}")]
    report = toolchain.probe_r(tool)
    if report.version is None:
        return [Check("r", level, False, f"{tool.path} did not run; reinstall R: "
                                         f"{toolchain.install_hint('r')}")]
    checks = [Check("r", level, True, f"R {report.version} at {tool.path} ({tool.source})")]
    for pkg in toolchain.R_REQUIRED:
        version = report.packages.get(pkg)
        checks.append(Check(
            f"r-{pkg}", level, version is not None,
            f"{pkg} {version}" if version else
            f"R package {pkg} is missing; run: Rscript -e \"install.packages('{pkg}', "
            "repos='https://cloud.r-project.org')\"",
        ))
    for pkg in toolchain.R_OPTIONAL:
        version = report.packages.get(pkg)
        checks.append(Check(
            f"r-{pkg}", "WARN", version is not None,
            f"{pkg} {version}" if version else
            f"R package {pkg} is missing (only needed if inline numbers read JSON files)",
        ))
    if toolchain.platform_name() == "windows" and _version_tuple(report.version) < R_UTF8_VERSION:
        checks.append(Check(
            "r-utf8", "WARN", False,
            f"R {report.version} on Windows is not UTF-8 native; Korean text in .qmd files can "
            "garble. Install R 4.2 or newer.",
        ))
    return checks


def system_checks(project: Path | None) -> list[Check]:
    checks = [Check("wongo", "HARD", True,
                    f"wongo {__version__} on Python {platform.python_version()} ({sys.executable})")]
    encoding = locale.getpreferredencoding(False)
    checks.append(Check("text-encoding", "WARN", True,
                        f"locale encoding {encoding}; wongo reads and writes UTF-8 regardless"))
    if toolchain.platform_name() == "windows":
        home = str(Path.home())
        if not home.isascii():
            checks.append(Check(
                "home-path", "WARN", False,
                f"your user folder ({home}) has non-ASCII characters; if R package installs "
                "fail, set R_LIBS_USER to an ASCII folder such as C:\\Rlibs",
            ))
        if project is not None and len(str(project)) > 200:
            checks.append(Check(
                "long-path", "WARN", False,
                f"the project path is {len(str(project))} characters; Windows tools can fail "
                "beyond 260, so prefer a shorter folder such as C:\\papers\\<name>",
            ))
    if project is not None and toolchain.platform_name() == "windows":
        reason = toolchain.unrenderable_path_reason(project)
        checks.append(Check("project-path", "HARD", reason is None,
                            "Quarto can render in this folder" if reason is None else reason))
    if project is not None and any(part.lower().startswith("onedrive") for part in project.parts):
        checks.append(Check(
            "sync-folder", "WARN", False,
            "the project is inside OneDrive; syncing can lock output files mid-render. "
            "If renders fail with 'open in another program', pause sync or move the project",
        ))
    return checks


def project_checks(project: Path) -> list[Check]:
    from wongo.profiles import (
        load_journal_config,
        load_profile,
        manuscript_type,
        profile_staleness_days,
        validate_profile,
    )
    from wongo.styles import load_style

    try:
        cfg = load_journal_config(project)
        profile = load_profile(cfg["journal"], project)
        mtype = manuscript_type(profile, cfg["ms_type"])
        style = cfg.get("style") or os.environ.get("WONGO_STYLE") or "default"
        load_style(style)
    except WongoError as exc:
        return [Check("project-config", "HARD", False, str(exc))]
    checks = [Check("project-config", "HARD", True,
                    f"{profile.get('journal', cfg['journal'])} · {mtype.get('type')} · style {style}")]
    problems = validate_profile(profile)
    checks.append(Check("profile-contract", "HARD", not problems,
                        "profile satisfies the contract" if not problems else "; ".join(problems)))
    days = profile_staleness_days(profile)
    checks.append(Check("profile-staleness", "WARN", days is not None and 0 <= days <= 183,
                        f"profile verified {days} days ago" if days is not None
                        else "profile has no verified_date"))
    if toolchain.platform_name() == "windows":
        for hook in _render_hooks(project):
            program = hook.split()[0] if hook.split() else ""
            if program in ("python3", "python"):
                found = shutil.which(program) or ""
                if not found or "windowsapps" in found.lower():
                    checks.append(Check(
                        "render-hook", "WARN", False,
                        f"_quarto.yml runs `{hook}`, but `{program}` is "
                        f"{'the Microsoft Store placeholder' if found else 'not installed'}; "
                        "install Python (winget install --id Python.Python.3.12 -e) or use `py`",
                    ))
    return checks


def run_doctor(project: Path | None = None) -> list[Check]:
    """All findings for this computer, plus the project when given."""
    project = Path(project).resolve() if project is not None else None
    is_project = project is not None and (project / "_journal.yml").exists()
    engine = _project_engine(project) if is_project else None
    checks = system_checks(project if is_project else None)
    checks += quarto_checks()
    checks += r_checks(required=engine == "knitr")
    if is_project:
        checks += project_checks(project)
    return checks
