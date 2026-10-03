"""A profile save never destroys the profiles already on disk (audit A-1).

The disk-full fault is injected where the profiles are serialised: the
writer emits part of the document and then fails, exactly as a full disk
fails part way through a write. The file is then read back, because a
message alone proves nothing about what is left on disk.
"""

import errno
import json

import pytest

import src.infrastructure.persistence.json_profile_repository as repo_module
from src.domain.exceptions.domain_exceptions import ProfileStorageException
from src.infrastructure.persistence.json_profile_repository import (
    JsonProfileRepository,
)
from tests.conftest import save_profile

# How much of the document the failing writer emits before the disk fills.
_PARTIAL_CHARACTERS = 40
_NAMES = ("Gaming", "Work", "Music")
_BACKUP_NAME = "profiles.json.bak"


def _three_profiles(path):
    repository = JsonProfileRepository(path)
    for name in _NAMES:
        save_profile(repository, name)
    return repository


def _disk_fills_part_way(data, handle, **kwargs):
    handle.write(json.dumps(data, **kwargs)[:_PARTIAL_CHARACTERS])
    raise OSError(errno.ENOSPC, "No space left on device")


def test_a_save_that_fails_part_way_keeps_every_profile(tmp_path, monkeypatch):
    path = tmp_path / "profiles.json"
    repository = _three_profiles(path)
    monkeypatch.setattr(repo_module.json, "dump", _disk_fills_part_way)

    with pytest.raises(ProfileStorageException, match="No space left"):
        save_profile(repository, "Fourth")

    monkeypatch.undo()
    names = [profile.name for profile in JsonProfileRepository(path).get_all()]
    assert names == list(_NAMES)


def test_a_failed_save_leaves_no_temporary_file(tmp_path, monkeypatch):
    path = tmp_path / "profiles.json"
    repository = _three_profiles(path)
    monkeypatch.setattr(repo_module.json, "dump", _disk_fills_part_way)

    with pytest.raises(ProfileStorageException):
        save_profile(repository, "Fourth")

    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "profiles.json",
        _BACKUP_NAME,
    ]


def test_a_reader_during_a_save_sees_the_previous_profiles(tmp_path, monkeypatch):
    path = tmp_path / "profiles.json"
    gui = JsonProfileRepository(path)
    save_profile(gui, "Gaming")
    cli = JsonProfileRepository(path)
    real_dump = json.dump
    seen = []

    def dump_while_another_process_reads(data, handle, **kwargs):
        seen.append([profile.name for profile in cli.get_all()])
        real_dump(data, handle, **kwargs)

    monkeypatch.setattr(repo_module.json, "dump", dump_while_another_process_reads)
    save_profile(gui, "Work")

    assert seen == [["Gaming"]]
    assert [profile.name for profile in cli.get_all()] == ["Gaming", "Work"]


def test_a_save_keeps_the_last_good_copy_as_a_backup(tmp_path):
    path = tmp_path / "profiles.json"
    repository = JsonProfileRepository(path)
    save_profile(repository, "First")
    save_profile(repository, "Second")

    backup = json.loads((tmp_path / _BACKUP_NAME).read_text(encoding="utf-8"))
    assert [entry["name"] for entry in backup] == ["First"]


def test_an_unreadable_file_names_the_backup(tmp_path):
    path = tmp_path / "profiles.json"
    repository = JsonProfileRepository(path)
    save_profile(repository, "First")
    save_profile(repository, "Second")
    path.write_text("[{", encoding="utf-8")

    with pytest.raises(ProfileStorageException, match=_BACKUP_NAME):
        repository.get_all()
