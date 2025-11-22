"""Main application entry point.

Author: Oliver Ernster
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

from src.infrastructure.windows.device_enumerator import WindowsDeviceEnumerator
from src.infrastructure.windows.windows_device_controller import WindowsDeviceController
from src.infrastructure.windows.windows_device_repository import WindowsDeviceRepository
from src.infrastructure.persistence.json_profile_repository import JsonProfileRepository
from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.create_profile_use_case import CreateProfileUseCase
from src.application.use_cases.update_profile_use_case import UpdateProfileUseCase
from src.application.use_cases.delete_profile_use_case import DeleteProfileUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.presentation.views.main_window import MainWindow
from src.cli.argument_parser import parse_arguments
from src.cli.cli_handler import CLIHandler


def get_resource_path(relative_path: str) -> Path:
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
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


def create_splash_screen() -> QSplashScreen:
    """Create and configure the splash screen.
    
    Returns:
        Configured splash screen widget
    """
    # Create a custom splash screen with icon and text
    splash_pixmap = QPixmap(300, 200)
    splash_pixmap.fill(Qt.white)
    
    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    
    # Create a widget to hold the content
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setAlignment(Qt.AlignCenter)
    
    # Try to load and display the app icon
    icon_path = get_resource_path("AudioDeck.png")
    if icon_path.exists():
        icon_label = QLabel()
        pixmap = QPixmap(str(icon_path))
        scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(scaled_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(icon_label)
    
    # Add app name
    name_label = QLabel("Audio Deck")
    name_font = QFont()
    name_font.setPointSize(18)
    name_font.setBold(True)
    name_label.setFont(name_font)
    name_label.setAlignment(Qt.AlignCenter)
    content_layout.addWidget(name_label)
    
    # Add version
    version_label = QLabel("Version 1.0.0")
    version_font = QFont()
    version_font.setPointSize(10)
    version_label.setFont(version_font)
    version_label.setAlignment(Qt.AlignCenter)
    content_layout.addWidget(version_label)
    
    # Add author
    author_label = QLabel("by Oliver Ernster")
    author_font = QFont()
    author_font.setPointSize(9)
    author_label.setFont(author_font)
    author_label.setAlignment(Qt.AlignCenter)
    content_layout.addWidget(author_label)
    
    # Add loading message
    loading_label = QLabel("Loading...")
    loading_font = QFont()
    loading_font.setPointSize(9)
    loading_font.setItalic(True)
    loading_label.setFont(loading_font)
    loading_label.setAlignment(Qt.AlignCenter)
    loading_label.setStyleSheet("color: #666;")
    content_layout.addWidget(loading_label)
    
    # Render the widget onto the splash screen pixmap
    content_widget.setGeometry(0, 0, 300, 200)
    content_widget.render(splash_pixmap)
    splash.setPixmap(splash_pixmap)
    
    return splash


def get_profiles_path() -> Path:
    """Get the path for storing profiles.

    Returns:
        Path to profiles directory
    """
    # Store profiles in user's AppData/Local directory
    app_data = Path.home() / "AppData" / "Local" / "AudioDeck"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "profiles.json"


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Check if CLI mode is requested
    if args.is_cli_mode:
        # Run in CLI mode (headless)
        cli_handler = CLIHandler(get_profiles_path())
        return cli_handler.handle(args)

    # Run in GUI mode
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Deck")
    app.setOrganizationName("AudioDeck")
    
    # Create and show splash screen
    splash = create_splash_screen()
    splash.show()
    app.processEvents()  # Process events to show splash immediately
    
    # Set global font size to 1.5x larger (base font size is typically 9pt, so 13.5pt)
    # Add graduated purple background to tab buttons only
    app.setStyleSheet("""
        * {
            font-size: 13.5pt;
        }
        QLabel {
            font-size: 13.5pt;
        }
        QPushButton {
            font-size: 13.5pt;
            padding: 6px 12px;
        }
        QLineEdit, QComboBox, QListWidget {
            font-size: 13.5pt;
            padding: 4px;
        }
        QTabWidget::pane {
            font-size: 13.5pt;
        }
        QTabBar::tab {
            font-size: 13.5pt;
            padding: 8px 16px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #B8A0D0, stop:1 #8B6EAD);
            color: white;
            border: 1px solid #5A3D7F;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #7B5CAA, stop:1 #4A2C6A);
            font-weight: bold;
        }
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #C8B0E0, stop:1 #9B7EBD);
        }
        QGroupBox {
            font-size: 13.5pt;
            font-weight: bold;
        }
        QMessageBox {
            font-size: 13.5pt;
        }
    """)

    # Infrastructure layer - dependency injection
    device_enumerator = WindowsDeviceEnumerator()
    device_controller = WindowsDeviceController()
    device_repository = WindowsDeviceRepository(device_enumerator)
    profile_repository = JsonProfileRepository(get_profiles_path())

    # Application layer - use cases
    get_devices_use_case = GetDevicesUseCase(device_repository)
    create_profile_use_case = CreateProfileUseCase(profile_repository)
    update_profile_use_case = UpdateProfileUseCase(profile_repository)
    delete_profile_use_case = DeleteProfileUseCase(profile_repository)
    get_profiles_use_case = GetProfilesUseCase(profile_repository)
    switch_profile_use_case = SwitchProfileUseCase(
        profile_repository, device_repository, device_controller
    )

    # Presentation layer - presenters
    configuration_presenter = ConfigurationPresenter(
        get_devices_use_case,
        create_profile_use_case,
        update_profile_use_case,
        delete_profile_use_case,
        get_profiles_use_case,
    )
    actuation_presenter = ActuationPresenter(
        get_devices_use_case, get_profiles_use_case, switch_profile_use_case
    )

    # Create and show main window
    main_window = MainWindow(configuration_presenter, actuation_presenter)
    main_window.show_and_raise()
    
    # Close splash screen after main window is shown
    splash.finish(main_window)

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
