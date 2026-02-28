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
4. Provide findings with proof:
   - Breaking input
   - Expected vs actual behavior
   - One-line fix direction

## Rules

- Focus on demonstrable issues, not abstract concerns
- If no bugs found, state what was tested and residual risk
