"""Main application window.

Author: Oliver Ernster
"""

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.notifiers.notifier_factory import (
    create_device_change_notifier,
)
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.presenters.update_presenter import UpdatePresenter
from src.presentation.views import help_dialogs, update_dialogs
from src.presentation.views.actuation_view import ActuationView
from src.presentation.views.configuration_view import ConfigurationView
from src.presentation.views.resource_paths import resource_path
from src.presentation.widgets.keyboard_nav import KeyboardNavigator
from src.presentation.widgets.nav_tab_bar import RING_GREEN as NAV_RING_GREEN
from src.presentation.widgets.nav_tab_bar import NavTabBar

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
    ) -> None:
        """Initialize main window.

        Args:
            configuration_presenter: Presenter for configuration view
            actuation_presenter: Presenter for actuation view
            update_presenter: Presenter for the update check
        """
        super().__init__()
        self._configuration_presenter = configuration_presenter
        self._actuation_presenter = actuation_presenter
        self._update_presenter = update_presenter
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

        # Create tab widget; its bar carries the keyboard cursor, one ring
        # stop per tab.
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabBar(NavTabBar())
        layout.addWidget(self._tab_widget)

        # Create Help button and add to tab widget corner
        self._create_help_button()

        # Create views
        self._configuration_view = ConfigurationView(self._configuration_presenter)
        self._actuation_view = ActuationView(self._actuation_presenter)

        # Add tabs
        self._tab_widget.addTab(self._actuation_view, "🔄 Quick Switch")
        self._tab_widget.addTab(self._configuration_view, "⚙️ Configuration")

        # React to device changes via the native notifier (debounced in the view)
        self._install_device_notifier()

    def _install_device_notifier(self) -> None:
        """Install the native device-change notifier on the application."""
        app = QApplication.instance()
        if app is None:
            return
        self._device_notifier = create_device_change_notifier(
            sys.platform, self._actuation_view.handle_device_change
        )
        self._device_notifier.install(app)

    def _create_help_button(self) -> None:
        """Create Help button in the tab widget corner."""
        # Create Help button with menu
        help_button = QToolButton()
        help_button.setObjectName("HelpButton")
        help_button.setText("ℹ️ Help")
        help_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        # Blue fill; the ring rules follow the app-wide three-state model
        # (green on hover or focus while enabled), stated here because an
        # object-name rule setting border would otherwise swallow them.
        help_button.setStyleSheet(f"""
            QToolButton#HelpButton {{
                background-color: #4A90E2;
                color: white;
                border: 2px solid transparent;
                border-radius: 20px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13.5pt;
                min-width: 60px;
            }}
            QToolButton#HelpButton:enabled:hover,
            QToolButton#HelpButton:enabled:focus {{
                border-color: {NAV_RING_GREEN};
            }}
            QToolButton#HelpButton:pressed {{
                background-color: #2868A8;
            }}
            QToolButton#HelpButton::menu-indicator {{
                image: none;
            }}
        """)
        help_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Create Help menu
        help_menu = QMenu(help_button)

        # Documentation action
        docs_action = QAction("View Documentation", self)
        docs_action.triggered.connect(self._show_documentation)
        help_menu.addAction(docs_action)

        # Development Documentation action
        dev_docs_action = QAction("Development Documentation", self)
        dev_docs_action.triggered.connect(self._show_dev_documentation)
        help_menu.addAction(dev_docs_action)

        # License action
        license_action = QAction("View License (LGPL-3.0)", self)
        license_action.triggered.connect(self._show_license)
        help_menu.addAction(license_action)

        help_menu.addSeparator()

        # Check for Updates action
        updates_action = QAction("Check for Updates", self)
        updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(updates_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("About Audio Deck", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        help_button.setMenu(help_menu)

        # Add Help button to tab widget corner (top-right)
        self._tab_widget.setCornerWidget(help_button, Qt.Corner.TopRightCorner)

    # The Help actions are thin wrappers so the menu wiring above reads as
    # a menu, so a Qt signal always has a bound method to connect to.
    def _show_documentation(self) -> None:
        help_dialogs.show_documentation(self)

    def _show_dev_documentation(self) -> None:
        help_dialogs.show_dev_documentation(self)

    def _show_license(self) -> None:
        help_dialogs.show_license(self)

    def _check_for_updates(self) -> None:
        self._update_presenter.check_manually()

    def _show_about(self) -> None:
        help_dialogs.show_about(self)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect tab change to refresh views
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

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

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event.

        Args:
            index: Index of the new tab
        """
        # Only refresh configuration view when switching to it
        # Actuation view will be refreshed only when profiles are saved
        if index == 1:  # Configuration view
            self._configuration_view.refresh()

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
