"""Tests for the per-tab-stop tab bar."""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent

from src.presentation.widgets.nav_tab_bar import NavTabBar


def _bar(qtbot, tabs=("One", "Two", "Three")):
    bar = NavTabBar()
    qtbot.addWidget(bar)
    for title in tabs:
        bar.addTab(title)
    return bar


def _key(bar, key):
    bar.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
    )


def test_the_ring_enters_at_the_side_it_arrives_from(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(1)
    assert bar.cursor_index() == 0
    bar.enter_cursor(-1)
    assert bar.cursor_index() == 2


def test_entering_skips_a_disabled_edge_tab(qtbot):
    bar = _bar(qtbot)
    bar.setTabEnabled(0, False)
    bar.enter_cursor(1)
    assert bar.cursor_index() == 1


def test_stepping_is_bounded_and_reports_running_out(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(1)
    assert bar.step_cursor(1) is True
    assert bar.step_cursor(1) is True
    assert bar.cursor_index() == 2
    assert bar.step_cursor(1) is False
    assert bar.cursor_index() is None


def test_stepping_without_a_cursor_reports_running_out(qtbot):
    bar = _bar(qtbot)
    assert bar.step_cursor(1) is False


def test_the_vertical_walk_wraps(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(-1)
    bar.step_cursor_wrapping(1)
    assert bar.cursor_index() == 0
    bar.step_cursor_wrapping(-1)
    assert bar.cursor_index() == 2


def test_the_vertical_walk_starts_from_the_top_without_a_cursor(qtbot):
    bar = _bar(qtbot)
    bar.step_cursor_wrapping(1)
    assert bar.cursor_index() == 0


def test_enter_commits_the_cursor_tab(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(-1)
    _key(bar, Qt.Key.Key_Return)
    assert bar.currentIndex() == 2


def test_space_commits_the_cursor_tab(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(1)
    bar.step_cursor(1)
    _key(bar, Qt.Key.Key_Space)
    assert bar.currentIndex() == 1


def test_commit_without_a_cursor_changes_nothing(qtbot):
    bar = _bar(qtbot)
    _key(bar, Qt.Key.Key_Return)
    assert bar.currentIndex() == 0


def test_the_bars_own_arrow_handling_is_swallowed(qtbot):
    # Qt's native left/right tab switching must not run while walking.
    bar = _bar(qtbot)
    bar.enter_cursor(1)
    _key(bar, Qt.Key.Key_Right)
    assert bar.currentIndex() == 0


def test_focus_in_seeds_the_cursor_from_the_current_tab(qtbot):
    bar = _bar(qtbot)
    bar.setCurrentIndex(1)
    bar.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
    assert bar.cursor_index() == 1


def test_focus_in_keeps_a_cursor_the_ring_already_placed(qtbot):
    bar = _bar(qtbot)
    bar.enter_cursor(-1)
    bar.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
    assert bar.cursor_index() == 2


def test_focus_in_on_an_empty_bar_has_no_cursor(qtbot):
    bar = _bar(qtbot, tabs=())
    bar.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
    assert bar.cursor_index() is None


def test_focus_out_drops_the_cursor_and_ring(qtbot):
    bar = _bar(qtbot)
    bar.focusInEvent(QFocusEvent(QEvent.Type.FocusIn))
    bar.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
    assert bar.cursor_index() is None


def test_painting_with_and_without_the_ring(qtbot):
    bar = _bar(qtbot)
    bar.resize(300, 40)
    bar.grab()  # no ring: the early return
    bar._show_ring = True
    bar._cursor = 1
    bar.grab()  # ring drawn around the cursor tab
    bar._cursor = 99
    bar.grab()  # a null rect: nothing to ring
