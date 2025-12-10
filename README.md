# Audio Deck

**A professional audio device switcher for Windows with Stream Deck integration.**

**Author:** Oliver Ernster  
**Version:** 1.0.1

### If you like it please buy me a coffee: [Donation link](https://www.paypal.com/ncp/payment/7XYN6DCYK24VY)

---

## Overview

Audio Deck allows you to switch between customized audio setups instantly. It’s ideal for gamers, remote workers, content creators, and Stream Deck users who want fast, reliable control over their audio environment.

## Features

- Quick profile switching  
- Stream Deck integration  
- Command-line support  
- Simple configuration through a GUI  
- Persistent profiles saved locally

## Requirements

- Windows 10 or Windows 11  
- Elgato Stream Deck (optional)

## Installation

1. Download the latest `AudioDeck.exe` from the releases page.  
2. Extract it to any folder.  
3. Run `AudioDeck.exe`.

No installation required.

## Quick Start

### Create Your First Profile

1. Open `AudioDeck.exe`.  
2. Navigate to the **Configuration** tab.  
3. Click **New Profile**.  
4. Name your profile (e.g., "Gaming Setup").  
5. Select your output device.  
6. Select your input device.  
7. Click **Save Profile**.

### Switch Profiles

1. Open the **Quick Switch** tab.  
2. Choose a profile.  
3. Click **Switch to Selected Profile**.  

Double-click a profile for even faster switching.

## Stream Deck Integration

### Using the Advanced Launcher Plugin (Recommended)

1. Install BarRaider’s **Advanced Launcher** plugin from the Stream Deck Store.  
2. List available profiles:  
   ```
   AudioDeck.exe --list
   ```
3. Configure a Stream Deck button:  
   - **Application**: Select `AudioDeck.exe`  
   - **Arguments**: `--profile "Profile Name"`  

### Using Batch Files (Alternative)

1. Create a batch file like:  
   ```batch
   @echo off
   cd /d "C:\Path\To\AudioDeck"
   AudioDeck.exe --profile "Gaming Setup"
   ```
2. In Stream Deck, use the **Open** action to launch the batch file.

## Command-Line Usage

```bash
AudioDeck.exe --list         # List profiles
AudioDeck.exe --profile NAME # Switch to a profile
AudioDeck.exe --help         # Show help
```

Profile names are case-sensitive.

## Troubleshooting

### Application Audio Settings

Applications must use Windows’ default audio devices.  
Configure each application to use “Default” for both input and output.

Examples:  
- Discord: Settings → Voice & Video → Set devices to “Default”  
- Spotify: Settings → Audio → Output Device → “Default”

### Devices Not Showing

- Ensure devices are enabled in Windows Sound settings.  
- Refresh device list in Audio Deck.  
- Reconnect the device.

### Profile Not Switching

- Confirm the devices in the profile still exist.  
- Ensure devices are enabled.  
- Recreate the profile if needed.

### Stream Deck Button Issues

- Test batch files manually.  
- Confirm the application path.  
- Ensure the profile name matches exactly.  
- Use `--list` to verify names.

## Configuration File

Profiles are stored at:  
```
%LOCALAPPDATA%\AudioDeck\profiles.json
```

Backup this file to save your configuration.

## Credits

- **Author:** Oliver Ernster  
- Built with PySide6  
- Uses pycaw for Windows Core Audio API  
- Packaged with PyInstaller

---

Enjoy seamless audio switching!
