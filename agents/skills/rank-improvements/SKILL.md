---
name: rank-improvements
description: "Review uncommitted or branch changes, rank improvements, implement safe fixes, and surface judgment calls. Use for prioritized review before committing or opening a PR. Modifiers: branch (full branch diff vs main), distribute."
---

# Rank Improvements

## Instructions

1. Scope: the uncommitted diff plus untracked files when the tree is dirty; otherwise, or with `branch`, the full branch diff vs `main` (`git log main..HEAD`, diff stats, full diff), never only the latest commit. Review both only when asked or inseparable, and expand repository-wide only when asked or an observed pattern warrants it.
2. Judge whether every edit earns its keep. Check correctness, regressions, edge cases, integration, robustness, performance, API/design quality, weak tests, duplicated setup, dead code, needless abstraction and unnecessary lines. Weigh complexity against utility; recommend dropping costly low-value features.
3. Rank findings by severity: Critical, High, Medium, Low. Correctness and regressions outrank stylistic polish.
4. Implement every verified, low-risk, behavior-preserving fix. Always centralize confirmed duplication; never merely report unDRY code.
5. Defer only high-risk, behavior-changing, design-level, high-effort or product-dependent findings. Include severity, location, problem, and recommended fix with a complexity/payoff assessment.
6. Run the narrowest affected checks once after any fix batch.
7. Keep this fast. Run an `adversarial-review` pass only when the user asks or the change is genuinely high-stakes: security, data loss, migrations, public API, or large behavior-changing refactors. Skip it for routine or large-but-mechanical changes.
8. Report **Implemented** items with severity and verification, then **Reported only — not done** items, ordered by severity.

Supports `distribute`.
