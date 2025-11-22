"""Command-line argument parser for AudioDeck."""

import argparse
from typing import Optional


class CLIArguments:
    """Container for parsed CLI arguments."""

    def __init__(
        self,
        list_profiles: bool = False,
        profile_name: Optional[str] = None,
    ) -> None:
        """Initialize CLI arguments.

        Args:
            list_profiles: Whether to list all profiles
            profile_name: Name of profile to switch to
        """
        self.list_profiles = list_profiles
        self.profile_name = profile_name

    @property
    def is_cli_mode(self) -> bool:
        """Check if any CLI arguments were provided.

        Returns:
            True if CLI mode should be used
        """
        return self.list_profiles or self.profile_name is not None


def parse_arguments() -> CLIArguments:
    """Parse command-line arguments.

    Returns:
        Parsed CLI arguments
    """
    parser = argparse.ArgumentParser(
        prog="AudioDeck",
        description="Audio device profile switcher for Windows",
        epilog="When run without arguments, launches the GUI interface.",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available audio profiles",
    )

    parser.add_argument(
        "--profile",
        type=str,
        metavar="NAME",
        help='Switch to the specified profile by name (e.g., --profile "Gaming Setup")',
    )

    parser.add_argument(
        "--version",
        action="version",
        version="AudioDeck 1.0.0",
    )

    args = parser.parse_args()

    return CLIArguments(
        list_profiles=args.list,
        profile_name=args.profile,
    )