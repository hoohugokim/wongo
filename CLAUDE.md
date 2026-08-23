# wongo — project instructions

wongo (원고, "manuscript") is a Quarto→journal manuscript pipeline being
uplifted from the `~/.claude/skills/quarto-manuscript-*` Claude Code skills
into a shareable Python package. Private repo, MIT, owner Hoo Hugo Kim (KIST).

**Start with `HANDOFF-wongo-uplift.md`** — it carries the migration map and
the three ground rules. The short version:

1. `legacy/` is verbatim, battle-tested code that produced a real ES&T
   submission. Migrations must keep `tests/` green and byte-compare renders
   against the the reference manuscript manuscript (`~/workbench/the reference manuscript/manuscript`).
2. The live the reference manuscript manuscript stays on the skill scripts until its r0 review
   round closes (`ms-r0-sent` tag). Fix bugs in BOTH places until then.
3. Correctness (OOXML patches) is unconditional engine behavior; taste
   (KIST-WCR house look) lives in `styles/*.yml`. Never blur that line.

Conventions: Python ≥3.11, `uv` for envs/tools, pytest for tests, fish for any
shell snippets. `docs/docx-quirks.md` is compounding memory — append every new
Quarto/pandoc/Word pathology you solve, with root cause and verification method
(raw XML, never python-docx introspection alone).
