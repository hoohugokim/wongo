<!-- statutor: plane=state | policy=overwrite_bounded (max 40 lines) | writer=executor | OVERWRITE, NEVER APPEND -->
# HANDOFF

last_verified: 2026-10-02 by pytest (469 passed, 4 skips), ruff, build, CLI/profile smoke
last_worker: antigravity
last_machine: unknown
handoff_id: v031-patches-20261002
supersedes: reference-word-count-20260930

## Goal
Implement review improvements across styles, roundtrip, review CLI, and diff; bump to v0.3.1.

## Last verified state
- All 5 review patches implemented and verified with 469 passed tests (11 new tests):
  1. Title block affiliation labeling supports >26 affiliations via `_index_to_label` (a..z, aa..zz).
  2. Multi-section table geometry in `fix_tables()` resolves per-table section widths.
  3. Roundtrip tracked-changes `SPAN_RE` parses nested bracket citations directly into changes.
  4. `wongo review` supports selective `--row N` and `--pending-only` filtering.
  5. `wongo diff` treats inline math (`m:oMath`), breaks (`w:br`), and tabs (`w:tab`) as rebuildable tokens.
- Bumped version to `v0.3.1` across `__init__.py`, `pyproject.toml`, `CITATION.cff`, and plugin.json.
- Full test suite, ruff linter, CLI smoke, and statutor-doctor pass cleanly.

## Next action
1. Commit v0.3.1 patches and prepare release PR / tag `v0.3.1`.
2. T-0025 needs smoke test on a real Korean-account Windows PC (desktop setup, IME, Word lock).
3. T-0022: PyPI trusted publishing after maintainer account setup.

## Gotchas
- Statutor guard: use editor tools for ledger changes; never append to HANDOFF.md.
- In `wongo diff`, inline equations are treated as atomic tokens wrapped in `w:ins`/`w:del`.
- `wongo review` requires a TTY; script/agent usage uses `wongo worksheet set`.

## Do not touch
- `plans/archive/`, frozen `docs/CHANGELOG.md`, existing `docs/docx-quirks.md` entries (append only),
  `_local/`, the reference repo.
