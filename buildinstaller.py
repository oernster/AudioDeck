"""Build the bespoke Audio Deck setup executable.

Stages the built app into an installer payload, then wraps the themed PySide6
installer into a single per-user ``AudioDeckSetup.exe`` with PyInstaller. Run
``buildexe.py`` first so ``dist/AudioDeck.exe`` exists.

Author: Oliver Ernster
"""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import PyInstaller.__main__

from installer import build_payload

PROJECT_ROOT = Path(__file__).resolve().parent

# Identity and inputs (no inline literals elsewhere).
SETUP_NAME = "AudioDeckSetup"
INSTALLER_ENTRY = PROJECT_ROOT / "installer" / "app.py"
ICON_FILE = PROJECT_ROOT / "assets" / "audiodeck.ico"
VERSION_FILE = PROJECT_ROOT / "VERSION"
LICENSE_FILE = PROJECT_ROOT / "LICENSE"
ASSETS_DIR = PROJECT_ROOT / "assets"
PAYLOAD_DIR = PROJECT_ROOT / "installer" / "payload"

# Build directories.
TEMP_DIST_DIR = PROJECT_ROOT / "dist-installer.build"
WORK_DIR = PROJECT_ROOT / "build" / "installer"
FINAL_DIST_DIR = PROJECT_ROOT / "dist-installer"

# Locked-file retry loop (antivirus or Explorer may briefly hold the exe).
RETRY_COUNT = 20
RETRY_DELAY_SECONDS = 0.15

# Windows separator for PyInstaller --add-data.
DATA_SEP = ";"


def _add_data(source: Path, dest: str) -> str:
    """Return a PyInstaller --add-data argument for the given source."""
    return f"--add-data={source}{DATA_SEP}{dest}"


def _move_with_retry(source: Path, dest: Path) -> None:
    """Move the built exe into place, retrying past transient file locks."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(RETRY_COUNT):
        try:
            if dest.exists():
                dest.unlink()
            shutil.move(str(source), str(dest))
            return
        except OSError:
            if attempt == RETRY_COUNT - 1:
                raise
            time.sleep(RETRY_DELAY_SECONDS)


def build_installer() -> None:
    """Stage the payload and build the setup executable."""
    print("Staging installer payload...")
    build_payload.build()

    payload_zip = PAYLOAD_DIR / "payload.zip"
    manifest = PAYLOAD_DIR / "manifest.json"
    if not payload_zip.exists() or not manifest.exists():
        print("Payload staging failed: payload.zip or manifest.json missing.")
        sys.exit(1)

    # Clean previous temp output.
    if TEMP_DIST_DIR.exists():
        shutil.rmtree(TEMP_DIST_DIR, ignore_errors=True)

    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={SETUP_NAME}",
        f"--icon={ICON_FILE}",
        f"--paths={PROJECT_ROOT}",
        f"--distpath={TEMP_DIST_DIR}",
        f"--workpath={WORK_DIR}",
        f"--specpath={WORK_DIR}",
        _add_data(payload_zip, "installer/payload"),
        _add_data(manifest, "installer/payload"),
        _add_data(VERSION_FILE, "."),
        _add_data(LICENSE_FILE, "."),
        _add_data(ASSETS_DIR, "assets"),
        "--hidden-import=installer.worker",
        "--hidden-import=installer.ops",
        "--hidden-import=installer.ui",
        "--hidden-import=installer.state",
        "--hidden-import=installer.registry",
        "--hidden-import=installer.shortcuts",
        "--hidden-import=installer.versioning",
        "--hidden-import=installer.theme",
        str(INSTALLER_ENTRY),
    ]

    print(f"Building {SETUP_NAME}.exe...")
    PyInstaller.__main__.run(args)

    built = TEMP_DIST_DIR / f"{SETUP_NAME}.exe"
    final = FINAL_DIST_DIR / f"{SETUP_NAME}.exe"
    _move_with_retry(built, final)
    shutil.rmtree(TEMP_DIST_DIR, ignore_errors=True)

    print("\nInstaller build complete.")
    print(f"Setup executable: {final}")


if __name__ == "__main__":
    build_installer()
