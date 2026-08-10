"""Pure walking rules for focus rings and tab strips.

Qt-free on purpose, so the rules can be tested without a QApplication. Two
walks over the same candidates: one wrapping (the vertical arrows inside a
strip or ring) and one bounded (Tab and Shift+Tab inside a strip, which must
run out at the ends so the ring can move on rather than being trapped).
"""

from __future__ import annotations

from typing import Optional, Set


def next_candidate(count: int, start: int, delta: int, skip: Set[int]) -> Optional[int]:
    """Return the next usable index, wrapping; None when nothing is usable.

    Args:
        count: How many candidates exist
        start: The current index (may be -1 or count for "outside")
        delta: +1 forward, -1 backward
        skip: Indices that are not usable
    """
    if count <= 0:
        return None
    index = start
    for _ in range(count):
        index = (index + delta) % count
        if index not in skip:
            return index
    return None


def next_candidate_bounded(
    count: int, start: int, delta: int, skip: Set[int]
) -> Optional[int]:
    """Return the next usable index without wrapping; None at the end.

    None is the signal that the strip has run out in that direction and the
    outer ring should take over.
    """
    index = start + delta
    while 0 <= index < count:
        if index not in skip:
            return index
        index += delta
    return None
