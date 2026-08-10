"""Tests for the main-window keyboard navigator.

The ring is driven by feeding key events straight into the navigator's
event filter, with the activity and modal checks injected so the tests
control them.
"""

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.widgets.keyboard_nav import KeyboardNavigator


def _window(qtbot):
    """A miniature of the real window: two view buttons and Help above a
    stack, whose current page holds a list, a combo, a line edit and a
    button."""
    window = QMainWindow()
    qtbot.addWidget(window)
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    quick_button = QPushButton("Quick Switch")
    config_button = QPushButton("Configuration")
    help_button = QToolButton()
    help_button.setText("Help")
    header = QHBoxLayout()
    header.addWidget(quick_button)
    header.addWidget(config_button)
    header.addStretch()
    header.addWidget(help_button)
    layout.addLayout(header)

    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.addWidget(QLabel("not a stop"))
    profile_list = QListWidget()
    profile_list.addItems(["one", "two"])
    page_layout.addWidget(profile_list)
    combo = QComboBox()
    combo.addItems(["a", "b"])
    page_layout.addWidget(combo)
    line_edit = QLineEdit()
    page_layout.addWidget(line_edit)
    button = QPushButton("Switch")
    page_layout.addWidget(button)

    other_page = QWidget()
    QVBoxLayout(other_page).addWidget(QPushButton("Other"))

    stack = QStackedWidget()
    stack.addWidget(page)
    stack.addWidget(other_page)
    layout.addWidget(stack)

    window.show()
    navigator = KeyboardNavigator(
        window, active_modal=lambda: None, window_is_active=lambda: True
    )
    QApplication.instance().removeEventFilter(navigator)

    widgets = {
        "window": window,
        "quick_button": quick_button,
        "config_button": config_button,
        "help": help_button,
        "list": profile_list,
        "combo": combo,
        "line_edit": line_edit,
        "button": button,
        "stack": stack,
    }
    return navigator, widgets


def _press(navigator, key, shift=False):
    modifiers = (
        Qt.KeyboardModifier.ShiftModifier if shift else Qt.KeyboardModifier.NoModifier
    )
    event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers)
    return navigator.eventFilter(navigator, event)


def test_non_key_events_pass_through(qtbot):
    navigator, _ = _window(qtbot)
    assert navigator.eventFilter(navigator, QEvent(QEvent.Type.Paint)) is False


def test_inert_while_a_modal_is_up(qtbot):
    navigator, widgets = _window(qtbot)
    navigator._active_modal = lambda: widgets["button"]
    assert _press(navigator, Qt.Key.Key_Tab) is False


def test_inert_while_the_window_is_inactive(qtbot):
    navigator, _ = _window(qtbot)
    navigator._window_is_active = lambda: False
    assert _press(navigator, Qt.Key.Key_Tab) is False


def test_the_first_forward_press_enters_at_the_first_view_button(qtbot):
    navigator, widgets = _window(qtbot)
    assert _press(navigator, Qt.Key.Key_Tab) is True
    assert widgets["window"].focusWidget() is widgets["quick_button"]


def test_the_first_backward_press_enters_at_the_ring_end(qtbot):
    navigator, widgets = _window(qtbot)
    assert _press(navigator, Qt.Key.Key_Left) is True
    assert widgets["window"].focusWidget() is widgets["button"]


def test_forward_walks_buttons_then_help_then_the_page(qtbot):
    navigator, widgets = _window(qtbot)
    _press(navigator, Qt.Key.Key_Tab)
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["config_button"]
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["help"]
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["list"]


def test_right_is_an_alias_for_tab(qtbot):
    navigator, widgets = _window(qtbot)
    _press(navigator, Qt.Key.Key_Right)
    assert widgets["window"].focusWidget() is widgets["quick_button"]


