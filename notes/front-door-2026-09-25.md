# Claude front door and pre-merge review (2026-09-25)

Branch `feat/windows-front-door`. D-0010 decided the front door. This note
records what was verified before merging, and how.

## What shipped

- `.claude-plugin/marketplace.json` (marketplace `wongo`) and the plugin in
  `integrations/claude-code/`, holding one skill. It is invoked as
  `/wongo:wongo`, but Claude also selects it on its own from plain-language
  requests.
- The skill reads only `--json` output. Its reference files cover per-OS setup,
  done only after asking the person, and the S4 worksheet protocol.
- `docs/getting-started.md`: a guide for people who have never used a
  terminal, on Windows and macOS. Path A is Claude-first; Path B is manual.

## Verified

- Every command, JSON field, exit code and quoted message in the skill and the
  guide was checked against `src/wongo`.
- `claude plugin validate` passes for the marketplace and the plugin. The one
  warning is intentional: with no `version` set, Claude Code versions the
  plugin by git commit.
- `claude plugin marketplace add <local checkout>` and
  `claude plugin install wongo@wongo` were run under a throwaway
  `CLAUDE_CONFIG_DIR`, so the real settings stayed untouched. Both succeeded,
  and the plugin reported version `aad690270382` (a commit SHA), enabled.
- A headless Sonnet session with the plugin loaded (`--plugin-dir`) ran in the
  scaffolded example. It was asked in plain words where the manuscript stood
  and whether the computer was ready. It chose the `wongo:wongo` skill
  unprompted, ran `wongo status --json` and `wongo doctor --json`, and gave a
  correct summary in 5 turns (about US$0.24).
- Docs facts:
  - An `owner/repo` marketplace needs git. That is why Windows users install
    Git for Windows first; it is also Claude Code's recommended shell there.
  - A URL-only `marketplace.json` cannot serve a relative plugin path.
  - Auto-update is off for third-party marketplaces.
  - The desktop app lists plugins only from marketplaces already added.

## Not yet verified (T-0025)

- The in-session `/plugin install` panel labels quoted in the guides.
- The `~/.claude/settings.json` registration fallback in the desktop app.
- A real Windows PC with a Korean user account: Claude desktop setup, a
  Korean IME in `wongo review`, and Word holding a file open during a render.

## Pre-merge review: 10 findings, all fixed test-first

- **Render promotion:** rolls back on any exception, Ctrl-C included. An
  `OSError` that is not a lock becomes an actionable `OutputError`.
- **Manifest:**
  - It is written into the stage and promoted with the DOCX files, so outputs
    and manifest always agree.
  - Sources are fingerprinted before Quarto runs, so a source saved during the
    render leaves the output stale rather than fresh.
- **Leftover staged file:** a failed Quarto run no longer leaves
  `.wongo-stage-*.docx` in `output/`. A leftover that is open in Word is
  reported as `locked`.
- **One JSON object whatever fails:**
  - A YAML typo is an `input` error with its file and line and the quoting fix.
  - A non-DOCX input is an `input` error.
  - A usage error is JSON with exit code 2.
  - `wongo --json <cmd>` works like `wongo <cmd> --json`.
  - Ctrl-C gives kind `interrupted` with exit code 130.
  - A wongo bug gives kind `internal`, with a traceback and the issue URL.
  - Worksheet and review errors name their command.
- **`worksheet set`:**
  - It refuses a `PROPOSED` or `PENDING` value over a recorded decision
    unless `--force`.
  - A decision over a mistyped value keeps the old text as `was ...`.
- **`status`:**
  - It never says "nothing to do" while an output was saved over; it offers
    no command, only the choice.
  - It reports the style a render would use, `$WONGO_STYLE` included.
- **`shell_arg`:** double quotes for spaces and `& ( )`, which work in bash,
  PowerShell and cmd. Single quotes when `$`, a backtick, `"`, `!` or a
  backslash appears.
- **`.qmd` guard:** it also refuses names that Windows opens as the `.qmd`:
  a trailing dot or space, or `name:stream`.
- **Quarto and R lookup:** uses `ProgramW6432`, so a 32-bit Python still finds
  64-bit installs.
