"""Tests for git line-rank reporting."""

import os
import shutil
import subprocess
import sys
from importlib import util
from pathlib import Path

import pytest

module_path = f"{os.path.dirname(__file__)}/git_line_rank.py"
spec = util.spec_from_file_location("git_line_rank", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"failed to load module spec for {module_path}")
git_line_rank = util.module_from_spec(spec)
sys.modules["git_line_rank"] = git_line_rank
spec.loader.exec_module(git_line_rank)
GIT_IDENTITY_ARGS = ("-c", "user.name=Test User", "-c", "user.email=test@example.com")


@pytest.fixture
def git_path() -> str:
    """Return the git executable path or skip tests."""
    if git_path := shutil.which("git"):
        return git_path
    pytest.skip("git is not installed")


def run_git(git_path: str, repo: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run git in a test repository."""
    return subprocess.run(
        [git_path, "-C", repo, *args],
        check=True,
        capture_output=True,
        text=True,
    )


def commit_all(git_path: str, repo: str, message: str) -> None:
    """Stage and commit all changes in a test repository."""
    run_git(git_path, repo, ["add", "--all"])
    run_git(git_path, repo, [*GIT_IDENTITY_ARGS, "commit", "-m", message])


@pytest.fixture
def changed_repo(tmp_path: Path, git_path: str) -> str:
    """Create a repo with one staged and one unstaged text change."""
    repo = str(tmp_path)
    run_git(git_path, repo, ["init"])
    (tmp_path / "staged.txt").write_text("old\n", encoding="utf-8")
    (tmp_path / "unstaged.txt").write_text("keep\nremove\n", encoding="utf-8")
    commit_all(git_path, repo, "initial")

    (tmp_path / "staged.txt").write_text("old\nnew staged\n", encoding="utf-8")
    run_git(git_path, repo, ["add", "staged.txt"])
    (tmp_path / "staged.txt").write_text("old\nnew staged\nnew unstaged\n", encoding="utf-8")
    (tmp_path / "unstaged.txt").write_text("keep\nnew unstaged\n", encoding="utf-8")
    (tmp_path / "untracked.txt").write_text("new\nuntracked\n", encoding="utf-8")
    return repo


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], ("table", 0, "n", "local", [])),
        (["--sort=a"], ("table", 0, "a", "local", [])),
        (["--staged"], ("table", 0, "n", "staged", [])),
        (["-s"], ("table", 0, "n", "staged", [])),
        (["--staged-files"], ("table", 0, "n", "staged_files", [])),
        (["--unstaged"], ("table", 0, "n", "unstaged", [])),
        (["-u"], ("table", 0, "n", "unstaged", [])),
        (["@~2"], ("table", 0, "n", "history", ["@~2"])),
        (["--history", "--since=1.year"], ("table", 0, "n", "history", ["--since=1.year"])),
        (["--since=1.year"], ("table", 0, "n", "history", ["--since=1.year"])),
        (["--local", "--", "*.py"], ("table", 0, "n", "local", ["--", "*.py"])),
    ],
)
def test_parse_args_selects_source(
    args: list[str], expected: tuple[str, int, str, str, list[str]]
) -> None:
    """Parse source and passthrough args."""
    assert git_line_rank.parse_args(args) == expected


def test_parse_numstat_rows_aggregates_text_changes() -> None:
    """Aggregate text changes, follow renames, and skip binary rows."""
    rows = git_line_rank.parse_numstat_rows("2\t1\ta.py\n-\t-\tbinary.bin\n3\t0\ta.py\n")
    assert rows == [(4, 5, 1, "a.py")]
    rename_numstat = (
        "3\t1\told.py\0\n1\t0\t\0old.py\0new.py\0"
        "\n-\t-\t\0new.py\0final.py\0\n2\t0\tfinal.py\0"
    )
    assert git_line_rank.parse_numstat_rows(rename_numstat) == [(5, 6, 1, "final.py")]


def test_history_sources_accept_revisions_and_print_commit_summaries(
    tmp_path: Path,
    git_path: str,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """History mode accepts revisions and prints selected commit summaries."""
    repo = str(tmp_path)
    run_git(git_path, repo, ["init"])
    base_history = "".join(f"line {idx:02d}\n" for idx in range(10))
    for history_text, other_text, message in [
        (base_history, "base\n", "base"),
        (f"{base_history}one\n", "base\n", "one"),
        (f"{base_history}one\ntwo\n", "base\ntwo\n", "two"),
    ]:
        (tmp_path / "history.txt").write_text(history_text, encoding="utf-8")
        (tmp_path / "other.txt").write_text(other_text, encoding="utf-8")
        commit_all(git_path, repo, message)

    def history_rows(args: list[str]) -> list[tuple[int, int, int, str]]:
        """Collect history rows from the test repo."""
        return git_line_rank.collect_line_rank_rows(repo, "history", args)

    middle_commit = run_git(git_path, repo, ["rev-parse", "HEAD~1"]).stdout.strip()
    last_two_commits = [(1, 1, 0, "other.txt"), (2, 2, 0, "history.txt")]
    assert history_rows([middle_commit]) == [(1, 1, 0, "history.txt")]
    assert history_rows(["@~2"]) == last_two_commits
    assert history_rows(["HEAD~2"]) == last_two_commits
    assert history_rows(["@~2", "--", "history.txt"]) == [(2, 2, 0, "history.txt")]
    assert history_rows(["HEAD"]) == [
        (2, 2, 0, "other.txt"),
        (12, 12, 0, "history.txt"),
    ]
    commit_shas = run_git(git_path, repo, ["log", "-2", "--format=%h"]).stdout.splitlines()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    assert git_line_rank.main(["@~2"]) == 0
    assert capsys.readouterr().out == (
        f"{commit_shas[0]} (2 files) two\n"
        f"{commit_shas[1]} (1 files) one\n"
        "\n"
        "lines  file\n"
        "   +1  other.txt\n"
        "   +2  history.txt\n"
        "   +3  total\n"
    )
    assert git_line_rank.main(["--markdown", "@~2"]) == 0
    assert capsys.readouterr().out == (
        f"{commit_shas[0]} (2 files) two\n"
        f"{commit_shas[1]} (1 files) one\n\n"
        "| Lines | File |\n"
        "| ---: | --- |\n"
        "| +1 | `other.txt` |\n"
        "| +2 | `history.txt` |\n"
        "| +3 | `total` |\n"
    )
    run_git(git_path, repo, ["mv", "history.txt", "moved.txt"])
    unchanged_line_count = 5
    moved_text = "".join(
        f"{'line' if idx < unchanged_line_count else 'new-'} {idx:02d}\n" for idx in range(12)
    )
    for file_text, message in [
        (moved_text, "move and rewrite"),
        (f"{moved_text}final\n", "edit moved file"),
    ]:
        (tmp_path / "moved.txt").write_text(file_text, encoding="utf-8")
        commit_all(git_path, repo, message)
    assert history_rows(["@~2"]) == [(1, 8, 7, "moved.txt")]
    expected_rows = [(1, 1, 0, "other.txt"), (2, 9, 7, "moved.txt")]
    assert history_rows(["@~3"]) == expected_rows
    assert history_rows(["@~3", "--reverse"]) == expected_rows


def test_commit_summary_lines_apply_display_limits() -> None:
    """Hide singleton ranges and limit message length and commit count."""
    format_lines = git_line_rank.commit_summary_lines
    assert format_lines([("aaaaaaa", 1, "one")]) == []
    assert format_lines(
        [("aaaaaaa", 3, "xxxxx"), ("bbbbbbb", 1, "two")], max_message_chars=3
    ) == [
        "aaaaaaa (3 files) xxx",
        "bbbbbbb (1 files) two",
    ]
    commits = [(f"{idx:07x}", idx, f"commit {idx}") for idx in range(5)]
    expected_lines = [f"{sha} ({count} files) {message}" for sha, count, message in commits]
    assert format_lines(commits[:3], max_commit_count=3) == expected_lines[:3]
    assert format_lines(commits, max_commit_count=3) == [
        expected_lines[0],
        "... (2 more)",
        *expected_lines[3:],
    ]


@pytest.mark.parametrize(
    ("sort_name", "expected_files"),
    [
        ("n", ["removed.py", "added.py", "net.py"]),
        ("a", ["removed.py", "net.py", "added.py"]),
        ("r", ["net.py", "added.py", "removed.py"]),
    ],
)
def test_parse_numstat_rows_sorts_by_requested_metric(
    sort_name: str, expected_files: list[str]
) -> None:
    """Sort rows by net, added, or removed lines."""
    numstat = "5\t0\tnet.py\n8\t4\tadded.py\n0\t6\tremoved.py\n"
    sorted_files = [row[3] for row in git_line_rank.parse_numstat_rows(numstat, sort_name)]
    assert sorted_files == expected_files


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        ("test_app.py", "test"),
        ("src/app.test.ts", "test"),
        ("readme.md", ""),
    ],
)
def test_file_kind_detects_code_and_test_files(file_path: str, expected: str) -> None:
    """Classify code and test file paths."""
    assert git_line_rank.file_kind(file_path) == expected


def test_print_table_formats_and_colors_rows(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Table output formats signs, colors, empty terms, and totals."""
    rows = (
        (2, 3, 1, "src/added.py"),
        (-1, 0, 1, "tests/removed.py"),
        (0, 1, 1, "changed.md"),
    )
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    git_line_rank.print_table(rows)
    assert capsys.readouterr().out == (
        "     lines  file\n"
        "+3 -1 = +2  src/added.py\n"
        "        -1  tests/removed.py\n"
        "+1 -1 = +0  changed.md\n"
        "+4 -3 = +1  total\n"
    )

    monkeypatch.setenv("FORCE_COLOR", "1")
    git_line_rank.print_table(rows)
    assert capsys.readouterr().out == (
        "     lines  file\n"
        f"{git_line_rank.ANSI_GREEN}+3{git_line_rank.ANSI_RESET} "
        f"{git_line_rank.ANSI_RED}-1{git_line_rank.ANSI_RESET} = "
        f"{git_line_rank.ANSI_GREEN}+2{git_line_rank.ANSI_RESET}  "
        f"{git_line_rank.ANSI_BLUE}src/added.py{git_line_rank.ANSI_RESET}\n"
        f"        {git_line_rank.ANSI_RED}-1{git_line_rank.ANSI_RESET}  "
        f"{git_line_rank.ANSI_YELLOW}tests/removed.py{git_line_rank.ANSI_RESET}\n"
        f"{git_line_rank.ANSI_GREEN}+1{git_line_rank.ANSI_RESET} "
        f"{git_line_rank.ANSI_RED}-1{git_line_rank.ANSI_RESET} = +0  changed.md\n"
        f"{git_line_rank.ANSI_GREEN}+4{git_line_rank.ANSI_RESET} "
        f"{git_line_rank.ANSI_RED}-3{git_line_rank.ANSI_RESET} = "
        f"{git_line_rank.ANSI_GREEN}+1{git_line_rank.ANSI_RESET}  total\n"
    )
    monkeypatch.delenv("FORCE_COLOR")
    git_line_rank.print_table([(2, 2, 0, "added.py")])
    assert capsys.readouterr().out == "lines  file\n   +2  added.py\n   +2  total\n"


def test_html_report_formats_rows_and_omits_total_link(
    tmp_path: Path,
    git_path: str,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTML report formats added/removed rows and leaves total unlinked."""
    repo = str(tmp_path)
    run_git(git_path, repo, ["init"])
    (tmp_path / "base.txt").write_text("base\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/removed.py").write_text("old\n", encoding="utf-8")
    commit_all(git_path, repo, "initial")
    (tmp_path / "tests/removed.py").write_text("", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/added.py").write_text("new\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(git_line_rank.webbrowser, "open", bool)
    assert git_line_rank.main(["--html"]) == 0
    report_path = capsys.readouterr().out.removeprefix("Opened ").strip()
    with open(report_path, encoding="utf-8") as report_file:
        report_html = report_file.read()
    os.remove(report_path)
    added_row = next(line for line in report_html.splitlines() if "src/added.py" in line)
    removed_row = next(line for line in report_html.splitlines() if "tests/removed.py" in line)
    total_row = next(line for line in report_html.splitlines() if "<code>total</code>" in line)
    assert '<span class="added">+1</span>' in added_row
    assert 'class="code-file"' in added_row
    assert " = " not in added_row
    assert '<span class="removed">-1</span>' in removed_row
    assert 'class="test-file"' in removed_row
    assert "net-negative" not in removed_row
    assert "-0" not in report_html
    assert "href=" not in total_row


@pytest.mark.parametrize(
    ("source_name", "expected"),
    [
        (
            "local",
            [
                (0, 1, 1, "unstaged.txt"),
                (2, 2, 0, "staged.txt"),
                (2, 2, 0, "untracked.txt"),
            ],
        ),
        ("staged", [(1, 1, 0, "staged.txt")]),
        ("staged_files", [(2, 2, 0, "staged.txt")]),
        (
            "unstaged",
            [(0, 1, 1, "unstaged.txt"), (1, 1, 0, "staged.txt"), (2, 2, 0, "untracked.txt")],
        ),
    ],
)
def test_local_line_rank_sources(
    changed_repo: str, source_name: str, expected: list[tuple[int, int, int, str]]
) -> None:
    """Local sources include the expected staged, unstaged, and untracked changes."""
    assert git_line_rank.collect_line_rank_rows(changed_repo, source_name, []) == expected
