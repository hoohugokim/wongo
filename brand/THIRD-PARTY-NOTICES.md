# Third-party notices

The offline [workflow brief](examples/workflow-brief.html) includes runtime
assets generated or copied by Quarto 1.10.18. Preserve this file, the
[vendor license texts](vendor-licenses/), and the existing notices in the assets
when redistributing the complete brand kit. The approved Wongo artwork is
separate from these upstream components.

| Component | Version | Included assets or bundle | License text |
|:--|:--|:--|:--|
| Quarto HTML runtime | 1.10.18 | `quarto.js`, `tabsets/tabsets.js`, generated HTML/CSS runtime | [MIT — Posit](vendor-licenses/quarto-1.10.18-MIT.txt) |
| Bootstrap | 5.3.1 | `bootstrap/bootstrap.min.js` and compiled Bootstrap CSS | [MIT — Bootstrap Authors](vendor-licenses/bootstrap-5.3.1-MIT.txt) |
| Bootstrap Icons | 1.13.1 | `bootstrap/bootstrap-icons.css` and `.woff` | [MIT — Bootstrap Authors](vendor-licenses/bootstrap-icons-1.13.1-MIT.txt) |
| Popper | 2.11.7; 2.11.8 | Standalone `popper.min.js`; embedded in the Bootstrap bundle, respectively | [MIT — Federico Zivolo](vendor-licenses/popper-2.11.7-2.11.8-MIT.txt) |
| Tippy.js | 6.3.7 | `tippy.umd.min.js` and `tippy.css` | [MIT — atomiks](vendor-licenses/tippy-6.3.7-MIT.txt) |
| Clipboard.js | 2.0.11 | `clipboard/clipboard.min.js` | [MIT — Zeno Rocha](vendor-licenses/clipboard-2.0.11-MIT.txt) |
| good-listener | 1.2.2 | Embedded in Clipboard | [Notice](vendor-licenses/good-listener-1.2.2-NOTICE.txt); [Zeno Rocha MIT text](vendor-licenses/clipboard-2.0.11-MIT.txt) |
| delegate | 3.2.0 | Embedded in Clipboard through good-listener | [Notice](vendor-licenses/delegate-3.2.0-NOTICE.txt); [Zeno Rocha MIT text](vendor-licenses/clipboard-2.0.11-MIT.txt) |
| select | 1.1.2 | Embedded in Clipboard | [Notice](vendor-licenses/select-1.1.2-NOTICE.txt); [Zeno Rocha MIT text](vendor-licenses/clipboard-2.0.11-MIT.txt) |
| tiny-emitter | 2.1.0 | Embedded in Clipboard | [MIT — Scott Corgan](vendor-licenses/tiny-emitter-2.1.0-MIT.txt) |

Asset paths in the table are relative to
`examples/workflow-brief_files/libs/`. The vendored font files, including the
copies in this directory, retain their separate
[Open Font Licenses](fonts/licenses/) and [font provenance](fonts/provenance.json).

## Sources and verification

Verified on **2026-10-02**. [Runtime provenance](vendor-licenses/provenance.json)
records the versioned upstream sources, package members, identification evidence,
and SHA-256 hashes of every license and notice file. Full license texts are
copied without modification.

The distributed Bootstrap and Clipboard JavaScript files match their tagged
upstream bundles byte-for-byte. Their release lockfiles identify the embedded
dependencies listed above. Both Popper releases have identical license texts.
Tippy's CSS matches its 6.3.7 package byte-for-byte; its JavaScript matches after
removing the upstream source-map directive and trimming surrounding whitespace.
The Quarto license matches the installed 1.10.18 distribution's `share/COPYING.md`.

Bootstrap, Bootstrap Icons, standalone Popper and Clipboard retain abbreviated
license headers, which do not contain the full permission notice. Tippy and the
Quarto JavaScript files do not embed a full MIT notice either. The complete
license texts are therefore included alongside the kit. The three small Zeno
Rocha packages distribute a README license link and attribution instead of a
separate license file; those exact notice sections are retained alongside the
full Zeno Rocha MIT text distributed with Clipboard.
