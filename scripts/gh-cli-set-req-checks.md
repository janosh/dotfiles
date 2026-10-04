# Auto-update required status checks for PR auto-merge with GitHub CLI

Found this command in this [issue comment](https://github.com/cli/cli/issues/3528#issuecomment-1303499736) (2023-07-12).

Makes the GitHub Actions checks that ran on commit `$sha` required to pass before a PR on `$branch` is auto-mergeable.

```sh
repo=materialsproject/pymatgen branch=master sha=2c75998
# repo=materialsproject/atomate2 branch=main sha=7d16877 # https://github.com/materialsproject/atomate2/pull/522
gh api -i "repos/$repo/branches/$branch/protection/required_status_checks" --method PATCH --input - <<<"$(gh api "repos/$repo/commits/$sha/check-runs" --paginate --jq '{ context: .check_runs[].name }' | jq -s '{ checks: . | unique }')"
```
