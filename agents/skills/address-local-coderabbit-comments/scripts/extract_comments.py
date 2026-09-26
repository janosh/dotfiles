"""Extract CodeRabbit comments from the latest review round for a workspace."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

if TYPE_CHECKING:
    from collections.abc import Iterator

DETAILS_BLOCK_RE = re.compile(r"<details\b[^>]*>.*?</details>", re.DOTALL | re.IGNORECASE)

type JsonValue = dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None

NITPICK_CACHE_KEYS = {
    "assertive": "assertiveComments",
    "additional": "additionalComments",
    "outsideDiffRange": "outsideDiffRangeComments",
    "duplicate": "duplicateComments",
}
TIMESTAMP_KEYS = ("endedAt", "updatedAt", "startedAt", "createdAt")
# A repo open in two editors has two independently-stale caches; newest round wins.
IDE_DIR_NAMES = (
    "Cursor",
    "Code",
    "Code - Insiders",
    "VSCodium",
    "Windsurf",
    "Positron",
)


def default_ide_user_dirs() -> list[str]:
    """Return every known editor user directory present on this machine."""
    home = os.path.expanduser("~")
    bases = (
        f"{home}/Library/Application Support",  # macOS
        f"{home}/.config",  # Linux
        os.environ.get("APPDATA", ""),  # Windows
    )
    return [
        candidate
        for base in bases
        if base
        for name in IDE_DIR_NAMES
        if os.path.isdir(candidate := f"{base}/{name}/User")
    ]


def local_time(epoch: float) -> datetime:
    """Convert an epoch timestamp to an aware datetime in the local timezone."""
    return datetime.fromtimestamp(epoch, tz=UTC).astimezone()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for extracting CodeRabbit comments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        required=True,
        help="Absolute workspace path, e.g. /Users/janosh/dev/matterviz",
    )
    parser.add_argument(
        "--ide-user-dir",
        dest="ide_user_dirs",
        action="append",
        help=(
            "Editor user directory containing workspaceStorage. Repeatable; "
            "defaults to every known VS Code-family editor found on this machine"
        ),
    )
    parser.add_argument(
        "--review-id",
        default="",
        help="Optional explicit CodeRabbit review ID to extract",
    )
    parser.add_argument(
        "--mode",
        choices=("all", "main", "nitpicks"),
        default="all",
        help=(
            "Filter the round's comments: all (default), main "
            "(fileReviewMap actionable) or nitpicks (additionalDetails buckets)"
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


def discover_workspace_dirs(ide_user_dirs: list[str], workspace: str) -> list[str]:
    """Return every workspaceStorage dir mapped to workspace (one per editor)."""
    workspace_uri = f"file://{workspace}"
    matched_dirs: list[str] = []
    for ide_user_dir in ide_user_dirs:
        for workspace_json_path in glob.glob(
            f"{ide_user_dir}/workspaceStorage/*/workspace.json"
        ):
            try:
                workspace_json = read_json_file(workspace_json_path)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(workspace_json, dict):
                continue
            folder = workspace_json.get("folder")
            # Editors percent-encode the stored URI; decoding it avoids having to mimic
            # each editor's choice of reserved characters when encoding the input.
            if not isinstance(folder, str) or unquote(folder) != workspace_uri:
                continue
            matched_dirs.append(os.path.dirname(workspace_json_path))
    return sorted(set(matched_dirs))


def discover_coderabbit_cache_files(workspace_dir: str) -> list[str]:
    """Return candidate CodeRabbit cache files for one workspaceStorage directory."""
    cache_glob = f"{workspace_dir}/coderabbit.coderabbit-vscode/*.json"
    return sorted(
        file_path
        for file_path in glob.glob(cache_glob)
        if not file_path.endswith("/categories.json")
    )


def parse_iso_datetime(timestamp_text: str) -> datetime | None:
    """Parse ISO-like timestamp text into a datetime."""
    try:
        return datetime.fromisoformat(timestamp_text.strip())
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


def extract_all_comments(review: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every comment in one round, main actionable ones first.

    Extraction is never partial (`--mode` only filters), so an empty bucket can't be
    mistaken for an empty round.
    """
    file_review_map = review.get("fileReviewMap")
    comments = flatten_file_comments(
        file_review_map if isinstance(file_review_map, dict) else {},
        comment_type="main",
        nested_key="comments",
    )
    additional_details = review.get("additionalDetails")
    if not isinstance(additional_details, dict):
        additional_details = {}
    for comment_type, cache_key in NITPICK_CACHE_KEYS.items():
        comments_by_file = additional_details.get(cache_key)
        comments.extend(
            flatten_file_comments(
                comments_by_file if isinstance(comments_by_file, dict) else {},
                comment_type=comment_type,
            )
        )
    return comments


