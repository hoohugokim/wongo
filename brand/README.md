# Wongo design system

Version **1.0.0** · Direction C approved **2026-10-02**

Wongo's identity pairs an abstract manuscript grid with a serif wordmark. The
grid recalls a journal page: a heading, text blocks, a figure and its captions.
Heavier rules and shortened endings make the symbol recognizable at a glance.
The small warm annotation is a restrained nod to the project's KIST context;
the identity belongs to Wongo and does not imply KIST endorsement.

Use this system for Wongo's software, documentation, website, presentations and
project communications. Apply it explicitly where useful. Journal manuscripts
continue to use their journal profile and selected manuscript style; this folder
does not override Wongo's DOCX engine or reference documents.

## Start here

- Open [design-system.html](design-system.html) for the visual specimen and usage
  examples.
- Use [logos/wongo-lockup.svg](logos/wongo-lockup.svg) as the default bilingual
  logo, or [logos/wongo-lockup-en.svg](logos/wongo-lockup-en.svg) for English-only
  use.
- Use [logos/wongo-icon.svg](logos/wongo-icon.svg) when the name already appears
  nearby, and the square PNG exports for favicons or app icons.
- Load [wongo.css](wongo.css) for a plain HTML application, or
  [_brand.yml](_brand.yml) for a Quarto document.
- Read [tokens.json](tokens.json) for machine-readable design values.

Copy the **entire `brand/` folder** when reusing the system in another project.
Its stylesheet, Quarto configuration, fonts and examples use relative paths.
SVG logos are self-contained and can also be copied individually: their lettering
is outlined, so displaying a logo requires no installed font.

## Logo assets

| Asset stem | Use |
|:--|:--|
| `wongo-lockup` | Emblem + lowercase serif `wongo` + Korean `원고`; default |
| `wongo-lockup-en` | Emblem + lowercase serif `wongo`; English-only |
| `wongo-icon` | Emblem only; compact navigation, app identity, repeated branding |
| `wongo-wordmark` | Serif `wongo` alone; when a separate emblem is unnecessary |

Each stem has a color SVG, a black `-mono.svg` and a white `-reverse.svg` in
`logos/`. Choose black for one-color printing and white for dark backgrounds.
Transparent PNG counterparts are supplied alongside the SVGs in `logos/` for
applications that do not accept SVG. Square app exports are named
`exports/wongo-icon-{size}.png`, with sizes
16, 32, 48, 180, 192 and 512 pixels.

Prefer SVG for documents, slides and the web. Preserve the artwork's aspect
ratio and internal spacing. Do not reconstruct the wordmark with live text,
rotate the emblem, round its corners, rearrange its blocks or add gradients,
shadows, outlines or a surrounding badge. Use the supplied reverse artwork on
a dark background rather than recoloring individual pieces.

The icon's construction area is **192 × 150 units**. Its annotation square is
20 × 20 units; use this length as the clear-space unit **u**. Keep at least
**1u** around the artwork and prefer **2u** when space allows. The regular
SVGs include the minimum clear space in their canvas; preserve it when placing
or exporting them. Scale the clear space proportionally with the logo.

For normal use, display the emblem at least **24 px wide** and preferably
**32 px or more**; in print, use at least **6 mm**. Use an English lockup at
**160 px or wider**, and a bilingual lockup at **220 px or wider**. These are
working minimums: check the actual output at its final size. The 16 px favicon
is a constrained exception; use the emblem without lettering at that size.
Minimum widths refer to visible artwork, excluding padding. For example, the
regular icon SVG needs a displayed width of about 29 px for 24 px of artwork,
or 39 px for 32 px of artwork. Square export sizes include their padding.

## Color

| Token | Hex | Role |
|:--|:--|:--|
| Ink | `#21313D` | Primary text, manuscript rules, wordmark |
| Petrol | `#416C78` | Figure panel, links, primary controls |
| Annotation | `#C56852` | Small warm accent and selected emphasis |
| Paper | `#FFFFFF` | Main background |
| Surface | `#F3F5F5` | Quiet panels and code backgrounds |
| Muted | `#52636D` | Secondary text and captions |
| Rule | `#CCD5D9` | Decorative dividers and light table rules |
| Success | `#3B705C` | Positive status, accompanied by a label |
| Warning | `#8A651D` | Review or attention status, accompanied by a label |
| Danger | `#A0413C` | Error or required action, accompanied by a label |

Let white space and ink carry the layout. Use petrol as the principal color
and annotation sparingly. Keep the warm square's color distinct from error
semantics: a brand accent is not a warning or failure message.

Ink on white has a contrast ratio of approximately **13.36:1**, and petrol on
white **5.77:1**. Annotation on white is approximately **3.83:1**, so it is not
for small text. Use ink or another verified text color for labels. Light rule
color is for decorative separators, not the sole boundary of a control.
Recheck contrast when changing backgrounds, opacity or color combinations.

## Typography

