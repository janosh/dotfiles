# Rewrite History

## Goal

Re-implement the current branch as if you had perfect foresight. Create an ideal commit history that tells a clear narrative—the commits you *would* have made if you knew the final solution from the start.

## Context

Real development is messy: false starts, debugging commits, "oops forgot this", fixups, and interleaved concerns. This command produces a clean history that's easy to review, bisect, and understand months later.

## Steps

1. **Understand end state:** Review the full diff (`git diff main`) to understand what the branch accomplishes.
2. **Identify logical units:** Break the changes into atomic, self-contained pieces:
   - Refactoring (no behavior change)
   - Infrastructure/setup (new files, dependencies, config)
   - Core implementation (the actual feature/fix)
   - Tests
   - Documentation/cleanup
3. **Order by dependency:** Determine the ideal sequence—what must exist before what?
4. **Create new branch:** `git checkout main && git checkout -b <branch>-clean`
5. **Replay commits:** Implement each logical unit as one clean commit:
   - Each commit should compile/pass tests independently
   - Each commit should be reviewable in isolation
   - Commit message explains *why*, not just *what*
6. **Improve along the way:** If you spot cleanup opportunities while rewriting—dead code, better names, simpler logic—take them. Don't just reproduce the original.
7. **Verify:** Ensure final functionality is equivalent or better. Run tests.

## Commit Sequencing Principles

| Order | Type                 | Example                                                       |
| ----- | -------------------- | ------------------------------------------------------------- |
| 1     | Mechanical refactors | Rename files, extract functions, move code (no logic changes) |
| 2     | Infrastructure       | Add dependencies, config, types, interfaces                   |
| 3     | Core logic           | The actual feature implementation                             |
| 4     | Edge cases           | Error handling, null checks, validation                       |
| 5     | Tests                | Unit tests, integration tests                                 |
| 6     | Polish               | Comments, docs, cleanup                                       |

## What to Eliminate

- "WIP", "fixup", "oops" commits
- Commits that add then immediately modify the same code
- Debugging code that got removed
- Back-and-forth refactoring (just show final form)
- Interleaved unrelated changes

## Commit Message Format

```text
Short summary (imperative, ≤50 chars)

Why this change is needed and any non-obvious decisions.
Keep it brief—the diff shows what, the message explains why.
```

## Outcome

A branch with equivalent (or cleaner) changes and a commit history that reads like a tutorial—each step logical, minimal, and purposeful.
