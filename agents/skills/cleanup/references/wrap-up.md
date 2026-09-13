# Wrap Up Ready Work

## Scope

- `wrap-up` authorizes committing all ready work in the current repository, including earlier turns and other contributors; preserve work still being edited. Follow the [commit skill](../../commit/SKILL.md) and its `local`, `mine`, and `nv` modifiers, replacing “stage all edits” with **stage only reviewed, ready changes**.
- Commit/push first, then suggest cleanup. Delete, trash, move, or discard leftovers only with approval for the specific action/paths, including prior authorization; do not ask twice.
- Do not remove branches/worktrees in this mode. Open PRs/issues only when requested.

## Commit what is ready

1. Inspect `git status --short --untracked-files=all`, staged/unstaged diffs, relevant untracked files, and outstanding conversation commitments/findings. Include known relevant ignored scratch files; do not crawl dependencies or unrelated caches.
2. Classify **ready**, **unfinished or uncertain**, and **cleanup candidates**. Ready groups must be coherent, useful, polished, verified, and independent of excluded changes. Exclude scratch data, handover notes, experiments, debug leftovers, and package-manager artifacts from commits. Age or unfamiliar names do not prove disposability.
3. Make confident, small finishing fixes; leave substantial redesigns, unresolved failures, or ambiguity pending with reasons. Capture existing changes before risky edits and preserve other agents' work. Run narrow checks after the fix batch, reusing valid same-session results.
4. Isolate ready groups without overwriting or unstaging unrelated work. Review exact commit content, including deletions/new files; stage explicit paths or selected hunks, never `git add -A`. Staged does not imply ready. Defer inseparable groups and continue independent ones. Validate the actual proposed commit without relying on excluded working-tree edits.
5. Make coherent commits with normal hooks and follow the commit skill's push rules. Inspect the full outgoing range, including pre-existing commits; keep commits local if it contains unfinished work. Verify the destination with a dry run. For missing upstreams or rejected pushes, report the blocker and retain local commits; do not create replacement branches/PRs. Report commit IDs, validation, and actual push status. If nothing is ready, explain and continue to cleanup suggestions.

## Sort out local leftovers

Recheck status after commits. Inspect each candidate's contents, purpose, references, and preservation elsewhere. Distinguish deleting a tracked file from discarding its edits. Preserve useful unfinished work.

Give a compact table of exact source paths, reasons, actions, and destinations:

| Action | When to recommend it |
| --- | --- |
| Delete | Disposable output or redundant copies with no useful unique content. |
| Trash | Unneeded files worth keeping recoverable through the operating system. |
| Archive to `tmp/` | Notes, experiments, logs, patches, or other reference material. |
| Keep | Active, useful unfinished, or uncertain work; explain what remains. |

1. Prefix archive names with the current local date: `YYYY-MM-DD-`, e.g. `tmp/2026-09-13-import-experiment.py`. Preserve needed directory structure, disambiguate collisions without overwriting, and keep archives local and uncommitted.
2. State any resulting tracked deletion or discarded edit. To archive edits before discarding, preserve staged/unstaged binary patches separately and relevant untracked files; current file copies lose staged-only content and deletions. Additional commits of cleanup side effects require authorization.
3. Group pending choices, explaining that approval is needed to remove or relocate local work. Finish independent authorized commits first.
4. Before approved operations, recheck concurrent edits, inspect with `ls -ld` and `file`, and resolve symlinks. Preserve type/content and verify destinations before removing sources. Use the operating system's Trash mechanism; if unavailable, report it without substituting permanent deletion.
5. Recheck status; report actual results, archive locations, and remaining useful work. Say when no cleanup is warranted.
