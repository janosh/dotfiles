---
name: audit-tests
description: Audit test files or directories for low-value coverage; simplify, fold duplicates, and delete only demonstrably redundant tests while preserving behavioral coverage. Use for test-suite cleanup.
---

# Audit Tests

## Workflow

1. Inspect the production code, related tests, and shared fixtures to identify the behaviors and failure modes each test protects.
2. Simplify first: parameterize repeated cases, fold related assertions, and remove duplicated setup or helpers. Before keeping a standalone test, search nearby tests for the same behavior and setup; fold it only when readability, intent, and failure clarity remain strong.
3. Identify only trivial, vacuous, implementation-only, or truly duplicate tests as deletion candidates. A named retained test must cover the same behavior and failure mode at the same or deeper integration level; otherwise keep the candidate. Keep candidates whose current pass/fail status is unknown until step 4.
4. Batch simplifications and run the narrowest affected tests once with unknown-status deletion candidates still present. Delete only candidates that passed in this run and satisfy step 3; if deletion changes fixtures, helpers, or collection behavior, verify that affected behavior afterward.
5. When coverage will decide a specific deletion, measure affected-file coverage with that candidate present and again with it removed, and reject a drop you cannot explain. Otherwise collect coverage only when project thresholds require it after the edit batch, and reject threshold failures. Mutation-check only deletion of sole regression, edge, or error-path coverage.
6. Escalate to a broader suite, lint, or type checks only when edits affect shared fixtures/helpers or cross-cutting behavior.

## Scope handling

- Use `distribute` when requested or when file-disjoint partitions with no shared edited fixtures or helpers justify one layer; otherwise work directly. The parent owns shared changes and aggregate verification. Explain any requested fallback.

## Report

- Summarize deletions, the retained behavior that justifies them, checks run, and uncertain candidates.

## Rules

- Distinct edge/error inputs and different test genres are not duplicates.
- Preserve snapshot, property, generated, integration/e2e, and skip/xfail/slow semantics.
- Coverage supports judgment but neither proves equivalence nor justifies a test by itself.
