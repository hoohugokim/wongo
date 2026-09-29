"""The Claude front door stays consistent with the CLI it drives: the plugin
marketplace resolves, the skill's frontmatter is valid, and every `wongo ...`
command the skill and the guides tell people or Claude to run exists."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from wongo.cli import build_parser

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "integrations" / "claude-code"
SKILL = PLUGIN / "skills" / "wongo" / "SKILL.md"
GUIDES = [
    SKILL,
    *sorted((SKILL.parent / "references").glob("*.md")),
    PLUGIN / "README.md",
    ROOT / "docs" / "getting-started.md",
    ROOT / "README.md",
]
CODE_RE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)  # commands live in code, not prose
# a code line that starts with a wongo command (chat prompts such as "set up
# wongo on this computer" are code blocks too, but do not start with it)
COMMAND_RE = re.compile(r"^\s*`*wongo ((?:worksheet|profile|style) [a-z]+|[a-z]+)\b", re.MULTILINE)


def _subcommands() -> set[str]:
    parser = build_parser()
    names: set[str] = set()
    for action in parser._subparsers._group_actions:  # argparse has no public API for this
        for name, sub in action.choices.items():
            nested = [a for a in sub._actions if a.__class__.__name__ == "_SubParsersAction"]
            if nested:
                names |= {f"{name} {child}" for child in nested[0].choices}
            else:
                names.add(name)
    return names


def test_the_marketplace_points_at_the_plugin():
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert market["name"] == "wongo" and market["owner"]["name"]
    (entry,) = market["plugins"]
    source = (ROOT / entry["source"]).resolve()
    assert source == PLUGIN
    manifest = json.loads((source / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == entry["name"] == "wongo"


def test_the_skill_frontmatter_is_valid():
    text = SKILL.read_text(encoding="utf-8")
    front = yaml.safe_load(text.split("---", 2)[1])
    assert front["name"] == "wongo" == SKILL.parent.name
    assert 0 < len(front["description"]) <= 1024
    assert len(front.get("compatibility", "")) <= 500


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_every_wongo_command_in_the_guides_exists(guide):
    known = _subcommands()
    code = "\n".join(CODE_RE.findall(guide.read_text(encoding="utf-8")))
    used = {m.group(1) for m in COMMAND_RE.finditer(code)}
    assert used, f"no wongo commands found in {guide.name}"
    assert used <= known, f"{guide.name} mentions unknown commands: {sorted(used - known)}"
