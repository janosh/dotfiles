# macOS Setup Automation

## Purpose

This repo contains shell scripts and config files which, when executed and copied into their respective destinations, bring a clean install of macOS into a working-ready state.

> Forked from [Vítor’s dotfiles](https://github.com/vitorgalvao/dotfiles) but quite diverged now.

## Usage

To run all automatic scripts in this repo:

```sh
zsh -c "$(curl -sSL 'https://raw.github.com/janosh/dotfiles/main/setup/main.sh')"
```

Or, if you've already cloned the repo locally, simply run:

```sh
./setup/main.sh
```

To customize OS settings and complete the setup, run:

```sh
zsh -c "$(curl -sSL 'https://raw.github.com/janosh/dotfiles/main/setup/system-settings.sh')"
```

**New Mac Setup Note:**
When setting up new Macs with iCloud "Desktop & Documents" sync enabled, check [notes-to-self.md](notes-to-self.md) for steps to handle duplicate `Documents` folders.

## Organization

The important files in this repo are:

```text
.
└── setup
    ├── 1-setup.sh
    ├── 2-apps.sh
    ├── 3-config.sh
    ├── 4-cleanup.sh
    ├── main.sh
    └── system-settings.sh
```

The files prefixed with numbers contain only functions. None of them will do anything if run on their own. `main.sh` imports all functions and runs them in sequence.

If you wish to run only parts of the setup process, source the appropriate script(s) and call the respective functions, e.g. `source setup/2-apps.sh && brew_install`.
