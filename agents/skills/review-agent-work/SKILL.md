---
name: review-agent-work
description: Adversarially review another agent's code against its plan. Use to verify plan.md completion or audit recent code for correctness, bloat, and test gaps.
---

# Review Agent Work

## Instructions

Review in read-only mode unless the user explicitly asks for fixes.

Start by establishing scope from `git status`, relevant diffs, recent commits, `plan.md`/handoff notes, and user-provided context. Treat unrelated dirty files as out of scope.

Treat the plan as a checklist, but do not assume it was complete or correct. Verify every goal and todo was addressed, and separately flag missing requirements the plan overlooked.

Review correctness first. Look for concrete break cases, bad assumptions, edge cases, state/side-effect bugs, integration mismatches, and error handling holes.

Then review conciseness and code quality. Call out bloat, redundant abstractions, compatibility shims, dead code, over-defensive fallbacks, or helpers that do not earn their keep.

Review tests last. Identify missing regression coverage, weak assertions, untested edge/error paths, duplicated setup, and cases that should be folded into existing tests. Run focused tests/lints when cheap and relevant; otherwise state what was not verified.

Lead with actionable findings ordered by severity, with affected files/symbols, impact, and fix direction. If everything is complete, say so, but still report residual risks or test gaps.
