# AudioDeck: Technical Debt

A standing reference to the project's outstanding technical debt. It records what is still open, weighs whether each item is worth doing and gives the rationale. Every item is a behaviour-preserving internal concern: nothing here proposes reverting a feature or changing any UI or UX behaviour. Scope is the whole repository (the `src` package, the CLI, the bespoke installer, the delivery scripts and the GitHub Pages site under `docs/`) read against `ARCHITECTURE.md`, `TESTING.md` and `tests/structural/test_architecture.py`.

This is a small, tidy repository: roughly 8,000 lines, a 100% gate with a short and well-argued omit list, plus a structural suite covering all four layer directions, a two-entry composition-root whitelist and the module size rule in two tiers. One file exceeds 330 lines (`configuration_view.py` at 341, comfortably under the cap and clear of the danger band). One open item remains, and it is a watch item rather than a task.

---

## 1. The CLI writes its own presentation inline

`src/cli/cli_handler.py` is one of the two declared composition roots and it carries twenty-two `print` calls that build the user-facing output directly: profile listings, the bullet-point device summaries, the usage examples, the error text.

This is normal for a CLI and it works. The debt is narrow and specific: `cli_handler.py` is a composition root by the structural test's own definition, so it is permitted to import infrastructure, yet it has now also become the presentation layer for the command-line surface. Two responsibilities in the one file the architecture rules deliberately exempt from the usual constraints.

If the CLI grows, the output formatting wants lifting into a small presenter that takes DTOs and returns strings, which is testable and leaves `cli_handler.py` as a genuine root. At its current size this is a watch item, not a task.

---

## Looks like debt, not worth touching

- The `I`-prefixed interface naming (`IDeviceRepository`, `IDeviceController`, `IProfileRepository`). Unconventional for Python and entirely consistent throughout.
- The `examples/streamdeck_profiles/*.bat` files and `launch_audio_deck.bat`. These are the Stream Deck integration surface: the whole point of the CLI is that a Stream Deck button runs a `.bat`. They are examples for users, not code.
- `src/presentation/workers/background_runner.py` at 23 lines with a single broad handler. A thread wrapper whose job is to not let a worker exception kill the app.
- The broad handlers in `src/infrastructure/windows/`. COM surfaces failure in many shapes, and an endpoint that vanishes mid-enumeration during a device change is ordinary rather than exceptional, so narrowing them would mean naming every shape `comtypes` can raise and would take the application down when it missed one. Each now states what it degrades to, in the house style of `installer/worker.py:49`. If a `BLE` rule is ever added to `[tool.ruff.lint]`, these want `# noqa: BLE001` rather than rewriting.
- The `docs/` site being two hand-written pages (`index.html`, `why.html`) with no generator. At that size a generator would cost more than it saves.
- `AudioDeck.spec` at root is a PyInstaller artefact and is untracked.

## Not debt (do not "fix" these)

These look like candidates but are correct as they stand; changing them would regress or add cost for nothing.

- **The coverage omit list.** Five entries, each with a written reason: package markers hold no logic; the composition root builds real COM objects and a `QApplication`; views are asserted by looking at the running app rather than by brittle tests; and the two COM modules would need real hardware and would change the machine's actual default audio device. That last reason is the strongest argument in any omit list in this portfolio, because running those tests would have a side effect on the developer's own machine.
- **The two-tier module size rule.** The cap at 400 lines plus a danger band whose width is derived from the cap, so the two numbers cannot drift apart. A module that reaches the band is taken to 350 rather than trimmed by a line, because shaving one line off buys nothing: the next edit puts it straight back over. Delivery scripts at the repo root are deliberately out of scope, being linear recipes where splitting costs more than it saves.
- **`test_cli_infrastructure_imports_stay_in_its_composition_root()` and `test_presentation_never_imports_the_cli()`.** Two application entry points (GUI and CLI) sharing one core, with the boundary between them held by AST scan rather than by convention. Exactly right, plus unusual enough to be worth naming.
- **The two-entry `COMPOSITION_ROOTS` whitelist** (`main.py`, `cli_handler.py`). A dual-entry-point application legitimately has two roots; naming both explicitly is what keeps the exemption honest.
- **`VERSION` at root.** Single source of truth, with no hardcoded version string anywhere else in the tree.
- **The domain being pure entities, value objects, interfaces and exceptions with no I/O.** Small, correct and enforced.
