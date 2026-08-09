---
name: code-simplifier
description: Simplify working code while preserving behavior. Use to remove bloat, duplication, and unnecessary complexity.
---

# Code Simplifier

## When to use

- Implementation works but is verbose or hard to maintain
- You want cleaner idiomatic code before merging

## Instructions

1. Review changed code for dead paths, duplication, and unnecessary abstraction.
2. Simplify control flow and reduce nesting where possible.
3. Improve naming and clarity with minimal edits.
4. Keep error handling robust but proportionate.
5. Reuse a same-session check only for paths you have not edited since; otherwise run the narrowest affected checks once after the edit batch. For logic-restructuring hunks, ensure that check includes a test exercising the changed path. If none exists, add one or compare a concrete adversarial input before and after the simplification; otherwise leave the hunk alone. Do not invoke another review skill.
6. Prefer net-negative or net-flat diffs. If a simplification grows the diff without a clear clarity or correctness win, undo only those hunks with a patch/editor, never git restore. Decide once per hunk to avoid churn.

## Rules

- Preserve behavior
- Keep scope focused on changed areas unless user expands it
- Ask before deleting code with uncertain external usage
