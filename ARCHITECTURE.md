# Architecture

Audio Deck follows a clean, layered architecture:
`UI -> Application -> Domain <- Infrastructure`. The domain is pure and depends
on nothing; the application orchestrates use cases over domain interfaces;
infrastructure implements those interfaces against each platform's audio stack
(Windows Core Audio, PulseAudio/PipeWire, macOS CoreAudio) and the filesystem;
the UI and the CLI are clients of the application layer only.

## Invariants

These properties are non-negotiable. Each is intended to be verified by the test
suite rather than left to convention.

| Invariant | Why | Enforced by |
| --- | --- | --- |
| The domain layer imports no framework, no I/O and no platform code | Keeps business rules portable and unit-testable in isolation | Structural import-scan test (`tests/structural/test_architecture.py`) |
| The application layer depends only on the domain and the standard library | Use cases stay decoupled from Qt, COM and storage details | Structural import-scan test |
| Infrastructure implements domain interfaces and is never imported by the domain or application | Dependency direction stays inward; the platform backends and JSON stay swappable | Structural import-scan test |
| The presentation layer never imports infrastructure | Views and presenters receive their use cases rather than building them | Structural import-scan test |
| Only a composition root names an infrastructure concrete | Everything else is constructor-injected and stays swappable | Composition-root whitelist test (`main.py` and `cli_handler.py`) |
| No module-level service singletons | No hidden global state or service locators | Structural AST scan for module-level service construction |
| The version string exists only in the root `VERSION` file | Single source of truth; no drift across code and packaging | `version.py` reads `VERSION`; `pyproject.toml` reads the same file |
| Code is formatted with black, lint-clean under ruff and type-clean under mypy | Mechanical consistency without review effort | `black --check .`, `ruff check` and `mypy src`, all run manually |
| Only one GUI instance runs per user session | Two windows would race over the same profiles file | Named-mutex guard on Windows, flocked lock file on Linux and macOS, covered by `tests/infrastructure/test_single_instance.py` and `test_posix_single_instance.py` |
| Every testable line and branch is covered | A gap is either a missing test or dead code; both should fail the build | `pytest -v --cov`, gated at 100% with branch coverage (see [TESTING.md](TESTING.md)) |

The test suite targets 100% coverage measured with `pytest -v --cov`, using real
implementations where safe and small hand-written fakes at each platform
boundary, with no mock libraries. Fragile PySide6 UI views and the raw-COM
enumerator and controller are excluded from coverage via the
`[tool.coverage.run]` omit list in `pyproject.toml`; the real pactl, CoreAudio,
flock and Win32 call wrappers carry `# pragma: no cover` for the same reason,
so the meaningful surface (domain, application, all backend logic over its
seam, repository logic, CLI and presenters) stays at 100%.

There are two composition roots, not one, because the GUI and the CLI are
separate entry points: `main.py` wires the GUI and `CLIHandler.from_profiles_path`
wires the headless path. The whitelist test names both, so adding a third would
fail the build rather than pass unnoticed.

The presentation layer does import a small number of domain types (the exception
hierarchy and `DeviceType`), which is deliberate: presenters translate domain
errors for display. The enforced rule is therefore the one that matters, that
presentation never reaches for infrastructure.

## Layers

