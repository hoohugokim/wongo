# Main-to-SI reference implementation and closure

Completed 2026-10-24 after the user resumed the paused T-0041 work. Behavior was
verified on 2026-10-23; the resumed review found no additional actionable issue
or reason to repeat those tests. HEAD remains `8590fe3`; this increment and the
prior T-0039/T-0040 work remain uncommitted.

## Contract and implementation

[D-0019](../DECISIONS.md) adds the explicitly enabled `si_references: true`
interface. In `index.qmd`, `[SI item](wongo-si:tbl-label)` or `fig-label` is a
placeholder for the printed label in the final SI. The result is plain text,
not a cross-file Word hyperlink. Usage and limits are in
[docs/si-references.md](../docs/si-references.md).

`engine/si_refs.py` resolves actual main body/footnote/endnote hyperlinks against
one matching final SI bookmark and numbered English Figure/Table caption. It
copies the displayed number instead of inferring order from source labels, and
does not add an S prefix absent from SI. The engine resolves after declared
transforms, then runs final checks and seals/promotes the output transaction.
The manifest records SI identity, main before/after hashes and each resolved
label/part. Enabled projects with missing resolution identity are stale.

Read-only source checks validate configuration and mark destination verification
as pending render. Native `@` references stay document-scoped; duplicate-label
rules remain. An explicit main callout can satisfy the SI item's uncited check.
Invalid explicit requests refuse both targets, while ordinary unresolved-native
warnings still promote collab with `checks_failed`. Source drift still refuses
both targets. D-0008/D-0009, plain-check/strict exits and coauthor protections
remain unchanged.

## Verification evidence

- `WONGO_REAL_QUARTO_TEST=1 UV_CACHE_DIR=/private/tmp/wongo-review-uv-cache UV_OFFLINE=1 uv run pytest -q`:
  **985 passed, 4 skipped**, 223.28 s. This run preceded the final caption-context
  guard below.
- A subsequent synthetic reproduction found a nested data cell styled Caption
  could supply `Table S999` when the float caption was unnumbered. The resolver
  now requires the float's own table context; the new regression first failed,
  then passed with the guard.
- After that final code change,
  `WONGO_REAL_QUARTO_TEST=1 UV_CACHE_DIR=/private/tmp/wongo-review-uv-cache UV_OFFLINE=1 uv run pytest -q tests/test_si_refs.py tests/test_si_refs_quarto.py`:
  **32 passed**, 49.62 s. Coverage includes exact/ambiguous/missing destinations,
  unsupported types/rich labels, code/comment examples, deleted references,
  header refusal, final transform renumbering, source drift, rollback, and stale
  manifest identity. Real Quarto/R cases cover data-driven table reorder,
  generated figures and footnote links for collab and submission.
- The final wheel/sdist build and changed-file Ruff passed. On 2026-10-24 the
  three implementation files were compared byte-for-byte with the final wheel:
  `engine/si_refs.py`, `engine/__init__.py`, `engine/checks.py` all matched.
- Feature-disabled synthetic parity against `8590fe3`: **52 DOCX parts identical**
  across main/SI and collab/submission, including document/styles/settings.
  Generated SI reorder also passed. Receipt:
  `/private/var/folders/8_/rh35ssj92h173ngj0pp8v6cr0000gn/T/wongo-f1-f4-acceptance-3ec90mu0/receipt.json`.
- Full Ruff still reports only the pre-existing `worksheet.py:1129` E713. It was
  left unchanged. This is not a release or a claim of full lint cleanliness.

## Preservation and limits

The initial T-0041 inventory at `/private/tmp/wongo-t0041-before.json` has 245
pre-existing dirty files. The resumed SHA comparison found all present and 239
byte-identical. The six intended deltas are DECISIONS.md, HANDOFF.md, TASKS.md,
docs/README.md, engine/__init__.py and engine/checks.py. New files are the SI
resolver, its two test files, the usage guide and this completion note. Existing
worksheet, profile, research, AIX and agent-state work was preserved.

No staging, commit, push, installation, version bump, accepted-manuscript edit
or private scientific-data access occurred. No journal rules were changed.
`WONGO_REF_PROJECT` is unset; private reference parity and native Windows/Word
execution remain unperformed release prerequisites. Subfigure panels, equations,
localized caption titles, source-include discovery and clickable cross-file Word
links are outside this first interface. Prior closure evidence remains in
[T-0039](T-0039-review-closure.md) and [T-0040](T-0040-completion.md).
