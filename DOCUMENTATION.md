# Using Audio Deck

Audio Deck saves named profiles that each pin a default output device and a
default input device, then switches the system defaults to a profile in one
click or one command. Profiles are stored locally as JSON; there is no
account, no cloud and no background service.

## Create a profile

1. Open the **Configuration** view (the gear icon).
2. Press **➕ New profile**.
3. Name the profile, then select an output device, an input device or both.
4. Press **💾 Save**.

A device that is currently disconnected still appears, marked offline, so
profiles can be built around it.

## Switch profiles

1. Open the **Quick Switch** view (the arrows icon).
2. Select a profile.
3. Press **▶️ Switch** or double-click the profile.

A profile with an offline device switches whatever is available now; the
missing device is applied automatically the moment it reconnects (for
example when a Bluetooth headset is turned on). Devices rescan on change
and periodically; **📡 Rescan** forces it.

## Stream Deck (Windows) and the command line

```
AudioDeck.exe --list           List all profiles
AudioDeck.exe --profile NAME   Switch to a profile by name
AudioDeck.exe --version        Print the version
```

Elgato Stream Deck integration applies to Windows only; that said, any
macro deck or macro buttons on any OS that can run a command work the
same way through the command line. Point a button (for example BarRaider's Advanced
Launcher on a Stream Deck) at `AudioDeck.exe` with
`--profile "Profile Name"` as the arguments. Profile names are case
sensitive. Command-line switching works while the window is open.

## Where profiles live

```
Windows  %LOCALAPPDATA%\AudioDeck\profiles.json
Linux    ~/.local/share/audiodeck/profiles.json  (or under $XDG_DATA_HOME)
macOS    ~/Library/Application Support/AudioDeck/profiles.json
```

Back up this file to keep your profiles.

## Troubleshooting

- **Applications still use the old device:** set each application to follow
  the system default device, so switching the default takes effect.
- **A profile only switched some devices:** expected when a device is
  offline; it is applied when it reconnects.
- **A second window will not open:** deliberate, one window per user. The
  command line is exempt, so Stream Deck buttons keep working.

Developer documentation (building, architecture, testing) lives in the
GitHub repository beside this file.
