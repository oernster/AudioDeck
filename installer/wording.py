"""What the setup program says, decided from the route it is on.

Pure text decisions with no Qt in sight, so the wording for every install state
can be asserted in a test rather than read off a screenshot. The route is
decided once and handed here; nothing in this module re-derives it.

Author: Oliver Ernster
"""

from __future__ import annotations

from installer import constants as c
from installer.route import Route

PRIMARY_LABELS = {
    Route.INSTALL: "Install",
    Route.UPDATE: "Update",
    Route.DOWNGRADE: "Go back",
    Route.MANAGE: "Repair",
    Route.UNINSTALL: "Uninstall",
}

LEADS = {
    Route.INSTALL: (
        "This installs for your account only, so Windows will not ask for "
        "administrator rights."
    ),
    Route.UPDATE: (
        "A newer version is ready to install. Your saved profiles are untouched."
    ),
    Route.DOWNGRADE: (
        "This setup file carries an older version than the one installed. Your "
        "saved profiles are untouched."
    ),
    Route.MANAGE: (
        "Repair puts the files back and leaves everything else alone. "
        "Reinstall writes them again with the choices below."
    ),
    Route.UNINSTALL: (
        f"This removes {c.APP_DISPLAY_NAME} and its shortcuts. Your saved "
        "profiles are never touched."
    ),
}


def primary_label(route: Route) -> str:
    """What the go-ahead button on this route does."""
    return PRIMARY_LABELS[route]


def heading(route: Route, installed: str, version: str) -> str:
    """The screen heading, which is where a single version belongs.

    An update and a downgrade name no version here: they are about two of them,
    so both are shown in the flow line under the heading instead. Naming one
    there would leave the other unsaid or contradict it.

    Args:
        route: The route this run is on.
        installed: The recorded version, empty when nothing is installed.
        version: The version this setup file carries.

    Returns:
        The heading for the screen the route shows.
    """
    if route is Route.UNINSTALL:
        return f"Remove {c.APP_DISPLAY_NAME} {installed or version}?"
    if route is Route.INSTALL:
        return f"Install {c.APP_DISPLAY_NAME} {version}"
    if route is Route.UPDATE:
        return "Update available"
    if route is Route.DOWNGRADE:
        return "Go back a version?"
    return f"{c.APP_DISPLAY_NAME} {installed} is installed"


def lead(route: Route) -> str:
    """The muted line under the heading."""
    return LEADS[route]


DESKTOP_LABEL = "Add a Desktop shortcut"
START_MENU_LABEL = "Add a Start Menu entry"
START_MENU_HINT = "Find it by typing its name in the Start Menu."
LAUNCH_LABEL = f"Start {c.APP_DISPLAY_NAME} when setup finishes"

RUNNING_HEADING = f"{c.APP_DISPLAY_NAME} is open"
RUNNING_LEAD = (
    "It has to close before setup can replace its files. Closing it affects "
    "nothing beyond the device profile it is holding, which is applied again "
    f"the next time you start {c.APP_DISPLAY_NAME}."
)
STILL_RUNNING_HEADING = f"{c.APP_DISPLAY_NAME} is still open"
STILL_RUNNING_LEAD = (
    "Setup could not close it. Close it yourself, including its tray icon, "
    "then run setup again."
)
LAUNCHING_LEAD = "It is starting now."
REMOVED_HEADING = f"{c.APP_DISPLAY_NAME} has been removed"
REMOVED_LEAD = "Your saved profiles have been left where they are."
REPAIRED_HEADING = "Repair complete"
REPAIRED_LEAD = "The files have been put back and nothing else was changed."
REINSTALLED_HEADING = f"{c.APP_DISPLAY_NAME} is reinstalled"
REINSTALLED_LEAD = (
    "The files were written again and the shortcuts put back as a new install "
    "would leave them."
)
FAILED_HEADING = "Setup could not finish"


def working_title(route: Route, reinstalling: bool) -> str:
    """What the progress screen is titled while the files are written."""
    if reinstalling:
        return f"Reinstalling {c.APP_DISPLAY_NAME}"
    titles = {
        Route.INSTALL: f"Installing {c.APP_DISPLAY_NAME}",
        Route.UPDATE: f"Updating {c.APP_DISPLAY_NAME}",
        Route.DOWNGRADE: "Going back a version",
        Route.MANAGE: f"Reinstalling {c.APP_DISPLAY_NAME}",
    }
    return titles[route]


def installed_lead(location: str) -> str:
    """Where the application went; how to open it."""
    return (
        f"It is at {location}. Open it from the Start Menu, then choose the "
        "devices each profile should switch to."
    )
