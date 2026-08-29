"""A disabled control still shows what it is set to.

While an operation runs, every option is disabled so it cannot be changed
underneath the work. Disabled must not mean BLANK: the boxes still describe
what the run is doing, so a ticked option that reads as unticked tells the user
the opposite of the truth at the one moment they cannot correct it.

This is pinned by rendering the real stylesheet and sampling the indicator,
because the defect it guards against is a rule-ordering one. A checked and
disabled indicator matches `::indicator:checked` and `::indicator:disabled`
equally, so whichever is written last wins; reading the sheet does not reveal
that, so only the painted pixel settles it.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox

from installer import constants as c
from installer.theme import DISABLED_MIX, blended, palette_for, stylesheet

APPEARANCES = (True, False)


def _indicator_colour(qapp, dark: bool, checked: bool, enabled: bool) -> str:
    """The colour the checkbox indicator actually paints, as a hex string."""
    qapp.setStyleSheet(stylesheet(dark))
    box = QCheckBox("option")
    box.setChecked(checked)
    box.setEnabled(enabled)
    box.resize(220, 40)
    box.show()
    qapp.processEvents()
    image = box.grab().toImage()
    # The middle of the indicator box, which sits at the left of the row.
    return QColor(image.pixel(5 + c.CHECK_PX // 2, box.height() // 2)).name().lower()


@pytest.mark.parametrize("dark", APPEARANCES)
def test_a_ticked_option_still_reads_as_ticked_once_disabled(qapp, dark: bool) -> None:
    """The bug this exists for: every box went blank when the run started."""
    ticked = _indicator_colour(qapp, dark, checked=True, enabled=False)
    unticked = _indicator_colour(qapp, dark, checked=False, enabled=False)

    assert ticked != unticked, (
        "a disabled checkbox paints the same whether ticked or not, so the "
        "options go blank the moment an operation starts"
    )


@pytest.mark.parametrize("dark", APPEARANCES)
def test_the_disabled_tick_is_the_accent_muted(qapp, dark: bool) -> None:
    """Muted rather than replaced, so it still reads as the same state."""
    colour = palette_for(dark)
    expected = blended(colour.accent, colour.disabled_surface, DISABLED_MIX)

    assert _indicator_colour(qapp, dark, checked=True, enabled=False) == (
        expected.lower()
    )


@pytest.mark.parametrize("dark", APPEARANCES)
def test_an_enabled_tick_is_the_full_accent(qapp, dark: bool) -> None:
    """The fix must not have dulled the ordinary case."""
    colour = palette_for(dark)

    assert _indicator_colour(qapp, dark, checked=True, enabled=True) == (
        colour.accent.lower()
    )


@pytest.mark.parametrize("dark", APPEARANCES)
def test_a_disabled_tick_stays_off_its_own_surface(qapp, dark: bool) -> None:
    """A fill equal to the surface behind it would be invisible either way."""
    colour = palette_for(dark)
    ticked = _indicator_colour(qapp, dark, checked=True, enabled=False)

    assert ticked != colour.disabled_surface.lower()
    assert ticked != colour.surface.lower()
