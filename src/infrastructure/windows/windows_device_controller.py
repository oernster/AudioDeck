"""Windows device controller using pycaw."""

import comtypes
from comtypes import GUID, CLSCTX_ALL, HRESULT, COMMETHOD
from ctypes import POINTER, c_wchar_p
from ctypes.wintypes import DWORD

from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import DeviceControlException


# IPolicyConfig interface definition for Windows 10/11
class IPolicyConfig(comtypes.IUnknown):
    """IPolicyConfig COM interface for setting default audio devices."""

    _iid_ = GUID("{f8679f50-850a-41cf-9c72-430f290290c8}")
    _methods_ = [
        # We only need SetDefaultEndpoint
        COMMETHOD([], HRESULT, "GetMixFormat"),
        COMMETHOD([], HRESULT, "GetDeviceFormat"),
        COMMETHOD([], HRESULT, "ResetDeviceFormat"),
        COMMETHOD([], HRESULT, "SetDeviceFormat"),
        COMMETHOD([], HRESULT, "GetProcessingPeriod"),
        COMMETHOD([], HRESULT, "SetProcessingPeriod"),
        COMMETHOD([], HRESULT, "GetShareMode"),
        COMMETHOD([], HRESULT, "SetShareMode"),
        COMMETHOD([], HRESULT, "GetPropertyValue"),
        COMMETHOD([], HRESULT, "SetPropertyValue"),
        COMMETHOD(
            [],
            HRESULT,
            "SetDefaultEndpoint",
            (["in"], c_wchar_p, "wszDeviceId"),
            (["in"], DWORD, "eRole"),
        ),
        COMMETHOD([], HRESULT, "SetEndpointVisibility"),
    ]


class WindowsDeviceController:
    """Controls audio devices using Windows Core Audio API."""

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: ID of device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If setting default fails
        """
        try:
            print(f"Setting default device: {device_id} (type: {device_type.value})")

            # Get IPolicyConfig interface
            from comtypes import CoCreateInstance

            # IPolicyConfig CLSID for Windows 10/11
            CLSID_PolicyConfig = GUID("{870af99c-171d-4f9e-af0d-e63df40c2bc9}")

            try:
                policy_config = CoCreateInstance(
                    CLSID_PolicyConfig, IPolicyConfig, CLSCTX_ALL
                )
                print("  Got IPolicyConfig interface")
            except Exception as e:
                print(f"  Failed to get IPolicyConfig: {e}")
                raise DeviceControlException(
                    f"Could not access audio policy interface: {e}"
                )

            # Set for all roles (Console, Multimedia, Communications)
            # ERole values: eConsole=0, eMultimedia=1, eCommunications=2
            roles = [0, 1, 2]  # All roles

            success_count = 0
            for role in roles:
                try:
                    result = policy_config.SetDefaultEndpoint(device_id, role)
                    print(f"  Set role {role}: HRESULT={result}")
                    success_count += 1
                except Exception as e:
                    print(f"  Failed to set role {role}: {e}")
                    # Continue with other roles

            if success_count == 0:
                raise DeviceControlException(
                    "Failed to set device as default for any role"
                )

            print(f"  Successfully set device as default for {success_count}/3 roles")

        except DeviceControlException:
            raise
        except Exception as e:
            raise DeviceControlException(f"Failed to set default device: {e}")

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        # Device changes are automatically reflected by Windows
        pass
