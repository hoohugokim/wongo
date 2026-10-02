<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-02 by local engine/brand gates, ancestry audit, documentation links and Statutor
last_worker: codex
last_machine: unknown
handoff_id: v031-main-integration-20261002
supersedes: brand-integration-20261002

## Goal
Integrate v0.3.1 into main and trim feature branches, authorized by the maintainer on 2026-10-02.

## Last verified state
- v0.3.1 combines the reference-inclusive count gate, five review fixes, audited MCP workflows and approved brand identity.
- AIX fixes are `dece132`; brand integration is `ba54a39`; the integration PR preserves their commit history.
- Approved identity v1.0.0 in `brand/`: outlined SVG/PNG logos, local fonts, tokens, CSS, Quarto example and licenses.
- Setup docs target v0.3.1 source on main; the latest tagged release remains v0.3.0 and PyPI publication is pending.
- All 33 generated assets rebuilt byte-identically; updated Quarto example rendered and inspected in browser.
- Branding is opt-in for communications; journal profiles, manuscript styles and engine behavior are unchanged.
- Prior engine verification: 528 tests passed, 6 skipped; 2 real Quarto/MCP tests; four benchmark dimensions passed.
- Fresh v0.3.0 reference comparison: 95 parts across four DOCX files byte-identical; live manuscript unchanged.
- Evidence: notes/aix-audit-revision-2026-10-02.md and notes/brand-integration-2026-10-02.md.
- All four local feature tips and three origin feature tips are contained in the integration history; no stashes or other worktrees.
- The maintainer considers the 공모신청서 update complete and is conducting human review; no agent work remains there.

## Next action
1. Complete T-0025 native Windows/client smoke; CI render checks do not cover the native UI or Korean user account.
2. T-0022: PyPI publishing needs maintainer setup; a v0.3.1 release tag is a separate step from the main merge.

## Gotchas
- SDK version and MCP protocol version differ; use the returned worksheet_uri verbatim.
- Row source alignment is unverified; tags are review hints, never scientific approval.
- The synthetic benchmark establishes workflow checks, not scientific validity, LLM accuracy or measured time savings.
- Copy the complete brand folder for offline HTML/Quarto reuse; SVG logos are independently portable.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries, reference manuscripts.
