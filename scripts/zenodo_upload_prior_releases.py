import os
import sys

import requests

__date__ = "2022-12-27"

# adapted from script posted by @jrs65 in
# https://github.com/zenodo/zenodo/issues/1463#issuecomment-1007602828

# repo = "janosh/matbench-discovery"
repo = "materialsproject/atomate2"  # 2024-02-19
# Token: query string from Zenodo GitHub hook payload URL (GitHub repo → Settings → Webhooks).
access_token = os.environ.get("ZENODO_GITHUB_HOOK_TOKEN")
if not access_token:
    sys.exit("Set ZENODO_GITHUB_HOOK_TOKEN to the Zenodo hook URL access token")

headers = {"Accept": "application/vnd.github.v3+json"}

repo_response = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
releases = requests.get(
    f"https://api.github.com/repos/{repo}/releases", headers=headers
).json()


print(f"prior {len(releases)=}")


# -- upload oldest release first --
# for release in reversed(releases):
# -- to only upload newest release, use releases[0] --
for release in [releases[0]]:
    payload = dict(
        action="published",
        release=release,
        repository=repo_response.json(),
    )

    response = requests.post(
        f"https://zenodo.org/api/hooks/receivers/github/events/?{access_token}",
        json=payload,
    )
    response.raise_for_status()

    print(f"uploaded {release['tag_name']}")
    print(response.json())
