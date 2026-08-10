"""Linux device controller over pactl.

Setting the default sink or source also moves the running streams onto the
new device on every mainstream PulseAudio and PipeWire setup, matching the
behaviour users expect from the desktop's own sound settings.
"""

from __future__ import annotations

from src.domain.exceptions.domain_exceptions import DeviceControlException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.pactl_api import PactlApi


class LinuxDeviceController:
    """Controls default audio devices via the PulseAudio command client."""

    def __init__(self, pactl: PactlApi) -> None:
        """Initialize the controller.

        Args:
            pactl: The pactl command seam
        """
        self._pactl = pactl

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: PulseAudio name of the device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If setting default fails
        """
        command = (
            "set-default-sink"
            if device_type == DeviceType.OUTPUT
            else "set-default-source"
        )
        try:
            self._pactl.run(command, device_id)
        except Exception as e:
            raise DeviceControlException(f"Failed to set default device: {e}") from e

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        # Device changes are reflected by the sound server automatically.
        pass
