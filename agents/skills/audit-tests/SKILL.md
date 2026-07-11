---
name: audit-tests
description: Audit test files or directories for low-value coverage; simplify, fold duplicates, and delete only demonstrably redundant tests while preserving behavioral coverage. Use for test-suite cleanup.
---

# Audit Tests

## Workflow

1. Run the narrowest scoped tests. Fix clear defects; ask only when intended behavior is ambiguous. Audit from a green baseline.
2. Inspect the production code, related tests, and shared fixtures. If existing coverage will help judge deletions, record affected-file line/branch coverage without adding tooling.
3. Simplify first: parameterize repeated cases, fold related assertions, and remove duplicated setup or helpers.
4. Delete only trivial, vacuous, implementation-only, or truly duplicate tests. A named retained test must cover the same behavior and failure mode at the same or deeper integration level; otherwise keep the candidate.
5. Batch low-risk edits and run the narrowest affected tests once. Run the full scoped suite, lint, and type checks once at the end.
6. Repeat coverage only when cases or paths were removed. Reject threshold failures or unexplained affected-file drops. Mutation-check only deletion of sole regression, edge, or error-path coverage.

## Scope handling

- Work serially for small scopes. For 5+ independent files, delegate disjoint file-local edits; the parent owns shared changes and final verification.

## Report

- Summarize edits, retained coverage for deletions, checks run, coverage changes, and uncertain candidates.

## Rules

- Distinct edge/error inputs and different test genres are not duplicates.
- Preserve snapshot, property, generated, integration/e2e, and skip/xfail/slow semantics.
- Coverage supports judgment but neither proves equivalence nor justifies a test by itself.
