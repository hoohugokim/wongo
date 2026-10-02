# AIX audit revision — 2026-10-02

Revision of Gemini's four LLM integration commits (`d20df3e..dedf336`), addressing
all 14 findings from the subsequent audit. D-0014 records the corrected contract;
T-0032 tracks this revision. Changes remain local pending publication.

## Finding-to-evidence map

| Finding | Revision | Verification |
|:---|:---|:---|
| Render adapter always failed | Remove nonexistent `force` argument; route Quarto stdout to stderr | Real stdio render test, stub stdout-isolation regression, real Quarto/R collab and submission outputs |
| Default roundtrip failed | Default source is `index.qmd` | Stdio tests omit `qmd` and extract expected changes |
| Invalid VS Code schema | Emit `servers` and `type: stdio`; retain other clients' schema | Installer and scaffold regressions; packaged asset inspection |
| Worksheet resource paths failed | Return encoded absolute `worksheet_uri`; explicitly permit absolute resource paths while rejecting traversal/NUL | Unicode, spaces and reserved-character tests; real stdio resource reads; benchmark worksheet-content probe |
| Incompatible MCP dependency range | Require tested SDK `>=2.2.0,<3`; refresh lockfile | Isolated built-wheel run with MCP 2.2.0, 12 tools, profile read and scaffold config |
| Generated values lacked tags | Inspect the current matched source line when serializing rows; expose unverified alignment and missing-source context | Source-tag regressions, real Quarto/R computed-value fixture regeneration and extraction |
| Benchmark falsely passed | Assert exact discovery, defects, edits, tags and decision states; aggregate failures into exit 1 | Negative tests for empty registries, missing tags, extra edits, resource mismatch, exceptions and failed dimensions |
| Parity/leak claims were unmeasured | Require citation GateError and unchanged hashes of all existing outputs/manifest; remove benchmark parity claim | Wrong-error, wrong-gate, output-leak and changed-manifest regressions; actual gate benchmark; separate reference parity below |
| Demo contradicted behavior | Synthetic inline-R fixture, correct WR line-number rule, development-install instructions, measured claims | Fresh fixture generation; real submission XML check; revised script, outline and generated scorecard |
| BOM config displaced other servers | BOM-aware read and preserving, atomic update; refuse unparseable config unchanged | BOM and existing-server preservation; invalid JSON/JSONC and failed-replace tests |
| Install failures returned success | Structured client results, aggregate `ok:false`, exit 1 | Partial-success JSON and text CLI tests |
| Decisions lost proposal history | Use `Worksheet.decide` for finals and retain force guard for existing decisions | Confirmation, override, history retention and no-write-on-refusal regressions |
| MCP lint skipped source checks | Infer or explicitly select manuscript project | Inline-code, missing-file and beyond-end warnings through MCP |
| Errors lost actionable details | Preserve stable `err.kind` and JSON-serializable `err.details` | Actual stdio submission refusal retains failed checks and `patch_hint` |

## Verified gates

- Full default suite: **528 passed, 6 skipped**. Four existing skips plus two
  opt-in real-Quarto tests; both added real tests were run separately and passed.
- Real Quarto/R: **2 passed** (fresh computed-value fixture and full MCP demo
  render/roundtrip/resource/source-tag workflow). Added to the cross-platform
  CI end-to-end job; local execution was on macOS, not Windows.
- Ruff and `git diff --check`: clean.
- AIX benchmark: **4/4 dimensions passed**, including exact worksheet resource
  content. `docs/aix-competition/scorecard.md` contains the actual measurements.
- Wheel and sdist build passed. Isolated wheel smoke used the declared minimum
  MCP SDK 2.2.0 and verified tools, profile access and VS Code package data.
- CLI version/profile offline smoke and `statutor-doctor .`: passed.
- Fresh v0.3.0 (`96c386e`) baseline versus revised checkout: **95 parts across
  four DOCX files byte-identical**, with an empty allowlist. Includes main/SI
  collab and submission document, styles and settings XML.

The normal bytecompare copy ran out of disk space while copying the large private
reference repository. Its session-owned scratch copy was removed. The unchanged
harness was then run with a temporary `shutil.copytree` wrapper using macOS APFS
copy-on-write copies (`cp -c -p`), preserving independent scratch files and the
full input tree. The live reference project was never rendered into or edited.
Logs: `/private/tmp/wongo-aix-{baseline,candidate}.log`,
`/private/tmp/wongo-aix-{pytest,benchmark}-final.log`,
`/private/tmp/wongo-aix-real-tests.log`.

Native client UI smoke on Windows remains T-0025. Benchmark results describe the
synthetic fixture; they do not establish LLM accuracy, scientific validity,
journal acceptance or measured researcher time savings. PyPI remains T-0022.
