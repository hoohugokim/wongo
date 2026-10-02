# Wongo-AIX synthetic manuscript demo

This project exercises the Water Research profile and kist-wcr house style with
synthetic data and illustrative scientific prose. It is software demonstration
material, not evidence of real experiments or a manuscript ready for submission.
Verify all science and references before adapting it to research.

Use the development checkout containing the MCP changes. From the repository root:

```fish
uv sync --all-extras
uv run wongo doctor --project examples/aix-demo
uv run python tools/aix_eval.py
```

The benchmark operates on temporary copies. It connects to a real stdio MCP
server for discovery, injects four source defects, checks the exact coauthor edits
and decision lifecycle, and verifies that a refused submission render preserves
existing outputs and their manifest. Failures return exit status 1. Results go
to `docs/aix-competition/scorecard.md`.

The tracked-change fixture is generated from an actual Quarto/R render:

```fish
uv run python examples/aix-demo/generate_coauthor_fixture.py
```

Its first row inserts “under steady-state potentiostatic polarization” in Methods.
Its second changes the generated current density `12.4` to “approximately 13.1”.
Source-aware inspection should tag the second row `inline-code`; propose reviewing
the R calculation rather than replacing it with a literal number. These are
simulated coauthor requests, not approved corrections.

To inspect the workflow manually:

```fish
uv run wongo roundtrip examples/aix-demo/from-coauthors/coauthor-edits.docx --project examples/aix-demo
uv run wongo mcp install --client vscode --project examples/aix-demo
uv run wongo render --target submission --project examples/aix-demo
```

Open `examples/aix-demo` in VS Code after installation. Use the actual worksheet
path and `worksheet_uri` returned by the MCP roundtrip tool. Proposals require
explicit author decisions; Wongo never applies them to the manuscript source.
Water Research submission output omits line numbers, while collaboration output
may keep the house style's line numbers.

This benchmark does not measure LLM accuracy or human time savings. Run
`tools/bytecompare.py` separately for reference-manuscript XML parity. See the
[demo script](../../docs/aix-competition/demo-script.md) and
[presentation outline](../../docs/aix-competition/presentation-deck.md) for
recording instructions and the current development-release limitations.
