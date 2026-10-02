"""Dynamic MCP Resources for Wongo.

Exposes project status, journal profile guidelines, and merge worksheets as readable resources.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.resources import ResourceSecurity

from wongo.clitools import to_jsonable
from wongo.errors import InputError
from wongo.profiles import load_profile
from wongo.status import project_status
from wongo.textio import read_text


def worksheet_uri(path: Path | str) -> str:
    """Encode a worksheet's absolute path as one RFC 6570 template parameter."""
    return "wongo://worksheet/" + quote(str(Path(path).resolve()), safe="")


def register_resources(server: MCPServer) -> None:
    """Register Wongo dynamic resources on the MCP server."""

    @server.resource("wongo://project/status", mime_type="application/json")
    def resource_project_status() -> str:
        """Current project readiness, configuration, and output freshness."""
        st = project_status(Path("."))
        return json.dumps(to_jsonable(st), ensure_ascii=False, indent=2)

    @server.resource("wongo://profile/{slug}", mime_type="application/json")
    def resource_profile(slug: str) -> str:
        """Verified journal submission requirements, word limits, and rules for {slug}."""
        prof = load_profile(slug)
        sanitized = {k: v for k, v in prof.items() if not k.startswith("_")}
        return json.dumps(to_jsonable(sanitized), ensure_ascii=False, indent=2)

    @server.resource(
        "wongo://worksheet/{path}", mime_type="text/markdown",
        # Local stdio clients already select absolute worksheet files in the tools.
        # Accept the same paths here; traversal and NUL checks remain enabled.
        security=ResourceSecurity(reject_absolute_paths=False),
    )
    def resource_worksheet(path: str) -> str:
        """Raw content of merge worksheet at {path}."""
        target = Path(path)
        if not target.exists() and (Path("decisions") / target).exists():
            target = Path("decisions") / target
        if not target.is_file() or target.suffix.lower() != ".md":
            raise InputError(f"worksheet Markdown file not found: {path}")
        return read_text(target)
