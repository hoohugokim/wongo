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
