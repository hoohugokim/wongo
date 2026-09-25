"""The first-run path for new users: scaffold, doctor, status, profile show,
style list. Toolchain lookups are stubbed so these run on any CI machine."""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from wongo import doctor, toolchain
from wongo.errors import ConfigError, InputError
from wongo.scaffold import scaffold

# ---------------------------------------------------------------------------
# scaffold


def test_scaffold_with_flags_writes_a_ready_journal_config(tmp_path):
    result = scaffold(tmp_path / "paper", journal="wr", ms_type="research-paper", style="kist-wcr")

    config = (result.dest / "_journal.yml").read_text(encoding="utf-8")
    assert "journal: wr " in config
    assert "ms_type: research-paper " in config
    assert "style: kist-wcr " in config
    assert result.journal_name == "Water Research"


def test_scaffold_ships_editor_tasks_and_agent_files_under_their_real_names(tmp_path):
    result = scaffold(tmp_path / "paper")

    assert (result.dest / ".vscode" / "tasks.json").is_file()
    tasks = json.loads((result.dest / ".vscode" / "tasks.json").read_text(encoding="utf-8"))
    assert any(t["command"] == "wongo render --target collab" for t in tasks["tasks"])
    assert (result.dest / "AGENTS.md").read_text(encoding="utf-8").startswith("# Manuscript project")
    assert (result.dest / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert not list(result.dest.rglob("*.tmpl"))
    assert "wrap: sentence" in (result.dest / "_quarto.yml").read_text(encoding="utf-8")


def test_scaffold_rejects_unknown_journal_type_and_style(tmp_path):
    with pytest.raises(ConfigError):
        scaffold(tmp_path / "a", journal="no-such-journal")
    with pytest.raises(ConfigError):
        scaffold(tmp_path / "b", journal="est", ms_type="sonnet")
    with pytest.raises(ConfigError):
        scaffold(tmp_path / "c", style="baroque")
    with pytest.raises(InputError):
        scaffold(tmp_path / "d", ms_type="research-article")
    assert not any((tmp_path / name).exists() for name in "abcd")


def test_scaffold_refuses_a_non_empty_folder(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "notes.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(InputError):
        scaffold(tmp_path / "paper")

    assert (tmp_path / "paper" / "notes.txt").read_text(encoding="utf-8") == "keep me"


def test_example_project_is_complete_and_passes_checks(tmp_path):
    from wongo.engine.checks import run_checks

    result = scaffold(tmp_path / "demo", example=True)

    assert (result.journal, result.ms_type) == ("est", "research-article")
    art = result.dest / "figures" / "toc-art.png"
    width, height = struct.unpack(">II", art.read_bytes()[16:24])
    assert (width, height) == (975, 525)
    failing = [c.name for c in run_checks(result.dest) if c.level == "HARD" and not c.ok]
    assert failing == []


def test_scaffold_cli_text_without_a_terminal(cli, tmp_path):
    code, out, err = cli("scaffold", str(tmp_path / "paper"), "--journal", "est",
                         "--ms-type", "research-article")

    assert code == 0, err
    lines = out.splitlines()
    assert lines[0] == f"scaffolded {(tmp_path / 'paper').resolve()}"
    assert "journal: est (Environmental Science & Technology)" in lines[1]
    assert any("wongo doctor" in line for line in lines)


def test_scaffold_prompts_only_at_a_terminal(cli, tmp_path, monkeypatch):
    import wongo.cli as cli_module

    answers = iter(["", "1"])  # journal: Enter is not a choice, then #1
    monkeypatch.setattr(cli_module, "is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers, ""))

    code, out, err = cli("scaffold", str(tmp_path / "paper"))

    assert code == 0, err
    assert "Which journal is this manuscript for?" in out
    assert "please type a number" in out
    config = (tmp_path / "paper" / "_journal.yml").read_text(encoding="utf-8")
    assert 'journal: ""' not in config


# ---------------------------------------------------------------------------
# doctor


@pytest.fixture
def no_r(monkeypatch):
    monkeypatch.setattr(toolchain, "find_rscript", lambda: None)


def _names(checks, ok=None):
    return [c.name for c in checks if ok is None or c.ok is ok]


def test_doctor_reports_missing_quarto_with_the_platform_install_command(monkeypatch, no_r, tmp_path):
    monkeypatch.delenv("WONGO_QUARTO", raising=False)
    monkeypatch.setattr(toolchain, "find_quarto", lambda: None)

    checks = doctor.run_doctor(tmp_path)

    quarto = next(c for c in checks if c.name == "quarto")
    assert quarto.level == "HARD" and not quarto.ok
    assert toolchain.install_hint("quarto") in quarto.detail


def test_doctor_warns_on_untested_quarto_and_off_path_quarto(monkeypatch, no_r, tmp_path):
    monkeypatch.setattr(toolchain, "find_quarto",
                        lambda: toolchain.Tool("/opt/q/quarto", "known location"))
    monkeypatch.setattr(toolchain, "tool_version", lambda cmd, *a, **k: "1.11.5")

    checks = doctor.run_doctor(tmp_path)

    assert "quarto" in _names(checks, ok=True)
    assert {"quarto-version", "quarto-path"} <= set(_names(checks, ok=False))


def test_doctor_requires_r_packages_for_a_knitr_project(monkeypatch, stub_quarto, wongo_project):
    (wongo_project / "_quarto.yml").write_text(
        (wongo_project / "_quarto.yml").read_text(encoding="utf-8") + "engine: knitr\n",
        encoding="utf-8")
    monkeypatch.setattr(toolchain, "find_rscript", lambda: toolchain.Tool("/r/Rscript", "PATH"))
    monkeypatch.setattr(toolchain, "probe_r", lambda tool: toolchain.RReport(
        version="4.6.1", packages={"knitr": "1.51", "rmarkdown": None, "jsonlite": None}))

    checks = doctor.run_doctor(wongo_project)

    by_name = {c.name: c for c in checks}
    assert by_name["r-knitr"].ok
    assert by_name["r-rmarkdown"].level == "HARD" and not by_name["r-rmarkdown"].ok
    assert "install.packages('rmarkdown'" in by_name["r-rmarkdown"].detail
    assert by_name["r-jsonlite"].level == "WARN"
    assert by_name["project-config"].ok


def test_doctor_windows_specific_warnings(monkeypatch, no_r, stub_quarto, wongo_project):
    monkeypatch.setattr(toolchain, "platform_name", lambda: "windows")
    monkeypatch.setattr(doctor.Path, "home", classmethod(lambda cls: Path("C:/Users/김하나")))
    (wongo_project / "_quarto.yml").write_text(
        "project:\n  type: default\n  output-dir: output\n  post-render:\n"
        "    - python3 scripts/fix.py\n", encoding="utf-8")
    monkeypatch.setattr(doctor.shutil, "which",
                        lambda name: r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python3.exe")

    checks = doctor.run_doctor(wongo_project)

    failing = set(_names(checks, ok=False))
    assert "home-path" in failing
    assert "render-hook" in failing


def test_doctor_cli_exit_code_and_json(cli, monkeypatch, no_r, tmp_path):
    monkeypatch.delenv("WONGO_QUARTO", raising=False)
    monkeypatch.setattr(toolchain, "find_quarto", lambda: None)

    code, out, err = cli("doctor", "--project", str(tmp_path), "--json")

    assert code == 1
    body = json.loads(out)
    assert body["command"] == "doctor" and body["ok"] is False
    assert any(c["name"] == "quarto" and not c["ok"] for c in body["checks"])


# ---------------------------------------------------------------------------
# status


def test_status_outside_a_project_suggests_scaffold(cli, tmp_path):
    code, out, err = cli("status", "--project", str(tmp_path))

    assert code == 0
    assert "not a wongo project" in out
    assert "wongo scaffold" in out


def test_status_walks_through_render_then_stale(cli, stub_quarto, wongo_project):
    code, out, err = cli("status", "--project", str(wongo_project))
    assert "next:       wongo render --target collab" in out

    assert cli("render", "--target", "collab", "--project", str(wongo_project))[0] == 0
    code, out, err = cli("status", "--project", str(wongo_project))
    assert "collab:     fresh" in out
    assert "next:       wongo render --target submission" in out

    index = wongo_project / "index.qmd"
    index.write_text(index.read_text(encoding="utf-8") + "\nOne more sentence.\n", encoding="utf-8")
    code, out, err = cli("status", "--project", str(wongo_project), "--json")
    body = json.loads(out)
    assert body["status"]["outputs"]["collab"]["state"] == "stale"
    assert body["status"]["outputs"]["collab"]["changed"] == ["index.qmd"]
    assert body["status"]["next_command"] == "wongo render --target collab"


def test_status_flags_an_output_saved_over_in_word(cli, stub_quarto, wongo_project):
    cli("render", "--target", "collab", "--project", str(wongo_project))
    main = wongo_project / "output" / "main-collab.docx"
    main.write_bytes(main.read_bytes() + b"\0")

    code, out, err = cli("status", "--project", str(wongo_project))

    assert "collab:     modified (main-collab.docx)" in out


# ---------------------------------------------------------------------------
# profile show / style list


def test_profile_show_text_and_json(cli):
    code, out, err = cli("profile", "show", "wr")

    assert code == 0
    assert out.startswith("wr — Water Research")
    assert "research-paper       8000 words incl. references" in out
    assert "SKILL.md" in out

    code, out, err = cli("profile", "show", "wr", "--json")
    body = json.loads(out)
    assert body["profile"]["slug"] == "wr"
    assert body["paths"]["checklist"].endswith("submission-checklist.md")


def test_style_list(cli):
    code, out, err = cli("style", "list")

    assert code == 0
    names = [line.split()[0] for line in out.splitlines()]
    assert names == ["default", "kist-wcr"]


def test_status_points_to_review_while_worksheet_rows_are_open(cli, stub_quarto, wongo_project, tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text('Body text [now]{.insertion author="Jane Doe" date="2026-09-01T00:00:00Z"} cites.\n',
                        encoding="utf-8")
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(markdown))
    coauthor = tmp_path / "coauthor.docx"
    coauthor.write_bytes(b"placeholder")
    cli("render", "--target", "collab", "--project", str(wongo_project))
    assert cli("roundtrip", str(coauthor), "--project", str(wongo_project))[0] == 0
    worksheet = next((wongo_project / "decisions").glob("merge-*.md"))

    code, out, err = cli("status", "--project", str(wongo_project), "--json")
    body = json.loads(out)["status"]
    assert code == 0, err
    assert body["worksheet_open"] == 1
    assert body["next_command"] == f"wongo review {Path('decisions') / worksheet.name}"

    assert cli("worksheet", "set", str(worksheet), "1", "PROPOSED apply — plain prose")[0] == 0
    assert cli("worksheet", "lint", str(worksheet))[0] == 1  # a proposal is not a decision
    assert cli("worksheet", "set", str(worksheet), "1", "apply")[0] == 0
    code, out, err = cli("worksheet", "lint", str(worksheet))
    assert code == 0, out + err
    body = json.loads(cli("status", "--project", str(wongo_project), "--json")[1])["status"]
    assert body["worksheet_open"] == 0


def test_review_refuses_without_a_terminal(cli, wongo_project):
    decisions = wongo_project / "decisions"
    decisions.mkdir()
    sheet = decisions / "merge-20260925-x.md"
    sheet.write_text("# Merge worksheet\n\n## 1. insertion — A\n- location: index.qmd:1\n"
                     "- old: —\n- new: x\n- context: …\n- disposition: PENDING\n", encoding="utf-8")

    code, out, err = cli("review", str(sheet))

    assert code == 1
    assert "wongo worksheet set" in err
