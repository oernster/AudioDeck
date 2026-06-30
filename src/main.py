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
from src.presentation.notifiers.device_change_notifier import (
    WindowsDeviceChangeNotifier,
)
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
    """Create and configure a themed splash screen.

    A rounded card with the app's purple gradient, the icon, the version and the
    author. The version is read from the single source of truth (the VERSION
    file, via __version__).

    Returns:
        Configured splash screen widget
    """
    from PySide6.QtGui import (
        QPainter,
        QColor,
        QFontMetrics,
        QLinearGradient,
        QPainterPath,
        QPen,
    )

    # Geometry and spacing (named, no magic numbers).
    WIDTH = 440
    HEIGHT = 300
    CORNER_RADIUS = 18
    BORDER_WIDTH = 2
    ICON_SIZE = 112
    ICON_TITLE_GAP = 16
    TITLE_VERSION_GAP = 8
    VERSION_AUTHOR_GAP = 4
    BOTTOM_MARGIN = 22

    # Palette: Audio Deck signature purple, fading to dark.
    color_top = QColor("#4a2c6a")
    color_bottom = QColor("#262430")
    color_border = QColor("#7b5caa")
    color_title = QColor("#ffffff")
    color_version = QColor("#d8ccea")
    color_author = QColor("#b0a4c4")
    color_loading = QColor("#8a7ea3")

    splash_pixmap = QPixmap(WIDTH, HEIGHT)
    splash_pixmap.fill(Qt.transparent)

    painter = QPainter(splash_pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Rounded gradient card.
    inset = BORDER_WIDTH
    card = QPainterPath()
    card.addRoundedRect(
        inset,
        inset,
        WIDTH - 2 * inset,
        HEIGHT - 2 * inset,
        CORNER_RADIUS,
        CORNER_RADIUS,
    )
    gradient = QLinearGradient(0, 0, 0, HEIGHT)
    gradient.setColorAt(0, color_top)
    gradient.setColorAt(1, color_bottom)
    painter.fillPath(card, gradient)
    painter.setPen(QPen(color_border, BORDER_WIDTH))
    painter.drawPath(card)

    # Fonts.
    font_title = QFont()
    font_title.setPointSize(22)
    font_title.setBold(True)
    font_version = QFont()
    font_version.setPointSize(11)
    font_author = QFont()
    font_author.setPointSize(10)
    font_loading = QFont()
    font_loading.setPointSize(9)

    fm_title = QFontMetrics(font_title)
    fm_version = QFontMetrics(font_version)
    fm_author = QFontMetrics(font_author)

    icon_path = get_resource_path("assets/audiodeck_icon_256.png")
    has_icon = icon_path.exists()
    icon_block = ICON_SIZE + ICON_TITLE_GAP if has_icon else 0

    block_height = (
        icon_block
        + fm_title.height()
        + TITLE_VERSION_GAP
        + fm_version.height()
        + VERSION_AUTHOR_GAP
        + fm_author.height()
    )
    y = (HEIGHT - block_height) // 2

    if has_icon:
        icon_pixmap = QPixmap(str(icon_path)).scaled(
            ICON_SIZE, ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        painter.drawPixmap((WIDTH - icon_pixmap.width()) // 2, y, icon_pixmap)
        y += icon_pixmap.height() + ICON_TITLE_GAP

    def draw_centered(text: str, font: QFont, color: QColor, gap: int) -> None:
        nonlocal y
        painter.setFont(font)
        painter.setPen(color)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        painter.drawText((WIDTH - text_width) // 2, y + metrics.ascent(), text)
        y += metrics.height() + gap

    draw_centered("Audio Deck", font_title, color_title, TITLE_VERSION_GAP)
    draw_centered(
        f"Version {__version__}", font_version, color_version, VERSION_AUTHOR_GAP
    )
    draw_centered("by Oliver Ernster", font_author, color_author, 0)

    # Loading line pinned near the bottom edge.
    painter.setFont(font_loading)
    painter.setPen(color_loading)
    fm_loading = QFontMetrics(font_loading)
    loading_text = "Loading..."
    loading_width = fm_loading.horizontalAdvance(loading_text)
    painter.drawText(
        (WIDTH - loading_width) // 2,
        HEIGHT - BOTTOM_MARGIN,
        loading_text,
    )

    painter.end()

    splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pixmap.mask())
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
        cli_handler = CLIHandler.from_profiles_path(get_profiles_path())
        return cli_handler.handle(args)

    # Run in GUI mode
    # Set Windows taskbar icon (must be done before creating QApplication)
    if sys.platform == "win32":
        # Set application user model ID to ensure proper taskbar icon display
        myappid = "OliverErnster.AudioDeck.1.0"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Deck")
    app.setOrganizationName("AudioDeck")

    # Set application icon for Windows taskbar
    icon_path = get_resource_path("assets/audiodeck.ico")
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

    # React to device add/remove/change events instantly (the periodic timer
    # in the actuation view remains as a fallback).
    device_change_notifier = WindowsDeviceChangeNotifier(
        actuation_presenter.on_devices_changed
    )
    device_change_notifier.install(app)

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
