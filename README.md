# Audio Deck

A professional audio device switcher for Windows with Stream Deck integration.

## Features

- **Two Modes**:
  - **Quick Switch Mode**: Instantly switch between saved audio profiles
  - **Configuration Mode**: Create and manage audio profiles with custom input/output device combinations

- **Clean Architecture**: Built with SOLID principles and Clean Architecture
- **Windows Integration**: Native Windows Core Audio API integration via pycaw
- **Stream Deck Ready**: Can be launched as a macro from Elgato Stream Deck
- **Persistent Profiles**: JSON-based profile storage

## Requirements

- Windows 10/11
- Python 3.10 or higher (for development)
- Elgato Stream Deck (optional, for macro integration)

## Installation

### For Users (Standalone Executable)

1. Download the latest release from the releases page
2. Extract `AudioDeck.exe` to a folder of your choice
3. Run `AudioDeck.exe` or use `launch_audio_deck.bat` with Stream Deck

### For Developers

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

4. Install development dependencies (optional):
```bash
pip install -r requirements-dev.txt
```

## Usage

### Running from Source

```bash
python src/main.py
```

### Building Executable

```bash
python build_exe.py
```

The executable will be created in the `dist` folder.

### Stream Deck Integration

1. Build the executable using `python build_exe.py`
2. In Stream Deck software, add a "System > Open" action
3. Point it to `launch_audio_deck.bat` or directly to `dist/AudioDeck.exe`
4. Optionally add a custom icon

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
└── presentation/        # GUI layer
    ├── views/          # PySide6 views
    └── presenters/     # MVP presenters
```

### Key Design Patterns

- **Clean Architecture**: Dependency inversion, separation of concerns
- **MVP Pattern**: Model-View-Presenter for GUI
- **Repository Pattern**: Abstract data access
- **Use Case Pattern**: Single responsibility business logic
- **Protocol-based Interfaces**: Duck typing for testability

## Development

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

## Project Structure

```
AudioDeck/
├── src/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── presentation/
│   └── main.py
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── build_exe.py
├── launch_audio_deck.bat
└── README.md
```

## Configuration

Profiles are stored in: `%LOCALAPPDATA%\AudioDeck\profiles.json`

## Troubleshooting

### Audio devices not showing up
- Ensure you have audio devices connected
- Try refreshing the device list using the 🔄 button
- Check Windows Sound settings to verify devices are enabled

### Profile switching not working
- Verify the devices in the profile still exist
- Check that devices are enabled in Windows
- Try recreating the profile with current devices

### Executable won't run
- Ensure you have the Visual C++ Redistributable installed
- Check Windows Defender/antivirus isn't blocking it
- Run as administrator if needed

## License

[Your License Here]

## Contributing

Contributions are welcome! Please follow the existing code style and architecture patterns.

## Credits

- Built with PySide6 (Qt for Python)
- Uses pycaw for Windows Core Audio API access
- Packaged with PyInstaller