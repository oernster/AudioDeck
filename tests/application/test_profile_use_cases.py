"""Tests for the profile create/update/delete/get use cases (real JSON repo)."""

from uuid import uuid4

import pytest

from src.application.use_cases.create_profile_use_case import CreateProfileUseCase
from src.application.use_cases.update_profile_use_case import UpdateProfileUseCase
from src.application.use_cases.delete_profile_use_case import DeleteProfileUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.domain.exceptions.domain_exceptions import (
    ProfileNotFoundException,
    ProfileStorageException,
)

from tests.conftest import save_profile

# --- Create -------------------------------------------------------------------


def test_create_profile(profile_repo):
    use_case = CreateProfileUseCase(profile_repo)
    dto = use_case.execute("Gaming", output_device_id="o", input_device_id="i")
    assert dto.name == "Gaming"
    assert profile_repo.get_by_name("Gaming") is not None


def test_create_duplicate_name_raises(profile_repo):
    use_case = CreateProfileUseCase(profile_repo)
    use_case.execute("Gaming")
    with pytest.raises(ProfileStorageException, match="already exists"):
        use_case.execute("Gaming")


# --- Update -------------------------------------------------------------------


def test_update_profile(profile_repo):
    profile = save_profile(profile_repo, "Old")
    use_case = UpdateProfileUseCase(profile_repo)
    dto = use_case.execute(profile.id, name="New", output_device_id="o2")
    assert dto.name == "New"
    assert dto.output_device_id == "o2"


def test_update_missing_raises(profile_repo):
    use_case = UpdateProfileUseCase(profile_repo)
    with pytest.raises(ProfileNotFoundException):
        use_case.execute(uuid4(), name="X")


def test_update_name_conflict_raises(profile_repo):
    save_profile(profile_repo, "Taken")
    target = save_profile(profile_repo, "Mine")
    use_case = UpdateProfileUseCase(profile_repo)
    with pytest.raises(ProfileStorageException, match="already exists"):
        use_case.execute(target.id, name="Taken")


def test_update_same_name_allowed(profile_repo):
    profile = save_profile(profile_repo, "Same")
    use_case = UpdateProfileUseCase(profile_repo)
    dto = use_case.execute(profile.id, name="Same", output_device_id="o3")
    assert dto.output_device_id == "o3"


# --- Delete -------------------------------------------------------------------


def test_delete_profile(profile_repo):
    profile = save_profile(profile_repo, "Bye")
    use_case = DeleteProfileUseCase(profile_repo)
    use_case.execute(profile.id)
    assert profile_repo.get_by_id(profile.id) is None


def test_delete_missing_raises(profile_repo):
    use_case = DeleteProfileUseCase(profile_repo)
    with pytest.raises(ProfileNotFoundException):
        use_case.execute(uuid4())


# --- Get ----------------------------------------------------------------------


def test_get_all_profiles(profile_repo):
    save_profile(profile_repo, "A")
    save_profile(profile_repo, "B")
    use_case = GetProfilesUseCase(profile_repo)
    assert len(use_case.execute()) == 2


def test_get_by_id(profile_repo):
    profile = save_profile(profile_repo, "Find")
    use_case = GetProfilesUseCase(profile_repo)
    assert use_case.get_by_id(profile.id).name == "Find"


def test_get_by_id_missing_raises(profile_repo):
    use_case = GetProfilesUseCase(profile_repo)
    with pytest.raises(ProfileNotFoundException):
        use_case.get_by_id(uuid4())


def test_get_by_name(profile_repo):
    save_profile(profile_repo, "Named")
    use_case = GetProfilesUseCase(profile_repo)
    assert use_case.get_by_name("Named").name == "Named"


def test_get_by_name_missing_returns_none(profile_repo):
    use_case = GetProfilesUseCase(profile_repo)
    assert use_case.get_by_name("Nope") is None
