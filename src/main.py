"""Main application entry point.

Author: Oliver Ernster
"""

import sys
from pathlib import Path
import ctypes

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import __version__

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
    from PySide6.QtGui import QPainter, QColor

    W, H = 300, 300
    ICON_SIZE = 100
    GAP = 8

    splash_pixmap = QPixmap(W, H)
    splash_pixmap.fill(Qt.white)

    painter = QPainter(splash_pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Measure text heights to compute total block height
    font_name = QFont()
    font_name.setPointSize(18)
    font_name.setBold(True)

    font_small = QFont()
    font_small.setPointSize(10)

    font_tiny = QFont()
    font_tiny.setPointSize(9)

    from PySide6.QtGui import QFontMetrics
    fm_name = QFontMetrics(font_name)
    fm_small = QFontMetrics(font_small)
    fm_tiny = QFontMetrics(font_tiny)

    lh_name = fm_name.height()
    lh_small = fm_small.height()
    lh_tiny = fm_tiny.height()

    icon_path = get_resource_path("AudioDeck.png")
    has_icon = icon_path.exists()
    icon_block = ICON_SIZE + GAP if has_icon else 0

    total_h = icon_block + lh_name + GAP + lh_small + GAP + lh_tiny + GAP + lh_tiny
    y = (H - total_h) // 2

    # Draw icon
    if has_icon:
        icon_pixmap = QPixmap(str(icon_path)).scaled(
            ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (W - icon_pixmap.width()) // 2
        painter.drawPixmap(x, y, icon_pixmap)
        y += icon_pixmap.height() + GAP

    def draw_centered(text, font, color=QColor(0, 0, 0)):
        nonlocal y
        painter.setFont(font)
        painter.setPen(color)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        painter.drawText((W - tw) // 2, y + fm.ascent(), text)
        y += fm.height() + GAP

    draw_centered("Audio Deck", font_name)
    draw_centered(f"Version {__version__}", font_small)
    draw_centered("by Oliver Ernster", font_tiny)
    draw_centered("Loading...", font_tiny, QColor(102, 102, 102))

    painter.end()

    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
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


def _set_windows_taskbar_icon(window: "QMainWindow", ico_path: Path) -> None:
    """Set Windows taskbar icon via WM_SETICON for reliable display.

    Qt's setWindowIcon does not always propagate to the Windows taskbar
    when a custom AppUserModelID is active. Sending WM_SETICON directly
    to the native window handle bypasses that limitation.
    """
    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x0010

    user32 = ctypes.windll.user32
    ico_str = str(ico_path)
    hwnd = int(window.winId())

    hicon_big = user32.LoadImageW(None, ico_str, IMAGE_ICON, 256, 256, LR_LOADFROMFILE)
    hicon_small = user32.LoadImageW(None, ico_str, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

    if hicon_big:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
    if hicon_small:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)


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
    # Set Windows taskbar icon (must be done before creating QApplication)
    if sys.platform == "win32":
        # Set application user model ID to ensure proper taskbar icon display
        myappid = 'OliverErnster.AudioDeck.1.0'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Deck")
    app.setOrganizationName("AudioDeck")
    
    # Set application icon for Windows taskbar
    icon_path = get_resource_path("AudioDeck.ico")
    if icon_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))
    
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

    # Explicitly set Windows taskbar icon via WM_SETICON after window is visible.
    # Qt + AUMID does not reliably propagate setWindowIcon to the taskbar button,
    # so we call the Windows API directly.
    if sys.platform == "win32" and icon_path.exists():
        _set_windows_taskbar_icon(main_window, icon_path)

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
