"""The CoreAudio seam, spoken through ctypes.

CoreAudio's HAL is a small, stable C API, so binding the handful of calls
this application needs directly through ctypes keeps the dependency
footprint at zero: no pyobjc, no compiled helper. The Protocol above the
bindings is deliberately pythonic (lists, strings, booleans) so the
enumerator and controller logic can be tested with a hand-written fake.

Device identity: an AudioDeviceID is transient (it can change across
reboots and unplugs), while a device UID is a stable string, so UIDs cross
this seam as the durable identifiers and AudioDeviceIDs stay internal to a
single call sequence.
"""

from __future__ import annotations

import ctypes
from typing import Any, List, Optional, Protocol

# The fixed AudioObjectID of the HAL's root object, which owns the device
# list and the default-device properties.
_SYSTEM_OBJECT_ID = 1

# Property selectors are big-endian four-character codes.
_SELECTOR_DEVICES = int.from_bytes(b"dev ", "big")
_SELECTOR_DEFAULT_INPUT = int.from_bytes(b"dIn ", "big")
_SELECTOR_DEFAULT_OUTPUT = int.from_bytes(b"dOut", "big")
_SELECTOR_DEVICE_UID = int.from_bytes(b"uid ", "big")
_SELECTOR_NAME = int.from_bytes(b"lnam", "big")
_SELECTOR_STREAMS = int.from_bytes(b"stm#", "big")

_SCOPE_GLOBAL = int.from_bytes(b"glob", "big")
_SCOPE_INPUT = int.from_bytes(b"inpt", "big")
_SCOPE_OUTPUT = int.from_bytes(b"outp", "big")

_ELEMENT_MAIN = 0

# CoreFoundation's UTF-8 string encoding id, from CFString.h.
_CF_STRING_ENCODING_UTF8 = 0x08000100

# Longest device name or UID this binding will read back.
_STRING_BUFFER_BYTES = 512

_CORE_AUDIO_FRAMEWORK = "/System/Library/Frameworks/CoreAudio.framework/CoreAudio"
_CORE_FOUNDATION_FRAMEWORK = (
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)

_OS_STATUS_OK = 0


class CoreAudioApi(Protocol):
    """The slice of CoreAudio this backend needs, in pythonic terms."""

    def all_device_ids(self) -> List[int]:
        """Return every AudioDeviceID currently present."""
        ...

    def device_uid(self, device_id: int) -> Optional[str]:
        """Return the stable UID of a device, None if unreadable."""
        ...

    def device_name(self, device_id: int) -> Optional[str]:
        """Return the human name of a device, None if unreadable."""
        ...

    def has_output_streams(self, device_id: int) -> bool:
        """Return True when the device can play audio."""
        ...

    def has_input_streams(self, device_id: int) -> bool:
        """Return True when the device can record audio."""
        ...

    def default_device_id(self, input_device: bool) -> Optional[int]:
        """Return the current default device id for a flow, None if unknown."""
        ...

    def set_default_device(self, device_id: int, input_device: bool) -> bool:
        """Make a device the default for a flow, returning success."""
        ...


class _PropertyAddress(ctypes.Structure):  # pragma: no cover
    """AudioObjectPropertyAddress: selector, scope and element."""

    _fields_ = [
        ("selector", ctypes.c_uint32),
        ("scope", ctypes.c_uint32),
        ("element", ctypes.c_uint32),
    ]


