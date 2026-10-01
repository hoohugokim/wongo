"""Wongo Model Context Protocol (MCP) server package."""
from __future__ import annotations

from wongo.mcp.installer import install_client_configs
from wongo.mcp.server import create_mcp_server, run_mcp_server

__all__ = ["create_mcp_server", "run_mcp_server", "install_client_configs"]
