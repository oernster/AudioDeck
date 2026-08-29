"""Build script for creating standalone executable.

Author: Oliver Ernster
"""

import re
from pathlib import Path

import PyInstaller.__main__

from installer import constants as identity

APP_NAME = "AudioDeck"

# Task Manager names a process by the PE FileDescription field and falls back
# to the file name when the executable carries no version resource at all,
# which is why an unstamped build shows as "AudioDeck.exe" rather than
# "Audio Deck". PyInstaller writes no resource unless given --version-file, so
# one is generated per build from the identity constants and VERSION.
#
# FileDescription is the application NAME, never the tagline. Giving it the
# marketing sentence is how postal-gambit ended up listed in Windows by its
# strapline instead of its name.
VERSION_RESOURCE_NAME = "file_version_info.txt"
COPYRIGHT = f"Copyright (C) {identity.APP_PUBLISHER}"
VERSION_FIELDS = 4

_VERSION_RESOURCE_TEMPLATE = """\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numeric},
    prodvers={numeric},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', {company!r}),
         StringStruct('FileDescription', {description!r}),
         StringStruct('FileVersion', {version!r}),
         StringStruct('InternalName', {original!r}),
         StringStruct('LegalCopyright', {copyright!r}),
         StringStruct('OriginalFilename', {original!r}),
         StringStruct('ProductName', {product!r}),
         StringStruct('ProductVersion', {version!r})])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

# Modules the application cannot start without. PyInstaller downgrades an
# import it cannot resolve to a line in its warn file and writes the
# executable anyway, so a build run by an interpreter that lacks one of these
# reports success and then dies on launch with ModuleNotFoundError. Reading
# the warn file back converts that silent failure into a loud one.
REQUIRED_MODULES = ("pycaw", "comtypes", "PySide6")

_MISSING_MODULE_PATTERN = re.compile(r"missing module named (\S+)")


def read_version(project_root: Path) -> str:
    """Return the canonical version from VERSION, else the development sentinel."""
    version_file = project_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0-dev"


def _numeric_version(version: str) -> tuple[int, ...]:
    """Return the four-part numeric tuple a PE version resource requires.

    A PE resource takes four integers, while VERSION carries a semver string
    that may also hold a pre-release suffix. Leading numeric parts are used and
    the tuple is padded, so a sentinel such as 0.0.0-dev still builds.
    """
    parts: list[int] = []
    for chunk in version.split(".")[:VERSION_FIELDS]:
        digits = re.match(r"\d+", chunk)
        parts.append(int(digits.group(0)) if digits else 0)
    while len(parts) < VERSION_FIELDS:
        parts.append(0)
    return tuple(parts)


def write_version_resource(
    destination: Path, version: str, description: str, original_filename: str
) -> Path:
    """Write a PyInstaller version file and return its path.

    Args:
        destination: Directory to write the resource into.
        version: The canonical version string from VERSION.
        description: PE FileDescription, which is what Task Manager displays.
        original_filename: PE OriginalFilename and InternalName.
    """
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / VERSION_RESOURCE_NAME
    path.write_text(
        _VERSION_RESOURCE_TEMPLATE.format(
            numeric=_numeric_version(version),
            company=identity.APP_PUBLISHER,
            description=description,
            version=version,
            original=original_filename,
            copyright=COPYRIGHT,
            product=identity.APP_DISPLAY_NAME,
        ),
        encoding="utf-8",
    )
    return path


def warn_file_for(work_path: Path, name: str) -> Path:
    """Return the path PyInstaller writes its missing-import report to.

    Args:
        work_path: The --workpath given to PyInstaller.
        name: The --name given to PyInstaller.
    """
    return work_path / name / f"warn-{name}.txt"


def missing_required_modules(warn_file: Path, required: tuple[str, ...]) -> list[str]:
    """Return the required modules PyInstaller could not bundle.

    Only an exact top-level name counts. A missing submodule of an installed
    package is normal and must not fail the build: comtypes generates its COM
    wrappers on demand, so a healthy report lists dozens of absent
    comtypes.gen.* and comtypes.test.* names. An interpreter genuinely lacking
    the dependency reports the bare package instead.

    Args:
        warn_file: The warn-<name>.txt PyInstaller writes into the work path.
        required: The top-level modules this artefact cannot run without.

    Returns:
        The required top-level modules reported missing, in the order first
        seen. Empty when the build resolved everything it needs.
    """
    if not warn_file.exists():
        return []

    missing: list[str] = []
    for line in warn_file.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _MISSING_MODULE_PATTERN.search(line)
        if match is None:
            continue
        name = match.group(1).strip("'\"")
        if name in required and name not in missing:
            missing.append(name)
    return missing


def fail_on_missing(warn_file: Path, required: tuple[str, ...]) -> None:
    """Abort the build when PyInstaller could not bundle a required module."""
    missing = missing_required_modules(warn_file, required)
    if not missing:
        return
    raise SystemExit(
        f"\nBUILD FAILED: PyInstaller could not bundle {', '.join(missing)}.\n"
        f"See {warn_file}\n\n"
        "The interpreter running this script must have every runtime "
        "dependency installed, because PyInstaller bundles what it can "
        "import. Run it from the project virtual environment:\n"
        "    .\\venv\\Scripts\\python.exe <script>.py"
    )


def build_executable() -> None:
    """Build the Audio Deck executable using PyInstaller."""
    # Get the project root directory
    project_root = Path(__file__).parent
    work_path = project_root / "build"

    version_resource = write_version_resource(
        work_path,
        read_version(project_root),
        identity.APP_DISPLAY_NAME,
        identity.APP_EXE_NAME,
    )

    # PyInstaller arguments
    # Note: Using --windowed to hide console window for clean GUI/CLI experience
    args = [
        str(project_root / "src" / "main.py"),  # Entry point
        f"--name={APP_NAME}",  # Executable name
        "--onefile",  # Single file executable
        "--windowed",  # Hide console window
        "--clean",  # Clean PyInstaller cache
        f"--distpath={project_root / 'dist'}",  # Output directory
        f"--workpath={work_path}",  # Build directory
        f"--specpath={project_root}",  # Spec file location
        # Add hidden imports for pycaw
        "--hidden-import=comtypes.gen",
        "--hidden-import=pycaw",
        "--hidden-import=pycaw.pycaw",
        # Collect all comtypes data
        "--collect-all=comtypes",
        # Add application icon (from the generated asset set)
        "--icon=assets/icons/audiodeck.ico",
        # PE version resource, so Windows names the process "Audio Deck"
        f"--version-file={version_resource}",
        # Bundle the VERSION file so the frozen app reads the real version
        f"--add-data={project_root / 'VERSION'};.",
        # Bundle the generated icon set (window, taskbar, splash, about, dialogs)
        f"--add-data={project_root / 'assets' / 'icons'};assets/icons",
        # Bundle the in-app user guide and the licence files (the Help menu
        # reads each of these from the bundle at runtime)
        f"--add-data={project_root / 'DOCUMENTATION.md'};.",
        f"--add-data={project_root / 'LICENSE'};.",
        f"--add-data={project_root / 'LICENSE-GPL-3.0.txt'};.",
        f"--add-data={project_root / 'LICENSE-LGPL-3.0.txt'};.",
    ]

    print("Building Audio Deck executable...")
    print(f"Arguments: {' '.join(args)}")

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    # A build is only complete if every module the app needs was bundled.
    fail_on_missing(warn_file_for(work_path, APP_NAME), REQUIRED_MODULES)

    print("\nBuild complete!")
    print(f"Executable location: {project_root / 'dist' / f'{APP_NAME}.exe'}")
    print("\nNote: The executable now supports both GUI and CLI modes:")
    print(f"  - GUI mode: Run without arguments (double-click or '{APP_NAME}.exe')")
    print(f"  - CLI mode: Run with arguments (e.g., '{APP_NAME}.exe --list')")


if __name__ == "__main__":
    build_executable()
