"""End-to-end tests of wongo.engine.checks.run_checks against tmp_path
projects with a project-local profile (profiles/<slug>/profile.yml is
resolved before the packaged/repo profiles per wongo.profiles resolution
order, so no monkeypatching of profile discovery is needed here).
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from wongo.engine.checks import Check, run_checks

WORD_LIMIT = 10


def _check(checks: list[Check], name: str) -> Check:
    for c in checks:
        if c.name == name:
            return c
    raise AssertionError(f"no check named {name!r} among {[c.name for c in checks]}")


def _write_profile(project: Path, *, verified_date: str | None = "today", si_separate: bool = True) -> None:
    if verified_date == "today":
        verified_date = date.today().isoformat()
    pdir = project / "profiles" / "demo"
    pdir.mkdir(parents=True, exist_ok=True)
    lines = [
        "slug: demo",
        "journal: Demo",
        "manuscript_types:",
        "  - type: article",
        f"    word_limit: {WORD_LIMIT}",
        '    counting_rule: "test"',
    ]
    if verified_date is not None:
        lines.append(f"verified_date: {verified_date}")
    lines += [
        "si:",
        f"  separate_file: {str(si_separate).lower()}",
    ]
    (pdir / "profile.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_journal_yml(project: Path) -> None:
    (project / "_journal.yml").write_text(
        "journal: demo\nms_type: article\n", encoding="utf-8"
    )


def make_project(
    tmp_path: Path,
    *,
    index_body: str = "Short body text here.",
    bib: str = "@article{smith2020,\n  title = {A},\n}\n",
    include_si: bool = False,
    si_body: str = "SI body text.",
    verified_date: str | None = "today",
    si_separate: bool = True,
    write_journal_yml: bool = True,
    write_index: bool = True,
) -> Path:
    project = tmp_path / "proj"
    project.mkdir()
    if write_journal_yml:
        _write_journal_yml(project)
    _write_profile(project, verified_date=verified_date, si_separate=si_separate)
    (project / "refs.bib").write_text(bib, encoding="utf-8")
    if write_index:
        (project / "index.qmd").write_text(
            "---\ntitle: Demo manuscript\n---\n\n" + index_body + "\n",
            encoding="utf-8",
        )
    if include_si:
        (project / "si.qmd").write_text(
            "---\ntitle: SI\n---\n\n" + si_body + "\n", encoding="utf-8"
        )
    return project


# ---------------------------------------------------------------------------
# (a) clean project: everything ok


def test_clean_project_passes_every_check(tmp_path):
    project = make_project(
        tmp_path,
        index_body="Short body citing [@smith2020].",
        include_si=True,
    )
    checks = run_checks(project)
    assert checks, "run_checks returned no checks"
    for c in checks:
        assert c.ok, f"{c.name} unexpectedly failed: {c.detail}"


# ---------------------------------------------------------------------------
# (b) missing citekey


def test_missing_citekey_fails_hard_citekeys_check(tmp_path):
    project = make_project(
        tmp_path,
        index_body="Body text citing [@ghost2099] which is not in refs.bib.",
        include_si=True,
    )
    checks = run_checks(project)
    c = _check(checks, "citekeys")
    assert c.level == "HARD"
    assert not c.ok
    assert "ghost2099" in c.detail


# ---------------------------------------------------------------------------
# (c) orphaned crossref


def test_orphan_crossref_fails_hard_crossrefs_check(tmp_path):
    project = make_project(
        tmp_path,
        index_body="See @fig-x for details, but no such label is ever defined.",
        include_si=True,
    )
    checks = run_checks(project)
    c = _check(checks, "crossrefs")
    assert c.level == "HARD"
    assert not c.ok
    assert "fig-x" in c.detail


# ---------------------------------------------------------------------------
# (d) knitr chunk header defines a label -> no orphan


def test_knitr_chunk_header_label_counts_as_defined(tmp_path):
    body = (
        "See @fig-plot for the trend.\n\n"
        "```{r fig-plot}\n"
        "#| echo: false\n"
        "plot(1)\n"
        "```\n"
    )
    project = make_project(tmp_path, index_body=body, include_si=True)
    checks = run_checks(project)
    c = _check(checks, "crossrefs")
    assert c.ok, c.detail


# ---------------------------------------------------------------------------
# (e) missing figure file


def test_missing_image_file_fails_hard_figures_check(tmp_path):
    project = make_project(
        tmp_path,
        index_body="A figure. ![caption](figures/missing.png)",
        include_si=True,
    )
    checks = run_checks(project)
    c = _check(checks, "figures")
    assert c.level == "HARD"
    assert not c.ok
    assert "missing.png" in c.detail


# ---------------------------------------------------------------------------
# (f) over word limit


def test_body_over_word_limit_fails_hard_word_limit_check(tmp_path):
    body = " ".join(f"word{i}" for i in range(WORD_LIMIT + 5))
    project = make_project(tmp_path, index_body=body, include_si=True)
    checks = run_checks(project)
    c = _check(checks, "word-limit")
    assert c.level == "HARD"
    assert not c.ok
    assert str(WORD_LIMIT) in c.detail


def test_body_within_word_limit_passes_word_limit_check(tmp_path):
    body = " ".join(f"word{i}" for i in range(WORD_LIMIT - 2))
    project = make_project(tmp_path, index_body=body, include_si=True)
    checks = run_checks(project)
    c = _check(checks, "word-limit")
    assert c.ok, c.detail


# ---------------------------------------------------------------------------
# (g) si-file WARN


def test_si_separate_file_expected_but_absent_warns(tmp_path):
    project = make_project(tmp_path, include_si=False, si_separate=True)
    checks = run_checks(project)
    c = _check(checks, "si-file")
    assert c.level == "WARN"
    assert not c.ok
    assert "si.qmd" in c.detail or "SI" in c.detail


def test_si_separate_file_expected_and_present_ok(tmp_path):
    project = make_project(tmp_path, include_si=True, si_separate=True)
    checks = run_checks(project)
    c = _check(checks, "si-file")
    assert c.level == "WARN"
    assert c.ok


# ---------------------------------------------------------------------------
# (h) profile-staleness WARN


def test_stale_verified_date_warns(tmp_path):
    stale = (date.today() - timedelta(days=200)).isoformat()
    project = make_project(tmp_path, include_si=True, verified_date=stale)
    checks = run_checks(project)
    c = _check(checks, "profile-staleness")
    assert c.level == "WARN"
    assert not c.ok
    assert "200" in c.detail


def test_fresh_verified_date_ok(tmp_path):
    project = make_project(tmp_path, include_si=True, verified_date="today")
    checks = run_checks(project)
    c = _check(checks, "profile-staleness")
    assert c.level == "WARN"
    assert c.ok


# ---------------------------------------------------------------------------
# (i) missing index.qmd raises SystemExit


def test_missing_index_qmd_raises_system_exit(tmp_path):
    project = make_project(tmp_path, include_si=True, write_index=False)
    with pytest.raises(SystemExit):
        run_checks(project)


def test_bibliography_is_discovered_from_quarto_config(tmp_path):
    """Quarto projects name their .bib in _quarto.yml (or the .qmd front
    matter); a hardcoded refs.bib would report every citekey as missing."""
    from wongo.engine.checks import run_checks

    project = make_project(tmp_path, index_body="Cites @doe2020.")
    (project / "refs.bib").unlink()
    (project / "_quarto.yml").write_text("bibliography: library/main.bib\n", encoding="utf-8")
    (project / "library").mkdir()
    (project / "library" / "main.bib").write_text(
        "@article{doe2020, title={T}, author={Doe}, year={2020}}\n", encoding="utf-8"
    )
    checks = {c.name: c for c in run_checks(project)}
    assert checks["citekeys"].ok, checks["citekeys"].detail


def test_bibliography_list_in_front_matter_is_honored(tmp_path):
    from wongo.engine.checks import run_checks

    project = make_project(tmp_path)
    (project / "index.qmd").write_text(
        "---\ntitle: T\nbibliography: [a.bib, b.bib]\n---\n\nCites @one and @two.\n",
        encoding="utf-8",
    )
    (project / "refs.bib").unlink()
    (project / "a.bib").write_text("@misc{one, title={1}}\n", encoding="utf-8")
    (project / "b.bib").write_text("@misc{two, title={2}}\n", encoding="utf-8")
    checks = {c.name: c for c in run_checks(project)}
    assert checks["citekeys"].ok, checks["citekeys"].detail
