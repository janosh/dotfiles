---
name: address-pr-comments
description: Triage and resolve PR comments from humans and bots, including code/test updates and thread resolution workflow.
---

# Address PR Comments

## Instructions

1. Determine PR number and fetch comments via `gh` APIs.
2. Interpret invocation modifiers; `blocking` and `distribute` may be combined:
   - `blocking`: poll for bot comments every 120 seconds in the foreground and do not switch to other tasks until bot comments appear or a clear timeout/error condition occurs. Without it, do a single fetch pass; if bot comments are not ready, report status and wait for a later re-run instead of idling.
   - `distribute`: use when requested or when independent file/thread groups justify one parallel layer. Subagents edit only assigned disjoint paths and propose thread dispositions; the parent owns replies, resolutions, aggregate checks, commits, and pushes. Explain any requested fallback.
3. Once comments are available, categorize into bugs, suggestions, nitpicks, and questions.
4. Address each with code/test updates.
5. Resolve review threads through GraphQL for comments that are fixed or intentionally accepted as no-change. Do not leave bot comment threads open.
6. Review the remediation diff directly for obvious bloat; invoke `/code-simplifier` only when the edits are substantial or clearly verbose. Run the narrowest affected checks once over the remediated paths. Do not cascade into other review skills unless risky logic remains unverified.
7. Batch related fixes into coherent commits, then push.

## Rules

- Do not silently ignore comments
- Reply within existing review threads only when it adds clear value for future human reviewers: a non-obvious tradeoff, partial acceptance, or reason for leaving code as-is. Skip rebuttals of clearly incorrect bot suggestions.
- Never post a top-level PR comment unless the user explicitly asks. Put useful rationale in the relevant existing review thread; report anything else only to the user.
- Add tests when comments expose missing behavior coverage
- Prioritize correctness and high-signal feedback first
