"""Tests for the update presenter: the three outcomes and the skip contract.

The runner fake executes submitted work immediately on the calling thread, so
signal emission order is deterministic; the threading itself belongs to
BackgroundRunner and is covered by its own tests.
"""

from PySide6.QtCore import QUrl

from src.application.dtos.update_status import UpdateStatus
from src.presentation.presenters.update_presenter import UpdatePresenter


class ImmediateRunner:
    """Runs submitted callables synchronously."""

    def submit(self, fn, *args):
        fn(*args)


class FakeCheckForUpdatesUseCase:
    """Returns a configured status, or raises."""

    def __init__(self, status=None, error=None):
        self._status = status
        self._error = error
        self.calls = []

    def execute(self, skipped_version=None):
        self.calls.append(skipped_version)
        if self._error is not None:
            raise self._error
        return self._status


class FakeUpdateSettings:
    """In-memory stand-in for the settings repository."""

    def __init__(self, skipped=None):
        self.skipped = skipped

    def get_skipped_version(self):
        return self.skipped

    def set_skipped_version(self, version):
        self.skipped = version


def status(available=True, download_url="https://x/setup.exe", page_url="https://x/r"):
    return UpdateStatus(
        current="1.4.0",
        latest="v1.5.0",
        update_available=available,
        download_url=download_url,
        page_url=page_url,
    )


def presenter_with(use_case, settings=None):
    return UpdatePresenter(
        use_case, settings or FakeUpdateSettings(), ImmediateRunner()
    )


def collect_args(signal):
    received = []
    signal.connect(lambda *args: received.append(args))
    return received


def collect(signal):
    received = []
    signal.connect(lambda: received.append(True))
    return received


class TestAutomaticCheck:
    def test_update_available_prompts(self, qtbot):
        use_case = FakeCheckForUpdatesUseCase(status())
        presenter = presenter_with(use_case)
        offers = collect_args(presenter.update_available)
        presenter.check_automatically()
        assert offers == [("v1.5.0", "1.4.0", "https://x/setup.exe", "https://x/r")]
        assert use_case.calls == [None]

    def test_skipped_tag_is_passed_through(self, qtbot):
        use_case = FakeCheckForUpdatesUseCase(status(available=False))
        presenter = presenter_with(use_case, FakeUpdateSettings("v1.5.0"))
        presenter.check_automatically()
        assert use_case.calls == ["v1.5.0"]

    def test_up_to_date_is_silent(self, qtbot):
        presenter = presenter_with(FakeCheckForUpdatesUseCase(status(available=False)))
        quiet = collect(presenter.up_to_date)
        failed = collect(presenter.check_failed)
        presenter.check_automatically()
        assert quiet == []
        assert failed == []

    def test_unreachable_is_silent(self, qtbot):
        presenter = presenter_with(FakeCheckForUpdatesUseCase(None))
        failed = collect(presenter.check_failed)
        presenter.check_automatically()
        assert failed == []

    def test_missing_urls_become_empty_strings(self, qtbot):
        use_case = FakeCheckForUpdatesUseCase(status(download_url=None, page_url=None))
        presenter = presenter_with(use_case)
        offers = collect_args(presenter.update_available)
        presenter.check_automatically()
        assert offers == [("v1.5.0", "1.4.0", "", "")]


class TestManualCheck:
    def test_manual_ignores_the_skip_by_construction(self, qtbot):
        use_case = FakeCheckForUpdatesUseCase(status())
        presenter = presenter_with(use_case, FakeUpdateSettings("v1.5.0"))
        offers = collect_args(presenter.update_available)
        presenter.check_manually()
        assert use_case.calls == [None]
        assert len(offers) == 1

    def test_up_to_date_is_reported(self, qtbot):
        presenter = presenter_with(FakeCheckForUpdatesUseCase(status(available=False)))
        quiet = collect(presenter.up_to_date)
        presenter.check_manually()
        assert quiet == [True]

    def test_unreachable_is_reported(self, qtbot):
        presenter = presenter_with(FakeCheckForUpdatesUseCase(None))
        failed = collect(presenter.check_failed)
        presenter.check_manually()
        assert failed == [True]

    def test_use_case_exception_reads_as_unreachable(self, qtbot):
        presenter = presenter_with(
            FakeCheckForUpdatesUseCase(error=RuntimeError("boom"))
        )
        failed = collect(presenter.check_failed)
        presenter.check_manually()
        assert failed == [True]


class TestChoices:
    def test_skip_version_persists_the_tag(self, qtbot):
        settings = FakeUpdateSettings()
        presenter = presenter_with(FakeCheckForUpdatesUseCase(), settings)
        presenter.skip_version("v1.5.0")
        assert settings.skipped == "v1.5.0"

    def test_open_download_opens_the_url(self, qtbot, monkeypatch):
        opened = []
        monkeypatch.setattr(
            "src.presentation.presenters.update_presenter.QDesktopServices.openUrl",
            lambda url: opened.append(url) or True,
        )
        presenter = presenter_with(FakeCheckForUpdatesUseCase())
        presenter.open_download("https://x/setup.exe")
        assert opened == [QUrl("https://x/setup.exe")]
