"""Generate all platform icon assets from a single master PNG.

Reads the repo-root master PNG (``audiodeck.png``) and emits the full icon
set into ``assets/``: per-size hicolor PNGs, a canonical 256px badge, a
multi-frame Windows ``.ico`` and a macOS ``.icns``. Every consumer
(buildexe.py, buildinstaller.py, the installer UI and the in-app icon
resolver) points at this generated set, so it is the single source for all
icon assets.

Author: Oliver Ernster
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent
MASTER_PNG = PROJECT_ROOT / "audiodeck.png"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Loose hicolor / badge PNG sizes emitted as audiodeck_icon_<size>.png.
PNG_SIZES = (16, 24, 32, 48, 64, 96, 128, 256, 512, 1024)
# Frames embedded in the multi-size Windows .ico.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# The single canonical badge size used by dialogs and the installer window.
CANONICAL_PNG_SIZE = 256
# macOS .icns is generated from the largest square source.
ICNS_SOURCE_SIZE = 1024

ICO_NAME = "audiodeck.ico"
ICNS_NAME = "audiodeck.icns"
CANONICAL_PNG_NAME = "audiodeck_icon.png"
PER_SIZE_PNG_TEMPLATE = "audiodeck_icon_{size}.png"

RESAMPLE = Image.Resampling.LANCZOS

# Icons must ALWAYS have a transparent background. A solid (e.g. white) backdrop
# in the master is flood-filled to transparency from the corners, so the
# artwork keeps any interior light pixels while the background is removed.
WHITE_BG_THRESHOLD = 40
TRANSPARENT = (0, 0, 0, 0)
NEAR_WHITE_MIN = 255 - WHITE_BG_THRESHOLD


def _is_near_white(pixel: tuple) -> bool:
    """Return True if a pixel is opaque and near white."""
    red, green, blue, alpha = pixel
    return (
        alpha > 0
        and red >= NEAR_WHITE_MIN
        and green >= NEAR_WHITE_MIN
        and blue >= NEAR_WHITE_MIN
    )


def _make_background_transparent(image: Image.Image) -> Image.Image:
    """Flood-fill a solid background from the corners to transparency.

    Only the background region connected to a corner is removed, so light
    pixels enclosed by the artwork are preserved.

    Args:
        image: A square RGBA image.

    Returns:
        The image with its background made transparent.
    """
    width, height = image.size
    corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    for corner in corners:
        if _is_near_white(image.getpixel(corner)):
            ImageDraw.floodfill(image, corner, TRANSPARENT, thresh=WHITE_BG_THRESHOLD)
    return image


def _load_square_master() -> Image.Image:
    """Load the master PNG, centre-crop to a square, ensure a transparent
    background and convert to RGBA.

    Returns:
        The master image as a square RGBA image with a transparent background.
    """
    master = Image.open(MASTER_PNG).convert("RGBA")
    width, height = master.size
    if width != height:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        master = master.crop((left, top, left + side, top + side))
    return _make_background_transparent(master)


def _resized(master: Image.Image, size: int) -> Image.Image:
    """Return the master resized to a square of the given pixel size.

    Args:
        master: Square RGBA master image.
        size: Target edge length in pixels.

    Returns:
        Resized square RGBA image.
    """
    return master.resize((size, size), RESAMPLE)


def generate_icons() -> None:
    """Generate the full icon set into the assets directory."""
    if not MASTER_PNG.exists():
        raise FileNotFoundError(
            f"Master icon not found: {MASTER_PNG}. "
            "Provide a square RGBA PNG at the repo root."
        )

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    master = _load_square_master()

    # Per-size hicolor / badge PNGs.
    for size in PNG_SIZES:
        out_path = ASSETS_DIR / PER_SIZE_PNG_TEMPLATE.format(size=size)
        _resized(master, size).save(out_path)
        print(f"  wrote {out_path.name}")

    # Canonical 256px badge.
    canonical_path = ASSETS_DIR / CANONICAL_PNG_NAME
    _resized(master, CANONICAL_PNG_SIZE).save(canonical_path)
    print(f"  wrote {canonical_path.name}")

    # Multi-frame Windows .ico.
    ico_path = ASSETS_DIR / ICO_NAME
    _resized(master, max(ICO_SIZES)).save(
        ico_path, format="ICO", sizes=[(s, s) for s in ICO_SIZES]
    )
    print(f"  wrote {ico_path.name}")

    # macOS .icns.
    icns_path = ASSETS_DIR / ICNS_NAME
    _resized(master, ICNS_SOURCE_SIZE).save(icns_path, format="ICNS")
    print(f"  wrote {icns_path.name}")


if __name__ == "__main__":
    print(f"Generating icons from {MASTER_PNG.name}...")
    generate_icons()
    print(f"Done. Icon set written to {ASSETS_DIR}.")
