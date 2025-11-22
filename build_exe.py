"""Build script for creating standalone executable."""

import PyInstaller.__main__
import sys
from pathlib import Path


def build_executable() -> None:
    """Build the Audio Deck executable using PyInstaller."""
    # Get the project root directory
    project_root = Path(__file__).parent

    # PyInstaller arguments
    args = [
        str(project_root / "src" / "main.py"),  # Entry point
        "--name=AudioDeck",  # Executable name
        "--onefile",  # Single file executable
        "--windowed",  # No console window
        "--clean",  # Clean PyInstaller cache
        f"--distpath={project_root / 'dist'}",  # Output directory
        f"--workpath={project_root / 'build'}",  # Build directory
        f"--specpath={project_root}",  # Spec file location
        # Add hidden imports for pycaw
        "--hidden-import=comtypes.gen",
        "--hidden-import=pycaw",
        "--hidden-import=pycaw.pycaw",
        # Collect all comtypes data
        "--collect-all=comtypes",
        # Add icon if available (optional)
        # "--icon=icon.ico",
    ]

    print("Building Audio Deck executable...")
    print(f"Arguments: {' '.join(args)}")

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print("\nBuild complete!")
    print(f"Executable location: {project_root / 'dist' / 'AudioDeck.exe'}")


if __name__ == "__main__":
    build_executable()
