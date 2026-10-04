"""Trigger Zenodo's GitHub webhook to archive a prior GitHub release of a repo.

Back-fills Zenodo DOIs for releases made before the Zenodo integration was enabled. Archives
only the newest release; loop over reversed(releases) to back-fill all, oldest first.
Requires ZENODO_GITHUB_HOOK_TOKEN (the access token query string from the Zenodo GitHub
webhook payload URL under GitHub repo -> Settings -> Webhooks).
Adapted from https://github.com/zenodo/zenodo/issues/1463#issuecomment-1007602828.
"""

import os
import sys

import requests

__date__ = "2022-12-27"
TIMEOUT = 30

repo = "materialsproject/atomate2"  # 2024-02-19
access_token = os.environ.get("ZENODO_GITHUB_HOOK_TOKEN")
if not access_token:
    sys.exit("Set ZENODO_GITHUB_HOOK_TOKEN to the Zenodo hook URL access token")

headers = {"Accept": "application/vnd.github.v3+json"}
repo_url = f"https://api.github.com/repos/{repo}"
repo_info = requests.get(repo_url, headers=headers, timeout=TIMEOUT).json()
releases = requests.get(f"{repo_url}/releases", headers=headers, timeout=TIMEOUT).json()
print(f"prior {len(releases)=}")

release = releases[0]
payload = {"action": "published", "release": release, "repository": repo_info}
response = requests.post(
    f"https://zenodo.org/api/hooks/receivers/github/events/?{access_token}",
    json=payload,
    timeout=TIMEOUT,
)
response.raise_for_status()
print(f"uploaded {release['tag_name']}")
print(response.json())
