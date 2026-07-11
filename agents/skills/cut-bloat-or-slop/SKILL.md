---
name: cut-bloat-or-slop
description: "Ruthless quality pass on uncommitted changes or PR diffs: cut bloat, improve design, raise correctness and tests."
disable-model-invocation: true
---

# Cut Bloat or Slop

## Reviewer stance

Act as an elite code reviewer with 10+ years in scientific computing and simulation codebases.
Prioritize correctness, reliability, maintainability, and concise design. Every line must earn its keep.

## When to use

- Before opening a PR, while changes are still uncommitted
- On an open PR before merge
- When code "works" but feels verbose, brittle, over-engineered, or low-signal

## Scope selection

Review in this order:

1. Uncommitted changes (`git diff` + untracked files)
2. If clean, full branch/PR diff against `main`
3. If neither exists, ask what scope to review

## Deep review checklist

For each file and logical block, check:

1. Necessity and signal
   - Is this addition justified?
   - Does each line materially improve behavior, correctness, or clarity?
2. API and design quality
   - Are interfaces minimal, coherent, and future-proof enough?
   - Is complexity placed in the right layer?
3. Implementation quality
   - Is it the simplest robust approach?
   - Is there a cleaner, lower-maintenance alternative with equal or better outcomes?
4. Correctness and edge cases
   - Silent failures, bad assumptions, state leaks, boundary conditions
5. Performance and scalability
   - Avoid avoidable overhead, unnecessary allocations, or fragile micro-optimizations
6. Test quality
   - Are tests meaningful and regression-catching?
   - Prefer strict assertions over "just runs without crashing"
   - Cover edge/error paths that are easy to regress

## Execution rules

- Default to fixing issues directly, not just reporting them.
- Prefer reductions in code size and conceptual complexity when behavior remains correct.
- Refactor aggressively when it clearly improves clarity and maintenance burden.
- Add or strengthen tests where practical for each meaningful fix.
- Verify changes locally (tests/lint/type checks as appropriate).
- After risky logic changes (not mechanical cleanups), run a `check-correctness` pass on your own diff; focused tests suffice for the rest.

## Escalation policy

- Validate issues yourself with concrete evidence before changing code.
- Ask the user only when truly blocked:
  - missing credentials/access
  - ambiguous product intent
  - external context unavailable from repo/runtime evidence

## Output expectations

When done, provide:

1. What was simplified/removed and why
2. What was fixed for correctness and why
3. Which tests were added/strengthened and what regressions they catch
4. Any intentionally deferred items with explicit complexity/utility rationale
