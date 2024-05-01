# Auto-update required status checks for PR auto-merge with GitHub CLi

Found this command in this [issue comment](https://github.com/cli/cli/issues/3528#issuecomment-1303499736) (2023-07-12).

Sets the set of GitHub actions that ran on the specified commit SHA as required to pass before a PR is auto-mergeable.

```sh
gh api -i repos/materialsproject/pymatgen/branches/master/protection/required_status_checks --method PATCH --input - <<<"$(gh api repos/materialsproject/pymatgen/commits/2c75998/check-runs --paginate --jq '{ context: .check_runs[].name }' | jq -s '{ checks: . | unique }')"
```

[For atomate2](https://github.com/materialsproject/atomate2/pull/522):

```sh
gh api -i repos/materialsproject/atomate2/branches/main/protection/required_status_checks --method PATCH --input - <<<"$(gh api repos/materialsproject/atomate2/commits/7d16877/check-runs --paginate --jq '{ context: .check_runs[].name }' | jq -s '{ checks: . | unique }')"
```
