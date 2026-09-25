# S4 protocol: coauthor edits through the merge worksheet

The rule behind every step: you propose, a person decides, wongo checks, and
only then do you edit the `.qmd`. wongo itself never writes a `.qmd`.

Worksheet commands, where `<ws>` is the worksheet path, e.g.
`decisions/merge-20260925-kim.md` (forward slashes work on every OS):

| Command | Who runs it | What it does |
|---|---|---|
| `wongo roundtrip <file.docx> [--qmd si.qmd] --json` | you | writes `decisions/merge-<date>-<stem>.md`, every row `PENDING` |
| `wongo worksheet status <ws> --json` | you | counts and every row as data |
| `wongo worksheet set <ws> <N> '<value>'` | you | writes one row's disposition exactly as given; refuses a `PROPOSED` or `PENDING` value over a recorded decision unless `--force` |
| `wongo worksheet set <ws> <N> --location <line>` | you | points a row at another `.qmd` line |
| `wongo review <ws>` | the person, in a terminal | decides rows one at a time with digits |
| `wongo worksheet lint <ws> --json` | you | `ok: true` only when every row is validly decided |

## 1. Before extracting

- The coauthor's file must not live in `output/`: a render replaces files there.
  Ask the person to save it as `from-coauthors/<coauthor>.docx` inside the
  project (English letters are safest in the name). If they saved over
  `output/main-collab.docx`, `wongo status` shows that output as `modified`:
  move the file to `from-coauthors/` before any render.
- One worksheet per coauthor file. For a coauthor-edited SI file add
  `--qmd si.qmd`.
- Look in `decisions/` first. Running roundtrip again on the same file writes a
  new `-2` worksheet with every row `PENDING`, and `wongo status` then points at
  the newest one. Continue the existing worksheet instead.
- If the coauthor edited without Track Changes, roundtrip finds nothing. With
  the person's OK, make a tracked copy against the version you sent, then
  extract that:
  `wongo diff output/main-collab.docx from-coauthors/kim.docx -o from-coauthors/kim-tracked.docx --author "Kim"`
  (only if `output/main-collab.docx` is still the version you sent; otherwise
  use the copy you sent). Tables and rich paragraphs are only reported by
  `wongo diff`; check those in Word Compare.

## 2. Extract

Run `wongo roundtrip from-coauthors/kim.docx --json` and read:

- `changes`: the number of rows. Zero usually means Track Changes was off.
- `kinds`: insertion, deletion, replacement, comment, unparsed.
- `unmatched`: rows wongo could not align to a `.qmd` line.
- `unparsed`: changes wongo could not extract (for example an inserted citation
  whose text contains brackets). They are real edits, never ignorable.

A row in the worksheet looks like this:

```
## 3. replacement — Kim Coauthor
- location: index.qmd:43
- old: 0.085
- new: 0.09
- context: …ults and Discussion The fitted first-order rate constant was…
- disposition: PENDING
```

`context` is the original text just before the change. `—` in `old` or `new`
means empty. For a comment, `old` is the text the comment is attached to and
`new` is the comment itself.

## 3. Check each location

Read the rows with `wongo worksheet status <ws> --json`, then open the `.qmd`
at each row's `line` and confirm the line holds `old` (or, for an insertion,
the end of `context`). The alignment is fuzzy and can pick the wrong line, for
example a line inside a multi-line `<!-- ... -->` comment. When it is wrong,
find the right line and run `wongo worksheet set <ws> <N> --location <line>`.

- `UNMATCHED`: search the `.qmd` for `old` or the context. Found: set the
  location. Not found: the text is probably generated (R output, a table, a
  caption, the reference list), which makes the row `fix-code`, or it needs the
  person's judgment.
- Title, abstract, keywords and author list live in the YAML front matter, which
  roundtrip never matches. If the context reads like the abstract or the title,
  set the location to that front-matter line.
- `unparsed`: find the change in the coauthor's DOCX near the quoted context
  (or ask the person to look in Word) and describe it to the person. wongo
  refuses `apply` on these rows, so the choice is `fix-code`, `needs-PI` or
  `reject: <reason>`. If the person wants the edit, record that in the note (for
  example `needs-PI — inserted citation to Lee 2021; author to confirm`) and make
  it later as a separate edit they approve in chat.

## 4. Judge and propose every undecided row

| The change | Propose | Rationale to give |
|---|---|---|
| Plain prose (wording, grammar, a new sentence) | `apply` | what it changes and why it is safe |
| A number, table cell, caption or figure text produced by R code | `fix-code` or `reject: <reason>` | never type the number: say which code or data would produce what the coauthor wants, or why the computed value stands |
| On a line with inline R, but only the prose around the expression | `apply` | say that the R expression stays untouched |
| A citation typed as text, e.g. "(Smith et al., 2020)" | `apply` if its key is in `refs.bib` (you will write `[@key]`); otherwise `needs-PI` | name the key, or say the reference must be added first; never invent one |
| A comment that asks a question | `needs-PI`, or `reject: <the answer>` | draft the answer for the person to send |
| A comment that asks for a change | `apply` with the exact new wording in the rationale, or `needs-PI` | the person approves the actual text, not just the idea |
| Two coauthors making the same edit | decide one, `reject: duplicate of row N in <worksheet>` for the other | |
| Anything touching claims, data interpretation, authorship or funding | `needs-PI` | why it needs the PI |

