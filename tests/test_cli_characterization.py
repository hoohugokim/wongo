"""User-visible CLI behaviour, pinned before the engine refactor (error type,
staged renders, --json) so it cannot drift silently. The Claude skill reads this
text; an intentional change updates these tests and the skill together."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document


def _docx(path: Path, paragraphs: list[str]) -> Path:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))
    return path


def test_collab_render_writes_main_and_si_after_the_check_report(cli, stub_quarto, wongo_project):
    code, out, err = cli("render", "--target", "collab", "--project", str(wongo_project))

    assert code == 0, err
    output = wongo_project.resolve() / "output"
    assert (output / "main-collab.docx").is_file()
    assert (output / "si-collab.docx").is_file()
    lines = out.splitlines()
    assert lines[0].startswith("[PASS] HARD word-limit: ")
    wrote = [i for i, line in enumerate(lines) if line.startswith("wrote ")]
    assert [lines[i] for i in wrote][:2] == [
        f"wrote {output / 'main-collab.docx'}",
        f"wrote {output / 'si-collab.docx'}",
    ]
    report = [i for i, line in enumerate(lines) if line.startswith("[")]
    assert max(report) < min(wrote)
    assert [argv[1] for argv in stub_quarto.renders()] == ["index.qmd", "si.qmd"]


def test_submission_render_is_refused_before_quarto_on_a_hard_failure(cli, stub_quarto, project_factory):
    project = project_factory(word_limit=3)

    code, out, err = cli("render", "--target", "submission", "--project", str(project))

    assert code == 1
    assert "HARD checks failed — submission render refused" in err
    assert "[FAIL] HARD word-limit: " in out
    assert stub_quarto.renders() == []
    assert not (project / "output" / "main-submission.docx").exists()


def test_submission_render_is_refused_before_quarto_without_required_toc_art(cli, stub_quarto, project_factory):
    project = project_factory(toc_required=True)

    code, out, err = cli("render", "--target", "submission", "--project", str(project))

    assert code == 1
    assert "Profile requires TOC art but figures/toc-art." in err
    assert stub_quarto.renders() == []


def test_check_report_text(cli, wongo_project):
    code, out, err = cli("check", "--project", str(wongo_project))

    assert code == 0
    assert out == (
        "[PASS] HARD word-limit: 13 words vs limit 500 for article (rule: body plus abstract)\n"
        "[PASS] HARD citekeys: all citekeys resolve\n"
        "[PASS] HARD crossrefs: all cross-references resolve\n"
        "[PASS] HARD figures: all referenced figures exist\n"
        "[PASS] WARN profile-staleness: profile verified 0 days ago\n"
        "[PASS] WARN si-file: si.qmd present\n"
    )


def test_check_strict_exits_1_on_hard_failure(cli, project_factory):
    project = project_factory(word_limit=3)

    code, out, err = cli("check", "--strict", "--project", str(project))

    assert code == 1
    assert out.startswith("[FAIL] HARD word-limit: ")


def test_diff_report_text(cli, tmp_path):
    original = _docx(tmp_path / "a.docx", ["The catalyst was copper.", "Unchanged."])
    revised = _docx(tmp_path / "b.docx", ["The catalyst was nickel.", "Unchanged."])
    out_path = tmp_path / "tracked.docx"

    code, out, err = cli("diff", str(original), str(revised), "-o", str(out_path),
                         "--date", "2026-09-25T00:00:00Z")

    assert code == 0
    assert out == (
        f"wrote {out_path}\n"
        "  words: +1 inserted, -1 deleted\n"
        "  paragraphs: +0, -0\n"
    )


def test_profile_verify_offline_text(cli, tmp_path, monkeypatch):
    from wongo import profiles

    root = tmp_path / "profiles-root"
    (root / "demo").mkdir(parents=True)
    today = date.today().isoformat()
    (root / "demo" / "profile.yml").write_text(
        "slug: demo\njournal: Demo Journal\n"
        "manuscript_types: [{type: article, word_limit: 100, counting_rule: r}]\n"
        f"sources: [https://example.org]\nverified_date: {today}\n",
        encoding="utf-8")
    monkeypatch.setattr(profiles, "candidate_dirs", lambda project=None: [root])

    code, out, err = cli("profile", "verify", "demo", "--offline")

    assert code == 0
    assert out == (
        f"profile:   {root / 'demo'}\n"
        "journal:   Demo Journal\n"
        f"verified:  {today} (0d ago)\n"
        "live sources: skipped (--offline)\n"
        "\n"
        "VERIFY: clean — no evidence of guideline drift since verified_date (offline check only)\n"
    )


def test_roundtrip_writes_a_pending_worksheet(cli, stub_quarto, wongo_project, tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text(
        "# Introduction\n\nBody text [now]{.insertion author=\"Jane Doe\" "
        "date=\"2026-09-01T00:00:00Z\"} cites the work.\n",
        encoding="utf-8")
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(markdown))
    coauthor = _docx(tmp_path / "coauthor.docx", ["Body text now cites the work."])

    code, out, err = cli("roundtrip", str(coauthor), "--project", str(wongo_project))

    assert code == 0, err
    worksheets = sorted((wongo_project / "decisions").glob("merge-*-coauthor.md"))
    assert len(worksheets) == 1
    assert out == (f"wrote {worksheets[0]} (1 changes; NONE applied — "
                   "review dispositions first)\n"
                   f"next: wongo review {worksheets[0].as_posix()}\n")
    text = worksheets[0].read_text(encoding="utf-8")
    assert "## 1. insertion — Jane Doe" in text
    assert "- new: now" in text
    assert "- disposition: PENDING" in text


def test_scaffold_output_text(cli, tmp_path):
    dest = tmp_path / "new-paper"

    code, out, err = cli("scaffold", str(dest))

    assert code == 0
    assert (dest / "_journal.yml").is_file()
    assert out.splitlines()[0] == f"scaffolded {dest.resolve()}"


def test_roundtrip_next_step_is_relative_when_run_inside_the_project(cli, stub_quarto, wongo_project,
                                                                     tmp_path, monkeypatch):
    markdown = tmp_path / "pandoc.md"
    markdown.write_text('Body [now]{.insertion author="A" date="2026-09-01T00:00:00Z"} ok.\n',
                        encoding="utf-8")
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(markdown))
    coauthor = _docx(tmp_path / "coauthor.docx", ["Body now ok."])
    monkeypatch.chdir(wongo_project)

    code, out, err = cli("roundtrip", str(coauthor))

    assert code == 0, err
    name = next((wongo_project / "decisions").glob("merge-*.md")).name
    assert out.splitlines()[-1] == f"next: wongo review decisions/{name}"
