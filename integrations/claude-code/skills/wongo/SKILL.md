---
name: wongo
description: >-
  Run the wongo manuscript pipeline for a researcher who talks to Claude instead
  of using a terminal: set up wongo, Quarto and R on Windows or macOS; start,
  write and check Quarto (.qmd) manuscripts; render journal-ready Word files for
  coauthors or for submission; bring coauthors' Word tracked changes and comments
  back through a merge worksheet the person approves; and prepare revisions. Use
  whenever the user mentions wongo, a manuscript or paper, .qmd or Quarto, Word or
  DOCX output, coauthor edits, tracked changes, reviewer comments, a journal
  submission or revision (ES&T, Water Research, npj Clean Water, Nature Water,
  Microbiome, Environmental Microbiome, npj Biofilms and Microbiomes),
  Supporting Information, or asks to set up or update wongo; also for Korean
  requests about 원고, 논문, 공저자 수정, 투고 or 심사 의견.
compatibility: Windows 10/11 or macOS 13+. Installs wongo with uv; renders need Quarto 1.10 and R 4.2+ with knitr and rmarkdown.
---

# wongo: the manuscript front door

The person you help may never have used a terminal. They talk; you run wongo,
read its JSON, and explain the result in plain words. The `.qmd` files are the
manuscript. The Word files in `output/` are disposable renders. Manuscript text
reaches Claude as part of this workflow; the lab (KIST) has approved that.

## Start every session here

1. In the manuscript folder run `wongo status --json` (from elsewhere add `--project <folder>`).
2. If `wongo` is not found, go to Setup below.
3. If `status.is_project` is false, look for subfolders that contain `_journal.yml`
   and ask which manuscript to open, or offer to start one (S1).
4. Tell the person in one or two sentences where the manuscript stands, from
   `status.next_reason`, and offer `status.next_command` as the next step.
   Run it only when they agree.

Keep explanations short. Name folders the way File Explorer or Finder shows
them. Show a command only when the person has to type it themselves.

## Read wongo's JSON, not its prose

Every command except `wongo review` accepts `--json` and then prints exactly one
object on stdout: `{"command", "wongo", "ok", ...}`. Quarto's progress goes to
stderr, so read stdout only.

- `ok: false` comes with `error.kind` and `error.message`. The message already
  says how to fix the problem: relay it plainly, do not retry blindly. Kinds:
  `toolchain` (Quarto or R missing or failing), `config` (`_journal.yml`, profile
  or style), `input` (a file or argument, including a YAML typo, which the
  message locates by file and line), `gate` (submission refused), `locked` (a
  file is open in Word), `output` (an output file could not be replaced, e.g. by
  a sync client), `usage` (a wrong command line; exit code 2), `interrupted`, and
  `internal`: a wongo bug. For `internal`, tell the person, and offer to draft an
  issue for https://github.com/hoohugokim/wongo/issues from `error.message` and
  `error.traceback`.
- Exit code 1 means failure. It also means: `doctor` found a HARD problem,
  `check --strict` found a HARD failure, or `worksheet lint` is not ready.
  Plain `wongo check` exits 0 even when a HARD check fails: read `ok`.
- `status` returns `ok: false` when the project configuration is broken;
  `status.config_error` says why, and the next step is `wongo doctor`. An empty
  `next_command` with a `next_reason` other than "everything is rendered and
  current" is a choice for the person, not a command: read it to them.

| Command | Fields that matter |
|---|---|
| `status` | all under `status`: `next_command`, `next_reason`, `is_project`, `config_error`, `quarto` (null = not found), `hard_failures`, `warnings`, `outputs.collab.state`, `outputs.submission.state`, `worksheet`, `worksheet_open` |
| `doctor`, `check` | `checks[]` with `name`, `level` (HARD or WARN), `ok`, `detail`, `locations[]` (`file:line: item`) |
| `render` | `outputs[]`, `hard_failures[]`, `warnings[]`, `quarto` (version); a refused render still carries `checks` |
| `roundtrip` | `worksheet`, `changes`, `kinds`, `unmatched`, `unparsed` |
| `worksheet status` | `counts`, `next`, `rows[]` with `row`, `kind`, `author`, `location`, `line`, `unmatched`, `old`, `new`, `context`, `state`, `proposal`, `decision`, `needs_decision`, `apply_blocker` (`—` in `old` or `new` means empty) |
| `worksheet lint` | `ok`, `errors`, `warnings`, `problems[]` |
| `profile show <slug>` | `profile` (verified requirements), `paths.skill`, `paths.checklist`, `paths.editorial` |

Output states: `missing` (never rendered), `unknown` (rendered before wongo kept
a manifest), `stale` (sources changed since the render), `fresh`, and
`modified`: a file in `output/` was saved over after the render. A render
replaces it, so first ask whether it holds coauthor edits; if it might, move it
into `from-coauthors/` before rendering.