| Role | Family | Default treatment |
|:--|:--|:--|
| Brand wordmark | Source Serif 4 | Outlined weight 500, optical size 60 |
| Document headings | Source Serif 4 | Weight 600, line height 1.2 |
| Body and interface | Source Sans 3 | Weight 400; weight 600 for emphasis |
| Korean text | Noto Sans KR | Weight 400 or 600 |
| Code and commands | Source Code Pro | Weight 400 |

The production wordmark is a reproducible typographic interpretation of the
approved image, not a claim that the image used an identifiable font. Use the
supplied outlined artwork for logo applications; live fonts are for surrounding
content. The archived approval image is in
[reference/approved-c.png](reference/approved-c.png).

Use sentence case, a clear heading hierarchy and compact captions. Body text
defaults to **1.0625rem** with a **1.6** line height; code is slightly smaller.
Use `Wongo` in prose, lowercase `wongo` for the logo and command, and `원고`
for the Korean name. Keep Korean text in its own font rather than relying on
an accidental system fallback.

Bundled variable WOFF2 files allow local rendering without fetching web fonts.
Their Open Font Licenses are under [fonts/licenses/](fonts/licenses/), and
[fonts/provenance.json](fonts/provenance.json) records the pinned source URLs,
font versions and SHA-256 hashes. Retain the license files when redistributing
the fonts. The upstream families are
[Source Serif](https://github.com/adobe-fonts/source-serif),
[Source Sans](https://github.com/adobe-fonts/source-sans),
[Source Code Pro](https://github.com/adobe-fonts/source-code-pro) and
[Noto CJK](https://github.com/notofonts/noto-cjk); the bundled source files were
retrieved from a pinned [Google Fonts](https://github.com/google/fonts) revision.

## Layout, figures and interaction

Use a deliberate manuscript hierarchy: a strong heading, an ordered reading
column, aligned figure panels and closely associated captions. Prefer square
corners, flat fills, thin dividers and generous space to decorative containers.
Align content to shared edges and let related information stay together.

Use the **4 px** spacing unit and the supplied scale: **4, 8, 12, 16, 24, 32,
48, 64 and 96 px**. Reading text has a default maximum width of **68ch**;
wider page compositions use a **1120 px** maximum width and **32 px** gutters.
Adapt the layout to narrow viewports while retaining readable type and spacing.

Scientific figures should lead with the data. Use restrained axes, direct
labels where practical, consistent panel lettering and readable units. Petrol
can carry a primary series; use the annotation color for a specific highlighted
comparison. For additional groups, select a suitable data palette and verify
its legibility rather than adding arbitrary brand colors. Distinguish series
with labels, line styles or markers as well as color. Keep the logo outside the
data area.

Links are underlined. Keyboard focus must remain visible; the default uses a
petrol outline with an offset. Status messages use explicit words such as
“Pass”, “Review” or “Action required”, with text explaining the next step.
Never communicate status through color alone. Give a standalone logo meaningful
alt text such as `Wongo`; use empty alt text when an adjacent label already
provides the same name. Keep informative figure descriptions separate from
branding.

## Quarto and HTML

For a Quarto HTML document in a project containing the copied folder, opt in
through its front matter:

```yaml
brand: brand/_brand.yml
format:
  html:
    theme: [default, brand]
```

Use the bundled [workflow brief](examples/workflow-brief.qmd) as a complete
example. Its paths are relative to the example's own location. Render it from
the repository root:

```fish
quarto render brand/examples/workflow-brief.qmd
```

The example targets HTML and demonstrates bilingual type, the lockup,
manuscript hierarchy, statuses and code. The rendered HTML and its adjacent
`workflow-brief_files/` dependencies work offline with the complete `brand/`
folder. Retain the [third-party runtime notices](THIRD-PARTY-NOTICES.md) and
their linked license files when redistributing the kit.
Quarto 1.10.18 rendering and browser checks at 1440 px and 390 px were
verified; this kit does not claim verified Typst or PDF font integration. Quarto's
brand configuration is an explicit document choice; it does not apply these
fonts or colors to journal DOCX output automatically. For plain HTML, link to
`brand/wongo.css`, retain its adjacent `fonts/` directory and apply the opt-in
`wongo` class to the containing surface:

```html
<link rel="stylesheet" href="brand/wongo.css">
<main class="wongo">
  <img src="brand/logos/wongo-lockup.svg" width="240" alt="Wongo">
  <h1>A connected manuscript workflow</h1>
  <p>Write, check and review your manuscript.</p>
</main>
```

## Rebuilding and maintaining the kit

[tokens.json](tokens.json), [components.css](components.css) and
[build.py](build.py) hold the design values, component rules and deterministic
artwork construction. Regenerate the vector assets, CSS and PNG
exports from the repository root:

```fish
uv run brand/build.py
```

The build uses fontTools and HarfBuzz for outlined lettering, and
`rsvg-convert` for PNG rasterization. `uv` resolves the script's declared Python
dependencies. To rebuild only SVG and CSS without `rsvg-convert`, add
`--svg-only`. Keep the approved reference as an archival
record. Change production values in their sources, regenerate the assets and
inspect the specimen, monochrome/reverse variants and smallest exports before
adopting a revision. Keep `_brand.yml` synchronized with the palette and type
system. Record subsequent identity changes here with a new version and date.
