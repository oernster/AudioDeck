# Audio Deck - Developer Documentation

**Author:** Oliver Ernster

Technical notes for working on the AudioDeck codebase. For user documentation see
[README.md](README.md). For the design and its invariants see
[ARCHITECTURE.md](ARCHITECTURE.md).

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

### Building the executable

```bash
python buildexe.py
```

The executable is written to `dist/AudioDeck.exe`. The build uses PyInstaller in
`--onefile --windowed` mode (a single windowed binary that still serves the CLI
when run with arguments), collects `comtypes`, declares the `pycaw` hidden
imports and bundles the icon, the `VERSION` file, the licence and the
documentation. Build identity and inputs live at the top of `buildexe.py`.

## Architecture

The codebase is a clean, layered architecture
(`UI -> Application -> Domain <- Infrastructure`) shared by the GUI and the CLI.
The full description, the dependency direction, the execution flow and the
enforced invariants are in [ARCHITECTURE.md](ARCHITECTURE.md). Key components:

- **Domain**: `AudioDevice` and `AudioProfile` entities, `DeviceType` and
  `DeviceState` value objects, the repository and controller Protocols, and the
  exception hierarchy.
- **Application**: the use cases (`GetDevices`, `GetProfiles`, `CreateProfile`,
  `UpdateProfile`, `DeleteProfile`, `SwitchProfile`) and the DTOs (`DeviceDTO`,
  `ProfileDTO`, `SwitchOutcome`). `SwitchProfile` returns a `SwitchOutcome` so a
  profile applies its available devices and reports any that are skipped.
- **Infrastructure**: `WindowsDeviceEnumerator`, `WindowsDeviceController` and
  `WindowsDeviceRepository` (Core Audio via pycaw and comtypes), and
  `JsonProfileRepository`. The enumerator lists disconnected and disabled devices
  too, so they can be selected.
- **Presentation**: `MainWindow`, `ConfigurationView`, `ActuationView` and their
  presenters (MVP), plus `WindowsDeviceChangeNotifier` (a `WM_DEVICECHANGE`
  filter) that drives live updates and auto-apply on reconnect.
- **CLI**: `argument_parser` and `cli_handler`, sharing the application layer.

## Development workflow

### Tests

```bash
pytest -v --cov
```

The suite targets 100% coverage on the non-UI surface, uses real implementations
where safe and small hand-written fakes at the Windows boundary, and uses no mock
libraries. Fragile PySide6 UI views and the raw-COM enumerator and controller are
excluded from coverage in `.coveragerc`.

### Code quality

```bash
black src tests
flake8 src tests
ruff check src tests
mypy src
```

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
2. Run `pytest -v --cov` and confirm it passes.
3. Run the code-quality checks (black, flake8, ruff, mypy).
4. Build with `python buildexe.py`.
5. Smoke-test the executable: GUI mode, `--list`, `--profile` and a Stream Deck
   button.
6. Assemble the release with `AudioDeck.exe`, `README.md`,
   `DEVELOPMENT_QUICKSTART.md`, `examples/streamdeck_profiles/` and `LICENSE`.

## Troubleshooting development issues

### Import errors

Ensure the virtual environment is active, the dependencies are installed and the
project root is on the Python path.

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