def test_shift_tab_and_backtab_step_backward(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["button"].setFocus()
    assert _press(navigator, Qt.Key.Key_Backtab) is True
    assert widgets["window"].focusWidget() is widgets["line_edit"]
    assert _press(navigator, Qt.Key.Key_Tab, shift=True) is True
    assert widgets["window"].focusWidget() is widgets["combo"]


def test_the_ring_wraps_forward_from_the_last_stop(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["button"].setFocus()
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["quick_button"]


def test_a_list_keeps_its_vertical_arrows(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["list"].setFocus()
    assert _press(navigator, Qt.Key.Key_Down) is False


def test_a_list_is_one_stop_and_tab_leaves_it(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["list"].setFocus()
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["combo"]


def test_a_closed_combo_drops_open_on_down(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["combo"].setFocus()
    assert _press(navigator, Qt.Key.Key_Down) is True
    assert widgets["combo"].view().isVisible() is True
    widgets["combo"].hidePopup()


def test_up_on_a_closed_combo_changes_nothing(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["combo"].setFocus()
    widgets["combo"].setCurrentIndex(1)
    assert _press(navigator, Qt.Key.Key_Up) is True
    assert widgets["combo"].currentIndex() == 1


def test_return_on_a_closed_combo_passes_through(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["combo"].setFocus()
    assert _press(navigator, Qt.Key.Key_Return) is False


def test_a_line_edit_keeps_its_horizontal_arrows(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["line_edit"].setFocus()
    assert _press(navigator, Qt.Key.Key_Left) is False
    assert _press(navigator, Qt.Key.Key_Right) is False


def test_enter_clicks_the_focused_button(qtbot):
    navigator, widgets = _window(qtbot)
    clicks = []
    widgets["button"].clicked.connect(lambda: clicks.append(True))
    widgets["button"].setFocus()
    assert _press(navigator, Qt.Key.Key_Return) is True
    assert clicks == [True]


def test_unhandled_keys_pass_through(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["button"].setFocus()
    assert _press(navigator, Qt.Key.Key_A) is False


def test_a_disabled_stop_is_skipped(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["combo"].setEnabled(False)
    widgets["list"].setFocus()
    _press(navigator, Qt.Key.Key_Tab)
    assert widgets["window"].focusWidget() is widgets["line_edit"]


def test_a_window_without_a_central_widget_has_no_ring(qtbot):
    window = QMainWindow()
    qtbot.addWidget(window)
    navigator = KeyboardNavigator(
        window, active_modal=lambda: None, window_is_active=lambda: True
    )
    QApplication.instance().removeEventFilter(navigator)
    assert _press(navigator, Qt.Key.Key_Tab) is False


def test_walk_edge_cases_are_skipped_not_collected(qtbot):
    # A window exercising every skip in the collector: a hidden button, a
    # disabled list, a container with no layout, a non-widget child and a
    # nested sub-layout with a spacer.
    window = QMainWindow()
    qtbot.addWidget(window)
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    hidden_button = QPushButton("hidden")
    layout.addWidget(hidden_button)

    disabled_list = QListWidget()
    disabled_list.setEnabled(False)
    layout.addWidget(disabled_list)

    layoutless = QWidget()
    inner_button = QPushButton("inner", layoutless)
    QTimer(layoutless)  # a non-widget child the fallback walk must pass over
    layout.addWidget(layoutless)

    sub_layout = QHBoxLayout()
    nested_button = QPushButton("nested")
    sub_layout.addWidget(nested_button)
    sub_layout.addStretch()  # a spacer item the layout walk must pass over
    layout.addLayout(sub_layout)

    window.show()
    hidden_button.hide()
    navigator = KeyboardNavigator(
        window, active_modal=lambda: None, window_is_active=lambda: True
    )
    QApplication.instance().removeEventFilter(navigator)

    collected = [widget for _, widget in navigator._stops()]
    assert hidden_button not in collected
    assert disabled_list not in collected
    assert inner_button in collected
    assert nested_button in collected


def test_focus_outside_the_ring_steps_to_the_first_stop(qtbot):
    navigator, widgets = _window(qtbot)
    sink = QWidget(widgets["window"])
    sink.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    sink.setFocus()
    # The sink is not a ring stop, so the lookup reports "outside".
    assert navigator._index_of_focus(navigator._stops(), sink) is None
    assert _press(navigator, Qt.Key.Key_Tab) is True
    assert widgets["window"].focusWidget() is widgets["quick_button"]


def test_switching_views_changes_the_collected_page(qtbot):
    navigator, widgets = _window(qtbot)
    widgets["stack"].setCurrentIndex(1)
    QApplication.processEvents()
    widgets["help"].setFocus()
    _press(navigator, Qt.Key.Key_Tab)
    focused = widgets["window"].focusWidget()
    assert isinstance(focused, QPushButton)
    assert focused.text() == "Other"