Write each proposal with:

```
wongo worksheet set <ws> <N> 'PROPOSED <final> — <rationale>'
```

- `<final>` is `apply`, `fix-code`, `needs-PI` or `reject: <reason>`.
- Use single quotes. Keep backticks, dollar signs and apostrophes out of the
  rationale; both Git Bash and PowerShell would change them. If a dash causes
  trouble, a plain ` - ` works as the separator too.
- A bad value changes nothing and wongo prints the grammar; fix and rerun.

Examples:

```
wongo worksheet set decisions/merge-20260925-kim.md 1 'PROPOSED apply — prose only; adds emphasis, meaning unchanged'
wongo worksheet set decisions/merge-20260925-kim.md 3 'PROPOSED fix-code — 0.085 is computed by R; for two decimals change the rounding in the inline code, never type 0.09'
wongo worksheet set decisions/merge-20260925-kim.md 5 'PROPOSED reject: the sentence repeats the Methods'
```

## 5. The person decides

Offer both ways; they may mix them.

### 5a. In their own terminal: `wongo review`

Tell them: open a terminal (Windows: Win + X, then Terminal; macOS: Terminal),
go to the project folder, and run `wongo review <ws>`. For each row it shows
the change, the `.qmd` line and your proposal. They type a digit and press
Enter:

- Enter alone: accept your proposal as written
- 1 apply, 2 reject (it asks for the reason), 3 fix-code, 4 needs-PI
- 5 skip for now, 0 save and quit, ? help

Every decision is saved at once. Digits work with the Korean keyboard on. You
cannot run `wongo review` yourself: without a terminal it refuses.

### 5b. In chat, row by row

Show at most five rows per message, each like this:

```
Row 3 of 12 · replacement · Kim Coauthor · index.qmd line 43
Change: "0.085" -> "0.09"
Manuscript line: The fitted first-order rate constant was `r sprintf("%.3f", k)` per day.
My proposal: fix-code. 0.085 is computed by R; if two decimals are wanted I change the rounding in the code. I will not type 0.09.
Your decision: apply, reject (with a reason), fix-code, needs-PI, or skip?
```

What counts as approval:

- An answer that names the row, or is given while only that row is shown, with
  a decision: "3 fix-code", "apply 1 and 2", "reject 5, it repeats the Methods".
- "Accept all your proposals": read the row numbers back with their proposals
  and ask "Set rows 1-12 exactly as proposed?". A yes to that list counts for
  each listed row.
- Never count silence, "thanks", "looks fine", or an answer about another row.

Record each answer right away:

- Same decision as proposed: `wongo worksheet set <ws> <N> apply` keeps your
  rationale. To record who decided, add a note:
  `wongo worksheet set <ws> <N> 'apply — confirmed in chat by Jiwon'`.
- A different decision: write theirs, e.g.
  `wongo worksheet set <ws> <N> 'reject: keep three decimals'`; wongo keeps your
  proposal after it as `was PROPOSED ...`.
- `reject` always needs the person's reason after the colon.
- Skip: leave the row as proposed and move on.

Never change a decision the person made, in either way, unless they ask. wongo
enforces this for proposals: `PROPOSED` or `PENDING` over a decided row is
refused, and only `--force` (after the person asks to reopen the row) overrides
it. A new final value never loses the old one: wongo keeps it as `was ...`.

## 6. Lint

Run `wongo worksheet lint <ws> --json`.

- `ok: false`: `problems[]` lists each row with what is wrong: still `PENDING`,
  `PROPOSED` but not confirmed, an invalid value, `reject` without a reason, or
  `apply` on an `UNMATCHED` location or an unparsed row. Go back to step 3 or 5.
- `ok: true` with warnings: `apply` on a line with inline code, or a line number
  past the end of the file. Re-check those rows before editing.

Do not edit the `.qmd` until lint returns `ok: true`.

## 7. Apply

Work row by row, top to bottom, and re-read each target line just before you
edit it.

- `apply`, replacement: replace `old` with `new` on that line only. If `old` is
  not on the line, stop: the location is stale; fix it and lint again.
- `apply`, insertion: insert `new` where the context ends. A new sentence goes
  on its own line.
- `apply`, deletion: remove `old` from the line.
- `apply`, comment: make the exact wording the person approved.
- Keep one sentence per line and never touch an inline R expression while
  applying prose.
- `fix-code`: show the person the code or data change and the value it will
  produce; change it only after they agree; re-render and read the new value.
- `needs-PI`: list the rows (number, change, question) so the person can
  forward them. Nothing changes in the `.qmd` yet.
- `reject`: nothing changes. Offer a short note the person can send back to
  the coauthor.

## 8. Re-render and report

1. `wongo check --json`; fix anything the edits broke (for example a citekey
   typo) before rendering.
2. `wongo render --target collab --json`. If it stops because Word has the file
   open, follow "When Word has the file open" in SKILL.md.
3. Tell the person, in plain words: how many edits were applied, which code
   fixes wait for their OK, which questions go to the PI, what was rejected,
   and that the new `output/main-collab.docx` is ready to send.
