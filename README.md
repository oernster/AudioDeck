# Audio Deck

**A professional audio device switcher for Windows
with Stream Deck integration.**

**Author:** Oliver Ernster
**Version:** 1.0.1

---

## What is Audio Deck?

Audio Deck lets you instantly switch between different audio setups with a single click. Perfect for:
- 🎮 **Gamers** - Switch between gaming headset and speakers
- 💼 **Remote Workers** - Quick switch to meeting microphone and headphones
- 🎵 **Content Creators** - Change audio setups for recording vs. streaming
- 🎛️ **Stream Deck Users** - Control audio profiles from your Stream Deck buttons

## Features

✅ **Quick Profile Switching** - Change audio devices instantly  
✅ **Stream Deck Integration** - Control from your Elgato Stream Deck  
✅ **Command-Line Support** - Automate with scripts and macros  
✅ **Easy Configuration** - Simple GUI for creating profiles  
✅ **Persistent Profiles** - Your setups are saved and ready to use

## Requirements

- Windows 10 or Windows 11
- Elgato Stream Deck (optional, for button control)

## Installation

1. **Download** the latest `AudioDeck.exe` from the releases page
2. **Extract** to a folder of your choice
3. **Run** `AudioDeck.exe` to start

That's it! No installation required.

## Quick Start

### Step 1: Create Your First Profile

1. Launch `AudioDeck.exe`
2. Go to the **Configuration** tab
3. Click **New Profile**
4. Enter a name (e.g., "Gaming Setup")
5. Select your output device (speakers/headphones)
6. Select your input device (microphone)
7. Click **Save Profile**

### Step 2: Switch Profiles

1. Go to the **Quick Switch** tab
2. Select a profile from the list
3. Click **Switch to Selected Profile**
4. Your audio devices change instantly!

**Tip:** Double-click a profile for even faster switching!

## Stream Deck Integration

Want to switch audio profiles with a button press? Here's how:

### Recommended: Using Advanced Launcher Plugin

**The easiest way** to integrate AudioDeck with Stream Deck is using BarRaider's **Advanced Launcher** plugin:

1. **Install Advanced Launcher**:
   - Open Stream Deck software
   - Go to the Stream Deck Store (marketplace)
   - Search for "Advanced Launcher" by BarRaider
   - Click Install

2. **List your profiles** to see their exact names:
   ```
   AudioDeck.exe --list
   ```

3. **Configure a Stream Deck button**:
   - Drag "Advanced Launcher" action to a button
   - **Application**: Browse to `AudioDeck.exe`
   - **Arguments**: `--profile "Gaming Setup"` (use your exact profile name)
   - Add a custom icon
   - Press the button to switch instantly!

**Benefits of Advanced Launcher:**
- ✅ No batch files needed
- ✅ Cleaner setup
- ✅ Better error handling
- ✅ More configuration options

### Alternative: Using Batch Files

If you prefer batch files or don't want to install plugins:

1. **Create a batch file** for each profile (e.g., `gaming.bat`):
   ```batch
   @echo off
   cd /d "C:\Path\To\AudioDeck"
   AudioDeck.exe --profile "Gaming Setup"
   ```

2. **Configure Stream Deck**:
   - Add a "System > Open" action
   - Browse to your batch file
   - Add a custom icon
   - Press the button to switch!

**Example batch files** are included in the `examples/streamdeck_profiles/` folder.

## Command-Line Usage

AudioDeck can be controlled from the command line:

```bash
# List all profiles
AudioDeck.exe --list

# Switch to a specific profile
AudioDeck.exe --profile "Gaming Setup"

# Show help
AudioDeck.exe --help
```

**Note:** Profile names are case-sensitive. Use the exact name shown in the GUI or `--list` command.

## Troubleshooting

### Audio devices not showing up
- Make sure your devices are connected and enabled in Windows Sound settings
- Click the 🔄 refresh button in AudioDeck
- Try unplugging and replugging the device

### Profile won't switch
- Check that the devices in the profile still exist
- Make sure devices are enabled in Windows
- Try recreating the profile with current devices

### Stream Deck button doesn't work
- Test the batch file by double-clicking it manually
- Verify the path to `AudioDeck.exe` is correct
- Make sure the profile name matches exactly (case-sensitive)
- Run `AudioDeck.exe --list` to see exact profile names

### Console window appears briefly
- This is normal when using CLI mode
- The window closes automatically after switching
- For GUI mode, the console stays open (this is intentional to support CLI features)

## Getting Help

- **In-App Documentation**: Select **Help > View Documentation** from the menu
- **Developer Documentation**: Select **Help > Development Documentation** for technical details

## Configuration

Your profiles are stored in:
```
%LOCALAPPDATA%\AudioDeck\profiles.json
```

You can back up this file to save your profiles.

## Credits

- **Author:** Oliver Ernster
- Built with PySide6 (Qt for Python)
- Uses pycaw for Windows Core Audio API
- Packaged with PyInstaller

---

**Enjoy seamless audio switching! 🎧**