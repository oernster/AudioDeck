"""JSON-backed store for the update check's user choices.

Deliberately best-effort, unlike the profile repository: profiles are user
content and a failed write must raise, while losing a skipped-version note
merely means one extra prompt after the next release. A damaged or unreadable
file reads as nothing-skipped and is rewritten whole on the next save;
unrelated keys another writer may add are preserved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

_SKIPPED_VERSION_KEY = "skipped_update_version"


class JsonUpdateSettingsRepository:
    """Persists the update check's settings in a small JSON file."""

    def __init__(self, file_path: Path) -> None:
        """Initialize the repository.

        Args:
            file_path: Path to the settings JSON file
        """
        self._file_path = file_path

    def _read(self) -> Dict[str, Any]:
        """Return the settings document, or an empty one on any failure."""
        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def get_skipped_version(self) -> Optional[str]:
        """Get the release tag the user chose to skip.

        Returns:
            The exact tag string, or None when nothing valid is stored
        """
        value = self._read().get(_SKIPPED_VERSION_KEY)
        return value if isinstance(value, str) and value else None

    def set_skipped_version(self, version: str) -> None:
        """Persist the release tag the user chose to skip.

        Args:
            version: The exact tag string the prompt offered
        """
        data = self._read()
        data[_SKIPPED_VERSION_KEY] = version
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            # Best-effort: the worst case is one extra prompt next release.
            pass
