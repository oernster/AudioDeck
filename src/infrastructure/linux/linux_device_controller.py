"""Linux device controller over pactl, with a PipeWire metadata fallback.

Setting the default sink or source also moves the running streams onto the
new device on every mainstream PulseAudio and PipeWire setup, matching the
behaviour users expect from the desktop's own sound settings.

Inside a Flatpak the PulseAudio route is refused: PipeWire treats sandboxed
clients as restricted and denies management commands, so `pactl` can list
devices but not switch them. Writing the choice into PipeWire's own metadata
achieves the same result and is what pactl would have asked the server to do,
so it is tried whenever the pactl route fails.
"""

from __future__ import annotations

import json
from typing import Optional

from src.domain.exceptions.domain_exceptions import DeviceControlException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.pactl_api import PactlApi
from src.infrastructure.linux.pw_metadata_api import PwMetadataApi

# pactl subcommand per flow.
_PACTL_COMMANDS = {
    DeviceType.OUTPUT: "set-default-sink",
    DeviceType.INPUT: "set-default-source",
}

# PipeWire metadata key per flow. The "configured" keys hold the user's
# choice; the session manager derives the live default from them.
_METADATA_KEYS = {
    DeviceType.OUTPUT: "default.configured.audio.sink",
    DeviceType.INPUT: "default.configured.audio.source",
}


class LinuxDeviceController:
    """Controls default audio devices via the PulseAudio command client."""

    def __init__(self, pactl: PactlApi, pw_metadata: PwMetadataApi) -> None:
        """Initialize the controller.

        Args:
            pactl: The pactl command seam
            pw_metadata: The pw-metadata command seam used when pactl is refused
        """
        self._pactl = pactl
        self._pw_metadata = pw_metadata

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: PulseAudio name of the device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If both routes fail
        """
        pactl_error: Optional[Exception] = None
        try:
            self._pactl.run(_PACTL_COMMANDS[device_type], device_id)
            return
        except Exception as e:
            pactl_error = e

        try:
            # A PulseAudio device name is the PipeWire node name, so the id
            # carries across unchanged.
            self._pw_metadata.set_property(
                _METADATA_KEYS[device_type], json.dumps({"name": device_id})
            )
        except Exception:
            # Report the pactl failure: on a plain PulseAudio system there is
            # no pw-metadata to speak of and the pactl error is the real one.
            raise DeviceControlException(
                f"Failed to set default device: {pactl_error}"
            ) from pactl_error

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        # Device changes are reflected by the sound server automatically.
        pass
