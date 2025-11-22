"""CLI handler for headless profile switching."""

import sys
from pathlib import Path
from typing import NoReturn

from src.infrastructure.windows.device_enumerator import WindowsDeviceEnumerator
from src.infrastructure.windows.windows_device_controller import WindowsDeviceController
from src.infrastructure.windows.windows_device_repository import WindowsDeviceRepository
from src.infrastructure.persistence.json_profile_repository import JsonProfileRepository
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.exceptions.domain_exceptions import (
    ProfileNotFoundException,
    DeviceNotFoundException,
    DeviceControlException,
)
from src.cli.argument_parser import CLIArguments


class CLIHandler:
    """Handler for CLI operations."""

    def __init__(self, profiles_path: Path) -> None:
        """Initialize CLI handler.

        Args:
            profiles_path: Path to profiles JSON file
        """
        # Infrastructure layer
        device_enumerator = WindowsDeviceEnumerator()
        device_controller = WindowsDeviceController()
        device_repository = WindowsDeviceRepository(device_enumerator)
        profile_repository = JsonProfileRepository(profiles_path)

        # Application layer
        self._get_profiles_use_case = GetProfilesUseCase(profile_repository)
        self._switch_profile_use_case = SwitchProfileUseCase(
            profile_repository, device_repository, device_controller
        )

    def handle(self, args: CLIArguments) -> int:
        """Handle CLI command.

        Args:
            args: Parsed CLI arguments

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            if args.list_profiles:
                return self._list_profiles()
            elif args.profile_name:
                return self._switch_profile(args.profile_name)
            else:
                # Should not reach here if argument parser is correct
                print("Error: No valid command specified", file=sys.stderr)
                return 1

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _list_profiles(self) -> int:
        """List all available profiles.

        Returns:
            Exit code
        """
        profiles = self._get_profiles_use_case.execute()

        if not profiles:
            print("No profiles configured.")
            print("\nTo create profiles, run AudioDeck without arguments to open the GUI.")
            return 0

        print("Available Audio Profiles:")
        print("=" * 50)
        for profile in profiles:
            devices = []
            if profile.has_output:
                devices.append("Output")
            if profile.has_input:
                devices.append("Input")

            device_info = f" ({' + '.join(devices)})" if devices else " (Empty)"
            print(f"  • {profile.name}{device_info}")

        print("\nTo switch to a profile, use:")
        print(f'  AudioDeck.exe --profile "PROFILE_NAME"')
        print("\nExample:")
        if profiles:
            print(f'  AudioDeck.exe --profile "{profiles[0].name}"')

        return 0

    def _switch_profile(self, profile_name: str) -> int:
        """Switch to the specified profile.

        Args:
            profile_name: Name of profile to switch to

        Returns:
            Exit code
        """
        # Get profile by name
        profile_dto = self._get_profiles_use_case.get_by_name(profile_name)

        if profile_dto is None:
            print(f'Error: Profile "{profile_name}" not found.', file=sys.stderr)
            print("\nAvailable profiles:", file=sys.stderr)

            profiles = self._get_profiles_use_case.execute()
            if profiles:
                for p in profiles:
                    print(f"  • {p.name}", file=sys.stderr)
            else:
                print("  (No profiles configured)", file=sys.stderr)

            print("\nUse --list to see all profiles with details.", file=sys.stderr)
            return 1

        # Switch to profile
        try:
            print(f'Switching to profile "{profile_name}"...')
            self._switch_profile_use_case.execute(profile_dto.id)
            print("✓ Profile switched successfully!")

            # Show what was changed
            if profile_dto.has_output and profile_dto.has_input:
                print("  Changed: Output and Input devices")
            elif profile_dto.has_output:
                print("  Changed: Output device")
            elif profile_dto.has_input:
                print("  Changed: Input device")

            return 0

        except ProfileNotFoundException as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except DeviceNotFoundException as e:
            print(f"Error: Device not found - {e}", file=sys.stderr)
            print("\nThe profile may reference devices that are no longer available.", file=sys.stderr)
            print("Please update the profile in the GUI.", file=sys.stderr)
            return 1
        except DeviceControlException as e:
            print(f"Error: Failed to switch devices - {e}", file=sys.stderr)
            return 1