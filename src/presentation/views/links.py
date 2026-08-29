"""Handing an address to whatever the desktop opens links with.

One function; it exists for a testing reason worth stating: calling Qt's
opener straight from the window would leave no way to prove the right address
is asked for without either mocking Qt or opening a real browser in the middle
of a test run. With the seam here, a test substitutes this one name and asserts
the exact address it was given.

Note what this does NOT do. It never fetches anything. It asks the desktop to
open the address and the user's own browser does the asking, which is why a
donate button costs the application's offline guarantee nothing.

Author: Oliver Ernster
"""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_externally(address: str) -> bool:
    """Ask the desktop to open `address`; False when it declined to.

    A False is not an exception: a desktop with no browser registered is a
    real state the caller has to tell the user about, rather than a fault.
    """
    return QDesktopServices.openUrl(QUrl(address))
