"""Profile Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ProfileDTO:
    """DTO for transferring profile data between layers."""

    id: UUID
    name: str
    output_device_id: Optional[str]
    input_device_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def has_output(self) -> bool:
        """Check if profile has output device configured."""
        return self.output_device_id is not None

    @property
    def has_input(self) -> bool:
        """Check if profile has input device configured."""
        return self.input_device_id is not None

    @property
    def is_complete(self) -> bool:
        """Check if profile has both input and output configured."""
        return self.has_output and self.has_input

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        parts = []
        if self.has_output:
            parts.append("Output")
        if self.has_input:
            parts.append("Input")

        if parts:
            return f"{self.name} ({' + '.join(parts)})"
        return f"{self.name} (Empty)"
