"""Every icon the UI asks for exists; the generator is what makes it.

The UI names its artwork by action ("switch", "delete-profile") and resolves
that name to a file at runtime. A name with no file behind it is invisible
until the window is on screen: the button still builds, still sizes and still
carries its tooltip, it simply draws nothing. That is deliberate, so a missing
asset costs one control rather than taking the application down, which is
exactly why the failure has to be caught HERE instead.

These are pure filesystem and source checks, so they run without a
QApplication, matching the rest of the suite.
"""

from __future__ import annotations

import ast
from pathlib import Path

import generate_icons
from src.presentation.views import icons, theme, tray
from src.presentation.views.resource_paths import button_icon_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _icon_names_declared_by_the_ui() -> set[str]:
    """Every artwork name the application can ask for at runtime.

    Read from the two modules that hold them rather than listed again here,
    so a name added to the UI is covered by these tests automatically.
    """
    from_vocabulary = {
        value
        for name, value in vars(icons).items()
        if name.startswith("ICON_") and isinstance(value, str)
    }
    toggle_names = set(vars(theme)["_TOGGLE_ICON_NAMES"].values())
    return from_vocabulary | toggle_names


def test_every_icon_the_ui_names_resolves_to_a_file() -> None:
    """No button can be built around artwork that is not there."""
    missing = sorted(
        name
        for name in _icon_names_declared_by_the_ui()
        if not button_icon_path(name).is_file()
    )
    assert not missing, f"UI names artwork with no file behind it: {missing}"


def test_every_icon_the_ui_names_is_produced_by_the_generator() -> None:
    """A file present but not generated is one somebody dropped in by hand.

    That matters because such a file survives until the next clean checkout and
    then vanishes, so the check is against what `generate_icons.py` declares it
    will write rather than against the directory listing.
    """
    generated = set(generate_icons.BUTTON_MASTERS) | set(
        generate_icons.BUTTON_COMPOSITES
    )
    generated.add(Path(generate_icons.DONATE_NAME).stem)
    unaccounted = sorted(_icon_names_declared_by_the_ui() - generated)
    assert not unaccounted, f"artwork not produced by the generator: {unaccounted}"


def test_every_master_the_generator_reads_is_committed() -> None:
    """The generator's inputs are source, so a missing one is a broken build."""
    masters = set(generate_icons.BUTTON_MASTERS.values())
    masters |= set(generate_icons.BUTTON_COMPOSITES.values())
    masters.add(generate_icons.NEGATIVE_MASTER)
    missing = sorted(
        name for name in masters if not (generate_icons.MASTERS_DIR / name).is_file()
    )
    assert not missing, f"master artwork missing from assets/: {missing}"
    assert generate_icons.APP_ICON_MASTER.is_file()
    assert generate_icons.DONATE_MASTER.is_file()


def test_button_artwork_is_rendered_well_above_the_height_it_is_drawn_at() -> None:
    """The generator renders large so Qt only ever scales DOWN.

    Scaling up is what makes artwork look soft, so the rendered height has to
    stay a comfortable multiple of the height the tray actually draws it at.
    This is the seam between a build script and the UI: stating the
    relationship here means the generator never has to import PySide6.
    """
    minimum_ratio = 4
    assert generate_icons.BUTTON_RENDER_HEIGHT_PX >= minimum_ratio * tray.ICON_HEIGHT_PX


def test_the_masters_themselves_are_never_read_at_runtime() -> None:
    """Only the generated directory is resolved by the application.

    The masters are multi-megabyte source artwork sitting beside the output. A
    runtime read of one would work in development and then fail in a packaged
    build, because the build stages the generated directory alone.
    """
    views = PROJECT_ROOT / "src" / "presentation" / "views"
    offenders = []
    for source in views.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            text = node.value
            if text.startswith("assets/") and not text.startswith("assets/icons"):
                offenders.append(f"{source.name}: {text}")
    assert not offenders, f"runtime paths reaching outside the icon set: {offenders}"
