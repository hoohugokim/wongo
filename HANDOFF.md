<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-02 by pytest (528 passed, 6 skips), real Quarto/MCP tests, ruff, build, aix_eval, 95-part parity
last_worker: codex
last_machine: unknown
handoff_id: aix-audit-revision-20261002
supersedes: aix-phases-1-4-20261002

## Goal
Address and verify all 14 findings in the audit of Wongo-AIX (T-0032, D-0014).

## Last verified state
- MCP render/default roundtrip/resource URI fixed; Quarto diagnostics stay on stderr; SDK pinned to tested >=2.2.0,<3.
- Client-specific schemas, BOM preservation, atomic config writes and truthful failure status verified.
- Source-aware row tags, proposal history, source lint and structured error details preserved.
- Real Quarto/R computed-value fixture; benchmark fails on unmet checks; demo/script/scorecard claims revised.
- 528 default tests passed; 2 opt-in real Quarto/MCP tests passed; Ruff, build and minimum-SDK wheel smoke passed.
- Fresh v0.3.0 reference comparison: 95 parts across four DOCX files byte-identical; live manuscript unchanged.
- Evidence map and limitations: notes/aix-audit-revision-2026-10-02.md.

## Next action
1. Review the local AIX revision before publication; prior T-0003 publication approval remains outstanding.
2. Record the demo from actual outputs; complete T-0025 native Windows/client smoke.
3. T-0022: PyPI publishing needs maintainer setup; these MCP changes are not in a published release.

## Gotchas
- SDK version and MCP protocol version are different; use the returned worksheet_uri verbatim.
- Row source alignment is explicitly unverified; tags are review hints, never scientific approval.
- JSONC client configs are preserved unchanged with manual-edit guidance.
- Reference parity scratch copies use substantial space; this verification used independent APFS clones.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries, reference manuscripts.
