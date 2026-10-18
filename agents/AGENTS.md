# Global Agent Instructions

These rules apply to all projects.

## Correctness (don't bullshit)

- **Equivalence is measured, not read.** To claim two implementations match, run both on identical inputs (representative *and* edge cases) and paste `max |a-b|` and max relative error. Never pronounce on equivalence from reading the code.
- **Round-off has a size, compute it.** Never wave off a numerical mismatch as "floating-point", "round-off", "precision", or "tolerance" without computing the actual error and comparing to machine eps for the dtype (f64 ≈ 2.2e-16, f32 ≈ 1.2e-7). Bisect it: compare intermediate values, not just final outputs, and locate the first step where the paths diverge.
- **Compare with explicit, justified tolerances.** Use `np.testing.assert_allclose(rtol=..., atol=...)` with values you chose deliberately (not defaults). For "bit-identical" claims use exact equality. Pin seeds before comparing stochastic outputs.
- **Verify before claiming.** Read relevant implementations and callees, distinguish observed results from inference, and never report unrun checks as passing.

## Multi-agent branch sharing

Multiple agents may work on the same branch concurrently. Editing a file that already has uncommitted changes from another agent is fine, don't be timid, except at git time: when staging and committing. Don't stage changes unless asked to commit. Include only the changes relevant to your task and use explicit `git add <your-files>` instead of `git add -A` so you don't commit, revert, or stash another agent's out-of-scope work. Only exception being if other agent's work looks related or too menial to warrant its own commit, then just include in your commit.

Work in the main checkout by default. Create a new worktree only when the user asks for one, or when your work would clash with another agent's in a way that signaling them can't resolve (rare). Worktree proliferation costs build targets, disk and cleanup passes: avoid it.

Skills that say they support `distribute`: use it when the user asks, or when independent, file-disjoint slices (features, directories, comment threads) justify one parallel subagent layer; otherwise work directly. Subagents read, or edit only their assigned disjoint paths. The parent verifies and aggregates their findings, owns shared files and every external write (commits, pushes, PR replies), and runs the aggregate checks. If `distribute` was requested but no safe split exists, say so and work directly.

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
- **In `notebooks/`, prefer pymatviz widgets** instead: `BarPlotWidget`, `HeatmapMatrixWidget`, `HistogramWidget`, `ScatterPlotWidget`, `StructureWidget`, `ConvexHullWidget`, `TrajectoryWidget`, `PhaseDiagramWidget`, etc. over `plotly` or `matplotlib` figures. Check existing demos/notebooks for usage and API patterns before writing new visualization code.
- avoid `typing.cast` unless absolutely necessary

## TypeScript/Svelte Projects (*.ts,*.svelte)

- Use snake_case for variables and functions, not camelCase
- Prefer backticks to single or double quotes, except inside TypeScript type definitions
- Use `it.each([...])` and `test.each([...])` for parameterized vitest tests
- Never use `/**` or `/* */` for docs (JSDoc/TSDoc included). Always `//`, with consecutive `//` lines for multi-line notes. Reserve `/* */` for CSS and tool pragmas (`eslint-disable`, etc.)
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
- Use `SvelteSet`/`SvelteMap` only where the collection is UI state that templates or effects must react to; plain `Set`/`Map` for constant lookup tables, function-local scratch and non-reactive bookkeeping (timers, caches)

## Git & GitHub CLI

