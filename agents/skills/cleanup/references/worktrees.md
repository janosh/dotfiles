# Cleanup Branches and Worktrees

## Scope and authorization

- `worktrees` authorizes deleting verified inactive, redundant local branches and clean linked worktrees in the current repository without another confirmation. Audit/dry-run is report-only.
- Inspect all local branches and registered worktrees, including detached HEADs. Other repositories, remote branch deletion, publishing, PR creation, and moving unique changes require explicit user instruction.
- Protect the primary checkout, executing agent's checkout and branch, `main`, configured default branch, locked worktrees, running agents/sessions, active PR heads, and destinations retaining another candidate's changes.
- Never discard modified, staged, untracked, or valuable ignored files without explicit approval for that worktree. Never stash, reset, restore, force-switch branches, or use `git clean` to make deletion possible.

## Inventory and activity

1. Resolve the repository, primary/current checkouts, remotes, and canonical `main` ref. The primary checkout may be on another branch. Resolve an absent `main` or ambiguous remote before dependent deletion decisions.
2. Fetch relevant refs without pruning, merging, or changing checkouts; record exact comparison commit IDs. On failure, report it and retain candidates needing unavailable remote information.
3. Enumerate with `git worktree list --porcelain` and `git for-each-ref refs/heads/`. Record paths, branch/detached HEAD, upstream, tip, locks, operations in progress, and `git status --porcelain=v1 --untracked-files=all`. Include missing registrations; their directories may be on unmounted volumes.
4. Inspect open/recently merged PRs with read-only tools, matching head repository, branch, and commit, including forks. Use task/session status and recent branch/PR activity to identify ongoing work. Check for unique local commits after a PR closed or merged.
5. Exclude protected work before deep inspection. For candidates and needed retention/recovery destinations, separately inspect committed changes, staged/unstaged binary diffs, untracked/ignored files, nested repositories, and submodules recursively. Merged tips do not establish preservation of local content or detached submodule commits; ignored files are not automatically disposable.
6. Age, gone upstreams, and merged PR labels only identify candidates. Require inactivity and preservation for deletion; retain uncertain ownership, activity, or content and name the missing evidence.

## Prove what is preserved

Choose retained destinations before deletion: canonical main first, then active branches, worktrees, or open PRs. Keep them throughout cleanup; never let candidates justify deleting each other. Reflogs, dangling objects, temporary audit files, and closed PR labels do not qualify.

| Evidence | Decision |
| --- | --- |
| `git merge-base --is-ancestor <source-tip> <retained-tip>` succeeds | Source commits are retained; still check local changes and activity. |
| Squashed, rebased, or cherry-picked history | Compare actual changes as below. |
| Only another worktree's uncommitted files preserve the changes | Compare complete relevant content and protect that worktree. Deleting the committed source's only durable copy requires explicit approval. |
| Unique or uncertain changes | Keep the source and prepare recovery options. |

For rewritten history, locate matches with `git cherry -v <retained-tip> <source-tip>` and `git range-diff`, then compare the aggregate diff from the merge base against retained changes. Patch matching can ignore whitespace and miss squash groups or merge resolutions; inspect merge commits explicitly. Compare affected contents, deletions, renames, executable bits, symlinks, binaries, and submodule commits; report the result. Matching subjects, similar-looking code, no `+` lines, or merged PR labels are insufficient. If subsequent edits prevent exact comparison, require a verified mapping of every source change or retain the candidate.

Identify retained replacements for superseded changes; leave uncertain cases for the user.

## Recover useful unmerged work

1. Isolate the smallest useful missing change set from preserved or questionable work. Summarize its purpose, source branch/worktree and tip, files, size, and validation.
2. Before asking, record the primary checkout's absolute path/branch and existing diff. Prepare the missing binary patch and extra-file manifest; check applicability, overlapping edits, untracked-path conflicts, and missing inputs without modifying the destination. Keep artifacts in a temporary directory outside candidate worktrees, uncommitted and unstaged. If the primary checkout is not on `main`, resolve the destination in the proposal; do not switch it automatically.
3. First offer **Move into the main checkout, verify, then delete the source branch/worktree**. Specify destination, changes, conflicts, and source paths/refs to remove. Approval covers that transfer and removal after verification, including named dirty files once preserved, but no unrelated commit or push.
4. For substantial, coherent work meriting separate review, also offer **Open a PR from this branch/worktree** with proposed title/body, base, head repository/branch, and validation status. Prefer continuing a relevant open PR over duplication. Retain the source pending the choice. Selecting a PR authorizes committing/publishing the selected work, not deleting its branch.
5. Group choices into one concise request, explaining which useful changes lack safe retention elsewhere. Continue independent, verified cleanup while awaiting the choice.
6. After approval, recheck source/destination for concurrent edits and apply only agreed changes, preserving unrelated work. Verify contents and metadata against the intended patch/source; run the narrowest relevant checks once. Leave the source intact on conflicts, failed checks, or unaccounted changes.

## Delete and verify

1. Record each path/ref, source tip, retained destination/tip, activity evidence, and preservation result in tool results or notes; a separate file is optional. Immediately before removal, recheck refs, task activity, status, and file manifests. Reassess changed candidates.
2. Inspect directories with `ls -ld` and `file`, resolve symlinks, and use Git's registered path. Remove verified clean, inactive worktrees with `git worktree remove <path>`; never substitute recursive filesystem deletion. Inspect any refusal. A single `--force` is allowed solely for submodule presence after recursive checks prove the worktree/submodules clean and their commits/local content retained. Dirty content requires explicit approval for the named worktree and verified preservation. Never force-remove locked worktrees.
3. After handling its worktrees, delete an eligible branch with `git branch -d -- <branch>`. Independently verify retention: Git may check the branch's upstream. If squash/rebase history or retention on another branch makes `-d` refuse, use `git branch -D -- <branch>` only with recorded preservation proof. Retain branches needed for open PRs.
4. Before pruning missing registrations, check recorded HEAD/index for recoverable work and rule out unavailable volumes. Run `git worktree prune --dry-run --verbose`, then the matching prune only if every proposed entry is verified safe; retain uncertain entries.
5. Re-list branches/worktrees and verify retained destinations and contents. Report actual removals, where work survives, and what remains; finish with ranked recovery choices or unresolved evidence.

Git command reference: [worktrees](https://git-scm.com/docs/git-worktree), [branches](https://git-scm.com/docs/git-branch), and [patch comparison](https://git-scm.com/docs/git-cherry).
