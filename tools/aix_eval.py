#!/usr/bin/env python3
"""Reproducible checks of the local AIX demo, with failures reflected in exit status.

Discovery uses a real stdio client. Other dimensions exercise the engine against
scratch copies. This is a fixture regression benchmark, not a measurement of LLM
accuracy, time saved, journal acceptance, or release-to-release render parity.
Use tools/bytecompare.py for the separate reference-manuscript parity gate.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from wongo import __version__
from wongo.engine import render_project
from wongo.engine.checks import run_checks
from wongo.engine.roundtrip import extract
from wongo.engine.worksheet import Worksheet
from wongo.errors import GateError
from wongo.mcp.resources import worksheet_uri
from wongo.textio import read_text

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "wongo_status": {"project"},
    "wongo_doctor": {"project"},
    "wongo_scaffold": {"dest", "journal"},
    "wongo_profile_get": {"slug"},
    "wongo_check": {"project", "strict"},
    "wongo_render": {"project", "target"},
    "wongo_roundtrip": {"docx_path", "project", "qmd"},
    "wongo_worksheet_status": {"file"},
    "wongo_worksheet_set": {"file", "row", "disposition"},
    "wongo_worksheet_batch_propose": {"file", "proposals"},
    "wongo_worksheet_lint": {"file"},
    "wongo_diff": {"original", "revised"},
}
EXPECTED_PROMPTS = {
    "wongo-pre-submission-audit": {"project"},
    "wongo-coauthor-review": {"project", "docx_path"},
    "wongo-revision-diff": {"original_docx", "revised_docx"},
}
EXPECTED_RESOURCES = {"wongo://project/status"}
EXPECTED_TEMPLATES = {"wongo://profile/{slug}", "wongo://worksheet/{path}"}
WORKSHEET_PROBE_TEXT = "# Worksheet discovery probe\n\nUTF-8 roundtrip: 원고.\n"


def _copy_demo(demo_dir: Path, destination: Path) -> Path:
    shutil.copytree(demo_dir, destination, ignore=shutil.ignore_patterns(
        "output", "decisions", ".quarto", "*_files", "__pycache__",
    ))
    return destination


def evaluate_discovery(payload: dict) -> dict:
    """Validate the public discovery payload; empty registries must fail."""
    tools = payload["tools"]
    prompts = payload["prompts"]
    tool_names = {tool["name"] for tool in tools}
    prompt_names = {prompt["name"] for prompt in prompts}
    schemas_valid = all(
        tool.get("description")
        and tool.get("inputSchema", {}).get("type") == "object"
        and isinstance(tool["inputSchema"].get("properties"), dict)
        and EXPECTED_TOOLS.get(tool["name"], set()) <= set(tool["inputSchema"]["properties"])
        and set(tool["inputSchema"].get("required", [])) <= set(tool["inputSchema"]["properties"])
        for tool in tools
    )
    prompt_arguments_valid = all(
        prompt.get("description")
        and {arg["name"] for arg in prompt.get("arguments", [])}
        == EXPECTED_PROMPTS.get(prompt["name"])
        for prompt in prompts
    )
    resources = {item["uri"] for item in payload["resources"]}
    templates = {item["uriTemplate"] for item in payload["templates"]}
    checks = {
        "tool_names_match": tool_names == set(EXPECTED_TOOLS) and len(tools) == len(EXPECTED_TOOLS),
        "tool_schemas_valid": bool(tools) and schemas_valid,
        "prompt_names_match": prompt_names == set(EXPECTED_PROMPTS) and len(prompts) == len(EXPECTED_PROMPTS),
        "prompt_arguments_valid": bool(prompts) and prompt_arguments_valid,
        "resource_uris_match": resources == EXPECTED_RESOURCES and templates == EXPECTED_TEMPLATES,
        "resource_reads_valid": payload.get("resource_reads_valid") is True,
        "worksheet_resource_read_valid": payload.get("worksheet_resource_read_valid") is True,
        "prompt_reads_valid": payload.get("prompt_reads_valid") is True,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "tool_count": len(tools), "prompt_count": len(prompts),
        "resource_count": len(payload["resources"]) + len(payload["templates"]),
        "tools": sorted(tool_names), "prompts": sorted(prompt_names), "checks": checks,
    }


async def _worksheet_resource_matches(session: ClientSession) -> bool:
    """Read an encoded absolute worksheet URI without writing into the demo."""
    with tempfile.TemporaryDirectory(prefix="wongo-aix-resource-") as temporary:
        worksheet = Path(temporary) / "merge 원고 probe.md"
        worksheet.write_text(WORKSHEET_PROBE_TEXT, encoding="utf-8")
        result = await session.read_resource(worksheet_uri(worksheet))
        return len(result.contents) == 1 and result.contents[0].text == WORKSHEET_PROBE_TEXT


async def _discover(demo_dir: Path) -> dict:
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "wongo.cli", "mcp", "run"], cwd=demo_dir,
    )
    started = time.perf_counter()
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=30) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            prompts = await session.list_prompts()
            resources = await session.list_resources()
            templates = await session.list_resource_templates()
            status = await session.read_resource("wongo://project/status")
            profile = await session.read_resource("wongo://profile/wr")
            worksheet_matches = await _worksheet_resource_matches(session)
            status_data = json.loads(status.contents[0].text)
            profile_data = json.loads(profile.contents[0].text)
            prompt_results = [
                await session.get_prompt("wongo-pre-submission-audit", {"project": "."}),
                await session.get_prompt("wongo-coauthor-review", {"project": ".", "docx_path": "edits.docx"}),
                await session.get_prompt("wongo-revision-diff", {"original_docx": "old.docx", "revised_docx": "new.docx"}),
            ]
            payload = {
                "tools": [item.model_dump(by_alias=True) for item in tools.tools],
                "prompts": [item.model_dump(by_alias=True) for item in prompts.prompts],
                "resources": [item.model_dump(by_alias=True) for item in resources.resources],
                "templates": [item.model_dump(by_alias=True) for item in templates.resource_templates],
                "resource_reads_valid": status_data.get("is_project") is True and profile_data.get("slug") == "wr",
                "worksheet_resource_read_valid": worksheet_matches,
                "prompt_reads_valid": all(result.messages and result.messages[0].content.text for result in prompt_results),
            }
    return {
        **evaluate_discovery(payload),
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "protocol_version": initialized.protocol_version,
        "sdk_version": version("mcp"),
    }


def benchmark_discovery(demo_dir: Path) -> dict:
    return asyncio.run(_discover(demo_dir))


def benchmark_audit_and_hints(demo_dir: Path) -> dict:
    started = time.perf_counter()
    clean_checks = run_checks(demo_dir)
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    clean_pass = all(c.ok for c in clean_checks if c.level == "HARD")
    with tempfile.TemporaryDirectory(prefix="wongo-aix-audit-") as temporary:
        scratch = _copy_demo(demo_dir, Path(temporary) / "manuscript")
        index = scratch / "index.qmd"
        original = read_text(index)
        index.write_text(original + "\n\n@ghostCite2029 @fig-missingRef ![](figures/nonexistent.png).\n", encoding="utf-8")
        defects = {check.name: check for check in run_checks(scratch)}
        expected = {
            "citekeys": ("add_bibtex", "missing_keys", ["ghostCite2029"]),
            "crossrefs": ("define_labels", "orphan_refs", ["fig-missingRef"]),
            "figures": ("create_assets", "missing_paths", ["figures/nonexistent.png"]),
        }
        measurements = {}
        for name, (action, field, values) in expected.items():
            check = defects.get(name)
            hint = check.patch_hint if check else None
            measurements[name] = bool(check and check.level == "HARD" and not check.ok and hint
                                      and hint.get("action") == action and hint.get(field) == values)
        # Independently exceed WR's source lower bound; do not pretend the three
        # preceding injections exercised the word-limit hint.
        index.write_text(original + "\n\n" + "measurement " * 8001 + "\n", encoding="utf-8")
        word_check = next(check for check in run_checks(scratch) if check.name == "word-limit")
        hint = word_check.patch_hint or {}
        measurements["word-limit"] = (
            not word_check.ok and word_check.level == "HARD"
            and hint.get("action") == "trim_words" and hint.get("target_words") == 8000
            and isinstance(hint.get("excess_words"), int) and hint["excess_words"] > 0
        )
    return {
        "status": "PASS" if clean_pass and all(measurements.values()) else "FAIL",
        "clean_audit_latency_ms": elapsed, "clean_hard_checks_pass": clean_pass,
        "clean_checks_passed": sum(check.ok for check in clean_checks), "total_checks": len(clean_checks),
        "defects_verified": measurements, "verified_defects": sum(measurements.values()),
        "tested_defects": len(measurements),
    }


def benchmark_roundtrip_and_batch(demo_dir: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="wongo-aix-roundtrip-") as temporary:
        scratch = _copy_demo(demo_dir, Path(temporary) / "manuscript")
        fixture = scratch / "from-coauthors" / "coauthor-edits.docx"
        if not fixture.exists():
            return {"status": "FAIL", "error": "coauthor-edits.docx fixture missing"}
        sources_before = {path.name: path.read_bytes() for path in scratch.glob("*.qmd")}
        started = time.perf_counter()
        extracted = extract(fixture, scratch)
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        worksheet = Worksheet.load(extracted.worksheet)
        rows = [row.to_dict(project=scratch) for row in worksheet.rows]
        generated = [row for row in rows if row["kind"] == "replacement"
                     and row["old"] == "12.4" and row["new"] == "approximately 13.1"]
        prose = [row for row in rows if row["kind"] == "insertion"
                 and row["new"] == "under steady-state potentiostatic polarization"]
        exact_edits = extracted.changes == 2 and len(rows) == 2 and len(generated) == len(prose) == 1
        tags_valid = bool(exact_edits and generated[0]["tags"] == ["inline-code"]
                          and generated[0]["word_count_delta"] == 1 and prose[0]["tags"] == []
                          and prose[0]["word_count_delta"] == 4
                          and all(row["line"] and not row["unmatched"] for row in rows))
        checks = {"exact_edits": exact_edits, "source_tags_and_deltas": tags_valid,
                  "initial_pending": worksheet.counts().pending == 2}
        if exact_edits:
            proposals = [
                {"row": generated[0]["row"], "disposition": "fix-code", "rationale": "review the R calculation; preserve generated source"},
                {"row": prose[0]["row"], "disposition": "apply", "rationale": "methodological clarification requires author review"},
            ]
            updated = worksheet.batch_propose(proposals)
            worksheet.save()
            worksheet = Worksheet.load(extracted.worksheet)
            counts = worksheet.counts()
            proposal_lint = worksheet.lint(project=scratch)
            checks["proposals_recorded"] = (
                len(updated) == 2 and counts.proposed == 2 and counts.pending == counts.final == counts.invalid == 0
                and all(worksheet.row(prop["row"]).disposition.proposal == prop["disposition"]
                        and prop["rationale"] in worksheet.row(prop["row"]).disposition.note for prop in proposals)
            )
            checks["proposals_require_decision"] = (
                len(proposal_lint) == 2 and all(problem.severity == "error" for problem in proposal_lint)
                and {problem.row for problem in proposal_lint} == {prop["row"] for prop in proposals}
            )
            # Simulated author decisions exercise the fixture lifecycle; this is
            # not approval of a real manuscript edit and does not change .qmd.
            for proposal in proposals:
                worksheet.decide(proposal["row"], proposal["disposition"])
            worksheet.save()
            worksheet = Worksheet.load(extracted.worksheet)
            final_lint = worksheet.lint(project=scratch)
            checks["final_decisions_and_lint"] = worksheet.counts().final == 2 and not final_lint
        checks["sources_unchanged"] = sources_before == {path.name: path.read_bytes() for path in scratch.glob("*.qmd")}
        return {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "extraction_latency_ms": elapsed, "extracted_changes": extracted.changes,
            "change_kinds": extracted.kinds, "rows": rows, "checks": checks,
        }


def _output_hashes(project: Path) -> dict[str, str]:
    output = project / "output"
    return {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(output.rglob("*")) if path.is_file()}


def benchmark_gate_enforcement(demo_dir: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="wongo-aix-gate-") as temporary:
        scratch = _copy_demo(demo_dir, Path(temporary) / "manuscript")
        started = time.perf_counter()
        collab = render_project(scratch, target="collab", quarto_stdout=2)
        collab_ms = round((time.perf_counter() - started) * 1000, 2)
        submission = render_project(scratch, target="submission", quarto_stdout=2)
        outputs = [*collab.outputs, *submission.outputs]
        snapshot = _output_hashes(scratch)
        index = scratch / "index.qmd"
        index.write_text(read_text(index) + "\n\nInvalid cite [@nonexistent_key_999].\n", encoding="utf-8")
        blocked = False
        gate_check_names = []
        error = None
        try:
            render_project(scratch, target="submission", quarto_stdout=2)
        except GateError as exc:
            gate_check_names = [check.name for check in exc.details.get("checks", [])
                                if check.level == "HARD" and not check.ok]
            blocked = "citekeys" in gate_check_names
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        checks = {
            "clean_outputs_present": len(collab.outputs) == len(submission.outputs) == 2
            and all(Path(output).is_file() and Path(output).stat().st_size > 0 for output in outputs),
            "expected_citekey_gate": blocked,
            "manifest_present": ".wongo-manifest.json" in snapshot,
            "outputs_and_manifest_unchanged": snapshot == _output_hashes(scratch),
            "no_staging_leftovers": not list(scratch.glob(".wongo-stage-*"))
            and not list((scratch / "output").glob(".stage-*")),
        }
        return {
            "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "collab_render_latency_ms": collab_ms, "collab_outputs_count": len(collab.outputs),
            "submission_outputs_count": len(submission.outputs), "failing_gate_checks": gate_check_names,
            "preserved_file_count": len(snapshot), "error": error,
        }


def generate_scorecard(results: dict, out_path: Path) -> None:
    """Every verdict and metric comes from this run; failures remain visible."""
    passed = sum(result.get("status") == "PASS" for result in results.values())
    overall = "PASS" if passed == len(results) == 4 else "FAIL"
    names = {
        "discovery": "Stdio discovery, schemas, resources and prompts",
        "audit": "Injected defects and patch hints",
        "roundtrip": "Exact edits, source tags and decision lifecycle",
        "gate": "Submission refusal and existing-output preservation",
    }
    rows = "\n".join(f"| {names[name]} | {result.get('status', 'FAIL')} |" for name, result in results.items())
    markdown = f"""# Wongo-AIX fixture regression scorecard

