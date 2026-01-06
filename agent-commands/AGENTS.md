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
- Use `ty` for type checking, never `mypy`, `pyright`, or others
- Never use `__all__`: we want to discourage star imports which make it hard to statically analyze types and imports
- No bare except: always catch specific exceptions

## TypeScript/Svelte Projects (*.ts,*.tsx, *.svelte)

- Always use `pnpm` for package management, never npm or yarn
- Run tests with `pnpm vitest` or `pnpm playwright test`
- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes
- Avoid single-letter variable names (idx not i, event not e)
- Use `it.each([...])` and `test.each([...])` for parameterized vitest tests
- Prefer single-line comments (`//`) over multiline (`/** */`), even for multi-line comments use multiple `//` lines
- In CSS/style blocks, don't leave blank lines between rules - the closing `}` is enough separation
- Keep CSS simple: prefer nested selectors over many classes; inline styles if a class only has 1-2 rules. offer to remove CSS classes that aren't used at all.
- Prefer [attachments](https://svelte.dev/docs/svelte/@attach) over the legacy [`use:` directive](https://svelte.dev/docs/svelte/use) for actions
- Avoid `switch` statements, prefer simple `if`/`else` chains
- `$derived` is writable! Don't use `$state` + `$effect` when `$derived` with later reassignment works
- Pass Svelte `$state` variables (not plain values) to `bind:`-able props to avoid `state_referenced_locally` warnings. e.g. avoid `x_axis={{ label: 'foo' }}` if `x_axis` is bindable. instead define `let x_axis = $state(label: 'foo')` and pass `bind:x_axis` to component.
- Never use `any` type! - Use unknown and narrow, or define proper types
- Destructure props: `const { name, age } = user` over `user.name, user.age` repeatedly
- Keep components focused: extract when a component exceeds many hundreds of lines and has multiple responsibilities

## Git & GitHub CLI & Interactive Rebases

- Git editor is set to `cursor --wait` for interactive operations
- Use `GIT_EDITOR` to bypass interactive mode and avoid getting stuck:

   ```bash
   # Squash last 2 commits
   GIT_EDITOR="sed -i '' '2s/pick/squash/'" git rebase -i HEAD~2

   # General pattern: override editor with sed commands
   GIT_EDITOR="sed -i '' 's/pick/squash/2'" git rebase -i HEAD~n
   ```

- If `gh` commands fail with auth errors (e.g. "Unauthorized"), try switching accounts: `gh auth switch`
- Don't commit or amend without being asked

## NEVER delete or `rm -rf` cache directories without explicit user approval

- check with `ls -la` and `file <path>` to see if a directory is a symlink before deleting
- get approval before `git stash`, `git checkout`, or `git reset` that could discard/hide uncommitted work
- cache dirs like `~/.cache/**/matterviz` may be symlinked to `~/dev/matterviz`, a working copy with uncommitted changes!

## General

- Be concise. Avoid filler language.
- Never install dependencies without asking first.
- Prefer editing existing files over creating new ones.
- Keep existing comments when editing files.
- Never create or commit lock files (no `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `deno.lock`, etc.)
- Run commands yourself to collect logs/errors—don't ask the user. Run tests (`pytest`, `vitest`, `playwright`), start dev servers, visit pages in browser, take actions to reproduce issues.
