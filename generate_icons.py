"""Generate every icon asset the application ships, from the committed masters.

Two kinds of artwork come out of here, from two kinds of master. The
difference between them is the whole design:

* The APPLICATION ICON is square by nature. It is centre-cropped to a square
  and emitted at the platform sizes, plus a multi-frame Windows ``.ico``. It
  ends up on the executable, the window, the taskbar, the shortcuts, the Apps
  list, the splash screen and the About dialog.
* A BUTTON ICON is not square and must never be squared. It is a picture drawn
  at a button's height, so a square canvas would spend the difference on empty
  space and shrink the artwork inside its own box. Each one is cropped to the
  tight box of its opaque pixels, then scaled by HEIGHT alone with the aspect
  ratio kept. Fitting by the longer side instead makes a wide picture SHORTER
  than its neighbours, which is what breaks a row of icons: the eye checks the
  shared bottom edge, so equal heights matter and equal widths do not.

Masters live in ``assets/`` and are the committed source. Nothing here writes
to them. Everything generated goes to ``assets/icons/``, which is the only
directory the build stages, so the multi-megabyte masters never ride into an
installer.

Two button icons are COMPOSITES rather than masters of their own: a red
prohibition bar (``negative.png``) laid over the icon of the thing being
negated. Delete a profile is that bar over the stored-profile icon; cancel an
edit is the same bar over the edit icon. Compositing here rather than shipping
two more masters means the bar can never drift between them.

Author: Oliver Ernster
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent
MASTERS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = MASTERS_DIR / "icons"
DOCS_DIR = PROJECT_ROOT / "docs"

RESAMPLE = Image.Resampling.LANCZOS

# ---------------------------------------------------------------- application

APP_ICON_MASTER = MASTERS_DIR / "application-icon.png"

# Loose hicolor / badge PNG sizes emitted as audiodeck_icon_<size>.png. The
# Flatpak build installs these directly as its hicolor set.
PNG_SIZES = (16, 24, 32, 48, 64, 96, 128, 256, 512, 1024)
# Frames embedded in the multi-size Windows .ico, which Windows picks from
# according to where it is drawing: 16 in a title bar, 256 in a large view.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# The single canonical badge size used by the dialogs, the splash and the
# installer window.
CANONICAL_PNG_SIZE = 256

ICO_NAME = "audiodeck.ico"
CANONICAL_PNG_NAME = "audiodeck_icon.png"
PER_SIZE_PNG_TEMPLATE = "audiodeck_icon_{size}.png"

# Icons must ALWAYS have a transparent background. A solid backdrop in a master
# is flood-filled to transparency from the corners, so the artwork keeps any
# interior light pixels while the background is removed.
WHITE_BG_THRESHOLD = 40
TRANSPARENT = (0, 0, 0, 0)
NEAR_WHITE_MIN = 255 - WHITE_BG_THRESHOLD

# --------------------------------------------------------------------- button

# The height a button icon is RENDERED at. Four times the height the buttons
# actually draw it at, so it stays crisp on a display running above 100% scale
# and Qt only ever scales DOWN, which is the direction that looks good. The
# relationship to the drawn height is pinned by a structural test rather than
# by importing the UI here, which would drag PySide6 into a build script.
BUTTON_RENDER_HEIGHT_PX = 288

# The same artwork again, small, for the in-app guide's key to the buttons.
# Rendered rather than scaled at display time because the guide is markdown and
# Qt draws an image there at its natural size. Not smaller than this: below
# about forty pixels the darker marks stop being tellable apart, which is the
# one thing a key has to get right.
GUIDE_RENDER_HEIGHT_PX = 48
GUIDE_PREFIX = "guide-"

# Every button icon, named by what its button DOES rather than by what the
# picture contains, since the name is what the UI asks for.
BUTTON_MASTERS = {
    "quick-switch": "quick-switch.png",
    "configuration": "configuration.png",
    "switch": "switch.png",
    "rescan": "rescan.png",
    "add-profile": "add-profile.png",
    "edit-profile": "edit-profile.png",
    "save-profile": "save-profile.png",
    "light-mode": "light-mode.png",
    "dark-mode": "dark-mode.png",
    "help-info": "help-info.png",
}

# name -> (base master, overlay master). The overlay is scaled to the base's
# own box and centred, so the bar covers the artwork it negates whatever the
# two masters' proportions are.
NEGATIVE_MASTER = "negative.png"
BUTTON_COMPOSITES = {
    "delete-profile": "save-profile.png",
    "cancel-edit": "edit-profile.png",
}

# --------------------------------------------------------------------- donate

# The donate master is the one that sits at the repo root rather than in
# assets/, because it is not part of the app's own icon vocabulary: it is a
# picture of a beer and a coffee that means "buy the author a drink".
DONATE_MASTER = PROJECT_ROOT / "donate.png"
DONATE_NAME = "donate.png"

# ----------------------------------------------------------------------- site

# The GitHub Pages site carries its own copies of the application icon: a
# favicon, the Apple touch icon and the badge the pages and the Open Graph tags
# point at. They are derived here rather than dropped in by hand, because a
# redrawn application icon that reaches the app and not the site is a
# difference nobody notices until the two are seen side by side.
SITE_PNG_SIZES = {
    "favicon-32.png": 32,
    "apple-touch-icon.png": 180,
    "audiodeck-512.png": 512,
}
SITE_ICO_NAME = "favicon.ico"
SITE_ICO_SIZES = (16, 32, 48, 256)


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
    """
    width, height = image.size
    corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    for corner in corners:
        if _is_near_white(image.getpixel(corner)):
            ImageDraw.floodfill(image, corner, TRANSPARENT, thresh=WHITE_BG_THRESHOLD)
    return image


