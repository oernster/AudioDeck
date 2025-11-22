# Stream Deck Profile Batch Files

This directory contains example batch files for integrating AudioDeck with Elgato Stream Deck.

## How to Use

1. **Build AudioDeck**: Run `python build_exe.py` to create `dist/AudioDeck.exe`

2. **List Your Profiles**: Run `AudioDeck.exe --list` to see all your configured profiles

3. **Create Batch Files**: Copy one of the example batch files and modify it with your profile name

4. **Configure Stream Deck**:
   - Open Stream Deck software
   - Add a "System > Open" action
   - Browse to your batch file
   - Add a custom icon (optional)

## Example Batch Files

- `gaming_profile.bat` - Example for a gaming audio setup
- `work_profile.bat` - Example for work/meeting audio setup
- `music_profile.bat` - Example for music production setup

## Creating Your Own

1. Copy an example batch file
2. Rename it to match your profile (e.g., `my_profile.bat`)
3. Edit the file and replace the profile name with your exact profile name
4. Save and use it in Stream Deck

## Important Notes

- Profile names are **case-sensitive**
- Use the **exact** profile name as shown in AudioDeck GUI or `--list` command
- The batch file must be in the same directory as `AudioDeck.exe` or use full paths
- If your profile name contains spaces, keep the quotes: `--profile "My Profile"`

## Troubleshooting

If the profile doesn't switch:
1. Run the batch file manually to see any error messages
2. Verify the profile name with `AudioDeck.exe --list`
3. Check that AudioDeck.exe path is correct in the batch file
4. Ensure the profile still exists and devices are connected