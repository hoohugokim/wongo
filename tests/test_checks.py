"""Word-count approximation: chunk-option captions count, fenced code does not."""
from datetime import date, timedelta

from wongo.engine.checks import prose, word_count
from wongo.profiles import profile_staleness_days

DOC = """---
title: T
abstract: |
  one two three
---

# Heading

Body sentence with `r fmt(x)` inline code.

```{r tbl-demo}
#| echo: false
#| tbl-cap: "Caption alpha beta gamma delta."
knitr::kable(data.frame(a = 1))
```

![Fig caption epsilon zeta.](fig.png){#fig-demo}
"""


def test_chunk_caption_counted_but_code_not():
    p = prose(DOC.split("---\n", 2)[2])
    assert "alpha beta gamma delta" in p
    assert "knitr::kable" not in p and "echo: false" not in p
    assert "epsilon zeta" in p


def test_word_count_includes_abstract_captions_and_placeholder():
    # abstract 3 + body "Body sentence with X inline code." 6 + tbl-cap 5 + fig-cap 4 = 18
    assert word_count(DOC) == 18


def test_future_profile_verification_date_is_negative_staleness():
    tomorrow = date.today() + timedelta(days=1)
    assert profile_staleness_days({"verified_date": tomorrow}) == -1


def test_commented_out_images_are_not_missing_figures():
    from wongo.engine.checks import image_paths

    body = "---\ntitle: T\n---\n\n<!-- ![old](figures/gone.png) -->\n\n![live](figures/here.png)\n"
    assert image_paths(body) == ["figures/here.png"]


def test_word_count_ignores_div_fences_and_shortcodes():
    doc = "---\ntitle: T\n---\n\nOne two three.\n\n{{< pagebreak >}}\n\n# References\n\n::: {#refs}\n:::\n"
    assert word_count(doc) == 3


def test_display_items_defined_extraction():
    from wongo.engine.checks import display_items_defined

    content = """---
title: Demo
---

# Section {#sec-intro}

First paragraph with @fig-1 and @tbl-1 reference.

```{r}
#| label: fig-1
#| fig-cap: "First figure"
plot(1)
```

![Second figure](photo.png){#fig-2}

: First table {#tbl-1}

```{r fig-3, echo=FALSE}
plot(2)
```

```{r}
#| label: "tbl-2"
knitr::kable(head(cars))
```

<!--
```{r}
#| label: fig-hidden
```
![Hidden](hidden.png){#fig-hidden-2}
-->

```{python}
#| label: lst-code
print("not a display item")
```
"""
    items = display_items_defined(content)
    labels = [lbl for lbl, _ in items]
    assert labels == ["fig-1", "fig-2", "tbl-1", "fig-3", "tbl-2"]
    # Check line numbers exist and are > 0
    assert all(lineno > 0 for _, lineno in items)
    # Ensure lst- and sec- are not included
    assert "lst-code" not in labels
    assert "sec-intro" not in labels
    # Ensure commented out labels are excluded
    assert "fig-hidden" not in labels
    assert "fig-hidden-2" not in labels


def test_abstract_words_function():
    from wongo.engine.checks import abstract_words

    assert abstract_words({}) == (0, False)
    assert abstract_words({"abstract": ""}) == (0, False)
    assert abstract_words({"abstract": "   "}) == (0, False)
    assert abstract_words({"abstract": "One two three four five."}) == (5, True)
    assert abstract_words({"abstract": ["First paragraph has four.", "Second has three."]}) == (7, True)


