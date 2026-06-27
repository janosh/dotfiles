---
name: commit
description: Stage and commit local changes in logical chunks with high-quality commit messages.
disable-model-invocation: true
---

# Commit Changes

## When to use

- User explicitly requests creating commit(s)

## Instructions

1. Review uncommitted diff and untracked files.
2. Group related edits into coherent commit units.
3. Stage appropriately (partial staging when necessary).
4. Write descriptive commit messages:
   - short imperative summary
   - optional body focused on rationale

## Rules

- Never commit unless user explicitly asks
- Exclude debug code and commented-out instrumentation
- Prefer fewer coherent commits over fragmented micro-commits
