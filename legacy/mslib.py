"""Shared helpers for quarto-manuscript-sci scripts (render/validate/roundtrip).

Not a CLI. Sibling scripts import it directly (same directory on sys.path).
Journal profiles resolve to <skills-dir>/quarto-manuscript-<slug>/profile.yml,
where <skills-dir> defaults to this skill's parent directory and can be
overridden with the QM_SKILLS_DIR environment variable (used by tests).
"""
from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

import yaml

CROSSREF_PREFIXES = ("fig-", "tbl-", "eq-", "sec-", "lst-", "thm-")

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?\n)(?:---|\.\.\.)\n", re.DOTALL)
FENCE_RE = re.compile(r"^(```|~~~)[^\n]*\n.*?^\1\s*$\n?", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)(\{[^}]*\})?")
HEADING_RE = re.compile(r"^#+\s.*$", re.MULTILINE)
REF_USE_RE = re.compile(r"@((?:fig|tbl|eq|sec|lst|thm)-[\w.-]+)")
LABEL_DEF_RE = re.compile(
    r"#\|\s*label:\s*\"?((?:fig|tbl|lst)-[\w.-]+)\"?"
    r"|\{#((?:fig|tbl|eq|sec|lst|thm)-[\w.-]+)"
    # knitr chunk-name form, e.g. ```{r fig-plot} — also a valid Quarto label
    r"|^```\{\w+[,]?\s+((?:fig|tbl|lst)-[\w.-]+)\s*[},]",
    re.MULTILINE,
)
CITE_RE = re.compile(r"(?<![\w@.\\])-?@([A-Za-z][\w:.#$%&+?<>~/-]*)")
BIB_KEY_RE = re.compile(r"^@\w+\{([^,\s]+)\s*,", re.MULTILINE)


def skills_dir() -> Path:
    override = os.environ.get("QM_SKILLS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent.parent


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


def load_profile(slug: str) -> dict:
    pdir = skills_dir() / f"quarto-manuscript-{slug}"
    pfile = pdir / "profile.yml"
    if not pfile.exists():
        raise SystemExit(
            f"Journal profile for slug '{slug}' not found: {pfile}. "
            f"Install or create the quarto-manuscript-{slug} skill."
        )
    profile = yaml.safe_load(pfile.read_text(encoding="utf-8"))
    profile["_dir"] = str(pdir)
    return profile


def manuscript_type(profile: dict, ms_type: str) -> dict:
    types = profile.get("manuscript_types") or []
    for t in types:
        if t.get("type") == ms_type:
            return t
    known = ", ".join(t.get("type", "?") for t in types)
    raise SystemExit(f"ms_type '{ms_type}' not defined by profile '{profile.get('slug')}'. Known: {known}")


def split_front_matter(text: str) -> tuple[dict, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def prose(body: str) -> str:
    """Fenced chunks and HTML comments removed; each image markdown collapses
    to its alt/caption text (captions are prose the journal's word count
    includes — dropping them entirely undercounts); each inline code
    expression collapses to one placeholder word (a code-generated number
    reads as one word in any journal's count)."""
    body = FENCE_RE.sub("", body)
    body = COMMENT_RE.sub("", body)
    body = IMAGE_RE.sub(lambda m: m.group(1), body)
    return INLINE_CODE_RE.sub("X", body)


def word_count(text: str) -> int:
    """Approximation of a journal's official word count: body prose (see
    `prose`) plus the front-matter `abstract` when present, since most SCI
    journals' verified counting rules include the abstract (e.g. ES&T: "count
    runs from the Abstract through the end of the main text"). Title,
    keywords, and author metadata are never counted. This is NOT a verbatim
    implementation of any single journal's rule — see profile.yml's
    `counting_rule` for the authoritative text, and treat the journal's own
    submission-system checker as the final word."""
    meta, body = split_front_matter(text)
    total = len(HEADING_RE.sub("", prose(body)).split())
    abstract = meta.get("abstract")
    if isinstance(abstract, str):
        total += len(abstract.split())
    return total


def crossrefs_used(text: str) -> set[str]:
    body = prose(split_front_matter(text)[1])
    return {ref.rstrip(".,;:]") for ref in REF_USE_RE.findall(body)}


def labels_defined(text: str) -> set[str]:
    out = set()
    for groups in LABEL_DEF_RE.findall(text):
        out.add(next(g for g in groups if g))
    return out


def citekeys_used(text: str) -> set[str]:
    body = prose(split_front_matter(text)[1])
    keys = set()
    for m in CITE_RE.finditer(body):
        key = m.group(1).rstrip(".,;:]")
        if not key.startswith(CROSSREF_PREFIXES):
            keys.add(key)
    return keys


def bib_keys(bib_text: str) -> set[str]:
    return set(BIB_KEY_RE.findall(bib_text))


def image_paths(text: str) -> list[str]:
    body = FENCE_RE.sub("", split_front_matter(text)[1])
    return [m.group(2) for m in IMAGE_RE.finditer(body)]


def profile_staleness_days(profile: dict) -> int | None:
    vd = profile.get("verified_date")
    if not vd:
        return None
    if isinstance(vd, str):
        vd = date.fromisoformat(vd)
    return (date.today() - vd).days
