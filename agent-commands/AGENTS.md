# Global Agent Instructions

These rules apply to all projects in `~/dev/`.

## Python Projects (*.py, pyproject.toml)

- Always add typing annotations to functions and classes, including return types
- Add descriptive docstrings to all functions and classes
- Don't add shebangs (no `#!/usr/bin/env python`)
- Use `pytest` for testing, never `unittest`
- All tests go in `./tests` with concise single-line docstrings
- Use `pytest.mark.parametrize()` to cover multiple parameter values
- Use `np.random.default_rng(seed=0)` not deprecated `np.random.*`
- Prefer `os.path.isfile/isdir` over `os.path.exists`
- Use f-strings for paths, not `os.path.join()`
- Prefer `os.path` over `pathlib.Path` (except with `tmp_path` fixture)
- Never create new uv virtual environments unprompted
- Use existing venv at `.venv/` or ask which to use
- Prefer `uv pip install` over `pip install`
- Use `ty` for type checking, never `mypy`, `pyright`, or others
- **NEVER use `__all__`!** We discourage star imports—they break static analysis of types and imports
- No bare except: always catch specific exceptions
- Use `time.perf_counter()` instead of `time.time()` for wall-time measurements
- Always prefer `plotly` over `matplotlib` for plotting. use pymatviz widgets (`StructureWidget`, `ConvexHullWidget`, `TrajectoryWidget`, `PhaseDiagramWidget`, etc.) for interactive visuals where applicable.
- avoid `typing.cast` unless absolutely necessary

## TypeScript/Svelte Projects (*.ts,*.tsx, *.svelte)

- Always use `pnpm` for package management, never npm or yarn
- Run tests with `pnpm vitest` or `pnpm playwright test`
- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes
- Use `it.each([...])` and `test.each([...])` for parameterized vitest tests
- Prefer single-line comments (`//`) over multiline (`/** */`), even for multi-line comments use multiple `//` lines
- In CSS/style blocks, don't leave blank lines between rules - the closing `}` is enough separation
- Keep CSS simple: prefer nested selectors over many classes; inline styles if a class only has 1-2 rules. offer to remove CSS classes that aren't used at all.
- Prefer [attachments](https://svelte.dev/docs/svelte/@attach) over the legacy [`use:` directive](https://svelte.dev/docs/svelte/use) for actions
- Avoid `switch` statements, prefer simple `if`/`else` chains
- `$derived` is writable! Don't use `$state` + `$effect` when `$derived` with later reassignment works
- Pass Svelte `$state` variables (not plain values) to `bind:`-able props to avoid `state_referenced_locally` warnings. e.g. avoid `x_axis={{ label: 'foo' }}` if `x_axis` is bindable. instead define `let x_axis = $state(label: 'foo')` and pass `bind:x_axis` to component.
- Never use `any` type! Use `unknown` and narrow, or define proper types
- Avoid `!` non-null assertions—narrow types instead
- Prefer optional chaining `?.` and nullish coalescing `??`
- Destructure props: `const { name, age } = user` over `user.name, user.age` repeatedly
- Keep components focused: extract when a component exceeds many hundreds of lines and has multiple responsibilities
- Prefer `format_num` from `matterviz` over `.toFixed()` for number formatting (handles SI prefixes, trailing zeros)
- Always use `SvelteSet`/`SvelteMap` instead of plain `Set`/`Map` — Svelte 5 needs these reactive wrappers for proper reactivity tracking, even for non-reactive-looking usage

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
- Don't commit without being asked
- Never add `Co-authored-by: Cursor` or similar to commit messages
- Amending unpushed commits is fine; amending pushed commits requires force push, so ask first before `git push --force` or `--force-with-lease`

## CRITICAL: Protect Uncommitted Work

**NEVER run `git reset`, `git checkout <file>`, or `git stash` on modified files without explicit approval!**

Multiple agents may be working on the same repo or files. Resetting/discarding changes destroys their progress and testing. Always ask first.

- Check with `ls -la` and `file <path>` before deleting—directories may be symlinks to working copies
- When stashing, use `git stash -u` to include untracked files if needed for clean context switch
- Cache dirs like `~/.cache/**/matterviz` may be symlinked to `~/dev/matterviz` with uncommitted changes!

## General

- **No single-letter or concatenated variable names!** Use proper snake_case: `idx` not `i`, `n_images` not `nimages`, `f_max` not `fmax`, `col_idx` not `colidx`
- Prefer early returns over deep nesting
- Log useful context with errors—include relevant variable values
- Test names should describe behavior, not implementation
- Prefer composition over inheritance
- keep code DRY but don't over-abstract
- Be concise. Avoid filler language.
- Never install dependencies without asking first.
- Prefer editing existing files over creating new ones.
- Keep existing comments when editing files.
- Use single-line section headers: `// === Section Name ===` not verbose multi-line box comments
- Never create or commit lock files (no `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `deno.lock`, etc.)
- Use `prek` (Rust port), never `pre-commit` (Python)
- Run commands yourself to collect logs/errors—don't ask the user. Run tests (`pytest`, `vitest`, `playwright`), start dev servers, visit pages in browser, take actions to reproduce issues.
