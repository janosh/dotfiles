"""Tests for interactive shell configuration."""

import os

import pytest


@pytest.mark.parametrize(
    ("file_name", "setting"),
    [
        (".zshrc", "HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1"),
        (".bashrc", "HISTCONTROL=ignoreboth:erasedups"),
    ],
)
def test_history_search_ensures_unique_matches(file_name: str, setting: str) -> None:
    """Configure Up-arrow history search to skip duplicate commands."""
    config_path = f"{os.path.dirname(__file__)}/../dotfiles/{file_name}"
    with open(config_path, encoding="utf-8") as config_file:
        assert setting in config_file.read()
