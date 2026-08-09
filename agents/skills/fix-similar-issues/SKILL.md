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
3. Search serially by default. Fan out one layer only when area partitions are disjoint, require substantial independent work, and serial execution clearly costs more than dispatch and aggregation; do not share edited files between agents.
4. Apply fixes consistently.
5. If repeated 3+ times, consider shared abstraction only when it improves clarity.
6. Run one aggregated focused verification after all fixes.

## Rules

- Be thorough, not just text-match based
- Avoid over-abstraction when call sites differ materially
- Preserve behavior while normalizing fixes
