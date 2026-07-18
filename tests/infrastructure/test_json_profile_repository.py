"""Tests for the JSON profile repository (real filesystem on tmp_path)."""

from uuid import uuid4

import pytest

import src.infrastructure.persistence.json_profile_repository as repo_module
from src.domain.exceptions.domain_exceptions import ProfileStorageException
from src.infrastructure.persistence.json_profile_repository import (
    JsonProfileRepository,
)
from tests.conftest import save_profile


def test_init_creates_file(tmp_path):
    path = tmp_path / "nested" / "profiles.json"
    JsonProfileRepository(path)
    assert path.exists()


def test_save_new_and_get_all(profile_repo):
    save_profile(profile_repo, "A")
    assert len(profile_repo.get_all()) == 1


def test_save_updates_existing(profile_repo):
    profile = save_profile(profile_repo, "A")
    profile.update(name="A2")
    profile_repo.save(profile)
    all_profiles = profile_repo.get_all()
    assert len(all_profiles) == 1
    assert all_profiles[0].name == "A2"


def test_get_by_id_found_and_missing(profile_repo):
    profile = save_profile(profile_repo, "A")
    assert profile_repo.get_by_id(profile.id).id == profile.id
    assert profile_repo.get_by_id(uuid4()) is None


def test_delete(profile_repo):
    profile = save_profile(profile_repo, "A")
    profile_repo.delete(profile.id)
    assert profile_repo.get_all() == []


def test_exists(profile_repo):
    profile = save_profile(profile_repo, "A")
    assert profile_repo.exists(profile.id) is True
    assert profile_repo.exists(uuid4()) is False


def test_get_by_name_found_and_missing(profile_repo):
    save_profile(profile_repo, "Named")
    assert profile_repo.get_by_name("Named").name == "Named"
    assert profile_repo.get_by_name("Nope") is None


def test_read_invalid_json_raises(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text("not json", encoding="utf-8")
    repo = JsonProfileRepository(path)
    with pytest.raises(ProfileStorageException, match="parse"):
        repo.get_all()


def test_read_bad_structure_raises(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text('[{"id": "not-a-uuid"}]', encoding="utf-8")
    repo = JsonProfileRepository(path)
    with pytest.raises(ProfileStorageException, match="read"):
        repo.get_all()


def test_write_failure_raises(profile_repo, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(repo_module.json, "dump", boom)
    with pytest.raises(ProfileStorageException, match="write"):
        save_profile(profile_repo, "A")