def _load_master(name: str) -> Image.Image:
    """Load a master by filename from the assets directory, as RGBA."""
    path = MASTERS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Master artwork not found: {path}")
    return Image.open(path).convert("RGBA")


def _cropped_to_artwork(image: Image.Image) -> Image.Image:
    """Return the image cropped to the tight box of its opaque pixels.

    A master is drawn on a generous canvas, so the artwork rarely fills it.
    Scaling without cropping first would size the CANVAS to the button and
    leave the picture floating small inside it.
    """
    box = image.getchannel("A").getbbox()
    return image.crop(box) if box else image


def _scaled_to_height(image: Image.Image, height: int) -> Image.Image:
    """Return the image scaled to `height`, keeping its aspect ratio."""
    width = max(1, round(image.width * height / image.height))
    return image.resize((width, height), RESAMPLE)


def _square_app_master() -> Image.Image:
    """Load the application icon master, centre-cropped square and transparent."""
    master = Image.open(APP_ICON_MASTER).convert("RGBA")
    width, height = master.size
    if width != height:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        master = master.crop((left, top, left + side, top + side))
    return _make_background_transparent(master)


def _write(image: Image.Image, path: Path) -> None:
    """Write one PNG and report it."""
    image.save(path)
    print(f"  wrote {path.relative_to(PROJECT_ROOT)}")


def generate_app_icons() -> None:
    """Emit the application icon set: per-size PNGs, a badge and the .ico."""
    if not APP_ICON_MASTER.exists():
        raise FileNotFoundError(
            f"Application icon master not found: {APP_ICON_MASTER}. "
            "Provide a square RGBA PNG there."
        )
    master = _square_app_master()

    for size in PNG_SIZES:
        _write(
            master.resize((size, size), RESAMPLE),
            OUTPUT_DIR / PER_SIZE_PNG_TEMPLATE.format(size=size),
        )

    _write(
        master.resize((CANONICAL_PNG_SIZE, CANONICAL_PNG_SIZE), RESAMPLE),
        OUTPUT_DIR / CANONICAL_PNG_NAME,
    )

    ico_path = OUTPUT_DIR / ICO_NAME
    master.resize((max(ICO_SIZES), max(ICO_SIZES)), RESAMPLE).save(
        ico_path, format="ICO", sizes=[(s, s) for s in ICO_SIZES]
    )
    print(f"  wrote {ico_path.relative_to(PROJECT_ROOT)}")