def test_parse_highlights_text_and_frontmatter():
    from wongo.engine.checks import parse_frontmatter_highlights, parse_highlights_text

    text = """# Article Highlights

- First bullet point with exactly few words.
- Second bullet point that wraps
  onto a continuation line seamlessly.
* Third bullet with special symbol CO₂ and 50 µm thickness.
"""
    bullets = parse_highlights_text(text)
    assert len(bullets) == 3
    assert bullets[0][0] == "First bullet point with exactly few words."
    assert "onto a continuation line seamlessly." in bullets[1][0]
    assert bullets[2][0] == "Third bullet with special symbol CO₂ and 50 µm thickness."

    fm_list = ["Point alpha", "- Point beta", "* Point gamma"]
    fm_bullets = parse_frontmatter_highlights(fm_list)
    assert len(fm_bullets) == 3
    assert [b for b, _ in fm_bullets] == ["Point alpha", "Point beta", "Point gamma"]


def _make_test_project(
    tmp_path,
    *,
    max_display_items=None,
    abstract_limit=None,
    highlights_required=None,
    max_chars_per_bullet=None,
    index_body="Main body text.",
    abstract_text="A brief abstract for testing.",
    include_highlights_file=False,
    highlights_content=None,
    frontmatter_highlights=None,
):
    project = tmp_path / "proj"
    project.mkdir(parents=True, exist_ok=True)
    pdir = project / "profiles" / "testj"
    pdir.mkdir(parents=True, exist_ok=True)

    mtype_lines = [
        "  - type: research",
        "    word_limit: 5000",
        '    counting_rule: "standard"',
    ]
    if max_display_items is not None:
        mtype_lines.append(f"    max_display_items: {max_display_items}")
    if abstract_limit is not None:
        mtype_lines.append(f"    abstract_limit: {abstract_limit}")

    profile_lines = [
        "slug: testj",
        "journal: Test Journal",
        "verified_date: 2026-09-01",
        "sources: [https://example.org]",
        "manuscript_types:",
        *mtype_lines,
    ]
    if highlights_required is not None:
        profile_lines.append("highlights:")
        profile_lines.append(f"  required: {str(highlights_required).lower()}")
        if max_chars_per_bullet is not None:
            profile_lines.append(f"  max_chars_per_bullet: {max_chars_per_bullet}")

    (pdir / "profile.yml").write_text("\n".join(profile_lines) + "\n", encoding="utf-8")
    (project / "_journal.yml").write_text("journal: testj\nms_type: research\n", encoding="utf-8")
    (project / "refs.bib").write_text("@article{k,\n  title={T},\n}\n", encoding="utf-8")

    fm_lines = ["---", "title: Demo"]
    if abstract_text is not None:
        fm_lines.append(f"abstract: {abstract_text}")
    if frontmatter_highlights is not None:
        fm_lines.append("highlights:")
        for h in frontmatter_highlights:
            fm_lines.append(f"  - {h}")
    fm_lines.extend(["---", "", index_body, ""])
    (project / "index.qmd").write_text("\n".join(fm_lines), encoding="utf-8")

    if include_highlights_file and highlights_content is not None:
        (project / "highlights.md").write_text(highlights_content, encoding="utf-8")

    return project


def test_display_items_limit_enforced_hard(tmp_path):
    from wongo.engine.checks import run_checks

    # 4 items allowed, 3 defined -> PASS
    body_pass = """
```{r}
#| label: fig-1
plot(1)
```
![Fig 2](a.png){#fig-2}
: Table 1 {#tbl-1}
"""
    proj_pass = _make_test_project(tmp_path / "pass", max_display_items=4, index_body=body_pass)
    checks_pass = run_checks(proj_pass)
    c_pass = next(c for c in checks_pass if c.name == "display-items-limit")
    assert c_pass.level == "HARD"
    assert c_pass.ok
    assert "3 display items vs limit 4" in c_pass.detail

    # 4 items allowed, 5 defined -> FAIL HARD
    body_fail = body_pass + """
```{r}
#| label: fig-extra
plot(3)
```
: Table 2 {#tbl-extra}
"""
    proj_fail = _make_test_project(tmp_path / "fail", max_display_items=4, index_body=body_fail)
    checks_fail = run_checks(proj_fail)
    c_fail = next(c for c in checks_fail if c.name == "display-items-limit")
    assert c_fail.level == "HARD"
    assert not c_fail.ok
    assert "5 display items exceed limit 4" in c_fail.detail
    assert c_fail.patch_hint is not None
    assert c_fail.patch_hint["action"] == "reduce_display_items"
    assert c_fail.patch_hint["excess_items"] == 1
    assert c_fail.patch_hint["target_items"] == 4
    assert len(c_fail.locations) == 5


