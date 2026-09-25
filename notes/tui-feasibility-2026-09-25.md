# TUI feasibility and value assessment — wongo — 2026-09-25

Question: should wongo become a full-fledged terminal UI (TUI) application,
still GUI-less, so that non-technical lab members can use it?

Method: a 34-agent workflow (run `wf_82cc068f-3a3`). Six independent
investigators (engine architecture, user journeys, TUI frameworks, install
friction, alternatives, devil's advocate), three competing plans, three judges
(maintainer, non-technical postdoc, research-software engineer), one synthesis,
two refuters per load-bearing claim (repository lens and external-source lens),
and a completeness critic. The orchestrator re-checked the two most serious
findings by hand. Nothing in the repository code was changed.

## 1. Verdict

A full TUI is **feasible but not worth building now**, and it would not make
wongo usable by non-technical people on its own.

- **Feasible:** the engine can sit under a TUI after a bounded refactor, and
  Textual provides every widget needed.
- **Low value now:** the hard parts of wongo lie where no screen reaches:
  installing Quarto, R and knitr; writing `.qmd` with inline R for every number;
  and the judgment in S4. Word-native coauthors never run wongo. The lead author
  is already served by the Claude skill, which also does judgment work a screen
  cannot.
- **Recommended instead:** fix four engine and tooling defects found during the
  analysis, harden installation, then build an S4 review loop only when a real
  labmate and a real coauthor round exist. A full-screen TUI stays an option
  gated on pilot evidence.

All three judges independently chose this "seam first, screen last" plan.

## 2. Feasibility

### Engine readiness (confirmed by both refuters)

The render output code (docxpatch, styles, the zip pass) is well isolated and
would not change. The orchestration around it is written only for a terminal:

| Seam | Today | Why it blocks a TUI |
|---|---|---|
| Errors | 20 `raise SystemExit` sites across 7 modules | In a worker thread it is silently lost; under asyncio it escapes `except Exception` and kills the event loop (probe reproduced both) |
| Results | 40 `print()` calls; `render_project` returns 0 and prints paths | A UI cannot learn what was written without re-deriving paths |
| Quarto | `subprocess.run` with inherited stdio, no progress, no cancel | Output would draw over a full-screen UI; nothing to show progress with |
| Transactions | raw DOCX lands in `output/` before post-processing; main finishes before SI renders | A failure or a Cancel button leaves a partial deliverable |

Estimated refactor: roughly 500–700 changed source lines plus about 200 test
lines, touching orchestration only. The byte pin stays checkable because the
harness drives the CLI end to end. All effort figures in this report are
unvalidated estimates, not measured velocity.

### Framework landscape (as of 2026-09-25)

- **Textual 8.2.8** (MIT, 2026-06-30) is the most feature-rich option: tables,
  logs, Markdown viewer, directory tree, background workers, headless Pilot and
  snapshot tests. It adds 8 packages and about 11 MiB, so it belongs in an
  optional extra.
- **Correction from verification:** Textual is not the only mature choice.
  urwid 4.1.7 (released 2026-09-23) and prompt_toolkit 3.0.53 are mature and
  maintained, and questionary builds on prompt_toolkit.
- **Textual risks:** no upstream commits or pushes since 2026-07-11, effectively
  one maintainer after Textualize wound down in 2025, 8 major versions in 14
  months, open Windows Korean-IME bugs with unmerged fix PRs, single-letter
  shortcuts that do not fire while the Korean IME is on, and no screen-reader
  support.
- **No auto-generation:** Trogon supports only Click and Typer, and
  argparse-tui needs Textual below 1.0. Every screen would be hand-written.

### Platform and language

- Korean input in any raw-mode TUI is fragile; bindings must avoid letter keys.
- macOS Terminal.app renders TUIs poorly; Windows 10 still defaults to the old
  console.
- Independently of any TUI, `wongo roundtrip` crashes with UnicodeDecodeError
  on a Hangul DOCX under a CP949 locale (Korean Windows), and silently turns
  °C into 째C. Reproduced.

## 3. Value by user group

| Group | What a full TUI gives them |
|---|---|
| Word-native coauthors | Nothing directly: they never run wongo. They would gain from the Track Changes fix in section 5 instead. |
| Lead author (you) | Little, and some loss: the Claude skill already offers a natural-language front end, proposes S4 dispositions with rationale, and runs project scripts wongo does not know. A TUI cannot be driven by the agent or CI. |
| Future labmates leading a manuscript | Some. A rough, low-confidence estimate is that a TUI removes about 10% of a newcomer's difficulty; setup is about 15% and S2 authoring about 55–60%, neither of which a TUI touches. None exists today. |
| The PI (`needs-PI` rows) | Not examined by the investigators; open question. |

The reference manuscript carries 628 inline `r` expressions (235 in the main
text, 393 in the SI) and 23 R chunks. That is the scale of S2 authoring a
non-technical author would face regardless of the interface.

## 4. Where interactive surfaces would pay off, ranked

1. **S4 disposition review** (high). The one genuinely interactive, many-item
   job, like Word's accept/reject pane. Needs a worksheet parser and validator
   first. A standard-library prompt loop captures most of the value. Demand is
   unproven so far.
2. **Doctor / setup check** (high). The value is in the checks, deliverable as
   a CLI command.
3. **Render with a pinned HARD/WARN summary** (medium). A summary line at the end
   of CLI output gets most of it; live progress needs streaming inside the
   byte-pinned path.
4. **Read-only project status** (medium). A `wongo status` card does most of it.
5. **New-manuscript wizard** (medium). TTY-gated prompts close the gap.
6. **Submit checklist, diff review, profile verify** (low).

## 5. Defects found along the way (verified)

These matter more than the TUI question. Recorded as T-0017 to T-0020.

1. **The byte-compare harness renders into the live reference project.** Since
   `a02eac4` (2026-08-25), `prepare_project()` copies the reference repo to
   scratch but returns the live `manuscript/` path. Running T-0002 as written
   would overwrite the reference project's `output/*.docx`. The harness also
   compares any `output/*.docx` that exists, so a pre-existing stale SI file can
   make a broken render pass, and it never clears old `candidate/` trees.
   **Fix before running T-0002.** (T-0017; HANDOFF now warns.)
2. **Collab DOCX does not validly turn on Track Changes.** The engine writes
   `<w:trackChanges/>`, which is not an OOXML settings element; the schema name
   is `<w:trackRevisions/>` (python-docx's own settings sequence lists only the
   latter). wongo's collab renders carry the invalid element; the Word-saved
   files in the reference repo carry `<w:trackRevisions/>`. The test suite pins
   the wrong string. Fixing it changes collab `settings.xml` bytes, so it needs
   an allowlist entry and a check in real Word. (T-0018)
3. **Renders are not all-or-nothing.** A failure after quarto leaves a
   half-processed `output/main-*.docx`, breaking the no-partial-deliverable
   rule. (T-0019)
4. **Environment failures surface as tracebacks.** Missing quarto gives a raw
   FileNotFoundError; roundtrip mis-decodes Korean-locale output. (T-0020)
5. Known already: the Water Research word count can show a false PASS because
   the limit includes references (T-0003). A friendlier UI would make that
   green check look more authoritative.
6. Minor: `diff.main` duplicates the CLI's diff report and its note text has
   already drifted from the CLI's; the CLI never calls it.

## 6. Recommended path

| Step | Deliverable | Effort (unvalidated) | Gate |
|---|---|---|---|
| 0 | Fix the harness (T-0017), then run T-0002 yourself and tag v0.2.0; interim T-0003 (HARD FAIL when body plus abstract alone exceeds the limit, else WARN "approximate, excludes references"); publish to PyPI | 3–5 pd | Clean byte compare; `uv tool install wongo` works on a clean Mac |
| 1 | Environment floor, no render-path edits: `wongo doctor [--json]`, quarto preflight with per-OS hints, UTF-8 in roundtrip and CLI output, macOS and Windows CI, TTY-gated scaffold prompts, `wongo status`, scaffold `.vscode/tasks.json`, install guide per OS | 7–9 pd | A labmate reaches an all-green doctor on a fresh Mac in 45 minutes or less |
| 2 | Headless seam: `WongoError` instead of SystemExit, result dataclasses, staged all-or-nothing renders, `--json` on every command, render summary line, output manifest; fix Track Changes (T-0018) in the same byte-compare batch | 10–15 pd, capped | Fault injection at each stage leaves `output/` unchanged; one clean byte compare you start |
| 3 | Only when a named labmate and a real coauthor round of 10+ rows are due within about 6 weeks: worksheet parser and validator, `wongo worksheet status|lint|set`, `wongo review` prompt loop (digit keys, save after each row, never writes `.qmd`) | 6–8 pd | Lossless parse/serialize round trip; lint blocks while rows are PENDING |
| 4 | Pilot with one labmate and one real round; log where time is lost | ~2 pd of your time | Continue only if 2+ labmates are committed and 40%+ of lost time is in wongo commands or S4 bookkeeping |
| 5 | Optional `wongo[tui]`: Korean-IME spike comparing Textual and prompt_toolkit first; then two screens (S4 review, read-only dashboard), Ctrl/F-key bindings only | 12–18 pd | Spike passes on the lab's terminals; pilot user is faster or makes fewer disposition errors |

Steps 0–2 pay off even if no TUI is ever built. A full six-stage TUI was
estimated at 50 person-days by its own plan and 70–120 realistically.

## 7. Alternatives considered

| Alternative | Verdict |
|---|---|
| Full six-stage Textual TUI | Reject for now: built for a user who does not exist yet, on a stalled framework |
| Claude skill as the non-technical front door | Adopt and document: the only option that helps with S2 authoring and S4 judgment. Costs a paid plan per user and sends manuscript text off the machine |
| TTY-gated guided prompts (stdlib, questionary as fallback) | Adopt: line-oriented prompts avoid most IME and screen-reader problems |
| Editor tasks (`.vscode/tasks.json` for Positron/VS Code) | Adopt now: steers users away from the editor's own Render button, which produces an ungated, unstyled DOCX |
| Browser delivery via textual-serve | Reject: no authentication, would expose an executor of manuscript R code, bends the no-GUI rule |
| Quarto extension or post-render hook hosting the pipeline | Reject: cannot do OOXML post-processing; non-idempotent steps would run twice |
| Single-file executable or justfile | Skip: bundles neither Quarto nor R; duplicates a six-command CLI |
| Toolchain pinning (pixi with quarto 1.10.x, r-base, knitr from conda-forge) | Evaluate in Step 1: would cover most setup difficulty and record the R/knitr versions behind the byte pin; conda-forge availability of 1.10.x unchecked |

## 8. Verification of load-bearing claims

| Claim | Result |
|---|---|
| SystemExit is unsafe in UI workers (20 error sites; probe) | Confirmed by both refuters |
| quarto stdio is inherited; missing quarto gives a raw traceback | Confirmed |
| Renders can leave a partial deliverable | Confirmed, reproduced |
| Only the WR false PASS and T-0002 block the milestone | Confirmed (plus T-0017 found afterwards) |
| The S4 worksheet is never read back | Contested: no code parses it, but the agent reads it by design and has applied rows |
| Most difficulty lies outside any screen; coauthors already get tracked collab files | Contested: the conclusion holds, but the Track Changes part is wrong (defect 2) and the inline-R count is 628, not 235 |
| Render orchestration has no tests | Contested: the top-level glue has none, but its parts are unit-tested |
| roundtrip crashes under CP949 on Hangul or an em-dash | Contested: Hangul crashes; em-dash does not (pandoc writes `---`); °C silently becomes 째C |
| Textual is the only mature Python TUI framework | Refuted: urwid and prompt_toolkit are mature and maintained |
| Textual must be an optional extra | Contested: sensible default, not a necessity; an extra adds an install step for exactly the target users |

## 9. Open questions for you

- How many labmates will lead a `.qmd` manuscript in the next 6 months, and can
  they write inline R? If S2 is their wall, stop at Step 2.
- Does anyone render on Windows? This sets the depth of Windows CI and the IME
  test matrix.
- Is the Claude skill acceptable as the front door under KIST data-security or
  network-separation rules, given that manuscript text leaves the machine?
- Would labmates render on an SSH-only lab server? That is the one case where a
  TUI clearly beats a GUI, and it was not examined.
- Do non-technical users need Korean-language messages and docs?
- When is the next real Word coauthor round? It is the earliest real S4 data.
- Who maintains a Textual front end if you are unavailable?
