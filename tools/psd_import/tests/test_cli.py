"""Exercise the installed entry point and exit codes using real PSD files."""

import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "psd_import.cli", *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_is_available_without_artwork():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "manifest v1" in result.stdout


def test_unknown_arguments_are_rejected():
    assert run_cli("--convert").returncode == 2


def test_cli_converts_and_compares(synthetic_psd, tmp_path):
    output = tmp_path / "bundle"
    result = run_cli(synthetic_psd, output, "--compare")
    assert result.returncode == 0, result.stderr
    assert "EMPTY_LAYER" in result.stdout
    assert json.loads((output / "comparison.json").read_text())["passed"]
    assert run_cli(synthetic_psd, output).returncode == 2


def test_missing_input_is_clear(tmp_path):
    result = run_cli(tmp_path / "absent.psd", tmp_path / "bundle")
    assert result.returncode == 2
    assert "absent.psd" in result.stderr
    assert not (tmp_path / "bundle").exists()
