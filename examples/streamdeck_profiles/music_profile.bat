@echo off
REM Batch file to switch to Music Production audio profile
REM For use with Elgato Stream Deck

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Navigate to AudioDeck directory (adjust path as needed)
REM If AudioDeck.exe is in the same directory as this batch file:
cd /d "%SCRIPT_DIR%..\..\dist"

REM If AudioDeck.exe is in a different location, use full path instead:
REM cd /d "C:\Path\To\AudioDeck\dist"

REM Switch to the Music profile
REM IMPORTANT: Replace "Music Production" with your exact profile name
AudioDeck.exe --profile "Music Production"

REM Optional: Pause to see any error messages (remove for Stream Deck use)
REM pause