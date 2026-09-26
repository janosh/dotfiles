"""Tests for the CodeRabbit comment extractor."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    f"{os.path.dirname(__file__)}/../agents/skills/"
    "address-local-coderabbit-comments/scripts/extract_comments.py"
)
_SPEC = importlib.util.spec_from_file_location("extract_comments", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
extract_comments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(extract_comments)


def make_editor_cache(user_dir: Path, folder_uri: str, reviews: list[dict[str, str]]) -> str:
    """Write a fake editor workspaceStorage tree holding one CodeRabbit cache file."""
    storage_dir = user_dir / "workspaceStorage" / "ws1"
    (storage_dir / "coderabbit.coderabbit-vscode").mkdir(parents=True)
    (storage_dir / "workspace.json").write_text(json.dumps({"folder": folder_uri}))
    cache_file = storage_dir / "coderabbit.coderabbit-vscode" / "cache.json"
    cache_file.write_text(json.dumps(reviews))
    return str(storage_dir)


@pytest.mark.parametrize(
    ("filename", "start_line", "end_line", "expected"),
    [
        ("a.py", 10, 10, "a.py:10"),
        ("a.py", 10, 12, "a.py:10-12"),
        ("a.py", 10, None, "a.py:10"),
        ("a.py", None, 12, "a.py:12"),
        ("a.py", None, None, "a.py"),
    ],
)
def test_format_location(
    filename: str, start_line: int | None, end_line: int | None, expected: str
) -> None:
    """Format file:line ranges compactly."""
    assert extract_comments.format_location(filename, start_line, end_line) == expected


def test_format_comments_text() -> None:
    """Plain text strips details chrome and headlines the round's composition."""
    text = extract_comments.format_comments_text(
        [
            {
                "filename": "src/lib/FindBar.svelte",
                "start_line": 64,
                "end_line": 70,
                "severity": "trivial",
                "type": "assertive",
                "comment": (
                    "Confirm the refresh effect tracks the query.\n\n"
                    "<details>\n<summary>Proposed change</summary>\n\n"
                    "```diff\n+ find.query\n```\n</details>"
                ),
            }
        ],
        review_title="Add find bar",
        review_date="2026-09-03",
    )
    header = "# 1 comment(s) (1 assertive) · Add find bar · reviewed 2026-09-03\n"
    assert text.startswith(header)
    assert "src/lib/FindBar.svelte:64-70 [trivial]" in text
    assert "Confirm the refresh effect tracks the query." in text
    assert "<details>" not in text
    assert "find.query" not in text

    empty = extract_comments.format_comments_text([], review_title="Review", review_date="")
    assert empty.startswith("# 0 comment(s) · Review\n")


def test_default_is_the_whole_round(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI and extraction both default to every bucket, so empty means an empty round."""
    monkeypatch.setattr(sys, "argv", ["extract_comments.py", "--workspace", "/workspace/repo"])
    assert extract_comments.parse_args().mode == "all"

    review = {
        "fileReviewMap": {"a.py": {"comments": [{"comment": "Fix the bug."}]}},
        "additionalDetails": {
            "assertiveComments": {"b.py": [{"comment": "Nitpick."}]},
            "additionalComments": {"c.py": [{"comment": "Also this."}]},
        },
    }
    everything = extract_comments.extract_all_comments(review)
    assert [comment["type"] for comment in everything] == ["main", "assertive", "additional"]

    main_only = extract_comments.filter_by_mode(everything, "main")
    assert [comment["comment"] for comment in main_only] == ["Fix the bug."]
    nitpicks = extract_comments.filter_by_mode(everything, "nitpicks")
    assert [comment["filename"] for comment in nitpicks] == ["b.py", "c.py"]
    assert extract_comments.filter_by_mode(everything, "all") == everything


def test_workspace_matching_decodes_uris_and_reports_misses(tmp_path: Path) -> None:
    """Spaces in a path match the percent-encoded stored URI; a miss names where it looked."""
    user_dir = tmp_path / "Code" / "User"
    storage_dir = make_editor_cache(
        user_dir, "file:///Volumes/SanDisk%20Extreme%204TB/example-project", []
    )

    matched = extract_comments.discover_workspace_dirs(
        [str(user_dir)], "/Volumes/SanDisk Extreme 4TB/example-project"
    )
    assert matched == [storage_dir]
    assert extract_comments.discover_workspace_dirs([str(user_dir)], "/dev/other") == []

    with pytest.raises(RuntimeError, match="No workspaceStorage folder matched"):
        extract_comments.collect_cache_files([str(user_dir)], "/dev/other")


def test_select_review_prefers_newest_round_across_editors(tmp_path: Path) -> None:
    """A stale cache in one editor never outranks a fresher round in another."""
    workspace = "/Users/janosh/dev/hive"
    # Discovery sorts its results, so the stale editor must sort FIRST for this to
    # catch a selector that degrades to picking the first cache it sees.
    stale_dir = tmp_path / "Code" / "User"
    fresh_dir = tmp_path / "Cursor" / "User"
    uri = f"file://{workspace}"
    make_editor_cache(stale_dir, uri, [{"id": "old", "endedAt": "2026-08-23T10:00:00Z"}])
    make_editor_cache(fresh_dir, uri, [{"id": "new", "endedAt": "2026-09-03T10:00:00Z"}])

    cache_files = extract_comments.collect_cache_files(
        [str(stale_dir), str(fresh_dir)], workspace
    )
    assert "/Code/User/" in cache_files[0]
    review, source_file, _ = extract_comments.select_review(cache_files, "")
    assert review["id"] == "new"
    assert "/Cursor/User/" in source_file

    # Zulu timestamps must parse; otherwise only cache mtimes would order the rounds.
    assert extract_comments.review_timestamp_epoch({"endedAt": "1970-01-01T00:00:01Z"}) == 1
    # An explicit id still reaches the older editor's round, proving both caches were read.
    assert extract_comments.select_review(cache_files, "old")[0]["id"] == "old"
