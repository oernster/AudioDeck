"""Windows device enumerator using pycaw."""

import warnings
from typing import Any, List, Optional

from pycaw.pycaw import DEVICE_STATE, AudioUtilities, EDataFlow, ERole

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType

# pycaw raises a UserWarning while building its device list whenever it cannot
# read a friendly name from an inactive device (disconnected or disabled). That
# is expected now that those devices are enumerated, so silence that one noise.
warnings.filterwarnings(
    "ignore",
    message="COMError attempting to get property",
    category=UserWarning,
    module=r"pycaw\.utils",
)

# Enumerate devices that are usable now or that the user could reasonably pick
# and connect later (for example a Bluetooth headset that is currently off).
# NOTPRESENT is excluded to avoid listing every device Windows has ever seen.
_STATE_MASK = (
    DEVICE_STATE.ACTIVE.value
    | DEVICE_STATE.DISABLED.value
    | DEVICE_STATE.UNPLUGGED.value
)

# Map the Windows endpoint state to the domain availability state.
_WINDOWS_STATE_TO_DEVICE_STATE = {
    DEVICE_STATE.ACTIVE.value: DeviceState.AVAILABLE,
    DEVICE_STATE.UNPLUGGED.value: DeviceState.DISCONNECTED,
    DEVICE_STATE.DISABLED.value: DeviceState.DISABLED,
    DEVICE_STATE.NOTPRESENT.value: DeviceState.NOT_PRESENT,
}


class WindowsDeviceEnumerator:
    """Enumerates audio devices using Windows Core Audio API."""

    def __init__(self) -> None:
        """Initialize the enumerator."""
        self._default_output_id: Optional[str] = None
        self._default_input_id: Optional[str] = None

    def _get_default_device_id(self, data_flow: int) -> Optional[str]:
        """Get the ID of the current default device for a data flow.

        Args:
            data_flow: 0 for output (eRender), 1 for input (eCapture)

        Returns:
            Device ID of the default device, or None if not found
        """
        try:
            device_enumerator = AudioUtilities.GetDeviceEnumerator()
            if device_enumerator is None:
                return None

            # Get default device for multimedia role (eMultimedia = 1)
            # ERole: eConsole=0, eMultimedia=1, eCommunications=2
            default_device = device_enumerator.GetDefaultAudioEndpoint(
                data_flow, ERole.eMultimedia.value
            )
            if default_device is None:
                return None

            device_id: Optional[str] = default_device.GetId()
            return device_id
        except Exception:
            # Degrade to "no default known". A machine with no endpoint of this
            # flow, or one mid-way through a device change, is a normal state
            # rather than an error, and the caller renders it as None.
            return None

    def enumerate_devices(
        self, data_flow: int, all_devices_cache: Optional[List[Any]] = None
    ) -> List[AudioDevice]:
        """Enumerate devices of a specific flow type.

        Args:
            data_flow: 0 for output (eRender), 1 for input (eCapture)
            all_devices_cache: Cached list from AudioUtilities.GetAllDevices()

        Returns:
            List of AudioDevice entities
        """
        devices: List[AudioDevice] = []

        try:
            # Use cached default device ID (set in get_all_devices)
            default_device_id = (
                self._default_output_id if data_flow == 0 else self._default_input_id
            )
            device_enumerator = AudioUtilities.GetDeviceEnumerator()
            if device_enumerator is None:
                return devices

            # Get collection of endpoints across usable and selectable states
            collection = device_enumerator.EnumAudioEndpoints(data_flow, _STATE_MASK)
            if collection is None:
                return devices

            count = collection.GetCount()

            for i in range(count):
                try:
                    endpoint = collection.Item(i)
                    if endpoint is None:
                        continue

                    # Get device ID
                    device_id = endpoint.GetId()

                    # Resolve the endpoint state and friendly name.
                    try:
                        state_value = endpoint.GetState()
                        device_state = _WINDOWS_STATE_TO_DEVICE_STATE.get(
                            state_value, DeviceState.AVAILABLE
                        )

                        # Get the device's friendly name from the cached list
                        # (which includes inactive devices), keyed by ID.
                        device_name = None
                        if all_devices_cache:
                            for audio_device in all_devices_cache:
                                if (
                                    hasattr(audio_device, "id")
                                    and audio_device.id == device_id
                                ):
                                    device_name = audio_device.FriendlyName
                                    break

                        if not device_name:
                            device_name = f"Audio Device {i+1}"

                    except Exception:
                        # Degrade to a positional name and an assumed-available
                        # state. An endpoint that will not report its name or
                        # state is still a real device the user can select, so
                        # losing it from the list would be the worse outcome.
                        device_name = f"Audio Device {i+1}"
                        device_state = DeviceState.AVAILABLE

                    # Determine device type based on data flow
                    device_type = (
                        DeviceType.OUTPUT if data_flow == 0 else DeviceType.INPUT
                    )

                    # Check if this is the default device
                    is_default = device_id == default_device_id

                    # Create device entity
                    device = AudioDevice(
                        id=device_id,
                        name=device_name,
                        device_type=device_type,
                        is_default=is_default,
                        state=device_state,
                    )
                    devices.append(device)

                except Exception:
                    # Degrade to skipping this one endpoint. The collection can
                    # hand back an item that vanishes before it is read, so
                    # dropping it keeps every other device in the list.
                    continue

        except Exception:
            # Degrade to whatever was collected before the failure. The
            # enumerator itself can disappear mid-walk during a device change,
            # and a partial list still lets the user switch to a known device.
            pass

        return devices

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        try:
            # Get default device IDs for both render and capture
            self._default_output_id = self._get_default_device_id(
                EDataFlow.eRender.value
            )
            self._default_input_id = self._get_default_device_id(
                EDataFlow.eCapture.value
            )

            # Fetch the friendly-name cache once; guard against COM races that
            # can occur while audio sources are changing.
            try:
                all_devices_cache = AudioUtilities.GetAllDevices()
            except Exception:
                all_devices_cache = []

            # Explicitly enumerate render and capture devices
            output_devices = self.enumerate_devices(
                EDataFlow.eRender.value, all_devices_cache
            )
            input_devices = self.enumerate_devices(
                EDataFlow.eCapture.value, all_devices_cache
            )

            return output_devices + input_devices
        except Exception:
            # Never let a device-change race crash the caller.
            return []
