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
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.presentation.presenters.actuation_presenter import ActuationPresenter


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
        self._profile_list.setMinimumHeight(200)
        profile_layout.addWidget(self._profile_list)

        # Action buttons
        button_layout = QHBoxLayout()
        self._switch_button = QPushButton("Switch to Selected Profile")
        self._switch_button.setEnabled(False)
        self._switch_button.setMinimumHeight(40)
        button_layout.addWidget(self._switch_button)

        self._refresh_button = QPushButton("🔄 Refresh")
        self._refresh_button.setMaximumWidth(100)
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

    def refresh(self) -> None:
        """Refresh the view with current data."""
        self._load_profiles()
        self._load_current_devices()

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

        for profile in profiles:
            item = QListWidgetItem(profile.display_name)
            item.setData(Qt.UserRole, profile.id)
            self._profile_list.addItem(item)

    def _load_current_devices(self) -> None:
        """Load current default devices."""
        output_device = self._presenter.get_current_output_device()
        input_device = self._presenter.get_current_input_device()

        print(
            f"Current default output device: {output_device.name if output_device else 'None'} (ID: {output_device.id if output_device else 'N/A'})"
        )
        print(
            f"Current default input device: {input_device.name if input_device else 'None'} (ID: {input_device.id if input_device else 'N/A'})"
        )

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
