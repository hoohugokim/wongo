"""MCP adapter contracts, including an actual JSON-RPC stdio workflow."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from wongo.engine.worksheet import Worksheet
from wongo.mcp.resources import worksheet_uri
from wongo.mcp.server import create_mcp_server


def call(server, name, **arguments):
    return asyncio.run(server.call_tool(name, arguments)).structured_content


def worksheet(project, *, disposition="PROPOSED apply — matched calculation", line=1):
    path = project / "decisions" / "한 글 #100%.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Merge worksheet\n\n## 1. replacement — Reviewer\n"
        f"- location: index.qmd:{line}\n- old: 12.4\n- new: 13.1\n"
        f"- context: Current density was 12.4.\n- disposition: {disposition}\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("final,expected", [
    ("apply", "apply — matched calculation"),
    ("reject: figure contradicts this", "was PROPOSED apply — matched calculation"),
])
def test_mcp_final_decisions_preserve_proposal(tmp_path, final, expected):
    path = worksheet(tmp_path)
    result = call(create_mcp_server(), "wongo_worksheet_set",
                  file=str(path), row=1, disposition=final)
    assert result["ok"] is True
    assert expected in Worksheet.load(path).row(1).disposition.text


def test_mcp_final_decision_requires_force_and_keeps_history(tmp_path):
    path = worksheet(tmp_path, disposition="apply — author approved")
    before = path.read_bytes()
    server = create_mcp_server()
    result = call(server, "wongo_worksheet_set", file=str(path), row=1,
                  disposition="reject: corrected", location=5)
    assert result["ok"] is False
    assert path.read_bytes() == before
    result = call(server, "wongo_worksheet_set", file=str(path), row=1,
                  disposition="reject: corrected", force=True)
    assert result["ok"] is True
    assert "was apply — author approved" in Worksheet.load(path).row(1).disposition.text


@pytest.mark.parametrize("source,line,warning", [
    ("Current density was `r rate`.\n", 1, "inline"),
    ("A short file.\n", 10, "beyond"),
    (None, 1, "not found"),
])
def test_mcp_lint_retains_source_warnings(tmp_path, source, line, warning):
    path = worksheet(tmp_path, disposition="apply", line=line)
    if source is not None:
        (tmp_path / "index.qmd").write_text(source, encoding="utf-8")
    result = call(create_mcp_server(), "wongo_worksheet_lint", file=str(path))
    assert warning in str(result["warnings"])
    assert result["project"] == str(tmp_path)


def test_mcp_resource_roundtrips_unicode_and_reserved_characters(tmp_path):
    path = worksheet(tmp_path)
    server = create_mcp_server()
    result = asyncio.run(server.read_resource(worksheet_uri(path)))
    assert result[0].content == path.read_text(encoding="utf-8")


def test_mcp_stdio_manuscript_workflow(wongo_project, stub_quarto, tmp_path, monkeypatch):
    """Real child process and SDK client; only Quarto/Pandoc are stubbed."""
    extracted = tmp_path / "tracked.md"
    extracted.write_text(
        'Body text cites @doe2020 and shows [a clearer figure]{.insertion author="Reviewer"}.\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("WONGO_STUB_PANDOC_MD_FILE", str(extracted))
    monkeypatch.setenv("WONGO_STUB_QUARTO_STDOUT", "render diagnostic on stdout")
    log = tmp_path / "server-stderr.log"

    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "wongo.cli", "mcp", "run"],
            cwd=Path(__file__).resolve().parents[1], env=dict(os.environ),
        )
        with log.open("w", encoding="utf-8") as stderr:
            async with stdio_client(params, errlog=stderr) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=30) as session:
                    await session.initialize()
                    render = await session.call_tool("wongo_render", {
                        "project": str(wongo_project), "target": "submission",
                    })
                    data = render.structured_content
                    assert data["ok"] is True, data
                    assert len(data["outputs"]) == 2
                    assert all(Path(p).is_file() for p in data["outputs"])
                    result = await session.call_tool("wongo_roundtrip", {
                        "project": str(wongo_project), "docx_path": data["outputs"][0],
                    })
                    data = result.structured_content
                    assert data["ok"] is True, data
                    assert data["changes"] == 1
                    resource = await session.read_resource(data["worksheet_uri"])
                    assert resource.contents[0].text == Path(data["worksheet"]).read_text(
                        encoding="utf-8",
                    )
                    # Failure responses must retain checks and their actionable hints.
                    with (wongo_project / "index.qmd").open("a", encoding="utf-8") as source:
                        source.write("\nMissing cite [@doesNotExist].\n")
                    refusal = await session.call_tool("wongo_render", {
                        "project": str(wongo_project), "target": "submission",
                    })
                    data = refusal.structured_content
                    assert data["ok"] is False
                    assert data["error"]["kind"] == "gate"
                    check = next(c for c in data["checks"] if c["name"] == "citekeys")
                    assert check["ok"] is False
                    assert check["patch_hint"]["action"] == "add_bibtex"

    asyncio.run(run())
    # Quarto chatter reached stderr, never the JSON-RPC stdout stream.
    assert "render diagnostic on stdout" in log.read_text(encoding="utf-8")
