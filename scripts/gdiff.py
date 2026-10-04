"""Rank files in a git repo by net lines added."""

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from collections import Counter
from collections.abc import Callable, Sequence
from html import escape
from urllib.parse import quote

LineRankRow = tuple[int, int, int, str]
CommitSummary = tuple[str, int, str]
ParsedArgs = tuple[str, int, str, str, list[str]]
CODE_EXT_PATTERN = re.compile(r"\.(?:c|cpp|css|go|html|js|jsx|py|rs|svelte|ts|tsx)")
ANSI_RESET = "\033[0m"
# Keyed by the kinds line_expr passes to its style callback and file_kind returns; both
# double as HTML classes.
ANSI_BY_KIND = {
    "added": "\033[32m",
    "net-positive": "\033[32m",
    "removed": "\033[31m",
    "net-negative": "\033[31m",
    "code-file": "\033[34m",
    "test-file": "\033[33m",
}
HTML_STYLE = """
body { color: #222; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid #ddd; padding: 0.35rem 0.5rem; text-align: left; }
th { position: sticky; top: 0; background: white; }
td.num, th.num { font-variant-numeric: tabular-nums; text-align: right; }
tr:hover { background: #f7f7f7; }
a { color: inherit; text-decoration-color: #999; text-underline-offset: 0.15rem; }
a:hover { text-decoration-color: currentColor; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.added, .net-positive { color: #16a34a; }
.removed, .net-negative { color: #dc2626; }
.code-file { color: #2563eb; }
.test-file { color: #ca8a04; }
""".strip()


