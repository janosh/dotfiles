---
name: simplify-tests
description: Refactor tests to be clearer and more concise while preserving coverage. Use when tests are verbose or repetitive.
---

# Simplify Tests

## When to use

- Tests pass but are hard to read or maintain
- Similar test cases can be parameterized

## Instructions

1. Establish baseline by running tests.
2. For a large suite (roughly 7+ test files), fan out subagents partitioned by file/dir (one layer, disjoint partitions) to refactor in parallel; keep shared-helper/fixture changes in the parent.
3. Refactor for clarity:
   - Parameterize repeated cases
   - Remove unnecessary setup and helper duplication
   - Clarify Arrange-Act-Assert flow
4. Keep behavior checks intact.
5. Re-run tests and confirm no coverage regression.

## Rules

- Preserve effective coverage
- Prefer readability over clever abstractions
- Accept only minor performance tradeoffs for substantially clearer tests
