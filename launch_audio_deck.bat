@echo off
REM Batch file to launch Audio Deck from Stream Deck
REM This assumes the executable is in the dist folder

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Launch the Audio Deck executable
start "" "%SCRIPT_DIR%dist\AudioDeck.exe"