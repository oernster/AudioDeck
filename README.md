# <img width="64" height="64" alt="Audio Deck icon" src="https://github.com/user-attachments/assets/0ee08d6a-0311-414b-8188-cf09a58c46b5" /> Audio Deck

A local-first audio device switcher for Windows, Linux and macOS, with a GUI,
a command-line interface and Stream Deck integration on Windows. Any macro
deck or macro buttons on any OS that can run a command work through the
command-line interface.

**Author:** Oliver Ernster

If you find it useful, you can [buy me a coffee](https://www.paypal.com/ncp/payment/Z36XJEEA4MNV6).

## What it is

Audio Deck saves named profiles that each pin a default output device and a
default input device, then switches the system default devices to a profile in
one click or one command. Profiles are stored locally as JSON; there is no
account, no cloud and no background service.

The one thing Audio Deck asks the network is whether a newer release exists:
one anonymous call to GitHub's releases API shortly after launch and once a day
while the window is open. It carries no identifier and nothing about your
profiles; a failed check is silent.

## Who it is for

- Anyone who regularly moves between audio setups (speakers for music,
  a headset for calls, an interface for recording) and wants fast switching.
- Streamers and gamers who own an Elgato Stream Deck (Windows) or any macro
  deck or macro buttons that can run a command (any OS) and want a physical
  button per setup.
- Remote workers who switch between a meeting headset and desk speakers.

## Who it is not for

- Anyone needing per-application audio routing. Audio Deck sets the system
  default input and output devices; it does not route individual apps to
  different devices.
- Anyone needing mixing, effects or virtual audio cables. Audio Deck only
  selects existing physical or virtual endpoints the operating system already
  exposes.
- Linux users on bare ALSA. The Linux backend speaks the PulseAudio protocol,
  which covers PulseAudio and PipeWire desktops; a system with neither is not
  supported.

## Capabilities

- Quick switching between saved audio profiles.
- A GUI for creating, editing and deleting profiles.
- A command-line interface for automation and Stream Deck.
- Selecting devices that are not connected yet (for example a Bluetooth headset
  that is currently off), which are applied automatically when they reconnect.
- Partial switching: the available devices in a profile are applied even if one
  is currently missing; the missing one is reported.
- Automatic and on-demand rescanning of devices, with offline devices marked.
- A single window per user: launching Audio Deck again while the window is open
  starts no second copy. On Windows the existing window is brought to the
  front; on Linux and macOS the second launch simply exits, because neither
  platform lets one process reliably raise another's window. Command-line
  switching is not restricted, so Stream Deck buttons keep working while the
  window is open.
- An update check against GitHub's releases API: shortly after launch, daily
  while running and on demand from the Help menu, prompting with Download,
  Skip This Version and Later. Only a published release can prompt, a skipped
  version never prompts again and an unreachable network is silent; the manual
  check reports every outcome and ignores the skip.
- Profiles persisted locally with no external dependencies.

## Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.10+ |
| GUI | PySide6 (Qt for Python) |
| Audio API (Windows) | pycaw with comtypes (Windows Core Audio) |
| Audio API (Linux) | pactl (PulseAudio/PipeWire), no extra Python dependency |
| Audio API (macOS) | CoreAudio via ctypes, no extra Python dependency |
| Persistence | JSON file in the platform's per-user app-data directory |
| Packaging | PyInstaller (Windows, macOS), Flatpak (Linux) |
| Tests | pytest with coverage |

## Requirements

- Windows 10 or Windows 11; a Linux desktop running PulseAudio or PipeWire
  (Ubuntu and every mainstream distribution); or macOS on Apple Silicon.
- An Elgato Stream Deck is optional and its integration is Windows only;
  other macro decks and macro buttons work on any OS through the command
  line.

## Installation

On Windows, two options, both per user and neither needing admin rights.

### Installer (recommended, Windows)

1. Download `AudioDeckSetup.exe` from the releases page.
2. Run it and choose Install.
3. It installs to `%LOCALAPPDATA%\Programs\AudioDeck`, offers Desktop and Start
   Menu shortcuts and registers an entry in Add or Remove Programs.

Running the same setup again on an installed copy offers Update, Reinstall,
Repair and Uninstall, chosen from the version it finds.

### Portable (Windows)

1. Download the standalone `AudioDeck.exe` from the releases page.
2. Place it in any folder.
3. Run it. Nothing is installed and no registry entry is written.

Both builds read and write the same profiles file, so you can move between them.

### Linux (Flatpak)

1. Download `audiodeck.flatpak` from the releases page.
2. Install it:
   ```
   flatpak install --user audiodeck.flatpak
   ```
3. Launch Audio Deck from your desktop's app grid or run
   `flatpak run uk.codecrafter.AudioDeck`.

### macOS (DMG)

1. Download `audiodeck-macos-arm64.dmg` from the releases page.
2. Open it and drag Audio Deck into Applications.

The DMG is signed and notarised, so Gatekeeper opens it without warnings.

## Quick start

### Create a profile

1. Open `AudioDeck.exe`.
2. Open the **Configuration** view (the gear icon).
3. Press **➕ New profile** in the header tray.
4. Name the profile (for example "Gaming Setup").
5. Select an output device and an input device.
6. Press **💾 Save**.

### Switch profiles

1. Open the **Quick Switch** view (the arrows icon).
2. Select a profile.
3. Press **▶️ Switch** in the header tray or double-click the profile.

A profile whose device is currently offline is marked in the list. Switching to
it applies whatever devices are available now; a device that is off is applied
automatically the moment it reconnects (for example when you turn on a Bluetooth
headset). The device list rescans on device changes and periodically; the
**📡 Rescan** tray button forces an immediate rescan.

## Stream Deck integration (Windows)

Elgato's Stream Deck software is Windows-focused here; on other platforms
any macro deck or macro buttons that can run a command drive Audio Deck the
same way, through the command line below.

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

Profiles are stored per platform at:

```
Windows  %LOCALAPPDATA%\AudioDeck\profiles.json
Linux    ~/.local/share/audiodeck/profiles.json  (or under $XDG_DATA_HOME)
macOS    ~/Library/Application Support/AudioDeck/profiles.json
```

Back up this file to keep your profiles.

The update check keeps its one setting (a skipped version, if you chose one)
beside the profiles in `update_settings.json`. Losing it costs nothing but one
extra prompt after the next release.

## Building from source

Windows:

```powershell
pip install -r requirements.txt
python buildexe.py
python buildinstaller.py
```

`buildexe.py` writes the portable executable to `dist/AudioDeck.exe`.
`buildinstaller.py` wraps that build into `dist-installer/AudioDeckSetup.exe`,
so run it after `buildexe.py`.

Linux (needs flatpak and flatpak-builder):

```
./build_flatpak.sh
```

writes `audiodeck.flatpak`; `./cleanup_flatpak.sh` removes the Flatpak build
artefacts and nothing else.

macOS (notarisation reads the `AudioDeck` notarytool keychain profile, stored
once with `xcrun notarytool store-credentials AudioDeck`; `APPLE_ID` and
`APPLE_APP_PASSWORD` in the environment override it):

```
python builddmg.py
```

writes `AudioDeck.dmg` in the repo root, signed, notarised and stapled. The
build fails rather than emit an unnotarised image; `SKIP_NOTARIZE=1` opts out
for a local test build.

## Documentation

This README covers using Audio Deck. The rest is split by audience.

| Document | What it covers |
| --- | --- |
| [DOCUMENTATION.md](DOCUMENTATION.md) | The succinct user guide, also shown by Help > View Documentation in the app |
| [DEVELOPMENT_README.md](DEVELOPMENT_README.md) | Developer notes: setup, running from source, the build, workflow, code style and releasing |
| [CLI_USAGE.md](CLI_USAGE.md) | The command-line surface in depth, with batch-file recipes for Stream Deck |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The design, the layers, the dependency direction and the enforced invariants |
| [TESTING.md](TESTING.md) | How to run the tests, what the coverage gate measures and what it excludes |
| [TECH_DEBT.md](TECH_DEBT.md) | What is still open, what is deliberately left and what only looks like debt |

## Troubleshooting

### Applications still use the old device

Set each application to use the Windows default device for input and output, so
that switching the default takes effect. For example, in Discord set
Settings > Voice & Video to "Default"; in Spotify set the output device to
"Default".

### A device is missing

Disconnected devices still appear in the Configuration view marked as offline, so
you can build profiles around them. To use one now, connect and enable it; Audio
Deck picks it up automatically, though **Refresh Devices** forces it.

### A profile only switched some devices

This is expected when one of the profile's devices is currently offline. The
available device is applied and the offline one is reported. It is applied
automatically when it reconnects; switching again once it is connected also
works.

### Audio Deck will not open a second window

This is deliberate. Only one window may be open per user, because two windows
editing the same profiles file would conflict. On Windows, launching it again
brings the window you already have to the front; on Linux and macOS the second
launch exits quietly. Command-line switching is exempt, so `--profile` and
`--list` still run as often as you like.

### A Stream Deck button does nothing

Run the batch file manually to read the error, confirm the path to
`AudioDeck.exe` and verify the profile name with `--list`.

## License

Distributed under two licences, split by component: the backend (domain,
application, infrastructure and CLI layers) under
[GPL-3.0](LICENSE-GPL-3.0.txt) and the PySide6 user interface
(`src/presentation`) under [LGPL-3.0](LICENSE-LGPL-3.0.txt), aligning with
Qt's own licensing. See [LICENSE](LICENSE) for the map; the running
application shows both under Help.

Copyright (C) 2024-2026 Oliver Ernster.

## Credits

- Built with PySide6 (Qt for Python).
- Uses pycaw for the Windows Core Audio API, pactl for PulseAudio/PipeWire on
  Linux and CoreAudio on macOS.
- Packaged with PyInstaller and Flatpak.