## Setup: always ask first

Use this when `wongo` is not found, when `wongo doctor` reports a HARD problem,
or when the person asks to set up or update wongo. Commands per OS, detection,
full paths and fixes: [references/setup.md](references/setup.md).

- Never install, update or remove software without a clear yes for that item.
  Before each install say in one line what it is and why wongo needs it, show
  the command, and wait for the answer.
- Order: uv, wongo, Quarto 1.10, R (4.2 or newer), then the R packages knitr,
  rmarkdown and jsonlite. Skip whatever `wongo doctor` already shows as passing.
- Windows may ask "Do you want to allow this app to make changes to your
  device?"; the person clicks Yes. On macOS, installers that need the login
  password are run by the person (double-click the installer, or paste the
  command into their own Terminal window); you cannot type passwords.
- Programs installed during this session are not on your shell's PATH yet.
  Call them by full path as the reference shows. When setup is finished, ask the
  person to type `exit`, open a new terminal window, go back to the folder and
  start Claude again with `claude --continue`.
- Finish with `wongo doctor --json` and explain every failing check with its
  fix. Setup is done when `ok` is true (in text, the last line starts with
  `doctor: ready to render`).
- To update wongo later, ask, then run
  `uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip --reinstall`
  and confirm with `wongo --version`. Keep Quarto on 1.10.x: wongo's output is
  verified against 1.10.18.

## Route the request (S1-S6)

| Stage | The person says | You do |
|---|---|---|
| S1 Start | "new paper", "start a manuscript", "try wongo" | Trial: `wongo scaffold demo --example`, then inside `demo` run `wongo doctor` and `wongo render --target collab`. Real project: ask the journal (`wongo profile list --json`), the manuscript type (`wongo profile show <slug> --json`) and the house style (`wongo style list --json`: `kist-wcr` is the lab's look, `default` the journal template's), then `wongo scaffold <folder> --journal <slug> --ms-type <type> --style <name>`. Always pass all three: without a terminal wongo does not prompt. |
| S2 Write | write, edit, shorten, add a figure, table or number | Edit the `.qmd` under the house rules below; run `wongo check --json` after each round of edits and report failures with their `locations`. |
| S3 Render | "make the Word file", "send it to my coauthors" | `wongo check --json`, then `wongo render --target collab --json`. Say where `output/main-collab.docx` (and `output/si-collab.docx`) is and that it opens with Track Changes on. |
| S4 Coauthor edits | a coauthor's Word file with tracked changes or comments | The S4 protocol below. |
| S5 Submit | "submit", "checklist", "cover letter", "TOC graphic" | `wongo profile show <slug> --json`; read the files at `paths.checklist` and `paths.editorial`; `wongo check --strict --json`; TOC art at `figures/toc-art.png` (or .tif/.jpg) when the profile requires it; then `wongo render --target submission --json`. |
| S6 Revise | reviewer comments, response letter, marked-up copy | Build a response table (comment, response, change with its location); make the edits under the house rules; `wongo diff <submitted.docx> <revised.docx> -o <name>-tracked.docx`; tables and rich paragraphs it reports need Word Compare. Check the profile's `revision_rule` where it has one, and its journal notes. |

If the stage is unclear, ask one question. For new projects prefer
`C:/papers/<name>` on Windows and `~/papers/<name>` on macOS, outside OneDrive
and other synced folders. Folder names with English letters, digits, `-` and
`_` always work; Hangul names work on macOS and on Korean Windows, but Quarto
cannot render in a Hangul path on Windows set to another language
(`wongo doctor` shows a HARD `project-path` check). Windows accepts forward
slashes in every wongo command.

## House rules (non-negotiable)

1. One sentence per line in `.qmd` prose. Never reflow a paragraph; the Word
   round trip depends on it.
2. Numbers that come from analysis are inline R (`` `r ...` ``) computed from
   the data, never typed by hand. When a number must change, change the code or
   the data, re-render, and read the new value.
3. Cite only with `@citekey` from the project's bibliography (usually
   `refs.bib`). Never invent a reference, DOI or citekey. If a source is missing,
   ask the person to add it (for example from Zotero) and leave a visible TODO.
4. Cross-reference only with `@fig-`, `@tbl-`, `@sec-` (and `@eq-`) labels.
5. Never describe a figure or table you have not seen rendered. Render, then
   look at it: a DOCX is a zip archive, so extract `word/media/` into a
   temporary folder outside the project and view the images.
6. Journal requirements (word limits, abstract rules, sections, TOC art, SI)
   come only from `wongo profile show <slug> --json` and the files in its
   `paths`, never from memory. The journal notes there also guide framing and
   cover letters.
