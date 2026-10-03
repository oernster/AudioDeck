"""Structural tests enforcing the clean-architecture dependency direction.

These scan the source for imports that would violate the layer boundaries
described in ARCHITECTURE.md.
"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = PROJECT_ROOT / "src"
TESTS = PROJECT_ROOT / "tests"

DOMAIN = SRC / "domain"
APPLICATION = SRC / "application"
PRESENTATION = SRC / "presentation"
CLI = SRC / "cli"
INSTALLER = PROJECT_ROOT / "installer"

# Delivery scripts are exempt from the size rule wherever they live: they are
# linear recipes read top to bottom, so splitting them costs more than it buys.
DELIVERY_SCRIPTS = frozenset({"build_payload.py"})

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

# The name a call to the __import__ builtin is reported under, so a layer can
# forbid it like any module.
DYNAMIC_IMPORT = "__import__"

# Package that roots every module path; relative imports resolve from it.
SOURCE_PACKAGE = "src"

# Prefixes that must never begin an import within a given layer.
DOMAIN_FORBIDDEN = (
    "src.application",
    "src.infrastructure",
    "src.presentation",
    "src.cli",
    "PySide6",
    "pycaw",
    "comtypes",
    # Dynamic imports, processes and native calls are platform reach by
    # another route; the domain needs none of them.
    "importlib",
    "subprocess",
    "ctypes",
    DYNAMIC_IMPORT,
)
APPLICATION_FORBIDDEN = (
    "src.infrastructure",
    "src.presentation",
    "src.cli",
    "PySide6",
    "pycaw",
    "comtypes",
)


def _package_of(path: Path) -> list:
    """Return the dotted package parts of a module, from the src root down.

    Found by walking up to the nearest folder named src, so the same rule
    resolves the real tree and a throwaway one planted under a temp folder.
    """
    parts = list(path.parent.parts)
    root = len(parts) - 1 - parts[::-1].index(SOURCE_PACKAGE)
    return parts[root:]


def _absolute(path: Path, node: ast.ImportFrom):
    """Yield the absolute module names a from-import refers to.

    `from ...infrastructure import x` resolves against the module's own
    package; `from ... import infrastructure` names a module in each alias.
    """
    if node.level == 0:
        yield node.module or ""
        return
    package = _package_of(path)
    base = ".".join(package[: len(package) - (node.level - 1)])
    if node.module is not None:
        yield f"{base}.{node.module}"
        return
    for alias in node.names:
        yield f"{base}.{alias.name}"


def _imported_names(path: Path):
    """Yield every imported module name in a source file, made absolute.

    A call to the __import__ builtin yields DYNAMIC_IMPORT, because what it
    loads is a string the scan cannot follow.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield from _absolute(path, node)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == DYNAMIC_IMPORT
        ):
            yield DYNAMIC_IMPORT


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

    The application package, the bespoke installer and the tests. Delivery
    scripts are deliberately out of scope: they are linear recipes of flags
    and steps, where splitting a sequence across modules costs more than it
    saves. That covers the scripts at the repo root and the installer's own
    payload builder, which is one of them by nature rather than by location.

    The installer was omitted here until its window reached 422 lines with
    nothing reporting it, while TECH_DEBT.md described it as in scope. A rule
    that names a file and never measures it is not a rule.
    """
    installer_modules = [
        path
        for path in sorted(INSTALLER.rglob("*.py"))
        if path.name not in DELIVERY_SCRIPTS
    ]
    return sorted(SRC.rglob("*.py")) + installer_modules + sorted(TESTS.rglob("*.py"))


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


# Every spelling the audit found passing the scan (A-12), planted one at a time
# into a throwaway domain package. The positive control is the plain absolute
# import the scan always caught.
PLANTED_DOMAIN_VIOLATIONS = {
    "absolute": "from src.infrastructure.caching_device_repository import C\n",
    "relative": "from ...infrastructure.caching_device_repository import C\n",
    "relative_bare": "from ... import infrastructure\n",
    "dynamic": 'import importlib\nimportlib.import_module("src.cli")\n',
    "dynamic_from": "from importlib import import_module\n",
    "dunder": 'm = __import__("PySide6.QtCore")\n',
    "subprocess": "import subprocess\n",
    "ctypes": "import ctypes\n",
    "ctypes_from": "from ctypes import wintypes\n",
}


def _plant_in_domain(tmp_path: Path, source: str) -> Path:
    """Write one module into a throwaway src/domain/entities package."""
    domain = tmp_path / "src" / "domain"
    package = domain / "entities"
    package.mkdir(parents=True)
    (package / "planted.py").write_text(source, encoding="utf-8")
    return domain


@pytest.mark.parametrize(
    "source",
    list(PLANTED_DOMAIN_VIOLATIONS.values()),
    ids=list(PLANTED_DOMAIN_VIOLATIONS),
)
def test_the_domain_scan_catches_every_spelling(tmp_path, source):
    domain = _plant_in_domain(tmp_path, source)
    assert _violations(domain, DOMAIN_FORBIDDEN) != []


def test_a_relative_import_inside_the_domain_is_allowed(tmp_path):
    domain = _plant_in_domain(tmp_path, "from ..value_objects import device_type\n")
    assert _violations(domain, DOMAIN_FORBIDDEN) == []


# Every composition root builds the same per-user switch lock, so the window
# and a Stream Deck key never interleave (audit A-9). A root that forgot it
# would run unlocked with no test noticing, since the roots are not covered.
SWITCH_LOCK_FACTORY = "create_switch_lock"


def test_every_composition_root_wires_the_switch_lock():
    roots = [SRC / "main.py", CLI / "cli_handler.py"]
    unwired = [
        root.name
        for root in roots
        if f"{SWITCH_LOCK_FACTORY}(" not in root.read_text(encoding="utf-8")
    ]
    assert unwired == []
