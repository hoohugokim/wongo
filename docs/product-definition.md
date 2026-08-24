# Wongo product definition (v0.1.0)

> One-sentence positioning: **Wongo is a Python package that ships a CLI research-software pipeline and an extensible pipeline framework for verified journal-manuscript production.**

This file is the canonical answer to "is it a software / framework / package?" — the answer is *all three, at different layers*. Use the layer that matches your context (citation vs installation vs extension).

## Taxonomy

| Layer | What Wongo is | What to do with it | Where it lives |
|---|---|---|---|
| **Distribution (package)** | A Python package `wongo` (wheel `wongo-0.1.0-py3-none-any.whl`, sdist `wongo-0.1.0.tar.gz`), built with `hatchling`, `src/` layout, `pyproject.toml:3` declares `requires-python >=3.11`, MIT, owner Hoo Hugo Kim (KIST). Name `wongo` was free on PyPI 2026-08-24 and is reserved for a future public release; the current distribution is private (GitHub Release `v0.1.0`, `uv tool install` / `pip install` from a local checkout or wheel, not PyPI). | Install: `uv tool install --editable .` or `pip install dist/wongo-0.1.0-py3-none-any.whl` | `pyproject.toml`, `src/wongo/`, `dist/` |
| **Runnable (research software)** | An installed CLI `wongo` (`project.scripts: wongo = "wongo.cli:main"`) that runs locally — no server, no SaaS. Deterministic local transforms: Quarto → docx → python-docx post-processing (`wongo.docxpatch` unconditional OOXML fixes, `wongo.styles` house look) → validation (`wongo check`) → round-trip extraction (`wongo roundtrip`). Cite as software (see `CITATION.cff` when added; until then cite the GitHub Release `hoohugokim/wongo@v0.1.0` with the `src/wongo/` commit hash). | Run: `wongo scaffold`, `wongo check`, `wongo render --target collab|submission`, `wongo roundtrip <docx>`, `wongo profile list|verify` | `~/.local/bin/wongo`, `src/wongo/cli.py:1` |
| **Architecture (pipeline framework)** | An opinionated lifecycle framework S1 Scaffold → S2 Author → S3 Render → S4 Round-trip → S5 Submit → S6 Revise, driven by declarative data: verified journal profiles (`src/wongo/profiles/<slug>/profile.yml` satisfying `docs/journal-profile-contract.md:1`) and house styles (`src/wongo/styles/*.yml` via `wongo.styles`). Extending Wongo means adding a profile/style that satisfies the contract — you do not subclass code. The framework ships 7 verified profiles (`est`, `wr`, `npjcw`, `natwater`, `microbiome`, `envmicrobiome`, `npjbiofilms`) and 2 styles (`kist-wcr`, `default`). | Extend: add `src/wongo/profiles/<slug>/` per `CONTRIBUTING.md:26` contract | `src/wongo/profiles/`, `src/wongo/styles/`, `src/wongo/engine/` |
| **Code (library)** | Importable Python library (`import wongo`, `wongo.engine`, `wongo.docxpatch`, `wongo.profiles`, `wongo.styles`, `wongo.engine.checks`) for programmatic use inside Quarto/R/Python manuscript projects. The Claude Code skills at `~/.claude/skills/quarto-manuscript-*` are now thin wrappers that call this library via the CLI and retain only judgment content (`SKILL.md` S4–S6, `references/editorial-framing.md`). | Import: `from wongo.profiles import load_profile` etc. | `src/wongo/` |

## What Wongo is not

- **Not a SaaS / web service.** Nothing leaves the machine except the optional `wongo profile verify` live `HEAD` against a profile's official `sources` URLs (and `--offline` skips it).
- **Not a Quarto extension or Word add-in.** It drives `quarto render` with `-M reference-doc` / `-M csl` and post-processes the docx with `python-docx` + raw OOXML zip passes.
- **Not a general-purpose publishing framework** (like a web or data framework you build arbitrary apps on). It is a *manuscript-pipeline* framework — narrow, opinionated, and verified per journal. The extension surface is intentionally small (profiles/styles satisfying a contract), not a plugin API.
- **Not the Claude Code skill itself anymore.** The skills (`quarto-manuscript-sci` + `quarto-manuscript-<slug>`) were the incubator; since `v0.1.0` the canonical implementation is this package (`src/wongo/`), and the skills are wrappers. `docs/docx-quirks.md:1` is the canonical quirks memory; `HANDOFF-wongo-uplift.md:1` is retained as historical record.

