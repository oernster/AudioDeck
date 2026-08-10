"""macOS device controller over the CoreAudio seam.

Profiles store the stable device UID, so setting a default first resolves
the UID back to the current transient AudioDeviceID, then asks CoreAudio to
make that device the flow's default.
"""

from __future__ import annotations

from typing import Optional

from src.domain.exceptions.domain_exceptions import DeviceControlException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.macos.coreaudio_api import CoreAudioApi


class MacosDeviceController:
    """Controls default audio devices via CoreAudio."""

    def __init__(self, core_audio: CoreAudioApi) -> None:
        """Initialize the controller.

        Args:
            core_audio: The CoreAudio seam
        """
        self._core_audio = core_audio

    def _resolve_device_id(self, device_uid: str) -> Optional[int]:
        """Return the current AudioDeviceID for a UID, None if absent."""
        for device_id in self._core_audio.all_device_ids():
            if self._core_audio.device_uid(device_id) == device_uid:
                return device_id
        return None

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: Stable UID of the device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If setting default fails
        """
        resolved_id = self._resolve_device_id(device_id)
        if resolved_id is None:
            raise DeviceControlException(
                f"Device is not currently present: {device_id}"
            )

        input_device = device_type == DeviceType.INPUT
        if not self._core_audio.set_default_device(resolved_id, input_device):
            raise DeviceControlException(f"Failed to set default device: {device_id}")

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        # Device changes are reflected by CoreAudio automatically.
        pass
