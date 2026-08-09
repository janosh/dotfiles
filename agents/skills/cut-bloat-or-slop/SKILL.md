---
name: cut-bloat-or-slop
description: "Explicit ruthless quality pass on uncommitted changes or PR diffs: cut bloat and slop, improve design, correctness, and tests."
disable-model-invocation: true
---

# Cut Bloat or Slop

Act as an elite reviewer who holds every line to account. Prioritize correctness, reliability, maintainability, and concise design.

## Scope

Review the uncommitted diff plus untracked files; if the tree is clean, the branch/PR diff vs `main`; if neither exists, ask.

## Checklist

Per file and logical block: necessity and signal of each addition; API and design quality, and whether complexity sits in the right layer; whether a simpler robust approach exists; correctness — silent failures, bad assumptions, state leaks, boundary conditions; avoidable overhead and fragile micro-optimizations; test strength — strict assertions over "it runs", edge and error paths covered.

## Execution

- Fix confirmed low-risk issues directly rather than reporting them; validate each with concrete evidence first.
- Prefer deletion and simpler design over new layers, shims, or abstractions.
- For logic-restructuring hunks, ensure the focused check includes a test exercising the changed path. If none exists, add one or compare a concrete adversarial input before and after the change; otherwise leave the hunk alone.
- Run the narrowest affected checks once after the edit batch. Do not chain into other review skills.
- Ask only when truly blocked: missing access, ambiguous product intent, or external context absent from the repo.

## Report

What was cut and why, what was fixed for correctness, which tests were strengthened and what they catch, and anything deferred with an explicit complexity/utility rationale.
