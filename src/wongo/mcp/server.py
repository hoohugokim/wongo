"""Wongo MCP Server creation and lifecycle."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from wongo import __version__
from wongo.mcp.prompts import register_prompts
from wongo.mcp.resources import register_resources
from wongo.mcp.tools import register_tools


def create_mcp_server() -> MCPServer:
    """Create and configure the Wongo MCP Server instance."""
    server = MCPServer(
        name="wongo",
        version=__version__,
        instructions=(
            "Wongo MCP server: verified Quarto-to-journal DOCX pipeline. "
            "Exposes tools to inspect project status, run doctor diagnostics, "
            "validate manuscripts against journal profiles with actionable patch hints, "
            "render collab and submission DOCX, extract coauthor Word track changes into merge worksheets, "
            "propose and record worksheet decisions in batch, and stamp revision diffs."
        ),
    )
    register_tools(server)
    register_resources(server)
    register_prompts(server)
    return server


def run_mcp_server(transport: str = "stdio") -> None:
    """Run the Wongo MCP server synchronously on the requested transport."""
    server = create_mcp_server()
    server.run(transport=transport)
