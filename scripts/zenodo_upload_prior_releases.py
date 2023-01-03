import requests

__date__ = "2022-12-27"

# adapted from script posted by @jrs65 in
# https://github.com/zenodo/zenodo/issues/1463#issuecomment-1007602828

repo = "janosh/pymatviz"
# token copied from
# https://github.com/janosh/pymatviz/settings/hooks/394259611
access_token = "**************"

headers = {"Accept": "application/vnd.github.v3+json"}

repo_response = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
releases = requests.get(
    f"https://api.github.com/repos/{repo}/releases", headers=headers
).json()


print(f"prior {len(releases)=}")


# upload oldest release first
for release in reversed(releases):

    payload = dict(
        action="published",
        release=release,
        repository=repo_response.json(),
    )

    submit_response = requests.post(
        f"https://zenodo.org/api/hooks/receivers/github/events/?{access_token=}",
        json=payload,
    )

    print(submit_response.status_code)
