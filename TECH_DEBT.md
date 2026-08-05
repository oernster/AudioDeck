# AudioDeck: Technical Debt

A standing reference to the project's outstanding technical debt. It records what is still open, weighs whether each item is worth doing and gives the rationale. Every item is a behaviour-preserving internal concern: nothing here proposes reverting a feature or changing any UI or UX behaviour. Scope is the whole repository (the `src` package, the CLI, the bespoke installer, the delivery scripts and the GitHub Pages site under `docs/`) read against `ARCHITECTURE.md`, `TESTING.md` and `tests/structural/test_architecture.py`.

This is a small, tidy repository: roughly 8,000 lines, a 100% gate with a short and well-argued omit list, and a structural suite covering all four layer directions plus a two-entry composition-root whitelist. Only two files exceed 350 lines. The list below is correspondingly short.

---

## 1. The structural suite has no module-size rule, and `main_window.py` is 606 lines

`tests/structural/test_architecture.py` enforces layering in five directions, the composition-root whitelist and the module-level-singleton ban. It asserts nothing about file size.

Two files are affected:

- `src/presentation/views/main_window.py` at 606 lines, half again over the 400-line cap.
- `src/main.py` at 387 lines, inside the 381 to 399 danger band, so the next edit takes it over.

The view is the more interesting of the two. It is omitted from coverage on the documented and correct grounds that widget layout should not be pinned by brittle tests, which means 606 lines are neither measured for size nor exercised by the suite. Whatever decision logic has accumulated in there is invisible to every mechanism the project runs.

Two things close this, and they are independent: add a size assertion to the structural suite so the rule is enforced rather than assumed, and split the view along the seams the package already suggests (`ConfigurationView` and `ActuationView` exist beside it, and the presenters exist below it). Anything in `main_window.py` that a presenter could own should move to a presenter, where the gate can see it.

`src/main.py` should drop to 350 or below in the same pass. It is the composition root, so a root that needs 387 lines is worth a second look regardless of the cap.

## 2. A macOS icon is tracked for a platform the project cannot run on

`assets/audiodeck.icns` is tracked. There is no `builddmg.py`, no Flatpak script and no macOS or Linux delivery path of any kind, and there cannot be one: the whole device layer is raw COM against Windows audio endpoints (`device_enumerator.py`, `windows_device_controller.py`).

The `.icns` is a by-product of `generate_icons.py` emitting the full portfolio icon set regardless of target. It costs nothing but it implies a platform that will never be supported.

`README.md` already states the constraint plainly, under "Who it is not for", so what is left is the tracked asset itself. There are two ways out: teach `generate_icons.py` to skip the macOS output for Windows-only projects and drop the file; or accept it as harmless generator output. The first is the honest one, because the constraint is real: this application manipulates the Windows default audio endpoint and has no meaning elsewhere.

## 3. The CLI writes its own presentation inline

`src/cli/cli_handler.py` is one of the two declared composition roots and it carries twenty-two `print` calls that build the user-facing output directly: profile listings, the bullet-point device summaries, the usage examples, the error text.

This is normal for a CLI and it works. The debt is narrow and specific: `cli_handler.py` is a composition root by the structural test's own definition, so it is permitted to import infrastructure, and it has now also become the presentation layer for the command-line surface. Two responsibilities in the one file the architecture rules deliberately exempt from the usual constraints.

If the CLI grows, the output formatting wants lifting into a small presenter that takes DTOs and returns strings, which is testable and leaves `cli_handler.py` as a genuine root. At its current size this is a watch item, not a task.

## 4. Twenty-five broad exception handlers, almost none with a reason

They fall into two groups:

- **`src/infrastructure/windows/` (nine, across `device_enumerator.py` and `windows_device_controller.py`).** Raw COM. Broad handling is correct here, because COM surfaces failure in many shapes and an audio-device enumeration that raises would take the application down. These need one line each saying what is being degraded to.
- **`src/presentation/presenters/` (eight, across `actuation_presenter.py` and `configuration_presenter.py`).** These matter more. A presenter swallowing an exception means the user pressed a button, the profile did not switch and nothing said so. Actuation is the entire point of the application; a silent failure there is the worst outcome available. Each of these should either surface the failure to the view or be narrowed to the specific exception it is tolerating.

`installer/worker.py:49` shows the house style done correctly (`# surface any failure to the UI`). Apply it everywhere.

## 5. `htmlcov/` is regenerated on every test run

`addopts` includes `--cov-report=html`, so every invocation of `pytest` writes an HTML coverage report into `htmlcov/` at root. It is correctly untracked and correctly ignored, so nothing is broken.

It is listed because the terminal report is the one that is actually read and the HTML report is a build artefact produced unconditionally on a surface that is already gated. Dropping the flag from `addopts` and generating HTML on demand keeps the working tree clean. Minor, and purely a preference until someone is confused by a stale report.

## 6. Two development dependency lists that disagree, one of them naming a banned library

`requirements-dev.txt` and the `dev` extra in `pyproject.toml` both claim to describe the development environment and they do not match. The extra adds `pytest-mock` and `hypothesis`; neither appears in `requirements-dev.txt` and neither is imported anywhere in `tests/`.

`pytest-mock` is the one that matters. TESTING.md states as a rule that the suite uses no mock libraries and the suite honours that, so advertising the plugin as a development dependency invites the next contributor to reach for exactly the thing the project has decided against. `hypothesis` is merely unused.

The fix is to pick one list as authoritative (`requirements-dev.txt` is the one the documentation tells people to install) and make the other match it or point at it, dropping both unused entries in the process.

---

## Looks like debt, not worth touching

- The `I`-prefixed interface naming (`IDeviceRepository`, `IDeviceController`, `IProfileRepository`). Unconventional for Python and entirely consistent throughout.
- The `examples/streamdeck_profiles/*.bat` files and `launch_audio_deck.bat`. These are the Stream Deck integration surface: the whole point of the CLI is that a Stream Deck button runs a `.bat`. They are examples for users, not code.
- `src/presentation/workers/background_runner.py` at 23 lines with a single broad handler. A thread wrapper whose job is to not let a worker exception kill the app.
- The `docs/` site being two hand-written pages (`index.html`, `why.html`) with no generator. At that size a generator would cost more than it saves.
- `AudioDeck.spec` at root is a PyInstaller artefact and is untracked.

## Not debt (do not "fix" these)

These look like candidates but are correct as they stand; changing them would regress or add cost for nothing.

- **The coverage omit list.** Five entries, each with a written reason: package markers hold no logic; the composition root builds real COM objects and a `QApplication`; views are asserted by looking at the running app rather than by brittle tests; and the two COM modules would need real hardware and would change the machine's actual default audio device. That last reason is the strongest argument in any omit list in this portfolio, because running those tests would have a side effect on the developer's own machine.
- **`test_cli_infrastructure_imports_stay_in_its_composition_root()` and `test_presentation_never_imports_the_cli()`.** Two application entry points (GUI and CLI) sharing one core, with the boundary between them held by AST scan rather than by convention. Exactly right, and unusual enough to be worth naming.
- **The two-entry `COMPOSITION_ROOTS` whitelist** (`main.py`, `cli_handler.py`). A dual-entry-point application legitimately has two roots, and naming both explicitly is what keeps the exemption honest.
- **`VERSION` at root.** Single source of truth, and no hardcoded version string anywhere else in the tree.
- **The domain being pure entities, value objects, interfaces and exceptions with no I/O.** Small, correct and enforced.
