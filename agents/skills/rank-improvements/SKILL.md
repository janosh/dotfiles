---
name: rank-improvements
description: Review changed code, rank improvements, implement safe fixes, and surface judgment calls. Use for prioritized review of uncommitted or branch changes.
---

# Rank Improvements

## Instructions

1. Review uncommitted changes when the tree is dirty; otherwise review the branch diff vs `main`. Review both only when asked or inseparable, and expand repository-wide only when asked or an observed pattern warrants it.
2. Find correctness, robustness, simplification, performance, readability, and maintainability improvements. Weigh complexity against utility; recommend dropping costly low-value features.
3. Rank findings by severity: Critical, High, Medium, Low.
4. Implement every verified, low-risk, behavior-preserving fix. Always centralize confirmed duplication; never merely report unDRY code.
5. Defer only high-risk, behavior-changing, design-level, or high-effort findings. Include severity, location, problem, and recommended fix.
6. Run the narrowest affected checks once after any fix batch; reuse a same-session result only when no covered path changed since that run.
7. Report **Implemented** items with severity and verification, then **Reported only — not done** items, ordered by severity.
