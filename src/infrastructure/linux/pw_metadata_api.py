"""The pw-metadata command seam.

PipeWire refuses to let a sandboxed client change the default device: its
access module strips the metadata permission from every Flatpak client, so
inside the sandbox `pactl set-default-sink` is denied outright and a direct
metadata write is accepted and then silently dropped. No sandbox permission
lifts that, so the write is handed to the host session instead, which is why
the Flatpak asks to talk to org.freedesktop.Flatpak.

Writing the default into PipeWire's metadata is the same write pactl would
have asked the sound server to perform, and pw-metadata ships with PipeWire
itself, so the host always has it.
"""

from __future__ import annotations

import os
import subprocess
from typing import Protocol, Tuple

# The metadata write answers from the local sound server; if it has not
# answered in this long the server is wedged and waiting further would hang
# the app. Kept in step with the pactl seam's own timeout.
_PW_METADATA_TIMEOUT_SECONDS = 5

# PipeWire's global core object owns the default-device metadata.
_CORE_OBJECT_ID = "0"

# The metadata store holding the user's device choices.
_DEFAULT_METADATA_NAME = "default"

# The value type WirePlumber expects; without it the entry is ignored.
_JSON_VALUE_TYPE = "Spa:String:JSON"

# Flatpak drops this file into every sandbox, so its presence is the
# supported way for an app to know it is running inside one.
_FLATPAK_MARKER_PATH = "/.flatpak-info"

# Runs a command in the host session rather than the sandbox.
_HOST_COMMAND_PREFIX = ("flatpak-spawn", "--host")


class PwMetadataApi(Protocol):
    """The slice of the pw-metadata command line this backend needs."""

    def set_property(self, key: str, value: str) -> None:
        """Write one property into PipeWire's default metadata store.

        Raises:
            OSError: If pw-metadata is not installed or cannot be executed
            subprocess.SubprocessError: If pw-metadata fails or times out
        """
        ...


class SubprocessPwMetadataApi:  # pragma: no cover
    """Real pw-metadata invocations, kept behind PwMetadataApi for testing."""

    def _command(self, key: str, value: str) -> Tuple[str, ...]:
        """Build the command, routed to the host when sandboxed."""
        prefix = _HOST_COMMAND_PREFIX if os.path.exists(_FLATPAK_MARKER_PATH) else ()
        return (
            *prefix,
            "pw-metadata",
            "-n",
            _DEFAULT_METADATA_NAME,
            _CORE_OBJECT_ID,
            key,
            value,
            _JSON_VALUE_TYPE,
        )

    def set_property(self, key: str, value: str) -> None:
        """Write the property, raising on any failure."""
        subprocess.run(
            self._command(key, value),
            capture_output=True,
            text=True,
            check=True,
            timeout=_PW_METADATA_TIMEOUT_SECONDS,
        )
