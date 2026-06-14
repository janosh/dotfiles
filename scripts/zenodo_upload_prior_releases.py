"""Trigger Zenodo's GitHub webhook to archive prior GitHub releases of a repo.

Back-fills Zenodo DOIs for releases made before the Zenodo integration was enabled.
Requires ZENODO_GITHUB_HOOK_TOKEN (the access token query string from the Zenodo GitHub
webhook payload URL).
"""

import os
import sys

import requests

__date__ = "2022-12-27"
TIMEOUT = 30

# adapted from script posted by @jrs65 in
# https://github.com/zenodo/zenodo/issues/1463#issuecomment-1007602828

repo = "materialsproject/atomate2"  # 2024-02-19
# Token: query string from Zenodo GitHub hook payload URL (GitHub repo → Settings → Webhooks).
access_token = os.environ.get("ZENODO_GITHUB_HOOK_TOKEN")
if not access_token:
    sys.exit("Set ZENODO_GITHUB_HOOK_TOKEN to the Zenodo hook URL access token")

headers = {"Accept": "application/vnd.github.v3+json"}

url = f"https://api.github.com/repos/{repo}"
repo_response = requests.get(url, headers=headers, timeout=TIMEOUT)
releases = requests.get(f"{url}/releases", headers=headers, timeout=TIMEOUT).json()


print(f"prior {len(releases)=}")


# -- upload oldest release first --
# for release in reversed(releases):
# -- to only upload newest release, use releases[0] --
for release in [releases[0]]:
    payload = {"action": "published", "release": release, "repository": repo_response.json()}

    url = f"https://zenodo.org/api/hooks/receivers/github/events/?{access_token}"
    response = requests.post(url, json=payload, timeout=TIMEOUT)
    response.raise_for_status()

    print(f"uploaded {release['tag_name']}")
    print(response.json())