def _button_icon(master_name: str) -> Image.Image:
    """Return one button icon: cropped to its artwork, sized by height."""
    cropped = _cropped_to_artwork(_load_master(master_name))
    return _scaled_to_height(cropped, BUTTON_RENDER_HEIGHT_PX)


def _negated(base_name: str) -> Image.Image:
    """Return `base_name`'s icon with the prohibition bar laid over it.

    The bar is sized to the base's own box rather than to a fixed number, so a
    base that is wider or narrower than its siblings still gets a bar that
    crosses all of it.
    """
    base = _button_icon(base_name)
    bar = _cropped_to_artwork(_load_master(NEGATIVE_MASTER)).resize(base.size, RESAMPLE)
    composed = base.copy()
    composed.alpha_composite(bar)
    return composed


def generate_button_icons() -> None:
    """Emit every button icon, including the two composites.

    Each is written twice: once at the height the tray draws it and once small
    for the guide's key, both from the same render, so the picture explaining a
    button cannot fall out of step with the button.
    """
    for name, master_name in BUTTON_MASTERS.items():
        drawn = _button_icon(master_name)
        _write(drawn, OUTPUT_DIR / f"{name}.png")
        _write(
            _scaled_to_height(drawn, GUIDE_RENDER_HEIGHT_PX),
            OUTPUT_DIR / f"{GUIDE_PREFIX}{name}.png",
        )

    for name, base_name in BUTTON_COMPOSITES.items():
        drawn = _negated(base_name)
        _write(drawn, OUTPUT_DIR / f"{name}.png")
        _write(
            _scaled_to_height(drawn, GUIDE_RENDER_HEIGHT_PX),
            OUTPUT_DIR / f"{GUIDE_PREFIX}{name}.png",
        )


def generate_donate_mark() -> None:
    """Emit the donate mark for the app and for the site, from one render.

    Both destinations take the SAME image so the button in the window and the
    button on the site cannot drift apart.
    """
    if not DONATE_MASTER.exists():
        raise FileNotFoundError(f"Donate master not found: {DONATE_MASTER}")
    mark = _scaled_to_height(
        _cropped_to_artwork(Image.open(DONATE_MASTER).convert("RGBA")),
        BUTTON_RENDER_HEIGHT_PX,
    )
    _write(mark, OUTPUT_DIR / DONATE_NAME)
    _write(
        _scaled_to_height(mark, GUIDE_RENDER_HEIGHT_PX),
        OUTPUT_DIR / f"{GUIDE_PREFIX}{DONATE_NAME}",
    )
    if DOCS_DIR.is_dir():
        _write(mark, DOCS_DIR / DONATE_NAME)


def generate_site_icons() -> None:
    """Emit the site's own copies of the application icon.

    Skipped rather than failed when there is no site checked out, so the
    generator still works in a source tree without `docs/`.
    """
    if not DOCS_DIR.is_dir():
        return
    master = _square_app_master()
    for name, size in SITE_PNG_SIZES.items():
        _write(master.resize((size, size), RESAMPLE), DOCS_DIR / name)

    ico_path = DOCS_DIR / SITE_ICO_NAME
    master.resize((max(SITE_ICO_SIZES), max(SITE_ICO_SIZES)), RESAMPLE).save(
        ico_path, format="ICO", sizes=[(s, s) for s in SITE_ICO_SIZES]
    )
    print(f"  wrote {ico_path.relative_to(PROJECT_ROOT)}")


def generate_icons() -> None:
    """Generate every icon asset into the output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generate_app_icons()
    generate_button_icons()
    generate_donate_mark()
    generate_site_icons()


if __name__ == "__main__":
    print(f"Generating icons from {MASTERS_DIR.name}/ ...")
    generate_icons()
    print(f"Done. Icon set written to {OUTPUT_DIR}.")
