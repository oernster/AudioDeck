# Audio Deck - Quick Start Guide

## Installation & Setup

### 1. Install Dependencies

```bash
# Activate virtual environment (if not already activated)
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Run from Source

```bash
# Make sure you're in the AudioDeck directory
python src/main.py
```

**Note**: The application will launch a GUI window. Close it normally or press Ctrl+C in the terminal.

### 3. Build Executable

```bash
python build_exe.py
```

The executable will be created in `dist/AudioDeck.exe`

## Usage

### Configuration Mode

1. Launch Audio Deck
2. Go to the **Configuration** tab
3. Click **New Profile**
4. Enter a profile name
5. Select output device (speakers/headphones)
6. Select input device (microphone)
7. Click **Save Profile**

### Quick Switch Mode

1. Go to the **Quick Switch** tab
2. Select a profile from the list
3. Click **Switch to Selected Profile** (or double-click the profile)
4. Your audio devices will instantly switch!

## Stream Deck Integration

### Method 1: Using Batch File

1. Build the executable: `python build_exe.py`
2. In Stream Deck software, add a **System > Open** action
3. Browse to `launch_audio_deck.bat`
4. Optionally add a custom icon

### Method 2: Direct Executable

1. Build the executable: `python build_exe.py`
2. In Stream Deck software, add a **System > Open** action
3. Browse to `dist/AudioDeck.exe`
4. Optionally add a custom icon

## Troubleshooting

### "No devices found"
- Ensure audio devices are connected and enabled in Windows
- Click the 🔄 refresh button
- Check Windows Sound settings

### "Profile not switching"
- Verify devices still exist in Windows
- Try recreating the profile
- Check Windows permissions

### Build errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning build cache: delete `build/` and `dist/` folders
- Reinstall PyInstaller: `pip install --upgrade pyinstaller`

## Project Structure

```
AudioDeck/
├── src/
│   ├── domain/              # Business logic
│   ├── application/         # Use cases
│   ├── infrastructure/      # Windows integration
│   ├── presentation/        # GUI
│   └── main.py             # Entry point
├── requirements.txt
├── build_exe.py
├── launch_audio_deck.bat
└── README.md
```

## Configuration File Location

Profiles are stored in:
```
%LOCALAPPDATA%\AudioDeck\profiles.json
```

## Tips

- **Double-click** profiles in Quick Switch mode for faster switching
- Use **descriptive names** for profiles (e.g., "Gaming Setup", "Work Calls")
- Create profiles for different scenarios (gaming, meetings, music production)
- The 🔄 button refreshes device lists if you plug in new devices

## Next Steps

1. Create your first profile
2. Test switching between profiles
3. Set up Stream Deck integration
4. Enjoy seamless audio switching!

## Support

For issues or questions, check:
- README.md for detailed documentation
- Windows Event Viewer for system errors
- Audio device settings in Windows