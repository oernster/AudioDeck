"""Build script for creating standalone executable.

Author: Oliver Ernster
"""

from pathlib import Path

import PyInstaller.__main__


def build_executable() -> None:
    """Build the Audio Deck executable using PyInstaller."""
    # Get the project root directory
    project_root = Path(__file__).parent

    # PyInstaller arguments
    # Note: Using --windowed to hide console window for clean GUI/CLI experience
    args = [
        str(project_root / "src" / "main.py"),  # Entry point
        "--name=AudioDeck",  # Executable name
        "--onefile",  # Single file executable
        "--windowed",  # Hide console window
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
        # Add application icon (from the generated asset set)
        "--icon=assets/audiodeck.ico",
        # Bundle the VERSION file so the frozen app reads the real version
        f"--add-data={project_root / 'VERSION'};.",
        # Bundle the generated icon set (window, taskbar, splash, about, dialogs)
        f"--add-data={project_root / 'assets'};assets",
        # Bundle documentation and license files
        f"--add-data={project_root / 'README.md'};.",
        f"--add-data={project_root / 'LICENSE'};.",
        # Bundle development documentation files
        f"--add-data={project_root / 'ARCHITECTURE.md'};.",
        f"--add-data={project_root / 'CLI_USAGE.md'};.",
        f"--add-data={project_root / 'DEVELOPMENT_README.md'};.",
    ]

    print("Building Audio Deck executable...")
    print(f"Arguments: {' '.join(args)}")

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print("\nBuild complete!")
    print(f"Executable location: {project_root / 'dist' / 'AudioDeck.exe'}")
    print("\nNote: The executable now supports both GUI and CLI modes:")
    print("  - GUI mode: Run without arguments (double-click or 'AudioDeck.exe')")
    print("  - CLI mode: Run with arguments (e.g., 'AudioDeck.exe --list')")


if __name__ == "__main__":
    build_executable()
