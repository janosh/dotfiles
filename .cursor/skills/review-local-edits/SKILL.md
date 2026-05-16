---
name: review-local-edits
description: Review local edits for commit readiness — bloat, correctness, polish, test gaps. Use before committing or to judge if uncommitted changes earn their keep.
---

# Review Local Edits

## Instructions

Start in review mode. Ask: are all local edits real improvements that earn their keep and ready to commit? no bloat or unpolished code that needs more work before shipping?

Review the diff first for correctness, regressions, edge cases, integration issues, weak tests, duplicated setup, and unnecessary code.

Only after reviewing, immediately apply high-confidence polish fixes: remove bloat, simplify overbuilt code, tighten assertions, delete dead code, and clean obvious rough edges.

Do not action speculative ideas, behavior changes, or anything that needs product judgment. Report those separately.

Preserve behavior, keep edits targeted, and run focused tests/lints when cheap and relevant.
