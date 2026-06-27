---
name: fold-tests
description: Fold new standalone tests into existing related tests to cut setup duplication. Use after adding tests or spotting duplicated test setup/assertions.
---

# Fold Tests

## Instructions

When adding or reviewing tests, check whether a new standalone test can be folded into an existing related test.

Before keeping a new test file or function, search nearby tests for the same module, function, fixture setup, or behavior.

Prefer folding via `pytest.mark.parametrize`, `test.each`, `it.each`, table cases, or an added assertion when it preserves readability, intent, and failure clarity. Use clear case names/IDs for parameterized cases.

Keep the test standalone when it covers distinct behavior, needs different setup, would require awkward branching, weakens failure messages, mixes unrelated assertions, or makes fast tests depend on slow setup.

Preserve coverage and run the focused test target after refactoring.
