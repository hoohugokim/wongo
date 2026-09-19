"""wongo.profiles — journal profile discovery and loading (HANDOFF step 3).

Migrated from legacy/mslib.py. Resolution order for a profile slug:

1. project-local ``<project>/profiles/<slug>/profile.yml`` (experiments,
   unverified drafts)
2. ``$WONGO_PROFILES`` directory (user/site installs)
3. packaged profiles (this package's data dir — ships in the wheel)
4. legacy name compat: any root also tried as ``quarto-manuscript-<slug>``
   (the thinned Claude skills still carry that directory name)

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


def candidate_dirs(project: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if project is not None:
        roots.append(Path(project) / "profiles")
    env = os.environ.get("WONGO_PROFILES") or os.environ.get("QM_SKILLS_DIR")
    if env:
        roots.append(Path(env))
    roots.append(_packaged_dir())
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


# ---------------------------------------------------------------------------
# Contract enforcement (docs/journal-profile-contract.md)

REQUIRED_KEYS = ("journal", "slug", "manuscript_types", "sources", "verified_date")
LINE_NUMBER_VALUES = (True, False, None, "forbidden")


def validate_profile(profile: dict) -> list[str]:
    """Lint a loaded profile.yml against the journal-profile contract.

    Returns human-readable problems (empty when clean). Only structural
    guarantees the engine relies on are checked — the numbers themselves are
    the human's audit against the cited sources.
    """
    problems: list[str] = []
    for key in REQUIRED_KEYS:
        if not profile.get(key):
            problems.append(f"missing required key: {key}")
    types = profile.get("manuscript_types")
    if types and not isinstance(types, list):
        problems.append("manuscript_types must be a list")
    for i, t in enumerate(types or []):
        if not isinstance(t, dict) or not t.get("type"):
            problems.append(f"manuscript_types[{i}] has no type")
        if isinstance(t, dict) and "word_limit" not in t:
            problems.append(f"manuscript_types[{i}] has no word_limit (use null when unlimited)")
    vd = profile.get("verified_date")
    if vd is not None and not isinstance(vd, date):
        try:
            date.fromisoformat(str(vd))
        except ValueError:
            problems.append(f"verified_date is not an ISO date: {vd!r}")
    toc = profile.get("toc_graphic")
    if toc is not None:
        if not isinstance(toc, dict):
            problems.append("toc_graphic must be a mapping or null")
        elif "required" not in toc:
            problems.append("toc_graphic.required is missing (REQUIRED whenever the block is present)")
    if profile.get("line_numbers") not in LINE_NUMBER_VALUES:
        problems.append(
            f"line_numbers must be true, false, or 'forbidden' (got {profile.get('line_numbers')!r})"
        )
    sources = profile.get("sources")
    if sources is not None and not isinstance(sources, list):
        problems.append("sources must be a list of URLs/paths")
    return problems
