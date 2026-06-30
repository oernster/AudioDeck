# Audio Deck - Quick Start Guide

A short path from a clean checkout to a working build and a Stream Deck button.
For the design see [ARCHITECTURE.md](ARCHITECTURE.md); for deeper developer notes
see [DEVELOPMENT_README.md](DEVELOPMENT_README.md).

## Installation and setup

### 1. Install dependencies

```bash
# Activate the virtual environment if it is not already active
venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

### 2. Run from source

```bash
# From the AudioDeck directory
python src/main.py
```

The application opens a GUI window. Close it normally or press Ctrl+C in the
terminal.

### 3. Build the executable

```bash
python buildexe.py
```

The executable is created at `dist/AudioDeck.exe`.

## Usage

### Configuration mode

1. Launch Audio Deck.
2. Go to the **Configuration** tab.
3. Click **New Profile**.
4. Enter a profile name.
5. Select an output device (speakers or headphones).
6. Select an input device (microphone).
7. Click **Save Profile**.

### Quick switch mode

1. Go to the **Quick Switch** tab.
2. Select a profile from the list.
3. Click **Switch to Selected Profile**, or double-click the profile.

The audio devices switch immediately.

## Stream Deck integration

Audio Deck switches profiles directly from Stream Deck, so a button can change
your audio setup without opening the GUI.

### Recommended setup

#### Step 1: Build the executable

```bash
python buildexe.py
```

#### Step 2: List your profile names

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
```

Note the exact profile names, which are case sensitive.

#### Step 3: Create batch files

Create a `.bat` file for each profile (for example `gaming.bat`):

```batch
@echo off
cd /d "C:\Users\YourName\Development\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
```

Replace the path with your own and the profile name with your exact name. Example
batch files are in `examples/streamdeck_profiles/`.

#### Step 4: Configure Stream Deck

1. Open the Stream Deck software.
2. Drag a **System > Open** action onto a button.
3. Browse to your batch file (for example `gaming.bat`).
4. Optionally set a custom icon and a title.

#### Step 5: Test

Press the Stream Deck button and the audio devices switch.

### Alternative: GUI launcher

To open the GUI from Stream Deck, add a **System > Open** action pointing at
`dist/AudioDeck.exe` with no arguments.

## Troubleshooting

### No devices found

- Ensure devices are connected and enabled in Windows.
- Use the refresh control in Audio Deck.
- Check the Windows Sound settings.

### A profile only switched some devices

- This is expected when one device is offline. The available device is applied
  and the offline one is reported.
- It applies automatically when the device reconnects, or press **Refresh
  Devices** after connecting it.
- A profile with an offline device is marked in the Quick Switch list.

### Stream Deck button does nothing

Run the batch file manually first to read any error in the console, then check:

- **Profile not found**: run `AudioDeck.exe --list` for the exact names; names
  are case sensitive.
- **AudioDeck.exe not found**: verify the path in the batch file and that you
  built the executable with `python buildexe.py`.
- **Console flashes then nothing happens**: the profile may no longer exist or a
  device may be disconnected; run the batch file manually to see the message.
- **Wrong profile switches**: check the name in the batch file matches exactly
  ("Gaming" is not "gaming").

### Build errors

- Ensure dependencies are installed with `pip install -r requirements.txt`.
- Delete the `build/` and `dist/` folders to clear the cache.
- Reinstall PyInstaller with `pip install --upgrade pyinstaller`.

## Project structure

```
AudioDeck/
  src/
    domain/          Business logic
    application/     Use cases
    infrastructure/  Windows integration and storage
    presentation/    GUI
    cli/             Command-line interface
    main.py          Entry point
  examples/
  requirements.txt
  buildexe.py
  README.md
```

## Configuration file location

```
%LOCALAPPDATA%\AudioDeck\profiles.json
```

## Tips

### GUI

- Double-click a profile in Quick Switch for faster switching.
- Use descriptive names such as "Gaming Setup" or "Work Calls".
- You can select a device that is currently off (such as a Bluetooth headset); it
  is marked offline and is applied automatically when it reconnects.
- **Refresh Devices** forces an immediate rescan; the list also updates on device
  changes on its own.

### Stream Deck

- Keep all audio-profile batch files in one folder.
- Use clear icons (a microphone for input, a speaker for output).
- Add profile names as button titles.
- Test each button after setup.

### Profile naming

- Use simple, clear names without special characters.
- Keep names reasonably short so CLI output stays readable.
- Be consistent with capitalisation.
