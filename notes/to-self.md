# Notes to self

## Cursor/Codex Setup

`configure_agents` in `setup/3-config.sh` creates all the symlinks below. It runs as part of `setup/main.sh`; re-run it after cloning new repos:

```sh
source ~/dev/dotfiles/setup/3-config.sh && DOTFILES_DIR=~/dev/dotfiles configure_agents
```

Why each link exists:

- Codex and Claude Code inherit `AGENTS.md` up the directory tree, so `~/dev/AGENTS.md` covers every repo below it.
- Cursor only reads `AGENTS.md` at and below the workspace root, so opening a single repo misses `~/dev/AGENTS.md`. Every repo therefore gets its own link, except repos with their own `AGENTS.md`. The global gitignore keeps these links untracked.
- Global skills live in `~/.cursor/skills/` (Cursor), `~/.agents/skills/` (Codex) and `~/.claude/skills/` (Claude Code). All three share the `SKILL.md` frontmatter format, so the same skill dirs are linked into each.

## Recovering lost work in VS Code

VS Code keeps local file history in `~/Library/Application Support/Code/User/History` ([superuser answer](https://superuser.com/a/1723403)). Once (2022-08-04) a `.ipynb` renamed to `.py` reverted to its notebook JSON after closing the workspace, losing 2h of edits. Recover by grepping the history for a term added late in the session:

```sh
find . -name "*.py" -exec grep accuracy_dict {} +
```

## `brew upgrade` breaks `uv` venvs

A `uv` venv only symlinks its Python binary, so a brew Python upgrade (e.g. 3.12.3 -> 3.12.4 on 2024-07-09) left `~/.venv/py312/bin/python` dangling (`bad interpreter`). The stopgap was relinking it: `ln -f $(which python3) ~/.venv/py312/bin/python`.

Fixed for good in `setup/2-apps.sh`: `uv` comes from its standalone installer (not brew) and `~/.venv/py314` is created with `--managed-python`, so brew can no longer invalidate it.

## iCloud Documents Sync & New Mac Setup

With "Desktop & Documents Folders" sync enabled on a new Mac, macOS often creates a duplicate subfolder (e.g. `Documents - Janosh’s M4 MacBook Pro`) inside Documents instead of merging, to avoid overwriting cloud files. To merge:

1. Copy unique files into the main folder (`-a` preserves timestamps/perms, `--ignore-existing` skips files already there). Dry run first, then rerun without `--dry-run`:

    ```sh
    rsync -av --ignore-existing "Documents/Documents - Janosh’s M4 MacBook Pro/" "Documents/" --dry-run
    ```

2. Verify the nested folder holds only duplicates (the diff should print nothing), then delete it:

    ```sh
    diff -r "Documents/Documents - Janosh’s M4 MacBook Pro" "Documents" | grep "Only in Documents - "
    trash "Documents/Documents - Janosh’s M4 MacBook Pro"
    ```

Keep **"Optimize Mac Storage"** **OFF** (System Settings > Apple ID > iCloud). When on, macOS offloads files to the cloud, leaving placeholders that need internet to open; off keeps a full local copy (safest for backups and offline work).
