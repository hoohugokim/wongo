"""Tests for Wongo Model Context Protocol (MCP) server, tools, resources, prompts, and installer."""
import asyncio
import json
from pathlib import Path

from wongo.cli import main
from wongo.errors import InputError
from wongo.mcp.installer import (
    get_claude_desktop_config_path,
    get_wongo_server_config,
    install_client_configs,
    update_mcp_config_file,
)
from wongo.mcp.server import create_mcp_server
from wongo.mcp.tools import _safe_call


def test_mcp_server_registration():
    """Verify that all 12 tools, 3 prompts, and resources are registered on MCPServer."""
    server = create_mcp_server()
    assert server.name == "wongo"

    tool_names = set(server._tool_manager._tools.keys())
    expected_tools = {
        "wongo_status",
        "wongo_doctor",
        "wongo_scaffold",
        "wongo_profile_get",
        "wongo_check",
        "wongo_render",
        "wongo_roundtrip",
        "wongo_worksheet_status",
        "wongo_worksheet_set",
        "wongo_worksheet_batch_propose",
        "wongo_worksheet_lint",
        "wongo_diff",
    }
    assert expected_tools.issubset(tool_names)
    assert len(expected_tools) == 12

    prompt_names = set(server._prompt_manager._prompts.keys())
    expected_prompts = {
        "wongo-pre-submission-audit",
        "wongo-coauthor-review",
        "wongo-revision-diff",
    }
    assert expected_prompts == prompt_names

    assert "wongo://project/status" in server._resource_manager._resources
    templates = set(server._resource_manager._templates.keys())
    assert "wongo://profile/{slug}" in templates
    assert "wongo://worksheet/{path}" in templates


def test_safe_call_wrapper():
    """_safe_call wraps return values, catches WongoError and unexpected exceptions."""
    # Success case with dict
    res = _safe_call(lambda: {"sample": "val"})
    assert res["ok"] is True
    assert res["sample"] == "val"

    # Success case with primitive
    res2 = _safe_call(lambda: 42)
    assert res2["ok"] is True
    assert res2["data"] == 42

    # WongoError case
    def _raise_wongo():
        raise InputError("bad user input")

    res3 = _safe_call(_raise_wongo)
    assert res3["ok"] is False
    assert res3["error"]["kind"] == "InputError"
    assert "bad user input" in res3["error"]["message"]

    # Internal Exception case
    def _raise_internal():
        raise ValueError("unexpected")

    res4 = _safe_call(_raise_internal)
    assert res4["ok"] is False
    assert res4["error"]["kind"] == "internal"
    assert "unexpected" in res4["error"]["message"]


def test_mcp_tool_profile_get():
    async def _test():
        server = create_mcp_server()
        call_res = await server.call_tool("wongo_profile_get", {"slug": "est"})
        assert not call_res.is_error
        data = call_res.structured_content
        assert data["ok"] is True
        assert data["slug"] == "est"
        assert "Environmental Science" in data["journal"]
        assert any(m["type"] == "research-article" for m in data["manuscript_types"])

    asyncio.run(_test())


def test_mcp_tool_doctor():
    async def _test():
        server = create_mcp_server()
        call_res = await server.call_tool("wongo_doctor", {"project": "."})
        assert not call_res.is_error
        data = call_res.structured_content
        assert "checks" in data
        assert isinstance(data["checks"], list)

    asyncio.run(_test())


def test_mcp_tool_scaffold_and_status(tmp_path):
    async def _test():
        server = create_mcp_server()
        target_dir = tmp_path / "new_ms"

        # Scaffold
        call_scaffold = await server.call_tool(
            "wongo_scaffold",
            {"dest": str(target_dir), "journal": "est", "example": True},
        )
        assert not call_scaffold.is_error
        s_data = call_scaffold.structured_content
        assert s_data["ok"] is True
        assert (target_dir / "_journal.yml").exists()

        # Status
        call_status = await server.call_tool("wongo_status", {"project": str(target_dir)})
        assert not call_status.is_error
        st_data = call_status.structured_content
        assert st_data["ok"] is True
        assert st_data["journal"] == "est"
        assert st_data["is_project"] is True

    asyncio.run(_test())


def test_mcp_resources_and_prompts():
    async def _test():
        server = create_mcp_server()

        # Read profile resource
        res = await server.read_resource("wongo://profile/est")
        assert len(res) == 1
        content = json.loads(res[0].content)
        assert content["slug"] == "est"

        # Read project status resource
        st_res = await server.read_resource("wongo://project/status")
        assert len(st_res) == 1
        st_content = json.loads(st_res[0].content)
        assert "is_project" in st_content

        # Get prompt
        pr = await server.get_prompt("wongo-pre-submission-audit", {"project": "."})
        assert len(pr.messages) == 1
        assert "pre-submission audit" in pr.messages[0].content.text

    asyncio.run(_test())


