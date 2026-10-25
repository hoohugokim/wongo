<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-24 preservation, final-wheel source identity and ledger checks; behavior verified 2026-10-23 (985 full-suite passes then 32 focused passes)
last_worker: codex
last_machine: unknown
handoff_id: si-references-complete-20261024
supersedes: si-references-paused-20261023

## Goal
T-0041 implementation and resumed review are complete locally. T-0039/T-0040 remain complete. HEAD is still 8590fe3; all changes remain uncommitted.

## Last verified state
- T-0041/D-0019: si_references: true enables [SI item](wongo-si:tbl-label) / fig-label. New engine/si_refs.py resolves final bookmarked SI captions after declared transforms, before final checks/sealing; source stays unchanged.
- docs/si-references.md and two test_si_refs files cover the interface; notes/T-0041-completion.md records closure. Manifest binds SI hash, main before/after and labels; missing resolution identity is stale. T-0041 is done.
- Full real-Quarto suite: 985 passed, 4 skipped. Final audit then reproduced nested data styled Caption supplying a false label; fixed by matching the float's table context. All 32 SI-reference tests passed afterward, including real generated/reordered tables, figure and footnote links for both targets.
- Latest synthetic parity vs 8590fe3: 52 parts identical for both targets/main+SI; generated SI reorder passed (scratch wongo-f1-f4-acceptance-3ec90mu0). Private reference unset; Windows/Word still unperformed.
- Final wheel/sdist and changed-file Ruff pass. Resumed review found the three implementation files byte-identical to the final wheel; passing tests were not repeated. Full Ruff still reports only existing worksheet.py:1129 E713; leave it.
- Initial T-0041 dirty-file SHA inventory: /private/tmp/wongo-t0041-before.json (245 files). Resumed comparison: 239 unchanged, six intended integration/ledger edits, no missing files. Unrelated worksheet/profiles/research/AIX/agent work preserved.
- No staging, commit, push, installation or private manuscript/data edits. Prior evidence/AIX acceptance is in notes/T-0040-completion.md; T-0022/T-0025 remain open.

## Next action
1. Review the intended commit boundary for T-0039/T-0040/T-0041 before staging or committing; do not conflate these local changes with 8590fe3.
2. Private parity and native Windows/Word remain release prerequisites. No release, publication or commit has been authorized.
3. T-0041 creates plain text references, not cross-file Word hyperlinks. Additional reference types or localized captions require a separate scope.

## Gotchas
- Plain check exits 0 even JSON ok:false; --strict exits 1. Collab crossrefs-rendered failures still promote and record checks_failed. Mid-render drift refuses both targets.
- Audit and preview are explicit only; check/status/render never execute them. Trusted scripts have local process permissions; scratch copies are not an OS sandbox.
- No MCP approval/disposition confirmation tool. Human gates/native Word inspection are local attestations, not authenticated signatures; proposals never approve.
- Submission approval requires the submission target, technical/required evidence and configured human gates; coauthor rows remain explicit. Converted previews never certify Word layout.
- Exports default to records/identities, not raw dependencies/full extracted text; contexts, descriptions and claims can contain project content. Review before sharing.
- Existing source estimates/manual rule limits and D-0008/D-0009 remain. style_override distinguishes explicit/configured styles; manifest format stays 1. No version bump/release authorization.

## Do not touch
- plans/archive/, frozen CHANGELOG, existing quirks, worksheet E713, agent state, private reference/accepted manuscript, and unrelated dirty work.
