"""Install, upgrade, reinstall, repair and uninstall operations.

Pure operations with a progress callback, free of any Qt dependency so they can
be driven by the worker thread or called directly.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Callable

from installer import constants as c
from installer import registry, shortcuts

# Progress callback: (percent, message).
ProgressCallback = Callable[[int, str], None]

_CREATE_NO_WINDOW = 0x08000000
_HASH_CHUNK = 65536
_PCT_START = 5
_PCT_EXTRACTED = 55
_PCT_UNINSTALLER = 70
_PCT_REGISTRY = 80
_PCT_SHORTCUTS = 95
PCT_DONE = 100


class AppIsRunningError(RuntimeError):
    """Raised when a locked file shows the application is still running."""


def _locked_file_message() -> str:
    """Return a sentence the user can act on, rather than an errno and a path."""
    return (
        f"{c.APP_DISPLAY_NAME} is still running, so its files could not be "
        f"replaced. Close {c.APP_DISPLAY_NAME}, including its tray icon, then "
        "run this installer again."
    )


def extract_all(payload: Path, target: Path) -> None:
    """Extract the whole payload, reporting a locked file in plain words.

    Windows holds a running executable with an image mapping that denies
    write sharing, so this raises PermissionError on the first locked file.
    The setup program asks the user to close the app before it gets here, so
    reaching this means the app was started in between or the running check
    could not run at all. Either way an errno and a path tell the user
    nothing; the progress bar stopping at its first step is what made
    this look like a hang.

    Args:
        payload: The payload zip.
        target: The install directory.

    Raises:
        AppIsRunningError: A file could not be written.
    """
    try:
        with zipfile.ZipFile(payload, "r") as archive:
            archive.extractall(target)
    except PermissionError as error:
        raise AppIsRunningError(_locked_file_message()) from error


def extract_damaged(payload: Path, target: Path, manifest: dict) -> None:
    """Restore only the files that are missing or fail their hash.

    Args:
        payload: The payload zip.
        target: The install directory.
        manifest: The payload manifest, naming each file and its hash.

    Raises:
        AppIsRunningError: A file could not be written.
    """
    try:
        with zipfile.ZipFile(payload, "r") as archive:
            for entry in manifest["files"]:
                name = entry["name"]
                installed = target / name
                if not installed.exists() or _sha256(installed) != entry["sha256"]:
                    archive.extract(name, target)
    except PermissionError as error:
        raise AppIsRunningError(_locked_file_message()) from error


def _payload_zip() -> Path:
    """Return the bundled payload zip path."""
    return c.resource_path(f"installer/{c.PAYLOAD_DIR_NAME}/{c.PAYLOAD_ZIP_NAME}")


def _manifest() -> dict:
    """Load and return the bundled payload manifest."""
    manifest_path = c.resource_path(f"installer/{c.PAYLOAD_DIR_NAME}/{c.MANIFEST_NAME}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def payload_version() -> str:
    """Return the version recorded in the bundled payload manifest."""
    return _manifest()["version"]


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(_HASH_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _dir_size_kb(path: Path) -> int:
    """Return the total size of a directory tree in kilobytes."""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return max(1, total // c.BYTES_PER_KB)


def deploy(
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Path:
    """Write the whole payload: an install, an update, a downgrade or a reinstall.

    Args:
        create_desktop: Whether a Desktop shortcut is wanted.
        create_start_menu: Whether a Start Menu entry is wanted.
        progress: Callback receiving (percent, message).

    Returns:
        The installed executable.
    """
    target = c.install_dir()
    manifest = _manifest()

    progress(_PCT_START, "Starting...")
    target.mkdir(parents=True, exist_ok=True)

    progress(_PCT_START, "Extracting files...")
    extract_all(_payload_zip(), target)
    progress(_PCT_EXTRACTED, "Files extracted.")

    return _finalise(target, manifest, create_desktop, create_start_menu, progress)


def repair(
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Path:
    """Restore only the files that are missing or fail their hash.

    Args:
        create_desktop: Whether a Desktop shortcut is wanted.
        create_start_menu: Whether a Start Menu entry is wanted.
        progress: Callback receiving (percent, message).

    Returns:
        The installed executable.
    """
    target = c.install_dir()
    manifest = _manifest()

    progress(_PCT_START, "Verifying files...")
    target.mkdir(parents=True, exist_ok=True)
    extract_damaged(_payload_zip(), target, manifest)
    progress(_PCT_EXTRACTED, "Files verified.")

    return _finalise(target, manifest, create_desktop, create_start_menu, progress)


def _finalise(
    target: Path,
    manifest: dict,
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Path:
    """Register the uninstaller, write the registry entry and shortcuts."""
    exe_path = target / manifest["exe"]
    icon_path = target / manifest["icon"]

    uninstaller_path = _copy_uninstaller(target)
    progress(_PCT_UNINSTALLER, "Registering uninstaller...")

    registry.write_uninstall_entry(
        install_path=target,
        version=manifest["version"],
        uninstaller_path=uninstaller_path,
        icon_path=icon_path,
        estimated_size_kb=_dir_size_kb(target),
    )
    progress(_PCT_REGISTRY, "Creating shortcuts...")

    _apply_shortcut(
        create_desktop, shortcuts.desktop_shortcut_path(), exe_path, icon_path, target
    )
    _apply_shortcut(
        create_start_menu,
        shortcuts.start_menu_shortcut_path(),
        exe_path,
        icon_path,
        target,
    )

    progress(PCT_DONE, "Done.")
    return exe_path


def _apply_shortcut(
    wanted: bool,
    shortcut_path: Path,
    exe_path: Path,
    icon_path: Path,
    working_dir: Path,
) -> None:
    """Create a shortcut when wanted, otherwise remove any existing one."""
    if wanted:
        shortcuts.create_shortcut(shortcut_path, exe_path, icon_path, working_dir)
    else:
        shortcuts.remove_shortcut(shortcut_path)


def _copy_uninstaller(target: Path) -> Path:
    """Copy this setup exe into the install tree for later uninstalling."""
    uninstall_dir = target / c.UNINSTALL_SUBDIR
    uninstall_dir.mkdir(parents=True, exist_ok=True)
    uninstaller_path = uninstall_dir / c.INSTALLER_EXE_NAME
    # PyInstaller onefile: sys.executable is the real setup exe path.
    shutil.copy2(sys.executable, uninstaller_path)
    return uninstaller_path


def uninstall(progress: ProgressCallback) -> None:
    """Remove shortcuts and the registry entry, then delete the install tree.

    Args:
        progress: Callback receiving (percent, message).
    """
    progress(_PCT_START, "Removing shortcuts...")
    shortcuts.remove_shortcut(shortcuts.desktop_shortcut_path())
    shortcuts.remove_shortcut(shortcuts.start_menu_shortcut_path())

    progress(_PCT_REGISTRY, "Removing registry entry...")
    registry.remove_uninstall_entry()

    progress(_PCT_SHORTCUTS, "Removing files...")
    _schedule_self_delete(c.install_dir())
    progress(PCT_DONE, "Uninstall complete.")


def _schedule_self_delete(target: Path) -> None:
    """Spawn a detached process that deletes the install directory.

    The uninstaller runs from inside ``target``, so it cannot delete itself
    while running. A short detached command waits, then removes the tree.
    """
    delay = max(1, int(c.FILE_RETRY_COUNT * c.FILE_RETRY_DELAY_SECONDS))
    command = f'ping 127.0.0.1 -n {delay + 1} > nul & rmdir /s /q "{target}"'
    subprocess.Popen(
        ["cmd", "/c", command],
        creationflags=_CREATE_NO_WINDOW,
        close_fds=True,
    )


def launch(exe_path: Path) -> None:
    """Launch the installed application."""
    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent), close_fds=True)
