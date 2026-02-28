---
name: check-correctness
description: Hunt for concrete correctness bugs in changed code. Use for adversarial review of uncommitted or branch diffs.
---

# Check Code Correctness

## When to use

- Before commit/PR to catch subtle bugs
- After major refactors or risky logic changes

## Instructions

1. Determine scope:
   - Use uncommitted diff by default
   - If tiny, review branch diff vs `main`
2. Search for concrete break cases with real inputs.
3. Prioritize:
   - Silent wrong results
   - State mutation and side effects
   - Broken assumptions and edge cases
4. Verify and fix issues directly:
   - Confirm each issue yourself with concrete evidence before changing code
   - Do not ask the user to validate issues you can verify independently
   - Ask for user input only when blocked by missing access, ambiguous product intent, or external context you cannot derive
   - Apply the smallest correct fix
   - Do not defer small bugs or rare edge cases
   - Keep behavior-focused, low-risk changes
5. Add or strengthen tests where possible:
   - Cover the failing input or edge case that exposed the issue
   - Prefer concise, strict assertions that would catch regressions
6. Report what you changed with proof:
   - Breaking input
   - Expected vs actual behavior
   - Fix summary and test coverage added

## Rules

- Focus on demonstrable issues, not abstract concerns
- Directly fix every confirmed issue within scope, including small or rare edge-case bugs
- Add regression coverage whenever feasible for each fix
- If no bugs found, state what was tested and residual risk
