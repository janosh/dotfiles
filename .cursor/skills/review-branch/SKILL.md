---
name: review-branch
description: Perform full branch review against main and propose high-impact fixes. Use for pre-PR quality review.
---

# Review Branch

## When to use

- Branch is ready for full review before PR
- You need architecture/correctness/style assessment across all branch changes

## Instructions

1. Inspect branch scope (`git log main..HEAD`, diff stats, full diff).
2. Review serially by default; only for a clearly large diff (roughly 7+ files or several subsystems) fan out read-only reviewer subagents (one layer, no nested fan-out), aggregate findings, and apply the fixes yourself.
3. Identify bugs, performance concerns, and code smells.
4. Rank findings by impact.
5. Implement confident fixes immediately; collect clarifications if needed.
6. For genuinely high-stakes branches (security, data loss, public API, large refactors), run a `cross-model-review` second-opinion pass and action its findings. Skip it for small or routine branches.

## Rules

- Review entire branch diff, not only latest commit
- Prioritize correctness and regressions over stylistic polish
