"""Tests for shell and macOS configuration."""

import base64
import json
import os
import plistlib
import runpy
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("relative_path", "setting"),
    [
        ("dotfiles/.zshrc", "HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1"),
        ("dotfiles/.bashrc", "HISTCONTROL=ignoreboth:erasedups"),
        # Full loop line, not a bare path: prose elsewhere in the file matches a substring.
        (
            "setup/3-config.sh",
            "for dest in ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.cursor/skills",
        ),
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


def test_text_replacements(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Decode private values, retire shortcuts, and preserve unrelated local settings."""
    with open(
        f"{os.path.dirname(__file__)}/../setup/3-config.sh", encoding="utf-8"
    ) as source_file:
        script = source_file.read().split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    script_path = tmp_path / "sync.py"
    script_path.write_text(script)
    config_path = tmp_path / "replacements.json"
    expected = {"local": "untouched", "ustel": "+1 202 555 0123", "hello": "Hello\nworld"}
    config = {"oldtel": None, "ustel": expected["ustel"], "hello": expected["hello"]}
    encoded = {
        key: value and base64.b64encode(value.encode()).decode()
        for key, value in config.items()
    }
    config_path.write_text(json.dumps(encoded))
    database_dir = tmp_path / "Library/KeyboardServices"
    database_dir.mkdir(parents=True)
    database_path = database_dir / "TextReplacements.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript("""
            CREATE TABLE ZTEXTREPLACEMENTENTRY (
                Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER,
                ZNEEDSSAVETOCLOUD INTEGER, ZWASDELETED INTEGER, ZTIMESTAMP REAL,
                ZPHRASE TEXT, ZSHORTCUT TEXT, ZUNIQUENAME TEXT, ZREMOTERECORDINFO BLOB
            );
            CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_MAX INTEGER);
            INSERT INTO Z_PRIMARYKEY VALUES (1, 10);
            INSERT INTO ZTEXTREPLACEMENTENTRY VALUES
                (1, 1, 1, 0, 0, 0, 'retired', 'oldtel', 'old-id', NULL),
                (2, 1, 1, 0, 0, 0, 'untouched', 'local', 'local-id', NULL),
                (3, 1, 1, 0, 0, 0, 'previous', 'ustel', 'us-id', NULL);
        """)
    settings = {
        "KeyRepeat": 2,
        "NSLinguisticDataAssetsRequestTime": datetime.fromisoformat(
            "2026-01-02T03:04:05.123456"
        ),
        "NSUserDictionaryReplacementItems": [
            {"on": 1, "replace": "oldtel", "with": "retired"},
            {"on": 1, "replace": "local", "with": "untouched"},
        ],
    }

    service_commands: list[list[str]] = []

    def run_command(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        """Capture imported preferences and suppress the service restart."""
        if command[:3] == ["defaults", "export", "-g"]:
            assert command[3] != "-"  # XML stdout export discards timestamp precision.
            with open(command[3], "wb") as plist_file:
                plistlib.dump(settings, plist_file, fmt=plistlib.FMT_BINARY)
        elif command[0] == "defaults":
            assert command[:3] == ["defaults", "import", "-g"]
            with open(command[3], "rb") as plist_file:
                settings.clear()
                settings.update(plistlib.load(plist_file))
        else:
            service_commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [str(script_path), str(config_path)])
    monkeypatch.setattr(subprocess, "run", run_command)
    original_key_repeat = settings["KeyRepeat"]
    original_timestamp = settings["NSLinguisticDataAssetsRequestTime"]
    for _ in range(2):
        service_commands.clear()
        runpy.run_path(str(script_path))
        assert service_commands == [
            ["killall", "keyboardservicesd"],
            ["launchctl", "start", "com.apple.keyboardservicesd"],
            ["pkill", "-TERM", "-u", str(os.getuid()), "-x", "cfprefsd"],
        ]
        assert settings["KeyRepeat"] == original_key_repeat
        assert settings["NSLinguisticDataAssetsRequestTime"] == original_timestamp
        assert {
            entry["replace"]: entry["with"]
            for entry in settings["NSUserDictionaryReplacementItems"]
        } == expected
        with sqlite3.connect(database_path) as connection:
            active = connection.execute(
                "SELECT ZSHORTCUT, ZPHRASE FROM ZTEXTREPLACEMENTENTRY WHERE ZWASDELETED = 0"
            ).fetchall()
            assert sorted(active) == sorted(expected.items())  # also rejects duplicates
            # Z_OPT 2: the rerun must not bump (and re-sync) an existing tombstone.
            assert connection.execute(
                "SELECT ZWASDELETED, ZNEEDSSAVETOCLOUD, Z_OPT, ZUNIQUENAME "
                "FROM ZTEXTREPLACEMENTENTRY WHERE ZSHORTCUT = 'oldtel'"
            ).fetchone() == (1, 1, 2, "old-id")
