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
from collections.abc import Sequence
from html import escape
from urllib.request import pathname2url

LineRankRow = tuple[int, int, int, str]
ParsedArgs = tuple[str, int, str, str, list[str]]
NUMSTAT_FIELD_COUNT = 3
TOTAL_LABEL = "total"
CODE_EXTS = {
    ".c",
    ".cpp",
    ".css",
    ".go",
    ".html",
    ".js",
    ".jsx",
    ".py",
    ".rs",
    ".svelte",
    ".ts",
    ".tsx",
}
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_BLUE = "\033[34m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
HTML_STYLE = """
body {
  color: #222;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  margin: 2rem;
}
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid #ddd; padding: 0.35rem 0.5rem; text-align: left; }
th { position: sticky; top: 0; background: white; }
td.num, th.num { font-variant-numeric: tabular-nums; text-align: right; }
tr:hover { background: #f7f7f7; }
a { color: inherit; text-decoration-color: #999; text-underline-offset: 0.15rem; }
a:hover { text-decoration-color: currentColor; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.added { color: #16a34a; }
.removed { color: #dc2626; }
.net-positive { color: #16a34a; }
.net-negative { color: #dc2626; }
.code-file { color: #2563eb; }
.test-file { color: #ca8a04; }
""".strip()


def parse_args(args: Sequence[str]) -> ParsedArgs:
    """Parse glines arguments and pass unrecognized values through to git."""
    parser = argparse.ArgumentParser(
        prog="glines",
        allow_abbrev=False,
        description="Rank files in the current git repo by net lines added.",
        epilog=(
            "Examples:\n"
            "  glines\n"
            "  glines --staged\n"
            "  glines --staged-files\n"
            "  glines @~5\n"
            "  glines 1a2b3c4\n"
            "  glines --unstaged -- '*.py'\n"
            "  glines -n 25 --markdown\n"
            "  glines --history --html --since=1.year\n"
            "  glines --history --author='Jane Doe' -- '*.py'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--limit", type=int, default=0)
    parser.add_argument("--sort", choices=["a", "r", "n"], default="n")
    for group, dest, options in [
        (
            parser.add_mutually_exclusive_group(),
            "source_name",
            [
                (("--local",), "local"),
                (("-s", "--staged"), "staged"),
                (("--staged-files",), "staged_files"),
                (("-u", "--unstaged"), "unstaged"),
                (("--history",), "history"),
            ],
        ),
        (
            parser.add_mutually_exclusive_group(),
            "format_name",
            [
                (("--table",), "table"),
                (("--md", "--markdown"), "markdown"),
                (("--html",), "html"),
            ],
        ),
    ]:
        for flags, const in options:
            group.add_argument(
                *flags,
                dest=dest,
                action="store_const",
                const=const,
            )
    parser.set_defaults(format_name="table", source_name=None)

    parsed_args, git_args = parser.parse_known_args(args)
    if parsed_args.limit < 0:
        parser.error("--limit expects a non-negative integer")
    source_name = parsed_args.source_name or ("history" if git_args else "local")
    return parsed_args.format_name, parsed_args.limit, parsed_args.sort, source_name, git_args


def command_path(command: str) -> str:
    """Return the absolute path to an executable on PATH."""
    abs_command_path = shutil.which(command)
    if abs_command_path is None:
        print(f"glines: command not found: {command}", file=sys.stderr)
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


def parse_numstat_rows(numstat_stdout: str, sort_name: str = "n") -> list[LineRankRow]:
    """Parse git numstat output into sorted line-rank rows."""
    added_by_file: Counter[str] = Counter()
    removed_by_file: Counter[str] = Counter()
    for line in numstat_stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != NUMSTAT_FIELD_COUNT:
            continue
        added_text, removed_text, file_path = parts
        if not added_text.isdigit() or not removed_text.isdigit():
            continue
        added_by_file[file_path] += int(added_text)
        removed_by_file[file_path] += int(removed_text)

    return rows_from_counters(added_by_file, removed_by_file, sort_name)


def rows_from_counters(
    added_by_file: Counter[str],
    removed_by_file: Counter[str],
    sort_name: str = "n",
) -> list[LineRankRow]:
    """Return sorted line-rank rows from added and removed counters."""
    return sort_line_rank_rows(
        [
            (
                added_by_file[file_path] - removed_by_file[file_path],
                added_by_file[file_path],
                removed_by_file[file_path],
                file_path,
            )
            for file_path in added_by_file
        ],
        sort_name,
    )


def sort_line_rank_rows(
    rows: Sequence[LineRankRow], sort_name: str = "n"
) -> list[LineRankRow]:
    """Sort line-rank rows by net lines, added lines, and file path."""
    sort_idx = {"n": 0, "a": 1, "r": 2}[sort_name]
    return sorted(rows, key=lambda row: (-row[sort_idx], -row[1], row[3]))


def normalize_history_args(repo: str, git_args: Sequence[str]) -> list[str]:
    """Expand glines history shortcuts without changing normal git-log refs."""
    history_args = list(git_args)
    pathspec_idx = history_args.index("--") if "--" in history_args else len(history_args)
    normalized_args: list[str] = []
    git_path = command_path("git")
    for arg in history_args[:pathspec_idx]:
        if arg.startswith(("-", "^")) or ".." in arg:
            normalized_args.append(arg)
            continue
        if arg.startswith("@~") and arg[2:].isdigit():
            normalized_args.append(f"{arg}..@")
            continue
        if arg.startswith("HEAD~") and arg[5:].isdigit():
            normalized_args.append(f"{arg}..HEAD")
            continue
        rev_check = subprocess.run(
            [
                git_path,
                "-C",
                repo,
                "rev-parse",
                "--verify",
                "--quiet",
                f"{arg}^{{commit}}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        is_hex_sha = re.fullmatch(r"[0-9a-fA-F]{4,40}", arg) is not None
        normalized_args.append(f"{arg}^!" if rev_check.returncode == 0 and is_hex_sha else arg)
    return [*normalized_args, *history_args[pathspec_idx:]]


def collect_line_rank_rows(
    repo: str,
    source_name: str,
    git_args: Sequence[str],
    sort_name: str = "n",
) -> list[LineRankRow]:
    """Collect per-file line counts for the requested source."""
    if source_name == "history":
        return parse_numstat_rows(
            git_stdout(
                [
                    "-C",
                    repo,
                    "log",
                    "--numstat",
                    "--pretty=tformat:",
                    *normalize_history_args(repo, git_args),
                ],
                "glines: git log failed",
            ),
            sort_name,
        )
    if source_name == "staged_files":
        staged_files = git_stdout(
            ["-C", repo, "diff", "--cached", "--name-only", "-z", *git_args],
            "glines: git diff --cached failed",
        ).split("\0")[:-1]
        if not staged_files:
            return []
        return parse_numstat_rows(
            git_stdout(
                ["-C", repo, "diff", "--numstat", "HEAD", "--", *staged_files],
                "glines: git diff failed",
            ),
            sort_name,
        )
    diff_args = ["-C", repo, "diff", "--numstat"]
    if source_name == "local":
        diff_args.append("HEAD")
    elif source_name == "staged":
        diff_args.append("--cached")
    diff_args.extend(git_args)

    rows = parse_numstat_rows(git_stdout(diff_args, "glines: git diff failed"), sort_name)
    if source_name in {"local", "unstaged"}:
        if "--" in git_args:
            separator_idx = git_args.index("--")
            pathspec_args = ["--", *git_args[separator_idx + 1 :]]
        else:
            pathspec_only = git_args and all(not arg.startswith("-") for arg in git_args)
            pathspec_args = ["--", *git_args] if pathspec_only else []
        untracked_stdout = git_stdout(
            [
                "-C",
                repo,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                *pathspec_args,
            ],
            "glines: git ls-files failed",
        )
        for file_path in filter(None, untracked_stdout.split("\0")):
            try:
                with open(f"{repo}/{file_path}", encoding="utf-8") as file:
                    added = sum(1 for _line in file)
            except (OSError, UnicodeDecodeError):
                continue
            if added:
                rows.append((added, added, 0, file_path))

    added_by_file: Counter[str] = Counter()
    removed_by_file: Counter[str] = Counter()
    for _, added, removed, file_path in rows:
        added_by_file[file_path] += added
        removed_by_file[file_path] += removed
    return rows_from_counters(added_by_file, removed_by_file, sort_name)


def line_expr(row: LineRankRow) -> str:
    """Return a compact added/removed/net expression."""
    net, added, removed, _ = row
    parts: list[str] = []
    if added:
        parts.append(f"{added:+d}")
    if removed:
        parts.append(f"-{removed}")
    if added and removed:
        parts.extend(["=", f"{net:+d}"])
    return " ".join(parts)


def total_row(rows: Sequence[LineRankRow]) -> LineRankRow:
    """Return a total row for displayed rows."""
    added = sum(row[1] for row in rows)
    removed = sum(row[2] for row in rows)
    return (added - removed, added, removed, TOTAL_LABEL)


def print_table(rows: Sequence[LineRankRow]) -> None:
    """Print rows as an aligned shell table."""
    rows_with_total = [*rows, total_row(rows)]
    width = max(len("lines"), *(len(line_expr(row)) for row in rows_with_total))
    print(f"{'lines':>{width}}  file")
    for row in rows_with_total:
        net, added, removed, file_path = row
        line_parts: list[str] = []
        if added:
            line_parts.append(terminal_color(f"{added:+d}", ANSI_GREEN))
        if removed:
            line_parts.append(terminal_color(f"-{removed}", ANSI_RED))
        if added and removed:
            color_code = ANSI_GREEN if net > 0 else ANSI_RED if net < 0 else ""
            net_text = f"{net:+d}"
            net_text = terminal_color(net_text, color_code) if color_code else net_text
            line_parts.extend(["=", net_text])
        color_code = {"code": ANSI_BLUE, "test": ANSI_YELLOW}.get(file_kind(file_path))
        file_text = terminal_color(file_path, color_code) if color_code else file_path
        line_text = " " * (width - len(line_expr(row))) + " ".join(line_parts)
        print(f"{line_text}  {file_text}")


def terminal_color(text: str, color_code: str) -> str:
    """Return terminal-colored text when color output is enabled."""
    force_color = "FORCE_COLOR" in os.environ
    if not force_color and ("NO_COLOR" in os.environ or not sys.stdout.isatty()):
        return text
    return f"{color_code}{text}{ANSI_RESET}"


def file_kind(file_path: str) -> str:
    """Return the display category for a file path."""
    file_name = os.path.basename(file_path)
    if (
        file_path.startswith("tests/")
        or file_name.startswith("test_")
        or ".test." in file_name
        or ".spec." in file_name
    ):
        return "test"
    if os.path.splitext(file_name)[1] in CODE_EXTS:
        return "code"
    return ""


def print_markdown(rows: Sequence[LineRankRow]) -> None:
    """Print rows as a Markdown table."""
    print("| Lines | File |")
    print("| ---: | --- |")
    for row in [*rows, total_row(rows)]:
        file_path = row[3]
        md_file_path = file_path.replace("|", "\\|").replace("`", "&#96;")
        print(f"| {line_expr(row)} | `{md_file_path}` |")


def html_table_row(
    repo: str,
    row: LineRankRow,
) -> str:
    """Return one HTML table row."""
    net, added, removed, file_path = row
    line_parts: list[str] = []
    if added:
        line_parts.append(f'<span class="added">{added:+d}</span>')
    if removed:
        line_parts.append(f'<span class="removed">-{removed}</span>')
    if added and removed:
        net_class = "net-positive" if net > 0 else "net-negative" if net < 0 else ""
        net_text = f"{net:+d}"
        net_html = f'<span class="{net_class}">{net_text}</span>' if net_class else net_text
        line_parts.extend(["=", net_html])

    escaped_file_path = escape(file_path)
    file_class = file_kind(file_path)
    class_attr = f' class="{file_class}-file"' if file_class else ""
    file_cell = f"<code{class_attr}>{escaped_file_path}</code>"
    if file_path != TOTAL_LABEL:
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "cursor"
        try:
            editor_cmd = os.path.basename(shlex.split(editor)[0])
        except ValueError:
            editor_cmd = os.path.basename(editor)
        encoded_path = pathname2url(f"{repo}/{file_path}")
        if editor_cmd in {"cursor", "cursor-insiders"}:
            file_url = f"cursor://file{encoded_path}"
        elif editor_cmd in {"code", "code-insiders"}:
            file_url = f"vscode://file{encoded_path}"
        else:
            file_url = "file://" + encoded_path
        file_url = escape(file_url, quote=True)
        file_cell = f'<a href="{file_url}">{file_cell}</a>'
    return f'<tr><td class="num">{" ".join(line_parts)}</td><td>{file_cell}</td></tr>'


def main(args: Sequence[str] | None = None) -> int:
    """Run the git line rank CLI."""
    format_name, limit, sort_name, source_name, git_args = parse_args(
        sys.argv[1:] if args is None else args
    )
    repo = git_stdout(
        ["-C", os.getcwd(), "rev-parse", "--show-toplevel"],
        "glines: not inside a git repo",
        2,
    )
    rows = collect_line_rank_rows(repo, source_name, git_args, sort_name)
    if limit:
        rows = rows[:limit]

    if not rows:
        print("glines: no text-file line changes found")
        return 0

    if format_name == "table":
        print_table(rows)
    elif format_name == "markdown":
        print_markdown(rows)
    else:
        repo_name = os.path.basename(repo)
        html_rows = "\n".join(html_table_row(repo, row) for row in [*rows, total_row(rows)])
        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8", prefix="git-line-rank-", suffix=".html"
        ) as report_file:
            report_path = report_file.name
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
<p>Sorted by net lines added over git history. Source: <code>{escape(repo)}</code></p>
<table>
<thead>
<tr>
<th class="num">Lines</th><th>File</th>
</tr>
</thead>
<tbody>
{html_rows}
</tbody>
</table>
</body>
</html>
"""
            )
        report_url = "file://" + pathname2url(report_path)
        if not webbrowser.open(report_url) and sys.platform == "darwin":
            subprocess.run([command_path("open"), report_path], check=False)
        print(f"Opened {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
