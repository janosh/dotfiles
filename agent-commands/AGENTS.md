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
- Always prefer `plotly` over `matplotlib` for plotting. When exporting to HTML, always use `include_plotlyjs="cdn"` for much smaller file sizes (3 KB vs 3 MB).
- Prefer `fig.add_scatter(...)`, `fig.add_bar(...)`, etc. over `fig.add_trace(go.Scatter(...))`; avoids redundant `go` trace imports.
- **In `notebooks/`, prefer pymatviz widgets instead: `BarPlotWidget`, `HeatmapMatrixWidget`, `HistogramWidget`, `ScatterPlotWidget`, `StructureWidget`, `ConvexHullWidget`, `TrajectoryWidget`, `PhaseDiagramWidget`, etc. over `plotly` or `matplotlib` figures. Check existing demos/notebooks for usage and API patterns before writing new visualization code.
- avoid `typing.cast` unless absolutely necessary

## TypeScript/Svelte Projects (*.ts,*.tsx, *.svelte)

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
- Never commit with `--no-verify` unless explicitly told; fix `prek` hook failures before committing.
- Treat force push as a last resort, not a routine cleanup tool.
- Prefer a new follow-up commit over amending/rebasing once work is pushed.
- Never `git push --force` or `--force-with-lease` unless explicitly asked by the user for that specific branch and situation.

## CRITICAL: Protect Uncommitted Work

**Never run destructive git ops (`reset`, `checkout -- <path>`, `restore`, `stash`, `clean`) on modified/untracked files without explicit approval.**

Multiple agents may have in-progress work. Ask before discarding anything, including files you did not modify.

- If you need a clean working tree for your task, use `git worktree add` instead of stashing
- Check with `ls -la` and `file <path>` before deleting—directories may be symlinks to working copies
- Cache dirs like `~/.cache/**/matterviz` may be symlinked to `~/dev/matterviz` with uncommitted changes!

## General

- **Units notation**: don't use obscure glyphs like `ų`. Use ASCII `A^3`, `e/A^3`, `eV/A`; in Rust/Python docs, use standard `Å` forms: `Å³`, `e/Å³`, `eV/Å`.
- **No single-letter or concatenated variable names!** Use proper snake_case: `idx` not `i`, `n_images` not `nimages`, `f_max` not `fmax`, `col_idx` not `colidx`
- Prefer early returns over deep nesting
- **No fallbacks or backward-compatible interfaces** unless explicitly told. Throw an error or fail early—silent catches, default shims, and compatibility wrappers mask bugs.
- Remove dead code aggressively. Prefer a clean codebase over deprecation.
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
- **Never commit handover docs, temp data files, or proof-of-concept artifacts** (no `HANDOVER.md`, sample `.jsonl`/`.lmdb` files, exploratory notebooks, etc.). These clutter the monorepo — keep them local or in `tmp/`.
- Use `prek` (Rust port), never `pre-commit` (Python)
- Run commands yourself to collect logs/errors—don't ask the user. Run tests (`pytest`, `vitest`, `playwright`), start dev servers, visit pages in browser, take actions to reproduce issues.
- When fixing a bug, ALWAYS add or update a unit test that would have caught it. Prefer extending an existing nearby test over creating a separate new test file when that keeps coverage concise and co-located.
- **Never create GitHub issues or PRs without asking first.** Always ask before running `gh issue create` or `gh pr create`. When asked to "draft" an issue or PR, output the title and body as markdown for the user to review — do NOT run the `gh` command until explicitly told to post it.
