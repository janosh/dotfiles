---
name: verify-tests
description: Validate test robustness using mutation-style checks. Use when you need evidence tests actually fail on real bugs.
---

# Verify Tests via Mutation

## Instructions

1. Target recently changed code paths.
2. Introduce one deliberate breaking mutation at a time.
3. Run tests and inspect results:
   - If tests still pass, strengthen assertions or add cases
   - If tests fail, confirm failure is meaningful
4. Record each exact mutation hunk and undo only that hunk with a patch/editor before the next trial. Never use stash, reset, restore, or checkout to remove mutations from a dirty working tree; run the trials in an isolated worktree when exact in-place undo is unsafe.
5. Finish clean: confirm in the scoped diff for files you mutated that the recorded mutation hunks are gone, not that the whole working tree is clean. Then run the focused tests once on the restored code.

## Rules

- Prefer strengthening existing tests before adding many new ones
