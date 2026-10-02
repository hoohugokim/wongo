<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-03 by main CI/CodeQL, release metadata checks and recorded engine/brand gates
last_worker: codex
last_machine: unknown
handoff_id: release-v031-20261003
supersedes: v031-main-integration-20261002

## Goal
Deliver the v0.3.1 GitHub release, authorized by the maintainer on 2026-10-03 (T-0034).

## Last verified state
- v0.3.1 integration merged in PR #5 as `5710f2f`; main CI/CodeQL passed; all prior feature branches were removed.
- AIX fixes are `dece132`; brand integration is `ba54a39`; the integration PR preserves their commit history.
- Approved identity v1.0.0 in `brand/`: outlined SVG/PNG logos, local fonts, tokens, CSS, Quarto example and licenses.
- Release metadata and installation guidance target v0.3.1; PyPI publication remains T-0022.
- All 33 generated assets rebuilt byte-identically; updated Quarto example rendered and inspected in browser.
- Branding is opt-in for communications; journal profiles, manuscript styles and engine behavior are unchanged.
- Prior engine verification: 528 tests passed, 6 skipped; 2 real Quarto/MCP tests; four benchmark dimensions passed.
- Fresh v0.3.0 reference comparison: 95 parts across four DOCX files byte-identical; live manuscript unchanged.
- Release record: notes/release-v031-2026-10-03.md and https://github.com/hoohugokim/wongo/releases/tag/v0.3.1.
- Engine/brand evidence: notes/aix-audit-revision-2026-10-02.md and notes/brand-integration-2026-10-02.md.
- The maintainer considers the 공모신청서 update complete and is conducting human review; no agent work remains there.

## Next action
1. The maintainer will tackle T-0025 native Windows/client smoke and T-0022 PyPI setup afterwards.
2. Use v0.3.1 as the reference baseline for future render changes; the comparison allowlist is empty.

## Gotchas
- SDK version and MCP protocol version differ; use the returned worksheet_uri verbatim.
- Row source alignment is unverified; tags are review hints, never scientific approval.
- The synthetic benchmark establishes workflow checks, not scientific validity, LLM accuracy or measured time savings.
- Copy the complete brand folder for offline HTML/Quarto reuse; SVG logos are independently portable.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries, reference manuscripts.
