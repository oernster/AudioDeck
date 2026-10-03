"""Tests for the whole-file writer and the tolerant reader (audit A-1)."""

import sys

import pytest

import src.infrastructure.persistence.atomic_file as atomic_module
from src.infrastructure.persistence.atomic_file import (
    read_tolerantly,
    write_atomically,
)


def test_the_replace_waits_out_a_reader_holding_the_file(tmp_path, monkeypatch):
    # Windows refuses to replace a file another process has open (measured:
    # PermissionError, winerror 5), so a reader holding it briefly is waited
    # out rather than turned into a failed save.
    path = tmp_path / "file.json"
    real_replace = atomic_module.os.replace
    refusals = [PermissionError("held"), PermissionError("held")]
    waits = []

    def replace_refused_twice(source, target):
        if refusals:
            raise refusals.pop()
        real_replace(source, target)

    monkeypatch.setattr(atomic_module.os, "replace", replace_refused_twice)
    write_atomically(path, lambda handle: handle.write("new"), sleep=waits.append)

    assert path.read_text(encoding="utf-8") == "new"
    assert len(waits) == 2


def test_the_replace_gives_up_after_a_bounded_wait(tmp_path, monkeypatch):
    path = tmp_path / "file.json"
    path.write_text("old", encoding="utf-8")
    waits = []

    def always_refused(source, target):
        raise PermissionError("held")

    monkeypatch.setattr(atomic_module.os, "replace", always_refused)
    with pytest.raises(PermissionError):
        write_atomically(path, lambda handle: handle.write("new"), sleep=waits.append)

    assert len(waits) == atomic_module.SHARING_ATTEMPTS - 1
    assert path.read_text(encoding="utf-8") == "old"
    assert [p.name for p in tmp_path.iterdir()] == ["file.json"]


def test_a_read_waits_out_a_replace_in_progress(tmp_path, monkeypatch):
    path = tmp_path / "file.json"
    path.write_text("whole", encoding="utf-8")
    real_read = type(path).read_text
    refusals = [PermissionError("mid-replace")]

    def read_refused_once(self, *args, **kwargs):
        if refusals:
            raise refusals.pop()
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(type(path), "read_text", read_refused_once)
    waits = []
    assert read_tolerantly(path, sleep=waits.append) == "whole"
    assert len(waits) == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Windows file sharing rules")
def test_a_save_succeeds_once_a_real_reader_lets_go(tmp_path):
    path = tmp_path / "file.json"
    path.write_text("old", encoding="utf-8")
    reader = open(path, encoding="utf-8")

    def reader_finishes(_seconds):
        reader.close()

    write_atomically(path, lambda handle: handle.write("new"), sleep=reader_finishes)
    assert reader.closed
    assert path.read_text(encoding="utf-8") == "new"
