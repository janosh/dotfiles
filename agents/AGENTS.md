# Global Agent Instructions

These rules apply to all projects in `~/dev/`.

## Correctness (don't bullshit)

- **Verify, don't reason.** Decide correctness/equivalence by running code, not by reading it. To claim two implementations match, write a script that feeds identical inputs to both and prints `max |a-b|` and max relative error over representative *and* edge-case inputs. Paste the numbers, don't assert the conclusion.
- **Round-off has a size — compute it.** Never wave off a numerical mismatch as "floating-point", "round-off", "precision", or "tolerance" without computing the actual error and comparing to machine eps for the dtype (f64 ≈ 2.2e-16, f32 ≈ 1.2e-7). Find real source of difference; don't excuse it, bisect it! Compare intermediate values, not just final outputs, locate first step where paths diverge. Don't guess at the cause.
- **Compare with explicit, justified tolerances.** Use `np.testing.assert_allclose(rtol=..., atol=...)` with values you chose deliberately (not defaults). For "bit-identical" claims use exact equality. Pin seeds before comparing stochastic outputs.
- **Read before you explain.** Before answering code questions, read it carefully as well as surrounding/related code *and* the callees it depends on. Quote specific lines your answer rests on. Never infer behavior from a name, signature, docstring, or comment; they can lie.
- **Separate observed from inferred.** Say "I ran X and saw Y" vs "I expect Y, haven't checked". Never report a test/build as passing, outputs as matching, or a bug as fixed unless you ran it and saw the result. If it's unverified, say so.
- **Surface uncertainty, then resolve it.** When unsure, name the checks that would settle it and run them. A flagged unknown beats a confident wrong answer. Ban vague reassurance; replace it with evidence or a missing check.

## Multi-agent branch sharing

Multiple agents may work on the same branch concurrently. Editing a file that already has uncommitted changes from another agent is fine, don't be timid, except at git time: when staging and committing. Don't stage changes unless asked to commit. Include only the changes relevant to your task and use explicit `git add <your-files>` instead of `git add -A` so you don't commit, revert, or stash another agent's out-of-scope work. Only exception being if other agent's work looks related or too menial to warrant it's own commit, then just include in your commit.

## Python Projects (*.py, pyproject.toml)

- Always add typing annotations to functions and classes, including return types
- Add descriptive docstrings to all functions and classes
- Don't add shebangs (no `#!/usr/bin/env python`)
- Use `pytest` for testing, never `unittest`
- All tests go in `./tests` with concise single-line docstrings
- Use `pytest.mark.parametrize()` to cover multiple parameter values
- When asserting numerical equality, use `np.testing.assert_allclose` with explicit `rtol`/`atol` you can justify; reserve `==` for integer/bit-exact cases
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
- Never use `fig.add_trace(go.Scatter(...))` — use `fig.add_scatter(...)`, `fig.add_bar(...)`, `fig.add_histogram(...)`, etc. directly. Shorter, avoids the redundant `go.` import for trace types, and lets plotly validate args at call time.
- **In `notebooks/`, prefer pymatviz widgets instead: `BarPlotWidget`, `HeatmapMatrixWidget`, `HistogramWidget`, `ScatterPlotWidget`, `StructureWidget`, `ConvexHullWidget`, `TrajectoryWidget`, `PhaseDiagramWidget`, etc. over `plotly` or `matplotlib` figures. Check existing demos/notebooks for usage and API patterns before writing new visualization code.
- avoid `typing.cast` unless absolutely necessary

## TypeScript/Svelte Projects (*.ts,*.svelte)

- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes
- Use `it.each([...])` and `test.each([...])` for parameterized vitest tests
- Prefer single-line comments (`//`) over multiline (`/** */`), even for multi-line comments use multiple `//` lines
- In CSS/style blocks, don't leave blank lines between rules - the closing `}` is enough separation
- Keep CSS simple: prefer nested selectors over many classes; inline styles if a class only has 1-2 rules. offer to remove CSS classes that aren't used at all.
- Prefer [attachments](https://svelte.dev/docs/svelte/@attach) over the legacy [`use:` directive](https://svelte.dev/docs/svelte/use) for actions
- Avoid `switch` statements, prefer simple `if`/`else` chains
- Prefer arrow functions for direct-return functions (body is a single `return`), e.g. `const f = (x) => x + 1` over `function f(x) { return x + 1 }`
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
- **Never use `--no-verify` when committing to ferrox.** prek hooks run `cargo clippy`, `cargo fmt`, `typos`, stub regeneration, etc. and `--no-verify` silently skips them, causing CI failures on push. If a commit doesn't pass hooks, fix the issue before committing, don't bypass. `--no-verify` only allowed in monorepos.
- Treat force push as a last resort, not a routine cleanup tool.
- Prefer a new follow-up commit over amending/rebasing once work is pushed.
- Never `git push --force` or `--force-with-lease` unless explicitly asked by the user for that specific branch and situation.

## CRITICAL: Protect Uncommitted Work

**NEVER run `git reset`, `git checkout <file>`, `git stash`, or `git clean` on modified/untracked files without explicit user approval!**

Multiple agents work on the same repo concurrently. Any destructive git operation (`reset`, `checkout -- <path>`, `stash`, `clean`, `restore`) can silently destroy another agent's in-progress work. This includes files you didn't modify — they may belong to a parallel agent. Always ask before discarding anything.

- If you need a clean working tree for your task, use `git worktree add` instead of stashing
- Check with `ls -la` and `file <path>` before deleting—directories may be symlinks to working copies
- Cache dirs like `~/.cache/**/matterviz` may be symlinked to `~/dev/matterviz` with uncommitted changes!

## General

- **Units notation**: never use `ų` or other obscure Unicode glyphs for units. Write `A^3` (cubic angstrom), `e/A^3` (electron density), `eV/A` (force), etc. In Rust doc comments and Python docstrings use `Å³`, `e/Å³`, `eV/Å` with the standard Å character.
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
- Run commands yourself to collect logs/errors—don't ask the user, and don't reason about outputs you could just observe. Run tests (`pytest`, `vitest`, `playwright`) or scripts, start dev servers, visit pages in browser, take actions to reproduce issues.
- When fixing a bug or making a behavior tweak, ALWAYS add or update a unit test that would have caught it. Prefer extending an existing related test over creating a new test to avoid extra setup/teardown bloat. Only create a new test when there is no related test to extend.
- **Never create GitHub issues or PRs without asking first.** Always ask before running `gh issue create` or `gh pr create`. When asked to "draft" an issue or PR, output the title and body as markdown for the user to review — do NOT run the `gh` command until explicitly told to post it.
