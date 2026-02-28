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
5. Run relevant tests to ensure behavior remains unchanged.

## Rules

- Preserve behavior
- Keep scope focused on changed areas unless user expands it
- Ask before deleting code with uncertain external usage
