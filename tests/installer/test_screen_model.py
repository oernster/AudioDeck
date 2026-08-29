"""The setup program moves to a screen; it never disables the options in place.

The defect this exists for was visible: starting an operation greyed the
checkboxes where they stood and drew a red rectangle round each one, because a
disabled control wears the danger ring by design. Making the greyed boxes
readable was tried and was still wrong. The controls should not be on screen at
all while work is running, so the work has its own screen and the footer under
it offers nothing.

Two guards, because either alone is weak. The runtime one drives the window and
reads what is showing; the static one scans the package for the shape of the
old approach, so it cannot come back by a route the runtime test does not
happen to walk.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox

from installer import constants as c
from installer import screens, wording
from installer.existing import Existing
from installer.route import Route, route_for
from installer.ui import InstallerWindow

INSTALLER_DIR = Path(__file__).resolve().parent.parent.parent / "installer"
ARRIVING = "2.2.0"
INSTALLED = "2.1.0"
OLDER = "2.0.0"

# The shape of the old approach: a loop switching a list of controls off.
DISABLE_IN_PLACE = re.compile(r"setEnabled\(\s*False\s*\)")


@pytest.fixture
def window(qapp, monkeypatch, tmp_path) -> InstallerWindow:
    """A window built on a fixed reading of the machine.

    The real reading is a registry lookup and a manifest file, so it is
    replaced here: the screens are what is under test, not what this developer
    happens to have installed.
    """
    monkeypatch.setattr("installer.ui.ops.payload_version", lambda: ARRIVING)
    monkeypatch.setattr(
        "installer.ui.existing.look",
        lambda: Existing(
            version=INSTALLED,
            location=tmp_path,
            desktop=False,
            start_menu=True,
        ),
    )
    made = InstallerWindow()
    yield made
    made.close()


def test_the_route_is_read_from_what_the_machine_holds() -> None:
    """One reading decides the conversation, so nothing else can re-derive it."""
    assert route_for("", ARRIVING, uninstalling=False) is Route.INSTALL
    assert route_for(INSTALLED, ARRIVING, uninstalling=False) is Route.UPDATE
    assert route_for(INSTALLED, OLDER, uninstalling=False) is Route.DOWNGRADE
    assert route_for(INSTALLED, INSTALLED, uninstalling=False) is Route.MANAGE
    assert route_for("", ARRIVING, uninstalling=True) is Route.UNINSTALL


@pytest.mark.parametrize("route", (Route.UPDATE, Route.DOWNGRADE))
def test_a_change_of_version_names_neither_of_them_in_the_heading(route) -> None:
    """Both versions belong in the flow line, so naming one there is wrong."""
    heading = wording.heading(route, INSTALLED, ARRIVING)

    assert INSTALLED not in heading
    assert ARRIVING not in heading


def test_working_shows_the_progress_screen_and_offers_nothing(window) -> None:
    """A screen with nothing safe to offer offers nothing at all."""
    window._working("Updating")

    assert window._body.currentIndex() == screens.SCREEN_PROGRESS
    assert window._footer.buttons() == ()


def test_no_option_is_disabled_while_the_work_runs(window) -> None:
    """The options are not on screen to be greyed, so none of them is."""
    window._working("Updating")

    boxes = window.findChildren(QCheckBox)
    assert boxes, "the route screen should carry the choices"
    assert [box for box in boxes if not box.isEnabled()] == []


def test_a_verdict_leaves_only_a_way_out(window) -> None:
    """Every path ends in a verdict; a verdict ends in Close."""
    window._verdict("x", "It worked", "Nothing else changed.")

    assert window._body.currentIndex() == screens.SCREEN_VERDICT
    assert [b.text() for b in window._footer.buttons()] == ["Close"]


def test_the_footer_belongs_to_the_screen(window) -> None:
    """Rebuilding drops the old buttons rather than relabelling one row.

    A button awaiting deletion is still a child and still drawn, so the old
    ones are unparented as well: this reads the row, not the deletion queue.
    """
    window._working("Updating")
    window._show_route()

    labels = [b.text() for b in window._footer.buttons()]
    assert labels == ["Uninstall", "Not now", "Update"]


def test_removal_is_a_screen_reachable_from_the_route(window) -> None:
    """The route never becomes removal; the screen behind it stays put."""
    window._show_uninstall()

    assert window.route is Route.UPDATE
    assert window._body.currentIndex() == screens.SCREEN_UNINSTALL
    assert [b.text() for b in window._footer.buttons()] == ["Cancel", "Uninstall"]

    window._cancel_removal()

    assert window._body.currentIndex() == screens.SCREEN_ROUTE


def _ring(window: InstallerWindow) -> list:
    """The stops a real Tab press would reach, in the order it reaches them."""
    start = window._focus_sink
    stops, current = [], start
    while True:
        current = current.nextInFocusChain()
        if current is start:
            return stops
        if (
            current.focusPolicy() & Qt.FocusPolicy.TabFocus
            and current.isVisible()
            and current.isEnabled()
        ):
            stops.append(current)


def test_the_ring_runs_in_reading_order(window) -> None:
    """Header, then the choices, then the footer.

    The footer's buttons are built fresh for each screen, so Qt's own order
    follows when they were made rather than where they are drawn: without the
    window stating the order, the first Tab lands in the footer.
    """
    window.resize(c.WINDOW_MIN_WIDTH, c.WINDOW_MIN_HEIGHT)
    window.show()

    stops = _ring(window)
    places = [
        (
            stop.mapTo(window, stop.rect().center()).y(),
            stop.mapTo(window, stop.rect().center()).x(),
        )
        for stop in stops
    ]

    assert len(stops) > 1
    assert places == sorted(places), [(type(s).__name__, s.objectName()) for s in stops]


def test_nothing_in_the_setup_program_disables_a_control() -> None:
    """The static half: the old approach cannot return by another route.

    Proved to bite by planting `widget.setEnabled(False)` in the window and
    watching this fail.
    """
    offences = [
        f"{path.name}:{number}"
        for path in sorted(INSTALLER_DIR.glob("*.py"))
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if DISABLE_IN_PLACE.search(line)
    ]

    assert offences == [], (
        "a control is switched off where it stands; work belongs on its own "
        f"screen instead: {offences}"
    )
