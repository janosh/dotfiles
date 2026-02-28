"""Extract CodeRabbit comments from the latest review round for a workspace."""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from typing import Any

COMMENT_TYPES = ("assertive", "additional", "outsideDiffRange", "duplicate")
CACHE_KEYS = {
    "assertive": "assertiveComments",
    "additional": "additionalComments",
    "outsideDiffRange": "outsideDiffRangeComments",
    "duplicate": "duplicateComments",
}
TIMESTAMP_KEYS = ("endedAt", "updatedAt", "startedAt", "createdAt")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for extracting CodeRabbit comments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        required=True,
        help="Absolute workspace path, e.g. /Users/janosh/dev/matterviz",
    )
    parser.add_argument(
        "--cursor-user-dir",
        default=f"{os.path.expanduser('~')}/Library/Application Support/Cursor/User",
        help="Cursor user directory containing workspaceStorage",
    )
    parser.add_argument(
        "--review-id",
        default="",
        help="Optional explicit CodeRabbit review ID to extract",
    )
    parser.add_argument(
        "--type",
        dest="comment_types",
        default="all",
        help=(
            "Comma-separated comment types to extract: "
            "assertive, additional, outsideDiffRange, duplicate, all "
            "(default: all)"
        ),
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output JSON file path (omit to print JSON to stdout)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON to stdout instead of writing a file",
    )
    return parser.parse_args()


def resolve_comment_types(raw_types: str) -> list[str]:
    """Resolve requested comment types from CLI input."""
    if raw_types.strip() == "all":
        return list(COMMENT_TYPES)
    requested_types = [comment_type.strip() for comment_type in raw_types.split(",")]
    filtered_types = [comment_type for comment_type in requested_types if comment_type]
    valid_types: list[str] = []
    for comment_type in filtered_types:
        if comment_type in COMMENT_TYPES:
            valid_types.append(comment_type)
            continue
        print(f"warning: unknown comment type '{comment_type}', skipping", file=sys.stderr)
    return valid_types


def read_json_file(file_path: str) -> Any:
    """Read and parse a JSON file."""
    with open(file_path, encoding="utf-8") as file_handle:
        return json.load(file_handle)


