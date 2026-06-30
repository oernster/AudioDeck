"""Structural tests enforcing the clean-architecture dependency direction.

These scan the source for imports that would violate the layer boundaries
described in ARCHITECTURE.md.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent / "src"

DOMAIN = SRC / "domain"
APPLICATION = SRC / "application"

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


def test_domain_has_no_outward_dependencies():
    assert _violations(DOMAIN, DOMAIN_FORBIDDEN) == []


def test_application_depends_only_on_domain():
    assert _violations(APPLICATION, APPLICATION_FORBIDDEN) == []
