"""Installer state machine: detect what is installed and which actions apply."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional

from installer import constants as c
from installer.versioning import compare_versions


class Operation(Enum):
    """An action the installer can perform."""

    INSTALL = "Install"
    UPGRADE = "Upgrade"
    REINSTALL = "Reinstall"
    REPAIR = "Repair"
    UNINSTALL = "Uninstall"


# Order in which primary actions fill the two action-button slots.
PRIMARY_PRIORITY = (
    Operation.INSTALL,
    Operation.UPGRADE,
    Operation.REINSTALL,
    Operation.REPAIR,
)


@dataclass(frozen=True)
class InstalledInfo:
    """Details of an existing installation, read from the registry."""

    version: str
    location: str


@dataclass(frozen=True)
class InstallerState:
    """The bundled version plus any detected existing installation."""

    bundled_version: str
    installed: Optional[InstalledInfo]

    def allowed_operations(self) -> FrozenSet[Operation]:
        """Return the operations valid for the current state.

        Returns:
            The set of allowed operations.
        """
        if self.installed is None:
            return frozenset({Operation.INSTALL})

        comparison = compare_versions(self.bundled_version, self.installed.version)
        if comparison == 0:
            return frozenset(
                {Operation.REINSTALL, Operation.REPAIR, Operation.UNINSTALL}
            )
        if comparison > 0:
            return frozenset({Operation.UPGRADE, Operation.UNINSTALL})
        return frozenset({Operation.REPAIR, Operation.UNINSTALL})

    def primary_operations(self) -> tuple[Operation, ...]:
        """Return the allowed primary (non-uninstall) operations, in order."""
        allowed = self.allowed_operations()
        return tuple(op for op in PRIMARY_PRIORITY if op in allowed)

    def status_line(self) -> str:
        """Return a human-readable status line describing the install state."""
        if self.installed is None:
            return f"{c.APP_DISPLAY_NAME} is not installed for this user."
        return (
            f"{c.APP_DISPLAY_NAME} version {self.installed.version} is installed "
            f"at {self.installed.location}."
        )
