"""Extract CodeRabbit comments from the latest review round for a workspace."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from typing import Any

DETAILS_BLOCK_RE = re.compile(r"<details\b[^>]*>.*?</details>", re.DOTALL | re.IGNORECASE)

type JsonValue = dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None

MODES = ("nitpicks", "main")
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
        "--mode",
        choices=MODES,
        default="nitpicks",
        help=(
            "Comment set to extract: nitpicks (assertiveComments) or "
            "main (higher-priority fileReviewMap actionable comments). "
            "Default: nitpicks"
        ),
    )
    parser.add_argument(
        "--type",
        dest="comment_types",
        default="assertive",
        help=(
            "Nitpicks mode only. Comma-separated types: "
            "assertive, additional, outsideDiffRange, duplicate, all "
            "(default: assertive)"
        ),
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (omit to print to stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON instead of compact plain text",
    )
    return parser.parse_args()


def resolve_comment_types(raw_types: str) -> list[str]:
    """Resolve requested comment types from CLI input."""
    if raw_types.strip() == "all":
        return list(COMMENT_TYPES)
    valid_types: list[str] = []
    for raw_type in raw_types.split(","):
        comment_type = raw_type.strip()
        if not comment_type:
            continue
        if comment_type in COMMENT_TYPES:
            valid_types.append(comment_type)
        else:
            print(f"warning: unknown comment type '{comment_type}', skipping", file=sys.stderr)
    return valid_types


def read_json_file(file_path: str) -> JsonValue:
    """Read and parse a JSON file."""
    with open(file_path, encoding="utf-8") as file_handle:
        return json.load(file_handle)


def iter_reviews(payload: JsonValue) -> list[dict[str, Any]]:
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
    parsed_timestamps = [
        parsed
        for key in TIMESTAMP_KEYS
        if isinstance((value := review.get(key)), str)
        and (parsed := parse_iso_datetime(value)) is not None
    ]
    return max(parsed_timestamps).timestamp() if parsed_timestamps else 0.0


def flatten_file_comments(
    by_file: dict[str, Any],
    *,
    comment_type: str | None = None,
    nested_key: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten per-file comment lists (optionally nested under nested_key)."""
    flattened_comments: list[dict[str, Any]] = []
    for filename, entry in by_file.items():
        if nested_key is not None:
            if not isinstance(entry, dict):
                continue
            comments = entry.get(nested_key)
        else:
            comments = entry
        if not isinstance(comments, list):
            continue
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            flattened_comments.append(
                {
                    "filename": comment.get("filename") or filename,
                    "start_line": comment.get("startLine"),
                    "end_line": comment.get("endLine"),
                    "severity": comment.get("severity"),
                    "type": comment_type or comment.get("type") or "actionable",
                    "comment": comment.get("comment"),
                }
            )
    return flattened_comments


def comment_sort_key(comment: dict[str, Any]) -> tuple[str, int, int]:
    """Sort comments by filename then line range."""
    return (
        str(comment["filename"]),
        int(comment["start_line"] or 0),
        int(comment["end_line"] or 0),
    )


