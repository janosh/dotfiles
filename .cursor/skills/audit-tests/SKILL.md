---
name: audit-tests
description: Audit tests for low-value coverage and rank improvements or deletions. Use for read-only test quality review.
---

# Audit Tests

## When to use

- Test suite feels noisy, brittle, or low signal
- You want a prioritized cleanup plan before editing tests

## Instructions

1. Review tests in the requested scope.
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

## Rules

- Read-only analysis unless user explicitly asks for edits
- Keep recommendations specific and actionable
- Preserve valid test intent when suggesting deletion
