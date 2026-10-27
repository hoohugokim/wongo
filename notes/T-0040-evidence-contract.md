# F5–F8 implementation contract

Execution design, 2026-10-23. The human authorized the five-increment plan in
this chat. Preserve D-0008/D-0009, existing check exits, collab warning promotion,
and all previous dirty work. No automatic audit enforcement during rendering.

## Shared evidence module (root owner)

`wongo.evidence` supplies these functions:

- `digest(value) -> str`: canonical JSON SHA-256 (no nonfinite JSON numbers).
- `hash_file(path) -> str`: SHA-256 with actionable InputError.
- `evidence_dir(project) -> Path`: `output/.wongo-evidence`.
- `snapshot(project, target='submission') -> dict`: requires fresh sealed
  outputs, returns `{id, subject, installation}`. Subject contains exact
  sources/assets/runtime-engine/tool/output identities. Installation git
  dirty/clean is informational and excluded from the subject digest.
- `make_record(snapshot, kind, producer, result, coverage, *, artifacts=None)
  -> dict`: schema `wongo-evidence/1`, subject+subject_id, producer, result,
  coverage, artifacts, recorded_at and record_id. Artifacts is a list of
  `{path: <project-relative>, sha256: ...}`.
- `save_record(project, record) -> Path`: validate envelope and atomically
  write under `output/.wongo-evidence/<kind>/<record_id>.json`.
- `load_records(project, kind=None, target=None) -> list[dict]`: sorted by
  recorded_at/record_id; validates records. Malformed records raise InputError.
- `verify_record(project, record, *, current=None) -> dict`: validates
  subject/hash/artifact bindings, returns `{state: fresh|stale|invalid, detail}`.
  Never executes external code. A provided current snapshot avoids repeated work.
- `safe_path(root, raw, *, must_exist=True) -> Path`: relative path inside
  root, rejects traversal/absolute/symlink escape; actionable InputError.

Each kind owns its result/coverage shape. Failed assertions are recorded results,
not successful observations. A fresh record can still contain failed assertions.
Metadata normalization is separate from exact subject binding.

## Work ownership

- Root: evidence.py, review export, evidence_cli.py, main cli.py integration,
  MCP adapters, docs/ledgers, cross-feature tests.
- Audit worker: audit.py, audit_helpers.py, engine/inputs.py audit input
  tracking, audit tests. `run_audits(project, target='submission', name=None)`
  returns JSON-able `{ok, records, paths, ...}`. `_journal.yml audits` list:
  `{id, script, inputs: [...], required: bool=false, timeout: positive int=120}`.
  Scripts/inputs are declared source inputs; use scratch copies, provide
  WONGO_AUDIT_PROJECT, WONGO_AUDIT_OUTPUTS, WONGO_AUDIT_RESULT (JSON result file).
  No shell commands. Python scripts use sys.executable. Results declare
  assertions with contextual evidence, coverage checked/untested, no generic
  scientific-validation claim. Script identity+inputs bind producer. Scripts
  must not mutate snapshots or live input/output files. No execution from status.
- QA worker: qa.py, qa_cli.py, toolchain.py QA tools, QA tests.
  `inspect_outputs(project,target)` produces kind `inspection` record with
  OOXML image/alt/text/table/math/revision inventory and declared coverage.
  `create_preview(project,target,...)` produces kind `preview` record with
  renderer/version/settings, PDF/pages/images hashes. CLI qa inspect|preview|
  review via `add_parsers(sub,common)`. Visual review kind `visual-review`
  names preview record, page hashes, reviewer, time, checked/untested pages;
  deliberate human interaction. Preview reuse requires exact renderer/settings
  and relevant page bytes, never certifies native Word pagination from conversion.
- Gate worker: gates.py, gates_cli.py, status.py, gate/status tests.
  Config `manual_gates` list `{id, label, required: bool=true}`. Proposals are
  `gate-proposal` records. Human-confirmed decisions are `approval` records
  binding gate definition+subject, attribution, decision approved|rejected,
  evidence references and time. `gates review` interactive only, no MCP approval
  operation. CLI `gates status|propose|review` via add_parsers. Status exposes
  technical/audit/visual/author_decisions independently, missing evidence as
  not-recorded, mismatches stale. Optional requirements via config audit.required
  and `visual_review_required: true`. No author approval from absent config.
  Locally attributed records are not authenticated identity or signatures.

Workers do not edit shared ledgers, main CLI or MCP files. All add meaningful
regression/acceptance tests and run focused checks. Root integrates adapters.
