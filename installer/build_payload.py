"""Stage the built Audio Deck app into an installer payload.

Produces ``installer/payload/payload.zip`` and ``installer/payload/manifest.json``
from the PyInstaller output in ``dist/``. Run after ``buildexe.py`` and before
``buildinstaller.py``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

from installer import constants as c

_HASH_CHUNK = 65536


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(_HASH_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
PAYLOAD_DIR = PROJECT_ROOT / "installer" / c.PAYLOAD_DIR_NAME
VERSION_FILE = PROJECT_ROOT / "VERSION"

# Files placed at the root of the install directory, taken from these sources.
PAYLOAD_FILES = (
    (DIST_DIR / c.APP_EXE_NAME, c.APP_EXE_NAME),
    (PROJECT_ROOT / "README.md", "README.md"),
    (PROJECT_ROOT / "LICENSE", "LICENSE"),
    (
        PROJECT_ROOT / "assets" / c.ICONS_DIR_NAME / c.ICON_FILE_NAME,
        c.ICON_FILE_NAME,
    ),
)


def _read_version() -> str:
    """Read the version string from the root VERSION file."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def build() -> Path:
    """Build the payload zip and manifest.

    Returns:
        Path to the generated payload zip.

    Raises:
        FileNotFoundError: If the built exe or any payload source is missing.
    """
    missing = [str(src) for src, _ in PAYLOAD_FILES if not src.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing payload sources (run buildexe.py first):\n  "
            + "\n  ".join(missing)
        )

    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = PAYLOAD_DIR / c.PAYLOAD_ZIP_NAME
    manifest_path = PAYLOAD_DIR / c.MANIFEST_NAME

    files = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, arc_name in PAYLOAD_FILES:
            archive.write(source, arc_name)
            files.append({"name": arc_name, "sha256": _sha256(source)})

    manifest = {
        "version": _read_version(),
        "exe": c.APP_EXE_NAME,
        "icon": c.ICON_FILE_NAME,
        "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"  wrote {zip_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {manifest_path.relative_to(PROJECT_ROOT)}")
    return zip_path


if __name__ == "__main__":
    print("Staging installer payload...")
    try:
        build()
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
    print("Payload staged.")
