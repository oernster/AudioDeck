"""Themed, state-driven installer window for Audio Deck.

Reads the registry to discover any existing installation, compares it to the
bundled version and offers Install, Upgrade, Reinstall, Repair and Uninstall
accordingly.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from installer import constants as c
from installer import ops, registry
from installer.state import InstallerState, Operation
from installer.theme import stylesheet
from installer.worker import InstallerWorker

# Delay before the window closes itself after launching the application. Any
# value posts the close onto a later turn of the event loop, which is the point;
# a short one also leaves the "Starting..." line readable.
CLOSE_ON_NEXT_TURN_MS = 400

# Upper bound on joining the worker thread while the window closes. The worker
# has finished its work by then and only has to unwind, so this is a guard
# against hanging the close rather than a real wait. A QThread destroyed while
# still running takes the process with it, so the join is never unbounded and
# never skipped.
WORKER_JOIN_TIMEOUT_MS = 5000


def _app_icon() -> QIcon:
    """Return the application icon for the window."""
    return QIcon(str(c.resource_path(f"assets/{c.ICON_FILE_NAME}")))


class LicenceDialog(QDialog):
    """Read-only viewer for the application licence."""

    def __init__(self, parent: QWidget) -> None:
        """Build the licence dialog."""
        super().__init__(parent)
        self.setWindowTitle(f"{c.APP_DISPLAY_NAME} License")
        self.setMinimumSize(c.LICENCE_DIALOG_WIDTH, c.LICENCE_DIALOG_HEIGHT)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setLineWrapMode(QTextBrowser.WidgetWidth)
        browser.setPlainText(self._licence_text())
        layout.addWidget(browser)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_row.addWidget(close_button)
        layout.addLayout(close_row)

    @staticmethod
    def _licence_text() -> str:
        """Return the bundled licence text, falling back to a placeholder."""
        try:
            return c.resource_path("LICENSE").read_text(encoding="utf-8")
        except OSError:
            return "GNU Lesser General Public License v3.0 (LGPL-3.0)."


class InstallerWindow(QWidget):
    """Main installer window with a registry-driven state machine."""

    def __init__(self, preselect: Optional[Operation] = None) -> None:
        """Build the window.

        Args:
            preselect: Operation to trigger automatically on show (used by the
                registered uninstall command).
        """
        super().__init__()
        self._dark = True
        self._started = False
        self._preselect = preselect
        self._worker: Optional[InstallerWorker] = None
        self._state = InstallerState(
            bundled_version=ops.payload_version(),
            installed=registry.read_installed_info(),
        )

        self.setWindowTitle(f"{c.APP_DISPLAY_NAME} Setup")
        self.setWindowIcon(_app_icon())
        self.setMinimumSize(c.WINDOW_MIN_WIDTH, c.WINDOW_MIN_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            c.CONTENT_MARGIN_H,
            c.CONTENT_MARGIN_TOP,
            c.CONTENT_MARGIN_H,
            c.CONTENT_MARGIN_BOTTOM,
        )
        layout.setSpacing(c.CONTENT_SPACING)

        layout.addLayout(self._build_header())
        self._build_body(layout)
        layout.addStretch()
        self._build_actions(layout)
        self._build_progress(layout)

        self._action_widgets = [
            w
            for w in (
                self._left_button,
                self._right_button,
                self._uninstall_button,
                self._desktop_check,
                self._start_menu_check,
                self._launch_check,
                self._licence_button,
                self._theme_button,
            )
            if w is not None
        ]

    def showEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Focus the natural action, then trigger any preselected operation.

        Qt's default hands focus to the first widget in tab order, which is
        the Licence button in the header; the natural first choice is the
        primary operation (Install, Update, Repair), so the ring starts
        there instead.
        """
        super().showEvent(event)
        if not self._started:
            self._started = True
            primary = self._left_button or self._right_button
            if (
                primary is not None
                and primary.isEnabled()
                and primary.isVisibleTo(self)
            ):
                primary.setFocus(Qt.FocusReason.TabFocusReason)
        if self._preselect is not None:
            preselect, self._preselect = self._preselect, None
            if preselect in self._state.allowed_operations():
                self._confirm_and_start(preselect)

    def _build_header(self) -> QHBoxLayout:
        """Build the icon, title, version and right-side buttons."""
        header = QHBoxLayout()
        header.setSpacing(c.HEADER_SPACING)

        icon = _app_icon()
        if not icon.isNull():
            badge = QLabel()
            badge.setPixmap(icon.pixmap(QSize(c.ICON_BADGE_PX, c.ICON_BADGE_PX)))
            header.addWidget(badge, alignment=Qt.AlignVCenter)

        title = QLabel(f"{c.APP_DISPLAY_NAME} Setup")
        title.setObjectName("HeaderTitle")
        header.addWidget(title, alignment=Qt.AlignVCenter)

        version = QLabel(f"v{self._state.bundled_version}")
        version.setObjectName("HeaderVersion")
        header.addWidget(version, alignment=Qt.AlignBottom)

        header.addStretch()

        self._licence_button = QPushButton("License")
        self._licence_button.clicked.connect(self._show_licence)
        header.addWidget(self._licence_button)

        self._theme_button = QPushButton("Theme")
        self._theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(self._theme_button)
        return header

    def _build_body(self, layout: QVBoxLayout) -> None:
        """Build the subtitle, status line, install location and checkboxes."""
        subtitle = QLabel(c.SUBTITLE_TEXT)
        subtitle.setObjectName("SubTitle")
        subtitle.setAlignment(Qt.AlignHCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        status = QLabel(self._state.status_line())
        status.setObjectName("StatusLine")
        status.setAlignment(Qt.AlignHCenter)
        status.setWordWrap(True)
        layout.addWidget(status)

        location_label = QLabel("Install location:")
        layout.addWidget(location_label)
        location = QLineEdit(str(c.install_dir()))
        location.setReadOnly(True)
        layout.addWidget(location)

        self._desktop_check = QCheckBox("Create a Desktop shortcut")
        self._desktop_check.setChecked(True)
        layout.addWidget(self._desktop_check)

        self._start_menu_check = QCheckBox("Create a Start Menu shortcut")
        self._start_menu_check.setChecked(True)
        layout.addWidget(self._start_menu_check)

        self._launch_check = QCheckBox("Launch Audio Deck when finished")
        self._launch_check.setChecked(True)
        layout.addWidget(self._launch_check)

    def _build_actions(self, layout: QVBoxLayout) -> None:
        """Build the primary action buttons and the uninstall button."""
        primary = self._state.primary_operations()
        allowed = self._state.allowed_operations()

        action_row = QHBoxLayout()
        action_row.setSpacing(c.ACTION_SPACING)
        action_row.addStretch()

        self._left_button = self._make_primary(primary[0]) if primary else None
        self._right_button = (
            self._make_primary(primary[1]) if len(primary) > 1 else None
        )
        if self._left_button is not None:
            action_row.addWidget(self._left_button)
        if self._right_button is not None:
            action_row.addWidget(self._right_button)

        self._close_button = QPushButton("Close")
        self._close_button.setObjectName("PrimaryAction")
        self._close_button.clicked.connect(self.close)
        self._close_button.setVisible(False)
        action_row.addWidget(self._close_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        self._uninstall_button: Optional[QPushButton] = None
        if Operation.UNINSTALL in allowed:
            uninstall_row = QHBoxLayout()
            uninstall_row.addStretch()
            self._uninstall_button = QPushButton(Operation.UNINSTALL.value)
            self._uninstall_button.setObjectName("DangerAction")
            self._uninstall_button.clicked.connect(
                lambda: self._confirm_and_start(Operation.UNINSTALL)
            )
            uninstall_row.addWidget(self._uninstall_button)
            uninstall_row.addStretch()
            layout.addLayout(uninstall_row)

    def _make_primary(self, operation: Operation) -> QPushButton:
        """Create a primary action button bound to an operation."""
        button = QPushButton(operation.value)
        button.setObjectName("PrimaryAction")
        button.clicked.connect(lambda: self._confirm_and_start(operation))
        return button

    def _build_progress(self, layout: QVBoxLayout) -> None:
        """Build the progress bar and progress text."""
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._progress_text = QLabel("")
        self._progress_text.setObjectName("StatusLine")
        self._progress_text.setAlignment(Qt.AlignHCenter)
        self._progress_text.setWordWrap(True)
        layout.addWidget(self._progress_text)

    def _show_licence(self) -> None:
        """Open the licence dialog."""
        LicenceDialog(self).exec()

    def _toggle_theme(self) -> None:
        """Switch between the dark and light palettes."""
        self._dark = not self._dark
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(self._dark))

    def _confirm_and_start(self, operation: Operation) -> None:
        """Confirm destructive actions, then start the operation."""
        if operation == Operation.UNINSTALL:
            reply = QMessageBox.question(
                self,
                f"Uninstall {c.APP_DISPLAY_NAME}",
                f"Remove {c.APP_DISPLAY_NAME} and its shortcuts? Your saved "
                "profiles are not removed.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self._start(operation)

    def _start(self, operation: Operation) -> None:
        """Begin the chosen operation on the worker thread."""
        for widget in self._action_widgets:
            widget.setEnabled(False)
        self._progress.setVisible(True)

        self._worker = InstallerWorker(
            operation,
            create_desktop=self._desktop_check.isChecked(),
            create_start_menu=self._start_menu_check.isChecked(),
        )
        self._operation = operation
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, percent: int, message: str) -> None:
        """Update the progress bar and text."""
        self._progress.setValue(percent)
        self._progress_text.setText(message)

    def _on_finished(self, installed_exe: object) -> None:
        """Handle a successful operation, launching and closing when asked to."""
        launching = (
            installed_exe is not None
            and self._operation != Operation.UNINSTALL
            and self._launch_check.isChecked()
        )
        if launching:
            ops.launch(installed_exe)
            self._progress_text.setText(f"Starting {c.APP_DISPLAY_NAME}...")
            # Close on the next turn of the event loop rather than from inside
            # this callback. This slot is a bound method of a widget living on
            # the interface thread, so the worker has already handed control
            # back by the time it runs; posting the close keeps application
            # shutdown out of a signal emission altogether, which is the state
            # that hung the o7Debrief setup program twice on launch-on-finish.
            QTimer.singleShot(CLOSE_ON_NEXT_TURN_MS, self.close)
            return

        for button in (self._left_button, self._right_button, self._uninstall_button):
            if button is not None:
                button.setVisible(False)
        self._close_button.setVisible(True)
        self._close_button.setEnabled(True)

    def _on_failed(self, message: str) -> None:
        """Handle a failed operation."""
        self._progress_text.setText(f"Failed: {message}")
        for widget in self._action_widgets:
            widget.setEnabled(True)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        """Join the worker before the window goes away.

        The window can close while the worker is still unwinding, whether the
        user pressed Close or the launch-on-finish path posted it. Destroying a
        running QThread aborts the process, so the join is bounded and always
        runs.
        """
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.wait(WORKER_JOIN_TIMEOUT_MS)
        super().closeEvent(event)
