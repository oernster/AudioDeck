"""The donate button: its address, its seam and what it says when it fails.

The address test is the one that matters most and is the cheapest: a single
wrong character sends a supporter to somebody else's payment page; nothing
about the application would look broken. So it is asserted LITERALLY here
rather than compared against itself.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.views import links, tray
from src.presentation.views import main_window as main_window_module
from src.presentation.views.header_band import DONATE_TOOLTIP
from src.presentation.views.icons import ICON_DONATE
from src.presentation.views.main_window import MainWindow
from src.presentation.widgets.keyboard_nav import KeyboardNavigator
from src.version import DONATE_URL

# The address AudioDeck's own donate button must send a browser to. Written out
# in full rather than imported into the comparison, so this test fails if the
# constant is ever edited, which is the whole point of it.
_EXPECTED_ADDRESS = "https://www.paypal.com/ncp/payment/KJBJ5BBWQ542G"


class _StatusBarStub:
    """Just enough of a window for `open_donation`: a status bar that records.

    The real method is called against this, so the code under test is the
    shipped one rather than a copy of its logic.
    """

    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def statusBar(self) -> "_StatusBarStub":
        return self

    def showMessage(self, text: str, timeout: int) -> None:
        self.messages.append((text, timeout))


def test_the_donation_address_is_audiodecks_own() -> None:
    """A copied address from another app would send money to the wrong project."""
    assert DONATE_URL == _EXPECTED_ADDRESS


def test_the_donation_address_is_https() -> None:
    """A payment page reached over plain http is not one to send anybody to."""
    assert DONATE_URL.startswith("https://")


def test_pressing_donate_asks_the_desktop_for_that_one_address(monkeypatch) -> None:
    """The button hands the address over; it never fetches anything itself."""
    asked: list[str] = []

    def _record(address: str) -> bool:
        asked.append(address)
        return True

    monkeypatch.setattr(main_window_module, "open_externally", _record)
    window = _StatusBarStub()
    MainWindow.open_donation(window)

    assert asked == [_EXPECTED_ADDRESS]
    assert window.messages == []


def test_a_desktop_that_refuses_says_so_in_the_status_bar(monkeypatch) -> None:
    """Silence would leave the user pressing a button that does nothing."""
    monkeypatch.setattr(main_window_module, "open_externally", lambda address: False)
    window = _StatusBarStub()
    MainWindow.open_donation(window)

    assert len(window.messages) == 1
    text, timeout = window.messages[0]
    assert "browser" in text
    assert timeout == main_window_module.STATUS_MESSAGE_TIMEOUT_MS


def test_open_externally_hands_the_address_to_the_desktop(monkeypatch) -> None:
    """The seam passes the address through unchanged and reports the answer."""
    seen: list[str] = []

    def _fake_open(url) -> bool:
        seen.append(url.toString())
        return True

    monkeypatch.setattr(links.QDesktopServices, "openUrl", _fake_open)
    assert links.open_externally(_EXPECTED_ADDRESS) is True
    assert seen == [_EXPECTED_ADDRESS]


def test_open_externally_reports_a_desktop_that_declined(monkeypatch) -> None:
    """A False is a real state to tell the user about, not a fault."""
    monkeypatch.setattr(links.QDesktopServices, "openUrl", lambda url: False)
    assert links.open_externally(_EXPECTED_ADDRESS) is False


def test_the_donate_button_wears_a_tooltip_saying_the_browser_opens() -> None:
    """A beer and a coffee do not say that pressing them leaves the app."""
    assert "browser" in DONATE_TOOLTIP


def test_the_donate_button_sits_immediately_left_of_the_theme_toggle(qtbot) -> None:
    """Ring order is reading order; this is where the header puts it.

    A miniature of the real header rather than the whole window: the ring is
    collected by walking the layout, so the ordering this proves is the same
    ordering the application gets.
    """
    window = QMainWindow()
    qtbot.addWidget(window)
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    view_button = QPushButton()
    tray.style_tray_button(view_button, "quick-switch", "Quick Switch", "ViewButton")
    donate_button = QPushButton()
    tray.style_tray_button(donate_button, ICON_DONATE, DONATE_TOOLTIP, "DonateButton")
    toggle = tray.ThemeToggleButton()
    help_button = QPushButton()
    tray.style_tray_button(help_button, "help-info", "Help", "HelpButton")

    header = QHBoxLayout()
    header.addWidget(view_button)
    header.addStretch()
    header.addWidget(donate_button)
    header.addWidget(toggle)
    header.addWidget(help_button)
    layout.addLayout(header)
    window.show()
    qtbot.waitExposed(window)

    navigator = KeyboardNavigator(
        window, active_modal=lambda: None, window_is_active=lambda: True
    )
    stops = [widget for _, widget in navigator._stops()]

    assert donate_button in stops, "the donate button is not on the keyboard ring"
    assert stops.index(donate_button) == stops.index(toggle) - 1
    assert donate_button.isEnabled()


def test_the_donate_button_draws_its_artwork_at_the_tray_height(qtbot) -> None:
    """It is a member of the tray band, so it takes that band's own height."""
    button = QPushButton()
    qtbot.addWidget(button)
    tray.style_tray_button(button, ICON_DONATE, DONATE_TOOLTIP, "DonateButton")

    assert button.icon().isNull() is False
    assert button.iconSize().height() == tray.ICON_HEIGHT_PX
    assert button.height() == tray.ICON_HEIGHT_PX + tray.ICON_BTN_CHROME_PX
