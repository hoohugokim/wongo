# Setup reference: run only after the person agrees

This file backs "Setup: always ask first" in SKILL.md. Its rules apply to every
step below: one item at a time, say what it is and why wongo needs it, show the
command, and wait for a yes. Skip every item `wongo doctor` already passes.

## 1. See what is already there

Nothing in this section installs anything.

| What | Git Bash (Windows) and macOS | PowerShell (Windows) |
|---|---|---|
| wongo | `wongo --version`, else `~/.local/bin/wongo --version` | `wongo --version`, else `& "$env:USERPROFILE\.local\bin\wongo.exe" --version` |
| uv | `uv --version`, else `~/.local/bin/uv --version` | `uv --version`, else `& "$env:USERPROFILE\.local\bin\uv.exe" --version` |
| Quarto, R, R packages, Windows hazards, the project | `wongo doctor --json` | same |
| winget (Windows) | `winget --version` | same |
| Homebrew (macOS, optional) | `brew --version` | not applicable |

On Windows, Claude Code's Bash tool is Git Bash when Git for Windows is
installed; otherwise commands run in PowerShell. Use the column for the shell
you have. Both accept forward slashes in paths.

As soon as wongo runs, `wongo doctor --json` names exactly what is missing and
prints the install hint for this computer. Install only that.

## 2. Windows 10/11

Tell the person first: for Quarto and R, Windows may ask "Do you want to allow
this app to make changes to your device?"; they click Yes. Nothing here needs
their password. After each install, programs appear on PATH only in new
windows, so call them by the full paths shown until setup is finished.

### 2.1 uv (installs wongo and a Python for it)

Recommended, because it needs no admin rights and installs to a known folder
(`%USERPROFILE%\.local\bin`). This line works from Git Bash and PowerShell:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternative: `winget install --id=astral-sh.uv -e` (then uv sits in a winget
folder, and you may need the restart before you can call it).

Success: `~/.local/bin/uv --version` (Git Bash) or
`& "$env:USERPROFILE\.local\bin\uv.exe" --version` (PowerShell) prints a version.

### 2.2 wongo

Git Bash:

```
~/.local/bin/uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip
```

PowerShell:

```
& "$env:USERPROFILE\.local\bin\uv.exe" tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip
```

No git is needed: uv builds wongo from the source archive, and it downloads a
suitable Python (3.11 or newer) by itself when the computer has none.

Success: `~/.local/bin/wongo --version` (or
`& "$env:USERPROFILE\.local\bin\wongo.exe" --version`) prints `wongo 0.2.0` or
newer. If uv warns that its tool folder is not on PATH, run
`uv tool update-shell` (by full path, like uv above); it takes effect in new
windows. Do not use the v0.2.0 release wheel: it predates `doctor`, `status`
and `review`.

### 2.3 Quarto 1.10

```
winget install --id Posit.Quarto -e
```

Fallback without winget: the Windows installer (.msi) from
https://quarto.org/docs/get-started/, which the person double-clicks. wongo's
output is verified against Quarto 1.10.18; if a newer Quarto has become the
current release, pin it with `winget install --id Posit.Quarto -e --version 1.10.18`.

wongo finds Quarto in its install folder even before PATH is updated; until the
next new window `wongo doctor` shows a WARN `quarto-path`, which is harmless.
Success: `wongo doctor --json` shows `quarto` passing with
`Quarto 1.10.x at ...`. A WARN `quarto-version` means it is not 1.10.x.

### 2.4 R 4.2 or newer

```
winget install --id RProject.R -e
```

This R is not added to PATH. That is fine: Quarto and wongo find R through the
Windows registry. Success: the `r` check in `wongo doctor --json` passes and its
`detail` names the Rscript it found, for example
`R 4.6.1 at C:\Program Files\R\R-4.6.1\bin\Rscript.exe (registry)`. Use that
path in the next step. A WARN `r-utf8` means R is older than 4.2, which can
garble Korean text: install a newer R.

### 2.5 R packages knitr, rmarkdown, jsonlite

The library inside `C:\Program Files\R` is not writable without admin rights,
and Rscript cannot answer R's "use a personal library instead?" question, so
install into the personal library explicitly. Replace `R-4.6.1` with the folder
the doctor showed.

Git Bash:

```
"/c/Program Files/R/R-4.6.1/bin/Rscript.exe" -e "lib <- Sys.getenv('R_LIBS_USER'); dir.create(lib, recursive = TRUE, showWarnings = FALSE); install.packages(c('knitr', 'rmarkdown', 'jsonlite'), lib = lib, repos = 'https://cloud.r-project.org')"
```

PowerShell:

```
& "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" -e "lib <- Sys.getenv('R_LIBS_USER'); dir.create(lib, recursive = TRUE, showWarnings = FALSE); install.packages(c('knitr', 'rmarkdown', 'jsonlite'), lib = lib, repos = 'https://cloud.r-project.org')"
```

Success: `wongo doctor --json` shows `r-knitr`, `r-rmarkdown` and `r-jsonlite`
passing. If the install fails and the doctor also shows WARN `home-path` (the
Windows user folder has Korean or other non-ASCII characters), point R at an
ASCII library folder, have the person restart Claude, and repeat this step:

