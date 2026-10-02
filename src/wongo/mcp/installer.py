"""Client configuration installer for Wongo MCP server.

Updates configuration files for Claude Desktop, Cursor, and VS Code.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from wongo.errors import InputError, WongoError
from wongo.textio import detect_newline, read_text, write_text_atomic


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
        executable = shutil.which(custom_command)
        if executable is None:
            raise InputError(
                f"MCP command {custom_command!r} is not an executable on PATH. "
                "Give --command a single executable path, without shell arguments; "
                "Wongo adds the 'mcp run' arguments separately."
            )
        return {
            "command": str(Path(executable).absolute()),
            "args": ["mcp", "run"],
        }
    # Resolve 'wongo' executable if available on PATH, else use sys.executable -m wongo
    wongo_bin = shutil.which("wongo")
    if wongo_bin:
        return {
            "command": str(Path(wongo_bin).absolute()),
            "args": ["mcp", "run"],
        }
    return {
        "command": sys.executable,
        "args": ["-m", "wongo.cli", "mcp", "run"],
    }


def update_mcp_config_file(
    config_path: Path,
    server_config: dict[str, Any],
    *,
    servers_key: str = "mcpServers",
) -> bool:
    """Merge Wongo atomically, refusing inputs that cannot be preserved safely.

    VS Code uses ``servers`` and accepts JSONC. This installer supports strict
    JSON only; commented files must be edited manually so their comments survive.
    """
    config_path = Path(config_path)
    data: dict[str, Any] = {}
    newline = "\n"
    try:
        if config_path.exists():
            newline = detect_newline(config_path.read_bytes())
            raw = read_text(config_path)
            data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise InputError(
            f"{config_path} is unchanged: automatic installation requires strict JSON "
            f"(parse error at line {exc.lineno}, column {exc.colno}). "
            "If this is a VS Code JSONC file with comments or trailing commas, "
            f"add the wongo entry under '{servers_key}' manually to preserve them; "
            "otherwise fix the JSON and retry."
        ) from exc
    except (OSError, WongoError) as exc:
        raise InputError(
            f"Cannot read {config_path}; the configuration is unchanged. "
            f"Check the file's encoding and permissions, then retry: {exc}"
        ) from exc

    if not isinstance(data, dict) or (
        servers_key in data and not isinstance(data[servers_key], dict)
    ):
        raise InputError(
            f"{config_path} is unchanged: the configuration and its '{servers_key}' "
            "entry must be JSON objects. Correct their structure and retry."
        )
    servers = data.setdefault(servers_key, {})
    servers["wongo"] = server_config

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(
            config_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", newline,
        )
    except OSError as exc:
        raise InputError(
            f"Cannot install Wongo in {config_path}; any existing configuration is unchanged. "
            f"Check directory permissions or close the program locking the file and retry: {exc}"
        ) from exc
    return True


def install_client_configs(
    clients: list[str] | None = None,
    project_dir: Path | None = None,
    custom_command: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Install Wongo configuration, returning an explicit outcome for each client.

    Supported clients: 'claude', 'cursor', 'vscode'; omission selects all three.
    """
    server_cfg = get_wongo_server_config(custom_command)
    targets = [c.lower() for c in (clients or ["claude", "cursor", "vscode"])]
    unknown = set(targets) - {"claude", "cursor", "vscode"}
    if unknown:
        raise InputError(
            f"Unknown MCP client(s): {', '.join(sorted(unknown))}. Use claude, cursor or vscode."
        )
    results: dict[str, dict[str, Any]] = {}

    project = project_dir or Path.cwd()
    configs = {
        "claude": ("claude_desktop", get_claude_desktop_config_path(), "mcpServers"),
        "cursor": ("cursor_project", project / ".cursor" / "mcp.json", "mcpServers"),
        "vscode": ("vscode_project", project / ".vscode" / "mcp.json", "servers"),
    }
    for client in dict.fromkeys(targets):
        result_key, config_path, servers_key = configs[client]
        definition = {"type": "stdio", **server_cfg} if client == "vscode" else server_cfg
        try:
            update_mcp_config_file(config_path, definition, servers_key=servers_key)
        except WongoError as exc:
            results[result_key] = {
                "ok": False,
                "path": str(config_path),
                "error": {"kind": exc.kind, "message": str(exc)},
            }
        else:
            results[result_key] = {"ok": True, "path": str(config_path)}

    return results
