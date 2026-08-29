# Audio Deck - Developer Documentation

**Author:** Oliver Ernster

The single developer guide for the AudioDeck codebase: setup, running from
source, the build, the workflow, the checks and the release steps. For user
documentation see [README.md](README.md); for the design and its invariants see
[ARCHITECTURE.md](ARCHITECTURE.md); for the test suite and the coverage gate see
[TESTING.md](TESTING.md); for the command-line surface see
[CLI_USAGE.md](CLI_USAGE.md).

## Development setup

### Prerequisites

- Windows 10 or 11; a Linux desktop with PulseAudio or PipeWire; or macOS.
- Python 3.10 or higher.
- Git.

### Installation

1. Clone the repository and enter it:
   ```bash
   git clone <repository-url>
   cd AudioDeck
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install runtime and development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

### Running from source

```bash
# GUI mode (default)
python src/main.py

# CLI mode - list profiles
python src/main.py --list

# CLI mode - switch to a profile
python src/main.py --profile "Gaming Setup"
```

Only one Audio Deck window may be open per user. If an installed or
packaged copy is already running, launching from source raises that window and
exits immediately rather than opening a second one, so close the other copy
before testing GUI changes. Headless runs (`--list` and `--profile`) are exempt
and can be run as often as you like.

### Building the executable and the installer

```powershell
python buildexe.py
python buildinstaller.py
```

`buildinstaller.py` wraps the built executable into
`dist-installer/AudioDeckSetup.exe`, a per-user themed setup application that
offers Install, Update, Reinstall, Repair and Uninstall based on the version it
detects. It has to run after `buildexe.py`.

The executable is written to `dist/AudioDeck.exe`. The build uses PyInstaller in
`--onefile --windowed` mode (a single windowed binary that still serves the CLI
when run with arguments), collects `comtypes`, declares the `pycaw` hidden
imports and bundles the generated icon set (`assets/icons`, the only part of
`assets/` that ships, since the masters beside it are source artwork), the
`VERSION` file, the in-app user guide
(`DOCUMENTATION.md`) and the three licence files (the overview plus the full
GPL-3.0 and LGPL-3.0 texts, all read by the Help menu at runtime). Build
identity and inputs live at the top of `buildexe.py`.

The Linux and macOS deliverables have their own entry points:
`./build_flatpak.sh` builds and installs the Flatpak (Linux) and
`python builddmg.py` builds the signed, notarised DMG (macOS). See the
README's building section for both.

## Project structure

```
AudioDeck/
  src/
    domain/          Pure business model
    application/     Use cases and DTOs
    infrastructure/  Platform audio backends (Windows, Linux, macOS) and JSON storage
    presentation/    PySide6 GUI (views, presenters, notifiers, workers)
    cli/             Command-line interface
    main.py          Entry point and GUI composition root
  tests/             Mirrors src/, plus the installer tests and the structural scans
  installer/         The bespoke themed setup application
  assets/            Artwork masters, with the generated set in assets/icons
  docs/              GitHub Pages site and screenshots
  examples/          Stream Deck batch-file templates
  VERSION            Single source of truth for the version
  buildexe.py        Portable executable
  buildinstaller.py  Setup executable, run after buildexe.py
  generate_icons.py  Regenerates assets/icons/ from the masters in assets/
  pyproject.toml     Packaging plus the pytest, coverage, black, ruff and mypy configuration