def iter_reviews(payload: Any) -> list[dict[str, Any]]:
    """Normalize one payload into a list of review dictionaries."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def discover_workspace_ids(cursor_user_dir: str, workspace: str) -> list[str]:
    """Return workspaceStorage IDs mapped to the workspace path."""
    workspace_storage_glob = f"{cursor_user_dir}/workspaceStorage/*/workspace.json"
    workspace_uri = f"file://{workspace}"
    matched_workspace_ids: list[str] = []
    for workspace_json_path in glob.glob(workspace_storage_glob):
        try:
            workspace_json = read_json_file(workspace_json_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(workspace_json, dict):
            continue
        if workspace_json.get("folder") != workspace_uri:
            continue
        workspace_id = os.path.basename(os.path.dirname(workspace_json_path))
        matched_workspace_ids.append(workspace_id)
    return sorted(set(matched_workspace_ids))


def discover_coderabbit_cache_files(cursor_user_dir: str, workspace_id: str) -> list[str]:
    """Return candidate CodeRabbit cache files for one workspace ID."""
    cache_glob = (
        f"{cursor_user_dir}/workspaceStorage/{workspace_id}/"
        "coderabbit.coderabbit-vscode/*.json"
    )
    return sorted(
        file_path
        for file_path in glob.glob(cache_glob)
        if not file_path.endswith("/categories.json")
    )


def parse_iso_datetime(timestamp_text: str) -> datetime | None:
    """Parse ISO-like timestamp text into a datetime."""
    normalized_text = timestamp_text.strip()
    if not normalized_text:
        return None
    if normalized_text.endswith("Z"):
        normalized_text = f"{normalized_text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(normalized_text)
    except ValueError:
        return None


def review_timestamp_epoch(review: dict[str, Any]) -> float:
    """Return best available review timestamp as epoch seconds."""
    parsed_timestamps: list[datetime] = []
    for timestamp_key in TIMESTAMP_KEYS:
        timestamp_value = review.get(timestamp_key)
        if not isinstance(timestamp_value, str):
            continue
        parsed_timestamp = parse_iso_datetime(timestamp_value)
        if parsed_timestamp is not None:
            parsed_timestamps.append(parsed_timestamp)
    if not parsed_timestamps:
        return 0.0
    return max(parsed_timestamps).timestamp()


def flatten_comments(
    comments_by_file: dict[str, Any], comment_type: str
) -> list[dict[str, Any]]:
    """Flatten comments-by-file mapping into a sorted flat list."""
    flattened_comments: list[dict[str, Any]] = []
    for filename, comments in comments_by_file.items():
        if not isinstance(comments, list):
            continue
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            flattened_comments.append(
                {
                    "filename": filename,
                    "start_line": comment.get("startLine"),
                    "end_line": comment.get("endLine"),
                    "severity": comment.get("severity"),
                    "type": comment_type,
                    "comment": comment.get("comment"),
                }
            )
    flattened_comments.sort(
        key=lambda item: (
            str(item["filename"]),
            int(item["start_line"] or 0),
            int(item["end_line"] or 0),
        )
    )
    return flattened_comments


def select_review(cache_files: list[str], review_id: str) -> tuple[dict[str, Any], str, float]:
    """Select explicit review ID or newest available review round."""
    if review_id:
        for cache_file in cache_files:
            try:
                payload = read_json_file(cache_file)
            except (OSError, json.JSONDecodeError):
                continue
            for review in iter_reviews(payload):
                if review.get("id") == review_id:
                    return review, cache_file, review_timestamp_epoch(review)
        raise RuntimeError(f"No CodeRabbit review with id '{review_id}' was found.")

    best_review: dict[str, Any] | None = None
    best_source_file = ""
    best_score: tuple[float, float] | None = None
    for cache_file in cache_files:
        try:
            payload = read_json_file(cache_file)
        except (OSError, json.JSONDecodeError):
            continue
        file_mtime = os.path.getmtime(cache_file)
        for review in iter_reviews(payload):
            timestamp_epoch = review_timestamp_epoch(review)
            score = (timestamp_epoch, file_mtime)
            if best_score is None or score > best_score:
                best_score = score
                best_review = review
                best_source_file = cache_file
    if best_review is None:
        raise RuntimeError("No CodeRabbit reviews were found for this workspace.")
    assert best_score is not None
    return best_review, best_source_file, best_score[0]


def main() -> None:
    """Extract CodeRabbit comments for selected review and emit JSON."""
    args = parse_args()
    workspace = os.path.abspath(args.workspace)
    requested_types = resolve_comment_types(args.comment_types)
    if not requested_types:
        raise RuntimeError("No valid comment types specified.")

    workspace_ids = discover_workspace_ids(args.cursor_user_dir, workspace)
    if not workspace_ids:
        raise RuntimeError(f"No Cursor workspaceStorage folder matched workspace: {workspace}")

    cache_files: list[str] = []
    for workspace_id in workspace_ids:
        cache_files.extend(discover_coderabbit_cache_files(args.cursor_user_dir, workspace_id))
    if not cache_files:
        raise RuntimeError("No CodeRabbit cache files found for this workspace.")

    selected_review, source_cache_file, selected_timestamp_epoch = select_review(
        cache_files=cache_files,
        review_id=args.review_id,
    )

    additional_details = selected_review.get("additionalDetails")
    if not isinstance(additional_details, dict):
        additional_details = {}

    extracted_comments: list[dict[str, Any]] = []
    counts_by_type: dict[str, int] = {}
    for comment_type in requested_types:
        cache_key = CACHE_KEYS[comment_type]
        comments_by_file = additional_details.get(cache_key)
        if not isinstance(comments_by_file, dict):
            comments_by_file = {}
        flattened_comments = flatten_comments(comments_by_file, comment_type)
        counts_by_type[comment_type] = len(flattened_comments)
        extracted_comments.extend(flattened_comments)

    extracted_comments.sort(
        key=lambda item: (
            str(item["filename"]),
            int(item["start_line"] or 0),
            int(item["end_line"] or 0),
        )
    )

    result = {
        "workspace": workspace,
        "workspace_ids": workspace_ids,
        "source_cache_file": source_cache_file,
        "selected_review_id": selected_review.get("id"),
        "selected_review_title": selected_review.get("title"),
        "selected_review_timestamp_epoch": selected_timestamp_epoch,
        "requested_types": requested_types,
        "counts_by_type": counts_by_type,
        "comment_count": len(extracted_comments),
        "comments": extracted_comments,
    }

    if args.stdout or not args.output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(result, file_handle, indent=2, ensure_ascii=False)
    print(output_path)
    print(f"comment_count={len(extracted_comments)}")
    print(f"source_cache_file={source_cache_file}")


if __name__ == "__main__":
    main()
