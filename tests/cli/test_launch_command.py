"""The CLI names the command each platform actually has.

Asserted literally, then against the build scripts: the Flatpak id and the
macOS bundle name each have their home in a delivery script, so a rename there
must fail here rather than leave the CLI naming a program that no longer
exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import builddmg
from src.cli.launch_command import (
    LINUX_COMMAND,
    MACOS_COMMAND,
    launch_command_for,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_windows_runs_the_executable() -> None:
    assert launch_command_for("win32") == "AudioDeck.exe"


def test_macos_runs_the_executable_inside_the_bundle() -> None:
    assert (
        launch_command_for("darwin")
        == "/Applications/AudioDeck.app/Contents/MacOS/AudioDeck"
    )


def test_linux_runs_the_flatpak() -> None:
    assert launch_command_for("linux") == "flatpak run uk.codecrafter.AudioDeck"


def test_the_flatpak_command_names_the_id_the_build_installs() -> None:
    script = (PROJECT_ROOT / "build_flatpak.sh").read_text(encoding="utf-8")
    match = re.search(r'^APP_ID="([^"]+)"', script, flags=re.MULTILINE)

    assert match is not None, "build_flatpak.sh no longer declares APP_ID"
    assert LINUX_COMMAND == f"flatpak run {match.group(1)}"


def test_the_macos_command_names_the_bundle_the_build_makes() -> None:
    name = builddmg.APP_NAME

    assert MACOS_COMMAND == f"/Applications/{name}.app/Contents/MacOS/{name}"
