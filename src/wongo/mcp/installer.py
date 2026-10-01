"""Client configuration installer for Wongo MCP server.

Auto-detects and updates configuration files for Claude Desktop, Cursor, and VS Code.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def get_claude_desktop_config_path() -> Path:
    """Return the platform-specific path to Claude Desktop configuration file."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "Claude" / "claude_desktop_config.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    # Linux
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home) if config_home else Path.home() / ".config"
    return base / "Claude" / "claude_desktop_config.json"


def get_wongo_server_config(custom_command: str | None = None) -> dict[str, Any]:
    """Generate the standard MCP server JSON definition for Wongo."""
    if custom_command:
        return {
            "command": custom_command,
            "args": ["mcp", "run"],
        }
    # Resolve 'wongo' executable if available on PATH, else use sys.executable -m wongo
    wongo_bin = shutil.which("wongo")
    if wongo_bin:
        return {
            "command": wongo_bin,
            "args": ["mcp", "run"],
        }
    return {
        "command": sys.executable,
        "args": ["-m", "wongo.cli", "mcp", "run"],
    }


def update_mcp_config_file(config_path: Path, server_config: dict[str, Any]) -> bool:
    """Safely merge Wongo into an existing or new mcpServers JSON configuration."""
    config_path = Path(config_path)
    data: dict[str, Any] = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else {}
        except Exception:
            # Backup corrupt or unparseable config
            backup = config_path.with_name(config_path.name + ".bak")
            shutil.copy2(config_path, backup)
            data = {}

    servers = data.setdefault("mcpServers", {})
    servers["wongo"] = server_config

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def install_client_configs(
    clients: list[str] | None = None,
    project_dir: Path | None = None,
    custom_command: str | None = None,
) -> dict[str, str]:
    """Install Wongo MCP server configuration into specified or all detected clients.

    Supported clients: 'claude', 'cursor', 'vscode'.
    """
    server_cfg = get_wongo_server_config(custom_command)
    targets = [c.lower() for c in (clients or ["claude", "cursor", "vscode"])]
    results: dict[str, str] = {}

    project = project_dir or Path.cwd()

    if "claude" in targets:
        claude_path = get_claude_desktop_config_path()
        try:
            update_mcp_config_file(claude_path, server_cfg)
            results["claude_desktop"] = f"configured: {claude_path}"
        except Exception as exc:
            results["claude_desktop"] = f"error: {exc}"

    if "cursor" in targets:
        cursor_path = project / ".cursor" / "mcp.json"
        try:
            update_mcp_config_file(cursor_path, server_cfg)
            results["cursor_project"] = f"configured: {cursor_path}"
        except Exception as exc:
            results["cursor_project"] = f"error: {exc}"

    if "vscode" in targets:
        vscode_path = project / ".vscode" / "mcp.json"
        try:
            update_mcp_config_file(vscode_path, server_cfg)
            results["vscode_project"] = f"configured: {vscode_path}"
        except Exception as exc:
            results["vscode_project"] = f"error: {exc}"

    return results
