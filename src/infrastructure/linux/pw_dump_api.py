"""The pw-dump command seam.

pactl belongs to PulseAudio's client tools, which a PipeWire-only machine has
no reason to install, so a Linux desktop can run perfectly well with no pactl
at all. pw-dump ships with PipeWire itself and reports the same devices, so
it is the reliable second source for enumeration.
"""

from __future__ import annotations

import subprocess
from typing import Protocol

# A dump answers from the local sound server; if it has not answered in this
# long the server is wedged and waiting further would hang the app. Kept in
# step with the other Linux seams.
_PW_DUMP_TIMEOUT_SECONDS = 5


class PwDumpApi(Protocol):
    """The slice of the pw-dump command line this backend needs."""

    def dump(self) -> str:
        """Return the sound server's object graph as JSON text.

        Raises:
            OSError: If pw-dump is not installed or cannot be executed
            subprocess.SubprocessError: If pw-dump fails or times out
        """
        ...


class SubprocessPwDumpApi:  # pragma: no cover
    """Real pw-dump invocations, kept behind PwDumpApi so the logic is testable."""

    def dump(self) -> str:
        """Run pw-dump and return its stdout, raising on any failure."""
        completed = subprocess.run(
            ("pw-dump",),
            capture_output=True,
            text=True,
            check=True,
            timeout=_PW_DUMP_TIMEOUT_SECONDS,
        )
        return completed.stdout