class CtypesCoreAudioApi:  # pragma: no cover
    """Real CoreAudio calls, kept behind CoreAudioApi so logic is testable.

    macOS only: the frameworks are loaded lazily on first use, so this class
    can be constructed (by the backend factory) on any platform without
    touching the filesystem.
    """

    def __init__(self) -> None:
        """Initialize with no frameworks loaded yet."""
        self._core_audio: Any = None
        self._core_foundation: Any = None

    def _load(self) -> None:
        """Load the frameworks on first use."""
        if self._core_audio is None:
            self._core_audio = ctypes.CDLL(_CORE_AUDIO_FRAMEWORK)
            self._core_foundation = ctypes.CDLL(_CORE_FOUNDATION_FRAMEWORK)

    def _property_size(self, object_id: int, address: _PropertyAddress) -> int:
        """Return the byte size of a property, 0 on failure."""
        size = ctypes.c_uint32(0)
        status = self._core_audio.AudioObjectGetPropertyDataSize(
            ctypes.c_uint32(object_id),
            ctypes.byref(address),
            ctypes.c_uint32(0),
            None,
            ctypes.byref(size),
        )
        return size.value if status == _OS_STATUS_OK else 0

    def _get_property(
        self, object_id: int, address: _PropertyAddress, buffer: Any
    ) -> bool:
        """Read a property into a ctypes buffer, returning success."""
        self._load()
        size = ctypes.c_uint32(ctypes.sizeof(buffer))
        status = self._core_audio.AudioObjectGetPropertyData(
            ctypes.c_uint32(object_id),
            ctypes.byref(address),
            ctypes.c_uint32(0),
            None,
            ctypes.byref(size),
            ctypes.byref(buffer),
        )
        return bool(status == _OS_STATUS_OK)

    def _cf_string_to_str(self, cf_string: Any) -> Optional[str]:
        """Convert and release a CFStringRef, None on failure."""
        if not cf_string:
            return None
        buffer = ctypes.create_string_buffer(_STRING_BUFFER_BYTES)
        ok = self._core_foundation.CFStringGetCString(
            cf_string,
            buffer,
            ctypes.c_long(_STRING_BUFFER_BYTES),
            ctypes.c_uint32(_CF_STRING_ENCODING_UTF8),
        )
        self._core_foundation.CFRelease(cf_string)
        return buffer.value.decode("utf-8") if ok else None

    def _read_cf_string(self, device_id: int, selector: int) -> Optional[str]:
        """Read a CFString property from a device."""
        address = _PropertyAddress(selector, _SCOPE_GLOBAL, _ELEMENT_MAIN)
        cf_string = ctypes.c_void_p(None)
        if not self._get_property(device_id, address, cf_string):
            return None
        return self._cf_string_to_str(cf_string)

    def _has_streams(self, device_id: int, scope: int) -> bool:
        """Return True when a device has streams in the given scope."""
        self._load()
        address = _PropertyAddress(_SELECTOR_STREAMS, scope, _ELEMENT_MAIN)
        return self._property_size(device_id, address) > 0

    def all_device_ids(self) -> List[int]:
        """Return every AudioDeviceID currently present."""
        try:
            self._load()
            address = _PropertyAddress(_SELECTOR_DEVICES, _SCOPE_GLOBAL, _ELEMENT_MAIN)
            byte_size = self._property_size(_SYSTEM_OBJECT_ID, address)
            count = byte_size // ctypes.sizeof(ctypes.c_uint32)
            if count == 0:
                return []
            buffer = (ctypes.c_uint32 * count)()
            if not self._get_property(_SYSTEM_OBJECT_ID, address, buffer):
                return []
            return list(buffer)
        except Exception:
            return []

    def device_uid(self, device_id: int) -> Optional[str]:
        """Return the stable UID of a device, None if unreadable."""
        try:
            return self._read_cf_string(device_id, _SELECTOR_DEVICE_UID)
        except Exception:
            return None

    def device_name(self, device_id: int) -> Optional[str]:
        """Return the human name of a device, None if unreadable."""
        try:
            return self._read_cf_string(device_id, _SELECTOR_NAME)
        except Exception:
            return None

    def has_output_streams(self, device_id: int) -> bool:
        """Return True when the device can play audio."""
        try:
            return self._has_streams(device_id, _SCOPE_OUTPUT)
        except Exception:
            return False

    def has_input_streams(self, device_id: int) -> bool:
        """Return True when the device can record audio."""
        try:
            return self._has_streams(device_id, _SCOPE_INPUT)
        except Exception:
            return False

    def default_device_id(self, input_device: bool) -> Optional[int]:
        """Return the current default device id for a flow, None if unknown."""
        try:
            self._load()
            selector = (
                _SELECTOR_DEFAULT_INPUT if input_device else _SELECTOR_DEFAULT_OUTPUT
            )
            address = _PropertyAddress(selector, _SCOPE_GLOBAL, _ELEMENT_MAIN)
            device_id = ctypes.c_uint32(0)
            if not self._get_property(_SYSTEM_OBJECT_ID, address, device_id):
                return None
            return device_id.value or None
        except Exception:
            return None

    def set_default_device(self, device_id: int, input_device: bool) -> bool:
        """Make a device the default for a flow, returning success."""
        try:
            self._load()
            selector = (
                _SELECTOR_DEFAULT_INPUT if input_device else _SELECTOR_DEFAULT_OUTPUT
            )
            address = _PropertyAddress(selector, _SCOPE_GLOBAL, _ELEMENT_MAIN)
            value = ctypes.c_uint32(device_id)
            status = self._core_audio.AudioObjectSetPropertyData(
                ctypes.c_uint32(_SYSTEM_OBJECT_ID),
                ctypes.byref(address),
                ctypes.c_uint32(0),
                None,
                ctypes.c_uint32(ctypes.sizeof(value)),
                ctypes.byref(value),
            )
            return bool(status == _OS_STATUS_OK)
        except Exception:
            return False
