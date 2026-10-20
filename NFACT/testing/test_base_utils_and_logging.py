import argparse
import logging
from pathlib import Path
import pytest
from NFACT.base.logging import NFACT_logs
from NFACT.base.signithandler import Signit_handler
from NFACT.base.utils import (
    Timer,
    colours,
    error_and_exit,
    no_args,
    nprint,
    verbose_help_message,
)


def test_timer_tic_and_toc() -> None:
    """
    Function to test Timer tic and toc execution.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    timer_instance = Timer()
    timer_instance.tic()
    elapsed_seconds = timer_instance.toc()
    assert float(elapsed_seconds) >= 0.0


@pytest.mark.parametrize(
    "seconds_input, expected_output",
    [
        (10.0, "10 seconds"),
        (45.2, "45 seconds"),
        (125.0, "2 minutes: 5 seconds"),
        (3665.0, "1 hours: 1 minutes: 5 seconds"),
    ],
)
def test_timer_format_time(seconds_input: float, expected_output: str) -> None:
    """
    Function to test time formatting across ranges.

    Parameters
    ----------
    seconds_input: float
        Number of seconds.
    expected_output: str
        Formatted expected time string.

    Returns
    -------
    None
    """
    timer_instance = Timer()
    assert timer_instance.format_time(seconds_input) == expected_output


def test_timer_how_long() -> None:
    """
    Function to test how_long method returns a formatted string.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    timer_instance = Timer()
    timer_instance.tic()
    how_long_result = timer_instance.how_long()
    assert "seconds" in how_long_result


def test_colours_keys_and_values() -> None:
    """
    Function to test colours dictionary contains all expected color keys.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    colour_dictionary = colours()
    expected_keys = [
        "reset",
        "red",
        "pink",
        "deep_pink",
        "purple",
        "darker_pink",
        "plum",
        "amethyst",
        "lav",
        "light_pink",
    ]
    for key_name in expected_keys:
        assert key_name in colour_dictionary
        assert colour_dictionary[key_name].startswith("\033[")


def test_error_and_exit_success() -> None:
    """
    Function to test error_and_exit does nothing when statement is True.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    error_and_exit(True, "Should not exit")


def test_error_and_exit_failure(capsys: pytest.CaptureFixture) -> None:
    """
    Function to test error_and_exit exits with code 1 when statement is False.

    Parameters
    ----------
    capsys: pytest.CaptureFixture
        Pytest capsys fixture.

    Returns
    -------
    None
    """
    with pytest.raises(SystemExit) as exit_info:
        error_and_exit(False, "[Errno 2] File not found error", log_message=False)
    assert exit_info.value.code == 1
    captured_output = capsys.readouterr()
    assert "File not found error" in captured_output.out
    assert "[Errno 2]" not in captured_output.out
    assert "Exiting..." in captured_output.out


def test_error_and_exit_with_logging(capsys: pytest.CaptureFixture) -> None:
    """
    Function to test error_and_exit with log_message=True.

    Parameters
    ----------
    capsys: pytest.CaptureFixture
        Pytest capsys fixture.

    Returns
    -------
    None
    """
    with pytest.raises(SystemExit) as exit_info:
        error_and_exit(False, "Test failure with log", log_message=True)
    assert exit_info.value.code == 1
    captured_output = capsys.readouterr()
    assert "Test failure with log" in captured_output.out


def test_nprint_output(capsys: pytest.CaptureFixture) -> None:
    """
    Function to test nprint outputs message to stdout.

    Parameters
    ----------
    capsys: pytest.CaptureFixture
        Pytest capsys fixture.

    Returns
    -------
    None
    """
    nprint("Test message from nprint", to_flush=True)
    captured_output = capsys.readouterr()
    assert "Test message from nprint" in captured_output.out


def test_no_args_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Function to test no_args triggers help and exits when no CLI arguments are passed.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    parser_instance = argparse.ArgumentParser(prog="test_prog")
    monkeypatch.setattr("sys.argv", ["test_prog"])
    with pytest.raises(SystemExit) as exit_info:
        no_args(parser_instance)
    assert exit_info.value.code == 1


def test_verbose_help_message_exits(capsys: pytest.CaptureFixture) -> None:
    """
    Function to test verbose_help_message prints verbose information and exits with 0.

    Parameters
    ----------
    capsys: pytest.CaptureFixture
        Pytest capsys fixture.

    Returns
    -------
    None
    """
    parser_instance = argparse.ArgumentParser(prog="test_prog")
    with pytest.raises(SystemExit) as exit_info:
        verbose_help_message(parser_instance, "Additional verbose explanation")
    assert exit_info.value.code == 0
    captured_output = capsys.readouterr()
    assert "Additional verbose explanation" in captured_output.out
    assert "NFACT version:" in captured_output.out


def test_nfact_logs_workflow(tmp_path: Path) -> None:
    """
    Function to test NFACT_logs logging setup and lifecycle.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    log_manager = NFACT_logs("nmf", "decomp", 5)
    log_name = log_manager.get_log_name()
    assert "decomp_NMF_" in log_name
    assert log_name.endswith(".log")

    date_dictionary = log_manager.process_datetime()
    assert "date" in date_dictionary
    assert "time" in date_dictionary

    logging.getLogger().handlers.clear()
    log_manager.set_up_logging(str(tmp_path))
    log_manager.inital_log("NFACT Splash Banner")
    log_manager.log_break("Section Break")
    log_manager.log_arguments({"outdir": "/tmp/output", "dim": 50})
    log_manager.log_parameters({"alpha_W": 0.1, "l1_ratio": 1.0})
    log_manager.log("Custom message logged")
    log_manager.clear_logging()

    log_file_path = tmp_path / log_name
    assert log_file_path.exists()
    file_content = log_file_path.read_text()
    assert "NFACT Splash Banner" in file_content
    assert "SECTION BREAK" in file_content
    assert "Custom message logged" in file_content
    assert "Input arguments:" in file_content


def test_signit_handler_registration_and_properties() -> None:
    """
    Function to test Signit_handler properties and exit behavior.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    handler_instance = Signit_handler()
    assert not handler_instance.get_suppress_messages
    handler_instance.set_suppress_messages = True
    assert handler_instance.get_suppress_messages

    with pytest.raises(SystemExit) as exit_info:
        handler_instance.handle_sigint(2, None)
    assert exit_info.value.code == 0
