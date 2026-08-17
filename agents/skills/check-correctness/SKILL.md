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
   - Use the uncommitted diff when the tree is dirty; otherwise use the branch diff vs `main`
   - Do not expand a small uncommitted diff into a branch review unless the user asks or the local change is inseparable from unreviewed branch commits
   - Use `distribute` when requested or when independent feature/directory reviews justify one read-only parallel layer; otherwise review directly. Aggregate findings and apply fixes yourself; explain any requested fallback
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
   - Prefer red-then-green when the fix is not yet applied. If it is already present and red evidence still matters, mutate only the relevant lines with a patch or in an isolated worktree, then undo the mutation and confirm the test passes on the restored code; never stash, reset, restore, or check out a mixed dirty tree. Use `verify-tests` only when assertion strength remains doubtful
   - After the fix batch, run the narrowest affected tests once and confirm they pass
6. Report what you changed with proof:
   - Breaking input
   - Expected vs actual behavior
   - Fix summary and test coverage added

## Rules

- Focus on demonstrable issues, not abstract concerns
- Directly fix every confirmed issue within scope, including small or rare edge-case bugs
- Add regression coverage whenever feasible for each fix
- If no bugs found, state what was tested and residual risk
