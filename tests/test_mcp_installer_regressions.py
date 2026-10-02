"""Client configuration must remain usable and failures must reach the caller."""
from __future__ import annotations

import json
import sys

import pytest

from wongo.cli import main
from wongo.errors import InputError
from wongo.mcp.installer import (
    get_wongo_server_config,
    install_client_configs,
    update_mcp_config_file,
)
from wongo.scaffold import scaffold


def test_installer_uses_each_clients_schema_and_preserves_other_settings(tmp_path, monkeypatch):
    claude = tmp_path / "claude.json"
    monkeypatch.setattr("wongo.mcp.installer.get_claude_desktop_config_path", lambda: claude)
    paths = {"claude_desktop": claude, "cursor_project": tmp_path / ".cursor" / "mcp.json",
             "vscode_project": tmp_path / ".vscode" / "mcp.json"}
    for client, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        key = "servers" if client == "vscode_project" else "mcpServers"
        path.write_text(json.dumps({key: {"existing": {"command": "other"}}, "inputs": []}),
                        encoding="utf-8-sig")

    results = install_client_configs(project_dir=tmp_path, custom_command=sys.executable)

    for client, path in paths.items():
        assert results[client]["ok"] is True
        assert results[client]["path"] == str(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        key = "servers" if client == "vscode_project" else "mcpServers"
        assert data[key]["existing"] == {"command": "other"}
        assert data[key]["wongo"]["args"] == ["mcp", "run"]
        assert data["inputs"] == []
        if client == "vscode_project":
            assert "mcpServers" not in data
            assert data[key]["wongo"]["type"] == "stdio"


@pytest.mark.parametrize("content", [
    b"NOT JSON",
    b'{"servers": { // VS Code permits comments\n "existing": {"command": "other"},\n},}',
    b"[]",
    b'{"servers": null}',
])
def test_unmergeable_config_stays_byte_identical(tmp_path, content):
    path = tmp_path / ".vscode" / "mcp.json"
    path.parent.mkdir()
    path.write_bytes(content)

    result = install_client_configs(
        clients=["vscode"], project_dir=tmp_path, custom_command=sys.executable,
    )["vscode_project"]

    assert result["ok"] is False
    assert "unchanged" in result["error"]["message"]
    assert path.read_bytes() == content
    assert not path.with_suffix(".json.bak").exists()


def test_failed_atomic_replace_keeps_existing_config(tmp_path, monkeypatch):
    path = tmp_path / "mcp.json"
    original = b'{"mcpServers":{"existing":{"command":"other"}}}\r\n'
    path.write_bytes(original)

    def fail_replace(*_args):
        raise PermissionError("file is locked")

    monkeypatch.setattr("wongo.textio.os.replace", fail_replace)
    with pytest.raises(InputError, match="unchanged"):
        update_mcp_config_file(path, {"command": "wongo", "args": ["mcp", "run"]})
    assert path.read_bytes() == original


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_reports_partial_install_failure(tmp_path, capsys, json_output):
    (tmp_path / ".cursor").write_text("not a directory", encoding="utf-8")
    args = ["mcp", "install", "--client", "cursor", "--client", "vscode",
            "--project", str(tmp_path), "--command", sys.executable]
    if json_output:
        args.append("--json")
    result = main(args)
    out = capsys.readouterr().out

    assert result == 1
    assert (tmp_path / ".vscode" / "mcp.json").is_file()
    if json_output:
        data = json.loads(out)
        assert data["ok"] is False
        assert data["results"]["cursor_project"]["ok"] is False
        assert data["results"]["vscode_project"]["ok"] is True
        assert data["results"]["cursor_project"]["error"]["message"]
    else:
        assert "error:" in out
        assert "configured:" in out


def test_custom_command_is_an_executable_not_a_shell_command(tmp_path):
    with pytest.raises(InputError, match="executable"):
        get_wongo_server_config("uvx wongo")
    path = tmp_path / "Program Files" / "wongo.exe"
    path.parent.mkdir()
    path.write_bytes(b"test executable")
    path.chmod(0o755)
    config = get_wongo_server_config(str(path))
    assert config == {"command": str(path), "args": ["mcp", "run"]}


def test_relative_executable_does_not_depend_on_client_working_directory(tmp_path, monkeypatch):
    path = tmp_path / "bin" / "wongo.exe"
    path.parent.mkdir()
    path.write_bytes(b"test executable")
    path.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    config = get_wongo_server_config(str(path.relative_to(tmp_path)))
    assert config["command"] == str(path)


def test_bad_custom_command_fails_before_creating_client_configuration(tmp_path, capsys):
    result = main(["mcp", "install", "--client", "vscode", "--project", str(tmp_path),
                   "--command", "uvx wongo", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert result == 1
    assert data["ok"] is False
    assert "single executable path" in data["error"]["message"]
    assert not (tmp_path / ".vscode").exists()


def test_scaffold_vscode_config_registers_stdio_server(tmp_path):
    dest = tmp_path / "paper"
    scaffold(dest, journal="wr")
    data = json.loads((dest / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert "mcpServers" not in data
    assert data["servers"]["wongo"]["type"] == "stdio"
    assert data["servers"]["wongo"]["args"] == ["mcp", "run"]
