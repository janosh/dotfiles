# Simplify Tests (Preserve Coverage)

## Goal

Improve test quality by making them more concise, readable, and maintainable while preserving all coverage.

## Steps

1. **Baseline:** Run tests to confirm they pass and measure current coverage/performance.
2. **Refactor:**
   - **Parameterize:** Identify similar test functions and combine using `test.each` (or equivalent) for different inputs/edge cases
   - **Simplify:** Remove verbose setup, helper redundancy, or overly complex assertions
   - **Clean up:** Delete low-quality, boilerplate tests that add no value
   - **Clarify:** Ensure "Arrange-Act-Assert" flow is clear
3. **Verify:** Run tests again to ensure they pass and coverage hasn't regressed.

## Rules

- **Zero Coverage Loss:** Do not drop any valid test cases
- **Readability First:** Clear, concise tests are better than clever ones
- **Minor performance regressions acceptable** if readability improves significantly
