"""Main application window.

Author: Oliver Ernster
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QDialog,
    QTextBrowser,
    QPushButton,
    QSizePolicy,
    QMenu,
    QToolButton,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap

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
        
        # Set window icon
        icon_path = self._get_resource_path("AudioDeck.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Create Help button and add to tab widget corner
        self._create_help_button()

        # Create views
        self._configuration_view = ConfigurationView(self._configuration_presenter)
        self._actuation_view = ActuationView(self._actuation_presenter)

        # Add tabs
        self._tab_widget.addTab(self._actuation_view, "Quick Switch")
        self._tab_widget.addTab(self._configuration_view, "Configuration")

    def _create_help_button(self) -> None:
        """Create Help button in the tab widget corner."""
        # Create Help button with menu
        help_button = QToolButton()
        help_button.setText("HELP")
        help_button.setPopupMode(QToolButton.InstantPopup)
        help_button.setStyleSheet("""
            QToolButton {
                background-color: #4A90E2;
                color: white;
                border: 2px solid #357ABD;
                border-radius: 20px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13.5pt;
                min-width: 60px;
            }
            QToolButton:hover {
                background-color: #357ABD;
            }
            QToolButton:pressed {
                background-color: #2868A8;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        
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
        
        # About action
        about_action = QAction("About Audio Deck", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        help_button.setMenu(help_menu)
        
        # Add Help button to tab widget corner (top-right)
        self._tab_widget.setCornerWidget(help_button, Qt.TopRightCorner)
    
    def _get_resource_path(self, relative_path: str) -> Path:
        """Get absolute path to resource, works for dev and for PyInstaller.
        
        Args:
            relative_path: Relative path to resource file
            
        Returns:
            Absolute path to resource
        """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = Path(sys._MEIPASS)
        except AttributeError:
            # Running in development mode
            base_path = Path(__file__).parent.parent.parent.parent
        
        return base_path / relative_path

    def _show_documentation(self) -> None:
        """Show the documentation viewer dialog."""
        # Try to find README.md
        readme_path = self._get_resource_path("README.md")
        
        if not readme_path.exists():
            QMessageBox.warning(
                self,
                "Documentation Not Found",
                "README.md file not found. Please check the installation.",
            )
            return

        # Read README content
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to read README.md: {e}",
            )
            return

        # Create documentation dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Audio Deck Documentation")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create text browser for markdown display with slightly smaller font
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setStyleSheet("font-size: 11.7pt;")  # 1.3x base size instead of 1.5x
        text_browser.setMarkdown(readme_content)
        layout.addWidget(text_browser)
        
        # Add floating icon overlay in top-right corner
        icon_path = self._get_resource_path("AudioDeck.png")
        if icon_path.exists():
            icon_label = QLabel(dialog)
            pixmap = QPixmap(str(icon_path))
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setFixedSize(64, 64)
            icon_label.setStyleSheet("""
                background-color: rgba(42, 42, 42, 200);
                padding: 5px;
                border-radius: 5px;
            """)
            icon_label.setScaledContents(False)
            
            # Position icon after dialog is shown
            def position_icon():
                icon_label.move(dialog.width() - 84, 10)
                icon_label.raise_()
            
            # Use a timer to position after dialog is fully rendered
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, position_icon)

        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _show_dev_documentation(self) -> None:
        """Show the development documentation dialog with links to dev files."""
        # Create development documentation dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Development Documentation")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Create header with icon in top-right
        header_layout = QHBoxLayout()
        
        # Left side: Title and description
        left_layout = QVBoxLayout()
        
        title_label = QLabel("<h2>Development Documentation</h2>")
        title_label.setTextFormat(Qt.RichText)
        left_layout.addWidget(title_label)
        
        desc_label = QLabel("<p>Technical documentation for developers and advanced users.</p>")
        desc_label.setTextFormat(Qt.RichText)
        left_layout.addWidget(desc_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        
        # Right side: App icon
        icon_path = self._get_resource_path("AudioDeck.png")
        if icon_path.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path))
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignTop)
            header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Create text browser for documentation links
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(False)
        
        # Build documentation content with links
        dev_docs_content = """
<h3>Available Documentation</h3>

<p><b>📘 Development Quick Start</b><br>
<a href="file:///DEVELOPMENT_QUICKSTART.md">DEVELOPMENT_QUICKSTART.md</a><br>
Step-by-step guide for setting up the development environment and building the application.</p>

<p><b>💻 CLI Usage Reference</b><br>
<a href="file:///CLI_USAGE.md">CLI_USAGE.md</a><br>
Complete command-line interface reference for automation and scripting.</p>

<p><b>🏗️ Development README</b><br>
<a href="file:///DEVELOPMENT_README.md">DEVELOPMENT_README.md</a><br>
Technical architecture, design patterns, and development guidelines.</p>

<hr>

<p><i>Note: Click on any link above to open the documentation file. These files are located in the project root directory.</i></p>
"""
        
        text_browser.setHtml(dev_docs_content)
        
        # Handle link clicks to open files
        def handle_link_click(url):
            file_name = url.toString().replace("file:///", "")
            file_path = self._get_resource_path(file_name)
            
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Create a new dialog to show the file content
                    file_dialog = QDialog(dialog)
                    file_dialog.setWindowTitle(f"Audio Deck - {file_name}")
                    file_dialog.setMinimumSize(800, 600)
                    
                    file_layout = QVBoxLayout(file_dialog)
                    
                    file_browser = QTextBrowser()
                    file_browser.setOpenExternalLinks(True)
                    file_browser.setStyleSheet("font-size: 11.7pt;")
                    file_browser.setMarkdown(content)
                    file_layout.addWidget(file_browser)
                    
                    close_btn = QPushButton("Close")
                    close_btn.clicked.connect(file_dialog.accept)
                    file_layout.addWidget(close_btn)
                    
                    file_dialog.exec()
                    
                    # Restore the content after child dialog closes
                    text_browser.setHtml(dev_docs_content)
                except Exception as e:
                    QMessageBox.critical(
                        dialog,
                        "Error",
                        f"Failed to read {file_name}: {e}",
                    )
            else:
                QMessageBox.warning(
                    dialog,
                    "File Not Found",
                    f"{file_name} not found. Please check the installation.",
                )
        
        text_browser.anchorClicked.connect(handle_link_click)
        layout.addWidget(text_browser)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()

    def _show_license(self) -> None:
        """Show the License dialog."""
        # Try to find LICENSE file
        license_path = self._get_resource_path("LICENSE")
        
        if not license_path.exists():
            QMessageBox.warning(
                self,
                "License Not Found",
                "LICENSE file not found. Please check the installation.",
            )
            return

        # Read LICENSE content
        try:
            with open(license_path, "r", encoding="utf-8") as f:
                license_content = f.read()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to read LICENSE file: {e}",
            )
            return

        # Create license dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("License - GNU LGPL v3.0")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Create text browser for license display
        text_browser = QTextBrowser()
        text_browser.setPlainText(license_content)
        layout.addWidget(text_browser)

        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _show_about(self) -> None:
        """Show the About dialog."""
        # Create custom dialog instead of QMessageBox for better layout control
        dialog = QDialog(self)
        dialog.setWindowTitle("About Audio Deck")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create header layout with content on left, icon on right
        header_layout = QHBoxLayout()
        
        # Left side: Title, version, author, subtitle
        left_layout = QVBoxLayout()
        
        title_label = QLabel("<h2>Audio Deck</h2>")
        title_label.setTextFormat(Qt.RichText)
        left_layout.addWidget(title_label)
        
        version_label = QLabel("<p><b>Version:</b> 1.0.0</p>")
        version_label.setTextFormat(Qt.RichText)
        left_layout.addWidget(version_label)
        
        author_label = QLabel("<p><b>Author:</b> Oliver Ernster</p>")
        author_label.setTextFormat(Qt.RichText)
        left_layout.addWidget(author_label)
        
        subtitle_label = QLabel("<p>A professional audio device switcher for Windows<br>with Stream Deck integration.</p>")
        subtitle_label.setTextFormat(Qt.RichText)
        subtitle_label.setWordWrap(True)
        left_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        
        # Right side: App icon
        icon_path = self._get_resource_path("AudioDeck.png")
        if icon_path.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path))
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignTop)
            header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Add about text (features and license)
        about_text = """
<p><b>Features:</b></p>
<ul>
<li>Quick profile switching</li>
<li>Command-line interface for automation</li>
<li>Stream Deck integration</li>
<li>Profile management</li>
</ul>
<p><b>License:</b> GNU Lesser General Public License v3.0 (LGPL-3.0)</p>
<p>Copyright (C) 2024 Oliver Ernster</p>
<p>For more information, select <b>Help > View License</b> or <b>Help > View Documentation</b>.</p>"""
        
        text_label = QLabel(about_text)
        text_label.setTextFormat(Qt.RichText)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()

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
