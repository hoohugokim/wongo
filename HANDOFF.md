<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-02 by pytest (480 passed, 4 skips), ruff, build, aix_eval
last_worker: antigravity
last_machine: unknown
handoff_id: aix-phases-1-4-20261002
supersedes: v031-patches-20261002

## Goal
Implement Phases 1-4 of Wongo LLM Work Surfaces (Wongo-AIX) for the KIST internal AIX competition.

## Last verified state
- Phase 1: Native MCP server (MCP 2.x standard, `wongo mcp run`, `wongo mcp install`, 12 tools, 3 prompts, resources).
- Phase 2: Actionable patch hints on `Check`, worksheet batch propose with semantic change tagging, `.vscode/mcp.json`.
- Phase 3: Turnkey showcase manuscript (`examples/aix-demo`, *Water Research*, `kist-wcr` style) & benchmark (`tools/aix_eval.py`).
- Phase 4: KIST presentation deck (`presentation-deck.md`), 3-min video script (`demo-script.md`), scorecard (`scorecard.md`).
- Verified: 480 passed tests, ruff green, `uv run python tools/aix_eval.py` passed 100%, `statutor-doctor .` clean.

## Next action
1. Commit branch `feat/v0.3.1-review-patches` with clean split commits.
2. Record 3-minute video presentation following `docs/aix-competition/demo-script.md`.
3. T-0022: Publish v0.3.1 to PyPI after maintainer credentials setup.

## Gotchas
- MCP 2.x server runs via `wongo.mcp.server.create_mcp_server()`; tools catch `WongoError` and return `{ok, ...}`.
- Worksheet batch propose preserves established final decisions unless `force=True`.
- Word track-changes extraction requires pandoc installed and accessible via toolchain.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries, reference manuscripts.
