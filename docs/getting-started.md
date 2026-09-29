# Getting started with wongo

wongo (원고, "manuscript") turns a manuscript written in Quarto into Word files
that follow your journal's rules. Your coauthors keep working in Word with
Track Changes. wongo collects their edits into a checklist, and only the edits
you approve go into the manuscript.

You do not need to know programming. The easiest way is to talk to Claude:
Claude runs wongo for you and asks before it installs or changes anything.

This guide is for Windows 10, Windows 11 and macOS.

## What you need

- A Windows PC (Windows 10 version 1809 or newer, or Windows 11), or a Mac
  with macOS 13 or newer.
- A Claude account that includes Claude Code (Pro, Max, Team or Enterprise).
  Ask the lab if you do not have one.
- An internet connection.

Your manuscript text is sent to Claude while you work with it. KIST has
approved this for wongo.

## Terminal basics

A terminal is a window where you type commands. You need it only for a few
steps.

- **Windows:** press Win + X and choose **Terminal** (or **Windows
  PowerShell**). Each line starts with `PS C:\Users\YourName>`.
- **macOS:** press Cmd + Space, type `Terminal`, and press Enter.

To run a command, copy it from this page, paste it into the terminal (Windows:
Ctrl + V or right-click; macOS: Cmd + V), and press Enter.

After you install anything, close the terminal window and open a new one.
Newly installed programs only work in new windows.

On Windows, the commands in this guide use forward slashes: `C:/papers` is the
folder that File Explorer shows as `C:\papers`. Both work.

## Path A (recommended): let Claude set things up

### A1. Windows only: install Git for Windows

Claude Code uses Git to download the wongo plugin.

```
winget install --id Git.Git -e --source winget
```

Success: the last line says `Successfully installed`. If Windows asks "Do you
want to allow this app to make changes to your device?", click **Yes**.

If `winget` is not recognized, download the installer from
https://git-scm.com/downloads/win instead, run it, and click **Next** on every
screen.

On a Mac you can skip this step. If a window later asks you to install the
"command line developer tools", click **Install**.

### A2. Install Claude Code

Windows (in PowerShell):

```
irm https://claude.ai/install.ps1 | iex
```

macOS:

```
curl -fsSL https://claude.ai/install.sh | bash
```

Success: the installer finishes without a red error message. Close the window
and open a new one, then check it with `claude --version`.

### A3. Make a folder for your papers and go there

A folder outside OneDrive and iCloud is best: syncing can lock files while
wongo writes them.

Windows, first:

```
mkdir C:/papers
```

then:

```
cd C:/papers
```

macOS, first:

```
mkdir ~/papers
```

then:

```
cd ~/papers
```

### A4. Start Claude

```
claude
```

The first time, a browser window opens so you can sign in. When you see the
Claude Code welcome screen, you are ready.

### A5. Add the wongo plugin

Type this into Claude Code and press Enter:

```
/plugin marketplace add hoohugokim/wongo
```

Success: `Successfully added marketplace: wongo`.

Then type:

```
/plugin install wongo@wongo
```

A panel opens. Choose **Install for you (user scope)**. Success:
`Plugin is now active.` (If it says `Run /reload-plugins to activate.`, Claude
Code does that for you.)

### A6. Ask Claude to set up wongo

Type:

```
Please set up wongo on this computer.
```

Claude checks what is missing and explains each piece before it installs it:

- **uv** installs wongo and the Python it needs;
- **wongo** itself;
- **Quarto** turns your manuscript into Word files;
- **R** and three R packages compute the numbers, figures and tables in your text.

Answer yes or no to each question. Along the way:

- Windows may ask "Do you want to allow this app to make changes to your
  device?" Click **Yes**.
- On a Mac, Quarto and R need your password. Claude asks you to double-click an
  installer, or to paste a command into a separate Terminal window.
- Claude may ask you to restart it. Type `exit`, close the window, open a new
  terminal, go back to your folder (`cd C:/papers` or `cd ~/papers`), and type
  `claude --continue`. Your conversation picks up where it stopped.

Setup is finished when Claude tells you the check says **ready to render**.

### If you use the Claude desktop app

