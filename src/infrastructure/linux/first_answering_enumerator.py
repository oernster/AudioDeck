"""Enumerator that asks each source in turn until one answers.

A Linux desktop may have pactl, or pw-dump, or both: PulseAudio machines have
only the former, PipeWire machines that never installed the PulseAudio client
tools have only the latter. Both enumerators already degrade to an empty list
when their command is missing, so an empty answer is the signal to try the
next source rather than an error to report.
"""

from __future__ import annotations

from typing import List, Sequence

from src.domain.entities.audio_device import AudioDevice
from src.domain.interfaces.device_enumerator import IDeviceEnumerator


class FirstAnsweringEnumerator:
    """Returns the devices of the first source that finds any."""

    def __init__(self, sources: Sequence[IDeviceEnumerator]) -> None:
        """Initialize the enumerator.

        Args:
            sources: The enumerators to consult, in order of preference
        """
        self._sources = sources

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities, empty when no source finds any
        """
        for source in self._sources:
            devices = source.get_all_devices()
            if devices:
                return devices
        return []
