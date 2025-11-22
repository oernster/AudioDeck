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

AudioDeck now supports **direct profile switching** from Stream Deck! You can create buttons that instantly switch to specific profiles without opening the GUI.

### Quick Setup (Recommended Method)

#### Step 1: Build the Executable
```bash
python build_exe.py
```

#### Step 2: Get Your Profile Names
Run the executable with the `--list` flag to see all your profiles:
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

**Important:** Note the exact profile names (case-sensitive!)

#### Step 3: Create Batch Files

Create a `.bat` file for each profile (e.g., `gaming.bat`):
```batch
@echo off
cd /d "C:\Users\YourName\Development\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
```

Replace:
- `C:\Users\YourName\Development\AudioDeck\dist` with your actual path
- `"Gaming Setup"` with your exact profile name

**Example batch files** are in `examples/streamdeck_profiles/`

#### Step 4: Configure Stream Deck

For each profile you want to control:

1. Open **Stream Deck** software
2. Drag a **System > Open** action to a button
3. Click the button to configure it
4. Browse to your batch file (e.g., `gaming.bat`)
5. (Optional) Add a custom icon:
   - Click the icon area
   - Choose an image or icon
   - Adjust as needed
6. (Optional) Add a title (e.g., "Gaming Audio")

#### Step 5: Test It!

Press the Stream Deck button - your audio devices should switch instantly!

### Alternative: GUI Launcher

To open the AudioDeck GUI from Stream Deck:

1. In Stream Deck software, add a **System > Open** action
2. Browse to `dist/AudioDeck.exe` (without any arguments)
3. This will open the full GUI for manual profile management

## Troubleshooting

### "No devices found"
- Ensure audio devices are connected and enabled in Windows
- Click the 🔄 refresh button
- Check Windows Sound settings

### "Profile not switching"
- Verify devices still exist in Windows
- Try recreating the profile
- Check Windows permissions

### Stream Deck button doesn't work

**Test the batch file manually first:**
1. Navigate to your batch file location
2. Double-click the `.bat` file
3. Watch for any error messages in the console window

**Common issues:**

1. **"Profile not found" error**
   - Run `AudioDeck.exe --list` to see exact profile names
   - Profile names are **case-sensitive**
   - Check for extra spaces or typos

2. **"AudioDeck.exe not found" error**
   - Verify the path in your batch file is correct
   - Make sure you built the executable: `python build_exe.py`
   - Use full paths in batch files (e.g., `C:\Path\To\AudioDeck\dist`)

3. **Console window flashes but nothing happens**
   - The profile might not exist anymore
   - Devices in the profile might be disconnected
   - Run the batch file manually to see the error message

4. **Wrong profile switches**
   - Check the profile name in the batch file matches exactly
   - Profile names are case-sensitive: "Gaming" ≠ "gaming"

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

### GUI Tips
- **Double-click** profiles in Quick Switch mode for faster switching
- Use **descriptive names** for profiles (e.g., "Gaming Setup", "Work Calls")
- Create profiles for different scenarios (gaming, meetings, music production)
- The 🔄 button refreshes device lists if you plug in new devices

### Stream Deck Tips
- Create a **dedicated folder** in Stream Deck for all your audio profiles
- Use **clear icons** for each profile (microphone for input, speaker for output)
- Add **profile names** as button titles for easy identification
- Test each button after setup to ensure it works correctly
- Keep batch files in a **dedicated folder** for easy management

### Profile Naming Tips
- Use **simple, clear names** without special characters
- Avoid names that are too long (they may be truncated in CLI output)
- Be consistent with capitalization (e.g., always use "Gaming" not "gaming")
- Consider using emojis in GUI but stick to plain text for CLI compatibility

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