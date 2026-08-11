"""Main application window.

Author: Oliver Ernster
"""

import sys
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.presentation.notifiers.notifier_factory import (
    create_device_change_notifier,
)
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.presenters.update_presenter import UpdatePresenter
from src.presentation.views import help_dialogs, tray, update_dialogs
from src.presentation.views.actuation_view import ActuationView
from src.presentation.views.configuration_view import ConfigurationView
from src.presentation.views.help_button import build_help_button
from src.presentation.views.resource_paths import resource_path
from src.presentation.widgets.keyboard_nav import KeyboardNavigator

# The main window's title. A second launch locates the running instance by
# this exact string, so the two must never drift apart.
WINDOW_TITLE = "Audio Deck"

# The launch update check waits so it never contends with startup work; the
# periodic re-check covers sessions that stay open for days.
UPDATE_LAUNCH_DELAY_MS = 3000
UPDATE_RECHECK_INTERVAL_MS = 24 * 60 * 60 * 1000


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(
        self,
        configuration_presenter: ConfigurationPresenter,
        actuation_presenter: ActuationPresenter,
        update_presenter: UpdatePresenter,
        on_toggle_theme: Callable[[], None],
    ) -> None:
        """Initialize main window.

        Args:
            configuration_presenter: Presenter for configuration view
            actuation_presenter: Presenter for actuation view
            update_presenter: Presenter for the update check
            on_toggle_theme: Switches the app between dark and light
        """
        super().__init__()
        self._configuration_presenter = configuration_presenter
        self._actuation_presenter = actuation_presenter
        self._update_presenter = update_presenter
        self._on_toggle_theme = on_toggle_theme
        self._started = False

        self._setup_ui()
        self._connect_signals()
        self._start_update_checks()

        # Neutral start: a zero-size focus sink absorbs the initial focus so
        # nothing is highlighted on launch; the first Tab or Right enters the
        # ring, driven by the application-level navigator.
        self._focus_sink = QWidget(self)
        self._focus_sink.setFixedSize(0, 0)
        self._focus_sink.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self._keyboard_navigator = KeyboardNavigator(self)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Start neutral: focus the sink once, on first show."""
        super().showEvent(event)
        if not self._started:
            self._started = True
            self._focus_sink.setFocus()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(600, 500)

        # Set window icon
        icon_path = resource_path("assets/audiodeck.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Two view icons, a separator, then the ACTIVE view's action icons,
        # then the theme toggle and Help on the right. Icons only: no button
        # chrome, the glyph is the control.
        self._quick_switch_button = self._make_view_button("🔄", "Quick Switch")
        self._configuration_button = self._make_view_button("⚙️", "Configuration")

        # Create views (their action buttons live in the header, below)
        self._configuration_view = ConfigurationView(self._configuration_presenter)
        self._actuation_view = ActuationView(self._actuation_presenter)

        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 0)
        header.addWidget(self._quick_switch_button)
        header.addWidget(self._configuration_button)
        header.addWidget(tray.make_separator())
        self._view_action_buttons = (
            self._adopt_tray_actions(header, self._actuation_view.tray_actions()),
            self._adopt_tray_actions(header, self._configuration_view.tray_actions()),
        )
        header.addStretch()
        self._theme_toggle = tray.ThemeToggleButton()
        self._theme_toggle.clicked.connect(self._on_toggle_theme)
        header.addWidget(self._theme_toggle)
        header.addWidget(self._create_help_button())
        layout.addLayout(header)

        self._view_stack = QStackedWidget()
        self._view_stack.addWidget(self._actuation_view)
        self._view_stack.addWidget(self._configuration_view)
        layout.addWidget(self._view_stack)

        self._quick_switch_button.clicked.connect(lambda: self._show_view(0))
        self._configuration_button.clicked.connect(lambda: self._show_view(1))
        self._show_view(0)

        # React to device changes via the native notifier (debounced in the view)
        self._install_device_notifier()

    @staticmethod
    def _make_view_button(glyph: str, name: str) -> QPushButton:
        """Build one view-switching icon, in the ClearBudget tray style."""
        button = QPushButton()
        tray.style_tray_button(button, glyph, name, "ViewButton")
        return button

    @staticmethod
    def _adopt_tray_actions(
        header: QHBoxLayout, actions: tuple[tuple[QPushButton, str, str], ...]
    ) -> tuple[QPushButton, ...]:
        """Restyle one view's action buttons as tray icons and add them."""
        buttons = []
        for button, glyph, name in actions:
            tray.style_tray_button(button, glyph, name, "TrayAction")
            header.addWidget(button)
            buttons.append(button)
        return tuple(buttons)

    def _show_view(self, index: int) -> None:
        """Show a view, mark its button active and swap the tray actions.

        Args:
            index: 0 for Quick Switch, 1 for Configuration
        """
        self._view_stack.setCurrentIndex(index)
        self._mark_active_view_button(index)
        for position, buttons in enumerate(self._view_action_buttons):
            for button in buttons:
                button.setVisible(position == index)
        # Refresh whichever view is being entered: the profile store can
        # have changed in the OTHER view (a save, an edit, a delete) and
        # a stale list would show a deleted profile as switchable.
        if index == 0:
            self._actuation_view.refresh()
        else:
            self._configuration_view.refresh()

    def _mark_active_view_button(self, index: int) -> None:
        """Disable the displayed view's button: present but inert.

        The disabled state paints the permanent red ring, which is the
        app-wide marker for a control that exists but cannot be used, and
        the keyboard ring skips it, so the current view is never a stop.
        """
        buttons = (self._quick_switch_button, self._configuration_button)
        for position, button in enumerate(buttons):
            button.setEnabled(position != index)

    def _install_device_notifier(self) -> None:
        """Install the native device-change notifier on the application."""
        app = QApplication.instance()
        if app is None:
            return
        self._device_notifier = create_device_change_notifier(
            sys.platform, self._actuation_view.handle_device_change
        )
        self._device_notifier.install(app)

    def _create_help_button(self) -> QPushButton:
        """Create the Help icon for the header row, menu wired to this window."""
        return build_help_button(
            self._show_documentation,
            self._show_ui_license,
            self._show_backend_license,
            self._check_for_updates,
            self._show_about,
        )

    # The Help actions are thin wrappers so the menu wiring above reads as
    # a menu, so a Qt signal always has a bound method to connect to.
    def _show_documentation(self) -> None:
        help_dialogs.show_documentation(self)

    def _show_ui_license(self) -> None:
        help_dialogs.show_ui_license(self)

    def _show_backend_license(self) -> None:
        help_dialogs.show_backend_license(self)

    def _check_for_updates(self) -> None:
        self._update_presenter.check_manually()

    def _show_about(self) -> None:
        help_dialogs.show_about(self)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect error signals
        self._configuration_presenter.error_occurred.connect(self._show_error)
        self._actuation_presenter.error_occurred.connect(self._show_error)

        # Friendly notice when a profile's device is not currently available
        self._actuation_presenter.device_unavailable.connect(self._show_notice)

        # Brief status when a reconnected device is applied automatically
        self._actuation_presenter.auto_applied.connect(self._on_auto_applied)

        # Connect success signals
        self._configuration_presenter.profile_saved.connect(self._on_profile_saved)
        self._actuation_presenter.profile_switched.connect(self._on_profile_switched)

        # Update check outcomes. The presenter emits from its worker thread;
        # these bound methods run on the GUI thread via queued connections.
        self._update_presenter.update_available.connect(self._on_update_available)
        self._update_presenter.up_to_date.connect(self._on_up_to_date)
        self._update_presenter.check_failed.connect(self._on_update_check_failed)

    def _start_update_checks(self) -> None:
        """Schedule the launch update check and the daily re-check."""
        QTimer.singleShot(
            UPDATE_LAUNCH_DELAY_MS, self._update_presenter.check_automatically
        )
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(UPDATE_RECHECK_INTERVAL_MS)
        self._update_timer.timeout.connect(self._update_presenter.check_automatically)
        self._update_timer.start()

    def _on_update_available(
        self, latest: str, current: str, download_url: str, page_url: str
    ) -> None:
        """Offer an available update.

        Args:
            latest: The published version
            current: The running version
            download_url: The platform asset URL, empty when none matched
            page_url: The release page URL, empty when the payload lacked one
        """
        update_dialogs.show_update_prompt(
            self, self._update_presenter, latest, current, download_url, page_url
        )

    def _on_up_to_date(self) -> None:
        """Report that no newer release exists (manual check only)."""
        update_dialogs.show_up_to_date(self)

    def _on_update_check_failed(self) -> None:
        """Report that the manual check could not reach GitHub."""
        update_dialogs.show_check_failed(self)

    def _show_error(self, message: str) -> None:
        """Show error message dialog.

        Args:
            message: Error message to display
        """
        QMessageBox.critical(self, "Error", message)

    def _show_notice(self, message: str) -> None:
        """Show a non-critical notice (for example a device being unavailable).

        Args:
            message: Notice message to display
        """
        QMessageBox.warning(self, "Device unavailable", message)

    def _on_profile_saved(self, profile_name: str) -> None:
        """Handle profile saved event.

        Args:
            profile_name: Name of the saved profile
        """
        QMessageBox.information(
            self,
            "Success",
            f"Profile '{profile_name}' saved successfully!",
        )
        # Refresh actuation view to show new profile
        self._actuation_view.refresh()

    def _on_auto_applied(self, message: str) -> None:
        """Show a brief status message when a reconnected device is applied.

        Args:
            message: Description of the auto-applied profile.
        """
        self.statusBar().showMessage(message, 5000)

    def _on_profile_switched(self, profile_name: str) -> None:
        """Handle profile switched event.

        Args:
            profile_name: Name of the switched profile
        """
        # Show brief notification (could use system tray notification in future)
        self.statusBar().showMessage(f"Switched to profile: {profile_name}", 3000)

    def show_and_raise(self) -> None:
        """Show window and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()
