# Quarto/Pandoc → DOCX Quirks Log (append-only)

Format per entry: date / symptom / cause / fix / affected versions.

- (seed) pandoc `reference-doc` controls styles only, NOT headers/footers/line
  numbers/margins reliably across Word versions → post-process with python-docx.
- (seed) Quarto docx output ignores `fig-pos`; figure placement must be handled
  in post-processing or by chunk ordering.

- 2026-07-03 / `doc.styles["Caption"]` (and every UI-name lookup that
  round-trips through python-docx's built-in "BabelFish" alias table, e.g.
  the docx-spec quirk where Word's real internal XML name is lowercase
  "caption" but the UI shows "Caption") silently emits
  `UserWarning: style lookup by style_id is deprecated. Use style name as key
  instead.` when applied to a Quarto/pandoc-produced document, even though
  the style is found and correct. Cause: pandoc's default reference.docx
  (`quarto pandoc --print-default-data-file reference.docx`) stores the
  built-in Caption style's `<w:name w:val="Caption"/>` capitalized, not
  lowercase as real Word documents do; python-docx's `Styles.__getitem__`
  first translates "Caption" -> "caption" for lookup (the BabelFish table)
  and only finds pandoc's capitalized name by falling back to a **deprecated**
  style-id match, which will be removed in a future python-docx release and
  would then raise `KeyError` instead of silently working. Fix: don't use
  `doc.styles[name]`; iterate `doc.styles` and compare `style.name == name`
  directly (added as `render._style_by_name`) — this reads the already
  UI-translated `.name` property and never triggers the id-fallback path.
  Verified no-warning under `python -W error::UserWarning`. Versions: quarto
  1.9.38, pandoc 3.8.3, python-docx 1.2.0.

- 2026-07-03 / Confirmed (no code change needed) two Step-5 "likely snags"
  behave correctly as designed at these versions: (1) `-M
  reference-doc:/abs/path` (no space around the colon) is honored by
  `quarto render --to docx` — pandoc's metadata dump during the run listed
  `reference-doc: /abs/path/reference.docx` and the resulting `Normal` style
  font matched the reference doc; no need for `--metadata` or a
  `-M "reference-doc: /abs/path"` (space) variant. (2) With `_quarto.yml`
  setting `project.output-dir: output`, `quarto render --output NAME.docx`
  writes directly into `<project>/output/NAME.docx` — it never appears at
  `<project>/NAME.docx` first — so `render.quarto_render`'s "move if produced
  next to input" branch is a no-op here but stays correct as a fallback for
  projects without `output-dir` set. Versions: quarto 1.9.38, pandoc 3.8.3.

- 2026-07-03 / A referenced figure (`![...](path){#fig-x}`) renders in docx
  as a 1-row/2-cell(ish) borderless table: the image paragraph uses style
  `Compact`, and the caption paragraph — "Figure 1: <caption text>" — uses
  style `Normal`, NOT `Caption` or `Image Caption` (both of those styles
  exist in the default reference.docx but pandoc doesn't apply them to
  figure captions at this version). Implication: font/style code that only
  targets `Caption`/`Image Caption` will miss figure captions entirely;
  `render.set_fonts`'s inclusion of `Normal` in `STYLES_TO_FONT` already
  covers this by accident, so no fix was required, but code that wants to
  style captions *differently* from body text cannot rely on paragraph style
  name — it must detect the caption by content/position within the table.
  Versions: quarto 1.9.38, pandoc 3.8.3.

