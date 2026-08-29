# Testing

How Audio Deck is tested, what the coverage gate measures and what it
deliberately does not. For the design see [ARCHITECTURE.md](ARCHITECTURE.md);
for developer setup see [DEVELOPMENT_README.md](DEVELOPMENT_README.md).

## Running the tests

```powershell
pip install -r requirements-dev.txt
pytest -v --cov
```

That is the whole command. Coverage settings live in `pyproject.toml` under
`[tool.coverage.run]`, so the flags do not have to be remembered.

Read the **exit code**, not the output. A coverage-gated run prints the coverage
table last and emits no "N passed" summary line, so grepping the text for
`passed` or `failed` matches coverage filenames instead of results.

```powershell
pytest -v --cov
$LASTEXITCODE   # 0 = all tests passed AND the coverage gate was met
```

Useful variations:

```powershell
pytest -q --no-cov                      # fast run, no coverage
pytest tests/domain -p no:cacheprovider # one layer
pytest --cov-report=html                # then open htmlcov/index.html
```

## The gate

The build fails below **100 percent**, measured with **branch coverage** as well
as statement coverage. This is deliberate: at 100 percent a gap is a signal
rather than noise, because it can only be one of two things.

- A missing test, which should be written.
- Unreachable code, which should be deleted.

Branch coverage found exactly that in `cli_handler`: an `if profiles:` guard
whose false path could never run, because the empty case had already returned
earlier. The fix was to remove the dead branch, not to write a test for it.

## What is measured

The coverage gate measures `src/` only. The installer has its own tests under
`tests/installer/` and is held to the structural rules; it sits outside the
percentage gate: most of it is Qt window construction, judged by running the
setup program rather than by brittle tests.

Everything under `src/` except the exclusions below, which is the domain, the
application layer, the repositories (profiles, devices and the update
settings), the update check's GitHub adapter, the CLI, the presenters, the
version reader, the single-instance guard, the device-change notifier and the
background worker.

## What is excluded and why

Set in `[tool.coverage.run]` in `pyproject.toml`. Each exclusion is a considered
decision rather than a convenience.

| Excluded | Why |
| --- | --- |
| `*/__init__.py` | Package markers hold no logic |
| `src/main.py` | The composition root builds real COM objects and a QApplication; wiring is proved by running the app |
| `src/presentation/views/*` | PySide6 widget construction. Layout is judged by looking at the running app, not by brittle tests that break on every UI tweak |
| `src/infrastructure/windows/device_enumerator.py` | Raw COM enumeration against live Windows audio endpoints, needing real hardware |
| `src/infrastructure/windows/windows_device_controller.py` | Sets the machine's actual default devices. A test that ran this would change your audio while it ran |

The two COM modules are excluded at the module level but not untested in effect:
everything that consumes them is driven through fakes at their seams, so the
logic around them is fully covered.

Line-level exclusions (`[tool.coverage.report]`) cover `pragma: no cover`,
`if TYPE_CHECKING:`, `raise NotImplementedError` and bare `...` Protocol bodies.

## No mock libraries

There is no `unittest.mock`, no `MagicMock` and no `pytest-mock` in the suite.
Doubles are hand written and live in `tests/conftest.py`: `FakeEnumerator`,
`FakeDeviceController` and small fakes for each use case. Where a real
implementation is safe it is used directly, so `JsonProfileRepository` is tested
against real files in a `tmp_path`.

`monkeypatch` is used sparingly for things like `sys.argv` and `sys._MEIPASS`.
It is a pytest builtin for patching attributes, not a mock framework, so it does
not conflict with this rule.

Qt is never mocked. Qt tests use a real `QApplication` through pytest-qt's
`qapp` fixture, with `QT_QPA_PLATFORM=offscreen` set in `tests/conftest.py` at
import time so the suite runs headless.

## Layout

`tests/` mirrors `src/`.

