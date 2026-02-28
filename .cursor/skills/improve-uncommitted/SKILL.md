---
name: improve-uncommitted
description: Review and improve uncommitted changes for robustness and clarity. Use before committing working tree changes.
---

# Improve Uncommitted Changes

## When to use

- Working directory contains edits that need hardening
- You want a cleanup/refactor pass pre-commit

## Instructions

1. Review all uncommitted changes for correctness, readability, and maintainability.
2. Rank opportunities by impact.
3. Apply confident fixes directly; batch unresolved questions at end.
4. Support `audit only` mode as read-only analysis.

## Rules

- Preserve behavior
- Prioritize high-impact improvements first
- Keep edits concise and targeted
