# Fix Similar Issues

## Goal

Find and fix all similar issues to what you just fixed elsewhere in the codebase — even if they're slightly different or more general variants.

## Steps

1. **Generalize:** Identify the pattern or root cause of the issue you just fixed.
2. **Search:** Scan the entire codebase for:
   - Exact duplicates of the same issue
   - Variations or more general forms of the issue
   - Related anti-patterns that stem from the same misunderstanding
3. **Consolidate:** If multiple occurrences exist, consider whether a shared solution (helper function, utility, abstraction) can DRY them up.
4. **Fix:**
   - Apply the fix to all occurrences
   - If a DRY solution is warranted, implement it and refactor all call sites
   - If fixes differ significantly per location, handle each appropriately
5. **Verify:** Run tests to ensure all fixes are correct and nothing regressed.

## Rules

- **Be Thorough:** Don't stop at obvious matches—look for conceptually similar issues.
- **DRY When Justified:** If 3+ occurrences exist, a shared abstraction is likely worth it.
- **Don't Over-Abstract:** If occurrences are too different, fix them individually rather than forcing a bad abstraction.
- **Preserve Behavior:** Each fix must maintain correct functionality.

## Outcome

The issue you fixed is now fixed everywhere, and if applicable, a reusable solution prevents it from recurring.
