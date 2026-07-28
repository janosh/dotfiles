---
name: loose-ends
description: Surface unfinished work before a completion event. Use before committing, pushing, opening or merging a PR, cutting a release, or handing off, to recover TODOs and deferrals raised earlier in the conversation and judge what follow-up is now advisable.
disable-model-invocation: true
---

# Loose Ends

## When to use

- Before a completion event: commit, push, PR open or merge, release, handoff
- User asks what is left, what was missed, or whether anything needs follow-up

## Instructions

1. Name the completion event. It sets the bar for what must land now versus later.
2. Re-read the conversation for work raised but never finished:
   - things you said you would do later, deferred, or "left as is"
   - findings you reported instead of fixing, and review comments never actioned
   - questions you asked the user that went unanswered
   - claims you made without running anything ("should work", "probably fine")
   - scaffolding you introduced: debug output, scratch files, backups, stubs, commented-out code
   - side effects outside the diff: config written, files created elsewhere, packages installed, setup left half-done
3. Verify against the repo instead of trusting memory. `git status --short` for the full picture (`git diff` alone hides untracked files), plus the range the event implies: `git diff HEAD` for a commit, `@{upstream}..HEAD` for a push, `$(git merge-base origin/main HEAD)..HEAD` for a PR, the previous release tag for a release. Grep changed and untracked files for `TODO|FIXME|XXX|HACK`. Work you remember doing may have been reverted; work you remember deferring may already be done.
4. Judge the last few turns for follow-up that is advisable even though nobody raised it: missing test for new logic or a fixed bug, stale docs and comments, adjacent callers the change breaks, lint or CI never run, version and changelog for a release.
5. Present a ranked list. Per item give one line of what and why it matters, plus a recommendation: do now, defer, or drop.
6. Offer to action the "do now" items. Use AskQuestion when the user should pick.

## Rules

- Check the event's own gate: staged scope for a commit, push destination for a push, CI and unresolved threads for a merge, version bump and changelog for a release
- Say so plainly when nothing is left; never pad the list to look thorough
- Separate blockers from nice-to-haves so a nit cannot hold up the event
- Always surface changes you made to the machine or repo that the user has not seen yet
