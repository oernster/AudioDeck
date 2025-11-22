"""Main application window."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt

from src.presentation.views.configuration_view import ConfigurationView
from src.presentation.views.actuation_view import ActuationView
from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.presenters.actuation_presenter import ActuationPresenter


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(
        self,
        configuration_presenter: ConfigurationPresenter,
        actuation_presenter: ActuationPresenter,
    ) -> None:
        """Initialize main window.

        Args:
            configuration_presenter: Presenter for configuration view
            actuation_presenter: Presenter for actuation view
        """
        super().__init__()
        self._configuration_presenter = configuration_presenter
        self._actuation_presenter = actuation_presenter

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Audio Deck")
        self.setMinimumSize(600, 500)

        # Create central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Create views
        self._configuration_view = ConfigurationView(self._configuration_presenter)
        self._actuation_view = ActuationView(self._actuation_presenter)

        # Add tabs
        self._tab_widget.addTab(self._actuation_view, "Quick Switch")
        self._tab_widget.addTab(self._configuration_view, "Configuration")

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        # Connect tab change to refresh views
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Connect error signals
        self._configuration_presenter.error_occurred.connect(self._show_error)
        self._actuation_presenter.error_occurred.connect(self._show_error)

        # Connect success signals
        self._configuration_presenter.profile_saved.connect(self._on_profile_saved)
        self._actuation_presenter.profile_switched.connect(self._on_profile_switched)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event.

        Args:
            index: Index of the new tab
        """
        if index == 0:  # Actuation view
            self._actuation_view.refresh()
        elif index == 1:  # Configuration view
            self._configuration_view.refresh()

    def _show_error(self, message: str) -> None:
        """Show error message dialog.

        Args:
            message: Error message to display
        """
        QMessageBox.critical(self, "Error", message)

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
