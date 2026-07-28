# macOS Setup Automation

## Purpose

Shell scripts and config to bootstrap a fresh macOS install (Homebrew, dotfiles, system defaults), plus Cursor agent rules/skills and assorted utilities.

## Usage

To run all automatic scripts in this repo, from a fresh machine or an existing checkout:

```sh
zsh -c "$(curl -fsSL 'https://raw.githubusercontent.com/janosh/dotfiles/main/setup/main.sh')"
```

It clones into `~/dev/dotfiles` (or updates an existing clone) and runs from there.

To customize OS settings and complete the setup, run:

```sh
zsh -c "$(curl -fsSL 'https://raw.githubusercontent.com/janosh/dotfiles/main/setup/system-settings.sh')"
```

**New Mac Setup Note:**
When setting up new Macs with iCloud "Desktop & Documents" sync enabled, check [notes/to-self.md](notes/to-self.md) for steps to handle duplicate `Documents` folders.

## Organization

```text
.
├── agents/AGENTS.md           # global agent rules (symlink to ~/dev/AGENTS.md)
├── agents/skills/             # agent skills symlinked into Cursor/Codex/Claude
├── dotfiles/                  # shell, git, spell-check dict
├── notes/                     # personal runbooks (Mac setup, Cursor, etc.)
├── setup/                     # macOS bootstrap scripts
└── scripts/                   # one-off utilities
```

Setup scripts are prefixed with numbers and define functions only. `setup/main.sh` sources them and runs the install sequence.

If you wish to run only parts of the setup process, source the appropriate script(s) and call the respective functions. They locate the repo via `DOTFILES_DIR`, which `main.sh` normally sets, and helpers like `renew_sudo` live in `1-setup.sh`:

```sh
export DOTFILES_DIR=~/dev/dotfiles
source setup/1-setup.sh
source setup/2-apps.sh
ask_details && brew_install
```
