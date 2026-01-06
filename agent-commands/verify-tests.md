# Verify Tests via Mutation

## Goal

Verify the robustness of current tests by manually introducing breaking changes (mutation testing) and ensuring tests fail.

## Steps

1. **Analyze recent changes:** Look at the code you just added or fixed.
2. **Inject defects:** Introduce temporary breaking changes or bugs into that logic.
3. **Run tests:** Check if existing tests catch the bug (fail).
    - **If tests pass (Bad):** The tests are insufficient. Improve them or add new cases until they fail.
    - **If tests fail (Good):** The tests are doing their job.
4. **Revert defects:** Remove the temporary breaking changes.
5. **Final verification:** Ensure all tests pass again.

## Guidelines

- Prefer improving assertions in existing tests over adding many new test files.
- Keep tests concise.
