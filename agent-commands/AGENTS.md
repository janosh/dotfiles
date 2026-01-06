# Global Agent Instructions

These rules apply to all projects in `~/dev/`.

## Python Projects (*.py, pyproject.toml)

- Always add typing annotations to functions and classes, including return types
- Add descriptive docstrings to all functions and classes
- Don't add shebangs (no `#!/usr/bin/env python`)
- Use `pytest` for testing, never `unittest`
- All tests go in `./tests` with concise single-line docstrings
- Use `pytest.mark.parametrize()` to cover multiple parameter values
- Avoid single-letter variable names (idx not i, exc not e, df_name not df)
- Use `np.random.default_rng(seed=0)` not deprecated `np.random.*`
- Prefer `os.path.isfile/isdir` over `os.path.exists`
- Use f-strings for paths, not `os.path.join()`
- Prefer `os.path` over `pathlib.Path` (except with `tmp_path` fixture)
- Never create new uv virtual environments unprompted
- Use existing venv at `.venv/` or ask which to use
- Prefer `uv pip install` over `pip install`

## TypeScript/Svelte Projects (*.ts,*.tsx, *.svelte)

- Always use `pnpm` for package management, never npm or yarn
- Run tests with `pnpm vitest` or `pnpm playwright test`
- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes
- Avoid single-letter variable names (idx not i, event not e)
- Use `it.each([...])` and `test.each([...])` for parameterized vitest tests
- Prefer single-line comments (`//`) over multiline (`/** */`), even for multi-line comments use multiple `//` lines
- In CSS/style blocks, don't leave blank lines between rules - the closing `}` is enough separation
- Prefer [attachments](https://svelte.dev/docs/svelte/@attach) over the legacy [`use:` directive](https://svelte.dev/docs/svelte/use) for actions
- Avoid `switch` statements, prefer simple `if`/`else` chains

## Git & Interactive Rebases

- Git editor is set to `cursor --wait` for interactive operations
- Use `GIT_EDITOR` to bypass interactive mode and avoid getting stuck:

  ```bash
  # Squash last 2 commits
  GIT_EDITOR="sed -i '' '2s/pick/squash/'" git rebase -i HEAD~2

  # General pattern: override editor with sed commands
  GIT_EDITOR="sed -i '' 's/pick/squash/2'" git rebase -i HEAD~n
  ```

## GitHub CLI

- If `gh` commands fail with auth errors (e.g. "Unauthorized"), try switching accounts: `gh auth switch`

## General

- Be concise. Avoid filler language.
- Never install dependencies without asking first.
- Prefer editing existing files over creating new ones.
- Keep existing comments when editing files.
- Never create or commit lock files (no `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `deno.lock`, etc.)
