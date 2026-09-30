# T-0023: Nature-family word counting

The previous checker always counted YAML abstracts, Methods and captions. A
regression through `run_checks` reproduced false HARD failures at all four
research-type boundaries: the body was exactly at the limit, but excluded
material added 22 words. Adding one main-text word must still fail after the fix.

## Sources checked on 2026-09-30

- [Nature Water content types](https://www.nature.com/natwater/content): Article
  and Analysis exclude abstracts, Methods, references and figure legends.
  Review and Perspective exclude abstracts, references, both caption kinds and
  boxes. Their rules do not authorize dropping Methods, so those words remain.
- [npj Clean Water content types](https://www.nature.com/npjcleanwater/content-types):
  Brief Communication has the four research exclusions. Its other limited
  formats specify a Main text count separately from abstract and back matter.
- [npj Biofilms and Microbiomes content types](https://www.nature.com/npjbiofilms/content-types):
  the same distinction applies, including this journal's Meeting Report type.

The prose rules and numeric limits are unchanged. Only the counting policies
were verified in this task; the profiles' broader `verified_date` values were
not advanced. Nature Water Comment/Correspondence/Matters Arising and unlimited
npj types retain their existing policy rather than inheriting exclusions from
another manuscript type.

## Implementation and scope

Each affected manuscript type carries an optional `word_count` mapping.
The default still counts the abstract and both caption kinds. Excluded
sections respect heading rank, code fences, numbering, emphasis and attributes.
Abstracts in YAML or a body section are supported, as are inline/chunk/figure-div
captions, labelled or pipe-table-adjacent table captions, and explicit boxes.

This remains a source estimate, not a rendered-text count. Complex table syntax,
raw HTML/LaTeX and dynamically generated prose still need manual checking.
Reference-inclusive counting is still T-0003. All non-counting checks inspect
the full manuscript, including excluded sections and captions.

The schema is checked both by `profile verify` and when the manuscript type is
selected; malformed policies produce an actionable ConfigError. Public-interface
tests cover exact-limit/over-limit behavior, type differences, Markdown boundaries,
invalid local policies, and a submission render that preserves existing outputs
when an extra main-text word exceeds the limit.

## Verification

- `uv run pytest -q`: 446 passed, 3 OS-specific skips.
- Ruff, wheel/sdist build, CLI version smoke and offline verification of ES&T
  and the three affected profiles passed.
- Fresh v0.3.0 baseline (`96c386e`) and candidate renders in a scratch copy of
  the private reference manuscript: all 95 parts across four documents are
  byte-identical, including document.xml, styles.xml and settings.xml. The
  allowlist is empty. Logs are in `/private/tmp/wongo-t0023-{baseline,candidate}.log`.
- No release version or published v0.3.0 asset was changed.