```
src/
  domain/              Pure business model
    entities/          AudioDevice, AudioProfile
    value_objects/     DeviceType, DeviceState, ReleaseInfo/ReleaseAsset
    interfaces/        IDeviceRepository, IDeviceController, IDeviceEnumerator,
                       IProfileRepository, IReleaseSource,
                       IUpdateSettingsRepository (Protocols)
    exceptions/        AudioDeckException hierarchy
  application/          Use cases and data transfer objects
    use_cases/         Get/Create/Update/Delete/GetProfiles, GetDevices,
                       SwitchProfile, CheckForUpdates (with the version compare
                       and platform asset selection beside it)
    dtos/              DeviceDTO, ProfileDTO, SwitchOutcome, UpdateStatus
  infrastructure/       External integrations
    backend_factory.py Platform dispatch: builds the enumerator, controller and
                       single-instance guard for sys.platform
    caching_device_repository.py
                       Platform-neutral repository answering queries from the
                       last enumeration, shared by all three backends
    windows/           Core Audio enumeration and control (pycaw, comtypes),
                       SingleInstanceGuard (named mutex, Win32 behind Protocols)
    linux/             PulseAudio/PipeWire enumeration and control over the
                       pactl command (subprocess behind a Protocol)
    macos/             CoreAudio enumeration and control over ctypes (behind a
                       Protocol; devices identified by stable UID)
    posix/             Lock-file single instance (flock behind a Protocol),
                       shared by Linux and macOS
    persistence/       JSON profile storage; JSON update-settings storage
    updates/           GitHubReleaseSource (stdlib urllib against the GitHub
                       releases/latest endpoint, opener injected for tests)
  presentation/         GUI layer (PySide6)
    views/             MainWindow, ConfigurationView, ActuationView, the
                       header tray recipes (tray.py) and theme facility
                       (theme.py: dark and light token dicts, stylesheet and
                       palette builders, persistence), the Help button and
                       its dialogs, icons, the update dialogs
                       (offer / up to date / failed)
    presenters/        ConfigurationPresenter, ActuationPresenter,
                       UpdatePresenter (MVP)
    widgets/           KeyboardNavigator (the explicit focus ring),
                       AutoScroller (self-reading help surfaces),
                       glyph metrics (measured emoji sizing)
    notifiers/         Device-change notifiers per platform behind one factory:
                       WM_DEVICECHANGE (Windows), pactl subscribe (Linux),
                       periodic polling (macOS)
    workers/           BackgroundRunner (keeps device work off the GUI thread)
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
2. The single-instance guard from `create_single_instance(sys.platform)` takes
   its per-user lock (a named mutex on Windows, a flocked lock file on Linux
   and macOS). If another instance already holds it, this process exits 0
   without constructing anything, first raising the other window where the
   platform allows it (Windows only).
3. It constructs the infrastructure (the platform backend from
   `create_device_backend(sys.platform)`, the caching device repository, the
   JSON profile repository), then the application use cases, then the
   presenters, then `MainWindow`.
4. Views call presenter methods; presenters call use cases; use cases act through
   domain interfaces implemented by infrastructure.
5. Presenters report outcomes back to views with Qt signals
   (`error_occurred`, `profile_saved`, `profile_switched`, `device_unavailable`,
   `status_ready`, `auto_applied`).
6. Device changes are delivered by the platform's notifier (native
   `WM_DEVICECHANGE` on Windows, a long-lived `pactl subscribe` process on
   Linux, a periodic poll on macOS) plus a periodic timer fallback; both call
   the actuation presenter's `on_devices_changed`, which refreshes the current
   defaults and re-applies any profile device that has just reconnected.
7. The update check runs a few seconds after launch, once a day and on demand
   from Help > Check for Updates. The `UpdatePresenter` runs the
   `CheckForUpdates` use case through its own `BackgroundRunner` and reports
   through `update_available`, `up_to_date` and `check_failed`; the window
   shows a Download / Skip This Version / Later prompt, with the skip persisted
   beside the profiles and honoured only by the automatic path. Every failure
   collapses to None in the adapter, so an automatic check that cannot reach
   GitHub says nothing.

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
the system default for each configured device: on Windows across the Console,
Multimedia and Communications roles, on Linux the default sink and source, on
macOS the default output and input device.

Devices carry a `DeviceState` (available, disconnected, disabled or not present)
so disconnected hardware can be listed and selected. A switch returns a
`SwitchOutcome` recording which devices were applied and which were skipped (and
why), which drives partial application and the auto-apply-on-reconnect flow.

The update check keeps its one setting (the skipped version) in
`update_settings.json`, beside the profiles but in its own file so neither
store's failure rules leak into the other.

Profiles are persisted as a JSON array in the platform's per-user app-data
directory (`%LOCALAPPDATA%\AudioDeck` on Windows, `$XDG_DATA_HOME/audiodeck`
on Linux, `~/Library/Application Support/AudioDeck` on macOS):

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
| Clean layered architecture with Protocol interfaces | Lets each platform's audio backend and the JSON store be replaced or faked without touching business rules |
| MVP for the GUI | Keeps logic in testable presenters and views passive |
| Local JSON persistence | Local-first, no service or account; the file is portable and easy to back up |
| Shared application core for GUI and CLI | One set of use cases, two front ends; no duplicated switching logic |
| Single `VERSION` file as source of truth | Runtime and packaging read the same value; nothing else hardcodes a version |
| One platform backend per operating system behind shared Protocols | Windows Core Audio via pycaw, PulseAudio/PipeWire via pactl, macOS CoreAudio via ctypes; the domain, application, presenters and CLI are identical on all three |
| pactl subprocess on Linux rather than a Python PulseAudio library | pactl ships with every PulseAudio and PipeWire desktop, so the port adds no Python dependency; JSON output keeps the parsing testable |
| ctypes CoreAudio on macOS rather than pyobjc | The needed HAL surface is a handful of stable C calls; pyobjc would be a heavyweight dependency for that sliver |
| macOS devices identified by UID, not AudioDeviceID | The AudioDeviceID is transient across reboots and unplugs; the UID is stable, so profiles survive |
| Partial application with a SwitchOutcome | A profile with one offline device still applies the available one, rather than failing outright |
| Event-driven device changes where the platform provides events, polling where it does not | WM_DEVICECHANGE (Windows) and pactl subscribe (Linux) are push; macOS polls on a slow timer because a CoreAudio listener's C callback lifetime rules are a crash risk from Python |
| Single-instance guard on the GUI only, never the CLI | Two windows editing one profiles file would race; the CLI must stay freely runnable because that is how a Stream Deck button drives it |
| Named mutex on Windows, flocked lock file on POSIX | Each is one atomic kernel operation that cannot be left stale by a crash |
| The guard fails open | If the lock cannot be created at all the application still starts; a guard that cannot be established must never be the reason it will not run |
| The update check reads only GitHub's `releases/latest` endpoint | That endpoint returns only a published, non-draft, non-prerelease release, so a tag pushed mid-development can never prompt; nothing re-checks those flags client-side |
| Unparseable versions compare as not-newer | A malformed tag can never raise a spurious prompt and a `0.0.0-dev` source run stays silent |
| The update settings store is best-effort where the profile store raises | Profiles are user content; losing a skipped-version note costs one extra prompt, so a failed write is swallowed rather than surfaced |

## Quality enforcement

- Formatting: black (line length 88). Clean.
- Linting: ruff. Clean. Note that `src/main.py` carries a per-file ignore for
  `E402` and `I001` in `pyproject.toml`, because it inserts the project root on
  `sys.path` before importing from `src`; sorting those imports would break
  running `python src/main.py` directly. Do not remove that ignore.
- Types: mypy over `src`, in its strict configuration. Clean. Qt enums must be
  written fully qualified (`Qt.ItemDataRole.UserRole`, not `Qt.UserRole`);
  PySide6 forwards the shorthand at runtime but does not declare it in its
  stubs, so the shorthand form fails type checking.
- Tests: pytest with statement and branch coverage, gated at 100% over the
  measured surface, with no mock libraries. See [TESTING.md](TESTING.md) for
  what is measured, what is excluded and why.
