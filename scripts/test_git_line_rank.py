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
email = "user.email=test@example.com"


@pytest.fixture
def git_path() -> str:
    """Return the git executable path or skip tests."""
    git_path = shutil.which("git")
    if git_path is not None:
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


@pytest.fixture
def changed_repo(tmp_path: Path, git_path: str) -> str:
    """Create a repo with one staged and one unstaged text change."""
    repo = str(tmp_path)
    run_git(git_path, repo, ["init"])
    (tmp_path / "staged.txt").write_text("old\n", encoding="utf-8")
    (tmp_path / "unstaged.txt").write_text("keep\nremove\n", encoding="utf-8")
    run_git(git_path, repo, ["add", "."])
    args = ["-c", "user.name=Test User", "-c", email, "commit", "-m", "initial"]
    run_git(git_path, repo, args)

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
    """Aggregate text numstat rows and skip binary rows."""
    rows = git_line_rank.parse_numstat_rows("2\t1\ta.py\n-\t-\tbinary.bin\n3\t0\ta.py\n")
    assert rows == [(4, 5, 1, "a.py")]


def test_history_sources_accept_commit_and_relative_revisions(
    tmp_path: Path, git_path: str
) -> None:
    """History mode accepts single commits and @~N ranges."""
    repo = str(tmp_path)
    run_git(git_path, repo, ["init"])
    for history_text, other_text, message in [
        ("base\n", "base\n", "base"),
        ("base\none\n", "base\n", "one"),
        ("base\none\ntwo\n", "base\ntwo\n", "two"),
    ]:
        (tmp_path / "history.txt").write_text(history_text, encoding="utf-8")
        (tmp_path / "other.txt").write_text(other_text, encoding="utf-8")
        run_git(git_path, repo, ["add", "history.txt", "other.txt"])
        run_git(
            git_path, repo, ["-c", "user.name=Test User", "-c", email, "commit", "-m", message]
        )

    def history_rows(args: list[str]) -> list[tuple[int, int, int, str]]:
        """Collect history rows from the test repo."""
        return git_line_rank.collect_line_rank_rows(repo, "history", args)

    middle_commit = run_git(git_path, repo, ["rev-parse", "HEAD~1"]).stdout.strip()
    last_two_commits = [
        (2, 2, 0, "history.txt"),
        (1, 1, 0, "other.txt"),
    ]
    assert history_rows([middle_commit]) == [(1, 1, 0, "history.txt")]
    assert history_rows(["@~2"]) == last_two_commits
    assert history_rows(["HEAD~2"]) == last_two_commits
    pathspec_rows = history_rows(["@~2", "--", "history.txt"])
    assert pathspec_rows == [(2, 2, 0, "history.txt")]
    assert history_rows(["HEAD"]) == [
        (3, 3, 0, "history.txt"),
        (2, 2, 0, "other.txt"),
    ]


@pytest.mark.parametrize(
    ("sort_name", "expected_files"),
    [
        ("n", ["net.py", "added.py", "removed.py"]),
        ("a", ["added.py", "net.py", "removed.py"]),
        ("r", ["removed.py", "added.py", "net.py"]),
    ],
)
def test_sort_line_rank_rows_uses_requested_metric(
    sort_name: str, expected_files: list[str]
) -> None:
    """Sort rows by net, added, or removed lines."""
    rows = [(5, 5, 0, "net.py"), (4, 8, 4, "added.py"), (-6, 0, 6, "removed.py")]
    sorted_files = [row[3] for row in git_line_rank.sort_line_rank_rows(rows, sort_name)]
    assert sorted_files == expected_files


def test_total_row_sums_displayed_rows() -> None:
    """Total row sums net, added, and removed values."""
    rows = [(2, 3, 1, "added.py"), (-1, 0, 1, "removed.py")]
    assert git_line_rank.total_row(rows) == (1, 3, 2, "total")


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        ("src/app.py", "code"),
        ("tests/test_app.py", "test"),
        ("test_app.py", "test"),
        ("src/app.test.ts", "test"),
        ("readme.md", ""),
    ],
)
def test_file_kind_detects_code_and_test_files(file_path: str, expected: str) -> None:
    """Classify code and test file paths."""
    assert git_line_rank.file_kind(file_path) == expected


def test_print_table_formats_signed_numbers(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Table output includes explicit signs for every number."""
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    git_line_rank.print_table(
        [(2, 3, 1, "src/added.py"), (-1, 0, 1, "tests/removed.py"), (0, 1, 1, "changed.md")]
    )
    assert capsys.readouterr().out == (
        "     lines  file\n"
        "+3 -1 = +2  src/added.py\n"
        "        -1  tests/removed.py\n"
        "+1 -1 = +0  changed.md\n"
        "+4 -3 = +1  total\n"
    )


def test_print_table_colors_added_and_removed_columns(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal table colors net by sign plus added and removed values."""
    monkeypatch.setenv("FORCE_COLOR", "1")
    git_line_rank.print_table(
        [
            (2, 3, 1, "src/added.py"),
            (-1, 0, 1, "tests/removed.py"),
            (0, 1, 1, "changed.md"),
        ]
    )
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


def test_print_markdown_formats_signed_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    """Markdown output includes explicit signs for every number."""
    git_line_rank.print_markdown([(0, 1, 1, "changed.py")])
    assert capsys.readouterr().out == (
        "| Lines | File |\n"
        "| ---: | --- |\n"
        "| +1 -1 = +0 | `changed.py` |\n"
        "| +1 -1 = +0 | `total` |\n"
    )


def test_html_table_row_formats_signed_numbers() -> None:
    """HTML output includes explicit signs for every number."""
    row = git_line_rank.html_table_row("/repo", (-1, 0, 1, "tests/removed.py"))
    assert '<span class="removed">-1</span>' in row
    assert 'class="test-file"' in row
    assert "net-negative" not in row


def test_renderers_hide_empty_numeric_columns(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Renderers omit zero terms and net when one side is zero."""
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    git_line_rank.print_table([(2, 2, 0, "added.py")])
    assert capsys.readouterr().out == "lines  file\n   +2  added.py\n   +2  total\n"

    git_line_rank.print_markdown([(-2, 0, 2, "removed.py")])
    assert capsys.readouterr().out == (
        "| Lines | File |\n| ---: | --- |\n| -2 | `removed.py` |\n| -2 | `total` |\n"
    )

    row = git_line_rank.html_table_row("/repo", (2, 2, 0, "src/added.py"))
    assert '<span class="added">+2</span>' in row
    assert 'class="code-file"' in row
    assert " = " not in row
    assert "-0" not in row
    total_row = git_line_rank.html_table_row("/repo", (2, 2, 0, "total"))
    assert "<code>total</code>" in total_row
    assert "href=" not in total_row


@pytest.mark.parametrize(
    ("source_name", "expected"),
    [
        (
            "local",
            [
                (2, 2, 0, "staged.txt"),
                (2, 2, 0, "untracked.txt"),
                (0, 1, 1, "unstaged.txt"),
            ],
        ),
        ("staged", [(1, 1, 0, "staged.txt")]),
        ("staged_files", [(2, 2, 0, "staged.txt")]),
        (
            "unstaged",
            [(2, 2, 0, "untracked.txt"), (1, 1, 0, "staged.txt"), (0, 1, 1, "unstaged.txt")],
        ),
    ],
)
def test_local_line_rank_sources(
    changed_repo: str, source_name: str, expected: list[tuple[int, int, int, str]]
) -> None:
    """Local sources include the expected staged, unstaged, and untracked changes."""
    assert git_line_rank.collect_line_rank_rows(changed_repo, source_name, []) == expected
