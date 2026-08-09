---
name: simplify-tests
description: Refactor tests to be clearer and more concise while preserving coverage. Use when tests are verbose or repetitive.
---

# Simplify Tests

## When to use

- Tests pass but are hard to read or maintain
- Similar test cases can be parameterized

## Instructions

1. Refactor for clarity:
   - Parameterize repeated cases
   - Remove unnecessary setup and helper duplication
   - Clarify Arrange-Act-Assert flow
2. Before keeping a new test file or function, search nearby tests for the same module, behavior, and setup. Fold it with parameterization or related assertions when readability, intent, failure clarity, and test speed remain strong; keep distinct behavior or setup standalone.
3. Keep behavior checks intact and confirm no cases were dropped while parameterizing.
4. Run the narrowest affected tests once after the edit batch.

## Scope handling

- Work serially by default. Parallelize only when partitions are file-disjoint, share no fixtures or helpers being edited, and serial execution is clearly slower; the parent owns shared changes and one aggregated verification.

## Rules

- Preserve effective coverage
- Prefer readability over clever abstractions
- Accept only minor performance tradeoffs for substantially clearer tests
