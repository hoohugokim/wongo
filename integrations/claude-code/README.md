# wongo plugin for Claude Code

This folder is a Claude Code plugin. It teaches Claude how to run
[wongo](https://github.com/hoohugokim/wongo) for you. You talk to Claude in
plain words; Claude runs the commands and explains the results.

With the plugin, Claude can:

- set up wongo, Quarto and R on your computer, asking before each installation;
- start a manuscript for your journal, and write and check it with you;
- make Word files for your coauthors (Track Changes already on) and for the journal;
- read your coauthors' tracked changes and comments back into a checklist, and
  apply only the edits you approve;
- prepare a revision with a tracked-changes copy.

The plugin holds one skill, `wongo` ([skills/wongo/SKILL.md](skills/wongo/SKILL.md)),
and two reference files Claude reads when needed: setup steps per operating
system and the coauthor-review protocol. Claude uses the skill on its own when
you talk about your manuscript. You can also call it by typing `/wongo:wongo`.

## Before you install

- Claude Code, on Windows 10 (version 1809 or newer), Windows 11, or macOS 13
  or newer, signed in with a Claude plan that includes Claude Code (Pro, Max,
  Team or Enterprise).
- Git, which Claude Code uses to download the plugin.
  - Windows: install Git for Windows once. In PowerShell:

    ```
    winget install --id Git.Git -e --source winget
    ```

    Or download the installer from https://git-scm.com/downloads/win and click
    Next on every screen.
  - macOS: nothing to do. If a window asks to install the "command line
    developer tools", click Install.
- You do not need wongo, Quarto or R yet. After installing the plugin, ask
  Claude to "set up wongo".

Your manuscript text is sent to Claude while you work with it. KIST has
approved this use.

New to all of this? The step-by-step guide is
[docs/getting-started.md](../../docs/getting-started.md).

## Install

1. Open a terminal, go to the folder you want to work in, and start Claude Code:

   ```
   claude
   ```

2. Add this repository as a plugin marketplace. Type into Claude Code:

   ```
   /plugin marketplace add hoohugokim/wongo
   ```

   Success: `Successfully added marketplace: wongo`.

3. Install the plugin:

   ```
   /plugin install wongo@wongo
   ```

   A panel opens with the plugin's details. Choose **Install for you (user
   scope)**. Success: `Plugin is now active.` (If it says
   `Run /reload-plugins to activate.`, Claude Code reloads for you.)

4. Check: type `/` and look for `/wongo:wongo`, or open `/plugin` and the
   **Installed** tab.

5. Ask Claude:

   ```
   Please set up wongo on this computer.
   ```

From a shell instead of a Claude Code session, run these two commands one after
the other (they install for your user account):

```
claude plugin marketplace add hoohugokim/wongo
```

```
claude plugin install wongo@wongo
```

### Claude desktop app

The desktop app's Code tab shares plugins with Claude Code in the terminal:
both read the same settings on your computer, so a plugin installed for your
user account in one appears in the other. In the desktop app, click the **+**
button next to the prompt box and choose **Plugins**: **Add plugin** lists
plugins from marketplaces you have already added, and **Manage plugins**
enables, disables or uninstalls them.

The desktop app's documentation does not describe adding a new marketplace. So
add the wongo marketplace and plugin once from a terminal (steps 1 to 3 above).
After that, wongo is available in the desktop app too.

If a terminal is not an option, the same registration can live in your Claude
settings file (`~/.claude/settings.json`; on Windows
`C:\Users\<you>\.claude\settings.json`). This form comes from the Claude Code
settings reference but has not been tested with the desktop app yet:

```json
{
  "extraKnownMarketplaces": {
    "wongo": { "source": { "source": "github", "repo": "hoohugokim/wongo" } }
  },
  "enabledPlugins": { "wongo@wongo": true }
}
```

Merge these two keys into the file if it already exists; do not replace the
file.

### VS Code

In the Claude Code panel, type `/plugins` to open **Manage plugins**. Add
`hoohugokim/wongo` on the **Marketplaces** tab, then install `wongo` on the
**Plugins** tab for your user account.

## Keep it up to date

Two things update separately: the plugin (Claude's instructions) and wongo (the
program). Update both together, because the plugin follows the commands of
wongo's main branch.

- **The plugin.** Automatic updates are off for this marketplace until you turn
  them on: open `/plugin`, go to **Marketplaces**, select `wongo`, and choose
  **Enable auto-update**. To update by hand, type
  `/plugin marketplace update wongo` in Claude Code, or run
  `claude plugin update wongo@wongo` in a shell. New versions load in your next
  session, or right away after `/reload-plugins`.
- **wongo.** Ask Claude to "update wongo". It asks first, then runs:

  ```
  uv tool install https://github.com/hoohugokim/wongo/archive/refs/heads/main.zip --reinstall
  ```

- **Claude Code** installed with the native installer updates itself. A winget
  install updates with `winget upgrade Anthropic.ClaudeCode`.

## What Claude will and will not do

- It asks before installing, updating or removing any software.
- It proposes a decision for every coauthor edit, but records a decision only
  when you approve it, in chat or with `wongo review` in your own terminal.
- It changes your manuscript only after `wongo worksheet lint` passes, and only
  for edits marked `apply`.
- It never types a number over one your analysis code computes, never invents a
  citation, and never describes a figure it has not seen.
- It takes journal requirements only from wongo's verified journal profiles.
- It will not make a submission file while a required check fails.

## Uninstall

- The plugin: `/plugin uninstall wongo@wongo` in Claude Code, or
  `claude plugin uninstall wongo@wongo` in a shell. To also remove the
  marketplace: `/plugin marketplace remove wongo`.
- wongo itself: `uv tool uninstall wongo`.

## For maintainers

```text
.claude-plugin/marketplace.json          marketplace "wongo" (repository root)
integrations/claude-code/
├── .claude-plugin/plugin.json           plugin manifest
├── README.md                            this file
└── skills/wongo/
    ├── SKILL.md                         the skill
    └── references/
        ├── setup.md                     per-OS setup, run only after asking
        └── coauthor-review.md           the S4 worksheet protocol
```

- The marketplace entry's `source` is `./integrations/claude-code`, resolved
  from the repository root (the folder that contains `.claude-plugin/`).
- Neither `plugin.json` nor the marketplace entry sets `version`, so Claude
  Code versions the plugin by git commit and users who update track `main`. To
  switch to explicit releases, set `version` in `plugin.json` only and change it
  on every release; users stay on a cached copy until it changes.
- Journal judgment is not copied into the skill: Claude reads it from the paths
  `wongo profile show <slug> --json` returns.
- Check the files after every edit, from the repository root:

  ```
  claude plugin validate .
  ```

  ```
  claude plugin validate integrations/claude-code
  ```

- Try local changes without installing, for one session:

  ```
  claude --plugin-dir integrations/claude-code
  ```
