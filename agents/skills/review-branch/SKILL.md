---
name: review-branch
description: Review the full branch diff against main for architecture, correctness, performance, and style, then fix or propose high-impact fixes. Use for pre-PR quality review.
---

# Review Branch

## Instructions

1. Inspect branch scope (`git log main..HEAD`, diff stats, full diff).
2. Use `distribute` when requested or when independent feature/directory reviews justify one read-only parallel layer; otherwise review directly. Aggregate findings and apply fixes yourself; explain any requested fallback.
3. Identify bugs, performance concerns, and code smells.
4. Rank findings by impact.
5. Implement confident fixes immediately; collect clarifications if needed.
6. For genuinely high-stakes branches (security, data loss, public API, or large behavior-changing refactors), run an `adversarial-review` second-opinion pass and action its findings. Skip it for routine or large-but-mechanical branches.

## Rules

- Review entire branch diff, not only latest commit
- Prioritize correctness and regressions over stylistic polish
