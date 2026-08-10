"""macOS device enumerator over the CoreAudio seam.

A CoreAudio device can carry both input and output streams (a USB headset
does), so one hardware device may map to two domain devices, exactly as it
does on Windows and Linux. Devices are identified by their stable UID, not
their transient AudioDeviceID.
"""

from __future__ import annotations

from typing import List, Optional

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.macos.coreaudio_api import CoreAudioApi


class MacosDeviceEnumerator:
    """Enumerates audio devices via CoreAudio."""

    def __init__(self, core_audio: CoreAudioApi) -> None:
        """Initialize the enumerator.

        Args:
            core_audio: The CoreAudio seam
        """
        self._core_audio = core_audio

    def _device_for_flow(
        self,
        device_id: int,
        position: int,
        device_type: DeviceType,
        default_id: Optional[int],
    ) -> Optional[AudioDevice]:
        """Build the domain device for one flow of one hardware device."""
        uid = self._core_audio.device_uid(device_id)
        if not uid:
            # A device with no readable UID cannot be stored in a profile
            # or re-found later, so it cannot be offered.
            return None

        name = self._core_audio.device_name(device_id) or (
            f"Audio Device {position + 1}"
        )

        return AudioDevice(
            id=uid,
            name=name,
            device_type=device_type,
            is_default=device_id == default_id,
            # CoreAudio only lists devices that are present.
            state=DeviceState.AVAILABLE,
        )

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        devices: List[AudioDevice] = []

        default_output_id = self._core_audio.default_device_id(input_device=False)
        default_input_id = self._core_audio.default_device_id(input_device=True)

        for position, device_id in enumerate(self._core_audio.all_device_ids()):
            try:
                if self._core_audio.has_output_streams(device_id):
                    device = self._device_for_flow(
                        device_id, position, DeviceType.OUTPUT, default_output_id
                    )
                    if device is not None:
                        devices.append(device)

                if self._core_audio.has_input_streams(device_id):
                    device = self._device_for_flow(
                        device_id, position, DeviceType.INPUT, default_input_id
                    )
                    if device is not None:
                        devices.append(device)
            except Exception:
                # Degrade to skipping this one device; one unreadable device
                # must not cost the user the rest of the list.
                continue

        return devices
