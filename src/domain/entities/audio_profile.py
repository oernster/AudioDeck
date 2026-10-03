"""Audio profile entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AudioProfile:
    """Represents an audio profile configuration."""

    id: UUID
    name: str
    output_device_id: Optional[str] = None
    input_device_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.name:
            raise ValueError("Profile name cannot be empty")

    def update(
        self,
        name: str,
        output_device_id: Optional[str],
        input_device_id: Optional[str],
    ) -> None:
        """Replace the profile's settings with the full desired state.

        Every field is stated: None for a device means "no device", never
        "leave it as it was", so choosing (None) in the editor clears it.

        Args:
            name: The profile name
            output_device_id: The output device ID, None for no output
            input_device_id: The input device ID, None for no input
        """
        if not name:
            raise ValueError("Profile name cannot be empty")
        self.name = name
        self.output_device_id = output_device_id
        self.input_device_id = input_device_id
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert profile to dictionary for serialization.

        Returns:
            Dictionary representation of profile
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "output_device_id": self.output_device_id,
            "input_device_id": self.input_device_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioProfile":
        """Create profile from dictionary.

        Args:
            data: Dictionary containing profile data

        Returns:
            AudioProfile instance
        """
        from uuid import UUID

        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            output_device_id=data.get("output_device_id"),
            input_device_id=data.get("input_device_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