The desktop app can use the same plugin. Add the plugin once from a terminal
(steps A1 to A5); after that it appears in the desktop app too, under the
**+** button next to the prompt box > **Plugins**. Details are in the
[plugin's README](../integrations/claude-code/README.md).

## Path B: set things up by hand

Use this path if you prefer to install everything yourself. You can add Claude
later (steps A1, A2, A4 and A5).

### Windows

1. Install uv, which installs wongo:

   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Close the window and open a new one. Check it:

   ```
   uv --version
   ```

   Success: a line such as `uv 0.12.17`.

2. Install wongo. No Python or Git setup is needed; uv takes care of it:

   ```
   uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip
   ```

   Close the window and open a new one. Check it:

   ```
   wongo --version
   ```

   Success: `wongo 0.2.0` or a newer number. If Windows says `wongo` is not
   recognized, run `uv tool update-shell`, then open a new window.

3. Install Quarto. Click **Yes** if Windows asks for permission:

   ```
   winget install --id Posit.Quarto -e
   ```

   Or use the Windows installer from https://quarto.org/docs/get-started/.
   Close the window and open a new one. Check it:

   ```
   quarto --version
   ```

   Success: `1.10.18`, or another number that starts with `1.10`.

4. Install R:

   ```
   winget install --id RProject.R -e
   ```

   This does not make `R` available as a command in the terminal. That is fine:
   Quarto and wongo find R on their own.

5. Install three R packages. Open **R** from the Start menu (or RStudio, if you
   use it). Paste this line into the R console and press Enter:

   ```
   install.packages(c("knitr", "rmarkdown", "jsonlite"), repos = "https://cloud.r-project.org")
   ```

   If R asks "Would you like to use a personal library instead?" or "Would you
   like to create a personal library?", answer **Yes**. Success: R finishes
   without a message starting with `Error`.

6. Check everything:

   ```
   wongo doctor
   ```

   Success: the last line starts with `doctor: ready to render` (a count of
   warnings after it is fine). If not, each failing line says what to do; see
   also [Troubleshooting](#troubleshooting).

### macOS

1. Install uv:

   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   (With Homebrew you can use `brew install uv` instead.) Close the window and
   open a new one. Check it with `uv --version`.

2. Install wongo:

   ```
   uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip
   ```

   Close the window and open a new one. Check it with `wongo --version`.
   Success: `wongo 0.2.0` or a newer number.

3. Install Quarto: download the macOS installer from
   https://quarto.org/docs/get-started/ and double-click it. (With Homebrew:
   `brew install --cask quarto`.) Check it with `quarto --version` in a new
   window. Success: a number that starts with `1.10`.

4. Install R: open https://cloud.r-project.org/, choose **Download R for
   macOS**, and pick the installer for your Mac: "arm64" for Apple silicon (M1
   or newer), "x86_64" for Intel. The Apple menu > **About This Mac** shows which
   one you have. Double-click the downloaded file. (With Homebrew:
   `brew install --cask r`.)

5. Install three R packages. Open the **R** app (or RStudio), paste this line
   into the console, and press Enter:

   ```
   install.packages(c("knitr", "rmarkdown", "jsonlite"), repos = "https://cloud.r-project.org")
   ```

   Answer **Yes** if R asks about a personal library.

6. Check everything:

   ```
   wongo doctor
   ```

   Success: the last line starts with `doctor: ready to render`.

## Your first manuscript

The quickest way: ask Claude "Make an example manuscript called demo and render
it for my coauthors." Claude runs the steps below.

To do it yourself:

1. Go to your papers folder. Windows:

   ```
   cd C:/papers
   ```

   macOS:

   ```
   cd ~/papers
   ```

2. Create the example manuscript:

   ```
   wongo scaffold demo --example
   ```

   Success: `scaffolded` followed by the folder's path and a list of next steps.

3. Go into the new folder:

   ```
   cd demo
   ```

4. Check that this computer is ready:

   ```
   wongo doctor
   ```

   Success: the last line starts with `doctor: ready to render`. On Windows
   set to a language other than Korean, Quarto cannot work in a folder whose
   path has Hangul (Korean) letters, and the doctor says so (`project-path`).
   When in doubt, keep folder names to English letters, digits, `-` and `_`.

5. Make the Word files for coauthors:

   ```
   wongo render --target collab
   ```

   Quarto prints its progress for a few seconds. Success: the last lines say
   `wrote ...main-collab.docx` and `wrote ...si-collab.docx`, followed by a
   summary such as `checks: 6 passed`.

6. Open the Word file. Windows:

   ```
   Invoke-Item output/main-collab.docx
   ```

   macOS:

   ```
   open output/main-collab.docx
   ```

   Or double-click `main-collab.docx` in the `demo/output` folder in File
   Explorer or Finder. Track Changes is already on, so everything a coauthor
   changes is recorded.

What is in the folder:

- `index.qmd` is the manuscript text. The numbers in it are computed by small
  pieces of R code, so they always match the data.
- `si.qmd` is the Supporting Information.
- `refs.bib` holds the references.
- `output/` holds the Word files wongo makes. Do not edit them: each render
  replaces them.
- `decisions/` appears later and holds the checklists of coauthor edits.

## The everyday loop

| Step | Say to Claude | What wongo does |
|---|---|---|
| 1. See where you are | "What is the status of my manuscript?" | `wongo status` shows where things stand and one next step |
| 2. Write | "Tighten the Introduction", "Add a table of the removal rates" | Claude edits `index.qmd` |
| 3. Check | "Check the manuscript" | `wongo check` tests the word limit, citations, cross-references and figures |
| 4. Make Word files | "Make the Word file for my coauthors" | `wongo render --target collab` |
| 5. Send | (you email `output/main-collab.docx` and `si-collab.docx`) | |
| 6. Bring edits back | "Kim sent comments, the file is in from-coauthors/kim.docx" | `wongo roundtrip` turns every tracked change and comment into a checklist row |
| 7. Decide | Claude proposes a decision for each row; you answer in chat, or run `wongo review` yourself | the decisions are saved in the checklist |
| 8. Apply | "Apply the approved edits" | after `wongo worksheet lint` passes, Claude applies only the rows you approved |
| 9. Make Word files again | "Render again for coauthors" | `wongo render --target collab` |

Save coauthors' files in a `from-coauthors` folder inside your project, never
in `output/`, because the next render replaces files there.

To decide the edits yourself instead of in chat, run this in a terminal in your
project folder (use the checklist name Claude or wongo tells you):

```
wongo review decisions/merge-20260925-kim.md
```

wongo shows one edit at a time. Type a digit and press Enter: Enter alone
accepts Claude's proposal, **1** apply, **2** reject (it asks for a reason),
**3** fix-code (change the R code instead of the text), **4** needs-PI, **5**
skip, **0** save and quit. Each answer is saved at once, and the digits work
with the Korean keyboard on.

When you are ready to submit, say "Prepare the submission". wongo makes
`output/main-submission.docx` only if every required check passes and, when
the journal asks for one, the table-of-contents graphic is in
`figures/toc-art.png`.

For a revision, say "Make a tracked-changes copy against the version we
submitted". Claude uses `wongo diff` for that.

## Troubleshooting

`wongo doctor` finds most problems and prints the fix. The table lists what
you may see.

| What you see | What it means | What to do |
|---|---|---|
| `Quarto was not found` | Quarto is not installed, or the window is older than the install | Install Quarto (Path B, step 3), then open a new window |
| `Quarto ... is untested` | Your Quarto is not version 1.10 | Usually fine for drafts. Before submitting, install Quarto 1.10 from quarto.org |
| `Quarto is not on PATH` | Installed, but this window is older than the install | Open a new terminal window |
| `R was not found` | R is not installed | Install R (Path B, step 4) |
| `R package knitr is missing` (or `rmarkdown`) | An R package is missing | Install the packages (Path B, step 5) |
| `R package jsonlite is missing` | Optional package | Needed only if your numbers are read from JSON files; install it the same way |
| `R ... on Windows is not UTF-8 native` | R is older than 4.2, so Korean text can garble | Install a newer R |
| `your user folder (...) has non-ASCII characters` | Your Windows user name has Korean letters | Only matters if installing R packages fails. Then ask Claude to point R at `C:\Rlibs` |
| `Quarto on Windows cannot render inside a folder whose path has characters your system code page ... cannot represent` | Windows is set to a language other than Korean, and the folder path has Hangul (or other non-Latin) letters | Rename or move the project folder to English letters, digits, `-` and `_`, for example `C:/papers/wetland-study`. Or turn on "Beta: Use Unicode UTF-8 for worldwide language support" (Settings > Time & language > Language & region > Administrative language settings) and restart Windows |
| `the project is inside OneDrive` | Syncing can lock files during a render | Move the project to `C:/papers`, or pause OneDrive while rendering |
| `the project path is ... characters` | The folder path is very long | Use a short folder such as `C:/papers/<name>` |
| `main-collab.docx is open in another program (probably Word)` | Word has the file open, so wongo cannot replace it | Close the file in Word and render again. Nothing was changed or lost |
| `HARD checks failed — submission render refused` | A required check fails, so no submission file was made | Run `wongo check`; each failure lists the file and line to fix |
| `Profile requires TOC art` | The journal needs a table-of-contents graphic | Put the image at `figures/toc-art.png` and render again |
| `profile verified ... days ago` (WARN) | The journal's rules in wongo were last checked long ago | Check the journal's current guide for authors, or ask the wongo maintainer |
| `wongo` or `uv` is not recognized / command not found | The window is older than the install, or the tool folder is not on PATH | Open a new window; if that does not help, run `uv tool update-shell` and open a new window |
| `wongo review needs a person at a terminal` | Claude cannot run `wongo review` for you | Run it yourself in a terminal, or decide the rows with Claude in chat |
| `... is not UTF-8 text` | A file was saved in an old Korean encoding | Re-save it as UTF-8 (in VS Code: Save with Encoding > UTF-8) |
| `destination not empty` | That folder already exists and has files | Choose a new name for `wongo scaffold` |
| `wongo roundtrip` reports `0 changes` | The coauthor edited without Track Changes | Ask Claude to compare their file with the version you sent (`wongo diff`) |

About Korean (Hangul) names: folder and file names in Hangul work on macOS and
on Windows set to Korean. On Windows set to English or another language,
Quarto cannot render in a folder whose path contains Hangul, and wongo stops
with the message above. When in doubt, use English letters, digits, `-` and
`_` for project folders.

## Keeping things up to date

- **wongo:** ask Claude to "update wongo", or run:

  ```
  uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip --reinstall
  ```

- **The plugin:** in Claude Code, type `/plugin marketplace update wongo`. To
  update automatically, open `/plugin`, go to **Marketplaces**, select `wongo`
  and choose **Enable auto-update**.
- **Claude Code:** it updates itself if you installed it as in step A2.
- **Quarto:** stay on version 1.10 unless the wongo maintainer says otherwise.

## Getting help

- Run `wongo doctor` and send its output to the lab's wongo maintainer.
- Report problems at https://github.com/hoohugokim/wongo/issues.
