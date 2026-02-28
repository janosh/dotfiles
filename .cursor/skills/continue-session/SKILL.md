---
name: continue-session
description: Resume long-running work from progress artifacts, implement next feature, and update session state.
disable-model-invocation: true
---

# Continue Session

## When to use

- User explicitly asks to continue an initialized long-running project

## Instructions

1. Read progress artifacts (`claude-progress.txt`, `features.md`) and recent commits.
2. Select first unchecked feature.
3. Run `init.sh` if present.
4. Implement one feature, add tests, and verify end-to-end behavior.
5. Update progress files and next-step status.

## Rules

- Do not skip feature order unless blocked
- Update both tracking files every session
- Keep each session focused on one feature
