"""Outcome of one update check, carried to the presentation layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UpdateStatus:
    """What the check found and what, if anything, to offer."""

    current: str
    latest: str
    update_available: bool
    download_url: Optional[str]
    page_url: Optional[str]
