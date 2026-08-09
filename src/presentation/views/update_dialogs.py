"""The update check's dialogs: the offer, the all-clear and the failure.

Kept beside help_dialogs rather than inside it: these are driven by presenter
signals where the help dialogs are driven by menu clicks, and the prompt is
the one dialog in the application that feeds a decision back (skip, download)
rather than only being read.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from src.presentation.presenters.update_presenter import UpdatePresenter

_TITLE = "Check for Updates"


def show_update_prompt(
    parent: QWidget,
    presenter: UpdatePresenter,
    latest: str,
    current: str,
    download_url: str,
    page_url: str,
) -> None:
    """Offer an available update: Download, Skip This Version or Later.

    Download opens the platform asset, falling back to the release page when
    no asset matched. Later simply closes; the next automatic check offers
    again. Skip persists the offered tag through the presenter.
    """
    box = QMessageBox(parent)
    box.setWindowTitle("Update Available")
    box.setText(f"Audio Deck {latest} is available.\nYou are running {current}.")
    download_button = box.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
    skip_button = box.addButton(
        "Skip This Version", QMessageBox.ButtonRole.DestructiveRole
    )
    box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
    box.exec()

    clicked = box.clickedButton()
    if clicked is download_button:
        presenter.open_download(download_url or page_url)
    elif clicked is skip_button:
        presenter.skip_version(latest)


def show_up_to_date(parent: QWidget) -> None:
    """Report that the running version is the newest published one."""
    QMessageBox.information(parent, _TITLE, "You are running the latest version.")


def show_check_failed(parent: QWidget) -> None:
    """Report that the manual check could not reach GitHub."""
    QMessageBox.warning(
        parent,
        _TITLE,
        "The update check could not reach GitHub. Please try again later.",
    )
