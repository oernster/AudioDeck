"""Every file the running application reads is staged by every build.

The icon contract next door holds that a name the UI asks for resolves to a
file in the repository. That is a different question from whether the file
reaches the machine it is installed on: the Windows build, the Flatpak and the
DMG each stage the tree in their own way; a picture left out of one of them is
invisible until somebody opens the window on that platform.

So this reads the three delivery scripts and asserts each one carries the
generated icon directory and the documents the Help menu opens. Nothing here
runs a build: the Flatpak needs Linux and the DMG needs macOS, so the point is
to fail in the suite on Windows rather than in a release on somebody else's
computer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import builddmg
from src.presentation.views.resource_paths import (
    APP_ICON_ICO,
    APP_ICON_PNG,
    ICONS_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICONS_PATH = PROJECT_ROOT / ICONS_DIR

# Read at runtime by the Help menu and the guide, so a build that omits one
# ships a menu entry that opens an error box.
RUNTIME_DOCUMENTS = ("DOCUMENTATION.md", "LICENSE", "VERSION")

# The scripts that put the application on a machine. Each stages the tree in
# its own way, so each is read for the same set of names.
DELIVERY_SCRIPTS = ("buildexe.py", "build_flatpak.sh", "builddmg.py")


def _script(name: str) -> str:
    """The delivery script's source, as text."""
    return (PROJECT_ROOT / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", DELIVERY_SCRIPTS)
def test_every_build_stages_the_generated_icon_directory(name: str) -> None:
    """One directory carries every picture, so each build must carry it whole."""
    assert ICONS_DIR in _script(name), (
        f"{name} does not stage {ICONS_DIR}, so the build it produces draws "
        "no button artwork"
    )


@pytest.mark.parametrize("name", DELIVERY_SCRIPTS)
@pytest.mark.parametrize("document", RUNTIME_DOCUMENTS)
def test_every_build_stages_what_the_help_menu_opens(name: str, document: str) -> None:
    """The guide, the licence and the version are read from the bundle."""
    assert document in _script(name), f"{name} does not stage {document}"


def test_the_guide_only_draws_pictures_that_are_staged() -> None:
    """The in-app guide references its artwork by repository-relative path.

    Qt resolves those against the bundle root, so a picture outside the one
    staged directory renders as a broken image in the guide on every platform
    at once.
    """
    guide = (PROJECT_ROOT / "DOCUMENTATION.md").read_text(encoding="utf-8")
    referenced = {
        line.split("](", 1)[1].rstrip(")")
        for line in guide.splitlines()
        if line.startswith("![](")
    }

    assert referenced, "the guide's key to the buttons draws no artwork at all"
    outside = sorted(path for path in referenced if not path.startswith(ICONS_DIR))
    assert outside == [], f"the guide draws artwork the builds do not stage: {outside}"
    missing = sorted(path for path in referenced if not (PROJECT_ROOT / path).is_file())
    assert missing == [], f"the guide draws artwork that does not exist: {missing}"


def test_the_macos_bundle_carries_the_documents_and_the_icons() -> None:
    """Read from the DMG script's own values rather than from its text."""
    assert builddmg.ASSETS_DIR == ICONS_PATH
    staged = {path.name for path in builddmg.DOC_FILES}
    assert "DOCUMENTATION.md" in staged
    assert {"LICENSE-GPL-3.0.txt", "LICENSE-LGPL-3.0.txt"} <= staged


def test_the_macos_icns_is_assembled_from_the_generated_set() -> None:
    """Every size iconutil is given must already exist, never be resampled."""
    missing = sorted(
        f"audiodeck_icon_{size}.png"
        for _entry, size in builddmg.ICONSET_ENTRIES
        if not (ICONS_PATH / f"audiodeck_icon_{size}.png").is_file()
    )

    assert (
        missing == []
    ), f"the DMG icon build reads sizes that are not generated: {missing}"


@pytest.mark.parametrize("asset", (APP_ICON_PNG, APP_ICON_ICO))
def test_the_window_icon_the_application_names_is_in_that_directory(asset: str) -> None:
    """The window, the dialogs and the shortcuts all read these two."""
    assert asset.startswith(ICONS_DIR)
    assert (PROJECT_ROOT / asset).is_file()
