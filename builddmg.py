"""Build the signed, notarised AudioDeck DMG (macOS only).

Flow: platform guard, clean, entitlements, PNG to icns, PyInstaller .app,
strip stray Mach-O objects, codesign, staged DMG via create-dmg, sign the
DMG, notarize and staple (gated on the Apple credentials being set in the
environment), verify. An unnotarised DMG is not a deliverable: Gatekeeper
blocks it on first launch, so the notarisation step is part of the build,
not an optional extra.

Author: Oliver Ernster
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

APP_NAME = "AudioDeck"
BUNDLE_ID = "uk.codecrafter.AudioDeck"
ENTRY_SCRIPT = PROJECT_ROOT / "src" / "main.py"
VERSION_FILE = PROJECT_ROOT / "VERSION"
LICENSE_FILE = PROJECT_ROOT / "LICENSE"
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_MASTER_PNG = ASSETS_DIR / "audiodeck_icon_1024.png"
DIST_DIR = PROJECT_ROOT / "dist"
APP_BUNDLE = DIST_DIR / f"{APP_NAME}.app"
DMG_PATH = DIST_DIR / "audiodeck-macos-arm64.dmg"

DEVELOPER_ID = os.environ.get(
    "DEVELOPER_ID_APPLICATION",
    "Developer ID Application: Oliver Ernster (W7K465GKFJ)",
)
APPLE_ID = os.environ.get("APPLE_ID", "")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD", "")
APPLE_TEAM_ID = os.environ.get("APPLE_TEAM_ID", "W7K465GKFJ")

# Load our-identity-signed bundled Qt libraries under the hardened runtime.
ENTITLEMENTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
"""

# create-dmg exits 2 when it succeeds but cannot set a custom window
# background (headless run); both codes mean the DMG was written.
CREATE_DMG_SUCCESS_CODES = (0, 2)


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, echoing it first."""
    print("+", " ".join(args))
    return subprocess.run(list(args), check=check)


def require(tool: str) -> None:
    """Ensure a command-line tool exists, brew-installing it on a miss."""
    if shutil.which(tool):
        return
    run("brew", "install", tool)
    if not shutil.which(tool):
        sys.exit(f"Required tool is not available: {tool}")


def png_to_icns(png_path: Path, icns_path: Path) -> None:
    """Convert the 1024px master PNG to a .icns via Pillow."""
    from PIL import Image

    Image.open(png_path).convert("RGBA").save(icns_path, format="ICNS")


def strip_object_files(bundle: Path) -> None:
    """Remove stray Mach-O *.o files codesign skips and Gatekeeper rejects."""
    for object_file in bundle.rglob("*.o"):
        object_file.unlink()
    for objects_dir in sorted(bundle.rglob("objects-*"), reverse=True):
        if objects_dir.is_dir() and not any(objects_dir.iterdir()):
            objects_dir.rmdir()


def build_app(entitlements: Path, icns_path: Path) -> None:
    """Build the .app with PyInstaller."""
    run(
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        f"--distpath={DIST_DIR}",
        f"--icon={icns_path}",
        f"--osx-bundle-identifier={BUNDLE_ID}",
        f"--codesign-identity={DEVELOPER_ID}",
        f"--osx-entitlements-file={entitlements}",
        f"--add-data={ASSETS_DIR}:assets",
        f"--add-data={VERSION_FILE}:.",
        f"--add-data={LICENSE_FILE}:.",
        str(ENTRY_SCRIPT),
    )


def sign_bundle(entitlements: Path) -> None:
    """Deep-sign the bundle under the hardened runtime, then verify."""
    run(
        "codesign",
        "--force",
        "--deep",
        "--options",
        "runtime",
        "--entitlements",
        str(entitlements),
        "--sign",
        DEVELOPER_ID,
        str(APP_BUNDLE),
    )
    run("codesign", "--verify", "--deep", "--strict", str(APP_BUNDLE))


def create_dmg() -> None:
    """Stage the app with ditto (symlinks intact) and build the DMG."""
    with tempfile.TemporaryDirectory() as staging_name:
        staging = Path(staging_name) / APP_NAME
        run("ditto", str(APP_BUNDLE), str(staging / f"{APP_NAME}.app"))
        result = run(
            "create-dmg",
            "--volname",
            APP_NAME,
            "--app-drop-link",
            "450",
            "170",
            str(DMG_PATH),
            str(staging),
            check=False,
        )
        if result.returncode not in CREATE_DMG_SUCCESS_CODES:
            sys.exit(f"create-dmg failed with exit code {result.returncode}")


def notarize_and_staple() -> None:
    """Notarize and staple the DMG; refuse to skip silently."""
    if not (APPLE_ID and APPLE_APP_PASSWORD):
        print(
            "WARNING: APPLE_ID / APPLE_APP_PASSWORD are not set, so the DMG"
            " is NOT notarised. Gatekeeper will block it on first launch;"
            " do not publish this file."
        )
        return
    run(
        "xcrun",
        "notarytool",
        "submit",
        str(DMG_PATH),
        "--apple-id",
        APPLE_ID,
        "--password",
        APPLE_APP_PASSWORD,
        "--team-id",
        APPLE_TEAM_ID,
        "--wait",
    )
    run("xcrun", "stapler", "staple", str(DMG_PATH))


def main() -> int:
    """Build, sign, package, notarize."""
    if sys.platform != "darwin":
        sys.exit("builddmg.py runs on macOS only.")

    require("create-dmg")
    require("fileicon")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    entitlements = Path(tempfile.mkstemp(suffix=".plist")[1])
    icns_path = DIST_DIR / "audiodeck.icns"
    try:
        entitlements.write_text(ENTITLEMENTS_XML, encoding="utf-8")
        png_to_icns(ICON_MASTER_PNG, icns_path)

        build_app(entitlements, icns_path)
        strip_object_files(APP_BUNDLE)
        sign_bundle(entitlements)

        create_dmg()
        run("codesign", "--force", "--sign", DEVELOPER_ID, str(DMG_PATH))
        notarize_and_staple()
        run("codesign", "--verify", str(DMG_PATH))
        run("fileicon", "set", str(DMG_PATH), str(ICON_MASTER_PNG), check=False)
    finally:
        entitlements.unlink(missing_ok=True)

    print(f"DMG ready: {DMG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
