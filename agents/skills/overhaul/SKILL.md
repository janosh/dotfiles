---
name: overhaul
description: "Explicit all-in quality pass on uncommitted or branch changes: redesign from first principles (breaking changes allowed), cut code to the minimum, adversarially review for bugs and bad APIs, then rank and fix what remains. Combines challenge-status-quo, code-simplifier, adversarial-review and rank-improvements. Modifier: distribute."
disable-model-invocation: true
---

# Overhaul

One pass that leaves the code smaller, correct and cleanly designed. Run the phases in order: redesign before trimming lines, trim before reviewing, review before ranking. This skill inlines the four source skills; do not invoke them separately.

## Scope

Review the uncommitted diff plus untracked files; if the tree is clean, the branch diff vs `main`; if neither exists, ask. Record the starting `git diff --stat` (vs the scope base) so the final report can show net lines. Expand beyond the scope only to update callers, tests and docs that a breaking change touches.

Supports `distribute`.

Hold every added line to account: does it earn its keep, does its complexity sit in the right layer, is there a simpler robust approach? Ask only when truly blocked: missing access, ambiguous product intent, or external context absent from the repo.

## Phase 1: Challenge the design

1. Derive the actual requirements from callers, tests, docs and user intent. Treat the current API, structure and compatibility paths as evidence, not constraints.
2. Ask what the smallest clean design would be if built today. Challenge every layer, abstraction, fallback, config option, compatibility shim and special case.
3. Prefer one source of truth, direct control flow, explicit invariants and fail-fast errors. Don't swap old complexity for speculative abstraction or change for novelty.
4. Breaking changes are allowed: when the new design is clearly superior (fewer concepts, less code, fewer failure modes, or measured speedups), implement it, delete obsolete interfaces and update in-scope callers, tests and docs instead of adding shims. Report breaks that reach outside the repo or public APIs before landing them.

## Phase 2: Minimize lines

1. Delete dead paths, unused params, needless indirection, defensive cruft and one-use helpers; centralize every confirmed duplication.
2. Flatten control flow, reduce nesting, tighten naming. Keep error handling proportionate.
3. Target a net-negative diff. Undo any hunk that grows the code without a clear clarity or correctness win (patch/editor, never `git restore`). Decide once per hunk.
4. Ask before deleting code with uncertain external usage.

Then run the narrowest affected checks once for the Phase 1–2 batch. Each logic-restructuring hunk needs a test exercising its changed path; if none exists, add one or compare a concrete adversarial input before and after, otherwise revert that hunk.

## Phase 3: Adversarial review

1. Write a self-contained prompt: user request, scope, the full diff, the redesign decisions and intentional breaks with their rationale, test results, and any corners cut. Don't hide risks.
2. Task the reviewer with: correctness (edge cases, boundary conditions, bad assumptions, integration, error paths, silent failures, state leaks); API and design quality (confusing signatures, leaky abstractions, wrong layer, misnamed concepts); test strength (strict assertions over "it runs", edge and error paths covered); performance (avoidable overhead, fragile micro-optimizations); and remaining bloat, slop or non-DRY code. Demand concrete fixes, including larger refactors when clearly better.
3. Pick the reviewer model: the strongest model from another family the harness exposes (newest version, medium or at most high effort, never invented version names); else your own model. Report which ran.
4. Dispatch read-only reviewer subagent(s): one by default; one parallel layer partitioned by feature/directory only for large, weakly coupled diffs.
5. Action every finding. Verify each with concrete evidence; implement confirmed ones now, preferring deletion over new layers. Findings you can't confirm or that need a product call go to the report with your reasoning.

## Phase 4: Rank and finish

1. Re-read the resulting diff once more for correctness, robustness, simplification, performance and maintainability gaps the earlier phases missed. Weigh complexity against utility; recommend dropping costly low-value features.
2. Rank all open findings Critical / High / Medium / Low. Implement every verified low-risk one; defer only high-risk, high-effort or product-level calls.
3. Run the narrowest affected checks once for the Phase 3–4 batch.

## Report

1. **Net size**: starting vs final `git diff --stat` totals (lines added/removed).
2. **Redesign**: what changed structurally, intentional breaking changes, migration notes for out-of-scope callers.
3. **Implemented**: what was cut and why, fixes by severity with how each was verified, tests strengthened and what they now catch; reviewer model and whether cross- or same-model.
4. **Reported only, not done**: severity, location, problem, recommended fix, why deferred (with a complexity/utility rationale).
