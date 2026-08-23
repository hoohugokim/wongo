"""wongo.engine.checks — manuscript validation + text analysis.

HARD/WARN report shape preserved verbatim from legacy/validate.py; the text
analysis helpers (word count, citekeys, crossrefs, image paths) moved
verbatim from legacy/mslib.py. Regexes here encode Quarto/pandoc markdown
conventions and journal counting-rule approximations — change with care and
record why in docs/docx-quirks.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from wongo.profiles import load_journal_config, load_profile, manuscript_type, profile_staleness_days  # noqa: F401

STALE_DAYS = 183

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


# ---------------------------------------------------------------------------
# Text analysis (verbatim from mslib)


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


# ---------------------------------------------------------------------------
# Checks (verbatim report shape from validate.py)


@dataclass
class Check:
    name: str
    level: str  # "HARD" | "WARN"
    ok: bool
    detail: str


def run_checks(project: Path) -> list[Check]:
    project = Path(project)
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    mtype = manuscript_type(profile, cfg["ms_type"])
    checks: list[Check] = []

    texts = {}
    for name in ("index.qmd", "si.qmd"):
        p = project / name
        if p.exists():
            texts[name] = p.read_text(encoding="utf-8")
    if "index.qmd" not in texts:
        raise SystemExit(f"index.qmd not found in {project}")

    wc = word_count(texts["index.qmd"])
    limit = mtype.get("word_limit")
    checks.append(Check(
        "word-limit", "HARD", limit is None or wc <= limit,
        f"{wc} words vs limit {limit} for {cfg['ms_type']} "
        f"(rule: {mtype.get('counting_rule', 'unspecified')})",
    ))

    bib_path = project / "refs.bib"
    bib = bib_keys(bib_path.read_text(encoding="utf-8")) if bib_path.exists() else set()
    used = set().union(*(citekeys_used(t) for t in texts.values()))
    missing = sorted(used - bib)
    checks.append(Check(
        "citekeys", "HARD", not missing,
        "all citekeys resolve" if not missing else f"missing from refs.bib: {', '.join(missing)}",
    ))

    defined = set().union(*(labels_defined(t) for t in texts.values()))
    orphans = sorted(set().union(*(crossrefs_used(t) for t in texts.values())) - defined)
    checks.append(Check(
        "crossrefs", "HARD", not orphans,
        "all cross-references resolve" if not orphans else f"orphaned: {', '.join(orphans)}",
    ))

    missing_figs = []
    for name, text in texts.items():
        for rel in image_paths(text):
            if not (project / rel).exists():
                missing_figs.append(f"{name} -> {rel}")
    checks.append(Check(
        "figures", "HARD", not missing_figs,
        "all referenced figures exist" if not missing_figs else "; ".join(missing_figs),
    ))

    days = profile_staleness_days(profile)
    checks.append(Check(
        "profile-staleness", "WARN", days is not None and days <= STALE_DAYS,
        f"profile verified {days} days ago" if days is not None
        else "profile has no verified_date",
    ))

    si_expected = (profile.get("si") or {}).get("separate_file")
    checks.append(Check(
        "si-file", "WARN", not si_expected or "si.qmd" in texts,
        "si.qmd present" if "si.qmd" in texts else "profile expects separate SI but si.qmd is absent",
    ))
    return checks


def print_report(checks: list[Check]) -> None:
    for c in checks:
        mark = "PASS" if c.ok else ("FAIL" if c.level == "HARD" else "WARN")
        print(f"[{mark}] {c.level:4} {c.name}: {c.detail}")
