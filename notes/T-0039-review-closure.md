# T-0039 — close the 8590fe3 review and audit accepted F1–F4 scope

2026-10-23. Baseline: local commit `8590fe3`. No commit, release, push, or
version bump. F5–F8 remain unstarted. No private manuscript was modified.

## Review findings

| Finding | Implementation and regression evidence |
|---|---|
| Final reference check precedes transforms | Final checks read transformed staged DOCX. An added Bibliography paragraph crossing the limit refuses submission and preserves prior main/SI/manifest bytes. |
| Hook stdout corrupts JSON | Quarto and hook streams are captured as diagnostic events. CLI and MCP emit diagnostics on stderr; engine calls print nothing. Success and failure are covered through actual child CLI and SDK stdio transport. |
| Assets can change during rendering | Snapshot source/profile/style/CSL/reference identities before checks. Compare before Quarto, after core render, after hooks, and before sealing. The manifest seals the captured identity. |
| Explicit style overrides appear stale | Record explicit override provenance separately from effective style. Config/environment selection is re-resolved for new non-overridden entries; explicit overrides stay fresh. Legacy entries retain recorded-style interpretation. |
| Highlights escape freshness | Automatically fingerprint highlights.md; adding, editing, removing, or changing it during rendering is covered. |
| Code examples count as floats | Shared context scanner distinguishes literal code, executable chunks, comments, metadata, inline spans, list nesting, and source line locations. |
| Malformed highlights/bounds crash | Profile lint and runtime share validators for counts, abstract/display bounds, types, bools, and ordering. CLI config failures remain one JSON object. |
| Caption self-reference counts as callout | Caption ownership excludes self-citations while retaining real references to other items and genuine body callouts, including wrapped captions and figure/table divs. |

Each original defect had a failing regression before its fix. Independent
reviewers rechecked the transaction/provenance and checker/profile changes.
Their additional concrete findings were fixed with regressions:

- Quoted hook paths, absolute interpreter prefixes, Windows backslashes,
  extensionless/custom-suffix scripts, interpreter options, and explicit
  external-hook permissions. Inline/module commands are not an execution trace;
  their dependent files still require explicit dependencies.
- Uppercase Python script suffixes use Wongo's interpreter.
- Successful hooks leaving missing or invalid DOCX raise InputError and roll
  back. Timeout diagnostics are captured too.
- Changes during initial check callbacks, final checks, or hooks refuse
  promotion. Reference-inclusive drift keeps the GateError/check contract.
- Root indented code and inline literal comment delimiters cannot hide or
  fabricate labels/callouts. Inline spans cannot cross blank paragraphs.
- Section exclusions use the same comment-aware scanner, preserving actual
  body text and executable captions around literal comment markers.

## Completeness against the accepted decisions

F1: declared files/directories, external permissions, missing sentinels,
optional static discovery, asset identity, drift refusal and freshness tests
are present. Unrelated files remain outside freshness.

F2: document-local references, duplicate labels across documents, uncited
items, structured Quarto warnings, collaboration promotion/checks_failed, and
status withholding the submission suggestion are covered. A real Quarto/R
regression renders both documents, reorders generated SI tables, and verifies
displayed references. The main-to-SI shortcode and a universal rendered
float registry remain explicitly outside D-0016; this does not claim every
proposal in the original report was implemented.

F3: abstract boundaries, exclusions, SI placement consistency and honest manual
coverage remain intact. Word-limit checks expose reconciled included/excluded
counts, rendered references, pending reference evidence, and approximation
limits using the existing counter. Display/highlights coverage is explicit.
Journal rules carry profile-level sources/date, labeled as inherited provenance
rather than a new per-rule source mapping. Generated content is not evaluated;
inline expressions contribute placeholders. No new journal hard numbers were
introduced, and existing numbers were not changed. One-paragraph form, keywords,
and ORCID remain manual.

F4: transforms run inside staging before final validation/sealing. Tests cover
failure rollback, fresh final hashes, unregistered edits, script/source changes,
reordering, an idempotent registered transform, and survival of tables, embedded
images, math, revisions and unrelated ZIP parts. Canonical document.xml is
compared after normalizing only the intended image-description change. Scripts
must cooperate with the staged-output interface; they are not sandboxed code.

## Verification

- `WONGO_REAL_QUARTO_TEST=1 UV_CACHE_DIR=/private/tmp/wongo-review-uv-cache
  UV_OFFLINE=1 uv run pytest -q`: **770 passed, 3 skipped**. This tests the
  integrated dirty workspace, including the existing uncommitted features.
  The four real-Quarto tests also passed separately.
- Real Quarto 1.10.19 synthetic parity against `8590fe3`: **52 compared DOCX
  parts byte-identical**, across main/SI and collab/submission. Generated SI
  references followed reordered tables. Probe:
  `/private/tmp/wongo_f1_f4_acceptance.py`; receipt:
  `/var/folders/8_/rh35ssj92h173ngj0pp8v6cr0000gn/T/wongo-f1-f4-acceptance-b6svw5ts/receipt.json`.
- Changed-file Ruff and `git diff --check` passed. Full-tree Ruff still reports
  only pre-existing `src/wongo/engine/worksheet.py:1129` E713; it is untouched.
- Wheel/sdist build passed offline with read-only cached build dependencies and
  `uv build --no-build-isolation`. Version and offline ES&T profile smoke passed.
- `statutor-doctor .` passed; rerun after the final ledger update too.

`WONGO_REF_PROJECT` is unset, so the private reference-manuscript byte comparison
was not run. Synthetic parity does not substitute for that release gate. No
native Windows or Microsoft Word execution was performed; T-0022 and T-0025
remain open.

## Existing dirty work

The initial snapshot hashed 194 modified/untracked files. Worksheet, new
profiles, research, AIX artifacts, and agent state were preserved. Three existing
dirty files needed surgical integration corrections: MCP diagnostic forwarding
in tools.py, literal escaped chunk/label fixtures in test_e2e_expansion.py, and
the indented-code expectation in test_adversarial_m1_m2.py. Their other edits
were retained. No worksheet E713 fix, staging, revert, or commit was performed.
Final hash verification: 191 original files are byte-identical; reversing only
the three integration deltas reproduces their original hashes exactly.

Compatibility checks retain non-strict check exit 0 when JSON ok is false,
strict exit 1, collaboration promotion of rendered cross-reference failures,
and refusal of source drift for both targets. D-0008 and D-0009 were not edited.
