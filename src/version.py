"""Single source of truth for the AudioDeck version.

The version string lives in the repo-root ``VERSION`` file. This module reads
it at runtime so nothing else hardcodes a version. ``pyproject.toml`` reads the
same file for packaging metadata, keeping one source of truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

_VERSION_FILENAME = "VERSION"
_DEV_FALLBACK = "0.0.0-dev"


def _read_version() -> str:
    """Read the version string from the VERSION file.

    Looks in the PyInstaller bundle directory when frozen, otherwise in the
    repo root (the parent of this file's ``src`` directory). Falls back to a
    development sentinel if the file cannot be read.

    Returns:
        The version string, else the development sentinel on failure.
    """
    candidates = []

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir is not None:
        candidates.append(Path(bundle_dir) / _VERSION_FILENAME)

    candidates.append(Path(__file__).resolve().parent.parent / _VERSION_FILENAME)

    for candidate in candidates:
        try:
            return candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue

    return _DEV_FALLBACK


__version__ = _read_version()
