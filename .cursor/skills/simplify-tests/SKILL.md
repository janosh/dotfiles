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
2. Refactor for clarity:
   - Parameterize repeated cases
   - Remove unnecessary setup and helper duplication
   - Clarify Arrange-Act-Assert flow
3. Keep behavior checks intact.
4. Re-run tests and confirm no coverage regression.

## Rules

- Preserve effective coverage
- Prefer readability over clever abstractions
- Accept only minor performance tradeoffs for substantially clearer tests
