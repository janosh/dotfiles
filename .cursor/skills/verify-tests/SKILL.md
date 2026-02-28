---
name: verify-tests
description: Validate test robustness using mutation-style checks. Use when you need evidence tests actually fail on real bugs.
---

# Verify Tests via Mutation

## When to use

- You suspect tests are too weak
- You want confidence that regressions are caught

## Instructions

1. Target recently changed code paths.
2. Introduce one deliberate breaking mutation at a time.
3. Run tests and inspect results:
   - If tests still pass, strengthen assertions or add cases
   - If tests fail, confirm failure is meaningful
4. Revert mutation before next trial.
5. Finish with original code and full passing suite.

## Rules

- One mutation at a time
- Prefer strengthening existing tests before adding many new ones
- Avoid leaving any intentional breakage behind
