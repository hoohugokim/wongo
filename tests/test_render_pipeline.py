"""Render pipeline behaviour beyond the pinned DOCX bytes: all-or-nothing
outputs, actionable toolchain errors, the output manifest, collab Track
Changes, JSON output, and Windows/Korean-locale robustness. Quarto is replaced
by tests/stub_quarto.py (see conftest.py)."""
from __future__ import annotations

import json
import locale
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from wongo import toolchain
from wongo.engine import render_project
from wongo.errors import OutputLockedError, ToolchainError

SRC = str(Path(__file__).resolve().parents[1] / "src")


def _outputs(project: Path) -> dict[str, bytes]:
    out = project / "output"
    return {p.name: p.read_bytes() for p in sorted(out.glob("*.docx"))} if out.exists() else {}


def _leftovers(project: Path) -> list[str]:
    out = project / "output"
    return sorted(p.name for p in out.iterdir()
                  if p.name.startswith((".stage-", ".wongo-stage-")) or p.name.endswith(".wongo-bak"))


def test_render_returns_outputs_checks_and_a_manifest(stub_quarto, wongo_project):
    result = render_project(wongo_project, "collab")

    assert [p.name for p in result.outputs] == ["main-collab.docx", "si-collab.docx"]
    assert all(p.is_file() for p in result.outputs)
    assert [c.name for c in result.checks][:2] == ["word-limit", "citekeys"]
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    entry = manifest["targets"]["collab"]
    assert set(entry["outputs"]) == {"main-collab.docx", "si-collab.docx"}
    assert {"index.qmd", "si.qmd", "refs.bib", "_journal.yml", "figures/demo.png"} <= set(entry["sources"])
    assert entry["quarto"] == "1.10.18"
    assert _leftovers(wongo_project) == []


def test_a_failed_si_render_leaves_the_previous_outputs_untouched(stub_quarto, wongo_project, monkeypatch):
    render_project(wongo_project, "collab")
    before = _outputs(wongo_project)
    monkeypatch.setenv("WONGO_STUB_QUARTO_FAIL", "si.qmd")

    with pytest.raises(ToolchainError):
        render_project(wongo_project, "collab")

    assert _outputs(wongo_project) == before
    assert _leftovers(wongo_project) == []


def test_a_post_processing_crash_leaves_no_partial_deliverable(stub_quarto, wongo_project, monkeypatch):
    import wongo.engine as engine

    def boom(*args, **kwargs):
        raise RuntimeError("post-processing exploded")

    monkeypatch.setattr(engine, "postprocess_si", boom)

    with pytest.raises(RuntimeError):
        render_project(wongo_project, "collab")

    assert _outputs(wongo_project) == {}
    assert _leftovers(wongo_project) == []


def test_an_output_open_in_word_is_reported_and_nothing_changes(stub_quarto, wongo_project, monkeypatch):
    import wongo.engine as engine

    render_project(wongo_project, "collab")
    before = _outputs(wongo_project)
    locked = wongo_project.resolve() / "output" / "si-collab.docx"
    real_replace = os.replace

    def replace(src, dst):
        if Path(src) == locked:  # Windows refuses to move a file Word holds open
            raise PermissionError(13, "The process cannot access the file", str(src))
        return real_replace(src, dst)

    monkeypatch.setattr(engine.os, "replace", replace)

    with pytest.raises(OutputLockedError) as excinfo:
        render_project(wongo_project, "collab")

    assert "si-collab.docx is open in another program" in str(excinfo.value)
    monkeypatch.setattr(engine.os, "replace", real_replace)
    assert _outputs(wongo_project) == before
    assert _leftovers(wongo_project) == []


def test_a_crashed_run_leftover_is_never_taken_for_this_run_output(stub_quarto, wongo_project, monkeypatch):
    out = wongo_project / "output"
    out.mkdir()
    (out / ".wongo-stage-main-collab.docx").write_bytes(b"left by a crashed run")
    monkeypatch.setenv("WONGO_STUB_QUARTO_FAIL", "index.qmd")

    with pytest.raises(ToolchainError):
        render_project(wongo_project, "collab")

    assert _outputs(wongo_project) == {}