7. wongo never edits a `.qmd` from a worksheet. You apply only rows whose final
   disposition is `apply`, only after `wongo worksheet lint` passes, and never
   replace an inline R expression with a typed number (`fix-code` means change
   the R code, the data or `refs.bib` that produce the text).
8. A submission render must pass every HARD check; never work around a refused
   render. Collab renders are for internal eyes only.
9. The word count is wongo's approximation of the journal's rule, which the
   check's `detail` quotes. Read that rule before asking anyone to cut text:
   Water Research counts references (a WARN gives the headroom), and for the
   Nature-family profiles (natwater, npjcw, npjbiofilms) wongo currently counts
   sections those journals exclude, so a FAIL there can be false.

## S4: coauthor edits (summary)

Read [references/coauthor-review.md](references/coauthor-review.md) before the
first S4 of a session: it has the judgment rules, the chat script and the
editing rules.

1. Keep the coauthor's file outside `output/` (for example
   `from-coauthors/kim.docx`), then run `wongo roundtrip <file> --json` (add
   `--qmd si.qmd` for an SI file). Every row starts as `PENDING`. Run it once
   per file: a second run writes a new `-2` worksheet that `status` then shows.
2. Read `wongo worksheet status <worksheet> --json`. For each row open the
   `.qmd` at `line` and check that the text there matches `old` and `context`.
   The alignment is fuzzy and can be wrong; fix it with
   `wongo worksheet set <worksheet> <N> --location <line>`.
3. Propose every row that has no decision yet:
   `wongo worksheet set <worksheet> <N> 'PROPOSED <final> — <rationale>'`, where
   final is `apply`, `reject: <reason>`, `fix-code` or `needs-PI`. Use single
   quotes and keep backticks, dollar signs and apostrophes out of the rationale.
   wongo refuses a proposal over a decision already recorded; leave that row
   (`--force` only when the person asks to reopen it).
4. The person decides, in one of two ways:
   - they run `wongo review <worksheet>` in their own terminal window (digits;
     Enter accepts your proposal). You cannot run it for them: it refuses
     without a terminal.
   - you walk the rows with them in chat and set a final value only after their
     explicit answer for that row, e.g. `wongo worksheet set <worksheet> <N> apply`
     (keeps your rationale) or `'reject: <their reason>'`. A different decision
     keeps your proposal as `was PROPOSED ...`.
5. `wongo worksheet lint <worksheet> --json` must return `ok: true`. Until then
   do not touch the `.qmd`.
6. Apply only `apply` rows. Turn `fix-code` rows into code or data changes the
   person approves, list `needs-PI` rows for the PI, and change nothing for
   `reject` rows.
7. Run `wongo check --json`, then `wongo render --target collab --json`, and
   tell the person what changed and what still waits for them or the PI.

## When Word has the file open

A render stops with `error.kind` `locked` and a message such as
`main-collab.docx is open in another program (probably Word). Close it and render again; output/ was left unchanged.`
Tell the person:

- Nothing was lost or half-written: the previous Word files are unchanged.
- Close that document in Word (every window showing it); if Word still holds
  it, quit Word.
- If the project is in OneDrive, wait until syncing finishes or pause it.
- Then say "render again", and you rerun the same command.

Never delete or rename files in `output/` to get around the lock.

## Other common stops

| Message starts with | What to do |
|---|---|
| `Quarto was not found` | Setup: install Quarto 1.10 (ask first). |
| `Quarto on Windows cannot render inside a folder whose path has characters` | Move or rename the project folder to English letters, digits, `-` and `_` (e.g. `C:/papers/wetland-study`), or turn on "Beta: Use Unicode UTF-8 for worldwide language support" (Settings > Time & language > Language & region > Administrative language settings) and restart Windows. |
| `HARD checks failed — submission render refused` | Show each failing check with its `locations`, fix them, or render `collab` for coauthors instead. |
| `Profile requires TOC art` | The journal needs a TOC graphic at `figures/toc-art.png` (or .tif/.jpg). The person or a coauthor makes it; do not invent one for a real submission. |
| `R package ... is missing` | Setup: install the R packages (ask first). |
| `... is not UTF-8 text` | Re-save that file as UTF-8 (in VS Code: Save with Encoding > UTF-8). |
| `destination not empty` | Pick a new folder name for `wongo scaffold`. |
| `wongo review needs a person at a terminal` | Expected when you run it: use `wongo worksheet set`, or ask the person to run `wongo review` themselves. |

## Never

- Install, update or remove software without asking.
- Edit a `.qmd` from a worksheet before lint passes, or apply a row the person
  did not approve.
- Type a number over an inline R expression, invent a citation, or describe a
  figure you have not seen.
- Hand-edit a DOCX in `output/`, or delete a coauthor's file or a worksheet.
- Quote journal requirements from memory, or render for submission while a
  HARD check fails.
