"""Declared manuscript inputs.

`source_fingerprint()` hashes the manuscript, its config, its bibliography,
and `figures/`. A project can add the files that actually feed the prose:
`_journal.yml` `dependencies`, Quarto pre/post-render scripts, and
`postprocess` scripts. Discovery only reports literal read calls. It does
not claim to see every file an R or Python program opens.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from wongo.errors import ConfigError
from wongo.textio import read_text

MISSING = "missing"
EMPTY_DIRECTORY = "empty-directory"

_READ_CALL_RE = re.compile(
    r"""(?ix)
    (?:read(?:\.csv|\.table|\.delim|_csv|_json)?|fromJSON|source|readRDS|load)
    \s*\(\s*['"]([^'"]+)['"]
    """
)
_SHELL_CHARS = set("\n|&;<>`$")


@dataclass(frozen=True)
class DeclaredInput:
    """One fingerprint entry. `path` is None when a declared input is gone."""

    key: str
    path: Path | None
    external: bool


def _load_quarto(project: Path) -> dict:
    path = project / "_quarto.yml"
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(read_text(path)) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"_quarto.yml is not valid YAML: {exc}") from exc
    return data if isinstance(data, dict) else {}


def dependency_specs(cfg: dict) -> list[dict]:
    """Normalize `_journal.yml` `dependencies` to `{path, external}` mappings."""
    raw = cfg.get("dependencies") or []
    if not isinstance(raw, list):
        raise ConfigError("_journal.yml dependencies must be a list of paths")
    specs = []
    for item in raw:
        if isinstance(item, str):
            if not item.strip():
                raise ConfigError("dependencies contains an empty path")
            specs.append({"path": item, "external": False})
        elif isinstance(item, dict):
            path = item.get("path")
            if not isinstance(path, str) or not path.strip():
                raise ConfigError("each dependency mapping needs a path string")
            external = item.get("external", False)
            if not isinstance(external, bool):
                raise ConfigError(f"dependency {path!r} external must be true or false")
            specs.append({"path": path, "external": external})
        else:
            raise ConfigError("each dependency must be a path or a mapping with path")
    return specs


def postprocess_paths(project: Path, cfg: dict) -> list[Path]:
    """Project-relative scripts that run inside the render transaction."""
    raw = cfg.get("postprocess") or []
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise ConfigError(
            "_journal.yml postprocess must be a list of project-relative script paths"
        )
    paths = []
    root = project.resolve()
    for item in raw:
        if any(char in item for char in _SHELL_CHARS):
            raise ConfigError(
                f"postprocess entry {item!r} must be a path, not a shell command"
            )
        path = _inside_project(root, item, label="postprocess")
        paths.append(path)
    return paths


def _inside_project(root: Path, raw: str, *, label: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ConfigError(
            f"{label} path {raw} must stay inside the project. "
            "Use dependencies with external: true for an outside file."
        )
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ConfigError(
            f"{label} path {raw} escapes the project. "
            "Use dependencies with external: true to record an outside file by hash."
        ) from None
    return resolved


def _hook_tokens(project: Path) -> list[str]:
    """Script paths named by Quarto pre-render and post-render hooks."""
    section = (_load_quarto(project).get("project") or {})
    if not isinstance(section, dict):
        return []
    tokens = []
    for key in ("pre-render", "post-render"):
        value = section.get(key) or []
        values = value if isinstance(value, list) else [value]
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            for part in text.split():
                if "/" in part or part.endswith((".R", ".r", ".py", ".sh")):
                    tokens.append(part.strip("'\""))
                    break
    return tokens


def _resolve_spec(root: Path, spec: dict) -> tuple[str, Path, bool]:
    raw = spec["path"]
    external = spec["external"]
    candidate = Path(raw)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        if not external:
            raise ConfigError(
                f"{raw} is outside the project. Add external: true to record its hash "
                "without copying it into the project."
            ) from None
        return resolved.as_posix(), resolved, True
    return relative.as_posix(), resolved, False


def _expand(root: Path, spec: dict) -> list[DeclaredInput]:
    key, resolved, external = _resolve_spec(root, spec)
    if not resolved.exists():
        return [DeclaredInput(key, None, external)]
    if resolved.is_file():
        return [DeclaredInput(key, resolved, external)]
    if not resolved.is_dir():
        return [DeclaredInput(key, None, external)]
    files = sorted(path for path in resolved.rglob("*") if path.is_file())
    if not files:
        return [DeclaredInput(key.rstrip("/") + "/", resolved, external)]
    items = []
    for path in files:
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError:
            if not external:
                raise ConfigError(
                    f"{path} is outside the project. Declare it with external: true."
                ) from None
            rel = path.resolve().as_posix()
        items.append(DeclaredInput(rel, path, external))
    return items


def declared_inputs(project: Path, cfg: dict) -> list[DeclaredInput]:
    """Files and missing paths whose hash belongs in the source fingerprint."""
    root = Path(project).resolve()
    items: list[DeclaredInput] = []
    for spec in dependency_specs(cfg):
        items.extend(_expand(root, spec))
    for token in _hook_tokens(root):
        items.extend(_expand(root, {"path": token, "external": False}))
    for path in postprocess_paths(root, cfg):
        try:
            key = path.relative_to(root).as_posix()
        except ValueError:
            key = path.as_posix()
        items.append(DeclaredInput(key, path if path.is_file() else None, False))
    unique: dict[str, DeclaredInput] = {}
    for item in items:
        unique.setdefault(item.key, item)
    return list(unique.values())


def missing_declared(items: list[DeclaredInput]) -> list[str]:
    return sorted(item.key for item in items if item.path is None or not item.path.exists())


def discover_candidates(project: Path, texts: dict[str, str], known: set[str]) -> list[str]:
    """Literal read/source paths that are not already fingerprinted.

    This is a scan of quoted calls, not a trace of what R or Python opened.
    """
    found: set[str] = set()
    blobs = list(texts.values())
    root = Path(project)
    for item in known:
        path = root / item
        if path.is_file() and path.suffix.lower() in {".r", ".py", ".qmd", ".rmd"}:
            try:
                blobs.append(read_text(path))
            except OSError:
                continue
    for blob in blobs:
        for match in _READ_CALL_RE.finditer(blob):
            raw = match.group(1).strip()
            if not raw or raw.startswith(("http://", "https://", "data:")):
                continue
            key = Path(raw).as_posix()
            if key not in known and key.rstrip("/") + "/" not in known:
                found.add(key)
    return sorted(found)
