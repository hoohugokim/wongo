"""wongo.profiles — journal profile discovery and loading (HANDOFF step 3).

Migrated from legacy/mslib.py. Resolution order for a profile slug:

1. project-local ``<project>/profiles/<slug>/profile.yml`` (experiments,
   unverified drafts)
2. ``$WONGO_PROFILES`` directory (user/site installs)
3. packaged profiles (this package's data dir — ships in the wheel)
4. repo-root ``profiles/`` fallback (development checkouts)
5. legacy name compat: any root also tried as ``quarto-manuscript-<slug>``
   until the Claude skills are thinned (HANDOFF step 6)

A profile dir must contain profile.yml; sibling assets (reference.docx, CSL)
resolve relative to the profile dir via the ``_dir`` key.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import yaml

LEGACY_NAME_FMT = "quarto-manuscript-{slug}"


def _packaged_dir() -> Path:
    return Path(__file__).resolve().parent


def _repo_root() -> Path | None:
    for parent in _packaged_dir().parents:
        if (parent / "pyproject.toml").exists() and (parent / "profiles").is_dir():
            return parent
    return None


def candidate_dirs(project: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if project is not None:
        roots.append(Path(project) / "profiles")
    env = os.environ.get("WONGO_PROFILES") or os.environ.get("QM_SKILLS_DIR")
    if env:
        roots.append(Path(env))
    roots.append(_packaged_dir())
    repo = _repo_root()
    if repo is not None:
        roots.append(repo / "profiles")
    # dedupe, preserve order
    seen: set[Path] = set()
    out = []
    for r in roots:
        r = Path(r).resolve()
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def find_profile_dir(slug: str, project: Path | None = None) -> Path:
    """Locate a profile dir; SystemExit with an actionable message if absent."""
    names = [slug, LEGACY_NAME_FMT.format(slug=slug)]
    for root in candidate_dirs(project):
        for n in names:
            pdir = root / n
            if (pdir / "profile.yml").exists():
                return pdir
    searched = "\n  ".join(str(r / names[-1]) for r in candidate_dirs(project))
    raise SystemExit(
        f"Journal profile for slug '{slug}' not found. Searched:\n  {searched}\n"
        f"Install or create the profile (contract: docs/journal-profile-contract.md)."
    )


def load_profile(slug: str, project: Path | None = None) -> dict:
    pdir = find_profile_dir(slug, project)
    profile = yaml.safe_load((pdir / "profile.yml").read_text(encoding="utf-8"))
    profile["_dir"] = str(pdir)
    return profile


# ---------------------------------------------------------------------------
# Project journal config + profile metadata helpers (verbatim from mslib)


def load_journal_config(project_dir: Path) -> dict:
    path = Path(project_dir) / "_journal.yml"
    if not path.exists():
        raise SystemExit(
            "_journal.yml not found in project. Create it with 'journal: <slug>' "
            "and 'ms_type: <type>' (see quarto-manuscript-sci S1)."
        )
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [k for k in ("journal", "ms_type") if not cfg.get(k)]
    if missing:
        raise SystemExit(f"_journal.yml missing required keys: {', '.join(missing)}")
    return cfg


def manuscript_type(profile: dict, ms_type: str) -> dict:
    types = profile.get("manuscript_types") or []
    for t in types:
        if t.get("type") == ms_type:
            return t
    known = ", ".join(t.get("type", "?") for t in types)
    raise SystemExit(f"ms_type '{ms_type}' not defined by profile '{profile.get('slug')}'. Known: {known}")


def profile_staleness_days(profile: dict) -> int | None:
    vd = profile.get("verified_date")
    if not vd:
        return None
    if isinstance(vd, str):
        vd = date.fromisoformat(vd)
    return (date.today() - vd).days