def test_display_items_limit_skipped_when_omitted(tmp_path):
    from wongo.engine.checks import run_checks

    proj = _make_test_project(tmp_path, max_display_items=None)
    checks = run_checks(proj)
    assert not any(c.name == "display-items-limit" for c in checks)


def test_abstract_word_limit_enforced_hard(tmp_path):
    from wongo.engine.checks import run_checks

    # 5 words vs limit 6 -> PASS
    proj_pass = _make_test_project(
        tmp_path / "pass",
        abstract_limit=6,
        abstract_text="One two three four five.",
    )
    checks_pass = run_checks(proj_pass)
    c_pass = next(c for c in checks_pass if c.name == "abstract-word-limit")
    assert c_pass.level == "HARD"
    assert c_pass.ok
    assert "5 words vs limit 6" in c_pass.detail

    # 8 words vs limit 6 -> FAIL HARD
    proj_fail = _make_test_project(
        tmp_path / "fail",
        abstract_limit=6,
        abstract_text="One two three four five six seven eight.",
    )
    checks_fail = run_checks(proj_fail)
    c_fail = next(c for c in checks_fail if c.name == "abstract-word-limit")
    assert c_fail.level == "HARD"
    assert not c_fail.ok
    assert "8 words exceed limit 6" in c_fail.detail
    assert c_fail.patch_hint["action"] == "trim_abstract"
    assert c_fail.patch_hint["excess_words"] == 2

    # Missing abstract -> FAIL HARD
    proj_missing = _make_test_project(
        tmp_path / "missing",
        abstract_limit=6,
        abstract_text=None,
    )
    checks_missing = run_checks(proj_missing)
    c_missing = next(c for c in checks_missing if c.name == "abstract-word-limit")
    assert c_missing.level == "HARD"
    assert not c_missing.ok
    assert "Abstract is missing" in c_missing.detail
    assert c_missing.patch_hint["action"] == "add_abstract"


def test_highlights_missing_reports_warn(tmp_path):
    from wongo.engine.checks import run_checks

    proj = _make_test_project(tmp_path, highlights_required=True, include_highlights_file=False)
    checks = run_checks(proj)
    c = next(c for c in checks if c.name == "highlights")
    assert c.level == "WARN"
    assert not c.ok
    assert "highlights.md (or frontmatter highlights) not found" in c.detail
    assert c.patch_hint["action"] == "create_highlights"


def test_highlights_valid_file_passes_hard(tmp_path):
    from wongo.engine.checks import run_checks

    content = """# Highlights
- Anode modification accelerates microbial colonization and electron transfer.
- Charge transfer resistance decreased by 68% relative to unmodified carbon cloth.
- Multi-heme cytochrome c alignment drives accelerated extracellular transfer.
"""
    proj = _make_test_project(
        tmp_path,
        highlights_required=True,
        include_highlights_file=True,
        highlights_content=content,
    )
    checks = run_checks(proj)
    c = next(c for c in checks if c.name == "highlights")
    assert c.level == "HARD"
    assert c.ok
    assert "3 highlights bullets" in c.detail