```

## Architecture

The codebase is a clean, layered architecture
(`UI -> Application -> Domain <- Infrastructure`) shared by the GUI and the CLI.
The full description, the dependency direction, the execution flow and the
enforced invariants are in [ARCHITECTURE.md](ARCHITECTURE.md). Key components:

- **Domain**: `AudioDevice` and `AudioProfile` entities, `DeviceType` and
  `DeviceState` value objects, the repository and controller Protocols plus the
  exception hierarchy.
- **Application**: the use cases (`GetDevices`, `GetProfiles`, `CreateProfile`,
  `UpdateProfile`, `DeleteProfile`, `SwitchProfile`, `CheckForUpdates`) and the
  DTOs (`DeviceDTO`, `ProfileDTO`, `SwitchOutcome`, `UpdateStatus`).
  `SwitchProfile` returns a `SwitchOutcome` so a profile applies its available
  devices and reports any that are skipped; `CheckForUpdates` decides whether a
  newer published release should be offered and with which download.
- **Infrastructure**: one audio backend per platform behind the shared
  Protocols, chosen by `backend_factory` (Windows: Core Audio via pycaw and
  comtypes; Linux: pactl over a subprocess seam; macOS: CoreAudio via ctypes,
  devices keyed by stable UID), the platform-neutral
  `CachingDeviceRepository`, `JsonProfileRepository`,
  `JsonUpdateSettingsRepository` (the skipped-version store, best-effort by
  design), `GitHubReleaseSource` (stdlib urllib against the GitHub releases
  endpoint, with the opener injected so tests never touch the network) plus
  the single-instance guards (a named mutex on Windows, a flocked lock file
  on Linux and macOS, the platform calls behind Protocols so the logic is
  testable). The Windows enumerator lists disconnected and disabled devices
  too, so they can be selected.
- **Presentation**: `MainWindow`, `ConfigurationView`, `ActuationView` and their
  presenters (MVP), `UpdatePresenter` (the update check's outcomes as signals,
  run through its own `BackgroundRunner`) with `update_dialogs` (the offer,
  the all-clear and the failure), plus the per-platform device-change
  notifiers behind `notifier_factory` (`WM_DEVICECHANGE` on Windows,
  `pactl subscribe` on Linux, a periodic poll on macOS) that drive live
  updates and auto-apply on reconnect, `BackgroundRunner`
  (a serial worker thread keeping COM and settle sleeps off the GUI thread),
  `icons` (the artwork names, defined once as named constants), the header
  band (`header_band.py`: the row's controls plus the window minimum its width
  demands), the tray recipes (`tray.py`: picture buttons matched on height and
  sized on width, the separator, the sun/moon theme toggle), the external-open
  seam (`links.py`, behind which the donate button hands its address to the
  desktop), the theme facility (`theme.py`: dark and light
  token dicts feeding one stylesheet and palette, persisted beside the
  profiles), the Help button with its menu and dialogs (`help_button.py`,
  `help_dialogs.py`) and the covered widgets (`KeyboardNavigator`,
  `AutoScroller`).
- **CLI**: `argument_parser` and `cli_handler`, sharing the application layer.

## The setup program

`installer/` is a PySide6 application in its own right, built to the house
setup-program shape rather than to the application's: `constants.py` holds the
identity, the paths and every colour and size; `theme.py` turns those into one
stylesheet per appearance; `shell.py` holds the furniture a screen is drawn
from (the header, the hairline, a styled label, a bare column);
`appearance.py` switches between the two palettes and re-faces the toggle;
`ui.py` is the window and `ops.py` the work it drives.

Two things about it are deliberate and easy to undo by accident. Its colours
are sampled from the application's own artwork, so the accent is the icon's
blue, the ring is its green and the danger colour is the red of the prohibition
bar, which is what makes the setup program and the app read as one product. Its
RING MODEL, however, is the house one and not the application's: no ring at
rest, green while an enabled control is hovered or focused, a permanent danger
ring while a control is disabled. That is why it is a stylesheet in its own
right rather than a layer over the app's, which carries a different model and
would fight it.

The theme toggle wears the application's OWN sun and moon artwork, taken from
the icon set the setup program already carries; it shows the appearance it
would switch TO rather than the one you are in. Both halves of that are the
same convention the application's toggle follows, so the two cannot end up
wearing different pictures for the same idea.

The version is not in the header. It belongs in the body line that names what
is installed and what the setup program carries, because the relationship
between those two numbers is the thing the reader needs and only reads as a
sentence.

## Artwork

Every picture the application draws is generated from a committed master by
`python generate_icons.py`. Masters live in `assets/`; the generated set lands
in `assets/icons/` and is the only part of `assets/` the build stages, because
the masters are multi-megabyte source artwork.

It emits three kinds of output. The application icon is centre-cropped square
and written at the platform sizes plus a multi-frame `.ico`. The button icons
are cropped to their opaque box and scaled by HEIGHT alone, never squared, at
four times the height the tray draws them at so Qt only ever scales down. The
donate mark is written to the app and the site from one render, so the two
cannot drift.

Two button icons are composites rather than masters: the prohibition bar
(`negative.png`) laid over the icon of the thing being negated, giving delete a
struck-through stored profile and cancel a struck-through edit. Adding a picture
means adding its master, naming it in `generate_icons.py` and naming it in
`icons.py`; the structural tests fail if those three ever disagree.

## Development workflow

### Tests

```powershell
pytest -v --cov
```

The gate is 100% with branch coverage, over everything except the composition
root, the PySide6 views and the two raw-COM modules. Coverage settings live in
`pyproject.toml`. Read `$LASTEXITCODE` rather than the output, because a gated
run prints no "N passed" line. See [TESTING.md](TESTING.md) for the full picture,
including the no-mock-libraries rule and the Qt threading caveat.

### Code quality

```powershell
ruff check
black --check .
mypy src
```

Run these from the repo root with no path arguments. Ruff then covers everything
it should: `src`, `tests`, the build scripts and the `installer` package. It
skips `venv`, `build` and `dist` on its own, because it honours `.gitignore`.

Passing explicit paths such as `ruff check src tests` silently misses the build
scripts and the installer, which is how findings accumulated there unnoticed.

Mypy stays scoped to `src` on purpose: the build scripts and the installer are
not annotated to the same standard. All three checks currently pass.

Qt enums are written in their fully-qualified form (`Qt.ItemDataRole.UserRole`,
not `Qt.UserRole`). PySide6 forwards the shorthand at runtime but its stubs do
not declare it, so the shorthand fails mypy. Keep new code qualified.

Black and ruff are both clean; keep them that way. `src/main.py` carries a
per-file ignore for `E402` and `I001` in `pyproject.toml`, because it inserts the
project root on `sys.path` before importing from `src`. Sorting those imports
would break `python src/main.py`, so leave that ignore in place. The same applies
to `tests/conftest.py`, which sets `QT_QPA_PLATFORM` before its imports and marks
them `# noqa: E402`.

