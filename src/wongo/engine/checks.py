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
INLINE_CODE_RE = re.compile(
    r"(?<!`)(`+)(?!`)((?:(?!\n[ \t\r]*\n).)*?)(?<!`)\1(?!`)", re.DOTALL,
)
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
DISPLAY_ITEM_MARKDOWN_ID_RE = re.compile(r"\{#((?:fig|tbl)-[\w.-]+)")
CODE_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
CHUNK_LABEL_RE = re.compile(r"^\s*#\|\s*label:\s*[\"']?((?:fig|tbl|lst)-[\w.-]+)[\"']?\s*$")
MARKDOWN_LABEL_RE = re.compile(r"\{#((?:fig|tbl|eq|sec|lst|thm)-[\w.-]+)")
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
    body, chunks = _markdown_context(body)
    captions = [
        caption for _, chunk in chunks for kind, caption in _chunk_captions(chunk)
        if (include_figure_captions if kind == "fig" else include_table_captions)
    ]
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
    lines = _markdown_context(body, keep_code=True)[0].splitlines(keepends=True)
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


def word_count_breakdown(text: str, policy: dict, reference_words: int | None,
                         includes_references: bool) -> dict:
    """Decompose the existing source counter without introducing another policy."""
    source_total = word_count(text, **policy)
    no_abstract_policy = {**policy, "include_abstract": False}
    no_abstract = word_count(text, **no_abstract_policy)
    no_figure_policy = {**no_abstract_policy, "include_figure_captions": False}
    no_figure = word_count(text, **no_figure_policy)
    body = word_count(text, **{**no_figure_policy, "include_table_captions": False})
    return {
        "abstract": source_total - no_abstract,
        "body": body,
        "figure_captions": no_abstract - no_figure,
        "table_captions": no_figure - body,
        "source_total": source_total,
        "excluded_source_words": word_count(text) - source_total,
        "excluded_sections": list(policy.get("exclude_sections") or []),
        "rendered_references": reference_words if includes_references else 0,
        "references_status": (
            "included-from-render" if reference_words is not None else "pending-render"
        ) if includes_references else "excluded-by-profile",
        "total": source_total + (reference_words or 0),
        "approximation": [
            "Whitespace-delimited source estimate; citation syntax remains source text.",
            "Inline code contributes one placeholder token; generated output is not evaluated.",
            "Caption categories follow the source counter, including figure-block text.",
            "Excluded words are diagnostic and are not added to the included total.",
        ],
        "generated_content": "not-evaluated",
        "inline_code": "one-placeholder-token-per-expression",
    }


def crossrefs_used(text: str) -> set[str]:
    body = prose(split_front_matter(text)[1])
    return {ref.rstrip(".,;:]") for ref in REF_USE_RE.findall(body)}


def labels_defined(text: str) -> set[str]:
    return {label for label, _ in _label_locations(text)}


def _comment_free_line(text: str, start: int, end: int, comment: bool,
                       inline_end: int) -> tuple[str, bool, int]:
    kept = []
    cursor = start
    while cursor < end:
        if inline_end > cursor:
            stop = min(end, inline_end)
            kept.append(text[cursor:stop])
            cursor = stop
        elif comment:
            closing = text.find("-->", cursor, end)
            if closing < 0:
                kept.append("\n" if text[start:end].endswith("\n") else "")
                break
            cursor = closing + 3
            comment = False
        else:
            token = re.search(r"<!--|`+", text[cursor:end])
            if token is None:
                kept.append(text[cursor:end])
                break
            token_start = cursor + token.start()
            kept.append(text[cursor:token_start])
            cursor = token_start + len(token[0])
            if token[0] == "<!--":
                comment = True
                continue
            closing = re.search(r"(?<!`)" + re.escape(token[0]) + r"(?!`)", text[cursor:])
            paragraph = re.search(r"\n[ \t\r]*\n", text[cursor:])
            if closing and (paragraph is None or closing.start() < paragraph.start()):
                inline_end = cursor + closing.end()
            kept.append(token[0])
    return "".join(kept), comment, inline_end