- 2026-07-03 / `render.add_line_numbers` and `render.restart_page_numbering`
  appended `<w:lnNumType>`/`<w:pgNumType>` as the *last* children of
  `<w:sectPr>` via plain `sect_pr.append(...)`. This validated fine against
  pandoc's minimal reference-doc sectPr (which today only carries
  `pgSz`/`pgMar`/`cols`/`docGrid`, and happens to tolerate the extra trailing
  elements), but is a schema violation: ECMA-376's `CT_SectPr` complex type
  defines a strict child sequence — `lnNumType` and `pgNumType` must appear
  *before* `cols`/`formProt`/`vAlign`/`noEndnote`/`titlePg`/`textDirection`/
  `bidi`/`rtlGutter`/`docGrid`/`printerSettings`/`sectPrChange`. A real
  journal Word template's sectPr already contains several of those successor
  elements (at minimum `cols`/`docGrid`, often `titlePg`), so appending after
  them produces out-of-sequence XML that Word treats as corrupt: either a
  "Word found unreadable content, do you want to recover?" repair prompt on
  open, or (depending on Word build) the malformed element is silently
  dropped, meaning line numbering / restarted page numbers silently don't
  appear in the delivered submission docx. Cause: the ad-hoc
  `OxmlElement(...); sect_pr.append(...)` pattern positions the new element
  with no knowledge of the CT_SectPr sequence. (Correction, same day: an
  earlier version of this entry claimed the order was available at runtime as
  `docx.oxml.section.CT_SectPr._tag_seq` — false: that tuple is a
  class-body-local literal in python-docx's source, `del`-eted at
  class-definition end, so `CT_SectPr._tag_seq` does not exist on the class
  at runtime in python-docx 1.2.0. The successor lists must be spelled out in
  our own code; they were transcribed from that source literal / ECMA-376.)
  Fix: use `sect_pr.insert_element_before(new_elm, *successors)` — it walks
  the successor list in schema order, finds the first present successor, and
  inserts immediately before it (or appends if none exist), which is
  schema-correct regardless of how populated the sectPr already is. The
  successor list differs per element because they are adjacent in the
  sequence (`... lnNumType, pgNumType, cols ...`): for `w:pgNumType` it is
  `"w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
  "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
  "w:printerSettings", "w:sectPrChange"` (= `render._SECT_PR_TAIL`); for
  `w:lnNumType` it is `"w:pgNumType"` followed by that same tail — omitting
  `w:pgNumType` from lnNumType's list is a subtle second bug (found in
  re-review): if the sectPr already carries a `w:pgNumType` (journal template,
  or `restart_page_numbering` ran first, as `postprocess_si` does), lnNumType
  would be inserted before `w:cols` but *after* `w:pgNumType` — still
  schema-invalid. Only used on the "create new element" branch, the "reuse
  existing element" branch is unaffected. Regression-proofed in
  `tests/test_render.py` by asserting the new element's index precedes
  `w:cols`'s index (a blank `python-docx` `Document()`'s sectPr already ships
  with `w:cols`/`w:docGrid`, so this catches the bug even without a real
  journal template fixture), plus a dedicated test that calls
  `restart_page_numbering` *before* `add_line_numbers` and asserts
  `lnNumType < pgNumType < cols`. Versions: quarto 1.9.38, pandoc 3.8.3,
  python-docx 1.2.0.

