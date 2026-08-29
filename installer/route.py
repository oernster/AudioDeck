"""Which conversation the setup program is having.

One reading of the machine decides everything the window then shows: the
screen, its heading, the options on it and the buttons under it. Deciding it
once, here, is what stops those four drifting apart, which is how a downgrade
came to be announced under a heading saying the newer version was already
installed.

Pure, with no Qt in sight, so every state can be asserted in a test rather than
read off a screenshot.

Author: Oliver Ernster
"""

from __future__ import annotations

import enum

from installer.versioning import compare_versions


class Route(enum.Enum):
    """The five states setup can be run in."""

    INSTALL = "install"
    UPDATE = "update"
    DOWNGRADE = "downgrade"
    MANAGE = "manage"
    UNINSTALL = "uninstall"


def route_for(installed: str, version: str, uninstalling: bool) -> Route:
    """Which route this run takes, from what is recorded as installed.

    Being asked to uninstall settles it before anything else is considered,
    because that is the one route the user names rather than setup deducing it.

    Args:
        installed: The recorded version, empty when nothing is installed.
        version: The version this setup file carries.
        uninstalling: Whether removal was asked for on the command line.

    Returns:
        The route this run of setup is on.
    """
    if uninstalling:
        return Route.UNINSTALL
    if not installed:
        return Route.INSTALL
    comparison = compare_versions(version, installed)
    if comparison > 0:
        return Route.UPDATE
    if comparison < 0:
        return Route.DOWNGRADE
    return Route.MANAGE
