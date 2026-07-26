# Global Agent Instructions

These rules apply to all projects.

## Correctness (don't bullshit)

- **Equivalence is measured, not read.** To claim two implementations match, run both on identical inputs (representative *and* edge cases) and paste `max |a-b|` and max relative error. Never pronounce on equivalence from reading the code.
- **Round-off has a size, compute it.** Never wave off a numerical mismatch as "floating-point", "round-off", "precision", or "tolerance" without computing the actual error and comparing to machine eps for the dtype (f64 ≈ 2.2e-16, f32 ≈ 1.2e-7). Bisect it: compare intermediate values, not just final outputs, and locate the first step where the paths diverge.
- **Compare with explicit, justified tolerances.** Use `np.testing.assert_allclose(rtol=..., atol=...)` with values you chose deliberately (not defaults). For "bit-identical" claims use exact equality. Pin seeds before comparing stochastic outputs.
- **Read before you explain.** Before answering code questions, read it carefully as well as surrounding/related code *and* the callees it depends on. Quote specific lines your answer rests on. Never infer behavior from a name, signature, docstring, or comment; they can lie.
- **Separate observed from inferred.** Say "I ran X and saw Y" vs "I expect Y, haven't checked". Never report a test/build as passing, outputs as matching, or a bug as fixed unless you ran it and saw the result. If it's unverified, say so; then name the check that would settle it and run it.

## Multi-agent branch sharing

Multiple agents may work on the same branch concurrently. Editing a file that already has uncommitted changes from another agent is fine, don't be timid, except at git time: when staging and committing. Don't stage changes unless asked to commit. Include only the changes relevant to your task and use explicit `git add <your-files>` instead of `git add -A` so you don't commit, revert, or stash another agent's out-of-scope work. Only exception being if other agent's work looks related or too menial to warrant it's own commit, then just include in your commit.

## Python Projects (*.py, pyproject.toml)

- Always add typing annotations to functions and classes, including return types
- Add descriptive docstrings to all functions and classes
- Don't add shebangs (no `#!/usr/bin/env python`)
- Run scripts with `uv run script.py`, not bare `python script.py`. `uv` picks the env itself: a project's existing `.venv/`, an isolated env for scripts declaring PEP 723 inline `dependencies`, the active `~/.venv/py314` otherwise. Never create venvs unprompted; don't want per-project `venv`s in repos that lack one.
- Use `pytest` for testing, never `unittest`
- All tests go in `./tests` with concise single-line docstrings
- Use `pytest.mark.parametrize()` to cover multiple parameter values
- Use `np.random.default_rng(seed=0)` not the legacy `np.random.*` API
- Prefer `os.path.isfile/isdir` over `os.path.exists`
- Use f-strings for paths, not `os.path.join()`
- Prefer `os.path` over `pathlib.Path` (except with `tmp_path` fixture)
- Use `ty` for type checking, never `mypy`, `pyright`, or others
- **NEVER use `__all__`!** We discourage star imports—they break static analysis of types and imports
- Use `time.perf_counter()` instead of `time.time()` for wall-time measurements
- Always prefer `plotly` over `matplotlib` for plotting. When exporting to HTML, always use `include_plotlyjs="cdn"` for much smaller file sizes (3 KB vs 3 MB).
- Never use `fig.add_trace(go.Scatter(...))` — use `fig.add_scatter(...)`, `fig.add_bar(...)`, `fig.add_histogram(...)`, etc. directly. Shorter, avoids the redundant `go.` import for trace types, and lets plotly validate args at call time.
- **In `notebooks/`, prefer pymatviz widgets instead: `BarPlotWidget`, `HeatmapMatrixWidget`, `HistogramWidget`, `ScatterPlotWidget`, `StructureWidget`, `ConvexHullWidget`, `TrajectoryWidget`, `PhaseDiagramWidget`, etc. over `plotly` or `matplotlib` figures. Check existing demos/notebooks for usage and API patterns before writing new visualization code.
- avoid `typing.cast` unless absolutely necessary

## TypeScript/Svelte Projects (*.ts,*.svelte)

- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes, except inside TypeScript type definitions
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
- Destructure props: `const { name, age } = user` over `user.name, user.age` repeatedly
- Don't split components on line count alone—core ones run past 2000 lines by design. Only offer an extraction when a file has clearly separable responsibilities.
- Prefer `format_num` from `matterviz` over `.toFixed()` for number formatting (handles SI prefixes, trailing zeros)
- Always use `SvelteSet`/`SvelteMap` instead of plain `Set`/`Map` — Svelte 5 needs these reactive wrappers for proper reactivity tracking, even for non-reactive-looking usage

## Git & GitHub CLI

