# Synthetic build evidence pilot

Copy this directory to a scratch location. It uses installed Quarto, R and
knitr, a local demonstration profile, and one invented CSV value. No journal
limits or scientific validity are asserted. Source changes stale every receipt.

Run from the scratch copy using an environment with the current Wongo installed:

```fish
wongo render --target submission --json
wongo audit --json
wongo qa inspect --json
wongo qa preview --json
wongo status --json
wongo evidence export review.zip --outputs --artifacts --json
wongo evidence verify review.zip --json
```

The audit checks one finite scalar, one paragraph and one table cell. Its receipt
lists interpretation, units policy and all other content as untested. Status
reads records; it never runs the audit or a converter.

Preview conversion requires LibreOffice and Poppler (`pdfinfo`, `pdftoppm`).
Open the exported page images before recording page inspection at a terminal:

```fish
wongo qa review --reviewer 'Your name' --all-pages --json
wongo gates propose scientific-release --rationale 'Interpretation ready for human review' --json
wongo gates review scientific-release --reviewer 'Your name' --json
wongo gates review author-release --reviewer 'Your name' --json
```

Only confirm decisions you actually made. Converted pages establish that
renderer's preview; they do not certify Microsoft Word layout. Native inspection
can instead be recorded with `qa native-review`; see its help for document page
counts. These are local human attestations, not authenticated signatures.
No approvals are supplied with this example.

Exports include source/dependency identities by default, not their bytes. The
`--outputs` and `--artifacts` flags explicitly include DOCX and generated QA
assets. To include a particular source, add `--include index.qmd`. Never use an
unreviewed bulk list containing credentials or protected scientific data.
