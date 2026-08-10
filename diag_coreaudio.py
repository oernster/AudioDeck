"""Diagnostic for the macOS CoreAudio binding. Run on the Mac, repo root:

    python3 diag_coreaudio.py

Prints raw OSStatus values and per-device reads with nothing swallowed, so a
failure names its exact call. Delete after use; not part of the application.
"""

import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.infrastructure.macos.coreaudio_api import (  # noqa: E402
    _ELEMENT_MAIN,
    _SCOPE_GLOBAL,
    _SELECTOR_DEVICES,
    _SYSTEM_OBJECT_ID,
    CtypesCoreAudioApi,
    _PropertyAddress,
)
from src.infrastructure.macos.macos_device_enumerator import (  # noqa: E402
    MacosDeviceEnumerator,
)

api = CtypesCoreAudioApi()
api._load()
print("frameworks loaded OK")

address = _PropertyAddress(_SELECTOR_DEVICES, _SCOPE_GLOBAL, _ELEMENT_MAIN)
size = ctypes.c_uint32(0)
status = api._core_audio.AudioObjectGetPropertyDataSize(
    ctypes.c_uint32(_SYSTEM_OBJECT_ID),
    ctypes.byref(address),
    ctypes.c_uint32(0),
    None,
    ctypes.byref(size),
)
print(f"device-list size query: status={status} bytes={size.value}")

ids = api.all_device_ids()
print(f"device ids: {ids}")
for device_id in ids:
    print(
        f"  id={device_id}"
        f" uid={api.device_uid(device_id)!r}"
        f" name={api.device_name(device_id)!r}"
        f" out={api.has_output_streams(device_id)}"
        f" in={api.has_input_streams(device_id)}"
    )
print(f"default output id: {api.default_device_id(input_device=False)}")
print(f"default input id: {api.default_device_id(input_device=True)}")

devices = MacosDeviceEnumerator(api).get_all_devices()
print(f"enumerator produced {len(devices)} devices:")
for device in devices:
    print(f"  {device.device_type.name}: {device.name!r} default={device.is_default}")