- PowerShell: `[Environment]::SetEnvironmentVariable('R_LIBS_USER', 'C:\Rlibs', 'User')`
- Git Bash: `setx R_LIBS_USER 'C:\Rlibs'`

### 2.6 Finish

Ask the person to type `exit`, open a new terminal window, go back to the
folder (`cd C:/papers`), and start Claude with `claude --continue`. Then run
`wongo doctor --json`. Setup is done when `ok` is true.

### 2.7 Windows findings `wongo doctor` can report

| Check | Level | Meaning and fix |
|---|---|---|
| `project-path` | HARD | Quarto cannot render in a folder whose path has characters outside the Windows code page (for example Hangul on English Windows). Move or rename the folder to English letters, digits, `-` and `_` (e.g. `C:/papers/wetland-study`), or turn on "Beta: Use Unicode UTF-8 for worldwide language support" (Settings > Time & language > Language & region > Administrative language settings) and restart Windows. Korean Windows is fine. |
| `sync-folder` | WARN | The project is in OneDrive, which can lock files mid-render. Move it to `C:/papers/<name>` or pause syncing while rendering. |
| `long-path` | WARN | The project path is over 200 characters. Use a short folder such as `C:/papers/<name>`. |
| `home-path` | WARN | The user folder has non-ASCII characters. Only matters if R package installs fail; see 2.5. |
| `quarto-path` | WARN | Quarto is installed but not on PATH yet. Open a new window, or set `WONGO_QUARTO` to the full path of quarto.exe. |
| `r-utf8` | WARN | R is older than 4.2; install a newer R (2.4). |
| `render-hook` | WARN | `_quarto.yml` runs a Python script, but `python` is missing or the Microsoft Store placeholder. Ask first, then `winget install --id Python.Python.3.12 -e`. |

## 3. macOS 13 or newer

Quarto and R installers need the Mac login password. You cannot type it: the
person either double-clicks the installer or pastes the Homebrew command into
their own Terminal window. uv and wongo need no password.

### 3.1 uv

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Alternative with Homebrew: `brew install uv`. Success:
`~/.local/bin/uv --version` prints a version.

### 3.2 wongo

```
~/.local/bin/uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip
```

Success: `~/.local/bin/wongo --version` prints `wongo 0.2.0` or newer. If uv
warns about PATH, run `~/.local/bin/uv tool update-shell`.

### 3.3 Quarto 1.10 (the person runs it)

Offer both ways and let them choose:

- Installer: run `open https://quarto.org/docs/get-started/` to show the
  download page; they download the macOS installer (.pkg) and double-click it.
- Homebrew: they paste `brew install --cask quarto` into their own Terminal
  window and type their password when asked.

Success: `wongo doctor --json` shows `quarto` passing with `Quarto 1.10.x`.

### 3.4 R (the person runs it)

- Installer: run `open https://cloud.r-project.org/`; they choose "Download R
  for macOS" and the build that matches `uname -m` (`arm64` means Apple
  silicon, `x86_64` means Intel), then double-click it.
- Homebrew: they paste `brew install --cask r` into their own Terminal window.

Success: the `r` check in `wongo doctor --json` passes.

### 3.5 R packages

```
Rscript -e "lib <- Sys.getenv('R_LIBS_USER'); dir.create(lib, recursive = TRUE, showWarnings = FALSE); install.packages(c('knitr', 'rmarkdown', 'jsonlite'), lib = lib, repos = 'https://cloud.r-project.org')"
```

If `Rscript` is not found yet, use the path from the doctor's `r` check, usually
`/Library/Frameworks/R.framework/Resources/bin/Rscript` (CRAN installer) or
`/opt/homebrew/bin/Rscript` (Homebrew). Success: the three `r-...` checks pass.

### 3.6 Finish

As on Windows: `exit`, new Terminal window, `cd ~/papers`, `claude --continue`,
then `wongo doctor --json` until `ok` is true.

## 4. Updating

- wongo (ask first):
  `uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip --reinstall`,
  then `wongo --version`.
- Quarto: stay on 1.10.x unless the maintainer says otherwise.
- The Claude plugin: you cannot run slash commands. The person types
  `/plugin marketplace update wongo`, or turns on auto-update once under
  `/plugin` > Marketplaces > wongo > Enable auto-update.

## 5. When an install fails

| Symptom | Fix |
|---|---|
| `winget` is not recognized | App Installer is missing or outdated. Use the fallback installers (quarto.org, cloud.r-project.org, the uv PowerShell line), or ask the person to update "App Installer" from the Microsoft Store. |
| `irm` is not recognized | The line ran in cmd, not PowerShell. Use the full `powershell -ExecutionPolicy ByPass -c "..."` line above, which works from any shell. |
| "Could not create SSL/TLS secure channel" (older Windows 10) | In PowerShell run `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12`, then retry in the same window. |
| Downloads blocked by a proxy or security software | Stop and ask the person to contact their IT staff. Never turn off security settings. |
| `wongo` or `uv` still not found after a restart | Run `uv tool update-shell` by full path, then open a new window. |
| Quarto installed but the doctor says not found | Open a new window, or set `WONGO_QUARTO` to the full path of the quarto executable. |
