# Audio Deck - Developer Documentation

**Author:** Oliver Ernster
**Version:** 1.0.1

This document contains technical information for developers who want to contribute to or understand the AudioDeck codebase.

## For Users

If you're looking for user documentation, please see [README.md](README.md) instead.

## Development Setup

### Prerequisites

- Windows 10/11
- Python 3.10 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AudioDeck
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running from Source

```bash
# GUI mode (default)
python src/main.py

# CLI mode - List profiles
python src/main.py --list

# CLI mode - Switch to a profile
python src/main.py --profile "Gaming Setup"
```

### Building Executable

```bash
python build_exe.py
```

The executable will be created in the `dist` folder.

## Architecture

The application follows Clean Architecture principles with clear separation of concerns:

```
src/
├── domain/              # Business logic and entities
│   ├── entities/        # Core business objects
│   ├── value_objects/   # Immutable value types
│   ├── interfaces/      # Abstract interfaces (Protocols)
│   └── exceptions/      # Domain exceptions
├── application/         # Use cases and DTOs
│   ├── use_cases/       # Business use cases
│   └── dtos/           # Data transfer objects
├── infrastructure/      # External integrations
│   ├── windows/        # Windows audio API integration
│   └── persistence/    # Profile storage
├── presentation/        # GUI layer
│   ├── views/          # PySide6 views
│   └── presenters/     # MVP presenters
└── cli/                # Command-line interface
    ├── argument_parser.py
    └── cli_handler.py
```

### Key Design Patterns

- **Clean Architecture**: Dependency inversion, separation of concerns
- **MVP Pattern**: Model-View-Presenter for GUI
- **Repository Pattern**: Abstract data access
- **Use Case Pattern**: Single responsibility business logic
- **Protocol-based Interfaces**: Duck typing for testability

### Layer Responsibilities

#### Domain Layer
- Contains core business logic and entities
- No dependencies on external frameworks
- Defines interfaces (protocols) for external dependencies
- Pure Python, framework-agnostic

#### Application Layer
- Implements use cases (business operations)
- Orchestrates domain entities
- Uses DTOs for data transfer
- Independent of UI and infrastructure details

#### Infrastructure Layer
- Implements domain interfaces
- Handles Windows Core Audio API integration
- Manages profile persistence (JSON)
- Contains platform-specific code

#### Presentation Layer
- PySide6-based GUI
- MVP pattern for testability
- Views are passive, presenters contain logic
- Communicates with application layer via use cases

#### CLI Layer
- Command-line interface for automation
- Headless profile switching
- Uses same application layer as GUI

## Development Workflow

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions small and focused
- Prefer composition over inheritance

## Project Structure

```
AudioDeck/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── interfaces/
│   │   └── exceptions/
│   ├── application/
│   │   ├── use_cases/
│   │   └── dtos/
│   ├── infrastructure/
│   │   ├── windows/
│   │   └── persistence/
│   ├── presentation/
│   │   ├── views/
│   │   └── presenters/
│   ├── cli/
│   └── main.py
├── tests/
├── examples/
│   └── streamdeck_profiles/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── build_exe.py
├── README.md
└── DEVELOPMENT_README.md
```

## Key Components

### Domain Entities

- **AudioProfile**: Represents a saved audio configuration
- **AudioDevice**: Represents an audio input/output device

### Use Cases

- **GetDevicesUseCase**: Retrieve available audio devices
- **CreateProfileUseCase**: Create a new profile
- **UpdateProfileUseCase**: Update an existing profile
- **DeleteProfileUseCase**: Delete a profile
- **GetProfilesUseCase**: Retrieve all profiles
- **SwitchProfileUseCase**: Switch to a specific profile

### Infrastructure

- **WindowsDeviceEnumerator**: Enumerates Windows audio devices
- **WindowsDeviceController**: Controls Windows audio devices
- **WindowsDeviceRepository**: Repository for device data
- **JsonProfileRepository**: JSON-based profile storage

### Presentation

- **MainWindow**: Main application window
- **ConfigurationView**: Profile configuration interface
- **ActuationView**: Quick profile switching interface
- **ConfigurationPresenter**: Presenter for configuration view
- **ActuationPresenter**: Presenter for actuation view

## Configuration

Profiles are stored in: `%LOCALAPPDATA%\AudioDeck\profiles.json`

Format:
```json
[
  {
    "id": "uuid-here",
    "name": "Profile Name",
    "output_device_id": "device-id",
    "input_device_id": "device-id",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

## Dependencies

### Runtime Dependencies
- **PySide6**: Qt for Python (GUI framework)
- **pycaw**: Python Core Audio Windows Library
- **comtypes**: COM interface support

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatter
- **ruff**: Fast Python linter
- **mypy**: Static type checker
- **PyInstaller**: Executable builder

## Building and Distribution

### Building the Executable

The `build_exe.py` script uses PyInstaller to create a standalone executable:

```python
python build_exe.py
```

Key PyInstaller options:
- `--onefile`: Single file executable
- `--console`: Show console for CLI support
- `--icon=icon.ico`: Application icon
- `--hidden-import`: Include pycaw and comtypes
- `--collect-all=comtypes`: Include all comtypes data

### Distribution Checklist

1. Update version number in:
   - `src/main.py`
   - `src/cli/argument_parser.py`
   - `src/presentation/views/main_window.py`
   - `README.md`

2. Run tests: `pytest`

3. Run code quality checks:
   ```bash
   black src tests
   ruff check src tests
   mypy src
   ```

4. Build executable: `python build_exe.py`

5. Test executable:
   - GUI mode
   - CLI mode (`--list`, `--profile`)
   - Stream Deck integration

6. Create release package with:
   - `AudioDeck.exe`
   - `README.md`
   - `DEVELOPMENT_QUICKSTART.md`
   - `examples/streamdeck_profiles/`
   - `LICENSE`

## Contributing

### Guidelines

1. Follow the existing architecture and design patterns
2. Write tests for new features
3. Update documentation
4. Follow code style guidelines
5. Keep commits focused and atomic

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request with a clear description

## Troubleshooting Development Issues

### Import Errors

If you encounter import errors, ensure:
- Virtual environment is activated
- All dependencies are installed: `pip install -r requirements.txt`
- Python path includes the project root

### Build Errors

If PyInstaller fails:
- Clean build cache: delete `build/` and `dist/` folders
- Reinstall PyInstaller: `pip install --upgrade pyinstaller`
- Check for missing hidden imports

### Audio API Issues

If audio device enumeration fails:
- Ensure Windows audio service is running
- Check that audio devices are enabled in Windows
- Verify pycaw is properly installed

## License

MIT License

Copyright (c) 2024 Oliver Ernster

## Credits

- **Author:** Oliver Ernster
- Built with PySide6 (Qt for Python)
- Uses pycaw for Windows Core Audio API access
- Packaged with PyInstaller
- Icon: Speaker/Audio icon