"""Main application entry point."""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

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
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Deck")
    app.setOrganizationName("AudioDeck")

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

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
