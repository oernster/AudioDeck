"""Linux device enumerator over pactl JSON output.

Sinks are output devices and sources are input devices, in PulseAudio
vocabulary. Monitor sources (the loopback of each sink) are excluded: they
are not devices a user would pick as a microphone. Devices are identified by
their PulseAudio name, which is stable across reboots, while the human
description is shown as the device name.
"""

from __future__ import annotations

import json
from typing import Any, List, Optional

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.pactl_api import PactlApi

# A source whose name carries this suffix is the loopback monitor of a sink.
_MONITOR_NAME_SUFFIX = ".monitor"


class LinuxDeviceEnumerator:
    """Enumerates audio devices via the PulseAudio/PipeWire command client."""

    def __init__(self, pactl: PactlApi) -> None:
        """Initialize the enumerator.

        Args:
            pactl: The pactl command seam
        """
        self._pactl = pactl

    def _default_name(self, command: str) -> Optional[str]:
        """Return the default sink or source name, None when unknown.

        Args:
            command: "get-default-sink" or "get-default-source"
        """
        try:
            name = self._pactl.run(command).strip()
        except Exception:
            # Degrade to "no default known". A machine with no device of
            # this flow (or a sound server mid-restart) is a normal state
            # rather than an error.
            return None
        return name or None

    def _listed_items(self, kind: str) -> List[Any]:
        """Return the parsed JSON list for sinks or sources.

        Args:
            kind: "sinks" or "sources"
        """
        try:
            items = json.loads(self._pactl.run("-f", "json", "list", kind))
        except Exception:
            # Degrade to an empty list: pactl missing, the server down or
            # non-JSON output all mean no devices can be read right now.
            return []
        return items if isinstance(items, list) else []

    def _is_monitor_source(self, item: Any) -> bool:
        """Return True when a source is the loopback monitor of a sink."""
        if item.get("monitor_of_sink_name"):
            return True
        name = item.get("name") or ""
        return name.endswith(_MONITOR_NAME_SUFFIX)

    def enumerate_devices(
        self, kind: str, device_type: DeviceType, default_name: Optional[str]
    ) -> List[AudioDevice]:
        """Enumerate devices of one flow.

        Args:
            kind: "sinks" or "sources"
            device_type: The domain type those items map to
            default_name: The current default device name for this flow

        Returns:
            List of AudioDevice entities
        """
        devices: List[AudioDevice] = []

        for position, item in enumerate(self._listed_items(kind)):
            try:
                if device_type == DeviceType.INPUT and self._is_monitor_source(item):
                    continue

                name = item.get("name")
                if not name:
                    continue

                devices.append(
                    AudioDevice(
                        id=name,
                        name=item.get("description") or f"Audio Device {position + 1}",
                        device_type=device_type,
                        is_default=name == default_name,
                        # PulseAudio only lists devices that are present;
                        # RUNNING, IDLE and SUSPENDED are all selectable.
                        state=DeviceState.AVAILABLE,
                    )
                )
            except Exception:
                # Degrade to skipping this one item; a malformed entry must
                # not cost the user the rest of the list.
                continue

        return devices

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        output_devices = self.enumerate_devices(
            "sinks", DeviceType.OUTPUT, self._default_name("get-default-sink")
        )
        input_devices = self.enumerate_devices(
            "sources", DeviceType.INPUT, self._default_name("get-default-source")
        )
        return output_devices + input_devices
