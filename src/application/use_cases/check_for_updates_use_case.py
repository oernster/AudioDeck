"""Use case deciding whether a newer release should be offered.

Version strings compare as dotted integer tuples with an optional leading
``v``. Anything unparseable compares as not-newer, so a malformed tag can
never raise a spurious prompt and a ``0.0.0-dev`` build stays silent.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from src.application.dtos.update_status import UpdateStatus
from src.domain.interfaces.release_source import IReleaseSource
from src.domain.value_objects.release_info import ReleaseAsset

_PLATFORM_SUFFIXES: Dict[str, str] = {
    "windows": ".exe",
    "macos": ".dmg",
    "linux": ".flatpak",
}

_SYS_PLATFORM_KEYS: Dict[str, str] = {
    "win32": "windows",
    "darwin": "macos",
}

_DEFAULT_PLATFORM_KEY = "linux"


def _parse(version: str) -> Optional[Tuple[int, ...]]:
    """Parse a dotted version, tolerating a leading v; None when malformed."""
    text = version.strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError:
        return None


def is_newer(latest: str, current: str) -> bool:
    """Return True when latest is a strictly newer version than current.

    Args:
        latest: The candidate version, usually a release tag
        current: The running version

    Returns:
        True only when both parse and latest is strictly greater
    """
    latest_parts = _parse(latest)
    current_parts = _parse(current)
    if latest_parts is None or current_parts is None:
        return False
    return latest_parts > current_parts


def platform_key_for(sys_platform: str) -> str:
    """Map a sys.platform value to the asset-selection key.

    Args:
        sys_platform: The value of ``sys.platform``

    Returns:
        The platform key used to pick a release asset
    """
    return _SYS_PLATFORM_KEYS.get(sys_platform, _DEFAULT_PLATFORM_KEY)


def select_asset_url(
    assets: Tuple[ReleaseAsset, ...], platform_key: str
) -> Optional[str]:
    """Pick the first asset whose name matches the platform's suffix.

    Args:
        assets: The release's downloadable assets
        platform_key: The key from platform_key_for

    Returns:
        The matching asset's download URL, or None when nothing matches
    """
    suffix = _PLATFORM_SUFFIXES.get(platform_key)
    if suffix is None:
        return None
    for asset in assets:
        if asset.name.lower().endswith(suffix):
            return asset.download_url
    return None


class CheckForUpdatesUseCase:
    """Decides whether an update should be offered, and with which download."""

    def __init__(
        self,
        release_source: IReleaseSource,
        current_version: str,
        platform_key: str,
    ) -> None:
        """Initialize the use case.

        Args:
            release_source: Source of the latest published release
            current_version: The running version string
            platform_key: The asset-selection key for this platform
        """
        self._release_source = release_source
        self._current_version = current_version
        self._platform_key = platform_key

    def execute(self, skipped_version: Optional[str] = None) -> Optional[UpdateStatus]:
        """Run one update check.

        Args:
            skipped_version: The exact tag the user chose to skip; both sides
                come from the same endpoint, so string equality is enough. The
                manual check passes None here, which is how it ignores the skip

        Returns:
            The check's outcome, or None when the release source is unreachable
        """
        release = self._release_source.latest_release()
        if release is None:
            return None
        newer = is_newer(release.version, self._current_version)
        available = newer and release.version != skipped_version
        download_url = (
            select_asset_url(release.assets, self._platform_key) if available else None
        )
        return UpdateStatus(
            current=self._current_version,
            latest=release.version,
            update_available=available,
            download_url=download_url,
            page_url=release.page_url,
        )
