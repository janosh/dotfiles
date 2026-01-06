# Notes to self

## When having lost work in VS Code

Incident on 2022-08-04: I had a `functorch_ensemble.ipynb` notebook which I renamed to a regular Python script `.py` and continued editing for 2 hours. After saving all files, I noticed 1 remaining blue dot indicating an unsaved file. This happens often when using the interactive window so I thought nothing of it, closed the workspace and left for lunch. I later reopened the folder and saw the `functorch_ensemble.py` had the original JSON content from the Jupyter notebook in it. All my edits were missing.

Recovery: Following this [superuser answer](https://superuser.com/a/1723403), I was able to recover my changes from `~/Library/Application\ Support/Code/User/History` by grepping for the term `accuracy_dict` which I knew I had added late in the 2h editing process. So any matching file would be a more recent backup.

```sh
find . -name "*.py" -exec grep accuracy_dict {} +
```

## `brew install/upgrade` breaks `uv` virtual env

reason is that a `uv` venv only stores a symlink to the Python binary which gets removed if a brew upgrade automatically installs a more recent Python version (e.g. 12.3->12.4 on `brew install mongodb-community` for me on 2024-07-09). fix was to update the symlink to a less brittle path

```sh
pytest # 1st symptom that something in the venv broke
>>> zsh: /Users/janosh/.venv/py312/bin/pytest: bad interpreter: /Users/janosh/.venv/py312/bin/python
readlink /Users/janosh/.venv/py312/bin/python # figure out why Python binary is missing
>>> /opt/homebrew/Cellar/python@3.12/3.12.3/Frameworks/Python.framework/Versions/3.12/bin/python3.12
ln -f $(which python3) /Users/janosh/.venv/py312/bin/python # update the symlink to fix venv
```

the last command brought the venv back to life and used `/opt/homebrew/bin/python3` instead of `/opt/homebrew/Cellar/python@3.12/3.12.3/Frameworks/Python.framework/Versions/3.12/bin/python3.12` which should not break again in future updates.
perhaps a better solution altogether would be to tell `uv` to copy the Python binary instead of linking it. `uv --link-mode=copy` appears to apply only to packages though.

## iCloud Documents Sync & New Mac Setup

**The Problem:**
When setting up a new Mac with "Desktop & Documents Folders" sync enabled in iCloud, macOS often creates a duplicate subfolder (e.g., `Documents - Janosh’s M4 MacBook Pro`) inside the main Documents folder instead of merging files. This is a safety feature to prevent overwriting existing cloud files with new local ones.

**Clean Merge Strategy:**
Use `rsync` to merge the unique files from the duplicate folder into the main one.

1. **Dry Run (Check what would happen):**

    ```sh
    # -a: archive mode (preserve timestamps, perms)
    # -v: verbose
    # --ignore-existing: skip files that already exist in destination
    # --dry-run: don't actually do anything yet
    rsync -av --ignore-existing "Documents/Documents - Janosh’s M4 MacBook Pro/" "Documents/" --dry-run
    ```

    If the dry run looks good, rerun without `--dry-run`.

2. **Verify & Delete:**
    Now the nested folder should contain *only* redundant duplicates.
    Verify this by diffing a sample file or checking counts, then delete the nested folder:

    ```sh
    diff -r "Documents/Documents - Janosh’s M4 MacBook Pro" "Documents" | grep "Only in Documents - "
    # Should return nothing (meaning no unique files left in the nested folder)

    trash "Documents/Documents - Janosh’s M4 MacBook Pro"
    ```

**Important Setting:**
Ensure **"Optimize Mac Storage"** is **OFF** (System Settings > Apple ID > iCloud).

* **ON:** macOS randomly offloads files to the cloud, leaving "ghost" files that need internet to open.
* **OFF:** Keeps a full copy of all files on your local drive (safest for backups and offline work).

## Cursor Setup

To make agent commands available globally across all Cursor projects:

```sh
ln -s ~/dev/dotfiles/agent-commands ~/.cursor/commands
```

Agent commands (e.g. `/commit`, `/continue-session`) become available in all projects.

For `AGENTS.md` rules to apply, they must be symlinked into each repo root (a common parent dir is not enough):

```sh
ln -s ~/dev/dotfiles/agent-commands/AGENTS.md ~/dev/repo1/AGENTS.md
ln -s ~/dev/dotfiles/agent-commands/AGENTS.md ~/dev/repo2/AGENTS.md
# repeat for each repo...
```
