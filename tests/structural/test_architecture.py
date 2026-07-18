"""Structural tests enforcing the clean-architecture dependency direction.

These scan the source for imports that would violate the layer boundaries
described in ARCHITECTURE.md.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent / "src"

DOMAIN = SRC / "domain"
APPLICATION = SRC / "application"
PRESENTATION = SRC / "presentation"
CLI = SRC / "cli"

# The only modules permitted to name infrastructure concretes. Everything else
# receives its dependencies through a constructor. Two entries because the GUI
# and the CLI are separate entry points: main.py wires the GUI, and
# CLIHandler.from_profiles_path wires the headless path.
COMPOSITION_ROOTS = frozenset({"main.py", "cli_handler.py"})

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
