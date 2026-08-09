"""Tests for the update settings store: best-effort by design."""

import json

from src.infrastructure.persistence.json_update_settings_repository import (
    JsonUpdateSettingsRepository,
)


def repo(tmp_path):
    return JsonUpdateSettingsRepository(tmp_path / "update_settings.json")


def test_fresh_install_has_nothing_skipped(tmp_path):
    assert repo(tmp_path).get_skipped_version() is None


def test_roundtrip(tmp_path):
    repository = repo(tmp_path)
    repository.set_skipped_version("v1.5.0")
    assert repository.get_skipped_version() == "v1.5.0"


def test_survives_a_new_instance(tmp_path):
    repo(tmp_path).set_skipped_version("v1.5.0")
    assert repo(tmp_path).get_skipped_version() == "v1.5.0"


def test_preserves_unrelated_keys(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text(json.dumps({"other": 1}), encoding="utf-8")
    JsonUpdateSettingsRepository(path).set_skipped_version("v1.5.0")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["other"] == 1
    assert data["skipped_update_version"] == "v1.5.0"


def test_damaged_file_reads_as_nothing_skipped(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text("{broken", encoding="utf-8")
    assert JsonUpdateSettingsRepository(path).get_skipped_version() is None


def test_damaged_file_is_rewritten_on_save(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text("{broken", encoding="utf-8")
    repository = JsonUpdateSettingsRepository(path)
    repository.set_skipped_version("v1.5.0")
    assert repository.get_skipped_version() == "v1.5.0"


def test_non_dict_document_reads_as_nothing_skipped(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text("[1, 2]", encoding="utf-8")
    assert JsonUpdateSettingsRepository(path).get_skipped_version() is None


def test_non_string_value_reads_as_nothing_skipped(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text(json.dumps({"skipped_update_version": 42}), encoding="utf-8")
    assert JsonUpdateSettingsRepository(path).get_skipped_version() is None


def test_empty_string_reads_as_nothing_skipped(tmp_path):
    path = tmp_path / "update_settings.json"
    path.write_text(json.dumps({"skipped_update_version": ""}), encoding="utf-8")
    assert JsonUpdateSettingsRepository(path).get_skipped_version() is None


def test_missing_parent_directory_is_created(tmp_path):
    repository = JsonUpdateSettingsRepository(tmp_path / "deep" / "settings.json")
    repository.set_skipped_version("v1.5.0")
    assert repository.get_skipped_version() == "v1.5.0"


def test_unwritable_path_fails_silently(tmp_path):
    # The target path IS a directory, so the write raises and is swallowed.
    target = tmp_path / "update_settings.json"
    target.mkdir()
    repository = JsonUpdateSettingsRepository(target)
    repository.set_skipped_version("v1.5.0")
    assert repository.get_skipped_version() is None
