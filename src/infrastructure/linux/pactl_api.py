"""The pactl command seam.

PulseAudio and PipeWire (via pipewire-pulse) both speak the PulseAudio
protocol and `pactl` is its standard client, so one subprocess seam covers
every mainstream Linux desktop without adding a Python dependency.
"""

from __future__ import annotations

import subprocess
from typing import Protocol

# A pactl call answers from the local sound server; if it has not answered
# in this long the server is wedged and waiting further would hang the app.
_PACTL_TIMEOUT_SECONDS = 5


class PactlApi(Protocol):
    """The slice of the pactl command line this backend needs."""

    def run(self, *args: str) -> str:
        """Run pactl with the given arguments and return its stdout.

        Raises:
            OSError: If pactl is not installed or cannot be executed
            subprocess.SubprocessError: If pactl fails or times out
        """
        ...


class SubprocessPactlApi:  # pragma: no cover
    """Real pactl invocations, kept behind PactlApi so the logic is testable."""

    def run(self, *args: str) -> str:
        """Run pactl and return its stdout, raising on any failure."""
        completed = subprocess.run(
            ("pactl", *args),
            capture_output=True,
            text=True,
            check=True,
            timeout=_PACTL_TIMEOUT_SECONDS,
        )
        return completed.stdout
