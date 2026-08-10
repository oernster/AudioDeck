"""Tests for the auto-scroller state machine.

The cycle is driven by calling the tick directly, never by waiting: every
phase is a whole number of 40ms ticks. The component's own timer is stopped
first, after asserting it was running.
"""

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QTextBrowser, QWidget

from src.presentation.widgets.auto_scroller import (
    BOTTOM_HOLD_MS,
    DESCENT_TICKS_PER_STEP,
    MANUAL_RESUME_MS,
    REWIND_STEP_PX,
    START_HOLD_MS,
    TICK_MS,
    TOP_HOLD_MS,
    AutoScroller,
)

_START_HOLD_TICKS = START_HOLD_MS // TICK_MS
_BOTTOM_HOLD_TICKS = BOTTOM_HOLD_MS // TICK_MS
_TOP_HOLD_TICKS = TOP_HOLD_MS // TICK_MS
# The manual hold is not a whole multiple of the tick, so one extra tick
# finishes it.
_MANUAL_TICKS = MANUAL_RESUME_MS // TICK_MS + 1

_LONG_TEXT = "\n".join(f"line {i}" for i in range(300))
_DESCEND_SAFETY_CAP = 100_000


def _browser(qtbot, text=_LONG_TEXT):
    browser = QTextBrowser()
    qtbot.addWidget(browser)
    browser.setPlainText(text)
    browser.resize(300, 120)
    browser.show()
    return browser


def _scroller(browser, active_modal=lambda: None):
    scroller = AutoScroller(browser, active_modal)
    assert scroller._timer.isActive()
    scroller._timer.stop()
    return scroller


def _tick(scroller, times):
    for _ in range(times):
        scroller._tick()


def _spend_start_hold(scroller):
    _tick(scroller, _START_HOLD_TICKS)


def _descend_to_bottom(scroller, bar):
    ticks = 0
    while bar.value() < bar.maximum():
        scroller._tick()
        ticks += 1
        assert ticks < _DESCEND_SAFETY_CAP
    return ticks


def test_overflowing_content_is_required(qtbot):
    browser = _browser(qtbot, text="short")
    assert browser.verticalScrollBar().maximum() == 0
    scroller = _scroller(browser)
    _tick(scroller, _START_HOLD_TICKS * 2)
    assert browser.verticalScrollBar().value() == 0
    # The start hold has not been consumed: overflow later still holds first.
    assert scroller._wait_ms == START_HOLD_MS


def test_the_surface_holds_still_before_the_first_descent(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _tick(scroller, _START_HOLD_TICKS - 1)
    assert browser.verticalScrollBar().value() == 0


def test_descent_moves_one_pixel_every_second_tick(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1
    _tick(scroller, DESCENT_TICKS_PER_STEP * 3)
    assert browser.verticalScrollBar().value() == 4


def test_input_during_the_start_hold_is_not_a_reader(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _tick(scroller, 10)
    scroller.eventFilter(browser, QEvent(QEvent.Type.Wheel))
    _tick(scroller, _START_HOLD_TICKS - 10)
    # The full start hold, not the shorter manual hold, governed the wait.
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_manual_input_suspends_then_resumes_in_place(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    _tick(scroller, DESCENT_TICKS_PER_STEP * 4)
    position = browser.verticalScrollBar().value()

    scroller.eventFilter(browser, QEvent(QEvent.Type.MouseButtonPress))
    _tick(scroller, _MANUAL_TICKS - 1)
    assert browser.verticalScrollBar().value() == position

    _tick(scroller, 1 + DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == position + 1


def test_key_press_counts_as_reading(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    scroller.eventFilter(browser, QEvent(QEvent.Type.KeyPress))
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 0


def test_unrelated_events_do_not_suspend(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    scroller.eventFilter(browser, QEvent(QEvent.Type.Paint))
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_focus_entering_the_surface_suspends(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    scroller._on_focus_changed(None, browser)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 0


def test_focus_entering_a_child_suspends(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    scroller._on_focus_changed(None, browser.viewport())
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 0


def test_focus_elsewhere_does_not_suspend(qtbot):
    browser = _browser(qtbot)
    elsewhere = QWidget()
    qtbot.addWidget(elsewhere)
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    scroller._on_focus_changed(None, elsewhere)
    scroller._on_focus_changed(None, None)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_the_full_cycle_holds_rewinds_and_repeats(qtbot):
    browser = _browser(qtbot)
    bar = browser.verticalScrollBar()
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    _descend_to_bottom(scroller, bar)
    assert bar.value() == bar.maximum()

    # The bottom hold keeps the tail readable before the rewind.
    _tick(scroller, _BOTTOM_HOLD_TICKS - 1)
    assert bar.value() == bar.maximum()

    # The rewind repositions fast.
    _tick(scroller, 2)
    assert bar.value() == bar.maximum() - REWIND_STEP_PX
    while bar.value() > 0:
        scroller._tick()

    # The top hold, then the next reading pass begins.
    _tick(scroller, _TOP_HOLD_TICKS)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert bar.value() == 1


def test_manual_at_the_bottom_resumes_with_the_rewind(qtbot):
    browser = _browser(qtbot)
    bar = browser.verticalScrollBar()
    scroller = _scroller(browser)
    _spend_start_hold(scroller)
    _descend_to_bottom(scroller, bar)

    scroller.eventFilter(browser, QEvent(QEvent.Type.Wheel))
    _tick(scroller, _MANUAL_TICKS + 1)
    assert bar.value() == bar.maximum() - REWIND_STEP_PX


def test_an_unrelated_modal_freezes_time_and_input(qtbot):
    browser = _browser(qtbot)
    modal_holder = {"modal": None}
    scroller = _scroller(browser, active_modal=lambda: modal_holder["modal"])
    _tick(scroller, 10)

    unrelated = QWidget()
    qtbot.addWidget(unrelated)
    modal_holder["modal"] = unrelated

    # Time does not pass and input is not a reader while frozen.
    _tick(scroller, _START_HOLD_TICKS)
    scroller.eventFilter(browser, QEvent(QEvent.Type.Wheel))
    assert browser.verticalScrollBar().value() == 0

    # The cycle resumes exactly where it was: the remaining hold, then down.
    modal_holder["modal"] = None
    _tick(scroller, _START_HOLD_TICKS - 10)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_the_surfaces_own_modal_window_does_not_freeze_it(qtbot):
    browser = _browser(qtbot)
    scroller = _scroller(browser, active_modal=lambda: browser)
    _spend_start_hold(scroller)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_a_modal_containing_the_surface_does_not_freeze_it(qtbot):
    outer = QWidget()
    qtbot.addWidget(outer)
    panel = QWidget(outer)
    browser = QTextBrowser(panel)
    browser.setPlainText(_LONG_TEXT)
    outer.resize(300, 120)
    panel.resize(300, 120)
    browser.resize(300, 120)
    outer.show()
    assert browser.verticalScrollBar().maximum() > 0

    scroller = _scroller(browser, active_modal=lambda: panel)
    _spend_start_hold(scroller)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1


def test_the_default_modal_lookup_is_the_application(qtbot):
    browser = _browser(qtbot)
    scroller = AutoScroller(browser)
    assert scroller._timer.isActive()
    scroller._timer.stop()
    _spend_start_hold(scroller)
    _tick(scroller, DESCENT_TICKS_PER_STEP)
    assert browser.verticalScrollBar().value() == 1
