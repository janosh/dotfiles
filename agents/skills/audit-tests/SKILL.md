---
name: audit-tests
description: "Simplify, fold and audit tests while preserving behavioral coverage: parameterize repeats, fold new standalone tests into related ones, delete only demonstrably redundant tests. Use after adding tests, when tests are verbose or repetitive, or for test-suite cleanup. Modifier: distribute."
---

# Audit Tests

## Workflow

1. Inspect the production code, related tests, and shared fixtures to identify the behaviors and failure modes each test protects.
2. Simplify first: parameterize repeated cases, remove duplicated setup or helpers, and clarify Arrange-Act-Assert flow. Prefer readability over clever abstractions; accept only minor speed costs for substantially clearer tests.
3. Fold: before keeping a standalone test file or function, search nearby tests for the same module, function, fixture setup, or behavior. Fold via `pytest.mark.parametrize`, `test.each`/`it.each`, table cases, or an added assertion, with clear case IDs. Keep it standalone when it covers distinct behavior, needs different setup, would require awkward branching, weakens failure messages, mixes unrelated assertions, or makes fast tests depend on slow setup. Preserve every folded case.
4. Identify only trivial, vacuous, implementation-only, or truly duplicate tests as deletion candidates. A named retained test must cover the same behavior and failure mode at the same or deeper integration level; otherwise keep the candidate. Keep candidates whose current pass/fail status is unknown until step 5.
5. Batch edits and run the narrowest affected tests once with unknown-status deletion candidates still present. Delete only candidates that passed in this run and satisfy step 4; if deletion changes fixtures, helpers, or collection behavior, verify that affected behavior afterward.
6. When coverage will decide a specific deletion, measure affected-file coverage with that candidate present and again with it removed, and reject a drop you cannot explain. Otherwise collect coverage only when project thresholds require it after the edit batch, and reject threshold failures. Mutation-check only deletion of sole regression, edge, or error-path coverage.
7. Escalate to a broader suite, lint, or type checks only when edits affect shared fixtures/helpers or cross-cutting behavior.
8. Report folds, deletions with the retained behavior that justifies them, checks run, and uncertain candidates.

Supports `distribute`; partitions must be file-disjoint with no shared edited fixtures or helpers.

## Rules

- Distinct edge/error inputs and different test genres are not duplicates.
- Preserve snapshot, property, generated, integration/e2e, and skip/xfail/slow semantics.
- Coverage supports judgment but neither proves equivalence nor justifies a test by itself.
