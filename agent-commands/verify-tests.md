# Verify Tests via Mutation

## Goal

Verify robustness of current tests by introducing breaking changes (mutations) and ensuring tests catch them.

## Steps

1. **Identify target:** Look at code you just added or fixed.
2. **Inject mutations:** Introduce one breaking change at a time.
3. **Run tests:** Check if tests fail.
   - **Tests pass (Bad):** Tests are insufficient—improve assertions or add cases.
   - **Tests fail (Good):** Tests caught the bug.
4. **Revert:** Remove the mutation.
5. **Repeat:** Try different mutation types until confident in coverage.
6. **Final check:** Ensure all tests pass with original code.

## Rules

- One mutation at a time—revert before trying the next
- prioritize mutations on recently changed code but if see a likely areas of low/no coverage, also a good target.
- Prefer improving existing tests with more assertions over adding new test files or functions unless genuinely testing a new scenario.
- Make tests no more verbose than necessary to get robust (non-flaky) and strict coverage.
