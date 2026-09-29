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

## Tracked-diff run rebuilding corrupts rich paragraphs

2026-08-30 / A changed paragraph containing a `w:hyperlink` was corrupted by
the first `wongo diff` implementation: the linked word moved to the start of
the paragraph and also appeared again inside `w:ins`. Cause: `Paragraph.text`
includes hyperlink text in python-docx 1.2, but `_strip_runs()` removed only
direct `w:r`/`w:ins`/`w:del` children. The nested hyperlink element survived,
then the flattened paragraph text was appended again as new runs. The same
rebuild could silently drop fields, drawings, footnote references, tabs, or
breaks nested inside a run. Fix: only rebuild paragraphs whose children are
plain `w:pPr`/`w:r` and whose runs contain only `w:rPr`/`w:t`; changed rich
paragraphs are not rewritten, are counted as `rich_paragraphs_skipped`, and
the CLI directs the author to Word Compare. Verification: inspect raw
`word/document.xml` and assert the output retains exactly one `w:hyperlink`
with the original visible order and no duplicate `w:ins`/`w:del`; pinned by
`test_changed_hyperlink_paragraph_is_preserved_and_reported`. Versions:
python-docx 1.2.0.

## pandoc 3.10's default reference.docx has NO page size — styles without `page:` crashed the render

2026-09-19 / `wongo render` with `style: default` died in `fix_tables` with
`TypeError: int() argument must be ... not 'NoneType'` after quarto had
already written `output/main-*.docx`, leaving a half-processed deliverable.
Cause: the profile reference docs are generated from `quarto pandoc
--print-default-data-file reference.docx`, whose `w:sectPr` at pandoc 3.10
carries only `w:footnotePr` — no `w:pgSz`/`w:pgMar` (the 2026-07-03 entry
above recorded `pgSz/pgMar/cols/docGrid` at pandoc 3.8.3; that changed). The
rendered document inherits that sectPr, so `section.page_width` and the
margins are None unless a style's `page:` block sets them, and `kist-wcr`
always did, which is why the reference manuscript never hit it. Fix:
`fix_tables` computes the text width only when all three values exist;
otherwise it sets `tblW` pct and leaves pandoc's grid alone (Word applies its
locale default page size). Verification: `unzip -p main.docx
word/document.xml | grep -o '<w:sectPr.*</w:sectPr>'` on a `default`-style
render shows no `w:pgSz`; pinned by
`test_fix_tables_tolerates_reference_doc_without_page_size` and
`test_default_style_renders_without_page_geometry_and_keeps_reference_fonts`.
Versions: quarto 1.10.18, pandoc 3.10, python-docx 1.2.0.

## Quarto emits every crossref and linked citation as `w:hyperlink` — the v1 diff skipped almost every body paragraph

2026-09-19 / On a real render, `wongo diff` reported the only changed body
paragraph as "rich OOXML … run Word Compare" although it contained just a
crossref. Cause: Quarto writes `@fig-x` as `<w:hyperlink w:anchor="fig-x">`
(and `link-citations` the same way), and the 2026-08-30 fix treated any
`w:hyperlink` as unrebuildable. In a manuscript nearly every paragraph cites
or cross-references something, so the S6 tool covered almost nothing. Fix:
the diff now reads paragraphs as run segments that remember their `w:rPr`
AND their hyperlink container; changed paragraphs are rebuilt token by token
inside a shell copy of each hyperlink (attributes only), with `w:ins`/`w:del`
placed INSIDE the hyperlink (CT_Hyperlink accepts EG_PContent, which includes
run-level tracked changes). Deleted tokens adopt the container of the
preceding revised token so a link whose text changed is not split in two.
Hyperlinks copied from the ORIGINAL document (deleted paragraphs) are kept
only when anchor-only — an `r:id` would dangle in the revised package.
Verified: `quarto pandoc --track-changes=all` parses the result as
`[Figure [2]{.insertion …}[1]{.deletion …}](#fig-x)`, so `wongo roundtrip`
still re-extracts our own output. Fields, drawings, footnote references,
tabs, breaks, math, and pre-existing `w:ins`/`w:del` remain "rich" and are
reported. Same pass fixed two silent losses: (1) per-run formatting — the v1
rebuild copied the FIRST run's `w:rPr` onto every token, so one word edit
turned a paragraph containing an italic species name entirely italic
(`python-docx` `Run` has no rPr until formatted, so the italic run was the
first WITH an rPr); (2) `tables_differ` compared `doc.tables` cell text, but
Quarto nests data tables inside 1x1 wrappers and `_Cell.text` ignores nested
tables, so data-cell edits were never reported — now every `w:t` under every
`w:tbl` (recursive `body.iter`) is compared. Also revision ids now start above
the highest existing `w:id` instead of a fixed 9000. Pinned by
`test_changed_hyperlink_paragraph_is_tracked_with_link_preserved`,
`test_inserted_paragraph_with_internal_crossref_link_keeps_the_link`,
`test_word_edit_preserves_per_run_formatting_of_untouched_words`,
`test_nested_table_cell_change_is_reported`,
`test_revision_ids_do_not_collide_with_existing_tracked_changes`.
Versions: quarto 1.10.18, pandoc 3.10, python-docx 1.2.0, lxml 6.1.2.

