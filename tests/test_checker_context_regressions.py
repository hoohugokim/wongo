"""Code examples and captions cannot stand in for rendered floats or callouts."""
from __future__ import annotations

import pytest
from docx import Document
from docx.enum.style import WD_STYLE_TYPE

from wongo.engine.checks import (
    crossrefs_used,
    display_items_defined,
    labels_defined,
    rule_coverage,
    run_checks,
    word_count,
)


def _check(project, name):
    return next(check for check in run_checks(project) if check.name == name)


@pytest.mark.parametrize("fence", ["```markdown", "~~~~markdown", "````"])
def test_literal_examples_are_not_display_definitions(wongo_project, fence):
    marker = fence.rstrip("markdown")
    inner = "~~~" if marker.startswith("`") else "```"
    text = (
        f"{fence}\n"
        f"{inner}{{r}}\n#| label: fig-example\n#| fig-cap: 'See @fig-missing.'\n{inner}\n"
        "![Example](nothing.png){#fig-markdown-example}\n"
        f"{marker}\n"
    )
    (wongo_project / "index.qmd").write_text(text, encoding="utf-8")
    assert display_items_defined(text) == []
    assert labels_defined(text) == set()
    assert _check(wongo_project, "crossrefs").ok
    assert _check(wongo_project, "uncited").ok


def test_literal_examples_do_not_satisfy_real_references(wongo_project):
    (wongo_project / "index.qmd").write_text(
        "See @fig-example.\n\n```markdown\n{#fig-example}\n```\n",
        encoding="utf-8",
    )
    assert not _check(wongo_project, "crossrefs").ok


def test_html_comment_markers_in_literal_example_do_not_hide_later_prose():
    text = "```markdown\n<!--\n```\n\n{#fig-real}\n\n<!-- end -->\n"
    assert labels_defined(text) == {"fig-real"}


def test_root_indented_code_cannot_define_items_or_captions(wongo_project):
    text = (
        "    ```{r}\n    #| label: fig-example\n"
        "    #| fig-cap: 'See @fig-missing.'\n    plot(1)\n    ```\n"
        "    {#tbl-example}\n\nReal body.\n"
    )
    (wongo_project / "index.qmd").write_text(text, encoding="utf-8")
    assert display_items_defined(text) == []
    assert labels_defined(text) == set()
    assert _check(wongo_project, "crossrefs").ok
    assert word_count(text) == 2


def test_list_nested_executable_chunks_remain_definitions():
    text = (
        "- List item.\n\n    ```{r}\n    #| label: fig-real\n"
        "    #| fig-cap: 'A real caption.'\n    plot(1)\n    ```\n"
    )
    assert display_items_defined(text) == [("fig-real", 4)]


@pytest.mark.parametrize("code", ["`<!--`", "``<!-- ` example``", "``example\n<!--\ncode``"])
def test_inline_code_comment_tokens_do_not_hide_later_prose(wongo_project, code):
    text = f"Example {code}.\n\nSee @fig-real.\n\n{{#fig-real}}\n"
    (wongo_project / "index.qmd").write_text(text, encoding="utf-8")
    assert labels_defined(text) == {"fig-real"}
    assert display_items_defined(text) == [("fig-real", len(text.splitlines()))]
    assert _check(wongo_project, "uncited").ok


def test_multiline_inline_code_cannot_define_a_label():
    text = "Example ``code\n{#fig-example}\ncode``.\n\n{#fig-real}\n"
    assert labels_defined(text) == {"fig-real"}


@pytest.mark.parametrize("paragraph_break", ["\n\n", "\n \n", "\n\t\n"])
def test_unmatched_ticks_cannot_hide_references_across_paragraphs(paragraph_break):
    text = paragraph_break.join([
        "A lone ` marker.", "See @fig-missing.", "Another ` marker.",
    ])
    assert crossrefs_used(text) == {"fig-missing"}
    assert word_count(text) == 9


