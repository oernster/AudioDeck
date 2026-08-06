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

- Windows 10 or Windows 11.
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

Only one Audio Deck window may be open per Windows user. If an installed or
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
imports and bundles the icon, the `VERSION` file, the licence and the
documentation. Build identity and inputs live at the top of `buildexe.py`.

## Project structure

```
AudioDeck/
  src/
    domain/          Pure business model
    application/     Use cases and DTOs
    infrastructure/  Windows Core Audio and JSON storage
    presentation/    PySide6 GUI (views, presenters, notifiers, workers)
    cli/             Command-line interface
    main.py          Entry point and GUI composition root
  tests/             Mirrors src/, plus structural boundary tests
  installer/         The bespoke themed setup application
  assets/            Generated icon set (one master image)
  docs/              GitHub Pages site and screenshots
  examples/          Stream Deck batch-file templates
  VERSION            Single source of truth for the version
  buildexe.py        Portable executable
  buildinstaller.py  Setup executable, run after buildexe.py
  generate_icons.py  Regenerates assets/ from the master image
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
  `UpdateProfile`, `DeleteProfile`, `SwitchProfile`) and the DTOs (`DeviceDTO`,
  `ProfileDTO`, `SwitchOutcome`). `SwitchProfile` returns a `SwitchOutcome` so a
  profile applies its available devices and reports any that are skipped.
- **Infrastructure**: `WindowsDeviceEnumerator`, `WindowsDeviceController` and
  `WindowsDeviceRepository` (Core Audio via pycaw and comtypes),
  `JsonProfileRepository` plus `SingleInstanceGuard` (a named mutex that keeps
  the GUI to one instance per logon session, with the Win32 calls behind
  Protocols so the logic is testable). The enumerator lists disconnected and
  disabled devices too, so they can be selected.
- **Presentation**: `MainWindow`, `ConfigurationView`, `ActuationView` and their
  presenters (MVP), plus `WindowsDeviceChangeNotifier` (a `WM_DEVICECHANGE`
  filter) that drives live updates and auto-apply on reconnect, `BackgroundRunner`
  (a serial worker thread keeping COM and settle sleeps off the GUI thread) and
  `icons` (the emoji button glyphs, defined once as named constants).
- **CLI**: `argument_parser` and `cli_handler`, sharing the application layer.

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
7. Refresh `docs/screenshots/` if the interface changed.
8. Assemble the release with `AudioDeckSetup.exe`, the portable `AudioDeck.exe`,
   `README.md`, `CLI_USAGE.md`, `examples/streamdeck_profiles/` and `LICENSE`.

## Troubleshooting development issues

### Import errors

Ensure the virtual environment is active, the dependencies are installed and the
project root is on the Python path.

### Running from source appears to do nothing

Another Audio Deck window is already open, most likely an installed or packaged
copy. Only one window is allowed per Windows user, so the second launch raises
the first and exits. Close the running copy and try again.

### Build errors

Delete the `build/` and `dist/` folders, reinstall PyInstaller
(`pip install --upgrade pyinstaller`) and check for missing hidden imports.

### Audio API issues

Ensure the Windows audio service is running, that devices are enabled in Windows
and that pycaw is installed correctly.

## Contributing

1. Follow the existing architecture and the invariants in ARCHITECTURE.md.
2. Add tests for new behaviour and keep coverage at 100% on the covered surface.
3. Update the documentation.
4. Keep commits focused.

## License

GNU Lesser General Public License v3.0 (LGPL-3.0). See [LICENSE](LICENSE).

Copyright (C) 2024-2026 Oliver Ernster.

## Credits

- Built with PySide6 (Qt for Python).
- Uses pycaw for the Windows Core Audio API.
- Packaged with PyInstaller.
