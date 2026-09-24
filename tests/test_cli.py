"""
The packaged executable's command line.

`--help` used to die with FileNotFoundError naming "--help", because the
GUI entry point read argv[0] straight into a file open with no argument
handling at all. The problem statement calls the deliverable "a
standalone executable application"; --help is the first thing anyone
types at one.
"""
import pathlib

import pytest

from fsoc_pat.__main__ import main

SCENARIO = str(pathlib.Path(__file__).resolve().parents[1]
               / "scenarios" / "leo_pass_nominal.yaml")


def test_help_prints_usage_and_succeeds(capsys):
    assert main(["--help"]) == 0
    assert "usage:" in capsys.readouterr().out


def test_short_help_works_too(capsys):
    assert main(["-h"]) == 0
    assert "usage:" in capsys.readouterr().out


def test_help_does_not_try_to_open_a_file_called_help(capsys):
    """The exact regression: --help reached open() as a path."""
    main(["--help"])
    assert "FileNotFoundError" not in capsys.readouterr().out


def test_an_unknown_option_is_a_sentence_not_a_traceback(capsys):
    assert main(["--nonsense"]) == 2
    err = capsys.readouterr().err
    assert "unknown option" in err and "--nonsense" in err


def test_a_missing_scenario_is_a_sentence_not_a_traceback(capsys):
    assert main(["definitely/not/here.yaml"]) == 2
    assert "no such scenario file" in capsys.readouterr().err


def test_two_scenarios_is_rejected_clearly(capsys):
    assert main([SCENARIO, SCENARIO]) == 2
    assert "at most one scenario" in capsys.readouterr().err


def test_headless_help_reaches_the_runners_own_parser(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--headless", "--help"])
    assert e.value.code == 0
    assert "duration" in capsys.readouterr().out


def test_headless_runs_and_reports(capsys, tmp_path):
    rc = main(["--headless", SCENARIO, "--duration", "3"])
    assert rc == 0
    out = capsys.readouterr().out
    # every field PS26169 names for the performance log
    for field in ("Simulation duration", "Processing throughput",
                  "Processing per frame", "Acquisition time",
                  "Lock retention", "Pointing error"):
        assert field in out, f"performance report is missing {field!r}"
