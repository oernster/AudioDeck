"""Tests for single-instance enforcement (over fake Win32 APIs)."""

from src.infrastructure.windows.single_instance import (
    ERROR_ALREADY_EXISTS,
    SingleInstanceGuard,
    activate_existing_window,
)

MUTEX_NAME = "Local\\AudioDeck-Test"
WINDOW_TITLE = "Audio Deck"

# Any non-zero handle stands in for a real Win32 handle.
A_HANDLE = 42
# Win32 reports this when a call succeeded without a pre-existing object.
ERROR_SUCCESS = 0


class FakeMutexApi:
    """Records calls and returns scripted results."""

    def __init__(self, handle=A_HANDLE, error=ERROR_SUCCESS):
        self.handle = handle
        self.error = error
        self.created = []
        self.closed = []

    def create_mutex(self, name):
        self.created.append(name)
        return self.handle

    def last_error(self):
        return self.error

    def close_handle(self, handle):
        self.closed.append(handle)


class FakeWindowApi:
    """Records calls and returns scripted results."""

    def __init__(self, handle=A_HANDLE, minimized=False, foreground=True):
        self.handle = handle
        self.minimized = minimized
        self.foreground = foreground
        self.searched = []
        self.restored = []
        self.fronted = []

    def find_window(self, title):
        self.searched.append(title)
        return self.handle

    def is_minimized(self, handle):
        return self.minimized

    def restore(self, handle):
        self.restored.append(handle)

    def bring_to_front(self, handle):
        self.fronted.append(handle)
        return self.foreground


def test_first_instance_acquires():
    api = FakeMutexApi()
    assert SingleInstanceGuard(MUTEX_NAME, api).acquire() is True
    assert api.created == [MUTEX_NAME]


def test_first_instance_keeps_the_handle_open():
    api = FakeMutexApi()
    SingleInstanceGuard(MUTEX_NAME, api).acquire()
    assert api.closed == []


def test_second_instance_is_refused():
    api = FakeMutexApi(error=ERROR_ALREADY_EXISTS)
    assert SingleInstanceGuard(MUTEX_NAME, api).acquire() is False


def test_second_instance_closes_its_handle():
    api = FakeMutexApi(error=ERROR_ALREADY_EXISTS)
    SingleInstanceGuard(MUTEX_NAME, api).acquire()
    assert api.closed == [A_HANDLE]


def test_guard_fails_open_when_the_mutex_cannot_be_created():
    api = FakeMutexApi(handle=0, error=ERROR_ALREADY_EXISTS)
    assert SingleInstanceGuard(MUTEX_NAME, api).acquire() is True


def test_failed_creation_closes_nothing():
    api = FakeMutexApi(handle=0)
    SingleInstanceGuard(MUTEX_NAME, api).acquire()
    assert api.closed == []


def test_release_closes_the_held_handle():
    api = FakeMutexApi()
    guard = SingleInstanceGuard(MUTEX_NAME, api)
    guard.acquire()
    guard.release()
    assert api.closed == [A_HANDLE]


def test_release_is_idempotent():
    api = FakeMutexApi()
    guard = SingleInstanceGuard(MUTEX_NAME, api)
    guard.acquire()
    guard.release()
    guard.release()
    assert api.closed == [A_HANDLE]


def test_release_without_acquire_does_nothing():
    api = FakeMutexApi()
    SingleInstanceGuard(MUTEX_NAME, api).release()
    assert api.closed == []


def test_released_name_can_be_acquired_again():
    api = FakeMutexApi()
    guard = SingleInstanceGuard(MUTEX_NAME, api)
    guard.acquire()
    guard.release()
    assert guard.acquire() is True


def test_activate_finds_window_by_title():
    api = FakeWindowApi()
    assert activate_existing_window(WINDOW_TITLE, api) is True
    assert api.searched == [WINDOW_TITLE]


def test_activate_brings_window_to_front():
    api = FakeWindowApi()
    activate_existing_window(WINDOW_TITLE, api)
    assert api.fronted == [A_HANDLE]


def test_activate_restores_a_minimized_window():
    api = FakeWindowApi(minimized=True)
    activate_existing_window(WINDOW_TITLE, api)
    assert api.restored == [A_HANDLE]


def test_activate_leaves_a_visible_window_alone():
    api = FakeWindowApi(minimized=False)
    activate_existing_window(WINDOW_TITLE, api)
    assert api.restored == []


def test_activate_reports_failure_when_no_window_found():
    api = FakeWindowApi(handle=0)
    assert activate_existing_window(WINDOW_TITLE, api) is False


def test_activate_does_not_touch_a_missing_window():
    api = FakeWindowApi(handle=0)
    activate_existing_window(WINDOW_TITLE, api)
    assert api.fronted == []


def test_activate_reports_failure_when_foreground_is_refused():
    api = FakeWindowApi(foreground=False)
    assert activate_existing_window(WINDOW_TITLE, api) is False
