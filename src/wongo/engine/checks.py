"""wongo.engine.checks — manuscript validation + text analysis.

HARD/WARN report shape preserved from legacy/validate.py; the text analysis
helpers originated in legacy/mslib.py. Regexes here encode Quarto/pandoc markdown
conventions and journal counting-rule approximations — change with care and
record why in docs/docx-quirks.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from docx import Document
from docx.oxml.ns import qn

from wongo.errors import InputError
from wongo.profiles import (
    load_journal_config,
    load_profile,
    manuscript_type,
    profile_staleness_days,
)
from wongo.textio import read_text, yaml_error_message

STALE_DAYS = 183

CROSSREF_PREFIXES = ("fig-", "tbl-", "eq-", "sec-", "lst-", "thm-")

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?\n)(?:---|\.\.\.)\n", re.DOTALL)
FENCE_RE = re.compile(
    r"^ {0,3}(?:(`{3,})(?!`)[^\n]*\n.*?^ {0,3}\1`*|"
    r"(~{3,})(?!~)[^\n]*\n.*?^ {0,3}\2~*)[ \t]*(?:\n|$)",
    re.DOTALL | re.MULTILINE,
)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)(\{[^}]*\})?")
# chunk-option captions (`#| tbl-cap: "..."` / `#| fig-cap: "..."`) live INSIDE fenced
# chunks, which `prose()` strips; journals count table/figure captions, so they are
# harvested before the fence is dropped (2026-08-25: an ES&T draft passed the gate at
# 6,739 while its rendered count, captions included, was 7,349).
CHUNK_CAPTION_RE = re.compile(r"^#\|\s*(tbl|fig)-cap:\s*[\"']?(.*?)[\"']?\s*$", re.MULTILINE)
HEADING_RE = re.compile(r"^#+\s.*$", re.MULTILINE)
# pandoc fenced-div delimiters (`::: {#refs}` / `:::`) and Quarto shortcodes
# (`{{< pagebreak >}}`) are markup, not prose; they must not count as words.
DIV_FENCE_RE = re.compile(r"^:{3,}.*$", re.MULTILINE)
SHORTCODE_RE = re.compile(r"\{\{<.*?>\}\}", re.DOTALL)
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
# Text analysis


def split_front_matter(text: str, source: str = "the .qmd") -> tuple[dict, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        first_line = text[:m.start(1)].count("\n") + 1
        raise InputError(yaml_error_message(source, exc, first_line=first_line)) from exc
    return (meta if isinstance(meta, dict) else {}), text[m.end():]


def prose(body: str, *, include_figure_captions: bool = True,
          include_table_captions: bool = True) -> str:
    """Fenced chunks and HTML comments removed; each image markdown collapses
    to its alt/caption text (captions are prose the journal's word count
    includes — dropping them entirely undercounts); each inline code
    expression collapses to one placeholder word (a code-generated number
    reads as one word in any journal's count). Table/figure captions declared
    as chunk options inside fences are kept unless the counting policy excludes
    that caption kind. Citation/crossref checks always use the inclusive defaults."""
    captions = [
        caption for kind, caption in CHUNK_CAPTION_RE.findall(body)
        if (include_figure_captions if kind == "fig" else include_table_captions)
    ]
    body = FENCE_RE.sub("", body)
    body = COMMENT_RE.sub("", body)
    body = DIV_FENCE_RE.sub("", body)
    body = SHORTCODE_RE.sub("", body)
    body = IMAGE_RE.sub(lambda m: m.group(1) if include_figure_captions else "", body)
    if not include_table_captions:
        body = _without_table_captions(body)
    if captions:
        body = body + "\n" + "\n".join(captions) + "\n"
    return INLINE_CODE_RE.sub("X", body)


def _without_table_captions(body: str) -> str:
    """A ':' paragraph is a caption when labelled or adjacent to a pipe table.

    Requiring table context preserves Markdown definition lists and prose
    paragraphs that happen to start with 'Table:'.
    """
    table_rule = re.compile(
        r"^ *\|? *:?-+:? *(?:\| *:?-+:? *)+\|? *$", re.MULTILINE)

    def remove(match: re.Match) -> str:
        caption = match[0]
        before = body[:match.start()].rstrip("\n").rsplit("\n\n", 1)[-1]
        after = body[match.end():].lstrip("\n").split("\n\n", 1)[0]
        if (re.search(r"\{#tbl-[\w-]+", caption)
                or table_rule.search(before) or table_rule.search(after)):
            return ""
        return caption

    return re.sub(r"^ {0,3}(?:Table:|:)[ \t]+\S[^\n]*(?:\n[^\n]+)*", remove, body,
                  flags=re.MULTILINE)


def _heading_name(title: str) -> str:
    """Match a section title, ignoring Pandoc attributes and manual numbering."""
    title = re.sub(r"\s+#+\s*$", "", title)
    title = re.sub(r"\s+\{[^}]*\}\s*$", "", title)
    title = re.sub(r"[*_`]", "", title)
    title = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", title)
    return " ".join(title.casefold().split())


def _without_sections(body: str, titles: list[str], *, exclude_boxes: bool = False,
                      exclude_figure_divs: bool = False) -> str:
    """Remove named sections through the next heading of equal/higher rank.

    Code fences cannot start or end manuscript sections. Keep retained chunks
    intact so `prose()` can still harvest their captions.
    """
    excluded = {_heading_name(t) for t in titles}
    lines = COMMENT_RE.sub("", body).splitlines(keepends=True)
    kept: list[str] = []
    skip_level = 0
    fence = ""
    divs: list[bool] = []
    underline_index = -1
    for i, line in enumerate(lines):
        if i == underline_index:
            continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence)
                    and not marker[2].strip()):
                fence = ""
        elif marker:
            fence = marker[1]
        else:
            div = re.match(r"^ {0,3}:{3,}(.*)$", line)
            if div:
                attributes = div[1].strip()
                if attributes:
                    box = exclude_boxes and bool(re.search(
                        r"(?:^|[\s{])(?:\.box|#box-[\w-]+|box)(?=[\s}]|$)", attributes))
                    figure = exclude_figure_divs and bool(re.search(
                        r"(?:^|[\s{])#fig-[\w-]+(?=[\s}]|$)", attributes))
                    divs.append(box or figure)
                elif divs:
                    divs.pop()
            if any(divs):
                continue
            heading = re.match(r"^ {0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
            level, title = (len(heading[1]), heading[2]) if heading else (0, "")
            if not heading and line.strip() and i + 1 < len(lines):
                underline = re.fullmatch(r" {0,3}(=+|-+)[ \t]*\n?", lines[i + 1])
                if underline:
                    level, title = (1 if underline[1][0] == "=" else 2), line.strip()
                    underline_index = i + 1
            if level:
                if skip_level and level <= skip_level:
                    skip_level = 0
                name = _heading_name(title)
                is_box = exclude_boxes and re.fullmatch(r"box(?:es)?(?:\s+\d+\b.*)?", name)
                if not skip_level and (name in excluded or is_box):
                    skip_level = level
                continue  # headings themselves never enter the prose count
        if not skip_level and not any(divs):
            kept.append(line)
    return "".join(kept)


def word_count(text: str, *, include_abstract: bool = True,
               exclude_sections: list[str] | None = None,
               include_figure_captions: bool = True,
               include_table_captions: bool = True,
               exclude_boxes: bool = False) -> int:
    """Source-level estimate using the manuscript type's explicit exclusions.

    Defaults preserve the legacy body + abstract + captions count. Section
    exclusions respect heading depth; excluding the abstract covers YAML and
    a body Abstract section. Title, keywords and author metadata never count.
    This remains a source approximation (inline code is one placeholder word),
    not the journal's submission-system count; `counting_rule` is authoritative.
    """
    meta, body = split_front_matter(text)
    titles = list(exclude_sections or [])
    if not include_abstract:
        titles.append("Abstract")
    if titles or exclude_boxes or not include_figure_captions:
        body = _without_sections(body, titles, exclude_boxes=exclude_boxes,
                                 exclude_figure_divs=not include_figure_captions)
    counted = prose(body, include_figure_captions=include_figure_captions,
                    include_table_captions=include_table_captions)
    total = len(HEADING_RE.sub("", counted).split())
    abstract = meta.get("abstract")
    if include_abstract and isinstance(abstract, str):
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


def bibliography_paths(project: Path, index_text: str) -> list[Path]:
    """The .bib files Quarto will resolve citations against: `bibliography`
    in the .qmd front matter, then in `_quarto.yml` (string or list), with
    `refs.bib` as the scaffold default when neither names one."""
    project = Path(project)
    names: list[str] = []

    def collect(value) -> None:
        if isinstance(value, str):
            names.append(value)
        elif isinstance(value, list):
            names.extend(str(v) for v in value)

    meta, _ = split_front_matter(index_text)
    collect(meta.get("bibliography"))
    quarto_yml = project / "_quarto.yml"
    if quarto_yml.exists():
        try:
            cfg = yaml.safe_load(read_text(quarto_yml)) or {}
        except yaml.YAMLError:
            cfg = {}
        collect(cfg.get("bibliography"))
    if not names:
        names = ["refs.bib"]
    return [project / n for n in names]


def image_paths(text: str) -> list[str]:
    """Markdown image targets in prose — fenced code and HTML comments are
    not rendered, so a commented-out figure is not a missing figure."""
    body = COMMENT_RE.sub("", FENCE_RE.sub("", split_front_matter(text)[1]))
    return [m.group(2) for m in IMAGE_RE.finditer(body)]


# ---------------------------------------------------------------------------
# Checks (verbatim report shape from validate.py)


@dataclass
class Check:
    name: str
    level: str  # "HARD" | "WARN"
    ok: bool
    detail: str
    locations: list[str] = field(default_factory=list)  # "index.qmd:12: @key"
    patch_hint: dict | None = None


def _locations(texts: dict[str, str], items: list[str], pattern) -> list[str]:
    """file:line hints for each item, in file then line order."""
    found = []
    for name, text in texts.items():
        for lineno, line in enumerate(text.splitlines(), start=1):
            for item in items:
                if pattern(item).search(line):
                    found.append(f"{name}:{lineno}: {item}")
    return found


def _at_ref(item: str):
    return re.compile(r"(?<![\w@.\\])-?@" + re.escape(item) + r"(?![\w:.#$%&+?<>~/-]*[\w])")


def _reference_words(path: Path) -> int:
    """Read Quarto/Pandoc's Bibliography paragraphs, including hyperlink text.

    Join runs before splitting words: italic titles and linked DOIs can split
    a word across XML elements. Tabs and line breaks are word separators.
    """
    doc = Document(path)
    total = 0
    for paragraph in doc.element.xpath(".//w:p[w:pPr/w:pStyle[@w:val='Bibliography']]"):
        text = "".join(
            (node.text or "") if node.tag == qn("w:t") else " "
            for node in paragraph.iter()
            if node.tag in {qn("w:t"), qn("w:tab"), qn("w:br"), qn("w:cr")}
        )
        total += len(text.split())
    return total


def _references_expected(project: Path, text: str) -> bool:
    """Citations or nocite request a bibliography even if the output lacks one."""
    meta, _ = split_front_matter(text)
    if citekeys_used(text):
        return True
    config = project / "_quarto.yml"
    if config.exists():
        try:
            data = yaml.safe_load(read_text(config))
        except yaml.YAMLError as exc:
            raise InputError(yaml_error_message("_quarto.yml", exc)) from exc
        if isinstance(data, dict):
            meta = {**data, **meta}
    return bool(meta.get("nocite")) or bool(citekeys_used(str(meta.get("abstract", ""))))


def run_checks(project: Path, *, rendered_main: Path | None = None) -> list[Check]:
    """Check sources; the render pipeline can supply its newly staged main DOCX.

    Never pick up an old output implicitly: its bibliography may be stale or
    edited in Word. The combined count remains a source estimate plus the
    rendered reference words, not Word's or a submission system's word count.
    """
    project = Path(project)
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    mtype = manuscript_type(profile, cfg["ms_type"])
    checks: list[Check] = []

    texts = {}
    for name in ("index.qmd", "si.qmd"):
        p = project / name
        if p.exists():
            texts[name] = read_text(p)
    if "index.qmd" not in texts:
        raise InputError(f"index.qmd not found in {project} (is this a wongo project? "
                         "`wongo scaffold` creates one)")
    for name, text in texts.items():  # a front-matter typo names its file and line
        split_front_matter(text, source=name)

    wc = word_count(texts["index.qmd"], **mtype.get("word_count", {}))
    limit = mtype.get("word_limit")
    includes_refs = bool(mtype.get("word_limit_includes_references"))
    reference_words = None
    missing_references = False
    if includes_refs and rendered_main is not None:
        reference_words = _reference_words(rendered_main)
        missing_references = reference_words == 0 and _references_expected(project, texts["index.qmd"])
        wc += reference_words
    detail = (f"{wc} words vs limit {limit} for {cfg['ms_type']} "
              f"(rule: {mtype.get('counting_rule', 'unspecified')})")
    if missing_references:
        detail += "; reference-inclusive total unverified: rendered bibliography text was not found"
    elif reference_words is not None:
        detail += (f"; estimated total: {wc - reference_words} source + "
                   f"{reference_words} reference words from this render's main DOCX")
    elif includes_refs:
        detail += "; lower bound: references are not counted but this limit includes them"
    wc_ok = limit is None or wc <= limit
    wc_hint = None
    if not wc_ok:
        wc_hint = {
            "action": "trim_words",
            "target_words": limit,
            "excess_words": wc - limit,
            "hint": f"Trim at least {wc - limit} words from index.qmd or exclude non-counted sections.",
        }
    checks.append(Check("word-limit", "HARD", wc_ok, detail, patch_hint=wc_hint))
    if missing_references:
        checks.append(Check(
            "word-limit-references", "HARD", False,
            "The main manuscript requests references, but this render has no text in "
            "Bibliography paragraphs. The reference-inclusive count is unverified. "
            "Enable Quarto's bibliography (remove suppress-bibliography) and preserve "
            "its Bibliography paragraph style; render --target collab to inspect the output.",
        ))
    elif includes_refs and reference_words is None and limit is not None and wc <= limit:
        # body + abstract is only a lower bound here, so a pass is unproven
        checks.append(Check(
            "word-limit-references", "WARN", False,
            f"{wc} words counted without references; the {limit}-word limit "
            f"includes references (headroom {limit - wc} words). Run "
            "`wongo render --target submission` to check the newly rendered bibliography "
            "before any deliverable is replaced",
        ))

    bib: set[str] = set()
    bib_paths = bibliography_paths(project, texts["index.qmd"])
    for bib_path in bib_paths:
        if bib_path.exists():
            bib |= bib_keys(read_text(bib_path))
    used = set().union(*(citekeys_used(t) for t in texts.values()))
    missing = sorted(used - bib)
    cite_hint = None
    if missing:
        cite_hint = {
            "action": "add_bibtex",
            "missing_keys": missing,
            "bib_files": [str(b.name) for b in bib_paths if b.exists()] or ["refs.bib"],
            "hint": f"Add BibTeX entries for {', '.join(missing)} to refs.bib or remove unused citations.",
        }
    checks.append(Check(
        "citekeys", "HARD", not missing,
        "all citekeys resolve" if not missing else f"missing from refs.bib: {', '.join(missing)}",
        _locations(texts, [f"@{k}" for k in missing], lambda item: _at_ref(item[1:])),
        patch_hint=cite_hint,
    ))

    defined = set().union(*(labels_defined(t) for t in texts.values()))
    orphans = sorted(set().union(*(crossrefs_used(t) for t in texts.values())) - defined)
    cross_hint = None
    if orphans:
        cross_hint = {
            "action": "define_labels",
            "orphan_refs": orphans,
            "hint": f"Define labels for {', '.join(orphans)} using '#| label: <name>' or '{{#<name>}}'.",
        }
    checks.append(Check(
        "crossrefs", "HARD", not orphans,
        "all cross-references resolve" if not orphans else f"orphaned: {', '.join(orphans)}",
        _locations(texts, [f"@{o}" for o in orphans], lambda item: _at_ref(item[1:])),
        patch_hint=cross_hint,
    ))

    missing_figs, missing_paths = [], []
    for name, text in texts.items():
        for rel in image_paths(text):
            if not (project / rel).exists():
                missing_figs.append(f"{name} -> {rel}")
                missing_paths.append(rel)
    fig_hint = None
    if missing_figs:
        fig_hint = {
            "action": "create_assets",
            "missing_paths": sorted(set(missing_paths)),
            "hint": f"Place image files at {', '.join(sorted(set(missing_paths)))} or fix image links.",
        }
    checks.append(Check(
        "figures", "HARD", not missing_figs,
        "all referenced figures exist" if not missing_figs else "; ".join(missing_figs),
        _locations(texts, sorted(set(missing_paths)),
                   lambda item: re.compile(r"\(" + re.escape(item) + r"[)\s]")),
        patch_hint=fig_hint,
    ))

    days = profile_staleness_days(profile)
    profile_date_ok = days is not None and 0 <= days <= STALE_DAYS
    if days is None:
        profile_detail = "profile has no verified_date"
    elif days < 0:
        profile_detail = f"profile verified_date is {-days} days in the future"
    else:
        profile_detail = f"profile verified {days} days ago"
    checks.append(Check(
        "profile-staleness", "WARN", profile_date_ok, profile_detail,
    ))

    si_expected = (profile.get("si") or {}).get("separate_file")
    si_ok = not si_expected or "si.qmd" in texts
    si_hint = None
    if not si_ok:
        si_hint = {
            "action": "create_si",
            "target": "si.qmd",
            "hint": "Create si.qmd for Supporting Information expected by journal profile.",
        }
    checks.append(Check(
        "si-file", "WARN", si_ok,
        "si.qmd present" if "si.qmd" in texts else "profile expects separate SI but si.qmd is absent",
        patch_hint=si_hint,
    ))
    return checks


def print_report(checks: list[Check]) -> None:
    for c in checks:
        mark = "PASS" if c.ok else ("FAIL" if c.level == "HARD" else "WARN")
        print(f"[{mark}] {c.level:4} {c.name}: {c.detail}")
        if not c.ok:
            for location in c.locations:
                print(f"      {location}")
            if c.patch_hint and "hint" in c.patch_hint:
                print(f"      hint: {c.patch_hint['hint']}")
