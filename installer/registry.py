"""Per-user Add/Remove Programs registry entry for Audio Deck.

Writes and removes the HKCU uninstall key using the standard library only.
"""

from __future__ import annotations

import winreg
from pathlib import Path
from typing import Optional

from installer import constants as c
from installer.state import InstalledInfo


def read_installed_info() -> Optional[InstalledInfo]:
    """Read the existing installation details from the registry, if any.

    Returns:
        InstalledInfo when a valid install is found, otherwise None.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, c.UNINSTALL_REG_KEY) as key:
            version = _read_str(key, "DisplayVersion")
            location = _read_str(key, "InstallLocation")
    except FileNotFoundError:
        return None

    if not version or not location:
        return None
    if not (Path(location) / c.APP_EXE_NAME).exists():
        return None
    return InstalledInfo(version=version, location=location)


def _read_str(key: "winreg.HKEYType", name: str) -> str:
    """Read a string value from a registry key, or return an empty string."""
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return str(value)
    except FileNotFoundError:
        return ""


def write_uninstall_entry(
    install_path: Path,
    version: str,
    uninstaller_path: Path,
    icon_path: Path,
    estimated_size_kb: int,
) -> None:
    """Create the HKCU uninstall entry shown in Add/Remove Programs.

    Args:
        install_path: Directory the app is installed in.
        version: Installed version string.
        uninstaller_path: Path to the setup exe copied for uninstalling.
        icon_path: Path to the display icon.
        estimated_size_kb: Installed size in kilobytes.
    """
    uninstall_command = f'"{uninstaller_path}" {c.UNINSTALL_FLAG}'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, c.UNINSTALL_REG_KEY) as key:
        _set_str(key, "DisplayName", c.APP_DISPLAY_NAME)
        _set_str(key, "DisplayVersion", version)
        _set_str(key, "Publisher", c.APP_PUBLISHER)
        _set_str(key, "InstallLocation", str(install_path))
        _set_str(key, "UninstallString", uninstall_command)
        _set_str(key, "DisplayIcon", str(icon_path))
        _set_dword(key, "NoModify", 1)
        _set_dword(key, "NoRepair", 1)
        _set_dword(key, "EstimatedSize", estimated_size_kb)


def remove_uninstall_entry() -> None:
    """Delete the HKCU uninstall entry if it exists."""
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, c.UNINSTALL_REG_KEY)
    except FileNotFoundError:
        pass


def _set_str(key: "winreg.HKEYType", name: str, value: str) -> None:
    """Write a string value to a registry key."""
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _set_dword(key: "winreg.HKEYType", name: str, value: int) -> None:
    """Write a DWORD value to a registry key."""
    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
