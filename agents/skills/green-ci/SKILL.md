---
name: green-ci
description: Diagnose and fix failed GitHub Actions PR checks, simplify and verify the patch, commit and push it, then address bot review comments that appear. Use for CI failures on the current or a specified PR.
---

# Green CI

1. Record `git status --short` and preserve pre-existing work. Verify `gh` authentication; switch accounts and retry on authentication errors.
2. Resolve the PR once with `gh pr view <pr> --json url,headRefName,headRefOid`, omitting `<pr>` for the current branch. Reuse its URL and require `headRefOid` to match `git rev-parse HEAD`; stop on a different revision.
3. Inspect checks with `gh pr checks "$pr_url" --json bucket,link,name,state,workflow`. For failed Actions runs at the PR head, use `gh run list --commit "$head_oid" --json conclusion,databaseId,status,url,workflowName` and `gh run view "$run_id" --log-failed`, falling back to job metadata and logs. Report external checks without investigating another provider unless requested.
4. Find the first causal failure; separate downstream failures, cancellations, infrastructure errors, and plausible flakes. Read the workflow and repository tooling, state the root cause, and do not edit for unrelated or unverified failures.
5. Apply the smallest root-cause fix with repository-native tooling. Add a focused regression test for behavior bugs; never weaken or skip checks.
6. Choose verification timing by risk. For exact-line, mechanical, semantics-preserving fixes, run any cheap check, push, and confirm locally while CI runs. Verify uncertain or behavior-changing fixes before push, and never report unrun checks as passing.
7. Invoke `$code-simplifier` on changed paths and recheck anything it edits, then `$commit mine`; stop when no code change is needed, required verification fails, or the patch remains uncertain.
8. Run deferred checks while polling CI and new bot comments. Invoke `$address-pr-comments` in this task when comments appear, never in `blocking` mode or through delegation. Commit each resulting fix and restart the loop; do not wait for comments after CI finishes.

Use Python only when it is part of the repository's own toolchain, not as a bundled GitHub-log adapter. Never amend, force-push, disturb unrelated dirty files, or claim a flaky or infrastructure failure is fixed by an unrelated code change.