- 2026-07-03 / `quarto pandoc --track-changes=all <docx> -t markdown`'s actual
  span syntax for tracked changes/comments differs from a plausible first
  guess in two ways, discovered building `roundtrip.py`'s S4 extraction
  against a synthetic coauthor DOCX (`tests/make_coauthor_docx.py`, built with
  raw `w:ins`/`w:del`/comment-range OOXML via python-docx 1.2.0's
  `Document.add_comment(runs, text, author, initials)` — this python-docx
  version has no `Paragraph.add_comment`). (1) Whitespace at the edge of a
  tracked run is emitted *outside* the span, not inside it: a deleted run
  with literal text `"partial "` (trailing space) renders as
  `[partial]{.deletion author="..." date="..."} defluorination.`, not
  `[partial ]{.deletion ...}defluorination.` — the space moves past the
  closing `}`. Any code assuming the span's bracket content is the exact
  verbatim run text (including boundary whitespace) will be off by that
  whitespace. (2) A comment's reviewer note text is emitted as the *content*
  of the `comment-start` span itself, and `comment-end` is always empty:
  `[<note text>]{.comment-start id="N" author="..." date="..."}<annotated
  text>[]{.comment-end id="N"}` — there is no separate `comment="..."`
  attribute carrying the note. (`roundtrip.extract_changes` already coded a
  defensive `m.group("text") or attrs.get("comment", "")` fallback for this
  exact ambiguity before confirming reality; the fallback turned out to be
  unnecessary but is kept as a no-op for other pandoc builds.) Separately:
  the default `--wrap=auto` can hard-wrap a long span's attribute list (and,
  for long enough insertion/deletion text, potentially the bracket content
  itself) across a line break, embedding a literal `\n` inside a
  regex-captured attribute or text run; `roundtrip.py`'s pandoc invocation
  therefore passes `--wrap=none`. Also: `python-docx` 1.2.0's
  `Document.add_comment` sets the comment's `w:date` to the current wall-clock
  time — it does not accept an explicit date parameter — so a comment's date
  cannot be pinned to a fixture constant the way `w:ins`/`w:del`'s `w:date`
  can via raw OOXML manipulation. Verified with a live `quarto pandoc
  --track-changes=all --wrap=none` run against the fixture docx; the
  fixture's unit-test PANDOC_MD constant in `tests/test_roundtrip.py` was
  updated to mirror this real syntax (the sanctioned exception to "don't edit
  the test to make it pass" — the fixture existed only to approximate
  pandoc's real output). Versions: quarto 1.9.38, pandoc 3.8.3, python-docx
  1.2.0.

- 2026-07-03 / A tracked-change span whose bracket content itself contains
  square brackets — e.g. a coauthor inserting a citation, which pandoc
  round-trips as `[cited work [@doe2020] supports this]{.insertion
  author="..." date="..."}` — is invisible to `roundtrip.SPAN_RE`: the
  regex's bracket-content class `[^\][]*` deliberately excludes nested
  brackets (allowing them naively would let a match run across unrelated
  bracket pairs elsewhere in the line). Under the original implementation
  such an edit vanished with no error and no worksheet row — a silent drop
  of a coauthor change, violating the tool's core S4 promise. Fix is a
  safety net, not a fancier regex (nested-bracket regexes trade one silent
  failure mode for subtler ones): after span parsing, `extract_changes`
  scans the markdown for every raw occurrence of `{.insertion` /
  `{.deletion` / `{.comment-start` that does not fall inside any
  regex-consumed span, and emits a `Change(kind="unparsed", author="?",
  old="", new="")` for each, with `context` = the plain-ified text
  preceding the marker (which ends with the unmatched span's own raw
  bracket text — the most useful thing a human can see).
  `write_worksheet` renders these rows with "PARSER COULD NOT EXTRACT THIS
  CHANGE — open the DOCX and review this location manually." and the
  worksheet header instructs that unparsed rows are not ignorable.
  `locate()` returns None for unparsed via an explicit kind guard — its
  context is non-empty, so the difflib path would otherwise produce a
  spurious line guess. The `Change.kind` contract now includes "unparsed".
  Regression test:
  `tests/test_roundtrip.py::test_unparsed_nested_bracket_span_surfaces_not_drops`.
  Versions: quarto 1.9.38, pandoc 3.8.3.

- 2026-07-04 / real-manuscript smoke test / three findings:
  (1) knitr engine boots WITHOUT the knitr/rmarkdown R packages only for
  chunk-less documents; the first real ```{r} chunk fails with "knitr package
  is not available". Cause: quarto's engine probe vs execution split. Fix:
  install.packages(c("knitr","rmarkdown")) once per R installation; also
  jsonlite if inline numbers read JSON artifacts. Versions: quarto 1.9.38,
  R 4.6.0.
  (2) knitr chunk-name labels (```{r fig-x}) are valid Quarto crossref
  targets but were missed by validate's LABEL_DEF_RE → false HARD failures.
  Fixed in mslib.py with regression test (47 suite).
  (3) roundtrip locate() cannot point into YAML front matter (title/abstract)
  by design — a coauthor edit inside the rendered abstract block gets located
  at the nearest BODY line instead. Worksheet dispositions should sanity-check
  whether the context sentence is actually the abstract. Documented in
  SKILL.md S4.

## Crossref floats hide their captions inside 1x1 wrapper tables (Quarto 1.10.18 / pandoc 3.10)

