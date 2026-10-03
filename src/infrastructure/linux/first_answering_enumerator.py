"""Enumerator that asks each source in turn until one answers.

A Linux desktop may have pactl, pw-dump or both: PulseAudio machines have
only the former, PipeWire machines that never installed the PulseAudio client
tools have only the latter. A source that cannot be read or that finds no
devices hands over to the next one. Only when every source failed to read
is that reported as a failure: a machine whose devices cannot be read must
never look like one whose devices are all disconnected.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from src.domain.entities.audio_device import AudioDevice
from src.domain.exceptions.domain_exceptions import DeviceEnumerationException
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
            List of all AudioDevice entities, empty when the sources that
            could be read found none

        Raises:
            DeviceEnumerationException: If no source could be read at all
        """
        answered = False
        last_failure: Optional[DeviceEnumerationException] = None
        for source in self._sources:
            try:
                devices = source.get_all_devices()
            except DeviceEnumerationException as failure:
                last_failure = failure
                continue
            if devices:
                return devices
            answered = True
        if not answered and last_failure is not None:
            raise last_failure
        return []
