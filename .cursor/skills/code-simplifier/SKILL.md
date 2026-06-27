---
name: code-simplifier
description: Simplify working code while preserving behavior. Use to remove bloat, duplication, and unnecessary complexity.
---

# Code Simplifier

## When to use

- Implementation works but is verbose or hard to maintain
- You want cleaner idiomatic code before merging

## Instructions

1. Review changed code for dead paths, duplication, and unnecessary abstraction.
2. Simplify control flow and reduce nesting where possible.
3. Improve naming and clarity with minimal edits.
4. Keep error handling robust but proportionate.
5. Verify behavior is preserved: run focused tests/lints. Only for risky logic changes (not mechanical cleanups) run a `check-correctness` pass on your diff.
6. When done, ensure your changes reduced net lines of code. If not, revert unless convinced the added lines improve code quality enough to earn their keep. But bias towards revert.

## Rules

- Preserve behavior
- Keep scope focused on changed areas unless user expands it
- Ask before deleting code with uncertain external usage