- Wongo version: `{__version__}`
- Evaluation time (UTC): `{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}`
- Fixture: `examples/aix-demo` (synthetic demonstration, Water Research profile, kist-wcr style)
- Overall: **{overall}** ({passed}/{len(results)} dimensions passed)

| Measured dimension | Result |
|:---|:---:|
{rows}

Discovery launches a real stdio server and checks the advertised schema and read
surfaces. The other dimensions exercise the engine in fresh temporary projects.
Proposal lint errors are expected until simulated author decisions are recorded;
final lint must be clean. The gate check requires the expected citation GateError
and unchanged hashes of every existing output file, including the manifest.

These are bounded fixture checks. They do not measure LLM decision accuracy,
hallucination rates, time saved, scientific validity, journal acceptance, or
release-to-release XML parity. Run `tools/bytecompare.py` separately for the
reference-manuscript parity gate. SDK and negotiated protocol versions below are
distinct values. Latencies describe this local run and have no pass threshold.

## Measurements from this run

```json
{json.dumps(results, ensure_ascii=False, indent=2)}
```

Generated by `tools/aix_eval.py`; rerun after changing code or fixtures.
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", type=Path, default=ROOT / "examples/aix-demo")
    parser.add_argument("--scorecard", type=Path, default=ROOT / "docs/aix-competition/scorecard.md")
    args = parser.parse_args(argv)
    results = {}
    for name, benchmark in (
        ("discovery", benchmark_discovery), ("audit", benchmark_audit_and_hints),
        ("roundtrip", benchmark_roundtrip_and_batch), ("gate", benchmark_gate_enforcement),
    ):
        print(f"Checking {name}...", flush=True)
        try:
            results[name] = benchmark(args.demo.resolve())
        except Exception as exc:
            results[name] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        print(f"  {results[name]['status']}", flush=True)
    generate_scorecard(results, args.scorecard)
    passed = sum(result.get("status") == "PASS" for result in results.values())
    print(f"{passed}/{len(results)} AIX dimensions passed. Scorecard: {args.scorecard}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
