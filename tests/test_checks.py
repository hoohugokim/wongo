"""Word-count approximation: chunk-option captions count, fenced code does not."""
from wongo.engine.checks import prose, word_count

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
