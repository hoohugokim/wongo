"""Regression tests for tools/bytecompare.py, the render-parity harness.

Commit a02eac4 silently made the harness render into the LIVE reference
project (it copied the repo to scratch, then returned the original path), and
the harness accepted any output/*.docx that happened to exist, so a render
that never wrote the SI could still "pass" on a stale file.
"""
from __future__ import annotations

import importlib.util
import subprocess
import zipfile
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / "tools" / "bytecompare.py"
_SPEC = importlib.util.spec_from_file_location("bytecompare", _PATH)
bc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bc)


def _reference_repo(tmp_path: Path) -> Path:
    root = tmp_path / "ref-repo"
    proj = root / "manuscript"
    (proj / "output").mkdir(parents=True)
    (proj / "index.qmd").write_text("body", encoding="utf-8")
    (proj / "si.qmd").write_text("si", encoding="utf-8")
    (proj / "output" / "main-collab.docx").write_bytes(b"stale main")
    (proj / "output" / "si-collab.docx").write_bytes(b"stale si")
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    (root / ".pixi" / "envs").mkdir(parents=True)
    (root / "training").mkdir()
    (root / "training" / "data.csv").write_text("1,2", encoding="utf-8")
    return root


@pytest.fixture
def env(tmp_path, monkeypatch):
    ref = _reference_repo(tmp_path)
    scratch = tmp_path / "scratch"
    monkeypatch.setenv("WONGO_REF_PROJECT", str(ref))
    monkeypatch.setenv("WONGO_BC_SCRATCH", str(scratch))
    return ref, scratch


def _fake_render(stems_to_write):
    """A subprocess.run stand-in that writes only the given outputs."""

    def run(cmd, cwd=None, check=False, **kwargs):
        # the engine command carries uv's own --project; wongo's is the last one
        last = len(cmd) - 1 - cmd[::-1].index("--project")
        project = Path(cmd[last + 1])
        target = cmd[cmd.index("--target") + 1]
        out = project / "output"
        out.mkdir(exist_ok=True)
        for stem in stems_to_write:
            with zipfile.ZipFile(out / f"{stem}-{target}.docx", "w") as z:
                z.writestr("word/document.xml", f"<doc>{stem}</doc>")
                z.writestr("docProps/core.xml", "<ignored/>")
        return subprocess.CompletedProcess(cmd, 0)

    return run


def test_prepare_project_returns_the_scratch_copy_not_the_live_project(env):
    ref, scratch = env

    project = bc.prepare_project()

    assert project.resolve().is_relative_to(scratch.resolve())
    assert (project / "index.qmd").read_text(encoding="utf-8") == "body"
    assert (project.parent / "training" / "data.csv").exists()  # ../ assets survive


def test_copy_skips_git_history_and_old_renders(env):
    project = bc.prepare_project()

    assert not (project.parent / ".git").exists()
    assert not (project.parent / ".pixi").exists()
    assert not (project / "output").exists()


def test_render_happens_in_scratch_and_leaves_live_outputs_alone(env, monkeypatch):
    ref, scratch = env
    monkeypatch.setattr(bc.subprocess, "run", _fake_render(["main", "si"]))

    stems = bc.render_and_extract(["wongo", "render"], "collab", scratch / "candidate")

    assert stems == ["main-collab", "si-collab"]
    live = ref / "manuscript" / "output"
    assert (live / "main-collab.docx").read_bytes() == b"stale main"
    assert (live / "si-collab.docx").read_bytes() == b"stale si"
    assert (scratch / "candidate" / "main-collab" / "word" / "document.xml").exists()
    assert not (scratch / "candidate" / "main-collab" / "docProps").exists()


def test_missing_expected_output_fails_instead_of_passing(env, monkeypatch):
    ref, scratch = env
    monkeypatch.setattr(bc.subprocess, "run", _fake_render(["main"]))  # SI never written

    with pytest.raises(SystemExit) as excinfo:
        bc.render_and_extract(["wongo", "render"], "collab", scratch / "candidate")

    assert "si-collab.docx" in str(excinfo.value)


def test_previous_tree_is_replaced_not_merged(env, monkeypatch):
    ref, scratch = env
    stale = scratch / "candidate" / "main-collab" / "word" / "stale.xml"
    stale.parent.mkdir(parents=True)
    stale.write_text("<old/>", encoding="utf-8")
    monkeypatch.setattr(bc.subprocess, "run", _fake_render(["main", "si"]))

    bc.render_and_extract(["wongo", "render"], "collab", scratch / "candidate")

    assert not stale.exists()


def test_engine_command_can_render_with_another_checkout(tmp_path):
    other = tmp_path / "wongo-at-v0.1.0"
    other.mkdir()

    cmd = bc.engine_command(other)

    assert cmd[:4] == ["uv", "run", "--project", str(other.resolve())]
    assert cmd[-2:] == ["wongo", "render"]


def test_diff_is_limited_to_the_requested_documents(tmp_path):
    base, cand = tmp_path / "base", tmp_path / "cand"
    for root, text in ((base, "a"), (cand, "a")):
        (root / "main-collab" / "word").mkdir(parents=True)
        (root / "main-collab" / "word" / "document.xml").write_text(text, encoding="utf-8")
    (base / "main-submission" / "word").mkdir(parents=True)
    (base / "main-submission" / "word" / "document.xml").write_text("b", encoding="utf-8")

    assert bc.diff_trees(base, cand, stems=["main-collab"]) == {}
    assert "main-submission/word/document.xml" in bc.diff_trees(base, cand)


def test_selftest_never_overwrites_the_stored_baseline(env, monkeypatch, capsys):
    ref, scratch = env
    baseline = scratch / "baseline" / "main-collab" / "word" / "document.xml"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("<from-an-older-engine/>", encoding="utf-8")
    monkeypatch.setattr(bc.subprocess, "run", _fake_render(["main", "si"]))

    assert bc.main(["selftest", "--target", "collab"]) == 0

    assert baseline.read_text(encoding="utf-8") == "<from-an-older-engine/>"


def test_check_without_a_baseline_is_an_error(env, monkeypatch):
    monkeypatch.setattr(bc.subprocess, "run", _fake_render(["main", "si"]))

    with pytest.raises(SystemExit) as excinfo:
        bc.main(["check", "--target", "collab"])

    assert "baseline" in str(excinfo.value)