def extract_comments_for_mode(
    review: dict[str, Any], mode: str, requested_types: list[str]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Extract comments for nitpicks or main mode; return comments and counts."""
    if mode == "main":
        file_review_map = review.get("fileReviewMap")
        comments = flatten_file_comments(
            file_review_map if isinstance(file_review_map, dict) else {},
            nested_key="comments",
        )
        return comments, {"main": len(comments)}

    additional_details = review.get("additionalDetails")
    if not isinstance(additional_details, dict):
        additional_details = {}
    comments: list[dict[str, Any]] = []
    counts_by_type: dict[str, int] = {}
    for comment_type in requested_types:
        comments_by_file = additional_details.get(CACHE_KEYS[comment_type])
        flattened = flatten_file_comments(
            comments_by_file if isinstance(comments_by_file, dict) else {},
            comment_type=comment_type,
        )
        counts_by_type[comment_type] = len(flattened)
        comments.extend(flattened)
    return comments, counts_by_type


def format_location(
    filename: str, start_line: int | str | None, end_line: int | str | None
) -> str:
    """Format file path with start/end line numbers for compact display."""
    if start_line is None:
        return filename if end_line is None else f"{filename}:{end_line}"
    if end_line is None or end_line == start_line:
        return f"{filename}:{start_line}"
    return f"{filename}:{start_line}-{end_line}"


def format_comments_text(
    comments: list[dict[str, Any]], *, review_title: str, mode: str
) -> str:
    """Render comments as compact plain text for agent context."""
    title = review_title.strip() or "(untitled review)"
    label = "nitpick(s)" if mode == "nitpicks" else "main comment(s)"
    header = f"# {len(comments)} {label} · {title}"
    if not comments:
        return f"{header}\n\n(none)\n"

    blocks: list[str] = []
    for comment in comments:
        location = format_location(
            str(comment["filename"]),
            comment.get("start_line"),
            comment.get("end_line"),
        )
        severity = comment.get("severity")
        if severity and severity != "none":
            location = f"{location} [{severity}]"
        body = comment.get("comment")
        if body:
            body_text = re.sub(r"\n{3,}", "\n\n", DETAILS_BLOCK_RE.sub("", str(body))).strip()
        else:
            body_text = "(empty comment)"
        blocks.append(f"{location}\n{body_text}")
    return f"{header}\n\n" + "\n\n---\n\n".join(blocks) + "\n"


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

    best: tuple[tuple[float, float], dict[str, Any], str] | None = None
    for cache_file in cache_files:
        try:
            payload = read_json_file(cache_file)
        except (OSError, json.JSONDecodeError):
            continue
        file_mtime = os.path.getmtime(cache_file)
        for review in iter_reviews(payload):
            score = (review_timestamp_epoch(review), file_mtime)
            if best is None or score > best[0]:
                best = (score, review, cache_file)
    if best is None:
        raise RuntimeError("No CodeRabbit reviews were found for this workspace.")
    best_score, best_review, best_source_file = best
    return best_review, best_source_file, best_score[0]


def main() -> None:
    """Extract CodeRabbit comments for selected review and emit text or JSON."""
    args = parse_args()
    workspace = os.path.abspath(args.workspace)
    requested_types = resolve_comment_types(args.comment_types)
    if args.mode == "nitpicks" and not requested_types:
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

    extracted_comments, counts_by_type = extract_comments_for_mode(
        selected_review, args.mode, requested_types
    )
    extracted_comments.sort(key=comment_sort_key)

    review_title = selected_review.get("title")
    review_title = review_title if isinstance(review_title, str) else ""

    if args.json:
        payload = json.dumps(
            {
                "workspace": workspace,
                "workspace_ids": workspace_ids,
                "source_cache_file": source_cache_file,
                "selected_review_id": selected_review.get("id"),
                "selected_review_title": review_title,
                "selected_review_timestamp_epoch": selected_timestamp_epoch,
                "mode": args.mode,
                "requested_types": requested_types if args.mode == "nitpicks" else ["main"],
                "counts_by_type": counts_by_type,
                "comment_count": len(extracted_comments),
                "comments": extracted_comments,
            },
            indent=2,
            ensure_ascii=False,
        )
    else:
        payload = format_comments_text(
            extracted_comments, review_title=review_title, mode=args.mode
        )
    if not payload.endswith("\n"):
        payload += "\n"

    if args.output:
        output_path = os.path.abspath(args.output)
        with open(output_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(payload)
        print(output_path, file=sys.stderr)
        print(f"comment_count={len(extracted_comments)}", file=sys.stderr)
        print(f"source_cache_file={source_cache_file}", file=sys.stderr)
        return
    print(payload, end="")


if __name__ == "__main__":
    main()
