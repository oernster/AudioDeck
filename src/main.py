"""Main application entry point.

Author: Oliver Ernster
"""

import os
import sys
from pathlib import Path
import ctypes

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow

from src.infrastructure.backend_factory import (
    create_device_backend,
    create_single_instance,
)
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from src.infrastructure.persistence.json_profile_repository import JsonProfileRepository
from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.check_for_updates_use_case import (
    CheckForUpdatesUseCase,
    platform_key_for,
)
from src.infrastructure.updates.github_release_source import GitHubReleaseSource
from src.infrastructure.persistence.json_update_settings_repository import (
    JsonUpdateSettingsRepository,
)
from src.presentation.presenters.update_presenter import UpdatePresenter
from src.presentation.workers.background_runner import BackgroundRunner
from src.version import __version__
from src.application.use_cases.create_profile_use_case import CreateProfileUseCase
from src.application.use_cases.update_profile_use_case import UpdateProfileUseCase
from src.application.use_cases.delete_profile_use_case import DeleteProfileUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.presentation.views.main_window import MainWindow, WINDOW_TITLE
from src.presentation.views.resource_paths import resource_path
from src.presentation.views.splash_screen import create_splash_screen
from src.cli.argument_parser import parse_arguments
from src.cli.cli_handler import CLIHandler

# Dark palette colours (Catppuccin Mocha, matching the project site). Keyed
# by Qt palette role name so the applying loop stays data-driven.
_DARK_WINDOW = "#1e1e2e"
_DARK_SURFACE = "#313244"
_DARK_FIELD = "#181825"
_DARK_TEXT = "#cdd6f4"
_DARK_MUTED_TEXT = "#6c7086"
_DARK_ACCENT = "#7b5caa"
_DARK_LINK = "#89b4fa"


def _apply_dark_theme(app: "QApplication") -> None:
    """Force the Fusion style with a dark palette.

    Args:
        app: The QApplication to restyle.
    """
    from PySide6.QtGui import QColor, QPalette

    app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: _DARK_WINDOW,
        QPalette.ColorRole.WindowText: _DARK_TEXT,
        QPalette.ColorRole.Base: _DARK_FIELD,
        QPalette.ColorRole.AlternateBase: _DARK_SURFACE,
        QPalette.ColorRole.Text: _DARK_TEXT,
        QPalette.ColorRole.Button: _DARK_SURFACE,
        QPalette.ColorRole.ButtonText: _DARK_TEXT,
        QPalette.ColorRole.ToolTipBase: _DARK_SURFACE,
        QPalette.ColorRole.ToolTipText: _DARK_TEXT,
        QPalette.ColorRole.PlaceholderText: _DARK_MUTED_TEXT,
        QPalette.ColorRole.Highlight: _DARK_ACCENT,
        QPalette.ColorRole.HighlightedText: _DARK_TEXT,
        QPalette.ColorRole.BrightText: _DARK_TEXT,
        QPalette.ColorRole.Link: _DARK_LINK,
    }
    for role, colour in roles.items():
        palette.setColor(role, QColor(colour))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(_DARK_MUTED_TEXT),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(_DARK_MUTED_TEXT),
    )
    app.setPalette(palette)


def get_profiles_path() -> Path:
    """Get the path for storing profiles, in the platform's app-data home.

    Returns:
        Path to profiles file
    """
    if sys.platform == "win32":
        app_data = Path.home() / "AppData" / "Local" / "AudioDeck"
    elif sys.platform == "darwin":
        app_data = Path.home() / "Library" / "Application Support" / "AudioDeck"
    else:
        xdg_data_home = os.environ.get(
            "XDG_DATA_HOME", str(Path.home() / ".local" / "share")
        )
        app_data = Path(xdg_data_home) / "audiodeck"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "profiles.json"


def get_update_settings_path() -> Path:
    """Get the path for the update check's settings, beside the profiles.

    Returns:
        Path to the update settings JSON file
    """
    return get_profiles_path().parent / "update_settings.json"


def _set_windows_taskbar_icon(window: QMainWindow, ico_path: Path) -> None:
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

    # Run in GUI mode. Only one GUI instance may run per logon session; the
    # CLI path above is deliberately left unguarded so a Stream Deck button
    # can switch profiles while the window is open.
    single = create_single_instance(sys.platform)
    if not single.guard.acquire():
        # Another instance owns the lock. Raise its window where the platform
        # allows it, rather than exiting silently, which would look like a
        # failed launch.
        single.activate(WINDOW_TITLE)
        return 0

    # Set Windows taskbar icon (must be done before creating QApplication)
    if sys.platform == "win32":
        # Set application user model ID to ensure proper taskbar icon display
        myappid = "OliverErnster.AudioDeck.1.0"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Deck")
    app.setOrganizationName("AudioDeck")

    # On Linux (in particular inside the Flatpak sandbox) Qt has no desktop
    # theme integration and falls back to a light palette. Windows and macOS
    # follow the system theme, so only Linux gets the explicit dark palette.
    if sys.platform.startswith("linux"):
        _apply_dark_theme(app)

    # Set application icon for Windows taskbar
    icon_path = resource_path("assets/audiodeck.ico")
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
    backend = create_device_backend(sys.platform)
    device_repository = CachingDeviceRepository(backend.enumerator)
    profile_repository = JsonProfileRepository(get_profiles_path())

    # Application layer - use cases
    get_devices_use_case = GetDevicesUseCase(device_repository)
    create_profile_use_case = CreateProfileUseCase(profile_repository)
    update_profile_use_case = UpdateProfileUseCase(profile_repository)
    delete_profile_use_case = DeleteProfileUseCase(profile_repository)
    get_profiles_use_case = GetProfilesUseCase(profile_repository)
    switch_profile_use_case = SwitchProfileUseCase(
        profile_repository, device_repository, backend.controller
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

    # Update check: the use case over the GitHub adapter, the skip stored
    # beside the profiles, the blocking call run off the GUI thread.
    update_runner = BackgroundRunner()
    update_presenter = UpdatePresenter(
        CheckForUpdatesUseCase(
            GitHubReleaseSource(), __version__, platform_key_for(sys.platform)
        ),
        JsonUpdateSettingsRepository(get_update_settings_path()),
        update_runner,
    )

    # Create and show main window (it installs the native device-change notifier)
    main_window = MainWindow(
        configuration_presenter, actuation_presenter, update_presenter
    )
    main_window.show_and_raise()

    # Close splash screen after main window is shown
    splash.finish(main_window)

    # Explicitly set Windows taskbar icon via WM_SETICON after window is visible.
    # Qt + AUMID does not reliably propagate setWindowIcon to the taskbar button,
    # so we call the Windows API directly.
    if sys.platform == "win32" and icon_path.exists():
        _set_windows_taskbar_icon(main_window, icon_path)

    # Run application
    try:
        return app.exec()
    finally:
        update_runner.stop()
        single.guard.release()


if __name__ == "__main__":
    sys.exit(main())
