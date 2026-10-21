"""Verify the installed entry point without using private artwork."""

import subprocess
import sys


def test_help_is_available_without_artwork():
    result = subprocess.run(
        [sys.executable, "-m", "psd_import.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Conversion is not implemented" in result.stdout


def test_unknown_arguments_are_rejected():
    result = subprocess.run(
        [sys.executable, "-m", "psd_import.cli", "--convert"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
