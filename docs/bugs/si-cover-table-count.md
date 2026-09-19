**Status: FIXED 2026-09-19** — `wongo.engine.si_item_counts` classifies floats by caption lead (see `docs/docx-quirks.md`, pinned by `tests/test_engine.py::test_si_item_counts_exclude_figure_wrappers_but_keep_nested_and_image_tables`).

The SI cover sheet counts Quarto/Pandoc figure-wrapper tables as scientific tables. A rendered SI with 14 figures and 11 numbered data tables prints `Contents: 14 figures, 25 tables`.

In `src/wongo/engine/__init__.py`, `postprocess_si()` computes `"tables": len(doc.tables)` after `wstyles.apply_style()`. Word's top-level table elements include the figure/caption wrappers. This counting expression is present at commit `ad6019d` and in the locally installed editable tree.

Reproduction:

1. Use an ES&T project with `style: kist-wcr`, a numbered figure and a numbered data table in `si.qmd`.
2. Run `wongo render --target collab` from the project directory.
3. Compare the cover's table count with the numbered Table S captions and inspect `word/document.xml` in the DOCX ZIP.

Observed on the affected output: 25 top-level `w:tbl` elements, 14 containing `w:drawing` and 11 without drawings; the cover reports 25 tables. The figure count is correctly 14. No manuscript or data attachment is needed to reproduce this structural issue.

Expected: count the 11 scientific tables, excluding the 14 figure wrappers. The fix should recognize figure/caption wrappers or use semantic table identifiers, rather than blindly excluding every table that contains a drawing (a legitimate data table might contain an image). Please cover ordinary tables, wrappers, and an image-containing data table with regression tests and preserve the reference render apart from the corrected count.

Current workaround: correct the SI cover's table count in Word at upload. Page count is a separate `NUMPAGES` field and must be refreshed/checked against the final paginated document.
