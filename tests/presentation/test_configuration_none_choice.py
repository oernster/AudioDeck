"""Choosing "(None)" for a device when editing a profile clears it (audit A-4).

Driven through the real ConfigurationView offscreen, the presenter, the use
cases and the JSON repository on a temporary path: the stored profile is read
back, because "Saved" on screen proves nothing about what was stored.
"""

import pytest

from src.application.use_cases.create_profile_use_case import CreateProfileUseCase
from src.application.use_cases.delete_profile_use_case import DeleteProfileUseCase
from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.update_profile_use_case import UpdateProfileUseCase
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from src.presentation.presenters.configuration_presenter import (
    ConfigurationPresenter,
)
from src.presentation.views.configuration_view import ConfigurationView
from tests.conftest import FakeMachine

# The editor's combo boxes list "(None)" first.
_NONE_INDEX = 0


@pytest.fixture
def editor(qtbot, profile_repo):
    machine = FakeMachine()
    machine.add("spk", DeviceType.OUTPUT)
    machine.add("mic", DeviceType.INPUT)
    presenter = ConfigurationPresenter(
        GetDevicesUseCase(CachingDeviceRepository(machine)),
        CreateProfileUseCase(profile_repo),
        UpdateProfileUseCase(profile_repo),
        DeleteProfileUseCase(profile_repo),
        GetProfilesUseCase(profile_repo),
    )
    CreateProfileUseCase(profile_repo).execute(
        "Call", output_device_id="spk", input_device_id="mic"
    )
    view = ConfigurationView(presenter)
    qtbot.addWidget(view)
    view.refresh()
    view._profile_list.setCurrentRow(0)
    view._on_edit_profile()
    return view


def test_none_for_the_output_clears_the_stored_output(editor, profile_repo):
    editor._output_combo.setCurrentIndex(_NONE_INDEX)
    editor._save_button.click()

    stored = profile_repo.get_all()[0]
    assert stored.output_device_id is None
    assert stored.input_device_id == "mic"


def test_none_for_the_input_clears_the_stored_input(editor, profile_repo):
    editor._input_combo.setCurrentIndex(_NONE_INDEX)
    editor._save_button.click()

    stored = profile_repo.get_all()[0]
    assert stored.output_device_id == "spk"
    assert stored.input_device_id is None
