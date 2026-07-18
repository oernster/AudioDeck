"""Tests that the real implementations satisfy the domain Protocols.

The Protocols are structural, so nothing fails at import time if an
implementation drifts. These checks make that drift a test failure instead of
a runtime AttributeError.
"""

from src.domain.interfaces import (
    IDeviceController,
    IDeviceRepository,
    IProfileRepository,
)
from src.infrastructure.persistence.json_profile_repository import (
    JsonProfileRepository,
)
from src.infrastructure.windows.windows_device_repository import (
    WindowsDeviceRepository,
)
from tests.conftest import FakeDeviceController


def _protocol_methods(protocol):
    """Return the public method names a Protocol declares."""
    return {
        name
        for name in vars(protocol)
        if not name.startswith("_") and callable(vars(protocol)[name])
    }


def test_device_repository_protocol_declares_methods():
    assert _protocol_methods(IDeviceRepository)


def test_windows_repository_satisfies_device_repository():
    missing = _protocol_methods(IDeviceRepository) - set(dir(WindowsDeviceRepository))
    assert missing == set()


def test_json_repository_satisfies_profile_repository():
    missing = _protocol_methods(IProfileRepository) - set(dir(JsonProfileRepository))
    assert missing == set()


def test_fake_controller_satisfies_device_controller():
    missing = _protocol_methods(IDeviceController) - set(dir(FakeDeviceController))
    assert missing == set()


def test_profile_repository_protocol_declares_methods():
    assert _protocol_methods(IProfileRepository)


def test_device_controller_protocol_declares_methods():
    assert _protocol_methods(IDeviceController)
