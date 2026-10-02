<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-02 by asset rebuild, Quarto render, browser preview, links, package build and Statutor
last_worker: codex
last_machine: unknown
handoff_id: brand-integration-20261002
supersedes: aix-audit-revision-20261002

## Goal
Publish the verified AIX revision and apply the approved Wongo identity (T-0032, T-0033).

## Last verified state
- AIX audit fixes committed as `dece132` and pushed with maintainer approval to `feat/v0.3.1-review-patches`.
- Approved identity v1.0.0 in `brand/`: outlined SVG/PNG logos, local fonts, tokens, CSS, Quarto example and licenses.
- README, documentation hub, contributor/plugin guides and AIX materials use the identity and distinguish release/development claims.
- All 33 generated assets rebuilt byte-identically; updated Quarto example rendered and inspected in browser.
- Branding is opt-in for communications; journal profiles, manuscript styles and engine behavior are unchanged.
- Prior engine verification: 528 tests passed, 6 skipped; 2 real Quarto/MCP tests; four benchmark dimensions passed.
- Fresh v0.3.0 reference comparison: 95 parts across four DOCX files byte-identical; live manuscript unchanged.
- Evidence: notes/aix-audit-revision-2026-10-02.md and notes/brand-integration-2026-10-02.md.

## Next action
1. Review/merge the published development branch; no PR has been opened for this revision.
2. Record the demo from actual outputs; complete T-0025 native Windows/client smoke.
3. T-0022: PyPI publishing needs maintainer setup; these MCP changes are not in a published release.
4. Update the KIST AIX application in its existing KIST 행정 chat using the verified claims and brand kit.

## Gotchas
- SDK version and MCP protocol version differ; use the returned worksheet_uri verbatim.
- Row source alignment is unverified; tags are review hints, never scientific approval.
- The synthetic benchmark establishes workflow checks, not scientific validity, LLM accuracy or measured time savings.
- Copy the complete brand folder for offline HTML/Quarto reuse; SVG logos are independently portable.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries, reference manuscripts.
