"""CLI handler for headless profile switching."""

import sys
from pathlib import Path

from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.cli.argument_parser import CLIArguments
from src.domain.exceptions.domain_exceptions import ProfileNotFoundException
from src.infrastructure.backend_factory import create_device_backend
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from src.infrastructure.persistence.json_profile_repository import JsonProfileRepository


class CLIHandler:
    """Handler for CLI operations."""

    def __init__(
        self,
        get_profiles_use_case: GetProfilesUseCase,
        switch_profile_use_case: SwitchProfileUseCase,
    ) -> None:
        """Initialize CLI handler with its use cases.

        Args:
            get_profiles_use_case: Use case for retrieving profiles
            switch_profile_use_case: Use case for switching profiles
        """
        self._get_profiles_use_case = get_profiles_use_case
        self._switch_profile_use_case = switch_profile_use_case

    @classmethod
    def from_profiles_path(
        cls, profiles_path: Path
    ) -> "CLIHandler":  # pragma: no cover
        """Build a CLI handler wired to the real platform infrastructure.

        This is the CLI composition root; it is excluded from coverage because
        it constructs the platform's real audio backend.

        Args:
            profiles_path: Path to profiles JSON file

        Returns:
            A CLIHandler wired to real infrastructure.
        """
        backend = create_device_backend(sys.platform)
        device_repository = CachingDeviceRepository(backend.enumerator)
        profile_repository = JsonProfileRepository(profiles_path)
        return cls(
            GetProfilesUseCase(profile_repository),
            SwitchProfileUseCase(
                profile_repository, device_repository, backend.controller
            ),
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
            print(
                "\nTo create profiles, run AudioDeck without arguments to open the GUI."
            )
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
        print('  AudioDeck.exe --profile "PROFILE_NAME"')
        print("\nExample:")
        # The empty case returned above, so there is always a first profile.
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
            outcome = self._switch_profile_use_case.execute(profile_dto.id)
        except ProfileNotFoundException as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        if outcome.anything_applied:
            print("✓ Profile switched successfully!")
            changed = " and ".join(
                device_type.display_name for device_type in outcome.applied
            )
            print(f"  Changed: {changed} device(s)")

        if outcome.skipped:
            print(
                "\nSome devices were not available and were skipped:",
                file=sys.stderr,
            )
            for skipped in outcome.skipped:
                print(
                    f"  - {skipped.device_type.display_name} "
                    f"({skipped.reason.label})",
                    file=sys.stderr,
                )

        return 0 if outcome.anything_applied else 1
