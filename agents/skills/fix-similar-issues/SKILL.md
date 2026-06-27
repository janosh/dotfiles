---
name: fix-similar-issues
description: Find and fix related variants of a recently fixed issue across the codebase. Use after resolving a bug or anti-pattern.
---

# Fix Similar Issues

## When to use

- You just fixed one issue and want broad consistency
- The same root cause may exist in multiple files

## Instructions

1. Generalize the root pattern of the original issue.
2. Search for exact and conceptual variants across the repo.
3. Search serially by default; when variants span many files / several packages, fan out subagents partitioned by area (one layer) to apply the generalized fix from step 1 in parallel — disjoint partitions, no shared files. Run one aggregated verification afterward.
4. Apply fixes consistently.
5. If repeated 3+ times, consider shared abstraction only when it improves clarity.
6. Run tests to guard against regressions.

## Rules

- Be thorough, not just text-match based
- Avoid over-abstraction when call sites differ materially
- Preserve behavior while normalizing fixes
