"""Tests for shell and macOS configuration."""

import os

import pytest


@pytest.mark.parametrize(
    ("relative_path", "setting"),
    [
        ("dotfiles/.zshrc", "HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1"),
        ("dotfiles/.bashrc", "HISTCONTROL=ignoreboth:erasedups"),
        ("setup/3-config.sh", "AppleInterfaceStyleSwitchesAutomatically -bool true"),
        ("setup/3-config.sh", "NSAutomaticDashSubstitutionEnabled -bool false"),
        ("setup/3-config.sh", "KeyRepeat -int 2"),
        ("setup/3-config.sh", "InitialKeyRepeat -int 15"),
        ("setup/3-config.sh", "AppleICUForce24HourTime -bool true"),
        ("setup/3-config.sh", "BatteryShowPercentage -bool true"),
        ("setup/3-config.sh", "socketfilterfw --setglobalstate on"),
        ("setup/system-settings.sh", "FileVault is On"),
    ],
)
def test_expected_config_setting(relative_path: str, setting: str) -> None:
    """Keep important shell and macOS defaults in setup."""
    config_path = f"{os.path.dirname(__file__)}/../{relative_path}"
    with open(config_path, encoding="utf-8") as config_file:
        assert setting in config_file.read()
