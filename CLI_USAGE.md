# AudioDeck CLI Usage Guide

This guide explains how to use AudioDeck's command-line interface for Stream Deck integration.

## Quick Reference

```bash
# List all profiles
AudioDeck.exe --list

# Switch to a profile
AudioDeck.exe --profile "Profile Name"

# Show help
AudioDeck.exe --help

# Show version
AudioDeck.exe --version

# Open GUI (no arguments)
AudioDeck.exe
```

## Getting Started

### 1. Build the Executable

```bash
python build_exe.py
```

The executable will be in `dist/AudioDeck.exe`

### 2. Create Profiles in GUI

1. Run `AudioDeck.exe` (without arguments)
2. Go to the **Configuration** tab
3. Create your audio profiles (e.g., "Gaming Setup", "Work Calls")
4. Save each profile

### 3. List Your Profiles

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

### 4. Test Profile Switching

```bash
dist\AudioDeck.exe --profile "Gaming Setup"
```

Expected output:
```
Switching to profile "Gaming Setup"...
✓ Profile switched successfully!
  Changed: Output and Input devices
```

## Stream Deck Integration

### Creating Batch Files

Create a `.bat` file for each profile:

**Example: gaming.bat**
```batch
@echo off
cd /d "C:\Path\To\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
```

**Important:**
- Replace the path with your actual AudioDeck location
- Use the exact profile name (case-sensitive)
- Keep quotes around profile names with spaces

### Method 3: Use Example Templates

Copy and modify the examples in `examples/streamdeck_profiles/`:
- `gaming_profile.bat`
- `work_profile.bat`
- `music_profile.bat`

## Stream Deck Setup

1. Open **Stream Deck** software
2. Add a **System > Open** action to a button
3. Browse to your batch file
4. (Optional) Add a custom icon
5. (Optional) Add a title
6. Press the button to test!

## Common Issues

### Profile Not Found

**Error:** `Error: Profile "Gaming" not found.`

**Solution:**
1. Run `AudioDeck.exe --list` to see exact names
2. Profile names are case-sensitive
3. Check for typos or extra spaces

### Path Issues

**Error:** `'AudioDeck.exe' is not recognized...`

**Solution:**
1. Use full path in batch file: `C:\Path\To\AudioDeck\dist\AudioDeck.exe`
2. Or use `cd /d` to change to the correct directory first

### Device Not Found

**Error:** `Error: Device not found`

**Solution:**
1. The profile references a device that's disconnected
2. Open AudioDeck GUI and update the profile
3. Ensure all devices are connected and enabled in Windows

## Tips

### Profile Naming
- Use simple, clear names
- Avoid special characters
- Be consistent with capitalization
- Keep names reasonably short

### Batch File Organization
- Create a dedicated folder for all batch files
- Name batch files clearly (e.g., `gaming_audio.bat`)
- Keep batch files with your AudioDeck installation

### Stream Deck Organization
- Create a folder in Stream Deck for audio profiles
- Use clear icons (microphone, speaker, headphones)
- Add descriptive titles to buttons
- Test each button after setup

## Advanced Usage

### Multiple Profiles in One Batch File

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

### Error Handling in Batch Files

```batch
@echo off
cd /d "C:\Path\To\AudioDeck\dist"
AudioDeck.exe --profile "Gaming Setup"
if errorlevel 1 (
    echo Failed to switch profile!
    pause
)
```

### Silent Mode (No Console Window)

For a cleaner experience, you can use VBScript to run the batch file without showing a console:

**run_silent.vbs**
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "C:\Path\To\gaming.bat", 0, False
```

Then point Stream Deck to the `.vbs` file instead.

## Troubleshooting

### Console Window Appears Briefly

This is normal behavior. The console appears, switches the profile, and closes automatically.

### GUI Opens Instead of Switching

Make sure you're using the `--profile` argument in your batch file.

### Changes Don't Take Effect

1. Check Windows Sound settings to verify the change
2. Some applications may need to be restarted
3. Try unplugging and replugging the device

## Support

For more help:
- Check `README.md` for detailed documentation
- Check `QUICKSTART.md` for setup instructions
- Review `examples/streamdeck_profiles/` for working examples