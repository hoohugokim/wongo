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
from docx import Document

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


def _manifest_bytes(project: Path) -> bytes | None:
    path = project / "output" / ".wongo-manifest.json"
    return path.read_bytes() if path.exists() else None


def test_an_interrupt_while_swapping_outputs_puts_the_previous_ones_back(
        stub_quarto, wongo_project, monkeypatch):
    import wongo.engine as engine

    render_project(wongo_project, "collab")
    before, manifest = _outputs(wongo_project), _manifest_bytes(wongo_project)
    real_replace = os.replace

    def replace(src, dst):
        if Path(dst).name == ".si-collab.docx.wongo-bak":  # Ctrl-C mid-swap
            raise KeyboardInterrupt
        return real_replace(src, dst)

    monkeypatch.setattr(engine.os, "replace", replace)
    with pytest.raises(KeyboardInterrupt):
        render_project(wongo_project, "collab")
    monkeypatch.setattr(engine.os, "replace", real_replace)

    assert _outputs(wongo_project) == before
    assert _manifest_bytes(wongo_project) == manifest
    assert _leftovers(wongo_project) == []


def test_a_non_lock_os_error_while_moving_outputs_in_is_actionable_and_rolled_back(
        stub_quarto, wongo_project, monkeypatch):
    import wongo.engine as engine
    from wongo.errors import WongoError

    render_project(wongo_project, "collab")
    before, manifest = _outputs(wongo_project), _manifest_bytes(wongo_project)
    real_replace = os.replace

    def replace(src, dst):
        if Path(src).parent.name == ".stage-collab" and Path(dst) == wongo_project.resolve() / "output" / "si-collab.docx":
            raise OSError(22, "The cloud file provider is not running", str(dst))
        return real_replace(src, dst)

    monkeypatch.setattr(engine.os, "replace", replace)
    with pytest.raises(WongoError) as excinfo:
        render_project(wongo_project, "collab")
    monkeypatch.setattr(engine.os, "replace", real_replace)

    assert "si-collab.docx" in str(excinfo.value)
    assert "output/ was left unchanged" in str(excinfo.value)
    assert _outputs(wongo_project) == before
    assert _manifest_bytes(wongo_project) == manifest
    assert _leftovers(wongo_project) == []


def test_an_edit_saved_while_quarto_runs_leaves_the_output_stale(stub_quarto, wongo_project, monkeypatch):
    from wongo.engine import output_freshness

    monkeypatch.setenv("WONGO_STUB_QUARTO_EDIT", str(wongo_project / "index.qmd"))
    render_project(wongo_project, "collab")

    assert output_freshness(wongo_project, "collab")["state"] == "stale"


def test_the_manifest_moves_in_with_the_outputs_or_not_at_all(stub_quarto, wongo_project, monkeypatch):
    import wongo.engine as engine
    from wongo.engine import output_freshness

    render_project(wongo_project, "collab")
    before, manifest = _outputs(wongo_project), _manifest_bytes(wongo_project)
    real_write = engine.write_text_atomic

    def write(path, *args, **kwargs):
        if Path(path).name == ".wongo-manifest.json":
            raise PermissionError(13, "Access is denied", str(path))
        return real_write(path, *args, **kwargs)

    monkeypatch.setattr(engine, "write_text_atomic", write)
    monkeypatch.setenv("WONGO_STUB_QUARTO_STAMP", "second render")  # new bytes this time
    with pytest.raises(OSError):
        render_project(wongo_project, "collab")
    monkeypatch.setattr(engine, "write_text_atomic", real_write)

    assert _outputs(wongo_project) == before
    assert _manifest_bytes(wongo_project) == manifest
    assert output_freshness(wongo_project, "collab")["state"] == "fresh"
    assert _leftovers(wongo_project) == []


def test_a_quarto_failure_after_writing_leaves_no_staged_file(stub_quarto, wongo_project, monkeypatch):
    monkeypatch.setenv("WONGO_STUB_QUARTO_FAIL_AFTER_WRITE", "index.qmd")

    with pytest.raises(ToolchainError):
        render_project(wongo_project, "collab")

    assert _leftovers(wongo_project) == []
    assert _outputs(wongo_project) == {}


def test_a_leftover_staged_file_open_in_word_is_reported(stub_quarto, wongo_project, monkeypatch):
    out = wongo_project / "output"
    out.mkdir()
    leftover = out / ".wongo-stage-main-collab.docx"
    leftover.write_bytes(b"left by an interrupted run, then opened in Word")
    real_unlink = Path.unlink

    def unlink(self, missing_ok=False):
        if self.name == leftover.name:
            raise PermissionError(13, "The process cannot access the file", str(self))
        return real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises(OutputLockedError) as excinfo:
        render_project(wongo_project, "collab")

    assert ".wongo-stage-main-collab.docx" in str(excinfo.value)


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


