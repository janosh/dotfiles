---
name: add-tests
description: Add high-value tests for changed code. Use when implementing features or fixes and coverage needs to be added or strengthened.
---

# Add Tests

## When to use

- New or changed code lacks strict behavioral coverage
- Error paths and edge cases are not exercised
- You need to raise confidence before commit/PR

## Instructions

1. Identify changed code and enumerate behavior to test.
2. Check nearby or upstream tests for patterns worth reusing.
3. Write strict assertions:
   - Assert concrete values and structures
   - Cover boundaries, invalid inputs, empty/null variants
   - Verify expected exceptions and messages for error paths
4. Keep tests concise:
   - Use parameterization (`pytest.mark.parametrize`, `test.each`) for input matrices
   - Extract repeated setup into fixtures/helpers
5. Run tests and ensure new behavior is validated, not just execution.

## Rules

- Prefer behavior-focused tests over implementation-coupled tests
- Avoid weak assertions like `is not None` when stronger checks are possible
- Favor fewer strong tests over many low-value tests
