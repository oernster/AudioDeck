"""Version parsing and comparison for the installer state machine.

A small PEP 440 subset (dotted numeric release with an optional pre-release
suffix) so the installer needs no third-party dependency.
"""

from __future__ import annotations

import re
from typing import Tuple

_RELEASE_RE = re.compile(r"(\d+(?:\.\d+)*)")


def _release_tuple(version: str) -> Tuple[int, ...]:
    """Return the numeric release part of a version as a tuple of ints.

    Args:
        version: A version string such as "1.2.0" or "1.2.0-rc1".

    Returns:
        The leading dotted-numeric part as a tuple, or (0,) if none is found.
    """
    match = _RELEASE_RE.match(version.strip())
    if match is None:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def _is_prerelease(version: str) -> bool:
    """Return True if the version carries a pre-release suffix."""
    return bool(re.search(r"[-+a-zA-Z]", version.strip().lstrip("0123456789.")))


def compare_versions(left: str, right: str) -> int:
    """Compare two version strings.

    Args:
        left: First version.
        right: Second version.

    Returns:
        1 if left is newer, -1 if left is older, 0 if equal.
    """
    left_release = _release_tuple(left)
    right_release = _release_tuple(right)

    length = max(len(left_release), len(right_release))
    left_padded = left_release + (0,) * (length - len(left_release))
    right_padded = right_release + (0,) * (length - len(right_release))

    if left_padded > right_padded:
        return 1
    if left_padded < right_padded:
        return -1

    # Equal release: a release with no pre-release suffix is newer.
    left_pre = _is_prerelease(left)
    right_pre = _is_prerelease(right)
    if left_pre == right_pre:
        return 0
    return -1 if left_pre else 1
