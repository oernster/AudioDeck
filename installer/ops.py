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
from typing import Callable, Optional

from installer import constants as c
from installer import registry, shortcuts
from installer.state import Operation

# Progress callback: (percent, message).
ProgressCallback = Callable[[int, str], None]

_CREATE_NO_WINDOW = 0x08000000
_HASH_CHUNK = 65536
_PCT_START = 5
_PCT_EXTRACTED = 55
_PCT_UNINSTALLER = 70
_PCT_REGISTRY = 80
_PCT_SHORTCUTS = 95
_PCT_DONE = 100

# Operations that deploy the full payload.
_FULL_DEPLOY = frozenset({Operation.INSTALL, Operation.UPGRADE, Operation.REINSTALL})


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


def run(
    operation: Operation,
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Optional[Path]:
    """Run the requested operation.

    Args:
        operation: The operation to perform.
        create_desktop: Whether to create or restore a Desktop shortcut.
        create_start_menu: Whether to create or restore a Start Menu shortcut.
        progress: Callback receiving (percent, message).

    Returns:
        The installed executable path for deploy and repair operations, or None
        for uninstall.
    """
    if operation == Operation.UNINSTALL:
        _uninstall(progress)
        return None
    if operation == Operation.REPAIR:
        return _repair(create_desktop, create_start_menu, progress)
    return _deploy(operation, create_desktop, create_start_menu, progress)


def _deploy(
    operation: Operation,
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Path:
    """Fully extract the payload (install, upgrade or reinstall)."""
    target = c.install_dir()
    manifest = _manifest()

    progress(_PCT_START, f"{operation.value} starting...")
    target.mkdir(parents=True, exist_ok=True)

    progress(_PCT_START, "Extracting files...")
    with zipfile.ZipFile(_payload_zip(), "r") as archive:
        archive.extractall(target)
    progress(_PCT_EXTRACTED, "Files extracted.")

    return _finalise(target, manifest, create_desktop, create_start_menu, progress)


def _repair(
    create_desktop: bool,
    create_start_menu: bool,
    progress: ProgressCallback,
) -> Path:
    """Restore only missing or corrupted files, verified by hash."""
    target = c.install_dir()
    manifest = _manifest()

    progress(_PCT_START, "Verifying files...")
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(_payload_zip(), "r") as archive:
        for entry in manifest["files"]:
            name = entry["name"]
            installed = target / name
            if not installed.exists() or _sha256(installed) != entry["sha256"]:
                archive.extract(name, target)
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

    progress(_PCT_DONE, "Done.")
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


def _uninstall(progress: ProgressCallback) -> None:
    """Remove shortcuts and the registry entry, then delete the install tree."""
    progress(_PCT_START, "Removing shortcuts...")
    shortcuts.remove_shortcut(shortcuts.desktop_shortcut_path())
    shortcuts.remove_shortcut(shortcuts.start_menu_shortcut_path())

    progress(_PCT_REGISTRY, "Removing registry entry...")
    registry.remove_uninstall_entry()

    progress(_PCT_SHORTCUTS, "Removing files...")
    _schedule_self_delete(c.install_dir())
    progress(_PCT_DONE, "Uninstall complete.")


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