def _markdown_context(text: str, *, keep_code: bool = False) -> tuple[str, list[tuple[int, str]]]:
    """Mask metadata/comments/fences and retain executable chunk source separately.

    Both masked prose and chunk offsets retain the source's line numbers.
    A literal code example cannot introduce labels or chunk-option captions.
    Section filtering retains code verbatim so later prose extraction can
    harvest captions and ignore headings inside code.
    """
    metadata = FRONT_MATTER_RE.match(text)
    if metadata:
        text = "\n" * text[:metadata.end()].count("\n") + text[metadata.end():]
    visible = []
    chunks = []
    fence = ""
    executable = False
    chunk = []
    start = 0
    comment = False
    inline_end = 0
    offset = 0
    list_indent = 0
    indented_code = False
    previous_blank = True
    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        line_end = offset + len(line)
        in_inline = inline_end > offset
        logical = line
        if not fence:
            indent = len(line) - len(line.lstrip(" "))
            item = re.match(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+", line)
            if item and not comment and not in_inline:
                list_indent = item.end()
                logical = line[item.end():]
            else:
                if line.strip() and indent < list_indent:
                    list_indent = 0
                logical = line[list_indent:] if list_indent else line
            relative_indent = len(logical) - len(logical.lstrip(" "))
            if (not comment and not in_inline and line.strip()
                    and relative_indent >= 4 and (indented_code or previous_blank)):
                indented_code = True
                visible.append(line if keep_code else "\n" if line.endswith("\n") else "")
                offset = line_end
                previous_blank = False
                continue
            if line.strip():
                indented_code = False
            line, comment, inline_end = _comment_free_line(text, offset, line_end, comment, inline_end)
            if item:
                logical = line[item.end():]
            else:
                logical = line[list_indent:] if list_indent else line
        else:
            logical = line[list_indent:] if list_indent else line
        marker = None if in_inline else CODE_FENCE_RE.match(logical)
        offset = line_end
        previous_blank = not line.strip()
        if not fence:
            if not marker:
                visible.append(line)
                continue
            fence = marker[1]
            inline_end = 0
            executable = bool(re.match(r"\{[A-Za-z]\w*(?:[\s,}]|$)", marker[2].strip()))
            chunk = [logical]
            start = lineno
        else:
            chunk.append(line)
            if (marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence)
                    and not marker[2].strip()):
                if executable:
                    chunks.append((start, "".join(chunk)))
                fence = ""
        visible.append(line if keep_code else "\n" if line.endswith("\n") else "")
    return "".join(visible), chunks


def _chunk_labels(chunk: str) -> list[tuple[str, int]]:
    labels = []
    lines = chunk.splitlines()
    header = re.match(r"^\s*(?:`{3,}|~{3,})\{\w+[,]?\s+((?:fig|tbl|lst)-[\w.-]+)\s*[},]", lines[0])
    if header:
        labels.append((header[1], 0))
    for offset, line in enumerate(lines[1:], start=1):
        match = CHUNK_LABEL_RE.match(line)
        if match:
            labels.append((match[1], offset))
    return labels


def _chunk_captions(chunk: str) -> list[tuple[str, str]]:
    options = "\n".join(
        match[1] for line in chunk.splitlines()
        if (match := re.match(r"^\s*#\| ?(.*)$", line))
    )
    try:
        parsed = yaml.safe_load(options)
    except yaml.YAMLError:
        return CHUNK_CAPTION_RE.findall(chunk)
    if not isinstance(parsed, dict):
        return []
    captions = []
    for kind in ("fig", "tbl"):
        raw = parsed.get(f"{kind}-cap")
        if isinstance(raw, str):
            captions.append((kind, raw))
        elif isinstance(raw, list):
            captions.extend((kind, str(value)) for value in raw)
    return captions


def _label_locations(text: str) -> list[tuple[str, int]]:
    visible, chunks = _markdown_context(text)
    visible = INLINE_CODE_RE.sub(lambda match: "\n" * match[0].count("\n"), visible)
    found = []
    for lineno, line in enumerate(visible.splitlines(), start=1):
        found.extend((match[1], lineno) for match in MARKDOWN_LABEL_RE.finditer(line))
    for start, chunk in chunks:
        found.extend((label, start + offset) for label, offset in _chunk_labels(chunk))
    return sorted(found, key=lambda item: item[1])