def test_mcp_worksheet_tools(tmp_path):
    async def _test():
        ws_path = tmp_path / "decisions" / "review.md"
        ws_path.parent.mkdir(parents=True)
        ws_content = (
            "# Merge worksheet — coauthor.docx — 2026-09-25\n\n"
            "Review each item; set disposition to one of: apply / reject: <reason> /\n"
            "fix-code (edit inside auto-generated output) / needs-PI.\n\n"
            "## 1. addition — Alice\n"
            "- location: index.qmd:10\n"
            "- old: —\n"
            "- new: additional explanation\n"
            "- context: …context…\n"
            "- disposition: PENDING\n\n"
            "## 2. deletion — Bob\n"
            "- location: index.qmd:20\n"
            "- old: redundant clause\n"
            "- new: —\n"
            "- context: …context…\n"
            "- disposition: PENDING\n"
        )
        ws_path.write_text(ws_content, encoding="utf-8")

        server = create_mcp_server()

        # Status
        status_res = await server.call_tool("wongo_worksheet_status", {"file": str(ws_path)})
        assert not status_res.is_error
        sdata = status_res.structured_content
        assert sdata["ok"] is True
        assert sdata["counts"]["total"] == 2
        assert sdata["counts"]["pending"] == 2

        # Set row 1
        set_res = await server.call_tool(
            "wongo_worksheet_set",
            {"file": str(ws_path), "row": 1, "disposition": "apply"},
        )
        assert not set_res.is_error
        assert set_res.structured_content["ok"] is True

        # Batch propose on row 2
        batch_res = await server.call_tool(
            "wongo_worksheet_batch_propose",
            {
                "file": str(ws_path),
                "proposals": [{"row": 2, "disposition": "reject", "rationale": "breaks flow"}],
            },
        )
        assert not batch_res.is_error
        assert batch_res.structured_content["ok"] is True
        assert batch_res.structured_content["updated_count"] == 1

        # Lint
        lint_res = await server.call_tool("wongo_worksheet_lint", {"file": str(ws_path)})
        assert not lint_res.is_error
        ldata = lint_res.structured_content
        assert "errors" in ldata

    asyncio.run(_test())


def test_installer_config_merging(tmp_path):
    assert isinstance(get_claude_desktop_config_path(), Path)
    cfg_path = tmp_path / "test-config.json"
    server_cfg = get_wongo_server_config(custom_command="uvx wongo")
    assert server_cfg["command"] == "uvx wongo"

    # First write
    assert update_mcp_config_file(cfg_path, server_cfg) is True
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["wongo"]["command"] == "uvx wongo"

    # Merge preserving other servers
    data["mcpServers"]["other_server"] = {"command": "other"}
    cfg_path.write_text(json.dumps(data), encoding="utf-8")

    new_cfg = {"command": "/custom/wongo", "args": ["mcp", "run"]}
    update_mcp_config_file(cfg_path, new_cfg)
    merged = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert merged["mcpServers"]["wongo"]["command"] == "/custom/wongo"
    assert merged["mcpServers"]["other_server"]["command"] == "other"


def test_installer_corrupt_file_recovery(tmp_path):
    cfg_path = tmp_path / "corrupt.json"
    cfg_path.write_text("NOT JSON CONTENT", encoding="utf-8")
    server_cfg = {"command": "wongo", "args": ["mcp", "run"]}

    assert update_mcp_config_file(cfg_path, server_cfg) is True
    assert (tmp_path / "corrupt.json.bak").exists()
    recovered = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert recovered["mcpServers"]["wongo"]["command"] == "wongo"


def test_install_client_configs(tmp_path):
    results = install_client_configs(
        clients=["cursor", "vscode"],
        project_dir=tmp_path,
        custom_command="wongo",
    )
    assert "cursor_project" in results
    assert "configured" in results["cursor_project"]
    assert (tmp_path / ".cursor" / "mcp.json").exists()
    assert (tmp_path / ".vscode" / "mcp.json").exists()


def test_cli_mcp_install(tmp_path, capsys):
    ret = main([
        "mcp",
        "install",
        "--project",
        str(tmp_path),
        "--client",
        "cursor",
        "--command",
        "uvx wongo",
        "--json",
    ])
    assert ret == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["ok"] is True
    assert "cursor_project" in data["results"]