def parse_args(args: Sequence[str]) -> ParsedArgs:
    """Parse gdiff arguments and pass unrecognized values through to git."""
    parser = argparse.ArgumentParser(
        prog="gdiff",
        allow_abbrev=False,
        description="Rank files in the current git repo by net lines added.",
        epilog=(
            "Examples:\n"
            "  gdiff\n"
            "  gdiff --staged\n"
            "  gdiff --staged-files\n"
            "  gdiff @~5\n"
            "  gdiff 1a2b3c4\n"
            "  gdiff --unstaged -- '*.py'\n"
            "  gdiff -n 25 --markdown\n"
            "  gdiff --history --html --since=1.year\n"
            "  gdiff --history --author='Jane Doe' -- '*.py'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--limit", type=int, default=0)
    parser.add_argument("--sort", choices=["a", "r", "n"], default="n")
    for dest, flags_by_const in (
        (
            "source_name",
            {
                "local": ["--local"],
                "staged": ["-s", "--staged"],
                "staged_files": ["--staged-files"],
                "unstaged": ["-u", "--unstaged"],
                "history": ["--history"],
            },
        ),
        (
            "format_name",
            {"table": ["--table"], "markdown": ["--md", "--markdown"], "html": ["--html"]},
        ),
    ):
        group = parser.add_mutually_exclusive_group()
        for const, flags in flags_by_const.items():
            group.add_argument(*flags, dest=dest, action="store_const", const=const)
    parser.set_defaults(format_name="table")

    parsed_args, git_args = parser.parse_known_args(args)
    if parsed_args.limit < 0:
        parser.error("--limit expects a non-negative integer")
    pathspec_idx = pathspec_index(git_args)
    has_revision_range = any(
        ".." in arg and not arg.startswith("-") for arg in git_args[:pathspec_idx]
    )
    source_name = parsed_args.source_name or (
        "diff" if has_revision_range else "history" if git_args else "local"
    )
    return parsed_args.format_name, parsed_args.limit, parsed_args.sort, source_name, git_args


def pathspec_index(git_args: Sequence[str]) -> int:
    """Return the index of the ``--`` pathspec separator, or len(git_args) if absent."""
    return git_args.index("--") if "--" in git_args else len(git_args)


def command_path(command: str) -> str:
    """Return the absolute path to an executable on PATH."""
    abs_command_path = shutil.which(command)
    if abs_command_path is None:
        print(f"gdiff: command not found: {command}", file=sys.stderr)
        raise SystemExit(127)
    return abs_command_path


def git_stdout(
    git_args: Sequence[str],
    error_message: str,
    exit_code: int | None = None,
) -> str:
    """Run a git command and return stdout."""
    git_proc = subprocess.run(
        [command_path("git"), *git_args],
        check=False,
        capture_output=True,
        text=True,
    )
    if git_proc.returncode != 0:
        print(git_proc.stderr.strip() or error_message, file=sys.stderr)
        raise SystemExit(git_proc.returncode if exit_code is None else exit_code)
    return git_proc.stdout.strip()


def parse_numstat_rows(numstat_stdout: str) -> list[LineRankRow]:
    """Parse git numstat output into unsorted line-rank rows, following renames."""
    added_by_file: Counter[str] = Counter()
    removed_by_file: Counter[str] = Counter()
    records = iter(
        numstat_stdout.split("\0") if "\0" in numstat_stdout else numstat_stdout.splitlines()
    )
    for record in records:
        try:
            added_text, removed_text, file_path = record.lstrip("\n").split("\t", 2)
        except ValueError:
            continue
        if not file_path:
            old_path, file_path = next(records), next(records)
            for line_counts in (added_by_file, removed_by_file):
                line_counts[file_path] += line_counts.pop(old_path, 0)
        if not added_text.isdigit() or not removed_text.isdigit():
            continue
        added_by_file[file_path] += int(added_text)
        removed_by_file[file_path] += int(removed_text)

    return [
        (added - removed_by_file[file_path], added, removed_by_file[file_path], file_path)
        for file_path, added in added_by_file.items()
    ]


def sort_rows(rows: list[LineRankRow], sort_name: str = "n") -> list[LineRankRow]:
    """Sort rows ascending by net (n), added (a), or removed (r) lines."""
    sort_idx = {"n": 0, "a": 1, "r": 2}[sort_name]
    return sorted(rows, key=lambda row: (row[sort_idx], row[1], row[3]))


def normalize_history_args(
    repo: str,
    git_args: Sequence[str],
    *,
    right_side_only: bool = False,
) -> tuple[list[str], list[str]]:
    """Split git_args into (revision args, pathspec tail), expanding history shortcuts.

    ``@~N``/``HEAD~N`` become ranges, bare commit SHAs select just that commit, and
    right_side_only turns symmetric ``a...b`` ranges into ``a..b``.
    """
    pathspec_idx = pathspec_index(git_args)
    revision_args = [
        arg.replace("...", "..", 1) if right_side_only and not arg.startswith("-") else arg
        for arg in git_args[:pathspec_idx]
    ]
    git_path = command_path("git")
    for idx, arg in enumerate(revision_args):
        if shortcut_match := re.fullmatch(r"(@|HEAD)~\d+", arg):
            revision_args[idx] = f"{arg}..{shortcut_match[1]}"
        elif re.fullmatch(r"[0-9a-fA-F]{4,40}", arg):
            rev_parse_args = ["rev-parse", "--verify", "--quiet", f"{arg}^{{commit}}"]
            rev_check = subprocess.run(
                [git_path, "-C", repo, *rev_parse_args], check=False, capture_output=True
            )
            if rev_check.returncode == 0:
                revision_args[idx] = f"{arg}^!"
    return revision_args, list(git_args[pathspec_idx:])


def collect_line_rank_rows(
    repo: str,
    source_name: str,
    git_args: Sequence[str],
    sort_name: str = "n",
) -> list[LineRankRow]:
    """Collect per-file line counts for the requested source, sorted by sort_name."""
    if source_name == "history":
        revision_args, pathspec_args = normalize_history_args(repo, git_args)
        log_args = [arg for arg in revision_args if arg != "--reverse"]
        flags = ["--reverse", "--numstat", "-z", "--find-renames=40%", "--pretty=tformat:"]
        numstat_stdout = git_stdout(
            ["-C", repo, "log", *log_args, *flags, *pathspec_args], "gdiff: git log failed"
        )
    elif source_name == "staged_files":
        staged_files = git_stdout(
            ["-C", repo, "diff", "--cached", "--name-only", "-z", *git_args],
            "gdiff: git diff --cached failed",
        ).split("\0")[:-1]
        numstat_stdout = ""
        if staged_files:
            numstat_stdout = git_stdout(
                ["-C", repo, "diff", "--numstat", "HEAD", "--", *staged_files],
                "gdiff: git diff failed",
            )
    else:
        base_args = {"local": ["HEAD"], "staged": ["--cached"]}.get(source_name, [])
        numstat_stdout = git_stdout(
            ["-C", repo, "diff", "--numstat", *base_args, *git_args], "gdiff: git diff failed"
        )

    rows = parse_numstat_rows(numstat_stdout)
    if source_name in {"local", "unstaged"}:
        pathspec_args = list(git_args[pathspec_index(git_args) :])
        if not pathspec_args and not any(arg.startswith("-") for arg in git_args):
            pathspec_args = ["--", *git_args]  # bare args are pathspecs
        untracked_stdout = git_stdout(
            ["-C", repo, "ls-files", "--others", "--exclude-standard", "-z", *pathspec_args],
            "gdiff: git ls-files failed",
        )
        for file_path in filter(None, untracked_stdout.split("\0")):
            try:
                with open(f"{repo}/{file_path}", encoding="utf-8") as file:
                    added = sum(1 for _line in file)
            except (OSError, UnicodeDecodeError):
                continue
            if added:
                rows.append((added, added, 0, file_path))
    # Untracked files never appear in git diff, so rows need no re-aggregation.
    return sort_rows(rows, sort_name)


def commit_summary_lines(
    commits: Sequence[CommitSummary],
    max_message_chars: int = 80,
    max_commit_count: int = 10,
) -> list[str]:
    """Format selected commits, abbreviating long messages and commit lists."""
    if len(commits) <= 1:
        return []
    lines = [
        f"{sha} ({file_count} files) {message[:max_message_chars]}"
        for sha, file_count, message in commits
    ]
    if len(lines) <= max_commit_count:
        return lines
    first_count, hidden_count = max_commit_count // 2, len(lines) - max_commit_count
    return [
        *lines[:first_count],
        f"... ({hidden_count} more)",
        *lines[first_count + hidden_count :],
    ]


def line_expr(
    row: LineRankRow, style: Callable[[str, str], str] = lambda _kind, text: text
) -> str:
    """Return a compact added/removed/net expression, styling each term by its kind."""
    net, added, removed, _ = row
    parts: list[str] = []
    if added:
        parts.append(style("added", f"{added:+d}"))
    if removed:
        parts.append(style("removed", f"-{removed}"))
    if added and removed:
        net_kind = "net-positive" if net > 0 else "net-negative" if net < 0 else ""
        parts.extend(["=", style(net_kind, f"{net:+d}") if net_kind else f"{net:+d}"])
    return " ".join(parts)


def total_row(rows: Sequence[LineRankRow]) -> LineRankRow:
    """Return a total row for displayed rows."""
    added = sum(row[1] for row in rows)
    removed = sum(row[2] for row in rows)
    return (added - removed, added, removed, "total")


def print_table(rows: Sequence[LineRankRow]) -> None:
    """Print rows as an aligned shell table."""
    rows_with_total = [*rows, total_row(rows)]
    width = max(len("lines"), *(len(line_expr(row)) for row in rows_with_total))
    color_enabled = "FORCE_COLOR" in os.environ or (
        "NO_COLOR" not in os.environ and sys.stdout.isatty()
    )

    def paint(kind: str, text: str) -> str:
        """Wrap text in the ANSI color for kind when color is enabled."""
        return f"{ANSI_BY_KIND[kind]}{text}{ANSI_RESET}" if color_enabled and kind else text

    print(f"{'lines':>{width}}  file")
    for row in rows_with_total:
        padding = " " * (width - len(line_expr(row)))
        print(f"{padding}{line_expr(row, paint)}  {paint(file_kind(row[3]), row[3])}")


def file_kind(file_path: str) -> str:
    """Return the display category (test-file, code-file or "") for a file path."""
    file_name = os.path.basename(file_path)
    stem, ext = os.path.splitext(file_name)
    if (
        file_path.startswith("tests/")
        or file_name.startswith("test_")
        or stem in {"test", "tests"}
        or ".test." in file_name
        or ".spec." in file_name
    ):
        return "test-file"
    return "code-file" if CODE_EXT_PATTERN.fullmatch(ext) else ""


def write_html_report(repo: str, rows: Sequence[LineRankRow], commit_lines: list[str]) -> str:
    """Write rows (plus a total) as an HTML report linking each file, returning its path."""
    repo_name = os.path.basename(repo)
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "cursor"
    try:
        editor_cmd = os.path.basename(shlex.split(editor)[0])
    except ValueError:
        editor_cmd = os.path.basename(editor)
    url_scheme = {"cursor": "cursor://file", "code": "vscode://file"}.get(
        editor_cmd.removesuffix("-insiders"), "file://"
    )
    html_row_lines: list[str] = []
    for row in [*rows, total_row(rows)]:
        file_path = row[3]
        file_class = file_kind(file_path)
        class_attr = f' class="{file_class}"' if file_class else ""
        file_cell = f"<code{class_attr}>{escape(file_path)}</code>"
        if file_path != "total":
            file_url = url_scheme + quote(f"{repo}/{file_path}")
            file_cell = f'<a href="{escape(file_url, quote=True)}">{file_cell}</a>'
        line_html = line_expr(row, lambda kind, text: f'<span class="{kind}">{text}</span>')
        html_row_lines.append(f'<tr><td class="num">{line_html}</td><td>{file_cell}</td></tr>')
    html_rows = "\n".join(html_row_lines)
    commit_text = escape("\n".join(commit_lines))
    commits_html = f"<h2>Commits</h2>\n<pre>{commit_text}</pre>\n" if commit_text else ""
    with tempfile.NamedTemporaryFile(
        "w", delete=False, encoding="utf-8", prefix="gdiff-", suffix=".html"
    ) as report_file:
        report_file.write(
            f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Line Rank: {escape(repo_name)}</title>
<style>
{HTML_STYLE}
</style>
</head>
<body>
<h1>Line Rank: <code>{escape(repo_name)}</code></h1>
<p>Sorted by net lines added. Source: <code>{escape(repo)}</code></p>
{commits_html}<table>
<thead><tr><th class="num">Lines</th><th>File</th></tr></thead>
<tbody>
{html_rows}
</tbody>
</table>
</body>
</html>
"""
        )
    return report_file.name


def main(args: Sequence[str] | None = None) -> int:
    """Run the git line rank CLI."""
    format_name, limit, sort_name, source_name, git_args = parse_args(
        sys.argv[1:] if args is None else args
    )
    repo = git_stdout(["rev-parse", "--show-toplevel"], "gdiff: not inside a git repo", 2)
    rows = collect_line_rank_rows(repo, source_name, git_args, sort_name)
    if limit:  # rows ascend, so the top-ranked files are at the end
        rows = rows[-limit:]

    if not rows:
        print("gdiff: no text-file line changes found")
        return 0

    commit_lines: list[str] = []
    if source_name in {"history", "diff"}:
        revision_args, pathspec_args = normalize_history_args(
            repo, git_args, right_side_only=source_name == "diff"
        )
        summary_flags = ["--no-patch", "--shortstat", "--format=%x00%h%x09%s"]
        summary_stdout = git_stdout(
            ["-C", repo, "log", *revision_args, *summary_flags, *pathspec_args],
            "gdiff: git log failed",
        )
        summaries: list[CommitSummary] = []
        for record in summary_stdout.split("\0")[1:]:
            sha, message = record.splitlines()[0].split("\t", 1)
            file_count_match = re.search(r"(\d+) files? changed", record)
            file_count = int(file_count_match[1]) if file_count_match else 0
            summaries.append((sha, file_count, message))
        commit_lines = commit_summary_lines(summaries)
    if format_name != "html" and commit_lines:
        print(*commit_lines, sep="\n", end="\n\n")
    if format_name == "table":
        print_table(rows)
    elif format_name == "markdown":
        print("| Lines | File |")
        print("| ---: | --- |")
        for row in [*rows, total_row(rows)]:
            file_path = row[3]
            md_file_path = file_path.replace("|", "\\|").replace("`", "&#96;")
            print(f"| {line_expr(row)} | `{md_file_path}` |")
    else:
        report_path = write_html_report(repo, rows, commit_lines)
        report_url = "file://" + quote(report_path)
        if not webbrowser.open(report_url) and sys.platform == "darwin":
            subprocess.run([command_path("open"), report_path], check=False)
        print(f"Opened {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