def _display_callouts_used(text: str) -> set[str]:
    visible, chunks = _markdown_context(text)

    def without_self_refs(caption: str, attributes: str) -> str:
        owners = set(DISPLAY_ITEM_MARKDOWN_ID_RE.findall(attributes))
        return REF_USE_RE.sub(lambda match: "" if match[1].rstrip(".,;:]") in owners
                             else match[0], caption)

    visible = IMAGE_RE.sub(
        lambda match: "![" + without_self_refs(match[1], match[3] or "")
        + "](" + match[2] + ")" + (match[3] or ""), visible,
    )
    visible = re.sub(
        r"^ {0,3}(?:Table:|:)[ \t]+\S[^\n]*(?:\n[^\n]+)*",
        lambda match: without_self_refs(match[0], match[0]), visible, flags=re.MULTILINE,
    )
    lines = visible.splitlines(keepends=True)
    divs = []
    for index, line in enumerate(lines):
        div = re.match(r"^ {0,3}:{3,}(.*)$", line)
        if not div:
            continue
        if div[1].strip():
            divs.append((index, div[1]))
        elif divs:
            opening, attributes = divs.pop()
            end = index
            while end > opening + 1 and not lines[end - 1].strip():
                end -= 1
            start = end
            while start > opening + 1 and lines[start - 1].strip():
                start -= 1
            for caption_line in range(start, end):
                lines[caption_line] = without_self_refs(lines[caption_line], attributes)
    visible = "".join(lines)
    used = crossrefs_used(visible)
    for _, chunk in chunks:
        owners = {label for label, _ in _chunk_labels(chunk)}
        for _, caption in _chunk_captions(chunk):
            used.update(crossrefs_used(caption) - owners)
    return used


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


def display_items_defined(text: str) -> list[tuple[str, int]]:
    """Harvest defined figure and table labels across index.qmd.

    Counts unique labels starting with 'fig-' and 'tbl-' defined via chunk options
    (#| label: ...), knitr chunk headers (```{r fig-...}), and markdown crossref
    identifiers ({#fig-...}, {#tbl-...}). HTML comments are stripped while
    preserving line numbers.
    """
    found: dict[str, int] = {}
    for label, lineno in _label_locations(text):
        if label.startswith(("fig-", "tbl-")):
            found.setdefault(label, lineno)
    return list(found.items())


def abstract_words(meta: dict) -> tuple[int, bool]:
    """Return (word_count, present_bool) for frontmatter abstract."""
    raw = meta.get("abstract")
    if raw is None:
        return 0, False
    if isinstance(raw, str):
        if not raw.strip():
            return 0, False
        return len(raw.split()), True
    if isinstance(raw, list):
        if not raw:
            return 0, False
        return sum(len(str(p).split()) for p in raw), True
    text = str(raw).strip()
    if not text:
        return 0, False
    return len(text.split()), True


def parse_highlights_text(text: str, filename: str = "highlights.md") -> list[tuple[str, str]]:
    """Parse bullet points from highlights markdown text.

    Ignores markdown headings (# ...) and blank lines. Lines starting with list
    markers (-, *, +, •, 1.) begin a new bullet item. Continuation lines append
    to the active bullet with a single space.
    """
    bullets: list[tuple[str, str]] = []
    current_bullet: list[str] = []
    current_lineno = 0

    def flush():
        nonlocal current_bullet, current_lineno
        if current_bullet:
            b_text = " ".join(current_bullet).strip()
            if b_text:
                bullets.append((b_text, f"{filename}:{current_lineno}"))
            current_bullet = []
            current_lineno = 0

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            flush()
            continue
        m = re.match(r"^(?:[-*+•]|\d+[.)])\s+(.*)$", stripped)
        if m:
            flush()
            current_bullet = [m.group(1).strip()]
            current_lineno = lineno
        elif current_bullet:
            current_bullet.append(stripped)
        else:
            current_bullet = [stripped]
            current_lineno = lineno

    flush()
    return bullets