def test_missing_quarto_is_an_actionable_error(wongo_project, monkeypatch):
    monkeypatch.delenv("WONGO_QUARTO", raising=False)
    monkeypatch.setattr(toolchain, "find_quarto", lambda: None)

    with pytest.raises(ToolchainError) as excinfo:
        render_project(wongo_project, "collab")

    message = str(excinfo.value)
    assert "Quarto was not found" in message
    assert toolchain.install_hint("quarto").split()[0] in message
    assert "NEW terminal" in message


def test_quarto_metadata_paths_use_forward_slashes(stub_quarto, wongo_project):
    profile = wongo_project / "profiles" / "demo" / "profile.yml"
    profile.write_text(profile.read_text(encoding="utf-8")
                       + "reference_doc: assets/reference.docx\ncsl: assets/style.csl\n",
                       encoding="utf-8")

    render_project(wongo_project, "collab")

    argv = stub_quarto.renders()[0]
    metadata = [argv[i + 1] for i, a in enumerate(argv) if a == "-M"]
    assert [m.split(":", 1)[0] for m in metadata] == ["reference-doc", "csl"]
    assert all("\\" not in m for m in metadata)


def test_collab_opens_with_track_changes_on_and_submission_does_not(stub_quarto, wongo_project):
    render_project(wongo_project, "collab")
    render_project(wongo_project, "submission")

    def settings(name):
        with zipfile.ZipFile(wongo_project / "output" / name) as z:
            return z.read("word/settings.xml").decode("utf-8")

    for name in ("main-collab.docx", "si-collab.docx"):
        assert "<w:trackRevisions/>" in settings(name)
    for name in ("main-submission.docx", "si-submission.docx", "main-collab.docx"):
        assert "<w:trackChanges" not in settings(name)
    assert "<w:trackRevisions" not in settings("main-submission.docx")


def test_render_summary_names_hard_failures_on_a_collab_render(cli, stub_quarto, project_factory):
    project = project_factory(body="Body text cites @ghost2099.")

    code, out, err = cli("render", "--target", "collab", "--project", str(project))

    assert code == 0, err
    last = out.splitlines()[-1]
    assert last.startswith("checks: ")
    assert "HARD FAIL: citekeys" in last
    assert "not submission-ready" in last


def test_render_json_prints_one_object_and_keeps_quarto_off_stdout(cli, stub_quarto, wongo_project):
    code, out, err = cli("render", "--target", "collab", "--project", str(wongo_project), "--json")

    assert code == 0, err
    body = json.loads(out)
    assert body["command"] == "render" and body["ok"] is True
    assert [Path(p).name for p in body["outputs"]] == ["main-collab.docx", "si-collab.docx"]
    assert {c["name"] for c in body["checks"]} >= {"word-limit", "citekeys"}


def test_a_refused_render_in_json_mode_reports_the_gate(cli, stub_quarto, project_factory):
    project = project_factory(word_limit=3)

    code, out, err = cli("render", "--target", "submission", "--project", str(project), "--json")

    assert code == 1
    body = json.loads(out)
    assert body["ok"] is False
    assert body["error"]["kind"] == "gate"
    assert "submission render refused" in body["error"]["message"]
    failing = [c["name"] for c in body["checks"] if c["level"] == "HARD" and not c["ok"]]
    assert failing == ["word-limit"]  # the agent can see what to fix


def test_check_json(cli, wongo_project):
    code, out, err = cli("check", "--project", str(wongo_project), "--json")

    body = json.loads(out)
    assert code == 0 and body["ok"] is True
    assert body["checks"][0]["name"] == "word-limit"
    assert body["checks"][0]["locations"] == []


def test_roundtrip_keeps_hangul_from_pandoc(cli, stub_quarto, wongo_project, tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text(
        '# Introduction\n\nBody text at 25 °C [수정]{.insertion author="김하나" '
        'date="2026-09-01T00:00:00Z"} cites the work.\n', encoding="utf-8")
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(markdown))
    coauthor = tmp_path / "coauthor.docx"
    coauthor.write_bytes(b"placeholder")

    code, out, err = cli("roundtrip", str(coauthor), "--project", str(wongo_project))

    assert code == 0, err
    worksheet = next((wongo_project / "decisions").glob("merge-*-coauthor.md"))
    text = worksheet.read_text(encoding="utf-8")
    assert "## 1. insertion — 김하나" in text
    assert "- new: 수정" in text
    assert "°C" in text


