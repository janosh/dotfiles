---
name: debug
description: Reproduce and fix bugs autonomously by gathering runtime evidence directly. Use when behavior is broken or failing.
---

# Debug

## When to use

- Failing tests or runtime errors
- User reports a bug and expects end-to-end investigation

## Instructions

1. Reproduce the issue locally (tests, app run, browser if relevant).
2. Gather evidence: logs, stack traces, network/console state.
3. Isolate minimal failing path and root cause.
4. Validate hypotheses with small focused checks.
5. Implement smallest correct fix.
6. Remove instrumentation and add regression coverage.

## Rules

- Collect evidence directly; do not offload basic debugging to user
- Iterate through hypotheses until root cause is confirmed
- Leave no debug noise in final code
