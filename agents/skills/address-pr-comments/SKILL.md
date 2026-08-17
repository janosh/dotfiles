---
name: address-pr-comments
description: Triage and resolve PR comments from humans and bots, including code/test updates and thread resolution workflow.
---

# Address PR Comments

## When to use

- A PR has unresolved review comments
- You need systematic comment-by-comment remediation

## Instructions

1. Determine PR number and fetch comments via `gh` APIs.
2. Interpret invocation modifiers; `blocking` and `distribute` may be combined:
   - `blocking`: poll for bot comments every 120 seconds in the foreground and do not switch to other tasks. Without it, do a single fetch pass and report when bot comments are not ready.
   - `distribute`: use when requested or when independent file/thread groups justify one parallel layer. Subagents edit only assigned disjoint paths and propose thread dispositions; the parent owns replies, resolutions, aggregate checks, commits, and pushes. Explain any requested fallback.
3. Once comments are available, categorize into bugs, suggestions, nitpicks, and questions.
4. Address each with code/test updates; only reply within existing review threads when the reply adds clear value for future human reviewers.
5. Resolve review threads through GraphQL for comments that are fixed or intentionally accepted as no-change. Do not leave bot comment threads open.
6. Review the remediation diff directly for obvious bloat; invoke `/code-simplifier` only when the edits are substantial or clearly verbose. Run the narrowest affected checks once over the remediated paths, reusing a same-session result only for paths you have not edited since. Do not cascade into other review skills unless risky logic remains unverified.
7. Batch related fixes into coherent commits, then push.

## Rules

- Do not silently ignore comments
- In `blocking` mode, continue polling until bot comments appear or a clear timeout/error condition occurs.
- In non-blocking mode, do not idle; report status and wait for a later re-run.
- Do not add low-value rebuttal noise. If a bot suggestion is clearly incorrect and not worth discussion, skip the reply and move on.
- Reply when context is genuinely useful (non-obvious tradeoff, partial acceptance, or reason for leaving code as-is).
- Never post a top-level PR comment unless the user explicitly asks. Put useful rationale in the relevant existing review thread; report anything else only to the user.
- Add tests when comments expose missing behavior coverage
- Prioritize correctness and high-signal feedback first
