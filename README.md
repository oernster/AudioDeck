# <img width="64" height="64" alt="{9C57229E-4B80-4394-94CF-B15DB37A0A28}" src="https://github.com/user-attachments/assets/0ee08d6a-0311-414b-8188-cf09a58c46b5" /> Audio Deck

A local-first audio device switcher for Windows, with a GUI, a command-line
interface and Stream Deck integration.

**Author:** Oliver Ernster

If you find it useful, you can [buy me a coffee](https://www.paypal.com/ncp/payment/Z36XJEEA4MNV6).

## What it is

Audio Deck saves named profiles that each pin a default output device and a
default input device, then switches the Windows default devices to a profile in
one click or one command. Profiles are stored locally as JSON; there is no
account, no cloud and no background service.

## Who it is for

- Windows users who regularly move between audio setups (speakers for music,
  a headset for calls, an interface for recording) and want fast switching.
- Streamers and gamers who own an Elgato Stream Deck and want a physical button
  per setup.
- Remote workers who switch between a meeting headset and desk speakers.

## Who it is not for

- macOS or Linux users. Audio Deck uses the Windows Core Audio API and is
  Windows only.
- Anyone needing per-application audio routing. Audio Deck sets the system
  default input and output devices; it does not route individual apps to
  different devices.
- Anyone needing mixing, effects or virtual audio cables. Audio Deck only
  selects existing physical or virtual endpoints that Windows already exposes.

## Capabilities

- Quick switching between saved audio profiles.
- A GUI for creating, editing and deleting profiles.
- A command-line interface for automation and Stream Deck.
- Selecting devices that are not connected yet (for example a Bluetooth headset
  that is currently off), which are applied automatically when they reconnect.
- Partial switching: the available devices in a profile are applied even if one
  is currently missing, and the missing one is reported.
- Automatic and on-demand rescanning of devices, with offline devices marked.
- A single window per user: launching Audio Deck again brings the open window to
  the front instead of starting a second copy. Command-line switching is not
  restricted, so Stream Deck buttons keep working while the window is open.
- Check for updates from the Help menu.
- Profiles persisted locally with no external dependencies.

## Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.10+ |
| GUI | PySide6 (Qt for Python) |
| Audio API | pycaw with comtypes (Windows Core Audio) |
| Persistence | JSON file under `%LOCALAPPDATA%` |
| Packaging | PyInstaller |
| Tests | pytest with coverage |

## Requirements

- Windows 10 or Windows 11.
- An Elgato Stream Deck is optional.

## Installation

Two options, both per user and neither needing admin rights.

### Installer (recommended)

1. Download `AudioDeckSetup.exe` from the releases page.
2. Run it and choose Install.
3. It installs to `%LOCALAPPDATA%\Programs\AudioDeck`, offers Desktop and Start
   Menu shortcuts and registers an entry in Add or Remove Programs.

Running the same setup again on an installed copy offers Update, Reinstall,
Repair and Uninstall, chosen from the version it finds.

### Portable

1. Download the standalone `AudioDeck.exe` from the releases page.
2. Place it in any folder.
3. Run it. Nothing is installed and no registry entry is written.

Both builds read and write the same profiles file, so you can move between them.

## Quick start

### Create a profile

1. Open `AudioDeck.exe`.
2. Go to the **Configuration** tab.
3. Click **New Profile**.
4. Name the profile (for example "Gaming Setup").
5. Select an output device and an input device.
6. Click **Save Profile**.

### Switch profiles

1. Open the **Quick Switch** tab.
2. Select a profile.
3. Click **Switch to Selected Profile**, or double-click the profile.

A profile whose device is currently offline is marked in the list. Switching to
it applies whatever devices are available now; a device that is off is applied
automatically the moment it reconnects (for example when you turn on a Bluetooth
headset). The device list rescans on device changes and periodically, and the
**Refresh Devices** button forces an immediate rescan.

## Stream Deck integration

### Advanced Launcher plugin (recommended)

1. Install BarRaider's **Advanced Launcher** plugin from the Stream Deck store.
2. List the available profiles:
   ```
   AudioDeck.exe --list
   ```
3. Configure a Stream Deck button:
   - **Application**: `AudioDeck.exe`
   - **Arguments**: `--profile "Profile Name"`

### Batch files (alternative)

1. Create a batch file:
   ```batch
   @echo off
   cd /d "C:\Path\To\AudioDeck"
   AudioDeck.exe --profile "Gaming Setup"
   ```
2. In Stream Deck, use the **System > Open** action to launch the batch file.

Worked examples live in `examples/streamdeck_profiles/`.

## Command-line usage

```
AudioDeck.exe --list           List all profiles
AudioDeck.exe --profile NAME   Switch to a profile by name
AudioDeck.exe --version        Print the version
AudioDeck.exe --help           Show help
AudioDeck.exe                  Launch the GUI (no arguments)
```

Profile names are case sensitive.

## Configuration file

Profiles are stored at:

```
%LOCALAPPDATA%\AudioDeck\profiles.json
```

Back up this file to keep your profiles.

## Building from source

```powershell
pip install -r requirements.txt
python buildexe.py
python buildinstaller.py
```

`buildexe.py` writes the portable executable to `dist/AudioDeck.exe`.
`buildinstaller.py` wraps that build into `dist-installer/AudioDeckSetup.exe`,
so run it after `buildexe.py`.

## Documentation

This README covers using Audio Deck. The rest is split by audience.

| Document | What it covers |
| --- | --- |
| [DEVELOPMENT_QUICKSTART.md](DEVELOPMENT_QUICKSTART.md) | The short path from a clean checkout to a working build and a Stream Deck button |
| [DEVELOPMENT_README.md](DEVELOPMENT_README.md) | Fuller developer notes: setup, workflow, code style, releasing |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The design, the layers, the dependency direction and the enforced invariants |
| [TESTING.md](TESTING.md) | How to run the tests, what the coverage gate measures and what it excludes |

## Troubleshooting

### Applications still use the old device

Set each application to use the Windows default device for input and output, so
that switching the default takes effect. For example, in Discord set
Settings > Voice & Video to "Default", and in Spotify set the output device to
"Default".

### A device is missing

Disconnected devices still appear in the Configuration tab marked as offline, so
you can build profiles around them. To use one now, connect and enable it; Audio
Deck picks it up automatically, or you can press **Refresh Devices**.

### A profile only switched some devices

This is expected when one of the profile's devices is currently offline. The
available device is applied and the offline one is reported. It is applied
automatically when it reconnects, or you can switch again once it is connected.

### Audio Deck will not open a second window

This is deliberate. Only one window may be open per Windows user, because two
windows editing the same profiles file would conflict. Launching it again brings
the window you already have to the front. Command-line switching is exempt, so
`--profile` and `--list` still run as often as you like.

### A Stream Deck button does nothing

Run the batch file manually to read the error, confirm the path to
`AudioDeck.exe`, and verify the profile name with `--list`.

## License

GNU Lesser General Public License v3.0 (LGPL-3.0). See [LICENSE](LICENSE).

Copyright (C) 2024-2026 Oliver Ernster.

## Credits

- Built with PySide6 (Qt for Python).
- Uses pycaw for the Windows Core Audio API.
- Packaged with PyInstaller.
