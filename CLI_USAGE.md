# AudioDeck CLI Usage Guide

How to use the AudioDeck command-line interface for automation and Stream Deck
integration.

## Quick reference

```bash
# List all profiles
AudioDeck.exe --list

# Switch to a profile
AudioDeck.exe --profile "Profile Name"

# Print the version
AudioDeck.exe --version

# Show help
AudioDeck.exe --help

# Open the GUI (no arguments)
AudioDeck.exe
```

When run with no arguments the GUI opens. When run with `--list` or `--profile`
it runs headless and returns a process exit code (0 on success, non-zero on
error).

## Getting started

### 1. Build the executable

```bash
python buildexe.py
```

The executable is created at `dist/AudioDeck.exe`.

### 2. Create profiles in the GUI

1. Run `AudioDeck.exe` with no arguments.
2. Go to the **Configuration** tab.
3. Create your audio profiles (for example "Gaming Setup" or "Work Calls").
4. Save each profile.

### 3. List your profiles

```bash
dist\AudioDeck.exe --list
```

Example output:

```
Available Audio Profiles:
==================================================
  • Gaming Setup (Output + Input)
  • Work Calls (Output + Input)
  • Music Production (Output)

To switch to a profile, use:
  AudioDeck.exe --profile "PROFILE_NAME"

Example:
  AudioDeck.exe --profile "Gaming Setup"
```

### 4. Test profile switching

```bash
dist\AudioDeck.exe --profile "Gaming Setup"
```

Expected output:

```
Switching to profile "Gaming Setup"...
✓ Profile switched successfully!
  Changed: Output and Input device(s)
```

If a device in the profile is currently offline, its available device(s) are
still applied and the offline one is reported on standard error, for example:

```
Switching to profile "Gaming Setup"...
✓ Profile switched successfully!
  Changed: Output device(s)
Some devices were not available and were skipped:
  - Input (not available)
```

The exit code is 0 when at least one device is applied, and non-zero when none
are. In the GUI, an offline device is applied automatically when it reconnects.

## Stream Deck integration

### Create batch files

Create a `.bat` file for each profile:

```batch
@echo off
cd /d "C:\Path\To\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
```

Notes:

- Replace the path with your actual AudioDeck location.
- Use the exact profile name (case sensitive).
- Keep quotes around profile names that contain spaces.

### Use the example templates

Copy and modify the examples in `examples/streamdeck_profiles/`:

- `gaming_profile.bat`
- `work_profile.bat`
- `music_profile.bat`

### Set up the Stream Deck button

1. Open the Stream Deck software.
2. Add a **System > Open** action to a button.
3. Browse to your batch file.
4. Optionally add a custom icon and a title.
5. Press the button to test.

## Common issues

### Profile not found

Error: `Error: Profile "Gaming" not found.`

- Run `AudioDeck.exe --list` to see the exact names.
- Profile names are case sensitive.
- Check for typos or extra spaces.

### Path issues

Error: `'AudioDeck.exe' is not recognized...`

- Use the full path in the batch file, for example
  `C:\Path\To\AudioDeck\dist\AudioDeck.exe`.
- Or use `cd /d` to change to the correct directory first.

### A device was skipped

Message: `Some devices were not available and were skipped`

- The profile references a device that is currently disconnected.
- The available devices are still applied; the skipped one applies automatically
  when it reconnects (in the GUI), or run the command again once it is connected.
- To change the profile, open the GUI and edit it.

## Advanced usage

### Multiple profiles in one batch file

```batch
@echo off
REM Switch between profiles based on time of day
set hour=%time:~0,2%
if %hour% LSS 12 (
    AudioDeck.exe --profile "Morning Setup"
) else if %hour% LSS 18 (
    AudioDeck.exe --profile "Work Setup"
) else (
    AudioDeck.exe --profile "Evening Setup"
)
```

### Error handling in batch files

```batch
@echo off
cd /d "C:\Path\To\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
if errorlevel 1 (
    echo Failed to switch profile
    pause
)
```

### Silent mode (no console window)

To run a batch file without a visible console, use a small VBScript wrapper:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\Path\To\gaming.bat", 0, False
```

Then point Stream Deck at the `.vbs` file.

## Troubleshooting

### A console window appears briefly

This is expected. The console opens, switches the profile and closes.

### The GUI opens instead of switching

Make sure the batch file passes the `--profile` argument.

### Changes do not take effect

- Check the Windows Sound settings to verify the change.
- Some applications need to be restarted to pick up the new default.
- Try reconnecting the device.

## Support

- See `README.md` for the user documentation.
- See `DEVELOPMENT_README.md` for setup and build instructions.
- See `examples/streamdeck_profiles/` for working examples.
