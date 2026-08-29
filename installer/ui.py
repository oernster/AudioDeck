"""The Audio Deck setup program.

The house shell: a header that never changes, a body showing one screen at a
time and a footer of actions, with a rule between each. The body is centred
rather than packed to the top, so a short screen sits in the middle of the
window instead of leaving a hole above the buttons.

What setup is FOR is decided once, from what the machine already holds: a first
install, an update, a downgrade, a matching version to manage or a removal.
That reading picks the screen, its heading, the versions it shows and the
actions under it, so no two of those can contradict each other.

The footer belongs to the screen rather than to the window; an operation moves
to the progress screen rather than disabling the options where they stand. A screen with nothing safe to offer, the one that is working, offers
nothing at all.

Every step is written to a log, because the worst installer failures are the
ones that never raise.

Author: Oliver Ernster
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from installer import appearance, existing, ops, screens, shell, wording
from installer import constants as c
from installer.footer import DANGER, PRIMARY, Action, Footer
from installer.licence_dialog import LicenceDialog
from installer.performing import WORKER_JOIN_TIMEOUT_MS, Performing
from installer.route import Route, route_for
from installer.steplog import StepLog


def _app_icon() -> QIcon:
    """Return the application icon for the window."""
    return QIcon(str(c.resource_path(f"assets/{c.ICONS_DIR_NAME}/{c.ICON_FILE_NAME}")))


class InstallerWindow(Performing, QWidget):
    """Install, repair or remove Audio Deck, per user, without admin rights.

    The setup program is a Qt application, so it carries ONE licence, the
    LGPL-3.0 that Qt asks for. Audio Deck's own split into a backend licence
    and an interface licence belongs to Audio Deck, not to the program that
    installs it.
    """

    def __init__(self, uninstalling: bool = False) -> None:
        """Build the window on one reading of the machine.

        Args:
            uninstalling: Whether removal was asked for on the command line,
                which is how the Apps list runs this program.
        """
        super().__init__()
        self.log = StepLog()
        self.version = ops.payload_version()
        self.here = existing.look()
        # The route never becomes UNINSTALL: removal is a screen reachable from
        # every other one, so the screen behind it stays the one to come back
        # to.
        self.route = route_for(self.here.version, self.version, uninstalling=False)
        self._uninstalling = uninstalling
        # Whether removal is the only reason this program was opened, which is
        # how the Apps list runs it. Cancelling then has nothing to go back to.
        self._opened_to_remove = uninstalling
        self._dark = True
        self._shown = False
        self._worker = None

        self.setObjectName("Shell")
        self.setWindowTitle(f"{c.APP_DISPLAY_NAME} Setup")
        self.setWindowIcon(_app_icon())
        self._build_widgets()
        self._build()
        appearance.apply(self._dark, self._theme_button)
        self._show_current()
        self.log.write(f"setup started, version {self.version}, {self.route.value}")

    # --------------------------------------------------------------- controls

    def _build_widgets(self) -> None:
        """Create every control the screens and the footer share."""
        self._licence_button = QPushButton("License", self)
        self._licence_button.clicked.connect(self._show_licence)
        self._theme_button = QPushButton(self)
        self._theme_button.setObjectName("ThemeToggle")
        self._theme_button.setIconSize(QSize(c.TOGGLE_ICON_PX, c.TOGGLE_ICON_PX))
        self._theme_button.clicked.connect(self._toggle_theme)

        self._desktop = QCheckBox(wording.DESKTOP_LABEL, self)
        self._start_menu = QCheckBox(wording.START_MENU_LABEL, self)
        self._launch = QCheckBox(wording.LAUNCH_LABEL, self)
        self._set_choices()

        self._progress = QProgressBar(self)
        self._progress.setRange(0, ops.PCT_DONE)
        self._progress.setValue(0)
        self._progress_title = shell.label(self, "", "Heading")
        self._progress_status = shell.label(self, "", "Status")
        self._running_heading = shell.label(self, "", "Heading")
        self._running_lead = shell.label(self, "", "Lead")
        self._verdict_mark = shell.label(self, "", "Verdict")
        self._verdict_title = shell.label(self, "", "Heading")
        self._verdict_lead = shell.label(self, "", "Lead")
        self._footer = Footer(self)

        # Neutral start: a zero-size sink absorbs the focus Qt would otherwise
        # hand to the first control in tab order.
        self._focus_sink = QWidget(self)
        self._focus_sink.setFixedSize(0, 0)
        self._focus_sink.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def _set_choices(self) -> None:
        """Open every box on what is already true.

        A box that says what is there is the whole point of reading the machine
        first: setup used to offer a shortcut the user had deliberately deleted
        as though they had asked for it back.
        """
        fresh = not self.here.installed
        self._desktop.setChecked(True if fresh else self.here.desktop)
        self._start_menu.setChecked(True if fresh else self.here.start_menu)
        self._launch.setChecked(True)

    # -------------------------------------------------------------- behaviour

    def showEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Start neutral, so no control wears a ring until one is asked for.

        The window is LOOKED AT before it is acted in: this one asks the reader
        to check what setup is about to do before pressing anything, so
        lighting a button up unasked argues for a decision that has not been
        made yet.
        """
        super().showEvent(event)
        if not self._shown:
            self._shown = True
            self._focus_sink.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Enter activates the focused control, as Space already does.

        Qt gives a plain window neither: Return only clicks a button inside a
        QDialog, so without this a focused button here ignores Enter entirely.
        """
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            target = self.focusWidget()
            if isinstance(target, QAbstractButton) and target.isEnabled():
                target.click()
                event.accept()
                return
        super().keyPressEvent(event)

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

    # ------------------------------------------------------------------ shell

    def _build(self) -> None:
        """Header, a rule, the centred body, a rule, then the footer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            c.CONTENT_MARGIN_H,
            c.CONTENT_MARGIN_TOP,
            c.CONTENT_MARGIN_H,
            c.CONTENT_MARGIN_BOTTOM,
        )
        layout.setSpacing(c.HEADER_PAD_PX)
        header = shell.header(
            self,
            f"{c.APP_DISPLAY_NAME} Setup",
            c.APP_TAGLINE,
            _app_icon(),
            (self._licence_button, self._theme_button),
        )
        layout.addLayout(header)
        layout.addWidget(shell.rule(self))
        self._body = QStackedWidget(self)
        self._body.setObjectName("Body")
        self._body.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for screen in self._screens():
            self._body.addWidget(screen)
        layout.addWidget(self._body, 1)
        layout.addWidget(shell.rule(self))
        layout.addWidget(self._footer)
        # Set once the header exists, so it is measured rather than guessed.
        self.setMinimumSize(*shell.minimum_window_size(header))

    def _screens(self) -> tuple[QWidget, ...]:
        """Every screen, in the order the stack indices name them."""
        return (
            self._route_screen(),
            self._uninstall_screen(),
            screens.message(self, self._running_heading, self._running_lead),
            screens.progress(
                self, self._progress_title, self._progress, self._progress_status
            ),
            screens.verdict(
                self, self._verdict_mark, self._verdict_title, self._verdict_lead
            ),
        )

    def _route_screen(self) -> QWidget:
        """What this run is for, with the choices that shape it."""
        options = (
            (self._start_menu, wording.START_MENU_HINT),
            (self._desktop, ""),
            (self._launch, ""),
        )
        location = str(c.install_dir()) if self.route is Route.INSTALL else ""
        versions = None
        if self.route in (Route.UPDATE, Route.DOWNGRADE):
            versions = (f"v{self.here.version}", f"v{self.version}")
        return screens.choices(
            self,
            wording.heading(self.route, self.here.version, self.version),
            wording.lead(self.route),
            options,
            location,
            versions,
        )

    def _uninstall_screen(self) -> QWidget:
        """The removal screen, reachable from every other one."""
        return screens.choices(
            self,
            wording.heading(Route.UNINSTALL, self.here.version, self.version),
            wording.lead(Route.UNINSTALL),
            (),
        )

    # ---------------------------------------------------------------- routing

    def _show_screen(self, index: int, actions: Iterable[Action]) -> None:
        """Show one screen with the actions that belong to it.

        Every screen change goes through here, so the footer is rebuilt for the
        screen rather than relabelled; the ring is put back into reading order
        afterwards.

        Args:
            index: Which screen the stack should show.
            actions: The buttons the footer offers under it.
        """
        self._body.setCurrentIndex(index)
        self._footer.show_actions(actions)
        self._order_ring()

    def _order_ring(self) -> None:
        """Put the tab ring back into reading order, header to footer.

        The footer's buttons are made fresh for each screen, so Qt's own order
        follows when they were created rather than where they are drawn: left
        alone, the ring offers the footer BEFORE the header. Stating the order
        is the fix; it is stated over the stops that are actually on screen,
        the choices only while the screen carrying them is showing.
        """
        stops: list[QWidget] = [
            self._focus_sink,
            self._licence_button,
            self._theme_button,
        ]
        if self._body.currentIndex() == screens.SCREEN_ROUTE:
            stops.extend((self._start_menu, self._desktop, self._launch))
        stops.extend(self._footer.buttons())
        # Deliberately uneven: each stop is paired with the one after it, so
        # the last has no partner.
        for first, second in zip(stops, stops[1:], strict=False):
            self.setTabOrder(first, second)

    def _show_current(self) -> None:
        """Show whichever screen is due, after a start or an interruption."""
        if self._uninstalling:
            self._show_uninstall()
            return
        self._show_route()

    def _show_route(self) -> None:
        """The screen this run is for, with the actions that belong to it."""
        self._uninstalling = False
        self._show_screen(screens.SCREEN_ROUTE, self._route_actions())

    def _route_actions(self) -> tuple[Action, ...]:
        """The actions under the route screen, destructive ones marked."""
        go = Action(wording.primary_label(self.route), self._go, PRIMARY)
        if self.route is Route.INSTALL:
            return (Action("Cancel", self.close), go)
        remove = Action("Uninstall", self._show_uninstall, DANGER)
        if self.route is Route.MANAGE:
            return (
                remove,
                Action("Close", self.close),
                Action("Reinstall", self._reinstall),
                go,
            )
        return (remove, Action("Not now", self.close), go)

    def _show_uninstall(self) -> None:
        """Ask before removing anything; this screen IS the confirmation."""
        self._uninstalling = True
        self._show_screen(
            screens.SCREEN_UNINSTALL,
            (
                Action("Cancel", self._cancel_removal),
                Action("Uninstall", self._remove, DANGER),
            ),
        )

    def _cancel_removal(self) -> None:
        """Back to what setup was otherwise for; nothing, when it was only this."""
        if self._opened_to_remove:
            self.close()
            return
        self._show_route()

    def _go(self) -> None:
        """The go-ahead: a repair when the version already matches, else files."""
        if self.route is Route.MANAGE:
            self._repair()
            return
        self._write_files()

    def _reinstall(self) -> None:
        """Write the files again with the choices showing on screen."""
        self._write_files(reinstalling=True)

    # ---------------------------------------------------------------- actions

    def _toggle_theme(self) -> None:
        """Switch between the dark and light appearances."""
        self._dark = not self._dark
        appearance.apply(self._dark, self._theme_button)

    def _show_licence(self) -> None:
        """Open the LGPL-3.0 text the setup program itself is covered by."""
        LicenceDialog(self).exec()
