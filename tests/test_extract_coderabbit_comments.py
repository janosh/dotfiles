"""Tests for CodeRabbit comment extractor text formatting."""

import importlib.util
import os

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


def test_format_comments_text_is_plain_not_json() -> None:
    """Plain-text output includes location + body without JSON wrapping."""
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
        mode="nitpicks",
    )
    assert text.startswith("# 1 nitpick(s) · Add find bar\n")
    assert "src/lib/FindBar.svelte:64-70 [trivial]" in text
    assert "Confirm the refresh effect tracks the query." in text
    assert "<details>" not in text
    assert "find.query" not in text
    assert "{" not in text


def test_format_comments_text_main_label() -> None:
    """Main mode header uses main comment label."""
    text = extract_comments.format_comments_text([], review_title="Review", mode="main")
    assert text.startswith("# 0 main comment(s) · Review\n")


def test_resolve_comment_types_default_path() -> None:
    """Default assertive filter resolves; all expands to every type."""
    assert extract_comments.resolve_comment_types("assertive") == ["assertive"]
    assert extract_comments.resolve_comment_types("all") == list(
        extract_comments.COMMENT_TYPES
    )


def test_extract_comments_for_mode_main_vs_nitpicks() -> None:
    """Main reads fileReviewMap; nitpicks reads assertiveComments."""
    review = {
        "fileReviewMap": {
            "a.py": {
                "comments": [
                    {
                        "filename": "a.py",
                        "startLine": 1,
                        "endLine": 2,
                        "severity": "major",
                        "type": "actionable",
                        "comment": "Fix the bug.",
                    }
                ]
            }
        },
        "additionalDetails": {
            "assertiveComments": {
                "b.py": [
                    {
                        "startLine": 3,
                        "endLine": 3,
                        "severity": "trivial",
                        "comment": "Nitpick.",
                    }
                ]
            }
        },
    }
    main_comments, main_counts = extract_comments.extract_comments_for_mode(
        review, "main", ["assertive"]
    )
    assert main_counts == {"main": 1}
    assert main_comments[0]["comment"] == "Fix the bug."
    assert main_comments[0]["type"] == "actionable"

    nit_comments, nit_counts = extract_comments.extract_comments_for_mode(
        review, "nitpicks", ["assertive"]
    )
    assert nit_counts == {"assertive": 1}
    assert nit_comments[0]["comment"] == "Nitpick."
    assert nit_comments[0]["filename"] == "b.py"
