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
2. Interpret invocation mode:
   - If the user includes the term `blocking` right after invoking this skill, poll for bot comments every 120 seconds in the foreground and do not switch to other tasks.
   - Otherwise, do a single fetch pass and report that bot comments are not ready yet if none are found.
3. Once comments are available, categorize into bugs, suggestions, nitpicks, and questions.
4. Address each with code/test updates; only post thread replies when they add clear value for future human reviewers.
5. Resolve review threads through GraphQL for comments that are fixed or intentionally accepted as no-change. Do not leave bot comment threads open.
6. Batch related fixes into coherent commits.

## Rules

- Do not silently ignore comments
- In `blocking` mode, continue polling until bot comments appear or a clear timeout/error condition occurs.
- In non-blocking mode, do not idle; report status and wait for a later re-run.
- Do not add low-value rebuttal noise. If a bot suggestion is clearly incorrect and not worth discussion, skip the reply and move on.
- Reply when context is genuinely useful (non-obvious tradeoff, partial acceptance, or reason for leaving code as-is).
- Add tests when comments expose missing behavior coverage
- Prioritize correctness and high-signal feedback first