### Code style

- Format with black (line length 88).
- Use type hints and docstrings on public methods.
- Keep modules focused and small; prefer composition over inheritance.
- No magic numbers, no em dashes.

## Versioning

The version string lives only in the root `VERSION` file. `src/version.py` reads
it at runtime and `pyproject.toml` reads it for packaging. To release, edit
`VERSION` and nothing else; do not hardcode a version anywhere in code or docs.

## Release checklist

1. Update `VERSION`.
2. Draft the release notes in `NOTES.md` (local, not committed).
3. Run `pytest -v --cov` and confirm `$LASTEXITCODE` is 0.
4. Run the code-quality checks (`ruff check`, `black --check .`, `mypy src`) and
   confirm each exits 0.
5. Build with `python buildexe.py` then `python buildinstaller.py`.
6. Smoke-test both artefacts: GUI mode, launching twice (the second should raise
   the first window), `--list`, `--profile` and a Stream Deck button.
7. Run the setup program over a copy that is already running. It should offer to
   close Audio Deck, wait for it to go and then install. This path has no
   automated coverage, because it needs a real running program and a real user;
   it is also the path that fails on locked files when it is wrong.
8. Refresh `docs/screenshots/` if the interface changed.
9. Assemble the release with `AudioDeckSetup.exe`, the portable `AudioDeck.exe`,
   `README.md`, `CLI_USAGE.md`, `examples/streamdeck_profiles/` and the licence
   files (`LICENSE`, `LICENSE-GPL-3.0.txt`, `LICENSE-LGPL-3.0.txt`).

## Troubleshooting development issues

### Import errors

Ensure the virtual environment is active, the dependencies are installed and the
project root is on the Python path.

### Running from source appears to do nothing

Another Audio Deck window is already open, most likely an installed or packaged
copy. Only one window is allowed per user, so the second launch defers to the
first (raising its window on Windows) and exits. Close the running copy and
try again.

### Build errors

Delete the `build/` and `dist/` folders, reinstall PyInstaller
(`pip install --upgrade pyinstaller`) and check for missing hidden imports.

### Audio API issues

On Windows, ensure the audio service is running, that devices are enabled and
that pycaw is installed correctly. On Linux, ensure PulseAudio or PipeWire is
running and `pactl info` answers. On macOS, ensure the devices appear in the
system sound settings.

## Contributing

1. Follow the existing architecture and the invariants in ARCHITECTURE.md.
2. Add tests for new behaviour and keep coverage at 100% on the covered surface.
3. Update the documentation.
4. Keep commits focused.

## License

Distributed under two licences, split by component: the backend under
[GPL-3.0](LICENSE-GPL-3.0.txt) and the PySide6 user interface
(`src/presentation`) under [LGPL-3.0](LICENSE-LGPL-3.0.txt). See
[LICENSE](LICENSE) for the map.

Copyright (C) 2024-2026 Oliver Ernster.

## Credits

- Built with PySide6 (Qt for Python).
- Uses pycaw for the Windows Core Audio API, pactl for PulseAudio/PipeWire on
  Linux and CoreAudio via ctypes on macOS.
- Packaged with PyInstaller and Flatpak.
