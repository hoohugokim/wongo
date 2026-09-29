"""Published journal counting rules exercised through the manuscript check."""
from __future__ import annotations

import pytest
import yaml

from wongo.engine.checks import run_checks
from wongo.errors import ConfigError


def _project(tmp_path, journal, ms_type, text):
    (tmp_path / "_journal.yml").write_text(
        f"journal: {journal}\nms_type: {ms_type}\n", encoding="utf-8")
    (tmp_path / "index.qmd").write_text(text, encoding="utf-8")
    return tmp_path


def _word_limit(project):
    return next(c for c in run_checks(project) if c.name == "word-limit")


@pytest.mark.parametrize("journal,ms_type,limit", [
    ("natwater", "article", 3000),
    ("natwater", "analysis", 4000),
    ("npjcw", "brief-communication", 1500),
    ("npjbiofilms", "brief-communication", 1500),
])
def test_research_at_limit_passes_with_abstract_methods_references_and_legends(
    tmp_path, journal, ms_type, limit,
):
    text = (
        "---\nabstract: An abstract outside the main text count.\n---\n\n"
        + "word " * limit
        + "\n\n# Methods\nExcluded methods prose.\n\n"
        "## Sampling\nNested methods prose.\n\n"
        "# References\nA manually formatted reference.\n\n"
        "# Figure legends\nA separately placed figure legend.\n"
    )
    project = _project(tmp_path, journal, ms_type, text)
    check = _word_limit(project)
    assert check.ok, check.detail
    assert check.detail.startswith(f"{limit} words ")

    # The exclusions must not turn a genuinely over-limit main text into a pass.
    (project / "index.qmd").write_text(
        text.replace("# Methods", "extra\n\n# Methods", 1), encoding="utf-8")
    assert not _word_limit(project).ok


@pytest.mark.parametrize("journal,ms_type", [
    ("natwater", "article"), ("natwater", "analysis"),
    ("npjcw", "brief-communication"), ("npjbiofilms", "brief-communication"),
])
def test_research_excludes_figure_captions_but_keeps_table_captions(tmp_path, journal, ms_type):
    text = """Body stays.

![An inline figure caption.](missing.png)

```{r}
#| fig-cap: "A generated figure caption."
plot(1)
```

```{r}
#| tbl-cap: "Table stays."
knitr::kable(data.frame(x = 1))
```
"""
    checks = run_checks(_project(tmp_path, journal, ms_type, text))
    count = next(c for c in checks if c.name == "word-limit")
    assert count.detail.startswith("4 words "), count.detail
    # Excluding the caption from the count must not hide a broken figure.
    assert not next(c for c in checks if c.name == "figures").ok


@pytest.mark.parametrize("ms_type", ["perspective", "review"])
def test_nature_water_reviews_exclude_both_captions_and_boxes_but_count_methods(tmp_path, ms_type):
    text = """---
abstract: Abstract outside the count.
---
Body stays.

```{r}
#| fig-cap: "Figure caption outside the count."
#| tbl-cap: "Table caption outside the count."
```

: Markdown table caption
  continued on another line. {#tbl-demo}

::: {#box-background .box}
Box prose.
::: {.callout-note}
Nested box prose.
:::
:::

# Box 1: Further background
More box prose.

# Methods
Methods stay.

# References
Reference outside the count.
"""
    check = _word_limit(_project(tmp_path, "natwater", ms_type, text))
    assert check.detail.startswith("4 words "), check.detail


@pytest.mark.parametrize("journal,ms_type", [
    (journal, ms_type)
    for journal in ["npjcw", "npjbiofilms"]
    for ms_type in ["comment", "matters-arising", "perspective", "review"]
] + [("npjbiofilms", "meeting-report")])
def test_npj_main_text_limits_exclude_abstract_and_back_matter(tmp_path, journal, ms_type):
    text = """---
abstract: The separate abstract.
---
Body stays.

# Methods
Methods stay.

# Acknowledgments
Funding outside main text.

# Author contributions
Contributions outside main text.

# Competing interests
Declarations outside main text.

# References
A reference.

# Figure legends
A caption.
"""
    check = _word_limit(_project(tmp_path, journal, ms_type, text))
    assert check.detail.startswith("4 words "), check.detail


