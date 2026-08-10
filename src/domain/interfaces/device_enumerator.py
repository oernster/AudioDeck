"""Device enumerator interface."""

from typing import List, Protocol

from src.domain.entities.audio_device import AudioDevice


class IDeviceEnumerator(Protocol):
    """Interface for reading the system's audio devices in one pass."""

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        ...
