"""Shared fixtures: a fake quarto on PATH and a minimal wongo project."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

STUB = Path(__file__).with_name("stub_quarto.py")


@dataclass
class StubQuarto:
    wrapper: Path
    log: Path

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line)["argv"] for line in self.log.read_text(encoding="utf-8").splitlines()]

    def renders(self) -> list[list[str]]:
        return [argv for argv in self.calls() if argv[:1] == ["render"]]


@pytest.fixture
def stub_quarto(tmp_path, monkeypatch) -> StubQuarto:
    """Put a fake `quarto` first on PATH (and in WONGO_QUARTO)."""
    bindir = tmp_path / "stub-bin"
    bindir.mkdir()
    if os.name == "nt":
        wrapper = bindir / "quarto.bat"
        wrapper.write_text(f'@echo off\r\n"{sys.executable}" "{STUB}" %*\r\n', encoding="utf-8")
    else:
        wrapper = bindir / "quarto"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{STUB}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
    log = tmp_path / "stub-quarto.log"
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ.get("PATH", ""))
    monkeypatch.setenv("WONGO_QUARTO", str(wrapper))
    monkeypatch.setenv("WONGO_STUB_QUARTO_LOG", str(log))
    monkeypatch.delenv("WONGO_STUB_QUARTO_FAIL", raising=False)
    return StubQuarto(wrapper=wrapper, log=log)


def make_wongo_project(
    root: Path,
    *,
    name: str = "paper",
    word_limit: int = 500,
    toc_required: bool = False,
    si: bool = True,
    body: str = "Body text cites @doe2020 and shows @fig-demo.",
) -> Path:
    """A project with a project-local `demo` profile, so tests never depend on
    the packaged journal profiles."""
    project = root / name
    (project / "profiles" / "demo").mkdir(parents=True)
    (project / "_journal.yml").write_text(
        "journal: demo\nms_type: article\nstyle: default\n", encoding="utf-8")
    (project / "_quarto.yml").write_text(
        "project:\n  type: default\n  output-dir: output\n"
        "format:\n  docx:\n    number-sections: false\nbibliography: refs.bib\n",
        encoding="utf-8")
    (project / "profiles" / "demo" / "profile.yml").write_text(
        "slug: demo\njournal: Demo Journal\npublisher: Demo\n"
        "manuscript_types:\n"
        f"  - {{type: article, word_limit: {word_limit}, counting_rule: \"body plus abstract\"}}\n"
        "line_numbers: false\n"
        f"toc_graphic: {{required: {str(toc_required).lower()}, width_mm: 80, height_mm: 40}}\n"
        "si: {separate_file: true, page_prefix: S, needs_cover_sheet: true}\n"
        "sources: [https://example.org/guide]\n"
        f"verified_date: {date.today().isoformat()}\n",
        encoding="utf-8")
    (project / "index.qmd").write_text(
        "---\ntitle: A Demo Manuscript\nauthor:\n  - name: Ada Author\n"
        "abstract: |\n  Short abstract here.\n---\n\n# Introduction\n\n"
        f"{body}\n\n![A demo figure.](figures/demo.png){{#fig-demo}}\n",
        encoding="utf-8")
    (project / "figures").mkdir()
    (project / "figures" / "demo.png").write_bytes(b"not really a png")
    (project / "refs.bib").write_text(
        "@article{doe2020,\n  title = {A Title},\n  author = {Doe, Jane},\n  year = {2020},\n}\n",
        encoding="utf-8")
    if si:
        (project / "si.qmd").write_text(
            "---\ntitle: Supporting Information\n---\n\n# Supplementary Methods\n\nSI text.\n",
            encoding="utf-8")
    return project


@pytest.fixture
def wongo_project(tmp_path) -> Path:
    return make_wongo_project(tmp_path)


def run_cli(argv: list[str], capsys) -> tuple[int, str, str]:
    """Run `wongo <argv>` in-process; SystemExit and return codes both map to
    an exit code, and a SystemExit message lands on stderr like the real CLI."""
    from wongo.cli import main

    try:
        code = main(argv)
    except SystemExit as exc:
        if isinstance(exc.code, int) or exc.code is None:
            code = exc.code or 0
        else:
            print(exc.code, file=sys.stderr)
            code = 1
    out, err = capsys.readouterr()
    return code, out, err


@pytest.fixture
def project_factory(tmp_path):
    def make(**kwargs) -> Path:
        return make_wongo_project(tmp_path, **kwargs)

    return make


@pytest.fixture
def cli(capsys):
    """cli("render", "--target", "collab") -> (exit_code, stdout, stderr)."""

    def run(*argv: str) -> tuple[int, str, str]:
        return run_cli(list(argv), capsys)

    return run
