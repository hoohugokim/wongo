# T-0003: reference-inclusive submission gate

PR #4 (T-0023) merged as `67ce1d9` before this work. The existing Water Research
profile declares reference-inclusive limits; this task changes their enforcement,
not the journal rules, limits or verification date.

## Design

Keep source-only `wongo check` fast and honest: its estimate cannot prove a
reference-inclusive pass. It now directs the user to render. Do not reuse old
DOCX files implicitly or depend on a cache whose freshness would have to cover
every bibliography, CSL and Quarto input.

After rendering and post-processing in staging, add the words in the new main
DOCX's `Bibliography` paragraphs to the same source estimate. The final check
reports both contributions and explicitly says **estimated total**. The gate
runs before any DOCX or manifest is promoted. An overflow leaves existing
deliverables byte-for-byte intact. Collab output remains available with the
failed HARD check so the author can inspect it.

The count reads raw paragraph XML, joins formatted runs before tokenization,
includes hyperlink text, and treats tabs/breaks as separators. It counts the
rendered reference list rather than all `.bib` entries, respects `nocite` via
Quarto, and keeps SI references separate. Manually written references in
ordinary source paragraphs are already in the source estimate.

No bibliography text when the main manuscript requests citations or `nocite`
is an unverified HARD failure, not a zero-word pass. Sources or journal policy
changed during rendering also leave the combined count unverified. The final
checks flow through the existing event, CLI text/JSON and GateError interfaces.

## Evidence and limits

A synthetic manuscript rendered with Quarto 1.10.18/Pandoc 3.10 and the shipped
Water Research CSL produces this ten-word reference (linked DOI included):

> Doe, J., Roe, R., 2020. Water science. Demo Journal. https://doi.org/10.1234/demo

The permanent real-Quarto regression uses 7,990 source words plus this reference:
8,000 passes; adding one source word fails and preserves previous output and its
manifest. An uncited `.bib` entry does not enter the count. CI runs the regression
on Linux, macOS and Windows in the existing Quarto jobs.

[Pandoc's citation documentation](https://pandoc.org/MANUAL.html#citations)
describes bibliography generation, `nocite`, and `suppress-bibliography`.
The bibliography paragraph style and linked-text behavior were verified directly
in the synthetic DOCX's `word/document.xml`.

This deliberately measures the missing reference-list contribution. The source
estimate still approximates citation expansion, generated body prose, includes
and complex markup; it is not Word's or a submission system's tokenizer. Custom
filters must preserve the standard `Bibliography` style for generated entries
and must not apply it to hand-written prose already counted in the source.

## Verification

- `WONGO_REAL_QUARTO_TEST=1 uv run pytest -q`: 459 passed, 3 OS-specific skips.
- Ruff, wheel/sdist build, CLI version smoke, offline verification of ES&T and
  Water Research profiles, and Statutor checks passed.
- Focused tests cover exact/over-limit behavior, output/manifest preservation,
  formatted/link text, main/SI separation, source-only warnings, collab inspection,
  missing bibliography, project/front-matter metadata, and source/profile changes
  during rendering.
- Fresh v0.3.0 baseline (`96c386e`) versus candidate on a scratch copy of the
  private reference manuscript: 95 parts across four DOCX files byte-identical,
  including document.xml, styles.xml and settings.xml; empty allowlist. Logs:
  `/private/tmp/wongo-t0003-{baseline,candidate}.log`.