- Git editor is `code --wait`, so interactive commands hang. Override it with a `sed` script instead, e.g. `GIT_EDITOR="sed -i '' 's/pick/squash/2'" git rebase -i HEAD~n`.
- If `gh` commands fail with auth errors (e.g. "Unauthorized"), try switching accounts: `gh auth switch` (don't ask permission for this, just do)
- Don't commit without being asked
- Never add `Co-authored-by: Cursor/Codex/...` or similar to commit messages
- Never `git push --force/--force-with-lease` unless explicitly asked for that specific branch and situation. Once work is pushed, prefer follow-up commits over amending/rebasing.
- A request to submit or open a PR authorizes publishing its branch and creating the PR without another confirmation. When asked to "draft" an issue or PR, output the title and body as markdown for review — don't run `gh` until explicitly told to post.
- **Concurrent branch updates are routine:** If an authorized push is rejected because the destination branch advanced (non-fast-forward), fetch and rebase onto the updated destination branch, resolve conflicts, run focused checks for affected code, and retry the push without asking. Preserve both local and remote commits; do not force-push or change the destination branch.
- **Never toggle a PR's auto-merge unasked.** Don't disable it to push follow-up commits and don't re-enable it afterwards: a push to an auto-merging PR is fine, since auto-merge waits for the new head's checks. Change it only when the user asks for that specific PR.
- **Refresh PR metadata when a push grows its scope.** After pushing work that a PR's title and body don't yet describe (a new feature, component, fix sweep, or breaking change, not a CI fix or review tweak), run `/update-pr-metadata` on that PR unasked so its title, body and labels match what it now ships.
- **Permission to commit is never permission to open a PR**, and neither is a blocked push. If a push is rejected by branch protection, required status checks, or a ruleset, stop and report that policy block. Do NOT bypass it by moving the commit to a new branch and opening a PR. Leave the commit local and let the user choose how to land it.
- Create an upstream (publish a new branch) only when asked, e.g. via `submit-pr`; that request needs no separate confirmation. Otherwise never push a branch that has no upstream. Verify the destination with `git push --dry-run`. For an existing fork PR, push to its actual head repository and branch rather than creating an unrelated branch on `origin`.
- Asking a question mid-task and getting an answer authorizes only what was asked. When the plan turns out not to work, ask again. Don't substitute a different action you think is equivalent.

## CRITICAL: Protect Uncommitted Work

**NEVER run `git reset`, `git checkout -- <path>`, `git restore`, `git stash`, or `git clean` on modified/untracked files without explicit user approval!** Multiple agents work on the same repo concurrently, so these can silently destroy another agent's in-progress work, including in files you didn't modify. Always ask before discarding anything.

- If you need a clean working tree for your task, use `git worktree add` instead of stashing
- Check with `ls -la` and `file <path>` before deleting—directories may be symlinks to working copies

## General

- Never mention private repository or project names in another repository's code, docs, tests, fixtures, commit messages, or PR metadata unless the user explicitly asks; always confirm with the user first when that authorization is absent.
- **GPU speed tests on the clusters:** always submit with `--qos=normal` (authorized 2026-09-04, including preempting preemptible jobs; don't ask again). Single-GPU H200 tests on cw1 go to `--partition=h200-shared --qos=normal`; `h100` also accepts normal QoS, plain `h200` only preemptible. Submit with normal QoS directly: a preemptible job can't be moved into a normal shared partition later. Record the actual GPU, and keep each before/after or Rust/reference timing pair within one allocation.
- **Units notation**: never use `ų` or other obscure Unicode glyphs for units. Write `A^3` (cubic angstrom), `e/A^3` (electron density), `eV/A` (force), etc. In Rust doc comments and Python docstrings use `Å³`, `e/Å³`, `eV/Å` with the standard Å character.
- **No single-letter or concatenated variable names!** Use proper snake_case: `idx` not `i`, `n_images` not `nimages`, `f_max` not `fmax`, `col_idx` not `colidx`
- **No fallbacks or backward-compatible interfaces** unless explicitly told. Throw an error or fail early—silent catches, default shims, and compatibility wrappers mask bugs. This is about software-engineering fallbacks (swallowed errors, legacy code paths, defaults that hide a broken input or call). It does not forbid scientific fallbacks: when a physical estimate is uncertain (e.g. no confident oxidation-state assignment for a MAGMOM seed), falling back to the next-best physical default is correct, as long as the result records which path was taken (audit field, log line) so it stays visible.
- Remove dead code aggressively. Prefer a clean codebase over deprecation.
- Log useful context with errors—include relevant variable values
- Ask before adding new dependencies.
- For my own upstream packages (e.g. `svelte-widgets` and `matterviz`), always track the upstream repository's latest `main` branch. Adapt consuming code to breaking API changes instead of pinning older commits or releases, downgrading, or adding compatibility fallbacks.
- Prefer editing existing files over creating new ones.
- Never write large files into iCloud Drive or iCloud-synced folders such as `~/Documents` and `~/Desktop`; use an unsynced location such as `~/Movies` for videos or `/tmp` for temporary files.
- Prefer fast Rust CLIs over stock Unix tools when available: `fd` over `find`, `dust` over `du`, `rg` over `grep`, and `bat` over `cat`.
- Keep existing comments when editing files unless they are stale or low value.
- Use single-line section headers: `// === Section Name ===` not verbose multi-line box comments
- **Never hard-wrap markdown.** There is no max line length: write each paragraph and list item as one long line and let the renderer wrap it. Reflowing prose to a column makes later edits produce noisy diffs. The only exception is inside code fences, where line breaks are content. This applies to prose you write for humans too, e.g. Slack messages, PR descriptions, commit bodies.
- **Always link issues, PRs and commit SHAs** in markdown and in message drafts (Slack, email, PR bodies): `[owner/repo#123](https://github.com/owner/repo/pull/123)`, `` [`e7b2128`](https://github.com/owner/repo/commit/e7b2128) ``, never a bare `#123` or SHA. Where the host has no per-commit URL (e.g. Overleaf), link the closest page (the project) and keep the SHA visible.
- Never add an `Unreleased` section to a changelog unless the user explicitly asks for one.
- Never create or commit package-manager artifacts: lock files (`uv.lock`, `pnpm-lock.yaml`, `package-lock.json`, `deno.lock`, etc.) or metadata such as `pnpm-workspace.yaml`. Prefer `uv run --no-project` (or keep `UV_FROZEN=1` / `UV_NO_SYNC=1`); do not run `uv lock` / `uv sync` in repos that omit a lockfile.
- **Never commit handover docs, temp data files, or proof-of-concept artifacts** (no `HANDOVER.md`, sample `.jsonl`/`.lmdb` files, exploratory notebooks, etc.). These clutter the monorepo — keep them local or in `tmp/`.
- Use `prek` (Rust port), never `pre-commit` (Python)
- **Never take an unrequested irreversible or externally-visible action** — opening PRs/issues, pushing branches, deleting remote refs, posting to Slack, commenting on GitHub. When a task stalls, report and ask; don't improvise a workaround that creates something the user has to undo. Exception: delete a remote branch you created yourself by mistake (e.g. a push that re-created a merged PR's deleted branch) without asking, once `git log <merged-head>..origin/<branch>` shows it holds only your own commits; then report it.
- Run commands yourself to collect logs/errors—don't ask the user. Run tests (`pytest`, `vitest`, `playwright`) or scripts, start dev servers, visit pages in browser, take actions to reproduce issues.
- **Avoid redundant verification.** Do not run tests solely to establish a green baseline. Batch edits and run the narrowest affected checks once after the batch. Reuse a same-session result only when it covered the path and nothing edited that path since. Escalate to broader suites, lint, types, coverage, or mutation checks only when the change's scope or risk warrants them. Workflows whose purpose is repeated failure testing, such as mutation checks, are exempt. Never run a large codebase's full suite by default: only when explicitly requested or when broad, cross-cutting changes cannot be validated otherwise.
- When you begin risky edits in a tree that is already dirty, capture its pre-edit diff first; you cannot reconstruct it later. If an unexpected failure cannot be attributed from the diff and control flow, diagnose it in a temporary worktree — never by stashing, resetting, restoring, or checking out files in the active tree. Compare the failing check on the clean base and on that base plus only your patch; where you captured a pre-edit diff, compare base plus that pre-existing patch against base plus both patches. Account for untracked inputs and missing build environments before attributing the failure.
- When fixing a bug or making a behavior tweak, ALWAYS add or update a unit test that would have caught it. Prefer extending an existing related test over creating a new test to avoid extra setup/teardown bloat. Only create a new test when there is no related test to extend.

## Response shape

Optimize replies for scanning. The reader should get the answer from the first line and know what's next from the last.

- Lead with the answer. When it's a command, path, or `file:line`, put that literal thing in the first line and explain after.
- Number multi-step instructions, one bounded action per step. Fold trivial steps into their neighbor.
- Rank list items by what matters most. When a list runs long, split it into "do now" vs "later" rather than leaving it flat.
- Finish one thing before raising the next. Park new issues as concise questions at the end, never mid-answer.
- Report errors matter-of-factly: location, cause, fix. Never "oh no"/"there seems to be a problem"/...
- When work is done, say what now works and give the command to see it: "Login works with magic links. Try `npm run dev`, open `/login`."
