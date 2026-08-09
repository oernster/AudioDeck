"""Value objects describing a published release, for the update check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ReleaseAsset:
    """One downloadable file attached to a release."""

    name: str
    download_url: str


@dataclass(frozen=True)
class ReleaseInfo:
    """A published release: its tag, its page and its downloadable assets."""

    version: str
    page_url: Optional[str]
    assets: Tuple[ReleaseAsset, ...]
