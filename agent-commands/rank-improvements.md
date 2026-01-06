# Rank Improvement Ideas

## Goal

Inspect current branch or uncommitted changes and produce a prioritized list of improvement opportunities. Read-only analysis—no changes applied.

## Scope

Analyze whichever is present (check in order):

1. Uncommitted changes (`git diff` + untracked files)
2. Branch diff from `main` (`git diff main...HEAD`)
3. If nothing found, ask what to analyze

## Steps

1. **Gather:** Collect all relevant code changes
2. **Analyze:** Review for improvement opportunities across these categories:
   - **Bugs/Correctness** - Logic errors, edge cases, race conditions
   - **Robustness** - Error handling, input validation, defensive coding
   - **Simplification** - Verbose patterns, unnecessary abstractions, dead code
   - **Performance** - Inefficient algorithms, redundant operations, N+1 patterns
   - **Readability** - Naming, structure, missing types/docs
   - **Maintainability** - DRY violations, tight coupling, missing tests
3. **Rank:** Order findings by priority using this framework:
   - **Critical** - Will cause bugs or data loss in production
   - **High** - Significant improvement to correctness or maintainability
   - **Medium** - Meaningful cleanup or robustness gain
   - **Low** - Nice-to-have polish, minor style improvements

## Output Format

```text
## Critical
1. [file:line] Brief description of issue and suggested fix

## High
1. ...

## Medium
1. ...

## Low
1. ...
```

Omit empty priority levels. For each item, include:

- File and line reference
- One-line problem description
- Concrete suggestion (not vague advice)

## Rules

- **Read-only:** Do not modify any files
- **Actionable:** Every item must have a clear fix, not just "consider improving"
- **Honest ranking:** Don't inflate priority to seem thorough; empty sections are fine
- **Stay scoped:** Only analyze the changed code, not the entire codebase

## Outcome

A prioritized punch list the user can work through or hand back to the agent to implement.