def parse_frontmatter_highlights(raw: object) -> list[tuple[str, str]]:
    """Parse highlights provided in index.qmd frontmatter (list or block)."""
    if isinstance(raw, list):
        out = []
        for idx, item in enumerate(raw, start=1):
            s = str(item).strip()
            m = re.match(r"^(?:[-*+•]|\d+[.)])\s+(.*)$", s)
            if m:
                s = m.group(1).strip()
            if s:
                out.append((s, f"index.qmd:frontmatter: highlights[{idx}]"))
        return out
    if isinstance(raw, str):
        return parse_highlights_text(raw, filename="index.qmd:frontmatter")
    return []


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
    breakdown: dict | None = None


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
    index_meta = {}
    for name, text in texts.items():  # a front-matter typo names its file and line
        meta, _ = split_front_matter(text, source=name)
        if name == "index.qmd":
            index_meta = meta

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
              f"(rule: {mtype.get('counting_rule', 'unspecified')}; "
              "source estimate, not a submission-portal count)")
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
    checks.append(Check(
        "word-limit", "HARD", wc_ok, detail, patch_hint=wc_hint,
        breakdown=word_count_breakdown(texts["index.qmd"], mtype.get("word_count", {}),
                                       reference_words, includes_refs),
    ))
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

    from wongo.engine.si_refs import enabled as si_refs_enabled
    from wongo.engine.si_refs import source_issues, source_requests

    si_issues, si_count = source_issues(cfg, texts)
    if si_count or si_refs_enabled(cfg):
        checks.append(Check(
            "si-references", "HARD", not si_issues,
            "; ".join(si_issues) if si_issues else
            f"{si_count} static main-to-SI request(s); destinations and numbers are unverified until render",
            si_issues,
            patch_hint={"action": "configure_si_references", "hint":
                        "Enable si_references: true and use [SI item](wongo-si:fig-label) "
                        "or [SI item](wongo-si:tbl-label) from index.qmd with si.qmd present."}
            if si_issues else None,
        ))

    defined = {name: labels_defined(text) for name, text in texts.items()}
    unresolved = []
    locations = []
    for name, text in texts.items():
        for ref in sorted(crossrefs_used(text)):
            if ref in defined.get(name, set()):
                continue
            unresolved.append(f"{name}: @{ref}")
            locations.extend(_locations(
                {name: text}, [f"@{ref}"], lambda item: _at_ref(item[1:]),
            ))
    owners: dict[str, list[str]] = {}
    for name, labels in defined.items():
        for label in labels:
            owners.setdefault(label, []).append(name)
    duplicates = sorted(label for label, docs in owners.items() if len(docs) > 1)
    for label in duplicates:
        for name in owners[label]:
            locations.append(f"{name}: duplicate {label}")
    parts = []
    if unresolved:
        parts.append("unresolved in their own document: " + ", ".join(unresolved))
    if duplicates:
        parts.append("defined in more than one document: " + ", ".join(duplicates))
    cross_hint = None
    if unresolved or duplicates:
        cross_hint = {
            "action": "define_labels",
            "orphan_refs": [item.split(": @", 1)[-1] for item in unresolved],
            "duplicate_labels": duplicates,
            "hint": (
                "A cross-reference resolves only in the document that defines its label. "
                "Define it there, or remove the duplicate label from the other document."
            ),
        }
    checks.append(Check(
        "crossrefs", "HARD", not parts,
        "all cross-references resolve" if not parts else "; ".join(parts),
        locations, patch_hint=cross_hint,
    ))

    uncited = []
    for name, text in texts.items():
        used = _display_callouts_used(text)
        if name == "si.qmd" and si_refs_enabled(cfg) and not si_issues:
            used.update(label for label, _ in source_requests(texts["index.qmd"]))
        labels = {lbl for lbl, _ in display_items_defined(text)}
        labels.update(lbl for lbl in defined.get(name, set()) if lbl.startswith(("fig-", "tbl-")))
        for label in sorted(labels - used):
            uncited.append(f"{name}: {label}")
    checks.append(Check(
        "uncited", "WARN", not uncited,
        ("all display items have local or explicit main-to-SI callouts" if si_refs_enabled(cfg) else
         "all display items are cited in their own document") if not uncited else
        "display items not cited in their own document: " + ", ".join(uncited),
        uncited,
    ))

    from wongo.engine.inputs import declared_inputs, discover_candidates

    declared = declared_inputs(project, cfg)
    missing_inputs = sorted(
        item.key for item in declared if item.path is None or not item.path.exists()
    )
    if declared:
        checks.append(Check(
            "dependencies", "HARD", not missing_inputs,
            "declared inputs present" if not missing_inputs else
            "declared input missing: " + ", ".join(missing_inputs),
            missing_inputs,
        ))
    if cfg.get("dependencies_discover") is True:
        from wongo.engine import source_fingerprint

        known = set(source_fingerprint(project))
        candidates = discover_candidates(project, texts, known)
        checks.append(Check(
            "undeclared-inputs", "WARN", not candidates,
            "no undeclared literal inputs found (static scan, not exhaustive)" if not candidates
            else "possible undeclared inputs (static scan, not exhaustive): "
            + ", ".join(candidates),
            candidates,
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

    max_display_items = mtype.get("max_display_items")
    if max_display_items is not None:
        detected = display_items_defined(texts["index.qmd"])
        fig_items = [lbl for lbl, _ in detected if lbl.startswith("fig-")]
        tbl_items = [lbl for lbl, _ in detected if lbl.startswith("tbl-")]
        total_items = len(detected)
        disp_ok = total_items <= max_display_items
        disp_detail = (
            f"{total_items} display items vs limit {max_display_items} for {cfg['ms_type']} "
            f"({len(fig_items)} figures, {len(tbl_items)} tables)"
            if disp_ok else
            f"{total_items} display items exceed limit {max_display_items} for {cfg['ms_type']} "
            f"({len(fig_items)} figures, {len(tbl_items)} tables)"
        )
        disp_locations = [f"index.qmd:{lineno}: {lbl}" for lbl, lineno in detected]
        disp_hint = None
        if not disp_ok:
            disp_hint = {
                "action": "reduce_display_items",
                "target_items": max_display_items,
                "excess_items": total_items - max_display_items,
                "defined_items": sorted([lbl for lbl, _ in detected]),
                "hint": (
                    f"Move at least {total_items - max_display_items} display item(s) to Supporting "
                    f"Information (si.qmd) or combine figures/tables to meet the limit of {max_display_items}."
                ),
            }
        checks.append(Check(
            "display-items-limit", "HARD", disp_ok, disp_detail,
            disp_locations, patch_hint=disp_hint,
        ))

    abstract_min = mtype.get("abstract_min")
    abstract_limit = mtype.get("abstract_limit")
    if abstract_min is not None or abstract_limit is not None:
        words, present = abstract_words(index_meta)
        estimate = "source estimate, not a submission-portal count"
        if not present:
            bound = abstract_limit if abstract_limit is not None else abstract_min
            checks.append(Check(
                "abstract-word-limit", "HARD", False,
                f"Abstract is missing from index.qmd frontmatter "
                f"(bound is {bound} words for {cfg['ms_type']}; {estimate})",
                ["index.qmd:frontmatter: abstract"],
                patch_hint={
                    "action": "add_abstract",
                    "target_words": bound,
                    "hint": f"Add an 'abstract:' block to index.qmd frontmatter (bound {bound} words).",
                },
            ))
        else:
            too_short = abstract_min is not None and words < abstract_min
            too_long = abstract_limit is not None and words > abstract_limit
            abs_hint = None
            if too_short:
                abs_ok = False
                abs_detail = (
                    f"{words} words are below the {abstract_min}-word minimum for "
                    f"{cfg['ms_type']} abstract ({estimate})"
                )
                abs_hint = {
                    "action": "extend_abstract",
                    "target_words": abstract_min,
                    "hint": f"Extend the frontmatter abstract to at least {abstract_min} words.",
                }
            elif too_long:
                abs_ok = False
                abs_detail = (
                    f"{words} words exceed limit {abstract_limit} for "
                    f"{cfg['ms_type']} abstract ({estimate})"
                )
                abs_hint = {
                    "action": "trim_abstract",
                    "target_words": abstract_limit,
                    "excess_words": words - abstract_limit,
                    "hint": (
                        f"Trim at least {words - abstract_limit} words from the frontmatter "
                        f"abstract to meet the limit of {abstract_limit} words."
                    ),
                }
            elif abstract_limit is not None:
                abs_ok = True
                abs_detail = (
                    f"{words} words vs limit {abstract_limit} for {cfg['ms_type']} abstract "
                    f"({estimate})"
                )
            else:
                abs_ok = True
                abs_detail = (
                    f"{words} words vs minimum {abstract_min} for {cfg['ms_type']} abstract "
                    f"({estimate})"
                )
            checks.append(Check(
                "abstract-word-limit", "HARD", abs_ok, abs_detail,
                ["index.qmd:frontmatter: abstract"], patch_hint=abs_hint,
            ))

    hl_cfg = profile.get("highlights")
    if isinstance(hl_cfg, dict) and hl_cfg.get("required") is True:
        hl_file = project / "highlights.md"
        has_file = hl_file.exists()
        has_frontmatter = "highlights" in index_meta and index_meta["highlights"] is not None

        if not has_file and not has_frontmatter:
            checks.append(Check(
                "highlights", "WARN", False,
                "highlights.md (or frontmatter highlights) not found; profile specifies highlights.required: true",
                ["highlights.md"],
                patch_hint={
                    "action": "create_highlights",
                    "target": "highlights.md",
                    "hint": "Create highlights.md with 3-5 bullet points (each <= 85 characters including spaces).",
                },
            ))
        else:
            if has_file:
                bullets_with_loc = parse_highlights_text(read_text(hl_file), filename="highlights.md")
            else:
                bullets_with_loc = parse_frontmatter_highlights(index_meta["highlights"])

            max_chars = hl_cfg.get("max_chars_per_bullet") or 85
            if cfg.get("ms_type") == "making-waves" and hl_cfg.get("count_making_waves"):
                min_bullets, max_bullets = 1, hl_cfg.get("count_making_waves")
            elif hl_cfg.get("count") and isinstance(hl_cfg["count"], list) and len(hl_cfg["count"]) == 2:
                min_bullets, max_bullets = hl_cfg["count"][0], hl_cfg["count"][1]
            elif hl_cfg.get("count_general") and isinstance(hl_cfg["count_general"], list) and len(hl_cfg["count_general"]) == 2:
                min_bullets, max_bullets = hl_cfg["count_general"][0], hl_cfg["count_general"][1]
            else:
                min_bullets, max_bullets = 3, 5

            bullets = [b for b, _ in bullets_with_loc]
            count_ok = min_bullets <= len(bullets) <= max_bullets
            long_bullets = [
                (idx, b, loc) for idx, (b, loc) in enumerate(bullets_with_loc, start=1)
                if len(b) > max_chars
            ]
            length_ok = len(long_bullets) == 0
            hl_ok = count_ok and length_ok

            if not count_ok and not length_ok:
                hl_detail = (
                    f"{len(bullets)} highlights bullets (expected {min_bullets}-{max_bullets}); "
                    f"{len(long_bullets)} bullet(s) exceed {max_chars} characters"
                )
            elif not count_ok:
                hl_detail = f"{len(bullets)} highlights bullets (expected {min_bullets}-{max_bullets})"
            elif not length_ok:
                max_len = max(len(b) for _, b, _ in long_bullets)
                hl_detail = f"{len(long_bullets)} highlight bullet(s) exceed {max_chars} characters (longest: {max_len} chars)"
            else:
                max_len = max((len(b) for b in bullets), default=0)
                hl_detail = f"{len(bullets)} highlights bullets (all <= {max_chars} characters, longest: {max_len} chars)"

            if long_bullets:
                hl_locations = [f"{loc}: {len(b)} chars (> {max_chars}): {b}" for _, b, loc in long_bullets]
            else:
                hl_locations = [loc for _, loc in bullets_with_loc]

            hl_hint = None
            if not hl_ok:
                if not length_ok:
                    hl_hint = {
                        "action": "trim_highlights",
                        "max_chars": max_chars,
                        "violations": [
                            {"bullet": idx, "chars": len(b), "excess": len(b) - max_chars, "text": b}
                            for idx, b, _ in long_bullets
                        ],
                        "hint": f"Trim {len(long_bullets)} highlight bullet point(s) to <= {max_chars} characters including spaces.",
                    }
                else:
                    hl_hint = {
                        "action": "adjust_highlights_count",
                        "target_count": [min_bullets, max_bullets],
                        "current_count": len(bullets),
                        "hint": f"Provide between {min_bullets} and {max_bullets} bullet points in highlights.",
                    }

            checks.append(Check(
                "highlights", "HARD", hl_ok, hl_detail,
                hl_locations, patch_hint=hl_hint,
            ))
    return checks


def rule_coverage(profile: dict, mtype: dict) -> list[dict]:
    """Which journal rules this type enforces, and which stay manual.

    `machine` is a check in `run_checks`. `manual` is prose the profile states
    and the checker does not decide. `unsupported` has no machine rule.
    """
    rules = []
    if mtype.get("word_limit") is not None:
        rules.append({"id": "word-limit", "enforcement": "machine"})
    else:
        rules.append({"id": "word-limit", "enforcement": "unsupported"})
    abstract_rule = str(mtype.get("abstract_rule") or "")
    if mtype.get("abstract_min") is not None or mtype.get("abstract_limit") is not None:
        rules.append({"id": "abstract-length", "enforcement": "machine"})
    elif abstract_rule:
        rules.append({"id": "abstract-length", "enforcement": "manual"})
    if (mtype.get("word_count") or {}).get("exclude_sections"):
        rules.append({"id": "word-count-exclusions", "enforcement": "machine"})
    if mtype.get("max_display_items") is not None:
        rules.append({"id": "display-items-limit", "enforcement": "machine"})
    if (profile.get("highlights") or {}).get("required") is True:
        rules.append({"id": "highlights", "enforcement": "machine",
                      "detail": "Present highlights have HARD count/length checks; missing highlights are WARN."})
    lowered = abstract_rule.lower()
    if "one paragraph" in lowered or "one-paragraph" in lowered:
        rules.append({"id": "abstract-one-paragraph", "enforcement": "manual"})
    if profile.get("keywords_count"):
        rules.append({"id": "keywords", "enforcement": "manual"})
    if (profile.get("si") or {}).get("availability_paragraph"):
        rules.append({"id": "si-availability-placement", "enforcement": "manual"})
    if profile.get("orcid_hard_at"):
        rules.append({"id": "orcid", "enforcement": "manual"})
    for rule in rules:
        rule.update({
            "provenance_scope": "profile",
            "sources": list(profile.get("sources") or []),
            "verified_date": str(profile["verified_date"]) if profile.get("verified_date") else None,
        })
    for name in ("citekeys", "crossrefs", "figures"):
        rules.append({"id": name, "enforcement": "machine"})
    return rules


def coverage_for_project(project: Path) -> list[dict]:
    project = Path(project)
    cfg = load_journal_config(project)
    profile = load_profile(cfg["journal"], project)
    return rule_coverage(profile, manuscript_type(profile, cfg["ms_type"]))


def print_report(checks: list[Check], coverage: list[dict] | None = None) -> None:
    for c in checks:
        mark = "PASS" if c.ok else ("FAIL" if c.level == "HARD" else "WARN")
        print(f"[{mark}] {c.level:4} {c.name}: {c.detail}")
        if c.breakdown:
            counts = c.breakdown
            print(
                f"      included: abstract {counts['abstract']}, body {counts['body']}, "
                f"figure captions {counts['figure_captions']}, table captions {counts['table_captions']}; "
                f"excluded source words {counts['excluded_source_words']}; "
                f"rendered references {counts['rendered_references'] if counts['rendered_references'] is not None else 'pending'}"
            )
        if not c.ok:
            for location in c.locations:
                print(f"      {location}")
            if c.patch_hint and "hint" in c.patch_hint:
                print(f"      hint: {c.patch_hint['hint']}")
    if coverage is None:
        return
    manual = [item["id"] for item in coverage if item.get("enforcement") == "manual"]
    unsupported = [item["id"] for item in coverage if item.get("enforcement") == "unsupported"]
    parts = []
    if manual:
        parts.append("manual/not enforced: " + ", ".join(manual))
    if unsupported:
        parts.append("unsupported: " + ", ".join(unsupported))
    if not parts:
        parts.append("recorded rules are machine-enforced")
    print("[INFO] coverage: " + "; ".join(parts))
