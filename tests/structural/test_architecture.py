"""Structural tests enforcing the clean-architecture dependency direction.

These scan the source for imports that would violate the layer boundaries
described in ARCHITECTURE.md.
"""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = PROJECT_ROOT / "src"
TESTS = PROJECT_ROOT / "tests"

DOMAIN = SRC / "domain"
APPLICATION = SRC / "application"
PRESENTATION = SRC / "presentation"
CLI = SRC / "cli"

# The only modules permitted to name infrastructure concretes. Everything else
# receives its dependencies through a constructor. Two entries because the GUI
# and the CLI are separate entry points: main.py wires the GUI, while
# CLIHandler.from_profiles_path wires the headless path.
COMPOSITION_ROOTS = frozenset({"main.py", "cli_handler.py"})

# The module size limit, plus the band just under it where a file is one edit
# from breaking the rule. Shaving a module to a line under the cap buys
# nothing, because the next change puts it back over and the same file gets
# refactored again and again, so a module that reaches the band is taken to
# DANGER_BAND_TARGET instead. The band width is derived from the cap rather
# than written as a second literal, so the two cannot drift apart.
MAX_MODULE_LINES = 400
DANGER_BAND_FRACTION = 0.05
DANGER_BAND_FLOOR = MAX_MODULE_LINES - int(MAX_MODULE_LINES * DANGER_BAND_FRACTION)
DANGER_BAND_TARGET = 350

# A module-level name bound to a call of a class matching one of these suffixes
# would be a hidden singleton, wired outside a composition root.
SERVICE_SUFFIXES = (
    "UseCase",
    "Repository",
    "Controller",
    "Presenter",
    "Enumerator",
    "Guard",
    "Notifier",
)

# Substrings that must never appear in an import within a given layer.
DOMAIN_FORBIDDEN = (
    "src.application",
    "src.infrastructure",
    "src.presentation",
    "src.cli",
    "PySide6",
    "pycaw",
    "comtypes",
)
APPLICATION_FORBIDDEN = (
    "src.infrastructure",
    "src.presentation",
    "src.cli",
    "PySide6",
    "pycaw",
    "comtypes",
)


def _imported_names(path: Path):
    """Yield every imported module name in a source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            yield node.module


def _violations(layer_dir: Path, forbidden):
    found = []
    for path in layer_dir.rglob("*.py"):
        for name in _imported_names(path):
            for bad in forbidden:
                if name.startswith(bad):
                    found.append(f"{path.name}: {name}")
    return found


def _module_level_service_bindings(path: Path):
    """Yield module-level names bound to a service-looking constructor call."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        called = (
            func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        )
        if called.endswith(SERVICE_SUFFIXES):
            for target in node.targets:
                name = getattr(target, "id", "<expr>")
                yield f"{path.name}: {name} = {called}(...)"


def test_domain_has_no_outward_dependencies():
    assert _violations(DOMAIN, DOMAIN_FORBIDDEN) == []


def test_application_depends_only_on_domain():
    assert _violations(APPLICATION, APPLICATION_FORBIDDEN) == []


def test_presentation_never_imports_infrastructure():
    # Views and presenters receive their use cases; they never build them.
    assert _violations(PRESENTATION, ("src.infrastructure",)) == []


def test_presentation_never_imports_the_cli():
    assert _violations(PRESENTATION, ("src.cli",)) == []


def test_cli_infrastructure_imports_stay_in_its_composition_root():
    offenders = [
        f"{path.name}: {name}"
        for path in CLI.rglob("*.py")
        if path.name not in COMPOSITION_ROOTS
        for name in _imported_names(path)
        if name.startswith("src.infrastructure")
    ]
    assert offenders == []


def _line_count(path: Path) -> int:
    """Return how many lines a module has."""
    return len(path.read_text(encoding="utf-8").splitlines())


def test_only_composition_roots_import_infrastructure():
    # Infrastructure may import itself; everything else outside it must be
    # wired by a composition root rather than reaching for a concrete.
    offenders = [
        f"{path.relative_to(SRC)}: {name}"
        for path in SRC.rglob("*.py")
        if path.name not in COMPOSITION_ROOTS
        and "infrastructure" not in path.relative_to(SRC).parts
        for name in _imported_names(path)
        if name.startswith("src.infrastructure")
    ]
    assert offenders == []


def test_no_module_level_service_singletons():
    offenders = [
        finding
        for path in SRC.rglob("*.py")
        for finding in _module_level_service_bindings(path)
    ]
    assert offenders == []


def _measured_modules() -> list[Path]:
    """Return every module the size rule applies to.

    The application package and the tests. Delivery scripts at the repo root
    are deliberately out of scope: they are linear recipes of flags and steps,
    where splitting a sequence across modules costs more than it saves.
    """
    return sorted(SRC.rglob("*.py")) + sorted(TESTS.rglob("*.py"))


def test_no_module_exceeds_the_line_limit():
    # Size is a structural property like layering: left unmeasured, a view
    # reaches 600 lines and nothing anywhere reports it.
    offenders = [
        f"{path.relative_to(PROJECT_ROOT)}: {_line_count(path)} lines"
        for path in _measured_modules()
        if _line_count(path) > MAX_MODULE_LINES
    ]
    assert offenders == []


def test_no_module_sits_in_the_danger_band():
    # A module just under the cap is one edit from breaking it, so it is taken
    # to DANGER_BAND_TARGET rather than trimmed by a line.
    offenders = [
        f"{path.relative_to(PROJECT_ROOT)}: {_line_count(path)} lines, take it "
        f"to {DANGER_BAND_TARGET} or fewer"
        for path in _measured_modules()
        if DANGER_BAND_FLOOR < _line_count(path) < MAX_MODULE_LINES
    ]
    assert offenders == []
