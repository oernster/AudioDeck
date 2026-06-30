"""Tests for the CLI handler (use cases injected; no real COM)."""

from src.cli.cli_handler import CLIHandler
from src.cli.argument_parser import CLIArguments
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.dtos.switch_outcome import (
    SkipReason,
    SkippedDevice,
    SwitchOutcome,
)
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import ProfileNotFoundException

from tests.conftest import FakeGetProfilesUseCase, FakeSwitchUseCase, save_profile


def handler(profile_repo, switch=None):
    return CLIHandler(GetProfilesUseCase(profile_repo), switch or FakeSwitchUseCase())


def applied_outcome(*types):
    return SwitchOutcome(applied=tuple(types), skipped=())


def test_list_profiles_with_all_combos(profile_repo, capsys):
    save_profile(profile_repo, "Both", "o", "i")
    save_profile(profile_repo, "OutOnly", "o", None)
    save_profile(profile_repo, "InOnly", None, "i")
    save_profile(profile_repo, "Empty", None, None)
    code = handler(profile_repo).handle(CLIArguments(list_profiles=True))
    out = capsys.readouterr().out
    assert code == 0
    assert "Both (Output + Input)" in out
    assert "OutOnly (Output)" in out
    assert "InOnly (Input)" in out
    assert "Empty (Empty)" in out


def test_list_no_profiles(profile_repo, capsys):
    code = handler(profile_repo).handle(CLIArguments(list_profiles=True))
    assert code == 0
    assert "No profiles configured" in capsys.readouterr().out


def test_no_command(profile_repo, capsys):
    code = handler(profile_repo).handle(CLIArguments())
    assert code == 1
    assert "No valid command" in capsys.readouterr().err


def test_handle_unexpected_exception(profile_repo, capsys):
    cli = CLIHandler(
        FakeGetProfilesUseCase(error=RuntimeError("boom")), FakeSwitchUseCase()
    )
    code = cli.handle(CLIArguments(list_profiles=True))
    assert code == 1
    assert "Error:" in capsys.readouterr().err


def test_switch_success_both(profile_repo, capsys):
    save_profile(profile_repo, "Both", "o", "i")
    switch = FakeSwitchUseCase(
        outcome=applied_outcome(DeviceType.OUTPUT, DeviceType.INPUT)
    )
    code = handler(profile_repo, switch).handle(CLIArguments(profile_name="Both"))
    out = capsys.readouterr().out
    assert code == 0
    assert "switched successfully" in out
    assert "Output and Input" in out


def test_switch_success_output_only(profile_repo, capsys):
    save_profile(profile_repo, "Out", "o", None)
    switch = FakeSwitchUseCase(outcome=applied_outcome(DeviceType.OUTPUT))
    handler(profile_repo, switch).handle(CLIArguments(profile_name="Out"))
    assert "Changed: Output device" in capsys.readouterr().out


def test_switch_success_input_only(profile_repo, capsys):
    save_profile(profile_repo, "In", None, "i")
    switch = FakeSwitchUseCase(outcome=applied_outcome(DeviceType.INPUT))
    handler(profile_repo, switch).handle(CLIArguments(profile_name="In"))
    assert "Changed: Input device" in capsys.readouterr().out


def test_switch_not_found_lists_available(profile_repo, capsys):
    save_profile(profile_repo, "Exists", "o", "i")
    code = handler(profile_repo).handle(CLIArguments(profile_name="Ghost"))
    err = capsys.readouterr().err
    assert code == 1
    assert "not found" in err
    assert "Exists" in err


def test_switch_not_found_no_profiles(profile_repo, capsys):
    code = handler(profile_repo).handle(CLIArguments(profile_name="Ghost"))
    err = capsys.readouterr().err
    assert code == 1
    assert "No profiles configured" in err


def test_switch_profile_not_found_exception(profile_repo, capsys):
    save_profile(profile_repo, "P", "o", "i")
    switch = FakeSwitchUseCase(error=ProfileNotFoundException("gone"))
    code = handler(profile_repo, switch).handle(CLIArguments(profile_name="P"))
    assert code == 1
    assert "Error:" in capsys.readouterr().err


def test_switch_nothing_available(profile_repo, capsys):
    save_profile(profile_repo, "P", "o", "i")
    outcome = SwitchOutcome(
        applied=(),
        skipped=(SkippedDevice(DeviceType.OUTPUT, "o", SkipReason.UNAVAILABLE),),
    )
    code = handler(profile_repo, FakeSwitchUseCase(outcome=outcome)).handle(
        CLIArguments(profile_name="P")
    )
    err = capsys.readouterr().err
    assert code == 1
    assert "were not available" in err


def test_switch_partial(profile_repo, capsys):
    save_profile(profile_repo, "P", "o", "i")
    outcome = SwitchOutcome(
        applied=(DeviceType.OUTPUT,),
        skipped=(SkippedDevice(DeviceType.INPUT, "i", SkipReason.UNAVAILABLE),),
    )
    code = handler(profile_repo, FakeSwitchUseCase(outcome=outcome)).handle(
        CLIArguments(profile_name="P")
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "switched successfully" in captured.out
    assert "were not available" in captured.err
