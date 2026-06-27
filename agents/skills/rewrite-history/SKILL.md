---
name: rewrite-history
description: Rebuild branch history into clean, logical commits with clear narrative and dependency ordering.
disable-model-invocation: true
---

# Rewrite History

## When to use

- User explicitly asks to clean up branch commit history

## Instructions

1. Understand final branch diff versus `main`.
2. Split work into atomic logical units (refactor, infra, core logic, tests, docs).
3. Recreate branch with commits ordered by dependency.
4. Ensure each commit is independently valid and reviewable.
5. Verify final functionality and tests match or improve original state.

## Rules

- Remove WIP/fixup noise from resulting history
- Keep each commit focused and rationale-driven
- Treat this as high-risk git workflow; proceed deliberately
