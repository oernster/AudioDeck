"""Configuration view for creating and editing profiles."""

from typing import Optional
from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.presenters.configuration_presenter import ConfigurationPresenter
from src.presentation.views.icons import (
    ICON_CANCEL,
    ICON_DELETE,
    ICON_EDIT,
    ICON_NEW,
    ICON_REFRESH,
    ICON_SAVE,
)


class ConfigurationView(QWidget):
    """View for configuring audio profiles."""

    def __init__(self, presenter: ConfigurationPresenter) -> None:
        """Initialize configuration view.

        Args:
            presenter: Presenter for this view
        """
        super().__init__()
        self._presenter = presenter
        self._current_profile_id: Optional[UUID] = None

        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Profile list section
        profile_group = QGroupBox("Saved Profiles")
        profile_layout = QVBoxLayout(profile_group)

        self._profile_list = QListWidget()
        self._profile_list.setMinimumHeight(350)
        profile_layout.addWidget(self._profile_list)
        layout.addWidget(profile_group)

        # Action buttons: created here so the enabled logic stays with the
        # view, but placed in the main window's header tray, not this layout.
        self._new_button = QPushButton()
        self._edit_button = QPushButton()
        self._delete_button = QPushButton()
        self._edit_button.setEnabled(False)
        self._delete_button.setEnabled(False)
        self._save_button = QPushButton()
        self._cancel_button = QPushButton()

        # Profile editor section
        editor_group = QGroupBox("Profile Editor")
        editor_layout = QVBoxLayout(editor_group)

        # Profile name
        name_layout = QHBoxLayout()
        name_label = QLabel("Profile Name:")
        name_label.setFixedWidth(140)
        name_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        name_layout.addWidget(name_label)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter profile name...")
        name_layout.addWidget(self._name_input)
        editor_layout.addLayout(name_layout)

        # Output device
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Device:")
        output_label.setFixedWidth(140)
        output_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        output_layout.addWidget(output_label)
        self._output_combo = QComboBox()
        self._output_combo.addItem("(None)", None)
        output_layout.addWidget(self._output_combo)
        self._refresh_output_button = QPushButton(ICON_REFRESH)
        self._refresh_output_button.setMaximumWidth(40)
        self._refresh_output_button.setToolTip("Refresh output devices")
        output_layout.addWidget(self._refresh_output_button)
        editor_layout.addLayout(output_layout)

        # Input device
        input_layout = QHBoxLayout()
        input_label = QLabel("Input Device:")
        input_label.setFixedWidth(140)
        input_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        input_layout.addWidget(input_label)
        self._input_combo = QComboBox()
        self._input_combo.addItem("(None)", None)
        input_layout.addWidget(self._input_combo)
        self._refresh_input_button = QPushButton(ICON_REFRESH)
        self._refresh_input_button.setMaximumWidth(40)
        self._refresh_input_button.setToolTip("Refresh input devices")
        input_layout.addWidget(self._refresh_input_button)
        editor_layout.addLayout(input_layout)

        layout.addWidget(editor_group)
        layout.addStretch()

        # Initially disable editor
        self._set_editor_enabled(False)

    def tray_actions(self) -> tuple[tuple[QPushButton, str, str], ...]:
        """Return (button, glyph, name) triples for the header tray."""
        return (
            (self._new_button, ICON_NEW, "New profile"),
            (self._edit_button, ICON_EDIT, "Edit the selected profile"),
            (self._delete_button, ICON_DELETE, "Delete the selected profile"),
            (self._save_button, ICON_SAVE, "Save the profile being edited"),
            (self._cancel_button, ICON_CANCEL, "Cancel the edit"),
        )

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._profile_list.itemSelectionChanged.connect(
            self._on_profile_selection_changed
        )
        self._new_button.clicked.connect(self._on_new_profile)
        self._edit_button.clicked.connect(self._on_edit_profile)
        self._delete_button.clicked.connect(self._on_delete_profile)
        self._save_button.clicked.connect(self._on_save_profile)
        self._cancel_button.clicked.connect(self._on_cancel)
        self._refresh_output_button.clicked.connect(
            lambda: self._load_devices(refresh=True)
        )
        self._refresh_input_button.clicked.connect(
            lambda: self._load_devices(refresh=True)
        )

    def refresh(self) -> None:
        """Refresh the view with current data."""
        self._load_profiles()
        self._load_devices()

    def _load_profiles(self) -> None:
        """Load profiles into the list."""
        self._profile_list.clear()
        profiles = self._presenter.get_profiles()

        for profile in profiles:
            item = QListWidgetItem(profile.display_name)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self._profile_list.addItem(item)

    def _load_devices(self, refresh: bool = False) -> None:
        """Load devices into combo boxes.

        Args:
            refresh: Whether to refresh device list
        """
        # Get devices
        output_devices = self._presenter.get_output_devices(refresh)
        input_devices = self._presenter.get_input_devices(refresh)

        # Save current selections
        current_output = self._output_combo.currentData()
        current_input = self._input_combo.currentData()

        # Clear and repopulate output combo
        self._output_combo.clear()
        self._output_combo.addItem("(None)", None)
        for device in output_devices:
            self._output_combo.addItem(device.display_name, device.id)

        # Clear and repopulate input combo
        self._input_combo.clear()
        self._input_combo.addItem("(None)", None)
        for device in input_devices:
            self._input_combo.addItem(device.display_name, device.id)

        # Restore selections if possible
        if current_output is not None:
            index = self._output_combo.findData(current_output)
            if index >= 0:
                self._output_combo.setCurrentIndex(index)

        if current_input is not None:
            index = self._input_combo.findData(current_input)
            if index >= 0:
                self._input_combo.setCurrentIndex(index)

    def _on_profile_selection_changed(self) -> None:
        """Handle profile selection change."""
        has_selection = len(self._profile_list.selectedItems()) > 0
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _on_new_profile(self) -> None:
        """Handle new profile button click."""
        self._current_profile_id = None
        self._name_input.clear()
        self._output_combo.setCurrentIndex(0)
        self._input_combo.setCurrentIndex(0)
        self._set_editor_enabled(True)
        self._name_input.setFocus()

    def _on_edit_profile(self) -> None:
        """Handle edit profile button click."""
        selected_items = self._profile_list.selectedItems()
        if not selected_items:
            return

        profile_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        profile = self._presenter.get_profile_by_id(profile_id)

        if profile is None:
            return

        self._current_profile_id = profile.id
        self._name_input.setText(profile.name)

        # Set output device
        if profile.output_device_id:
            index = self._output_combo.findData(profile.output_device_id)
            if index >= 0:
                self._output_combo.setCurrentIndex(index)
        else:
            self._output_combo.setCurrentIndex(0)

        # Set input device
        if profile.input_device_id:
            index = self._input_combo.findData(profile.input_device_id)
            if index >= 0:
                self._input_combo.setCurrentIndex(index)
        else:
            self._input_combo.setCurrentIndex(0)

        self._set_editor_enabled(True)
        self._name_input.setFocus()

    def _on_delete_profile(self) -> None:
        """Handle delete profile button click."""
        selected_items = self._profile_list.selectedItems()
        if not selected_items:
            return

        profile_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        profile = self._presenter.get_profile_by_id(profile_id)

        if profile is None:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._presenter.delete_profile(profile_id)
            self._load_profiles()

    def _on_save_profile(self) -> None:
        """Handle save profile button click."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            return

        output_device_id = self._output_combo.currentData()
        input_device_id = self._input_combo.currentData()

        if output_device_id is None and input_device_id is None:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select at least one device (input or output).",
            )
            return

        if self._current_profile_id is None:
            # Create new profile
            self._presenter.create_profile(name, output_device_id, input_device_id)
        else:
            # Update existing profile
            self._presenter.update_profile(
                self._current_profile_id, name, output_device_id, input_device_id
            )

        self._on_cancel()
        self._load_profiles()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self._current_profile_id = None
        self._name_input.clear()
        self._output_combo.setCurrentIndex(0)
        self._input_combo.setCurrentIndex(0)
        self._set_editor_enabled(False)
        self._profile_list.clearSelection()

    def _set_editor_enabled(self, enabled: bool) -> None:
        """Enable or disable the editor section.

        Args:
            enabled: Whether to enable the editor
        """
        self._name_input.setEnabled(enabled)
        self._output_combo.setEnabled(enabled)
        self._input_combo.setEnabled(enabled)
        self._refresh_output_button.setEnabled(enabled)
        self._refresh_input_button.setEnabled(enabled)
        self._save_button.setEnabled(enabled)
        self._cancel_button.setEnabled(enabled)
