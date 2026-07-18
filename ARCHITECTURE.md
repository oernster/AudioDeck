# Architecture

Audio Deck follows a clean, layered architecture:
`UI -> Application -> Domain <- Infrastructure`. The domain is pure and depends
on nothing; the application orchestrates use cases over domain interfaces;
infrastructure implements those interfaces against Windows and the filesystem;
the UI and the CLI are clients of the application layer only.

## Invariants

These properties are non-negotiable. Each is intended to be verified by the test
suite rather than left to convention.

| Invariant | Why | Enforced by |
| --- | --- | --- |
| The domain layer imports no framework, no I/O and no platform code | Keeps business rules portable and unit-testable in isolation | Structural import-scan test (`tests/structural/test_architecture.py`) |
| The application layer depends only on the domain and the standard library | Use cases stay decoupled from Qt, COM and storage details | Structural import-scan test |
| Infrastructure implements domain interfaces and is never imported by the domain or application | Dependency direction stays inward; Windows and JSON stay swappable | Structural import-scan test |
| The UI and the CLI depend only on the application layer | One composition root wires concretes; views stay passive | Structural import-scan test |
| Dependencies are wired in one explicit composition root, with constructor injection only | No hidden singletons or service locators | Composition-root whitelist test |
| The version string exists only in the root `VERSION` file | Single source of truth; no drift across code and packaging | `version.py` reads `VERSION`; `pyproject.toml` reads the same file |
| Code is formatted with black and passes flake8 | Mechanical consistency without review effort | `black --check` and `flake8` run as in-suite assertions |

The test suite targets 100% coverage measured with `pytest -v --cov`, using real
implementations where safe and small hand-written fakes at the Windows boundary,
with no mock libraries. Fragile PySide6 UI views and the raw-COM enumerator and
controller are excluded from coverage via `.coveragerc`, so the meaningful
surface (domain, application, repository logic, CLI and presenters) stays at
100%. The suite is being established; until each check lands, these invariants
are maintained by review.

## Layers

```
src/
  domain/              Pure business model
    entities/          AudioDevice, AudioProfile
    value_objects/     DeviceType, DeviceState
    interfaces/        IDeviceRepository, IDeviceController, IProfileRepository (Protocols)
    exceptions/        AudioDeckException hierarchy
  application/          Use cases and data transfer objects
    use_cases/         Get/Create/Update/Delete/GetProfiles, GetDevices, SwitchProfile
    dtos/              DeviceDTO, ProfileDTO, SwitchOutcome
  infrastructure/       External integrations
    windows/           Core Audio enumeration and control (pycaw, comtypes)
    persistence/       JSON profile storage
  presentation/         GUI layer (PySide6)
    views/             MainWindow, ConfigurationView, ActuationView
    presenters/        ConfigurationPresenter, ActuationPresenter (MVP)
    notifiers/         WindowsDeviceChangeNotifier (WM_DEVICECHANGE)
  cli/                  Headless command-line interface
  main.py              Composition root and entry point
```

## Dependency direction

```
   presentation (UI)        cli
            \              /
             v            v
              application
                  |
                  v
                domain   <----  infrastructure
```

The domain sits at the centre and is depended upon by everything else. The
application defines what it needs as domain interfaces (Protocols). Infrastructure
implements those interfaces; it points inward at the domain and is never pointed
at by it.

## Execution flow

### GUI

1. `main.py` parses arguments. With no CLI arguments it builds the GUI.
2. A `SingleInstanceGuard` takes a named mutex scoped to the logon session. If
   another instance already holds it, this process raises that instance's window
   and exits 0 without constructing anything.
3. It constructs the infrastructure (device enumerator, device controller, device
   repository, JSON profile repository), then the application use cases, then the
   presenters, then `MainWindow`.
4. Views call presenter methods; presenters call use cases; use cases act through
   domain interfaces implemented by infrastructure.
5. Presenters report outcomes back to views with Qt signals
   (`error_occurred`, `profile_saved`, `profile_switched`, `device_unavailable`,
   `current_devices_changed`, `auto_applied`).
6. Device changes are delivered two ways: a `WindowsDeviceChangeNotifier`
   (native `WM_DEVICECHANGE`) and a periodic timer fallback both call the
   actuation presenter's `on_devices_changed`, which refreshes the current
   defaults and re-applies any profile device that has just reconnected.

### CLI

1. `main.py` detects CLI arguments (`--list` or `--profile`) and delegates to
   `CLIHandler`.
2. `CLIHandler` builds the same infrastructure and use cases, runs the requested
   action and returns a process exit code.

The GUI and the CLI share the application and domain layers; only the entry path
and the presentation differ.

## Data model

A profile is an `AudioProfile` that holds an id, a name, an optional output
device id, an optional input device id and timestamps. Switching a profile sets
the Windows default endpoint for each configured device across the Console,
Multimedia and Communications roles.

Devices carry a `DeviceState` (available, disconnected, disabled or not present)
so disconnected hardware can be listed and selected. A switch returns a
`SwitchOutcome` recording which devices were applied and which were skipped (and
why), which drives partial application and the auto-apply-on-reconnect flow.

Profiles are persisted as a JSON array under
`%LOCALAPPDATA%\AudioDeck\profiles.json`:

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

## Design decisions

| Decision | Rationale |
| --- | --- |
| Clean layered architecture with Protocol interfaces | Lets the Windows audio backend and the JSON store be replaced or faked without touching business rules |
| MVP for the GUI | Keeps logic in testable presenters and views passive |
| Local JSON persistence | Local-first, no service or account; the file is portable and easy to back up |
| Shared application core for GUI and CLI | One set of use cases, two front ends; no duplicated switching logic |
| Single `VERSION` file as source of truth | Runtime and packaging read the same value; nothing else hardcodes a version |
| Windows-only Core Audio via pycaw | Direct, dependency-light access to the platform default-endpoint policy |
| Partial application with a SwitchOutcome | A profile with one offline device still applies the available one, rather than failing outright |
| Event-driven device changes (WM_DEVICECHANGE) plus a timer fallback | Reconnected devices apply promptly without polling, while the timer guarantees recovery if no event arrives |
| Single-instance guard on the GUI only, never the CLI | Two windows editing one profiles file would race; the CLI must stay freely runnable because that is how a Stream Deck button drives it |
| Named mutex rather than a lock file or port | Creating a named mutex is one atomic Win32 call, so two simultaneous launches cannot both win, and it cannot be left stale by a crash |
| The guard fails open | If Windows refuses the mutex the application still starts; a guard that cannot be established must never be the reason it will not run |

## Quality enforcement

- Formatting: black (line length 88).
- Linting: flake8 and ruff.
- Types: mypy.
- Tests: pytest with coverage, 100% target on the non-UI surface, no mock
  libraries (see the invariants section above).
