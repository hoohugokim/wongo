"""The advertised demo through stdio and real Quarto/R, in the CI e2e job."""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = pytest.mark.skipif(
    os.environ.get("WONGO_REAL_QUARTO_TEST") != "1", reason="run in the real-Quarto job",
)


def test_demo_mcp_render_roundtrip_resource_and_source_tags(tmp_path):
    demo = Path(__file__).resolve().parents[1] / "examples" / "aix-demo"
    project = tmp_path / "manuscript"
    shutil.copytree(demo, project, ignore=shutil.ignore_patterns(
        "output", "decisions", ".quarto", "*_files", "__pycache__",
    ))
    source_before = (project / "index.qmd").read_bytes()

    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "wongo.cli", "mcp", "run"],
            cwd=project, env=dict(os.environ),
        )
        with (tmp_path / "stderr.log").open("w", encoding="utf-8") as stderr:
            async with stdio_client(params, errlog=stderr) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=120) as session:
                    await session.initialize()
                    for target in ("collab", "submission"):
                        result = await session.call_tool("wongo_render", {"target": target})
                        rendered = result.structured_content
                        assert rendered["ok"] is True, rendered
                        assert len(rendered["outputs"]) == 2
                        for output in rendered["outputs"]:
                            with ZipFile(output) as archive:
                                xml = etree.fromstring(archive.read("word/document.xml"))
                            numbering = xml.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lnNumType")
                            if target == "submission":
                                assert not numbering, "WR submission must omit line numbering"
                    result = await session.call_tool("wongo_roundtrip", {
                        "docx_path": str(project / "from-coauthors" / "coauthor-edits.docx"),
                    })
                    data = result.structured_content
                    assert data["ok"] is True, data
                    assert data["changes"] == 2
                    assert data["unmatched"] == data["unparsed"] == 0
                    resource = await session.read_resource(data["worksheet_uri"])
                    assert resource.contents[0].text == Path(data["worksheet"]).read_text(encoding="utf-8")
                    result = await session.call_tool("wongo_worksheet_status", {"file": data["worksheet"]})
                    rows = result.structured_content["rows"]
                    calculated = next(row for row in rows if row["old"] == "12.4")
                    assert "inline-code" in calculated["tags"]
                    assert "`r " in calculated["source"]["text"]

    asyncio.run(run())
    assert (project / "index.qmd").read_bytes() == source_before
