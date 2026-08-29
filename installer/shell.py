"""The furniture every screen is drawn inside.

The header that never changes, the hairline that bounds it and the small pieces
a screen is built from: a styled line of text and a bare column. The window
itself is next door; keeping the two apart is what lets the window be read
without also reading how a label is styled.

Author: Oliver Ernster
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from installer import constants as c

# A hint lines up under its option's text rather than under the box, so the
# indent is derived from the box and the gap beside it.
HINT_INDENT_PX = c.CHECK_PX + c.OPTION_GAP_PX + c.HINT_PAD_PX


def header(
    parent: QWidget,
    title: str,
    tagline: str,
    icon: QIcon,
    controls: Iterable[QPushButton],
) -> QHBoxLayout:
    """The identity, drawn at a size that can be read across the room.

    The mark, then the name over its tagline, then the controls at the right.

    The VERSION is deliberately not here. It belongs in the body, in the line
    that talks about what is installed and what is about to be, where it can be
    read as a sentence; hung beside a 32px title it has no baseline to sit on
    and reads as a fragment that has come adrift.
    """
    row = QHBoxLayout()
    row.setSpacing(c.HEADER_SPACING)
    if not icon.isNull():
        mark = QLabel(parent)
        mark.setPixmap(icon.pixmap(QSize(c.MARK_PX, c.MARK_PX)))
        mark.setFixedSize(c.MARK_PX, c.MARK_PX)
        row.addWidget(mark, alignment=Qt.AlignmentFlag.AlignVCenter)

    who = QVBoxLayout()
    who.setSpacing(0)
    name = label(parent, title, "HeaderTitle")
    # The product name never breaks across two lines, whatever shares the row.
    name.setWordWrap(False)
    who.addWidget(name)
    who.addWidget(label(parent, tagline, "HeaderSub"))
    row.addLayout(who, 1)

    for control in controls:
        row.addWidget(control, alignment=Qt.AlignmentFlag.AlignVCenter)
    return row


def minimum_window_size(header: QHBoxLayout) -> tuple[int, int]:
    """The smallest the window may be, given the header it actually assembled.

    Measured rather than written down. The header is a fixed-size mark, a title
    that never wraps and however many controls sit at the right, so its width
    follows what is IN it: a literal minimum silently stops being big enough
    the moment a control is added; the symptom is a clipped title rather than
    anything that looks like a sizing bug.
    """
    needed = header.sizeHint().width() + 2 * c.CONTENT_MARGIN_H
    return (max(c.WINDOW_MIN_WIDTH, needed), c.WINDOW_MIN_HEIGHT)


def rule(parent: QWidget) -> QFrame:
    """The hairline that separates the header from the body."""
    line = QFrame(parent)
    line.setObjectName("Rule")
    line.setFixedHeight(1)
    # A hairline is chrome, never a stop on the keyboard ring.
    line.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return line


def label(parent: QWidget, text: str, name: str) -> QLabel:
    """One styled line of text."""
    made = QLabel(text, parent)
    made.setObjectName(name)
    made.setWordWrap(True)
    return made


def column(parent: QWidget, centred: bool = False) -> tuple[QWidget, QVBoxLayout]:
    """A bare screen and its column, with no margins of its own.

    Named `Pane` so the stylesheet can leave it transparent: a pane painting the
    flat window colour would cover the glow the window draws behind it.
    """
    screen = QWidget(parent)
    screen.setObjectName("Pane")
    # A pane holds controls; it is never one itself, so it takes no focus.
    screen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    made = QVBoxLayout(screen)
    made.setContentsMargins(0, 0, 0, 0)
    made.setSpacing(0)
    if centred:
        made.addStretch()
    return screen, made


def option(parent: QWidget, box: QCheckBox, hint: str) -> QWidget:
    """One choice, with the muted line that explains it underneath.

    Args:
        parent: The screen the choice is drawn on.
        box: The control the user acts on.
        hint: The note under it, empty when the label says enough.

    Returns:
        The assembled choice.
    """
    holder, made = column(parent)
    made.addWidget(box)
    if hint:
        note = label(holder, hint, "Hint")
        note.setContentsMargins(HINT_INDENT_PX, 0, 0, 0)
        made.addWidget(note)
    return holder