- Git editor is `cursor --wait`, so interactive commands hang. Override it with a `sed` script instead, e.g. `GIT_EDITOR="sed -i '' 's/pick/squash/2'" git rebase -i HEAD~n`.
- If `gh` commands fail with auth errors (e.g. "Unauthorized"), try switching accounts: `gh auth switch` (don't ask permission for this, just do)
- Don't commit without being asked
- Never add `Co-authored-by: Cursor/Codex/...` or similar to commit messages
- Never `git push --force/--force-with-lease` unless explicitly asked for that specific branch and situation. Once work is pushed, prefer follow-up commits over amending/rebasing.
- **Never create GitHub issues or PRs without asking.** When asked to "draft" one, output the title and body as markdown for review — don't run `gh` until explicitly told to post.
- **Permission to commit is never permission to open a PR**, and neither is a blocked push. If a push is rejected (branch protection, required status checks, ruleset), stop and report it. Do NOT work around it by moving the commit to a new branch and opening a PR. Leave the commit local and let the user choose how to land it.
- **Push only where the branch already publishes** — `git push --dry-run` prints the real destination. Never `git push -u origin <name>` for a branch with no `origin/<name>` (e.g. after `gh pr checkout` of a fork PR, that publishes a new upstream branch instead of updating their PR). No destination means stop and ask.
- Asking a question mid-task and getting an answer authorizes only what was asked. When the plan turns out not to work, ask again. Don't substitute a different action you think is equivalent.

## CRITICAL: Protect Uncommitted Work

**NEVER run `git reset`, `git checkout <file>`, `git stash`, or `git clean` on modified/untracked files without explicit user approval!**

Multiple agents work on the same repo concurrently. Any destructive git operation (`reset`, `checkout -- <path>`, `stash`, `clean`, `restore`) can silently destroy another agent's in-progress work. This includes files you didn't modify — they may belong to a parallel agent. Always ask before discarding anything.

- If you need a clean working tree for your task, use `git worktree add` instead of stashing
- Check with `ls -la` and `file <path>` before deleting—directories may be symlinks to working copies

## General

- **Units notation**: never use `ų` or other obscure Unicode glyphs for units. Write `A^3` (cubic angstrom), `e/A^3` (electron density), `eV/A` (force), etc. In Rust doc comments and Python docstrings use `Å³`, `e/Å³`, `eV/Å` with the standard Å character.
- **No single-letter or concatenated variable names!** Use proper snake_case: `idx` not `i`, `n_images` not `nimages`, `f_max` not `fmax`, `col_idx` not `colidx`
- **No fallbacks or backward-compatible interfaces** unless explicitly told. Throw an error or fail early—silent catches, default shims, and compatibility wrappers mask bugs.
- Remove dead code aggressively. Prefer a clean codebase over deprecation.
- Log useful context with errors—include relevant variable values
- Ask before adding new dependencies.
- Prefer editing existing files over creating new ones.
- Keep existing comments when editing files unless they are stale or low value.
- Use single-line section headers: `// === Section Name ===` not verbose multi-line box comments
- Never create or commit lock files (no `uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `deno.lock`, etc.)
- **Never commit handover docs, temp data files, or proof-of-concept artifacts** (no `HANDOVER.md`, sample `.jsonl`/`.lmdb` files, exploratory notebooks, etc.). These clutter the monorepo — keep them local or in `tmp/`.
- Use `prek` (Rust port), never `pre-commit` (Python)
- **Never take an unrequested irreversible or externally-visible action** — opening PRs/issues, pushing branches, deleting remote refs, posting to Slack, commenting on GitHub. When a task stalls, report and ask; don't improvise a workaround that creates something the user has to undo.
- Run commands yourself to collect logs/errors—don't ask the user. Run tests (`pytest`, `vitest`, `playwright`) or scripts, start dev servers, visit pages in browser, take actions to reproduce issues.
- When fixing a bug or making a behavior tweak, ALWAYS add or update a unit test that would have caught it. Prefer extending an existing related test over creating a new test to avoid extra setup/teardown bloat. Only create a new test when there is no related test to extend.

## Response shape

Optimize replies for scanning. The reader should get the answer from the first line and know what's next from the last.

- Lead with the answer. When it's a command, path, or `file:line`, put that literal thing in the first line and explain after.
- Number multi-step instructions, one bounded action per step. Fold trivial steps into their neighbor.
- Rank list items by what matters most. When a list runs long, split it into "do now" vs "later" rather than leaving it flat.
- Finish one thing before raising the next. Park new issues as concise questions at the end, never mid-answer.
- Report errors matter-of-factly: location, cause, fix. Never "oh no"/"there seems to be a problem"/...
- When work is done, say what now works and give the command to see it: "Login works with magic links. Try `npm run dev`, open `/login`."
