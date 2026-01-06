# Audit Tests

## Goal

Identify low-value tests that offer little defense against regressions. Rank them for improvement or deletion.

## Steps

1. **Scan:** Review all tests in the codebase (or specified scope).
2. **Identify low-value tests:**
   - Tests that only check trivial/obvious behavior
   - Tests that duplicate coverage from other tests
   - Tests that are tightly coupled to implementation details (brittle)
   - Tests with weak assertions (e.g., just checking something doesn't throw)
   - Tests that mock so heavily they don't test real behavior
   - Snapshot tests of unstable/frequently changing output
3. **Rank:** Order by priority (highest = worst offenders, easiest wins).
4. **For each test, provide:**
   - Why it's low value (one line)
   - Recommendation: **Improve** (with concrete suggestion) or **Delete** (with rationale)
   - If deleting: suggest a `# TODO: test X behavior` comment if the intent was valid but execution poor

## Output Format

```text
## High Priority

1. `test_foo_returns_value` (test_utils.py:42)
   - Problem: Only checks return type, not correctness
   - Action: Improve—add assertions for expected values with edge cases

2. `test_component_renders` (Component.test.ts:15)
   - Problem: Checks component mounts without errors, no behavioral assertions
   - Action: Delete—covered by integration tests; add `// TODO: test error state rendering`

## Medium Priority
...
```

## Rules

- **Be specific:** Vague "improve this" isn't helpful—say exactly what to add/change.
- **Consider ROI:** If improving a test requires major refactoring, deletion may be better.
- **Preserve intent:** If a test had a valid goal but poor execution, note what should be tested.
- **Don't over-delete:** Some simple tests are fine if they cover real edge cases.
