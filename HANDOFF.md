<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-27 release preparation and artifact smoke
last_worker: codex
handoff_id: release-v040-prepared-20261027
supersedes: si-references-complete-20261024

## Goal
Publish v0.4.0 on GitHub. User authorized release branch push, PR/merge after CI, tag and wheel/sdist/checksum publication. PyPI is excluded.

## Last verified state
- T-0039–T-0041 integration is committed as 7075a17; version preparation is 79c293f on codex/release-v040.
- Isolated integration: 889 passed, 4 skipped; release metadata/front-door tests: 16 passed. Full Ruff and clean-export wheel/sdist builds passed.
- Wheel Python source matches clean export; version/profile smoke passed; unrelated five profiles excluded. Original dirty tree and worksheet E713 remain untouched.
- Release metadata is synchronized to 0.4.0 in package, citation, lockfile and plugin; README installs the v0.4.0 tag.
- User explicitly waived private-reference parity for v0.4.0 and deferred native Windows/Korean-account/Word pilot to a future release. Neither check is claimed as passed.
- Release branch is pushed. Remote CI must pass before merge; final tag/release and uploaded digests still need verification.

## Next action
1. Finish remote CI, address concrete failures, merge the release PR, and build/verify final artifacts from the selected release revision.
2. Publish v0.4.0 with checksums, verify tag/release target and downloaded asset hashes.
3. Record final release evidence in notes/release-v040-2026-10-27.md. T-0022/T-0025 and future private parity remain separate.

## Gotchas
- Plain check exits 0 for JSON ok:false; strict exits 1. Native crossref warnings can promote collab; mid-render drift refuses both targets.
- Engine returns results/WongoError; CLI/MCP own output. Render promotion is transactional. Wongo never applies worksheet decisions to QMD.
- Evidence and agent proposals do not confer human approval or scientific validity. Converted previews do not certify native Word layout.

## Do not touch
- Original checkout's worksheet/profile/research/AIX/agent work; worksheet E713; private manuscript; plans/archive/; frozen CHANGELOG.
