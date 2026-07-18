"""Tests for the CLI argument parser."""

from src.cli.argument_parser import CLIArguments, parse_arguments


def test_parse_list(monkeypatch):
    monkeypatch.setattr("sys.argv", ["AudioDeck", "--list"])
    args = parse_arguments()
    assert args.list_profiles is True
    assert args.is_cli_mode is True


def test_parse_profile(monkeypatch):
    monkeypatch.setattr("sys.argv", ["AudioDeck", "--profile", "Gaming"])
    args = parse_arguments()
    assert args.profile_name == "Gaming"
    assert args.is_cli_mode is True


def test_parse_no_args_is_gui(monkeypatch):
    monkeypatch.setattr("sys.argv", ["AudioDeck"])
    args = parse_arguments()
    assert args.is_cli_mode is False


def test_cli_arguments_defaults():
    args = CLIArguments()
    assert args.list_profiles is False
    assert args.profile_name is None
    assert args.is_cli_mode is False


def test_is_cli_mode_with_profile_only():
    assert CLIArguments(profile_name="X").is_cli_mode is True
