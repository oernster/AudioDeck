"""Tests for the single-source-of-truth version reader."""

import sys
from pathlib import Path

from src import version as version_module

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
BUNDLED_VERSION = "9.9.9-bundled"


def _expected() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def test_reads_the_repo_version_file():
    assert version_module._read_version() == _expected()


def test_module_version_matches_the_file():
    assert version_module.__version__ == _expected()


def test_version_is_stripped():
    assert version_module.__version__ == version_module.__version__.strip()


def test_frozen_bundle_directory_wins(monkeypatch, tmp_path):
    (tmp_path / "VERSION").write_text(BUNDLED_VERSION, encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version_module._read_version() == BUNDLED_VERSION


def test_falls_back_to_repo_when_bundle_has_no_version(monkeypatch, tmp_path):
    # A frozen bundle without a VERSION file must not shadow the repo copy.
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert version_module._read_version() == _expected()


def test_dev_sentinel_when_nothing_is_readable(monkeypatch):
    def unreadable(*_args, **_kwargs):
        raise OSError("no version file")

    monkeypatch.setattr(Path, "read_text", unreadable)
    assert version_module._read_version() == version_module._DEV_FALLBACK
