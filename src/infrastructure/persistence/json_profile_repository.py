"""JSON-based profile repository."""

import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from src.domain.entities.audio_profile import AudioProfile
from src.domain.exceptions.domain_exceptions import ProfileStorageException
from src.infrastructure.persistence.atomic_file import (
    backup_path,
    keep_backup,
    read_tolerantly,
    write_atomically,
)


class JsonProfileRepository:
    """Repository for storing profiles in JSON format."""

    def __init__(self, file_path: Path) -> None:
        """Initialize repository.

        Args:
            file_path: Path to JSON file for storage
        """
        self._file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the storage file exists."""
        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_profiles([])

    def _read_profiles(self) -> List[AudioProfile]:
        """Read profiles from file.

        Every write replaces the file atomically, so a read made while
        another process saves (the CLI during a save in the window) sees the
        old profiles or the new ones, never half a document.

        Returns:
            List of profiles

        Raises:
            ProfileStorageException: If read fails
        """
        try:
            data = json.loads(read_tolerantly(self._file_path))
            return [AudioProfile.from_dict(p) for p in data]
        except json.JSONDecodeError as e:
            raise ProfileStorageException(
                f"Failed to parse profiles file: {e}{self._backup_hint()}"
            ) from e
        except Exception as e:
            raise ProfileStorageException(f"Failed to read profiles: {e}") from e

    def _backup_hint(self) -> str:
        """Name the last good copy, when there is one, for an unreadable file."""
        backup = backup_path(self._file_path)
        if not backup.exists():
            return ""
        return f". The last good copy is kept at {backup}"

    def _write_profiles(self, profiles: List[AudioProfile]) -> None:
        """Write profiles to file without ever leaving it half written.

        The current file is copied to its backup first; save and delete call
        this only after reading that file successfully, so the backup is the
        last good copy. A failure anywhere leaves the original untouched.

        Args:
            profiles: List of profiles to write

        Raises:
            ProfileStorageException: If write fails
        """
        try:
            data = [p.to_dict() for p in profiles]
            keep_backup(self._file_path)
            write_atomically(
                self._file_path, lambda handle: json.dump(data, handle, indent=2)
            )
        except Exception as e:
            raise ProfileStorageException(f"Failed to write profiles: {e}") from e

    def save(self, profile: AudioProfile) -> None:
        """Save a profile.

        Args:
            profile: Profile to save

        Raises:
            ProfileStorageException: If save fails
        """
        profiles = self._read_profiles()

        # Update existing or add new
        existing_index = next(
            (i for i, p in enumerate(profiles) if p.id == profile.id), None
        )

        if existing_index is not None:
            profiles[existing_index] = profile
        else:
            profiles.append(profile)

        self._write_profiles(profiles)

    def get_by_id(self, profile_id: UUID) -> Optional[AudioProfile]:
        """Get a profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile or None if not found
        """
        profiles = self._read_profiles()
        return next((p for p in profiles if p.id == profile_id), None)

    def get_all(self) -> List[AudioProfile]:
        """Get all profiles.

        Returns:
            List of all profiles
        """
        return self._read_profiles()

    def delete(self, profile_id: UUID) -> None:
        """Delete a profile.

        Args:
            profile_id: Profile ID to delete

        Raises:
            ProfileStorageException: If delete fails
        """
        profiles = self._read_profiles()
        profiles = [p for p in profiles if p.id != profile_id]
        self._write_profiles(profiles)

    def exists(self, profile_id: UUID) -> bool:
        """Check if a profile exists.

        Args:
            profile_id: Profile ID

        Returns:
            True if profile exists
        """
        return self.get_by_id(profile_id) is not None

    def get_by_name(self, name: str) -> Optional[AudioProfile]:
        """Get a profile by name.

        Args:
            name: Profile name

        Returns:
            Profile or None if not found
        """
        profiles = self._read_profiles()
        return next((p for p in profiles if p.name == name), None)
