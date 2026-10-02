# Wongo identity integration — 2026-10-02

The maintainer requested the approved design system under `brand/` be applied
to the repository, including the README, alongside publication of the AIX audit
revision. Identity v1.0.0 was prepared in the separate emblem-design chat and
adopted here without changing the approved artwork.

## Application

- README: light/dark bilingual lockup, concise workflow overview, documentation
  navigation, explicit v0.3.0 release versus v0.3.1 development status, brand links.
- New documentation hub, branded getting-started and Claude integration guides.
- Contributor instructions for canonical tokens, regeneration and opt-in styling.
- AIX presentation and recording guidance use Wongo's approved palette and type.
- Complete offline kit retained: SVG/PNG artwork, local licensed fonts, tokens,
  CSS, visual specimen, source and rendered Quarto workflow brief.
- The brief's worksheet status example now supplies its required worksheet path.
- Third-party notices cover the browser runtime bundled with the Quarto example;
  font licenses and pinned provenance remain with the kit.

No engine, journal profile, manuscript house style or reference DOCX was changed.
GitHub controls Markdown typography; those pages use the approved artwork and
reading hierarchy, while HTML/Quarto communications can apply the full type system.

## Verification

- `uv run <scratch-copy>/brand/build.py`: successful with declared pinned
  dependencies and local fonts; all **33** rebuilt SVG/PNG/CSS files exactly
  match the approved originals.
- `quarto render brand/examples/workflow-brief.qmd`: successful with Quarto
  1.10.18. Browser preview confirms bilingual fonts, logo, tables and commands.
- Browser inspection of the visual specimen and local README layout preview;
  the latter correctly selects the reverse logo for a dark background.
- Six font hashes match the pinned provenance; copied example fonts match the
  source font files. Palette values agree between tokens and `_brand.yml`.
- Local image, stylesheet, font and documentation references checked for existence.
- Package build confirms the runtime wheel does not include the brand bundle.
- `git diff --check` and Statutor ledger/staged checks pass. Brand attributes
  preserve upstream license line endings and exempt only generated/vendor
  files from whitespace checks; source documentation remains checked.

The separate AIX revision (`dece132`) was pushed to
`origin/feat/v0.3.1-review-patches` with explicit maintainer authorization. Its
engine verification remains recorded in
[aix-audit-revision-2026-10-02.md](aix-audit-revision-2026-10-02.md): 528 default
tests, two opt-in Quarto/MCP tests, four benchmark dimensions and 95-part parity.
Those checks were not rerun for this documentation-and-artwork-only change.

The user also authorized a follow-up to the existing KIST 행정 chat,
“AIX 성과공유회 제출 양식 파악”, after publication. The handoff should request
an updated 공모신청서 with the latest verified claims and Wongo identity, while
preserving the official form and leaving unmeasured outcomes explicit.