Every crossref-LABELED float (`![cap](f.png){#fig-x}`, kable with `tbl-cap` +
`tbl-` chunk label) renders to docx as a 1x1 borderless OUTER table; the image
or data table nests inside the cell, and the caption is a paragraph styled
plain **"Normal"** (not "Image Caption"/"Table Caption") inside that same cell,
with NBSPs in the lead ("Figure\xa01: ..."; SI prefixes get a second NBSP:
"Table S\xa01: ..."). Unlabeled floats keep the classic body-level
"Image Caption" paragraph. Consequences: (1) `doc.paragraphs` never sees
labeled-float captions — walk `doc.tables` cells too; (2) style-based caption
restyling misses them — match the text lead instead (see
`bold_caption_leads()` in render.py, which also normalizes the delimiter to
"Figure 1." and forces single spacing since the cell caption inherits Normal).

## Pandoc drops structured author affiliations from docx metadata

A Quarto `author:` list with nested `affiliations:` renders as bare
one-name-per-line "Author" paragraphs — affiliations, ORCID, corresponding
flags all silently vanish from the docx. `rebuild_title_block()` in render.py
re-reads the .qmd front matter (`read_front_matter()`) and rebuilds the
journal-style title block (superscript affiliation letters, * corresponding
marker, lettered affiliation lines, e-mail line) in post-processing.
Watch the YAML key spelling: `address` (a misspelled key is silently ignored
by yaml.safe_load and the line just loses its address).

## Pandoc DOCX opens in Word Compatibility Mode (and it breaks table/justification layout)

Pandoc writes NO `<w:compatSetting w:name="compatibilityMode">` into
word/settings.xml, so Word treats every render as a Word-2007-era file and opens
it in Compatibility Mode — where pct table widths and justification inside
fixed-layout table cells follow legacy rules. Fix: stamp
`compatibilityMode w:val="15"` into settings.xml (render.py `patch_theme_fonts`
does this in its zip pass).

## Pandoc hard-codes table grids to the reference doc's Letter text width

Every `w:tblGrid` is emitted for the reference doc's 6.5in/Letter text column
(7920 dxa in our case). On an A4/25mm page (9072 dxa) all tables — including the
crossref float wrappers that hold captions — stop ~2 cm short of the right
margin, so justified captions LOOK left-aligned and narrow tables never fill the
column. Fix: rescale every gridCol + tcW proportionally to the actual section
text width (render.py `_tbl_rescale_grid`, applied recursively to nested tables
with cell margins subtracted).

## Quarto 1.10 emits DUPLICATE <w:pPr> on float-caption paragraphs — python-docx edits the wrong one

Crossref float captions (inside the 1x1 wrapper tables) carry TWO <w:pPr>
children: an empty-ish first one and a second holding the real properties
(pStyle=ImageCaption, jc=left, spacing). Invalid OOXML. python-docx's
get_or_add_pPr finds and edits the FIRST; Word honors the LAST — so alignment,
spacing, and style set through python-docx silently never render (captions
stayed left-aligned through two "fixes"). Diagnose by dumping the raw w:p XML,
not via python-docx (p.alignment reads the first pPr and happily reports your
own edit back to you). Fix: merge duplicates before any restyling —
render.py `dedupe_ppr()` (later-wins per property, pStyle reordered first).

## Word silently discards pPr children that violate the CT_PPr sequence

Follow-up to the duplicate-pPr quirk: after merging pPr blocks (or any raw
lxml append), the child order can end up e.g. (pStyle, jc, spacing). CT_PPr
(ECMA-376 §17.3.1.26) requires spacing BEFORE jc — and Word does not repair,
it silently ignores the out-of-position property, so a perfectly-present
`<w:jc w:val="both"/>` renders as left-aligned. python-docx's own setters are
schema-aware, but they find-and-edit an existing element IN PLACE, so they
never fix an element that is already mispositioned. Fix: sort every pPr's
children into the canonical sequence as the FINAL post-processing pass
(render.py `normalize_ppr_order()`). Verify with raw XML, not python-docx.