## SI cover counted Quarto figure wrappers as tables

2026-09-19 / `docs/bugs/si-cover-table-count.md`: an SI with 14 figures and
11 tables printed "25 tables". Cause: `len(doc.tables)` counts the 1x1 float
wrapper of every figure. Fix: `wongo.engine.si_item_counts` classifies each
top-level table by its caption lead ("Figure S1" / "Table S1" — the semantic
identifier Quarto writes inside the wrapper cell), falling back to nested
table → table, drawing → figure; a multi-cell data table that merely
contains an image is a table, and unwrapped body-level pictures are
figures. Verification: count `w:tbl` children of `w:body` whose first cell
paragraph starts with "Table" vs "Figure" in raw `word/document.xml`; pinned
by `test_si_item_counts_exclude_figure_wrappers_but_keep_nested_and_image_tables`.
This changes `si-<target>/word/document.xml` (the cover line only) for the
reference manuscript — the file is already allowlisted in
`tools/bytecompare-allow.txt`; re-baseline after confirming the count.
Versions: quarto 1.10.18, pandoc 3.10.

## Correction to the 2026-07-03 sectPr and roundtrip entries: the named tests did not exist in this repo

2026-09-19 / Those entries cite `tests/test_render.py` and
`tests/test_roundtrip.py::test_unparsed_nested_bracket_span_surfaces_not_drops`
from the skill-era suite; neither was migrated into `wongo`. Recreated as
`tests/test_sectpr_order.py` and `tests/test_roundtrip_parser.py`
(2026-09-19); the behaviors they pin were re-verified against the current
engine and hold.

## pandoc sorts rFonts attributes alphabetically when copying reference-doc styles

2026-09-19 / Regenerating the profile reference docs with theme-linked font
attributes stripped from the heading styles (T-0015: a `w:asciiTheme` on the
same `w:rFonts` outranks the literal `w:ascii`, so `default`-style headings
rendered in Aptos) changed the kist-wcr render's `word/styles.xml` although
every attribute VALUE was identical. Cause: pandoc re-serializes the reference
doc's styles part with attributes in alphabetical order, so the order
`set_fonts` inherits depends on which attributes the reference doc carried
(`ascii, cs, eastAsia, hAnsi` vs the historical `ascii, hAnsi, eastAsia, cs`).
Fix: `set_fonts` now rebuilds the four rFonts attributes in one canonical order
after stripping the theme links, making the output independent of the
reference doc's attribute order; verified by rendering the same project with
the HEAD and regenerated ES&T reference docs — `main-*` and `si-*` are
byte-identical under kist-wcr. The builders also stop using `doc.styles[name]`
(deprecated style-id fallback, see the 2026-07-03 entry). Pinned by
`tests/test_reference_docs.py` and
`test_set_fonts_emits_rfonts_attributes_in_canonical_order`. Versions: quarto
1.10.18, pandoc 3.10, python-docx 1.2.0.

## Collab renders wrote `<w:trackChanges/>`, which is not an OOXML element — Track Changes never switched on

2026-09-25 / The collab target was meant to open with Track Changes already on,
so every coauthor edit is captured. `patch_document_package()` planted
`<w:trackChanges/>` in word/settings.xml. CT_Settings (ECMA-376 §17.15.1) has
no such element; the setting is `<w:trackRevisions/>` (python-docx's own
CT_Settings child sequence lists only trackRevisions, and every Word-saved file
in the reference project with tracking on carries `<w:trackRevisions/>`). An
element outside the schema cannot switch the setting on, so coauthors most
likely opened collab files with tracking off unless they turned it on
themselves (Word automation could not read back an old-style file in this
session; this part rests on the schema). Fix: write
`<w:trackRevisions/>` before its first schema successor present (the full
successor list is spelled out in docxpatch; pandoc output has doNotTrackMoves).
Verification: raw settings.xml of a collab render contains `<w:trackRevisions/>`
before `<w:defaultTabStop`, a submission render contains neither element, and
Microsoft Word for Mac (AppleScript `track revisions of active document`)
reports `true` for a collab render of `wongo scaffold --example`. Pinned by
`test_track_changes_collab_only` and
`test_collab_opens_with_track_changes_on_and_submission_does_not`. This changes
collab `word/settings.xml` bytes for the reference manuscript (allowlisted with
this justification). Versions: quarto 1.10.18, pandoc 3.10, python-docx 1.2.0,
Word for Mac 16.x.

