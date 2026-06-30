"""Actuation view for quick profile switching."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.presentation.workers.background_runner import BackgroundRunner

# Colour for a profile whose configured device is currently offline.
_OFFLINE_COLOR = QColor("#c0392b")
_OFFLINE_SUFFIX = "  (device offline)"

# Item data roles.
_PROFILE_ID_ROLE = Qt.UserRole
_OUTPUT_ID_ROLE = Qt.UserRole + 1
_INPUT_ID_ROLE = Qt.UserRole + 2
_BASE_TEXT_ROLE = Qt.UserRole + 3

# How often to rescan audio devices so newly connected hardware (for example a
# Bluetooth headset switched on) is picked up without a manual refresh.
DEVICE_REFRESH_INTERVAL_MS = 10000
# Coalesce bursts of device-change events into a single rescan.
DEVICE_CHANGE_DEBOUNCE_MS = 350


class ActuationView(QWidget):
    """View for quick switching between audio profiles."""

    def __init__(self, presenter: ActuationPresenter) -> None:
        """Initialize actuation view.

        Args:
            presenter: Presenter for this view
        """
        super().__init__()
        self._presenter = presenter
        self._runner = BackgroundRunner(self)
        self._available_ids = set()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._runner.stop)

        self._setup_ui()
        self._connect_signals()
        self._setup_timers()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title and instructions
        title_label = QLabel("Quick Profile Switch")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        instructions = QLabel(
            "Select a profile below to instantly switch your audio devices.\n"
            "Use the Configuration tab to create or edit profiles."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Profile list section
        profile_group = QGroupBox("Available Profiles")
        profile_layout = QVBoxLayout(profile_group)

        self._profile_list = QListWidget()
        self._profile_list.setMinimumHeight(350)
        profile_layout.addWidget(self._profile_list)

        # Action buttons
        button_layout = QHBoxLayout()
        self._switch_button = QPushButton("Switch to Selected Profile")
        self._switch_button.setEnabled(False)
        self._switch_button.setMinimumHeight(40)
        button_layout.addWidget(self._switch_button)

        self._refresh_button = QPushButton("🔄 Refresh Devices")
        self._refresh_button.setMinimumWidth(160)
        self._refresh_button.setToolTip(
            "Rescan audio devices and update the current defaults"
        )
        button_layout.addWidget(self._refresh_button)

        profile_layout.addLayout(button_layout)
        layout.addWidget(profile_group)

        # Current devices section
        current_group = QGroupBox("Current Default Devices")
        current_layout = QVBoxLayout(current_group)

        self._current_output_label = QLabel("Output: Loading...")
        self._current_input_label = QLabel("Input: Loading...")

        current_layout.addWidget(self._current_output_label)
        current_layout.addWidget(self._current_input_label)

        layout.addWidget(current_group)
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._profile_list.itemSelectionChanged.connect(
            self._on_profile_selection_changed
        )
        self._profile_list.itemDoubleClicked.connect(lambda: self._on_switch_profile())
        self._switch_button.clicked.connect(self._on_switch_profile)
        self._refresh_button.clicked.connect(self.refresh)
        # Status computed on the worker thread arrives here (queued to the GUI).
        self._presenter.status_ready.connect(self._on_status_ready)

    def _setup_timers(self) -> None:
        """Set up the periodic rescan and the device-change debounce timers."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(DEVICE_REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self.handle_device_change)
        self._refresh_timer.start()

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(DEVICE_CHANGE_DEBOUNCE_MS)
        self._debounce.timeout.connect(
            lambda: self._runner.submit(self._presenter.on_devices_changed)
        )

    def handle_device_change(self) -> None:
        """Debounce a device change, then rescan on the worker thread.

        Safe to call from the periodic timer and the native device-change
        notifier; bursts are coalesced into a single rescan.
        """
        self._debounce.start()

    def refresh(self) -> None:
        """Reload the profile list (fast) and rescan devices in the background."""
        self._load_profiles()
        self._runner.submit(self._presenter.refresh_status)

    def _load_profiles(self) -> None:
        """Load profiles into the list (reads local JSON only)."""
        self._profile_list.clear()
        profiles = self._presenter.get_profiles()

        if not profiles:
            item = QListWidgetItem(
                "No profiles configured. Use Configuration tab to create profiles."
            )
            item.setFlags(Qt.NoItemFlags)
            self._profile_list.addItem(item)
            return

        for profile in profiles:
            item = QListWidgetItem(profile.display_name)
            item.setData(_PROFILE_ID_ROLE, profile.id)
            item.setData(_OUTPUT_ID_ROLE, profile.output_device_id)
            item.setData(_INPUT_ID_ROLE, profile.input_device_id)
            item.setData(_BASE_TEXT_ROLE, profile.display_name)
            self._profile_list.addItem(item)
            self._apply_offline_badge(item)

    def _apply_offline_badge(self, item: QListWidgetItem) -> None:
        """Mark or clear a profile item based on cached device availability."""
        if item.data(_PROFILE_ID_ROLE) is None:
            return
        base_text = item.data(_BASE_TEXT_ROLE)
        offline = self._item_is_offline(item)
        item.setText(base_text + (_OFFLINE_SUFFIX if offline else ""))
        if offline:
            item.setForeground(_OFFLINE_COLOR)
            item.setToolTip(
                "A device in this profile is not currently available. "
                "Switching will apply the available device(s)."
            )
        else:
            item.setData(Qt.ForegroundRole, None)
            item.setToolTip("")

    def _item_is_offline(self, item: QListWidgetItem) -> bool:
        """Return True if a profile item references an unavailable device."""
        configured = [item.data(_OUTPUT_ID_ROLE), item.data(_INPUT_ID_ROLE)]
        return any(
            device_id is not None and device_id not in self._available_ids
            for device_id in configured
        )

    def _on_status_ready(self, output_device, input_device, available_ids) -> None:
        """Render device status produced on the worker thread."""
        self._available_ids = available_ids or set()

        self._current_output_label.setText(
            f"Output: {output_device.name}" if output_device else "Output: None"
        )
        self._current_input_label.setText(
            f"Input: {input_device.name}" if input_device else "Input: None"
        )

        for row in range(self._profile_list.count()):
            self._apply_offline_badge(self._profile_list.item(row))

    def _on_profile_selection_changed(self) -> None:
        """Handle profile selection change."""
        selected_items = self._profile_list.selectedItems()
        has_valid_selection = (
            len(selected_items) > 0
            and selected_items[0].data(_PROFILE_ID_ROLE) is not None
        )
        self._switch_button.setEnabled(has_valid_selection)

    def _on_switch_profile(self) -> None:
        """Handle switch profile request (runs on the worker thread)."""
        selected_items = self._profile_list.selectedItems()
        if not selected_items:
            return

        profile_id = selected_items[0].data(_PROFILE_ID_ROLE)
        if profile_id is None:
            return

        self._runner.submit(self._presenter.switch_profile, profile_id)