def test_inline_code_still_spans_soft_line_breaks_within_one_paragraph():
    text = "Before ``one\n@fig-example\n`two`` after."
    assert crossrefs_used(text) == set()
    assert word_count(text) == 3


@pytest.mark.parametrize("delimiter", ["`", "``"])
def test_section_exclusions_preserve_literal_inline_comment_tokens(delimiter):
    text = (
        f"Before {delimiter}<!--{delimiter}.\n\nKeep these body words.\n\n"
        f"After {delimiter}-->{delimiter}.\n\n# Acknowledgments\n\nThanks.\n"
    )
    assert word_count(text) == 9
    assert word_count(text, exclude_sections=["Acknowledgments"]) == 8


def test_section_exclusions_keep_chunk_source_and_caption_comment_literals():
    text = (
        "Before.\n\n```{r}\n#| label: fig-real\n#| fig-cap: 'A real caption.'\n"
        "html <- '<!--'\n```\n\nKeep body.\n\n<!-- hidden -->\n\n"
        "# Acknowledgments\n\nThanks.\n"
    )
    assert word_count(text, exclude_sections=["Acknowledgments"]) == 6


def test_wrapper_caption_does_not_cite_its_own_figure_but_body_can(wongo_project):
    wrapper = (
        "::: {#fig-wrapper}\n\n![Panel](figures/demo.png)\n\n"
        "Caption naming @fig-wrapper.\n\n:::\n"
    )
    (wongo_project / "index.qmd").write_text(wrapper, encoding="utf-8")
    assert not _check(wongo_project, "uncited").ok
    wrapper = wrapper.replace("![Panel]", "See @fig-wrapper.\n\n![Panel]")
    (wongo_project / "index.qmd").write_text(wrapper, encoding="utf-8")
    assert _check(wongo_project, "uncited").ok


def test_hidden_and_metadata_labels_are_not_owners(wongo_project):
    (wongo_project / "index.qmd").write_text(
        "---\ntitle: '{#fig-shared}'\n---\n<!-- {#fig-shared} -->\n",
        encoding="utf-8",
    )
    (wongo_project / "si.qmd").write_text("See @fig-shared.\n\n{#fig-shared}\n", encoding="utf-8")
    assert _check(wongo_project, "crossrefs").ok


@pytest.mark.parametrize("kind", ["chunk", "markdown", "table"])
def test_a_caption_self_reference_does_not_cite_its_own_item(wongo_project, kind):
    texts = {
        "chunk": "```{r}\n#| label: fig-one\n#| fig-cap: 'See @fig-one.'\nplot(1)\n```\n",
        "markdown": "![See @fig-one.](figures/demo.png){#fig-one}\n",
        "table": "| A | B |\n|---|---|\n| 1 | 2 |\n\n: See @tbl-one. {#tbl-one}\n",
    }
    (wongo_project / "index.qmd").write_text(texts[kind], encoding="utf-8")
    assert not _check(wongo_project, "uncited").ok
    assert _check(wongo_project, "crossrefs").ok


def test_caption_references_to_other_items_still_count(wongo_project):
    text = (
        "See @fig-one.\n\n```{r}\n#| label: fig-one\n"
        "#| fig-cap: 'Compare @fig-two.'\nplot(1)\n```\n"
        "```{python}\n#| label: fig-two\n#| fig-cap: 'Second figure.'\nprint(1)\n```\n"
    )
    (wongo_project / "index.qmd").write_text(text, encoding="utf-8")
    assert _check(wongo_project, "crossrefs").ok
    assert _check(wongo_project, "uncited").ok


def test_body_callout_on_same_line_as_markdown_figure_is_kept(wongo_project):
    (wongo_project / "index.qmd").write_text(
        "See @fig-one. ![See @fig-one.](figures/demo.png){#fig-one}\n", encoding="utf-8")
    assert _check(wongo_project, "uncited").ok