```
tests/
  conftest.py       Hand-written doubles, shared fixtures, headless Qt setup
  domain/           Entities, value objects, exceptions, Protocol conformance
  application/      Use cases and DTOs
  infrastructure/   JSON repository, device repository, single-instance guard
  presentation/     Presenters, background worker, device-change notifiers,
                    the keyboard navigator, the auto-scroller, the donate
                    button and the header's fit to the window
  cli/              Argument parsing and the CLI handler
  installer/        The setup program's screen model, its running-app
                    detection and its locked-file reporting
  structural/       Source scans enforcing the layer boundaries, the module
                    size rule, the focus-ring rules and the icon contract
  test_version.py   The VERSION file reader
```

## Testing patterns worth knowing

**Platform APIs go behind a Protocol.** `SingleInstanceGuard` takes a `MutexApi`,
so its logic is tested against a fake while the real `Win32MutexApi` stays a thin
`pragma: no cover` shim. Anything needing a Win32 call should follow this shape.

**Native event filters can be tested directly.** The device-change notifier is
exercised by building a real `ctypes` `MSG`, so the pointer cast is genuinely
executed rather than stubbed.

**Code on a QThread is not traced.** Coverage cannot see code Qt runs on a native
thread, so `_Worker._run` is unit-tested directly on the main thread while
separate tests cover the cross-thread wiring. If a new module runs work on a
QThread, expect the same split.

**Structural tests guard the architecture.** `tests/structural/` parses the
source so a violation fails the build rather than being caught in review.
Twenty checks currently run, in three files.

`test_architecture.py` holds nine, scanning imports with `ast`: the domain and
application boundaries, presentation not importing infrastructure or the CLI,
CLI infrastructure imports staying inside its composition root, the
composition-root whitelist, a scan for module-level service singletons, the
400-line module cap and the danger band beneath it.

The last two are the module size rule in its two tiers. The cap is 400 lines and
the band is the top 5% of it, so a file between 381 and 399 fails and has to come
down to 350 rather than being trimmed by a line. The band width is derived from
the cap in the test rather than written as a second literal, so the two numbers
cannot drift apart. The rule measures `src`, `installer` and `tests`. Delivery
scripts are exempt wherever they live, being linear recipes where splitting
costs more than it saves: that covers the scripts at the repo root and
`installer/build_payload.py`, which is one of them by nature rather than by
location. The installer was outside this measurement until its window reached
422 lines with nothing reporting it, which is why the scope is now named
explicitly.

`test_focus_rings.py` holds six, scanning the stylesheet sources rather than
imports. No ring selector may reach a container, no region may ring under the
mouse and no item view may ring in any state, because a list already shows the
user where they are through its current item. Four checks assert the rules; the
other two plant a violation of each kind and assert it is reported, so the guard
cannot quietly rot into a no-op. The scan is static on purpose: an offscreen
pixel diff cannot settle what a focus ring paints, since a focused button diffs
to zero changed pixels under every style tried.

`test_icon_assets.py` holds five, checking the artwork contract rather than the
source. The UI names its pictures by action and resolves them at runtime, so a
name with no file behind it draws nothing and the button still builds, sizes and
tooltips itself: deliberate, so one missing asset costs a control rather than
the window, which is exactly why it has to fail here instead. The five assert
that every name resolves, that every name is one the generator actually
produces, that every master the generator reads is committed, that artwork is
rendered at least four times the height it is drawn at so Qt only ever scales
down, plus that no runtime path reaches past the generated set into the masters.
Each was proved to bite by planting a violation and reading the exit code.

If you add a new entry point, add it to `COMPOSITION_ROOTS` in
`tests/structural/test_architecture.py` and say why in ARCHITECTURE.md. The
whitelist is meant to make a third composition root a deliberate decision rather
than an accident.

## Adding tests

1. Put the test beside its layer, mirroring `src/`.
2. Prefer the real implementation. If it touches COM, the network or the user's
   machine, put it behind a Protocol and write a fake.
3. Name the test for the behaviour, not the method: `test_second_instance_is_refused`
   rather than `test_acquire_returns_false`.
4. Run `pytest -v --cov` and check `$LASTEXITCODE` is 0 before handing over.
