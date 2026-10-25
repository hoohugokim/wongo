# Build evidence and author decisions

Wongo's optional audit, QA and review commands bind records to an exact build.
Start with the runnable [synthetic pilot](../examples/evidence-demo/README.md).
These interfaces add no automatic audit or preview execution to `check`,
`status`, rendering or MCP status resources.

## Configure project-owned checks

```yaml
audits:
  - id: rendered-values
    script: scripts/check_values.py
    inputs: [data/values.json, index.qmd]
    required: true
    timeout: 120
visual_review_required: true
manual_gates:
  - id: scientific-release
    label: Scientific interpretation reviewed
    required: true
  - id: author-release
    label: Authors authorize this build
```

Audit scripts and inputs join the render fingerprint. Audit inputs are explicit
permissions to copy those files into temporary scratch storage; ordinary
dependencies remain hash-only. An external audit input needs
`{path: /absolute/path, external: true}`. Scripts run as trusted local code,
with the user's process permissions; scratch copies are not an operating-system
sandbox. Enable scripts only after reviewing them.

`wongo audit --project PATH --json` executes only declared audits against copies
of sealed outputs. Python scripts use Wongo's interpreter; `.R` scripts use
discovered Rscript. The receipt identifies the script, input hashes, interpreter
executable hash and Wongo's Python runtime. Projects should declare pinned
analysis environments and relevant lockfiles among their inputs.

The script receives these environment variables:

| Variable | Value |
|---|---|
| `WONGO_AUDIT_PROJECT` | Scratch project root |
| `WONGO_AUDIT_OUTPUTS` | Absolute copied DOCX paths, separated by `os.pathsep` |
| `WONGO_AUDIT_INPUTS` | JSON mapping declared input keys to scratch paths |
| `WONGO_AUDIT_RESULT` | Result JSON file to write |
| `WONGO_AUDIT_TARGET`, `WONGO_AUDIT_ID` | Selected target and configured audit id |

Write a nonempty `assertions` list with unique `id`, boolean `ok`, `detail`,
`source`, `artifact`, and `rendered_context` fields. `coverage.checked` must name
each assertion exactly; `coverage.untested` lists unchecked areas. A valid
completed audit exits zero even if an assertion fails; Wongo derives overall
`ok` from assertions and exits one for a failed audit. Nonzero script exits,
timeouts, malformed reports, source drift or modified scratch inputs refuse a
receipt. Diagnostic output goes to stderr through the adapter.

`wongo.audit_helpers` provides `scalar_assertion`, `paragraph_assertion`,
`table_cell_assertion`, and `figure_order_assertion`. Missing keys fail; explicit
null is allowed only under the project's missingness policy. Prose `NA` is not
automatically an error. Paragraph anchors must be unique; table indices are
zero-based OOXML indices and include nested wrapper tables. The pilot selects
its table by unique column headers. Projects own rounding, units, denominators,
scientific assertions and complete coverage.

## Inspect final documents and pages

`wongo qa inspect` inventories final DOCX OOXML: images and descriptions, tables,
equations, superscripts, Unicode spaces and revisions. Persisted records retain
text identity and size, not full extracted manuscript text. This inventory
cannot determine whether alt text describes a figure accurately.

`wongo qa preview` optionally runs installed LibreOffice and Poppler (`pdfinfo`,
`pdftoppm`) in isolated scratch storage, preserving original DOCX bytes. The
receipt records renderer/tool versions, conversion settings, PDFs, page counts
and page-image hashes. It labels these `converted-layout-preview`; mathematical
appearance and pagination may differ in Microsoft Word.

After inspecting the pages, a person runs `wongo qa review --reviewer NAME
--all-pages` or repeats `--page document.docx:1`. A terminal confirmation records
checked and untested pages. `qa carry --preview ID --review ID` carries inspection
only when renderer/tool versions, settings and relevant page-image bytes match.
New or changed pages remain untested. Historical records retain their own build
subjects and original attribution.

`qa native-review --word-version VERSION --document document.docx:COUNT
--reviewer NAME --all-pages` instead records a person's native Word inspection.
Repeat `--document` for every sealed output. Native inspection is an explicit
local attestation, never automatic verification or authenticated identity; it
cannot be carried to another build automatically.

