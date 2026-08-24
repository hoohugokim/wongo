# wongo — project instructions

wongo (원고, "manuscript") is a Quarto→journal manuscript pipeline being
uplifted from the `~/.claude/skills/quarto-manuscript-*` Claude Code skills
into a shareable Python package. Private repo, MIT, owner Hoo Hugo Kim (KIST).

**Start with `HANDOFF-wongo-uplift.md`** — it carries the migration map and
the three ground rules. The short version:

1. Behavior is pinned. The ES&T submission engine that lived in `legacy/`
   is now in `src/wongo/` (`legacy/` removed in v0.1.0). Every change must
   keep `tests/` green and byte-compare renders against the the reference manuscript manuscript
   (`~/workbench/the reference manuscript/manuscript`, now pinned `style: kist-wcr`).
2. the reference manuscript now uses `wongo` directly (post-`ms-r0-sent` wiring); the
   `~/.claude/skills/quarto-manuscript-*` skills are thin wrappers that call the
   installed `wongo` CLI and keep only judgment content. Canonical quirks memory
   is `docs/docx-quirks.md`.
3. Correctness (OOXML patches) is unconditional engine behavior
   (`wongo.docxpatch`); taste (KIST-WCR house look) lives in
   `src/wongo/styles/*.yml` via `wongo.styles`. Never blur that line.

Conventions: Python ≥3.11, `uv` for envs/tools, pytest for tests, fish for any
shell snippets. `docs/docx-quirks.md` is compounding memory — append every new
Quarto/pandoc/Word pathology you solve, with root cause and verification method
(raw XML, never python-docx introspection alone).