## How to refer to Wongo (by audience)

- **For installation docs / `pyproject.toml` / GitHub:** "Python package `wongo`" (distribution).
- **For methods sections / citations / grant reports:** "research software `wongo` (CLI `wongo`, Python package, `hoohugokim/wongo` `v0.1.0`)" — cite the GitHub Release DOI/commit, not the skill name.
- **For extension docs / `CONTRIBUTING.md`:** "pipeline framework" — "add a journal profile that satisfies `docs/journal-profile-contract.md`" / "add a house style in `src/wongo/styles/`".
- **For code docs / API references:** "library `wongo`" — "import `wongo.engine`".

If one label is required (e.g., PyPI classifier, keyword): use **"manuscript pipeline (Python package and CLI)"** as the primary, with keywords `quarto`, `manuscript`, `docx`, `journal`, `publishing`, `reproducible-research`, `research-software`, `pipeline-framework` (see `pyproject.toml:9`).

## Distribution status (2026-08-24)

- **Version:** `0.1.0` (`src/wongo/__init__.py:3`, `pyproject.toml:3`, tag `v0.1.0`, GitHub Release `wongo v0.1.0` with wheel + sdist — private repo).
- **Install (private):** `uv tool install --editable .` (dev) or `uv tool install dist/wongo-0.1.0-py3-none-any.whl` / `pip install -e .`. PyPI publication is deferred (name `wongo` reserved, not yet published) — see `CHANGELOG.md:33` and `HANDOFF-wongo-uplift.md:63`.
- **First consumer:** the the reference manuscript manuscript (`~/workbench/the reference manuscript/manuscript`, now pinned `style: kist-wcr` in `_journal.yml`, tag `ms-r0-initial` baseline) — byte-compared via `tools/bytecompare.py:1`.

## Relation to the Claude Code skills

| Before `v0.1.0` (incubator) | Since `v0.1.0` (canonical) |
|---|---|
| Logic lived in `~/.claude/skills/quarto-manuscript-sci/scripts/` and `~/.claude/skills/quarto-manuscript-<slug>/` (verbatim `legacy/` in the repo) | Logic lives in `src/wongo/` (shipped as wheel data); `legacy/` removed (`f1e4e54`) |
| `~/.claude/skills/quarto-manuscript-*` were authoritative for the reference manuscript until `ms-r0-sent` | `~/.claude/skills/quarto-manuscript-*` are thin wrappers calling `wongo` CLI; judgment content (`SKILL.md` S4 disposition rules, `references/submission-checklist.md`, `references/editorial-framing.md`) retained, machine-readable `profile.yml`/`assets/` now pointers to `wongo` |
| `references/quarto-docx-quirks.md` in the skill was the quirks memory | `docs/docx-quirks.md` is canonical; skill's file is a pointer |

## Consequences for contributors

- Add a journal: follow `docs/journal-profile-contract.md:1` and `CONTRIBUTING.md:26` — create `src/wongo/profiles/<slug>/` with `profile.yml` (every hard number traces to `sources` + `verified_date`), `assets/reference.docx` (via `scripts/build_reference_docx.py`), `assets/*.csl`, `SKILL.md`, `references/`.
- Add a house look: add `src/wongo/styles/<name>.yml` per `wongo.styles` schema (`kist-wcr.yml` is the KIST Water Cycle Research look; `default.yml` is the no-taste baseline).
- Fix a rendering bug: append the pathology to `docs/docx-quirks.md:1` with raw XML verification (never `python-docx` alone) and pin with a test in `tests/`; OOXML fixes belong in `wongo.docxpatch` (unconditional), taste belongs in `wongo.styles` (never blur — `CONTRIBUTING.md:9`).