@pytest.mark.parametrize("kind", ["image", "table"])
def test_multiline_caption_self_reference_does_not_count(wongo_project, kind):
    text = (
        "![See @fig-one\nfor details](figures/demo.png){#fig-one}\n"
        if kind == "image" else
        "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
        ": See @tbl-one.\n  Caption continuation. {#tbl-one}\n"
    )
    (wongo_project / "index.qmd").write_text(
        text, encoding="utf-8")
    assert not _check(wongo_project, "uncited").ok


def test_real_chunk_caption_survives_but_example_caption_does_not_count():
    text = (
        "Body.\n\n```markdown\n#| fig-cap: 'Not a real caption.'\n```\n"
        "```{python}\n#| label: fig-real\n#| fig-cap: 'A real caption.'\nprint(1)\n```\n"
    )
    assert word_count(text) == 4


def test_coverage_lists_display_and_conditional_highlights():
    rules = {item["id"]: item for item in rule_coverage(
        {"highlights": {"required": True}},
        {"word_limit": 100, "max_display_items": 2},
    )}
    assert rules["display-items-limit"]["enforcement"] == "machine"
    assert rules["highlights"]["enforcement"] == "machine"
    assert "missing" in rules["highlights"]["detail"]
    assert "WARN" in rules["highlights"]["detail"]


def test_journal_coverage_names_profile_level_provenance():
    profile = {"sources": ["https://example.org/guide"], "verified_date": "2026-10-22"}
    rules = {item["id"]: item for item in rule_coverage(profile, {"word_limit": 100})}
    assert rules["word-limit"]["provenance_scope"] == "profile"
    assert rules["word-limit"]["sources"] == profile["sources"]
    assert rules["word-limit"]["verified_date"] == "2026-10-22"
    assert "provenance_scope" not in rules["crossrefs"]


def test_word_count_breakdown_reconciles_source_policy_and_rendered_references(wongo_project):
    profile = wongo_project / "profiles/demo/profile.yml"
    profile.write_text(profile.read_text(encoding="utf-8").replace(
        'counting_rule: "body plus abstract"',
        'counting_rule: "body plus abstract", word_limit_includes_references: true, '
        'word_count: {exclude_sections: [Acknowledgments]}',
    ), encoding="utf-8")
    text = (
        "---\nabstract: alpha beta\n---\n\nBody `r expression()` [@doe2020].\n\n"
        "![three caption words](figures/demo.png){#fig-one}\n\n"
        "```{r}\n#| label: tbl-one\n#| tbl-cap: 'two words'\nkable(df)\n```\n\n"
        "# Acknowledgments\n\nExcluded three words.\n"
    )
    (wongo_project / "index.qmd").write_text(text, encoding="utf-8")
    doc = Document()
    doc.styles.add_style("Bibliography", WD_STYLE_TYPE.PARAGRAPH)
    doc.add_paragraph("Four rendered reference words.", style="Bibliography")
    path = wongo_project / "rendered.docx"
    doc.save(path)
    counted = next(check for check in run_checks(wongo_project, rendered_main=path)
                   if check.name == "word-limit")
    breakdown = counted.breakdown
    assert breakdown["abstract"] == 2
    assert breakdown["figure_captions"] == 3
    assert breakdown["table_captions"] == 2
    assert breakdown["source_total"] == word_count(text, exclude_sections=["Acknowledgments"])
    assert sum(breakdown[key] for key in ("abstract", "body", "figure_captions", "table_captions")) == breakdown["source_total"]
    assert breakdown["excluded_source_words"] == 3
    assert breakdown["rendered_references"] == 4
    assert breakdown["total"] == breakdown["source_total"] + 4
    assert "not evaluated" in " ".join(breakdown["approximation"])


def test_word_count_breakdown_says_when_references_are_not_yet_counted(wongo_project):
    profile = wongo_project / "profiles/demo/profile.yml"
    profile.write_text(profile.read_text(encoding="utf-8").replace(
        'counting_rule: "body plus abstract"',
        'counting_rule: "body plus abstract", word_limit_includes_references: true',
    ), encoding="utf-8")
    breakdown = _check(wongo_project, "word-limit").breakdown
    assert breakdown["rendered_references"] is None
    assert breakdown["references_status"] == "pending-render"
