---
name: review-local-edits
description: Pre-commit gate for uncommitted edits: judge whether each earns its keep and apply confident cleanup. Use immediately before committing.
---

# Review Local Edits

## Instructions

1. Review the uncommitted diff and untracked files. Judge whether every edit earns its keep and is ready to commit.
2. Check correctness, regressions, edge cases, integration, performance, API/design quality, weak tests, duplicated setup, dead code, needless abstraction, and unnecessary lines.
3. Prioritize findings by impact and confidence. Immediately apply verified, low-risk, behavior-preserving fixes: remove bloat, simplify overbuilt code, tighten assertions, and clean rough edges.
4. Report speculative, behavior-changing, design-level, high-effort, or product-dependent improvements separately with a concrete recommendation and complexity/payoff assessment.
5. Keep edits targeted and run the narrowest affected checks once after the fix batch.
6. Keep this fast. Run a `cross-model-review` only when the user asks or the change is genuinely high-stakes: security, data loss, migrations, or public API.
