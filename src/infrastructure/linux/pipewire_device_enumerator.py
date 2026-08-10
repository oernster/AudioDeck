"""PipeWire device enumerator over pw-dump JSON output.

pw-dump reports every object the sound server knows about. Audio sinks are
output devices and audio sources are input devices, and unlike PulseAudio the
loopback monitor of a sink is not a separate node, so nothing has to be
filtered out. Devices are identified by their node name, which is the same
identifier PulseAudio reports and is stable across reboots, while the node
description is shown as the device name.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.pw_dump_api import PwDumpApi

_NODE_OBJECT_TYPE = "PipeWire:Interface:Node"
_METADATA_OBJECT_TYPE = "PipeWire:Interface:Metadata"

# The metadata store holding the current default devices.
_DEFAULT_METADATA_NAME = "default"

# Media classes per flow. Sources carry subtypes such as Audio/Source/Virtual
# for filters the user can legitimately pick, so they are matched by prefix.
_SINK_MEDIA_CLASS = "Audio/Sink"
_SOURCE_MEDIA_CLASS_PREFIX = "Audio/Source"

# Metadata keys naming the current default of each flow.
_DEFAULT_KEYS = {
    DeviceType.OUTPUT: "default.audio.sink",
    DeviceType.INPUT: "default.audio.source",
}


class PipewireDeviceEnumerator:
    """Enumerates audio devices via PipeWire's own command client."""

    def __init__(self, pw_dump: PwDumpApi) -> None:
        """Initialize the enumerator.

        Args:
            pw_dump: The pw-dump command seam
        """
        self._pw_dump = pw_dump

    def _objects(self) -> List[Any]:
        """Return the parsed object graph, empty when it cannot be read."""
        try:
            objects = json.loads(self._pw_dump.dump())
        except Exception:
            # Degrade to an empty list: pw-dump missing, the server down or
            # non-JSON output all mean no devices can be read right now.
            return []
        return objects if isinstance(objects, list) else []

    def _default_names(self, objects: List[Any]) -> Dict[DeviceType, Optional[str]]:
        """Return the current default device name per flow."""
        defaults: Dict[DeviceType, Optional[str]] = {
            DeviceType.OUTPUT: None,
            DeviceType.INPUT: None,
        }
        wanted = {key: flow for flow, key in _DEFAULT_KEYS.items()}

        for item in objects:
            # A malformed entry must not cost the user the defaults.
            if not isinstance(item, dict) or item.get("type") != _METADATA_OBJECT_TYPE:
                continue
            if item.get("props", {}).get("metadata.name") != _DEFAULT_METADATA_NAME:
                continue
            for entry in item.get("metadata") or []:
                flow = wanted.get(entry.get("key"))
                if flow is None:
                    continue
                value = entry.get("value")
                if isinstance(value, dict):
                    defaults[flow] = value.get("name")

        return defaults

    def _device_type(self, media_class: str) -> Optional[DeviceType]:
        """Return the flow a media class belongs to, None when it is neither."""
        if media_class == _SINK_MEDIA_CLASS:
            return DeviceType.OUTPUT
        if media_class.startswith(_SOURCE_MEDIA_CLASS_PREFIX):
            return DeviceType.INPUT
        return None

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        objects = self._objects()
        defaults = self._default_names(objects)
        devices: List[AudioDevice] = []

        for position, item in enumerate(objects):
            try:
                if item.get("type") != _NODE_OBJECT_TYPE:
                    continue

                props = item.get("info", {}).get("props", {})
                device_type = self._device_type(props.get("media.class") or "")
                if device_type is None:
                    continue

                name = props.get("node.name")
                if not name:
                    continue

                devices.append(
                    AudioDevice(
                        id=name,
                        name=props.get("node.description")
                        or f"Audio Device {position + 1}",
                        device_type=device_type,
                        is_default=name == defaults[device_type],
                        # PipeWire only reports nodes that exist right now,
                        # so every one of them is selectable.
                        state=DeviceState.AVAILABLE,
                    )
                )
            except Exception:
                # Degrade to skipping this one object; a malformed entry must
                # not cost the user the rest of the list.
                continue

        # Outputs first, matching the order the pactl enumerator reports.
        return [d for d in devices if d.device_type == DeviceType.OUTPUT] + [
            d for d in devices if d.device_type == DeviceType.INPUT
        ]
