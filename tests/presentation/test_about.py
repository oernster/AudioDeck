"""What the About box states about the application and who owns it.

Asserted LITERALLY rather than compared against the constant it came from: a
copyright line is a claim about ownership, so a test that reads it out of the
same string it is checking would pass whatever it said.
"""

from __future__ import annotations

from PySide6.QtWidgets import QTextBrowser

from src import __version__
from src.presentation.views.help_dialogs import ABOUT_HTML

EXPECTED_COPYRIGHT = "© Oliver Ernster 2026"


def test_the_about_box_carries_the_copyright(qapp) -> None:
    """The symbol itself, the name and the year of publication."""
    browser = QTextBrowser()
    browser.setHtml(ABOUT_HTML)

    assert EXPECTED_COPYRIGHT in browser.toPlainText()


def test_the_copyright_stands_on_its_own_line(qapp) -> None:
    """Its own paragraph, so it never reads as part of the licence sentence."""
    browser = QTextBrowser()
    browser.setHtml(ABOUT_HTML)

    lines = [line.strip() for line in browser.toPlainText().splitlines()]

    assert EXPECTED_COPYRIGHT in lines


def test_the_about_box_names_the_running_version() -> None:
    """The version comes from the one file that holds it."""
    assert __version__ in ABOUT_HTML