def _korean_locale() -> str | None:
    for name in ("ko_KR.CP949", "ko_KR.EUC-KR", "ko_KR.eucKR"):
        try:
            previous = locale.setlocale(locale.LC_CTYPE)
            locale.setlocale(locale.LC_CTYPE, name)
            locale.setlocale(locale.LC_CTYPE, previous)
            return name
        except locale.Error:
            continue
    return None


@pytest.mark.skipif(os.name == "nt" or _korean_locale() is None,
                    reason="needs a POSIX system with a Korean legacy locale")
def test_roundtrip_and_report_work_under_a_korean_legacy_locale(stub_quarto, wongo_project, tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text('Body at 25 °C [수정]{.insertion author="김하나" date="2026-09-01T00:00:00Z"} ok.\n',
                        encoding="utf-8")
    coauthor = tmp_path / "coauthor.docx"
    coauthor.write_bytes(b"placeholder")
    env = dict(os.environ, LC_ALL=_korean_locale(), PYTHONUTF8="0",
               WONGO_STUB_PANDOC_MD_FILE=str(markdown), PYTHONPATH=SRC)
    env.pop("PYTHONIOENCODING", None)

    done = subprocess.run([sys.executable, "-m", "wongo.cli", "roundtrip", str(coauthor),
                           "--project", str(wongo_project)],
                          capture_output=True, env=env, timeout=120)

    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    assert "NONE applied — review" in done.stdout.decode("utf-8")
    worksheet = next((wongo_project / "decisions").glob("merge-*-coauthor.md"))
    assert "김하나" in worksheet.read_text(encoding="utf-8")
    assert "°C" in worksheet.read_text(encoding="utf-8")


def test_reports_survive_a_non_utf8_output_encoding(wongo_project):
    env = dict(os.environ, PYTHONIOENCODING="cp949", PYTHONPATH=SRC)

    done = subprocess.run([sys.executable, "-m", "wongo.cli", "profile", "show", "est"],
                          capture_output=True, env=env, timeout=120)

    assert done.returncode == 0, done.stderr.decode("cp949", "replace")


def test_no_command_waits_for_input_without_a_terminal(tmp_path):
    env = dict(os.environ, PYTHONPATH=SRC)
    env.pop("WONGO_NO_PROMPT", None)

    done = subprocess.run([sys.executable, "-m", "wongo.cli", "scaffold", str(tmp_path / "new")],
                          stdin=subprocess.DEVNULL, capture_output=True, env=env, timeout=60)

    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    assert (tmp_path / "new" / "_journal.yml").is_file()


# ---------------------------------------------------------------------------
# Quarto on Windows converts file paths to the ANSI code page in its Lua
# filters; a folder name outside that code page crashes the render.


def _windows_codepage(monkeypatch, codepage: str) -> None:
    monkeypatch.setattr(toolchain, "platform_name", lambda: "windows")
    monkeypatch.setattr(toolchain.locale, "getencoding", lambda: codepage)


def test_windows_render_refuses_a_folder_outside_the_code_page(stub_quarto, project_factory, monkeypatch):
    project = project_factory(name="원고 예제")
    _windows_codepage(monkeypatch, "cp1252")

    with pytest.raises(ToolchainError) as excinfo:
        render_project(project, "collab")

    message = str(excinfo.value)
    assert "code page (cp1252)" in message
    assert "(here: '원고')" in message
    assert stub_quarto.renders() == []


@pytest.mark.parametrize("codepage", ["cp949", "utf-8", "cp65001"])
def test_windows_render_accepts_hangul_where_the_code_page_has_it(stub_quarto, project_factory, monkeypatch, codepage):
    project = project_factory(name="원고 예제")
    _windows_codepage(monkeypatch, codepage)

    result = render_project(project, "collab")

    assert [p.name for p in result.outputs] == ["main-collab.docx", "si-collab.docx"]


def test_doctor_flags_a_project_folder_quarto_cannot_render_in(stub_quarto, project_factory, monkeypatch):
    from wongo import doctor

    project = project_factory(name="원고 예제")
    _windows_codepage(monkeypatch, "cp1252")
    monkeypatch.setattr(toolchain, "find_rscript", lambda: None)

    checks = {c.name: c for c in doctor.run_doctor(project)}

    assert checks["project-path"].level == "HARD" and not checks["project-path"].ok
