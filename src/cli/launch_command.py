"""The command that runs Audio Deck from a shell, on each platform.

The CLI's own output tells the user what to type next, so it has to name the
command their platform actually has: a Windows install runs AudioDeck.exe; the
Flatpak runs through flatpak with its application id; the macOS bundle keeps
its executable inside the app. Printing AudioDeck.exe everywhere told a Linux
or macOS user to run a program they do not have.

The names come from the build scripts, the Flatpak's APP_ID in
build_flatpak.sh and the bundle name in builddmg.py, which a test holds them to.

Author: Oliver Ernster
"""

WINDOWS_COMMAND = "AudioDeck.exe"
MACOS_COMMAND = "/Applications/AudioDeck.app/Contents/MacOS/AudioDeck"
LINUX_COMMAND = "flatpak run uk.codecrafter.AudioDeck"

_COMMANDS = {"win32": WINDOWS_COMMAND, "darwin": MACOS_COMMAND}


def launch_command_for(platform: str) -> str:
    """Return the shell command for `platform`, a `sys.platform` value.

    Anything that is neither Windows nor macOS gets the Flatpak command, since
    the Flatpak is the only way Audio Deck ships for Linux.
    """
    return _COMMANDS.get(platform, LINUX_COMMAND)