## Word locks open DOCX files on Windows; renders now replace outputs as one unit

2026-09-25 / Re-rendering while `output/main-collab.docx` is open in Word on
Windows fails: Word opens documents without FILE_SHARE_DELETE, so renaming or
replacing the file raises PermissionError [WinError 32]. The old pipeline also
wrote Quarto's raw output straight into output/ and post-processed it in place,
and finished main before rendering SI, so any failure after Quarto (including
this lock) left a half-processed deliverable. Fix: Quarto renders under a
`.wongo-stage-<name>` file name, post-processing happens in
`output/.stage-<target>/`, and `promote()` first renames every existing output
to a backup (the step Word's lock refuses, reported as "<name> is open in
another program (probably Word)"), restores all backups on any failure, then
moves the staged files in. Verified with real Quarto that the `--output` name
does not change any compared part (word/*, [Content_Types].xml, _rels/.rels),
and that Quarto accepts a dot-prefixed output name. The reference project's
post-render hook finds its files through `QUARTO_PROJECT_OUTPUT_FILES`, so the
staging name does not affect it. Pinned by the tests in
`tests/test_render_pipeline.py` (failed SI render, post-processing crash,
locked output, crashed-run leftovers). Versions: quarto 1.10.18, Windows 10/11.

## Korean Windows: CP949 decoding of pandoc output, BOM-prefixed sources, and redirected output

2026-09-25 / Three encoding failures, reproduced on macOS under
`LC_ALL=ko_KR.CP949 PYTHONUTF8=0` (the code page Korean Windows uses):
(1) `wongo roundtrip` decoded `quarto pandoc` output with the locale encoding
(`text=True` without `encoding=`); pandoc always writes UTF-8, so Hangul crashed
with UnicodeDecodeError and Latin-1 symbols silently turned into Hangul
mojibake (°C became 째C). Fix: decode with `encoding="utf-8"`. (2) Older Windows
Notepad saves UTF-8 with a byte-order mark; read with `utf-8` the BOM stays in
the text, so the front-matter regex (`\A---`) and the first BibTeX key no
longer match (abstract uncounted, title block not rebuilt, first citekey
"missing"). Fix: every source is read through `wongo.textio.read_text`
(`utf-8-sig`), which also turns a non-UTF-8 file into an actionable error.
(3) Redirected stdout falls back to the locale code page, which cannot encode
the em-dash in wongo's reports. Fix: `configure_stdio()` switches non-UTF-8
streams to UTF-8 (or makes an explicit PYTHONIOENCODING lossy instead of
fatal). Pinned by `test_roundtrip_and_report_work_under_a_korean_legacy_locale`,
`test_bom_and_crlf_sources_parse_like_plain_utf8`,
`test_non_utf8_source_is_an_actionable_error`, and
`test_reports_survive_a_non_utf8_output_encoding`. Versions: Python 3.11-3.13.

## `editor: markdown: wrap: sentence` does not change render output

2026-09-25 / The scaffold now sets this `_quarto.yml` key so visual editors keep
one sentence per line. Verified with real Quarto that renders with and without
it are identical in every compared part. Versions: quarto 1.10.18.

## Quarto on Windows cannot render in a folder outside the system code page

2026-09-25 / Windows CI: rendering `wongo scaffold --example` inside a folder
named "원고 예제" failed in Quarto's own filter with `recoverEncode: invalid
argument (cannot encode character '\50896')` from `convert_from_utf8`, called
by `io.open` in `writeFullIndex` (quarto share/filters/main.lua). Cause: on
Windows (`pandoc.system.os == "mingw32"`) Quarto's Lua layer converts file
paths from UTF-8 to the ANSI code page before opening them; GitHub's Windows
runners use cp1252, which has no Hangul. Korean Windows uses cp949, which does,
and the system-wide "Beta: Use Unicode UTF-8" option (code page 65001) avoids it
entirely. wongo cannot fix Quarto, so `toolchain.unrenderable_path_reason()`
checks the project path against `locale.getencoding()` before Quarto runs:
`wongo render` stops with the fix (rename or move the folder, or enable the
UTF-8 option) and `wongo doctor` reports a HARD `project-path` finding. The
Windows e2e job asserts both. Also from the same runs: Posit's binary R
mirror must not be overridden with `repos=` on Linux CI, or rmarkdown's
dependency `fs` compiles from source and fails without libuv headers.
Versions: quarto 1.10.18, Windows Server 2022 runner (cp1252).
