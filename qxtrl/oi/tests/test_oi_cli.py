"""Basic CLI smoke tests."""

import subprocess
import sys
import json


def test_cli_run_rabi_json_succeeds():
    # Use python -m to avoid install
    result = subprocess.run(
        [sys.executable, "-m", "qxtrl.oi.cli", "run", "rabi", "--qubit", "q000", "--json", "--points", "3"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    # at least JSON like output with stable fields
    out = result.stdout
    assert "{" in out
    assert "final_state" in out
    assert "manifest_ref" in out


def test_cli_invalid_args_exit_2():
    result = subprocess.run(
        [sys.executable, "-m", "qxtrl.oi.cli", "run", "rabi", "--qubit", "q000", "--points", "1", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    if "{" in result.stdout:
        data = json.loads(result.stdout)
        assert data.get("code") == "OI-ARGUMENT-SCHEMA"


def test_cli_hardware_mode_exit_2():
    result = subprocess.run(
        [sys.executable, "-m", "qxtrl.oi.cli", "run", "rabi", "--qubit", "q000", "--mode", "hardware", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    if "{" in result.stdout:
        data = json.loads(result.stdout)
        assert data.get("code") == "OI-UNSUPPORTED-MODE"


def test_cli_manifest_missing_exit_4():
    result = subprocess.run(
        [sys.executable, "-m", "qxtrl.oi.cli", "manifest", "show", "run.nonexistent.123", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 4
    if "{" in result.stdout:
        data = json.loads(result.stdout)
        assert data.get("code") == "OI-MANIFEST-NOT-FOUND"
