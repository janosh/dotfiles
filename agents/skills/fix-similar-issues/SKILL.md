---
name: fix-similar-issues
description: Find and fix related variants of a recently fixed issue across the codebase. Use after resolving a bug or anti-pattern.
---

# Fix Similar Issues

## Instructions

1. Generalize the root pattern of the original issue.
2. Search for exact and conceptual variants across the repo; be thorough, not just text-match based.
3. Use `distribute` when requested or when disjoint areas justify one parallel search-and-fix layer; otherwise work directly. Never share edited files between agents; the parent owns shared changes and aggregate verification. Explain any requested fallback.
4. Apply fixes consistently, preserving behavior while normalizing them.
5. If repeated 3+ times, consider a shared abstraction only when it improves clarity; avoid it when call sites differ materially.
6. Run one aggregated focused verification after all fixes.
