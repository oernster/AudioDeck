# Using Audio Deck

Audio Deck saves named profiles. Each one pins a default output device and a
default input device; switching to it sets the system defaults in one click
or one command. Everything is stored locally as JSON: no account, no cloud and
no background service.

Every control in the window is a picture rather than a text label, so this page
is the key to them. Hover any button in the app to read the same thing as a
tooltip.

## The buttons along the top

In the order they appear. The first two choose the view; the ones after the
divider belong to whichever view you are in and change with it.

![](assets/icons/guide-quick-switch.png)
**Quick Switch.** Shows your saved profiles and is where you switch between
them.

![](assets/icons/guide-configuration.png)
**Configuration.** Where profiles are made, edited and deleted.

![](assets/icons/guide-switch.png)
**Switch.** Applies the selected profile to your devices. Double-clicking the
profile does the same thing.

![](assets/icons/guide-rescan.png)
**Rescan.** Looks at the audio devices again, now, rather than waiting for the
next automatic check.

![](assets/icons/guide-add-profile.png)
**New profile.** Starts a new profile and opens the editor on it.

![](assets/icons/guide-edit-profile.png)
**Edit profile.** Opens the selected profile in the editor.

![](assets/icons/guide-delete-profile.png)
**Delete profile.** Removes the selected profile. The bar struck through the
mark is the app's sign for undoing or removing something.

![](assets/icons/guide-save-profile.png)
**Save.** Keeps the changes in the editor.

![](assets/icons/guide-cancel-edit.png)
**Cancel.** Abandons the changes in the editor and closes it.

![](assets/icons/guide-donate.png)
**Donate.** Opens a payment page in your own browser. Audio Deck sends nothing
itself.

![](assets/icons/guide-light-mode.png)
![](assets/icons/guide-dark-mode.png)
**Light and dark.** Switches the appearance. The mark shows the mode it would
move to rather than the one you are in.

![](assets/icons/guide-help-info.png)
**Help.** The documentation, the two licences, the update check and this page.

The Rescan mark appears once more inside the Configuration editor, beside each
device list, where it reloads that list on the spot.

## Making a profile

Open **Configuration**, press **New profile**, give it a name, then choose an
output device, an input device or both. Press **Save**.

A device that is currently disconnected still appears, marked offline, so a
profile can be built around hardware that is switched off. That is deliberate:
it is how you set up a Bluetooth headset before turning it on.

## Switching

Open **Quick Switch**, select a profile and press **Switch**. Double-clicking it
does the same.

If one of the profile's devices is offline, the ones that are available are
applied anyway and the missing one is reported rather than failing the whole
switch. It is then applied on its own the moment it reconnects, so turning the
headset on finishes the job without you touching anything.

The device list refreshes when the system reports a change and periodically in
any case. **Rescan** forces it immediately.

## From the keyboard

Tab and the right arrow move forward through the controls; Shift and Tab
move back, as does the left arrow. Both wrap around. Enter or Space presses
whatever is focused. Nothing is focused when the window opens, so the first Tab is what
enters the ring.

A green outline marks the control you are on. A red outline means a control is
present but cannot be used yet, which usually means nothing is selected.

## From the command line

```
AudioDeck.exe --list           List all profiles
AudioDeck.exe --profile NAME   Switch to a profile by name
AudioDeck.exe --version        Print the version
```

Profile names are case sensitive; switching this way works while the window
is open. On Linux the command is `flatpak run uk.codecrafter.AudioDeck` and on
macOS it is `/Applications/AudioDeck.app/Contents/MacOS/AudioDeck`, with the
same arguments.

Elgato's Stream Deck integration is Windows only: point a button, for example
BarRaider's Advanced Launcher, at `AudioDeck.exe` with
`--profile "Profile Name"` as its arguments. Any other macro deck or macro
button on any operating system drives it the same way, because all of them are
running the same command.

## Where things are kept

```
Windows  %LOCALAPPDATA%\AudioDeck\profiles.json
Linux    ~/.local/share/audiodeck/profiles.json  (or under $XDG_DATA_HOME)
macOS    ~/Library/Application Support/AudioDeck/profiles.json
```

Back up that file to keep your profiles.

## If something looks wrong

- **An application still uses the old device.** Set that application to follow
  the system default rather than naming a device, so that changing the default
  reaches it.
- **Only some devices switched.** Expected when one of them is offline. It is
  applied on its own when it reconnects.
- **A second window will not open.** Deliberate: one window per user, because
  two would race over the same profiles file. The command line is exempt, so
  macro buttons keep working while the window is open.

## Supporting Audio Deck

Audio Deck is free and stays free. There is no paid tier, no licence key and no
feature held back behind a donation. The donate button opens a payment page in
your own browser; the application itself never contacts it.

Developer documentation, covering building, the architecture and the tests,
lives in the GitHub repository beside this file.