def filter_by_mode(comments: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    """Narrow extracted comments to main only, nitpicks only, or everything."""
    if mode == "main":
        return [comment for comment in comments if comment["type"] == "main"]
    if mode == "nitpicks":
        return [comment for comment in comments if comment["type"] != "main"]
    return comments


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
    comments: list[dict[str, Any]], *, review_title: str, review_date: str
) -> str:
    """Render comments as compact plain text for agent context.

    The header carries the round's date since caches go stale silently.
    """
    title = review_title.strip() or "(untitled review)"
    dated = f" · reviewed {review_date}" if review_date else ""
    counts = Counter(str(comment["type"]) for comment in comments)
    breakdown = ", ".join(f"{count} {name}" for name, count in counts.most_common())
    header = f"# {len(comments)} comment(s)"
    header += f" ({breakdown})" if breakdown else ""
    header += f" · {title}{dated}"
    if not comments:
        return f"{header}\n\n(none)\n"

    blocks: list[str] = []
    for comment in comments:
        location = format_location(
            str(comment["filename"]),
            comment.get("start_line"),
            comment.get("end_line"),
        )
        if (severity := comment.get("severity")) and severity != "none":
            location = f"{location} [{severity}]"
        body = str(comment.get("comment") or "(empty comment)")
        body_text = re.sub(r"\n{3,}", "\n\n", DETAILS_BLOCK_RE.sub("", body)).strip()
        blocks.append(f"{location}\n{body_text}")
    return f"{header}\n\n" + "\n\n---\n\n".join(blocks) + "\n"


def collect_cache_files(ide_user_dirs: list[str] | None, workspace: str) -> list[str]:
    """Return every CodeRabbit cache file for one workspace across all editors.

    Raises RuntimeError naming what was searched rather than returning nothing.
    """
    ide_user_dirs = ide_user_dirs or default_ide_user_dirs()
    if not ide_user_dirs:
        raise RuntimeError(
            "No VS Code-family editor user directory found; pass --ide-user-dir."
        )
    workspace_dirs = discover_workspace_dirs(ide_user_dirs, workspace)
    if not workspace_dirs:
        raise RuntimeError(
            f"No workspaceStorage folder matched workspace {workspace} "
            f"under: {', '.join(ide_user_dirs)}"
        )
    cache_files = [
        cache_file
        for workspace_dir in workspace_dirs
        for cache_file in discover_coderabbit_cache_files(workspace_dir)
    ]
    if not cache_files:
        raise RuntimeError(f"No CodeRabbit cache files under: {', '.join(workspace_dirs)}")
    return cache_files


def iter_cached_reviews(cache_files: list[str]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (cache_file, review) for every review in readable cache files."""
    for cache_file in cache_files:
        try:
            payload = read_json_file(cache_file)
        except (OSError, json.JSONDecodeError):
            continue
        for review in iter_reviews(payload):
            yield cache_file, review


def select_review(cache_files: list[str], review_id: str) -> tuple[dict[str, Any], str, float]:
    """Select explicit review ID or newest available review round."""
    reviews = iter_cached_reviews(cache_files)
    if review_id:
        match = next((item for item in reviews if item[1].get("id") == review_id), None)
        if match is None:
            raise RuntimeError(f"No CodeRabbit review with id '{review_id}' was found.")
    else:
        # Review timestamp first, cache file mtime breaks ties; the first maximum wins.
        match = max(
            reviews,
            key=lambda item: (review_timestamp_epoch(item[1]), os.path.getmtime(item[0])),
            default=None,
        )
        if match is None:
            raise RuntimeError("No CodeRabbit reviews were found for this workspace.")
    cache_file, review = match
    return review, cache_file, review_timestamp_epoch(review)


def main() -> None:
    """Extract CodeRabbit comments for selected review and emit text or JSON."""
    args = parse_args()
    workspace = os.path.abspath(args.workspace)
    cache_files = collect_cache_files(args.ide_user_dirs, workspace)

    selected_review, source_cache_file, selected_timestamp_epoch = select_review(
        cache_files=cache_files,
        review_id=args.review_id,
    )

    extracted_comments = filter_by_mode(extract_all_comments(selected_review), args.mode)
    # Main comments first: they are the ones that block, nitpicks are advisory.
    extracted_comments.sort(
        key=lambda comment: (
            comment["type"] != "main",
            str(comment["filename"]),
            int(comment["start_line"] or 0),
            int(comment["end_line"] or 0),
        )
    )

    review_title = selected_review.get("title")
    review_title = review_title if isinstance(review_title, str) else ""
    review_date = (
        local_time(selected_timestamp_epoch).strftime("%Y-%m-%d")
        if selected_timestamp_epoch
        else ""
    )
    cache_mtime_iso = local_time(os.path.getmtime(source_cache_file)).isoformat(
        timespec="minutes"
    )

    if args.json:
        payload = json.dumps(
            {
                "workspace": workspace,
                "cache_files": cache_files,
                "source_cache_file": source_cache_file,
                "selected_review_id": selected_review.get("id"),
                "selected_review_title": review_title,
                "selected_review_timestamp_epoch": selected_timestamp_epoch,
                "selected_review_date": review_date,
                "source_cache_file_mtime_iso": cache_mtime_iso,
                "mode": args.mode,
                "counts_by_type": dict(
                    Counter(str(comment["type"]) for comment in extracted_comments)
                ),
                "comment_count": len(extracted_comments),
                "comments": extracted_comments,
            },
            indent=2,
            ensure_ascii=False,
        )
        payload += "\n"
    else:
        payload = format_comments_text(
            extracted_comments,
            review_title=review_title,
            review_date=review_date,
        )

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
