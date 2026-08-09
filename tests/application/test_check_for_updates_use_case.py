"""Tests for version comparison and the update-offer decision."""

import pytest

from src.application.use_cases.check_for_updates_use_case import (
    CheckForUpdatesUseCase,
    is_newer,
    platform_key_for,
    select_asset_url,
)
from src.domain.value_objects.release_info import ReleaseAsset, ReleaseInfo

ASSETS = (
    ReleaseAsset("AudioDeckSetup.exe", "https://example.com/AudioDeckSetup.exe"),
    ReleaseAsset("audiodeck.dmg", "https://example.com/audiodeck.dmg"),
    ReleaseAsset("audiodeck.flatpak", "https://example.com/audiodeck.flatpak"),
)


class FakeReleaseSource:
    """Returns a configured release, or None."""

    def __init__(self, release=None):
        self._release = release

    def latest_release(self):
        return self._release


def release(version="v1.5.0", assets=ASSETS):
    return ReleaseInfo(
        version=version,
        page_url="https://github.com/oernster/AudioDeck/releases/latest",
        assets=assets,
    )


class TestIsNewer:
    def test_newer(self):
        assert is_newer("1.5.0", "1.4.0") is True

    def test_equal(self):
        assert is_newer("1.4.0", "1.4.0") is False

    def test_older(self):
        assert is_newer("1.3.9", "1.4.0") is False

    def test_v_prefix_stripped(self):
        assert is_newer("v1.5.0", "1.4.0") is True

    def test_uppercase_v_prefix_stripped(self):
        assert is_newer("V1.5.0", "1.4.0") is True

    def test_whitespace_tolerated(self):
        assert is_newer("  1.5.0  ", "1.4.0") is True

    def test_extra_component_compares_positionally(self):
        assert is_newer("1.5", "1.4.0") is True
        assert is_newer("1.4.0.1", "1.4.0") is True

    @pytest.mark.parametrize("latest", ["", "not-a-version", "1.5.0-rc1", "1..0"])
    def test_malformed_latest_is_not_newer(self, latest):
        assert is_newer(latest, "1.4.0") is False

    @pytest.mark.parametrize("current", ["", "0.0.0-dev", "garbage"])
    def test_malformed_current_is_not_newer(self, current):
        assert is_newer("1.5.0", current) is False


class TestExecute:
    def test_unreachable_source_returns_none(self):
        use_case = CheckForUpdatesUseCase(FakeReleaseSource(None), "1.4.0", "windows")
        assert use_case.execute() is None

    def test_newer_release_offers_update_with_asset_and_page(self):
        use_case = CheckForUpdatesUseCase(
            FakeReleaseSource(release()), "1.4.0", "windows"
        )
        status = use_case.execute()
        assert status.update_available is True
        assert status.latest == "v1.5.0"
        assert status.current == "1.4.0"
        assert status.download_url == "https://example.com/AudioDeckSetup.exe"
        assert status.page_url is not None

    def test_same_version_is_not_offered(self):
        use_case = CheckForUpdatesUseCase(
            FakeReleaseSource(release("v1.4.0")), "1.4.0", "windows"
        )
        status = use_case.execute()
        assert status.update_available is False
        assert status.download_url is None

    def test_skipped_version_is_seen_but_not_offered(self):
        use_case = CheckForUpdatesUseCase(
            FakeReleaseSource(release()), "1.4.0", "windows"
        )
        status = use_case.execute(skipped_version="v1.5.0")
        assert status.update_available is False
        assert status.latest == "v1.5.0"
        assert status.download_url is None

    def test_different_skipped_version_still_offers(self):
        use_case = CheckForUpdatesUseCase(
            FakeReleaseSource(release()), "1.4.0", "windows"
        )
        assert use_case.execute(skipped_version="v1.4.9").update_available is True

    def test_no_matching_asset_falls_back_to_page_only(self):
        source = FakeReleaseSource(
            release(assets=(ReleaseAsset("checksums.txt", "https://x/c"),))
        )
        use_case = CheckForUpdatesUseCase(source, "1.4.0", "windows")
        status = use_case.execute()
        assert status.update_available is True
        assert status.download_url is None


class TestSelectAssetUrl:
    @pytest.mark.parametrize(
        "platform_key,expected",
        [
            ("windows", "https://example.com/AudioDeckSetup.exe"),
            ("macos", "https://example.com/audiodeck.dmg"),
            ("linux", "https://example.com/audiodeck.flatpak"),
        ],
    )
    def test_platform_asset_selection(self, platform_key, expected):
        assert select_asset_url(ASSETS, platform_key) == expected

    def test_suffix_match_is_case_insensitive(self):
        assets = (ReleaseAsset("AUDIODECKSETUP.EXE", "https://x/setup"),)
        assert select_asset_url(assets, "windows") == "https://x/setup"

    def test_empty_assets(self):
        assert select_asset_url((), "windows") is None

    def test_unknown_platform_key(self):
        assert select_asset_url(ASSETS, "beos") is None


class TestPlatformKeyFor:
    @pytest.mark.parametrize(
        "sys_platform,expected",
        [
            ("win32", "windows"),
            ("darwin", "macos"),
            ("linux", "linux"),
            ("freebsd14", "linux"),
        ],
    )
    def test_mapping(self, sys_platform, expected):
        assert platform_key_for(sys_platform) == expected