# ---------------------------------------------------------------------------
# --json: exactly one object on stdout, whatever goes wrong


def test_a_front_matter_typo_is_an_input_error_naming_file_and_line(cli, stub_quarto, project_factory):
    project = project_factory()
    index = project / "index.qmd"
    index.write_text(index.read_text(encoding="utf-8").replace(
        "title: A Demo Manuscript", "title: Wetlands: a study"), encoding="utf-8")

    for argv in (("check", "--project", str(project), "--json"),
                 ("render", "--target", "collab", "--project", str(project), "--json")):
        code, out, err = cli(*argv)
        body = json.loads(out)
        assert code == 1 and body["ok"] is False, argv
        assert body["command"] == argv[0]
        assert body["error"]["kind"] == "input"
        assert "index.qmd line 2" in body["error"]["message"]
        assert 'title: "Wetlands: a study"' in body["error"]["message"]

    code, out, err = cli("status", "--project", str(project), "--json")
    body = json.loads(out)
    assert body["ok"] is False
    assert "index.qmd line 2" in body["status"]["config_error"]


def test_usage_errors_in_json_mode_are_json(cli):
    code, out, err = cli("render", "--json")

    body = json.loads(out)
    assert code == 2
    assert body["ok"] is False and body["command"] == "render"
    assert body["error"]["kind"] == "usage"
    assert "--target" in body["error"]["message"]


def test_json_before_the_command_works_too(cli, wongo_project):
    code, out, err = cli("--json", "check", "--project", str(wongo_project))

    assert code == 0
    assert json.loads(out)["command"] == "check"


def test_a_file_that_is_not_a_docx_is_an_input_error(cli, stub_quarto, wongo_project, tmp_path):
    fake = tmp_path / "notes.docx"
    fake.write_text("a text file renamed to .docx", encoding="utf-8")

    code, out, err = cli("diff", str(fake), str(fake), "-o", str(tmp_path / "out.docx"), "--json")
    body = json.loads(out)
    assert code == 1 and body["error"]["kind"] == "input"
    assert "notes.docx is not a Word .docx file" in body["error"]["message"]

    code, out, err = cli("roundtrip", str(fake), "--project", str(wongo_project), "--json")
    body = json.loads(out)
    assert code == 1 and body["error"]["kind"] == "input"
    assert "notes.docx is not a Word .docx file" in body["error"]["message"]


def test_worksheet_and_review_errors_name_their_command(cli, tmp_path):
    missing = tmp_path / "decisions" / "merge-none.md"

    for argv, command in ((("worksheet", "status", str(missing)), "worksheet status"),
                          (("worksheet", "lint", str(missing)), "worksheet lint"),
                          (("worksheet", "set", str(missing), "1", "apply"), "worksheet set"),
                          (("review", str(missing)), "review")):
        code, out, err = cli(*argv, "--json")
        body = json.loads(out)
        assert code == 1 and body["command"] == command, argv


def test_an_interrupt_in_json_mode_still_prints_one_object(cli, wongo_project, monkeypatch):
    import wongo.engine.checks as checks

    def interrupted(project):
        raise KeyboardInterrupt

    monkeypatch.setattr(checks, "run_checks", interrupted)
    code, out, err = cli("check", "--project", str(wongo_project), "--json")

    body = json.loads(out)
    assert code == 130
    assert body["ok"] is False and body["error"]["kind"] == "interrupted"


def test_an_unexpected_error_in_json_mode_is_reported_as_internal(cli, wongo_project, monkeypatch):
    import wongo.engine.checks as checks

    def broken(project):
        raise RuntimeError("something nobody anticipated")

    monkeypatch.setattr(checks, "run_checks", broken)
    code, out, err = cli("check", "--project", str(wongo_project), "--json")

    body = json.loads(out)
    assert code == 1
    assert body["ok"] is False and body["error"]["kind"] == "internal"
    assert "something nobody anticipated" in body["error"]["message"]
    assert "github.com/hoohugokim/wongo/issues" in body["error"]["message"]
    assert "RuntimeError" in body["error"]["traceback"]


def test_roundtrip_keeps_hangul_from_pandoc(cli, stub_quarto, wongo_project, tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text(
        '# Introduction\n\nBody text at 25 °C [수정]{.insertion author="김하나" '
        'date="2026-09-01T00:00:00Z"} cites the work.\n', encoding="utf-8")
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(markdown))
    coauthor = tmp_path / "coauthor.docx"
    Document().save(str(coauthor))  # pandoc is stubbed; it only has to be a DOCX

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
    Document().save(str(coauthor))  # pandoc is stubbed; it only has to be a DOCX
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
