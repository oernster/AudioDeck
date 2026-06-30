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
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from src.presentation.presenters.actuation_presenter import ActuationPresenter

# Colour for a profile whose configured device is currently offline.
_OFFLINE_COLOR = QColor("#c0392b")
_OFFLINE_SUFFIX = "  (device offline)"

# How often to rescan audio devices so newly connected hardware (for example a
# Bluetooth headset switched on) is picked up without a manual refresh.
DEVICE_REFRESH_INTERVAL_MS = 10000


class ActuationView(QWidget):
    """View for quick switching between audio profiles."""

    def __init__(self, presenter: ActuationPresenter) -> None:
        """Initialize actuation view.

        Args:
            presenter: Presenter for this view
        """
        super().__init__()
        self._presenter = presenter

        self._setup_ui()
        self._connect_signals()
        self.refresh()
        self._start_auto_refresh()

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
        self._presenter.current_devices_changed.connect(self._load_current_devices)

    def refresh(self) -> None:
        """Refresh the view with current data."""
        self._load_profiles()
        self._load_current_devices()

    def _start_auto_refresh(self) -> None:
        """Start the periodic device rescan timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(DEVICE_REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self._auto_refresh_devices)
        self._refresh_timer.start()

    def _auto_refresh_devices(self) -> None:
        """Periodically poll for device changes (fallback to the native notifier).

        Delegates to the presenter, which refreshes the current-default labels
        and re-applies any profile device that has reconnected. Selection and
        the profile list are left untouched.
        """
        self._presenter.on_devices_changed()

    def _load_profiles(self) -> None:
        """Load profiles into the list."""
        self._profile_list.clear()
        profiles = self._presenter.get_profiles()

        if not profiles:
            item = QListWidgetItem(
                "No profiles configured. Use Configuration tab to create profiles."
            )
            item.setFlags(Qt.NoItemFlags)
            self._profile_list.addItem(item)
            return

        available_ids = self._presenter.get_available_device_ids()
        for profile in profiles:
            offline = self._profile_is_offline(profile, available_ids)
            text = profile.display_name + (_OFFLINE_SUFFIX if offline else "")
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, profile.id)
            if offline:
                item.setForeground(_OFFLINE_COLOR)
                item.setToolTip(
                    "A device in this profile is not currently available. "
                    "Switching will apply the available device(s)."
                )
            self._profile_list.addItem(item)

    @staticmethod
    def _profile_is_offline(profile, available_ids) -> bool:
        """Return True if any device the profile needs is not available."""
        configured = [profile.output_device_id, profile.input_device_id]
        return any(
            device_id is not None and device_id not in available_ids
            for device_id in configured
        )

    def _load_current_devices(self) -> None:
        """Load current default devices."""
        output_device = self._presenter.get_current_output_device()
        input_device = self._presenter.get_current_input_device()

        if output_device:
            self._current_output_label.setText(f"Output: {output_device.name}")
        else:
            self._current_output_label.setText("Output: None")

        if input_device:
            self._current_input_label.setText(f"Input: {input_device.name}")
        else:
            self._current_input_label.setText("Input: None")

    def _on_profile_selection_changed(self) -> None:
        """Handle profile selection change."""
        selected_items = self._profile_list.selectedItems()
        has_valid_selection = (
            len(selected_items) > 0 and selected_items[0].data(Qt.UserRole) is not None
        )
        self._switch_button.setEnabled(has_valid_selection)

    def _on_switch_profile(self) -> None:
        """Handle switch profile button click."""
        selected_items = self._profile_list.selectedItems()
        if not selected_items:
            return

        profile_id = selected_items[0].data(Qt.UserRole)
        if profile_id is None:
            return

        self._presenter.switch_profile(profile_id)
        self._load_current_devices()
