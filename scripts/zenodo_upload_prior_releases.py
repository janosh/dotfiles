import requests

__date__ = "2022-12-27"

# adapted from script posted by @jrs65 in
# https://github.com/zenodo/zenodo/issues/1463#issuecomment-1007602828

repo = "janosh/matbench-discovery"
# token appears to be the same for every repo and was copied from the end of the
# payload url in the Zenodo webhook settings page:
# https://github.com/janosh/pymatviz/settings/hooks/424898772
access_token = "**************"

headers = {"Accept": "application/vnd.github.v3+json"}

repo_response = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
releases = requests.get(
    f"https://api.github.com/repos/{repo}/releases", headers=headers
).json()


print(f"prior {len(releases)=}")


# -- upload oldest release first --
# for release in reversed(releases):
# -- only upload oldest release --
for release in [releases[-1]]:
    payload = dict(
        action="published",
        release=release,
        repository=repo_response.json(),
    )

    response = requests.post(
        f"https://zenodo.org/api/hooks/receivers/github/events/?{access_token=!s}",
        json=payload,
    )

    if response.status_code != 200:
        msg = response.json()["message"]
        raise ValueError(f"Failed to submit release to Zenodo.\n\tMessage: {msg}")
    print(f"uploaded {release['tag_name']}")
    print(response.json())