## Technical readiness and authorization

Status and MCP expose `technical`, `audit`, `visual`, `author_decisions` and
`submission_approved` independently. Missing observations are `not-recorded`;
changed build subjects or gate definitions make old evidence stale. A narrow
audit pass retains its unchecked coverage.

`required: true` audits and `visual_review_required: true` affect readiness.
Required visual review needs complete human page coverage. A recorded failed,
stale or invalid OOXML inventory also blocks that axis; an absent inventory is
reported separately. Inspection of a converted preview never certifies Word.

`wongo gates propose ID` records an agent proposal. `wongo gates review ID`
requires a person at a terminal to approve or reject the exact build and gate
definition. MCP deliberately has no approval or confirmation tool. A technical
pass alone never produces author authorization. All configured required manual
gates, required audit/visual evidence, and coauthor worksheet decisions must be
complete for `submission_approved`; its scope is the project's configured gates.
Only a submission-target build can have this state; a collaboration-build
approval remains a collaboration decision.
Unconfigured author duties remain outside Wongo's knowledge. These local records
are editable attestations, not signatures or protection against malicious local
rewriting. `demonstration: true` labels synthetic worksheet context without
treating pending rows as approval.

Plain `wongo check` keeps exit zero even when JSON `ok` is false; use `--strict`
for a gating exit code. Collab cross-reference warnings still promote and record
`checks_failed`. Mid-render input drift still refuses both targets.

## Portable review exports

`wongo evidence export review.zip` includes the current build identity and scoped
current records. Dependencies, profile/style assets and installed engine source
are identified by hash; editable engine changes differ even with the same
displayed version. Git dirty/clean state is informational. `evidence verify`
checks raw hashes and bindings; `evidence list` reads freshness without execution.

No source or deliverable bytes are included by default. Add `--outputs` for sealed
DOCX, `--artifacts` for generated evidence assets, or repeat `--include PATH` for
specific project files. External paths, traversal and escaping symlinks are
refused. Records themselves may contain project-declared assertion contexts,
image descriptions or reviewer statements; inspect this material before sharing.
Full extracted manuscript text is excluded from inventory records. Wongo never
automatically copies raw dependencies or credentials. Missing artifact bytes and
unchecked pages remain visible in the manifest. Referenced old records are
included separately as historical provenance and never as current observations.

Reviewer claims use `review-note` records; tool observations retain their audit
or QA kinds. A human `review-disposition` refers to an exact claim, independently
of author approval. Both support exact hashed source lines or artifact pointers.

For example, save `[{"source_file": "index.qmd", "line": 16}]` as a JSON list,
then run `evidence note --reviewer NAME --statement
'Check this interpretation' --references references.json`. Source references
accept an optional `end_line`; artifact references use `artifact` and `pointer`.
Pointers can be JSON `/key/0`, DOCX `word/document.xml#xpath=/w:document/w:body/w:p[1]`,
or `/` for a whole artifact. They must resolve. A person runs `evidence disposition
NOTE_ID --decision accept --maintainer NAME --reason 'Assessed against the data'`
at a terminal to confirm a disposition. Agent claims and human dispositions
never supply author-gate approval.

`evidence compare FIRST SECOND` retains original byte hashes and adds a narrow
content identity. For DOCX, only ZIP container metadata and the text of
`dcterms:created`/`modified` in `docProps/core.xml` are normalized. Other ZIP parts,
scientific text, cells, field instructions/results and accessibility descriptions
remain exact. For PDF, only same-length literal CreationDate/ModDate strings in
a directly located, uncompressed trailer Info dictionary are masked. Streams,
XMP, IDs, incremental updates, encryption and unsupported formats remain exact.
This conservative handling may classify harmless changes as content changes.
The Info fields and cross-reference structure follow
[ISO 32000-1](https://developer.adobe.com/document-services/docs/assets/35e4369068f86065372c18787171a17e/PDF_ISO_32000-1.pdf).
Normalization never changes the actual files or relaxes receipt freshness.
