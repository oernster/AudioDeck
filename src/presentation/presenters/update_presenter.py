"""Presenter for the update check.

The check is one blocking HTTP call, so it runs through the injected runner
(the shared background-runner shape) and reports through Qt signals, which the
GUI thread receives over queued connections. The presenter is stateless
between checks: the automatic path reads the skipped tag from the settings
repository and the manual path ignores it by construction, so a release the
user declined stays reachable from the Help menu.
"""

from __future__ import annotations

from typing import Callable, Optional, Protocol

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices

from src.application.use_cases.check_for_updates_use_case import (
    CheckForUpdatesUseCase,
)
from src.domain.interfaces.update_settings_repository import (
    IUpdateSettingsRepository,
)


class IRunner(Protocol):
    """The slice of BackgroundRunner this presenter needs."""

    def submit(self, fn: Callable[..., None], *args: object) -> None:
        """Run fn(*args) off the GUI thread."""
        ...


class UpdatePresenter(QObject):
    """Presenter for the update check."""

    # (latest, current, download_url, page_url); empty strings when absent.
    update_available = Signal(str, str, str, str)
    up_to_date = Signal()
    check_failed = Signal()

    def __init__(
        self,
        check_for_updates_use_case: CheckForUpdatesUseCase,
        settings_repository: IUpdateSettingsRepository,
        runner: IRunner,
    ) -> None:
        """Initialize presenter.

        Args:
            check_for_updates_use_case: Use case running one check
            settings_repository: Store for the skipped-version choice
            runner: Executes the check off the GUI thread
        """
        super().__init__()
        self._check_for_updates_use_case = check_for_updates_use_case
        self._settings_repository = settings_repository
        self._runner = runner

    def check_automatically(self) -> None:
        """Run the launch or periodic check: silent on every non-offer outcome."""
        skipped = self._settings_repository.get_skipped_version()
        self._runner.submit(self._run_check, skipped, False)

    def check_manually(self) -> None:
        """Run the Help-menu check: reports every outcome and ignores the skip."""
        self._runner.submit(self._run_check, None, True)

    def skip_version(self, version: str) -> None:
        """Persist the offered tag so that version never prompts again.

        Args:
            version: The exact tag the prompt offered
        """
        self._settings_repository.set_skipped_version(version)

    def open_download(self, url: str) -> None:
        """Open a download or release-page URL in the default browser.

        Args:
            url: The URL the prompt resolved
        """
        QDesktopServices.openUrl(QUrl(url))

    def _run_check(self, skipped_version: Optional[str], manual: bool) -> None:
        """Run one check and emit the outcome. Runs on the worker thread."""
        try:
            status = self._check_for_updates_use_case.execute(skipped_version)
        except Exception:
            # The silent-failure contract: any error reads as unreachable.
            status = None
        if status is None:
            if manual:
                self.check_failed.emit()
            return
        if status.update_available:
            self.update_available.emit(
                status.latest,
                status.current,
                status.download_url or "",
                status.page_url or "",
            )
            return
        if manual:
            self.up_to_date.emit()