@pytest.mark.parametrize("methods,results", [
    ("## 2. METHODS {#sec-methods}", "## Results"),
    ("Methods\n-------", "Results\n-------"),
    ("## Materials and Methods", "## Results"),
    ("## Online Methods", "## Results"),
    ("## **Methods** {#sec-methods} ##", "## Results"),
])
def test_excluded_section_stops_at_its_sibling_but_keeps_nested_sections_out(
    tmp_path, methods, results,
):
    text = (
        "# Paper\nFirst words.\n\n"
        + methods + "\nExcluded words.\n\n"
        "### Sampling\nMore excluded words.\n\n"
        + results + "\nLast words.\n\n"
        "### Methods comparison\nThese words count.\n"
    )
    check = _word_limit(_project(tmp_path, "natwater", "article", text))
    assert check.detail.startswith("7 words "), check.detail


def test_heading_examples_and_comments_do_not_change_section_boundaries(tmp_path):
    text = """Body stays.

<!--
# Methods
#| fig-cap: Commented caption.
-->

````text
# Methods
```
Example inside a longer fence.
````

Body resumes.

# Methods
Excluded methods.

~~~python
# Results
print('a heading inside code cannot end Methods')
~~~

Still excluded.

# Discussion
Discussion stays.
"""
    check = _word_limit(_project(tmp_path, "natwater", "article", text))
    assert check.detail.startswith("6 words "), check.detail


def test_review_table_caption_filter_does_not_remove_definition_list_prose(tmp_path):
    text = """A term
: Its definition counts.

Body stays.
"""
    check = _word_limit(_project(tmp_path, "natwater", "review", text))
    assert check.detail.startswith("8 words "), check.detail


def test_figure_float_captions_are_excluded_without_losing_surrounding_prose(tmp_path):
    text = """First words.

::: {#fig-panels}
![](left.png)
![](right.png)

A combined caption for both panels.
:::

Last words.
"""
    check = _word_limit(_project(tmp_path, "natwater", "article", text))
    assert check.detail.startswith("4 words "), check.detail


def test_body_abstract_is_excluded_and_other_validation_still_sees_it(tmp_path):
    text = """# Abstract
An abstract cites @missing.

# Main text
Body words.
"""
    checks = run_checks(_project(tmp_path, "npjcw", "comment", text))
    count = next(c for c in checks if c.name == "word-limit")
    assert count.detail.startswith("2 words "), count.detail
    assert not next(c for c in checks if c.name == "citekeys").ok


def test_default_profile_keeps_abstract_methods_and_both_caption_kinds(tmp_path):
    text = """---
abstract: Abstract counts.
---
Body counts.

# Methods
Methods count.

![Figure caption.](figure.png)

```{r}
#| tbl-cap: "Table caption."
```
"""
    check = _word_limit(_project(tmp_path, "est", "research-article", text))
    assert check.detail.startswith("10 words "), check.detail


@pytest.mark.parametrize("policy", [
    None, [], "main-text", {"include_abstract": "false"}, {"exclude_sections": "Methods"},
    {"exclude_sections": [42]}, {"exclude_boxes": 1}, {"include_figures": False},
])
def test_malformed_counting_policy_is_an_actionable_config_error(tmp_path, policy):
    project = _project(tmp_path, "custom", "article", "Body words.")
    pdir = project / "profiles" / "custom"
    pdir.mkdir(parents=True)
    (pdir / "profile.yml").write_text(yaml.safe_dump({
        "slug": "custom", "manuscript_types": [
            {"type": "article", "word_limit": 10, "word_count": policy},
        ],
    }), encoding="utf-8")
    with pytest.raises(ConfigError, match="word_count"):
        run_checks(project)


def test_cli_submission_accepts_the_corrected_count_and_refuses_a_true_overflow(
    cli, stub_quarto, wongo_project,
):
    import json

    (wongo_project / "_journal.yml").write_text(
        "journal: natwater\nms_type: article\nstyle: default\n", encoding="utf-8")
    source = "---\nabstract: Short abstract.\n---\n" + "word " * 3000 + "\n# Methods\nDetails.\n"
    (wongo_project / "index.qmd").write_text(source, encoding="utf-8")
    code, out, _ = cli("check", "--project", str(wongo_project), "--strict", "--json")
    assert code == 0, out
    assert json.loads(out)["ok"]
    code, out, _ = cli("render", "--project", str(wongo_project), "--target", "submission", "--json")
    assert code == 0, out
    assert json.loads(out)["ok"]
    previous = {p.name: p.read_bytes() for p in (wongo_project / "output").glob("*.docx")}
    assert previous
    (wongo_project / "index.qmd").write_text(
        source.replace("# Methods", "extra\n# Methods"), encoding="utf-8")
    code, out, _ = cli("render", "--project", str(wongo_project), "--target", "submission", "--json")
    assert code == 1
    assert json.loads(out)["error"]["kind"] == "gate"
    assert {p.name: p.read_bytes() for p in (wongo_project / "output").glob("*.docx")} == previous
