"""Tests for detecting and ending a running copy of the application.

The command runner is injected, so these drive the real module against a
hand-written fake rather than patching the subprocess module.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest

from installer import constants as c
from installer import ops, running_app


class FakeRunner:
    """Records the commands it is given and replays scripted results."""

    def __init__(self, results: list[tuple[int, str]]) -> None:
        """Store the results to hand back, oldest first.

        Args:
            results: One (returncode, stdout) pair per expected call. The last
                pair repeats once the list runs out, so a poll can be fed a
                steady state without listing it thirty times.
        """
        self.results = list(results)
        self.commands: list[list[str]] = []

    def __call__(self, command) -> "subprocess.CompletedProcess[str]":
        """Record the command and return the next scripted result."""
        self.commands.append(list(command))
        code, out = self.results[0] if len(self.results) == 1 else self.results.pop(0)
        return subprocess.CompletedProcess(list(command), code, out, "")


class ExplodingRunner:
    """Raises OSError, standing in for a command that cannot be run at all."""

    def __call__(self, command) -> "subprocess.CompletedProcess[str]":
        """Fail the way a missing executable does."""
        raise OSError("tasklist is unavailable")


def test_is_running_finds_the_image() -> None:
    """A tasklist row naming the image means the app is running."""
    runner = FakeRunner([(0, '"AudioDeck.exe","1234","Console","1","90,000 K"')])
    assert running_app.is_running("AudioDeck.exe", runner) is True
    assert runner.commands[0][0] == "tasklist"
    assert "IMAGENAME eq AudioDeck.exe" in runner.commands[0]


def test_is_running_reads_the_no_match_banner() -> None:
    """tasklist reports absence in prose, not as empty output."""
    runner = FakeRunner([(0, "INFO: No tasks are running which match ...")])
    assert running_app.is_running("AudioDeck.exe", runner) is False


def test_is_running_is_false_on_empty_output() -> None:
    """No output at all means nothing was found."""
    runner = FakeRunner([(0, "   ")])
    assert running_app.is_running("AudioDeck.exe", runner) is False


def test_is_running_is_false_when_tasklist_cannot_run() -> None:
    """A runner that raises leaves the deploy no worse off than before."""
    assert running_app.is_running("AudioDeck.exe", ExplodingRunner()) is False


def test_close_never_passes_the_tree_flag() -> None:
    """The terminate ends the named image only.

    `/t` ends everything Windows considers descended from the target, decided
    from a recorded parent process id. Where pids churn, the setup program can
    be recorded as a descendant and terminate itself, leaving no traceback,
    because a terminate is not a crash. This pins the argument list so the
    flag cannot come back unnoticed.
    """
    runner = FakeRunner([(0, "")])
    assert running_app.close("AudioDeck.exe", runner) is True
    command = runner.commands[0]
    assert command[0] == "taskkill"
    assert "/t" not in command
    assert "/f" in command
    assert "/im" in command
    assert "AudioDeck.exe" in command


def test_close_reports_a_failed_terminate() -> None:
    """A non-zero exit is reported rather than assumed successful."""
    runner = FakeRunner([(1, "")])
    assert running_app.close("AudioDeck.exe", runner) is False


def test_close_is_false_when_taskkill_cannot_run() -> None:
    """A runner that raises is a failure to close, not a crash."""
    assert running_app.close("AudioDeck.exe", ExplodingRunner()) is False


def test_wait_until_closed_returns_at_once_when_gone() -> None:
    """Nothing running means no waiting and no sleeping."""
    slept: list[float] = []
    runner = FakeRunner([(0, "INFO: No tasks are running which match ...")])
    assert running_app.wait_until_closed("AudioDeck.exe", runner, slept.append) is True
    assert slept == []


def test_wait_until_closed_polls_until_the_process_goes() -> None:
    """A process that takes a moment to die is waited for, then confirmed."""
    slept: list[float] = []
    runner = FakeRunner(
        [
            (0, '"AudioDeck.exe","1234"'),
            (0, '"AudioDeck.exe","1234"'),
            (0, "INFO: No tasks are running which match ..."),
        ]
    )
    assert running_app.wait_until_closed("AudioDeck.exe", runner, slept.append) is True
    assert slept == [c.CLOSE_POLL_DELAY_SECONDS, c.CLOSE_POLL_DELAY_SECONDS]


def test_wait_until_closed_gives_up_and_says_so() -> None:
    """A process that outlasts the bounded wait is reported, not waited on."""
    slept: list[float] = []
    runner = FakeRunner([(0, '"AudioDeck.exe","1234"')])
    assert running_app.wait_until_closed("AudioDeck.exe", runner, slept.append) is False
    assert len(slept) == c.CLOSE_POLL_COUNT - 1


def test_close_and_confirm_terminates_then_verifies() -> None:
    """The terminate is sent first, then absence is confirmed."""
    runner = FakeRunner([(0, ""), (0, "INFO: No tasks are running which match ...")])
    assert (
        running_app.close_and_confirm("AudioDeck.exe", runner, lambda _s: None) is True
    )
    assert runner.commands[0][0] == "taskkill"
    assert runner.commands[1][0] == "tasklist"


def test_close_and_confirm_is_false_when_the_app_survives() -> None:
    """A terminate that reports success but leaves the app running is caught."""
    runner = FakeRunner([(0, ""), (0, '"AudioDeck.exe","1234"')])
    assert (
        running_app.close_and_confirm("AudioDeck.exe", runner, lambda _s: None) is False
    )


def _locked_payload(tmp: Path) -> tuple[Path, Path]:
    """Build a payload zip and an install dir holding a file that cannot be written."""
    target = tmp / "install"
    target.mkdir()
    victim = target / c.APP_EXE_NAME
    victim.write_bytes(b"old")
    os.chmod(victim, stat.S_IREAD)
    payload = tmp / "payload.zip"
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(c.APP_EXE_NAME, "new")
    return payload, target


def test_a_locked_file_becomes_a_sentence_the_user_can_act_on() -> None:
    """The bare errno and path are replaced by what actually happened.

    Extracting over a file that cannot be written raises PermissionError, the
    same failure a running app produces by holding its executable. Left alone
    it reaches the user as "[Errno 13] Permission denied" and a path, with the
    progress bar stopped at its first step, which is what made this look like
    a hang.
    """
    with tempfile.TemporaryDirectory() as raw:
        payload, target = _locked_payload(Path(raw))
        try:
            with pytest.raises(ops.AppIsRunningError) as caught:
                ops.extract_all(payload, target)
            message = str(caught.value)
        finally:
            os.chmod(target / c.APP_EXE_NAME, stat.S_IWRITE)
    assert c.APP_DISPLAY_NAME in message
    assert "tray icon" in message
    assert "Errno" not in message


def test_repair_reports_a_locked_file_the_same_way() -> None:
    """The repair path converts the same failure, not only the deploy path."""
    manifest = {"files": [{"name": c.APP_EXE_NAME, "sha256": "not-the-real-hash"}]}
    with tempfile.TemporaryDirectory() as raw:
        payload, target = _locked_payload(Path(raw))
        try:
            with pytest.raises(ops.AppIsRunningError):
                ops.extract_damaged(payload, target, manifest)
        finally:
            os.chmod(target / c.APP_EXE_NAME, stat.S_IWRITE)


def test_a_clean_extract_still_writes_the_files() -> None:
    """The wrapper does not change the successful path."""
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        target = tmp / "install"
        target.mkdir()
        payload = tmp / "payload.zip"
        with zipfile.ZipFile(payload, "w") as archive:
            archive.writestr(c.APP_EXE_NAME, "new")
        ops.extract_all(payload, target)
        assert (target / c.APP_EXE_NAME).read_text(encoding="utf-8") == "new"


def test_the_prompt_is_skipped_when_the_app_is_not_running() -> None:
    """Nothing is asked or reported when there is nothing to close.

    Only this path is covered here: the others open a modal message box, which
    needs a running application and a user, so they are verified by installing
    over a running copy rather than in the suite.
    """
    from installer.close_prompt import clear_running_app

    reported: list[str] = []
    proceed = clear_running_app(
        parent=None,
        report=reported.append,
        is_running=lambda: False,
        close_and_confirm=lambda: True,
    )
    assert proceed is True
    assert reported == []
