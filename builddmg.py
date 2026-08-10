"""Build the signed, notarised AudioDeck DMG (macOS only).

Flow: platform guard, clean, entitlements, icns from the generated PNG set,
PyInstaller .app, missing-module check, strip stray Mach-O objects, codesign,
staged DMG via create-dmg, sign the DMG, notarize and staple (gated on the
Apple credentials being set in the environment), verify. An unnotarised DMG is
not a deliverable: Gatekeeper blocks it on first launch, so the notarisation
step is part of the build, not an optional extra.

Author: Oliver Ernster
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from buildexe import fail_on_missing, warn_file_for

PROJECT_ROOT = Path(__file__).resolve().parent

APP_NAME = "AudioDeck"
BUNDLE_ID = "uk.codecrafter.AudioDeck"
ENTRY_SCRIPT = PROJECT_ROOT / "src" / "main.py"
VERSION_FILE = PROJECT_ROOT / "VERSION"
LICENSE_FILE = PROJECT_ROOT / "LICENSE"
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"
WORK_DIR = PROJECT_ROOT / "build"
APP_BUNDLE = DIST_DIR / f"{APP_NAME}.app"
# The DMG is the deliverable, so it lands at the repo root rather than inside
# the build output that the next run wipes.
DMG_PATH = PROJECT_ROOT / f"{APP_NAME}.dmg"

# The Help menu reads these from the bundle at runtime, so a build that omits
# one ships a menu entry that opens a "File Not Found" box.
DOC_FILES = (
    PROJECT_ROOT / "DOCUMENTATION.md",
    PROJECT_ROOT / "LICENSE-GPL-3.0.txt",
    PROJECT_ROOT / "LICENSE-LGPL-3.0.txt",
)

# Modules the application cannot start without. PyInstaller downgrades an
# import it cannot resolve to a line in its warn file and writes the bundle
# anyway, so a build run by an interpreter that lacks one reports success and
# then dies on launch. Reading the warn file back makes that loud.
REQUIRED_MODULES = ("PySide6",)

# iconutil builds the .icns from a directory of exactly these names. Every
# size is already generated into assets/ by generate_icons.py, so the set is
# assembled by copying rather than by resampling here.
ICONSET_DIR_NAME = f"{APP_NAME}.iconset"
ICONSET_ENTRIES = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)

# create-dmg window geometry, in points. The drop-link and app icon positions
# have to sit inside the window, so they are stated together with its size.
DMG_WINDOW_POS = ("200", "200")
DMG_WINDOW_SIZE = ("600", "360")
DMG_ICON_SIZE = "128"
DMG_APP_ICON_POS = ("150", "180")
DMG_DROP_LINK_POS = ("450", "180")

DEVELOPER_ID = os.environ.get(
    "DEVELOPER_ID_APPLICATION",
    "Developer ID Application: Oliver Ernster (W7K465GKFJ)",
)
APPLE_ID = os.environ.get("APPLE_ID", "")
APPLE_APP_PASSWORD = os.environ.get("APPLE_APP_PASSWORD", "")
APPLE_TEAM_ID = os.environ.get("APPLE_TEAM_ID", "W7K465GKFJ")

# notarytool credentials stored once with:
#     xcrun notarytool store-credentials AudioDeck --apple-id ... --team-id ...
# This is the normal path on a development machine; the APPLE_ID and
# APPLE_APP_PASSWORD variables above override it for a CI run that has no
# keychain to read.
NOTARY_KEYCHAIN_PROFILE = os.environ.get("NOTARY_KEYCHAIN_PROFILE", APP_NAME)

# Set to opt out of notarisation deliberately, for a local test build only.
SKIP_NOTARIZE = bool(os.environ.get("SKIP_NOTARIZE", ""))

NOTARIZE_HELP = (
    "Notarisation failed. Store the credentials once with:\n"
    f"    xcrun notarytool store-credentials {NOTARY_KEYCHAIN_PROFILE}"
    f" --apple-id <your-apple-id> --team-id {APPLE_TEAM_ID}\n"
    "or set APPLE_ID and APPLE_APP_PASSWORD in the environment. To build an\n"
    "unnotarised DMG for local testing only, set SKIP_NOTARIZE=1."
)

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


def build_icns(icns_path: Path, staging_dir: Path) -> None:
    """Build the .icns from the generated PNG set with iconutil.

    iconutil ships with macOS, so the icon step needs no third-party imaging
    library; the sizes it wants are already in assets/.

    Args:
        icns_path: Where to write the .icns.
        staging_dir: Directory to assemble the .iconset in.
    """
    iconset = staging_dir / ICONSET_DIR_NAME
    iconset.mkdir(parents=True, exist_ok=True)
    for iconset_name, size in ICONSET_ENTRIES:
        source = ASSETS_DIR / f"audiodeck_icon_{size}.png"
        if not source.exists():
            sys.exit(f"Missing icon asset: {source}. Run generate_icons.py first.")
        shutil.copyfile(source, iconset / iconset_name)
    run("iconutil", "--convert", "icns", str(iconset), "--output", str(icns_path))


def strip_object_files(bundle: Path) -> None:
    """Remove stray Mach-O *.o files codesign skips and Gatekeeper rejects."""
    for object_file in bundle.rglob("*.o"):
        object_file.unlink()
    for objects_dir in sorted(bundle.rglob("objects-*"), reverse=True):
        if objects_dir.is_dir() and not any(objects_dir.iterdir()):
            objects_dir.rmdir()


def build_app(entitlements: Path, icns_path: Path) -> None:
    """Build the .app with PyInstaller."""
    data_files = (VERSION_FILE, LICENSE_FILE) + DOC_FILES
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
        f"--workpath={WORK_DIR}",
        f"--specpath={PROJECT_ROOT}",
        f"--paths={PROJECT_ROOT}",
        f"--icon={icns_path}",
        f"--osx-bundle-identifier={BUNDLE_ID}",
        f"--osx-entitlements-file={entitlements}",
        f"--add-data={ASSETS_DIR}:assets",
        *(f"--add-data={data_file}:." for data_file in data_files),
        str(ENTRY_SCRIPT),
    )
    fail_on_missing(warn_file_for(WORK_DIR, APP_NAME), REQUIRED_MODULES)


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


def create_dmg(icns_path: Path) -> None:
    """Stage the app with ditto (symlinks intact) and build the DMG."""
    with tempfile.TemporaryDirectory() as staging_name:
        staging = Path(staging_name) / APP_NAME
        run("ditto", str(APP_BUNDLE), str(staging / f"{APP_NAME}.app"))
        result = run(
            "create-dmg",
            "--volname",
            APP_NAME,
            "--volicon",
            str(icns_path),
            "--window-pos",
            *DMG_WINDOW_POS,
            "--window-size",
            *DMG_WINDOW_SIZE,
            "--icon-size",
            DMG_ICON_SIZE,
            "--icon",
            f"{APP_NAME}.app",
            *DMG_APP_ICON_POS,
            "--app-drop-link",
            *DMG_DROP_LINK_POS,
            "--hide-extension",
            f"{APP_NAME}.app",
            str(DMG_PATH),
            str(staging),
            check=False,
        )
        if result.returncode not in CREATE_DMG_SUCCESS_CODES:
            sys.exit(f"create-dmg failed with exit code {result.returncode}")


def set_file_icon(icns_path: Path) -> None:
    """Give the DMG file itself the app icon in Finder.

    The icon is a Finder attribute on the file, so it is set after signing and
    notarisation; neither reads it. A failure here leaves a generic disk-image
    icon rather than a broken deliverable, so it warns instead of aborting.

    Args:
        icns_path: The multi-size .icns built for the app bundle.
    """
    result = run("fileicon", "set", str(DMG_PATH), str(icns_path), check=False)
    if result.returncode != 0:
        print(f"WARNING: could not set the DMG file icon ({result.returncode}).")


def notary_credential_args() -> tuple[str, ...]:
    """Return the notarytool credential flags to submit with.

    Explicit environment credentials win, so a CI run with no keychain works;
    otherwise the stored keychain profile is used.
    """
    if APPLE_ID and APPLE_APP_PASSWORD:
        return (
            "--apple-id",
            APPLE_ID,
            "--password",
            APPLE_APP_PASSWORD,
            "--team-id",
            APPLE_TEAM_ID,
        )
    return ("--keychain-profile", NOTARY_KEYCHAIN_PROFILE)


def notarize_and_staple() -> None:
    """Notarize and staple the DMG; refuse to skip silently.

    An unnotarised DMG is not a deliverable, so a failure here fails the
    build. Skipping is possible but has to be asked for with SKIP_NOTARIZE.
    """
    if SKIP_NOTARIZE:
        print(
            "WARNING: SKIP_NOTARIZE is set, so the DMG is NOT notarised."
            " Gatekeeper will block it on first launch; do not publish"
            " this file."
        )
        return
    submit = run(
        "xcrun",
        "notarytool",
        "submit",
        str(DMG_PATH),
        *notary_credential_args(),
        "--wait",
        check=False,
    )
    if submit.returncode != 0:
        sys.exit(NOTARIZE_HELP)
    run("xcrun", "stapler", "staple", str(DMG_PATH))
    verify_gatekeeper()


def verify_gatekeeper() -> None:
    """Assess the stapled DMG the way a user's Mac will on first open.

    notarytool can report a submission it accepted while the ticket is not
    usable, so the build ends on the assessment Gatekeeper itself makes
    rather than on the submission result.
    """
    assessment = run(
        "spctl",
        "--assess",
        "--type",
        "open",
        "--context",
        "context:primary-signature",
        "-v",
        str(DMG_PATH),
        check=False,
    )
    if assessment.returncode != 0:
        sys.exit("Gatekeeper rejected the notarised DMG; it is not shippable.")


def main() -> int:
    """Build, sign, package, notarize."""
    if sys.platform != "darwin":
        sys.exit("builddmg.py runs on macOS only.")

    require("create-dmg")
    require("fileicon")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)
    # create-dmg refuses to overwrite, so a previous deliverable is cleared.
    DMG_PATH.unlink(missing_ok=True)

    entitlements = Path(tempfile.mkstemp(suffix=".plist")[1])
    icns_path = DIST_DIR / "audiodeck.icns"
    try:
        entitlements.write_text(ENTITLEMENTS_XML, encoding="utf-8")
        with tempfile.TemporaryDirectory() as icon_staging:
            build_icns(icns_path, Path(icon_staging))

        build_app(entitlements, icns_path)
        strip_object_files(APP_BUNDLE)
        sign_bundle(entitlements)

        create_dmg(icns_path)
        run("codesign", "--force", "--sign", DEVELOPER_ID, str(DMG_PATH))
        notarize_and_staple()
        run("codesign", "--verify", str(DMG_PATH))
        set_file_icon(icns_path)
    finally:
        entitlements.unlink(missing_ok=True)

    print(f"DMG ready: {DMG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