def test_highlights_char_limit_exceeded_fails_hard(tmp_path):
    from wongo.engine.checks import run_checks

    # Bullet 2 is >85 chars (92 chars)
    long_bullet = "This is an excessively detailed bullet point that definitely exceeds eighty-five characters."
    assert len(long_bullet) > 85

    content = f"""# Highlights
- Point one is nice and short.
- {long_bullet}
- Point three is also well within the character limit.
"""
    proj = _make_test_project(
        tmp_path,
        highlights_required=True,
        include_highlights_file=True,
        highlights_content=content,
    )
    checks = run_checks(proj)
    c = next(c for c in checks if c.name == "highlights")
    assert c.level == "HARD"
    assert not c.ok
    assert "exceed 85 characters" in c.detail
    assert c.patch_hint["action"] == "trim_highlights"
    assert c.patch_hint["violations"][0]["bullet"] == 2
    assert c.patch_hint["violations"][0]["excess"] == len(long_bullet) - 85


def test_highlights_count_out_of_range_fails_hard(tmp_path):
    from wongo.engine.checks import run_checks

    # Only 2 bullets (expected 3-5)
    content = """# Highlights
- Point one.
- Point two.
"""
    proj = _make_test_project(
        tmp_path,
        highlights_required=True,
        include_highlights_file=True,
        highlights_content=content,
    )
    checks = run_checks(proj)
    c = next(c for c in checks if c.name == "highlights")
    assert c.level == "HARD"
    assert not c.ok
    assert "2 highlights bullets (expected 3-5)" in c.detail
    assert c.patch_hint["action"] == "adjust_highlights_count"


def test_highlights_in_frontmatter_supported(tmp_path):
    from wongo.engine.checks import run_checks

    fm_bullets = [
        "First frontmatter highlight point.",
        "Second frontmatter highlight point.",
        "Third frontmatter highlight point.",
        "Fourth frontmatter highlight point.",
    ]
    proj = _make_test_project(
        tmp_path,
        highlights_required=True,
        frontmatter_highlights=fm_bullets,
    )
    checks = run_checks(proj)
    c = next(c for c in checks if c.name == "highlights")
    assert c.level == "HARD"
    assert c.ok
    assert "4 highlights bullets" in c.detail


def test_profile_schema_validation_for_new_keys():
    from wongo.profiles import validate_profile

    base = {
        "journal": "Demo", "slug": "demo", "publisher": "P",
        "manuscript_types": [{"type": "article", "word_limit": 100, "counting_rule": "r"}],
        "sources": ["https://example.org/guide"], "verified_date": date(2026, 1, 1),
    }

    # max_display_items validation
    p1 = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "max_display_items": -1}])
    assert any("max_display_items" in p for p in validate_profile(p1))
    p2 = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "max_display_items": "four"}])
    assert any("max_display_items" in p for p in validate_profile(p2))
    p3 = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "max_display_items": True}])
    assert any("max_display_items" in p for p in validate_profile(p3))
    p_ok = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "max_display_items": 4}])
    assert validate_profile(p_ok) == []

    # abstract_limit validation
    p4 = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "abstract_limit": -5}])
    assert any("abstract_limit" in p for p in validate_profile(p4))
    p5 = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "abstract_limit": "200"}])
    assert any("abstract_limit" in p for p in validate_profile(p5))
    p_abs_ok = dict(base, manuscript_types=[{"type": "article", "word_limit": 100, "abstract_limit": 200}])
    assert validate_profile(p_abs_ok) == []

    # highlights validation
    ph1 = dict(base, highlights="invalid")
    assert any("highlights must be a mapping" in p for p in validate_profile(ph1))
    ph2 = dict(base, highlights={"count": [3, 5]})
    assert any("highlights.required is missing" in p for p in validate_profile(ph2))
    ph3 = dict(base, highlights={"required": "yes"})
    assert any("highlights.required must be true or false" in p for p in validate_profile(ph3))
    ph4 = dict(base, highlights={"required": True, "max_chars_per_bullet": -10})
    assert any("highlights.max_chars_per_bullet" in p for p in validate_profile(ph4))
    ph_ok = dict(base, highlights={"required": True, "max_chars_per_bullet": 85})
    assert validate_profile(ph_ok) == []

