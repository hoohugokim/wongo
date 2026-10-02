"""The AIX evidence harness must fail when its advertised requirements fail."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from wongo.engine.checks import Check
from wongo.engine.worksheet import Row
from wongo.errors import GateError

_PATH = Path(__file__).resolve().parents[1] / "tools" / "aix_eval.py"
_SPEC = importlib.util.spec_from_file_location("aix_eval", _PATH)
aix = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(aix)


def discovery_payload():
    return {
        "tools": [{"name": name, "description": "Tool description", "inputSchema": {
            "type": "object", "properties": {prop: {"type": "string"} for prop in properties},
        }} for name, properties in aix.EXPECTED_TOOLS.items()],
        "prompts": [{"name": name, "description": "Workflow description",
                     "arguments": [{"name": arg} for arg in arguments]}
                    for name, arguments in aix.EXPECTED_PROMPTS.items()],
        "resources": [{"uri": uri} for uri in aix.EXPECTED_RESOURCES],
        "templates": [{"uriTemplate": uri} for uri in aix.EXPECTED_TEMPLATES],
        "resource_reads_valid": True, "prompt_reads_valid": True,
        "worksheet_resource_read_valid": True,
    }


def test_discovery_requires_advertised_contract():
    payload = discovery_payload()
    assert aix.evaluate_discovery(payload)["status"] == "PASS"
    payload["tools"][0]["inputSchema"]["properties"] = {}
    assert aix.evaluate_discovery(payload)["status"] == "FAIL"


@pytest.mark.parametrize("surface", ["tools", "prompts", "resources", "templates"])
def test_discovery_rejects_empty_registries(surface):
    payload = discovery_payload()
    payload[surface] = []
    assert aix.evaluate_discovery(payload)["status"] == "FAIL"


@pytest.mark.parametrize("matches", [True, False])
def test_worksheet_resource_content_controls_discovery_verdict(matches):
    class Session:
        async def read_resource(self, uri):
            assert uri.startswith("wongo://worksheet/")
            assert "%20" in uri and "%" in uri
            text = aix.WORKSHEET_PROBE_TEXT if matches else "# Wrong worksheet\n"
            return SimpleNamespace(contents=[SimpleNamespace(text=text)])

    payload = discovery_payload()
    payload["worksheet_resource_read_valid"] = asyncio.run(aix._worksheet_resource_matches(Session()))
    assert aix.evaluate_discovery(payload)["status"] == ("PASS" if matches else "FAIL")


@pytest.fixture
def demo(tmp_path):
    root = tmp_path / "demo"
    root.mkdir()
    (root / "index.qmd").write_text(
        "Methods were measured.\nGenerated rate `r calculated_value`.\n", encoding="utf-8",
    )
    (root / "from-coauthors").mkdir()
    (root / "from-coauthors/coauthor-edits.docx").write_bytes(b"stub fixture")
    return root


def fake_extract(fixture, project):
    worksheet = project / "decisions" / "merge-test.md"
    worksheet.parent.mkdir()
    worksheet.write_text(
        "# Merge worksheet\n\n"
        "## 1. insertion — Example\n"
        "- location: index.qmd:1\n- old: —\n"
        "- new: under steady-state potentiostatic polarization\n"
        "- context: Methods were measured.\n- disposition: PENDING\n\n"
        "## 2. replacement — Example\n"
        "- location: index.qmd:2\n- old: 12.4\n- new: approximately 13.1\n"
        "- context: Generated rate 12.4.\n- disposition: PENDING\n",
        encoding="utf-8",
    )
    return SimpleNamespace(worksheet=worksheet, changes=2, kinds={"insertion": 1, "replacement": 1})


def test_roundtrip_requires_source_tags_and_final_lint(monkeypatch, demo):
    monkeypatch.setattr(aix, "extract", fake_extract)
    result = aix.benchmark_roundtrip_and_batch(demo)
    assert result["status"] == "PASS", result
    original = Row.to_dict

    def without_tags(self, **kwargs):
        return {**original(self, **kwargs), "tags": []}

    monkeypatch.setattr(Row, "to_dict", without_tags)
    result = aix.benchmark_roundtrip_and_batch(demo)
    assert result["status"] == "FAIL"
    assert result["checks"]["source_tags_and_deltas"] is False


def test_roundtrip_rejects_extra_changes(monkeypatch, demo):
    def extra_change(fixture, project):
        result = fake_extract(fixture, project)
        result.changes = 3
        return result

    monkeypatch.setattr(aix, "extract", extra_change)
    result = aix.benchmark_roundtrip_and_batch(demo)
    assert result["status"] == "FAIL"
    assert result["checks"]["exact_edits"] is False


@pytest.mark.parametrize("failure", ["expected", "unexpected", "wrong-gate", "leaked-output", "changed-manifest"])
def test_gate_requires_expected_error_and_preserved_outputs(monkeypatch, demo, failure):
    calls = []

    def render(project, target, **kwargs):
        calls.append(target)
        output = project / "output"
        output.mkdir(exist_ok=True)
        if len(calls) == 3:
            if failure == "unexpected":
                raise TypeError("adapter bug is not a successful gate")
            if failure == "leaked-output":
                (output / "leaked.docx").write_bytes(b"partial")
            if failure == "changed-manifest":
                (output / ".wongo-manifest.json").write_bytes(b"changed")
            name = "word-limit" if failure == "wrong-gate" else "citekeys"
            raise GateError("refused", checks=[Check(name, "HARD", False, "bad source")])
        paths = [output / f"{name}-{target}.docx" for name in ("main", "si")]
        for path in paths:
            path.write_bytes(b"valid prior output")
        (output / ".wongo-manifest.json").write_bytes(b"manifest")
        return SimpleNamespace(outputs=paths)

    monkeypatch.setattr(aix, "render_project", render)
    result = aix.benchmark_gate_enforcement(demo)
    assert result["status"] == ("PASS" if failure == "expected" else "FAIL"), result


@pytest.mark.parametrize("status", ["PASS", "FAIL"])
def test_main_exit_and_scorecard_reflect_all_results(monkeypatch, tmp_path, capsys, status):
    for name in ("discovery", "audit_and_hints", "roundtrip_and_batch", "gate_enforcement"):
        monkeypatch.setattr(aix, "benchmark_" + name, lambda _: {"status": status})
    scorecard = tmp_path / "scorecard.md"
    assert aix.main(["--scorecard", str(scorecard)]) == (0 if status == "PASS" else 1)
    text = scorecard.read_text(encoding="utf-8")
    assert f"Overall: **{status}**" in text
    assert "100%" not in text
    assert f"{4 if status == 'PASS' else 0}/4 AIX dimensions passed" in capsys.readouterr().out


def test_main_records_exception_and_continues_other_dimensions(monkeypatch, tmp_path):
    calls = []

    def broken(_):
        raise RuntimeError("connection failed")

    def passing(_):
        calls.append("continued")
        return {"status": "PASS"}

    monkeypatch.setattr(aix, "benchmark_discovery", broken)
    for name in ("audit_and_hints", "roundtrip_and_batch", "gate_enforcement"):
        monkeypatch.setattr(aix, "benchmark_" + name, passing)
    scorecard = tmp_path / "scorecard.md"
    assert aix.main(["--scorecard", str(scorecard)]) == 1
    assert len(calls) == 3
    assert "RuntimeError: connection failed" in scorecard.read_text(encoding="utf-8")
    assert "3/4 dimensions passed" in scorecard.read_text(encoding="utf-8")
