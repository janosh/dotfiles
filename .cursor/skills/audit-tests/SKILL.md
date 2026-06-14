---
name: audit-tests
description: Audit tests for low-value coverage, apply the clear fixes/deletions, and rank the rest. Use for test-suite cleanup.
---

# Audit Tests

## When to use

- Test suite feels noisy, brittle, or low signal
- You want a prioritized cleanup plan before editing tests

## Instructions

1. Review tests in the requested scope. Serial by default; only when clearly large (roughly 5+ test files or several dirs) fan out subagents partitioned by file/dir (one layer, no nesting) that apply their own file-local cleanups in parallel — partitions must be disjoint so no two ever edit the same file. Handle shared fixtures/conftest and cross-file consolidation yourself.
2. Identify low-value patterns:
   - Trivial assertions
   - Duplicative coverage
   - Brittle implementation coupling
   - "Does not throw" only checks
   - Over-mocking that hides behavior
3. Rank by impact and ease of improvement.
4. For each item, provide:
   - Why it is low value
   - `Improve` or `Delete`
   - Concrete replacement guidance
5. Apply clear, low-risk improvements directly. Only delete a test after confirming its coverage is redundant or folded into a stronger one (run the focused suite before/after); report deletions that aren't clearly safe and any uncertain-intent items for the user to confirm.

## Rules

- Auto-apply confident fixes/deletions; escalate only uncertain-intent cases
- Keep recommendations specific and actionable
- Preserve valid test intent when suggesting deletion
