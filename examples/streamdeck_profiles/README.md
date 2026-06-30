# Stream Deck Profile Batch Files

Example batch files for integrating AudioDeck with an Elgato Stream Deck.

## How to use

1. **Build AudioDeck**: run `python buildexe.py` to create `dist/AudioDeck.exe`.
2. **List your profiles**: run `AudioDeck.exe --list` to see your configured
   profiles.
3. **Create batch files**: copy one of the examples and set your profile name.
4. **Configure Stream Deck**:
   - Open the Stream Deck software.
   - Add a **System > Open** action.
   - Browse to your batch file.
   - Optionally add a custom icon.

## Example batch files

- `gaming_profile.bat` - a gaming audio setup.
- `work_profile.bat` - a work or meeting audio setup.
- `music_profile.bat` - a music production setup.

## Creating your own

1. Copy an example batch file.
2. Rename it to match your profile (for example `my_profile.bat`).
3. Edit it and set your exact profile name.
4. Save it and use it in Stream Deck.

## Notes

- Profile names are case sensitive.
- Use the exact profile name as shown in the GUI or by `--list`.
- Keep the batch file beside `AudioDeck.exe` or use full paths.
- If a profile name contains spaces, keep the quotes: `--profile "My Profile"`.

## Troubleshooting

If a profile does not switch:

1. Run the batch file manually to read any error message.
2. Verify the profile name with `AudioDeck.exe --list`.
3. Check the path to `AudioDeck.exe` in the batch file.
4. Confirm the profile still exists and the devices are connected.
