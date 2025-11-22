"""Windows device enumerator using pycaw."""

from typing import List, Optional
from pycaw.pycaw import AudioUtilities, DEVICE_STATE, EDataFlow, ERole

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_type import DeviceType


class WindowsDeviceEnumerator:
    """Enumerates audio devices using Windows Core Audio API."""

    def __init__(self):
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

            device_id = default_device.GetId()
            return device_id
        except Exception as e:
            print(f"Error getting default device ID for flow {data_flow}: {e}")
            return None

    def enumerate_devices(
        self, data_flow: int, all_devices_cache: List = None
    ) -> List[AudioDevice]:
        """Enumerate devices of a specific flow type.

        Args:
            data_flow: 0 for output (eRender), 1 for input (eCapture)
            all_devices_cache: Cached list from AudioUtilities.GetAllDevices()

        Returns:
            List of AudioDevice entities
        """
        devices = []

        try:
            # Use cached default device ID (set in get_all_devices)
            default_device_id = (
                self._default_output_id if data_flow == 0 else self._default_input_id
            )
            if default_device_id:
                print(
                    f"Current default device ID for flow {data_flow}: {default_device_id}"
                )

            device_enumerator = AudioUtilities.GetDeviceEnumerator()
            if device_enumerator is None:
                print(f"Could not get device enumerator")
                return devices

            # Get collection of active audio endpoints
            collection = device_enumerator.EnumAudioEndpoints(
                data_flow, DEVICE_STATE.ACTIVE.value
            )
            if collection is None:
                print(f"Could not get device collection for flow {data_flow}")
                return devices

            count = collection.GetCount()
            print(f"Found {count} devices for data_flow={data_flow}")

            for i in range(count):
                try:
                    endpoint = collection.Item(i)
                    if endpoint is None:
                        continue

                    # Get device ID
                    device_id = endpoint.GetId()

                    # Try to get device name using QueryInterface to get IMMDevice
                    try:
                        # Use the endpoint's GetState to verify it's active
                        state = endpoint.GetState()

                        # Get the device's friendly name by querying the device directly
                        # This is a workaround - we'll use the device ID as a lookup key
                        device_name = None

                        # Try to match with cached all_devices
                        if all_devices_cache:
                            for audio_device in all_devices_cache:
                                if (
                                    hasattr(audio_device, "id")
                                    and audio_device.id == device_id
                                ):
                                    device_name = audio_device.FriendlyName
                                    print(
                                        f"    Matched device ID {device_id} to name: {device_name}"
                                    )
                                    break

                        if not device_name:
                            print(
                                f"    WARNING: Could not match device ID {device_id} with cached devices"
                            )
                            # Fallback: try to get from the endpoint's description
                            device_name = f"Audio Device {i+1}"

                    except Exception as e:
                        print(f"    Could not get name for device {i}: {e}")
                        device_name = f"Audio Device {i+1}"

                    # Determine device type based on data flow
                    device_type = (
                        DeviceType.OUTPUT if data_flow == 0 else DeviceType.INPUT
                    )

                    # Check if this is the default device
                    is_default = device_id == default_device_id
                    if is_default:
                        print(f"  - {device_name} [DEFAULT]")
                    else:
                        print(f"  - {device_name}")

                    # Create device entity
                    device = AudioDevice(
                        id=device_id,
                        name=device_name,
                        device_type=device_type,
                        is_default=is_default,
                        is_enabled=True,  # Only active devices are enumerated
                    )
                    devices.append(device)

                except Exception as e:
                    print(f"Error processing device {i}: {e}")
                    continue

        except Exception as e:
            print(f"Error enumerating devices (flow={data_flow}): {e}")
            import traceback

            traceback.print_exc()

        return devices

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices (input and output).

        Returns:
            List of all AudioDevice entities
        """
        # Get default device IDs ONCE before enumeration to avoid recursion
        self._default_output_id = self._get_default_device_id(0)
        self._default_input_id = self._get_default_device_id(1)

        # Get all devices ONCE to avoid calling it in the loop
        print("Getting device names from AudioUtilities...")
        all_devices_cache = AudioUtilities.GetAllDevices()

        print("Enumerating output devices...")
        output_devices = self.enumerate_devices(0, all_devices_cache)  # eRender = 0

        print("Enumerating input devices...")
        input_devices = self.enumerate_devices(1, all_devices_cache)  # eCapture = 1

        print(
            f"\nTotal: {len(output_devices)} output devices, {len(input_devices)} input devices"
        )

        return output_devices + input_devices
