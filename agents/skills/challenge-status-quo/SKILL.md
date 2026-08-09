---
name: challenge-status-quo
description: Challenge an existing implementation from first principles and redesign it toward the simplest robust architecture, accepting breaking changes. Use when asking whether a design is still optimal, requesting a clean-slate rethink, or seeking less bloat, compatibility baggage, and incidental edge cases.
---

# Challenge Status Quo

1. Derive the actual requirements from callers, tests, docs, and user intent. Focus on implementation, but challenge requirements when evidence shows they are needless or harmful. Treat the current API and structure as evidence, not constraints.
2. Ask: if built today, what is the smallest clean design that satisfies those requirements? Challenge every layer, abstraction, fallback, configuration option, compatibility path, and special case.
3. Compare the current and proposed designs concretely: concepts, states, code size, duplication, failure modes, measured performance, and migration cost.
4. Prefer one source of truth, direct control flow, explicit invariants, and fail-fast errors. Do not replace old complexity with speculative abstraction.
5. Allow breaking changes. Remove obsolete interfaces and update in-scope callers, tests, and docs instead of adding shims.
6. When edits are authorized, implement a clearly superior design and verify retained requirements. Otherwise report the recommended architecture, intentional breaks, and migration steps.

Do not recommend change for novelty. Optimize primarily for deletion, less code, or measured performance gains while preserving required correctness and robustness.
