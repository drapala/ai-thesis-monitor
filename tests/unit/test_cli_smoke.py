import subprocess
import sys

from ai_thesis_monitor import __version__
from typer.testing import CliRunner


def test_version_command_prints_expected_value():
    from ai_thesis_monitor.cli.main import app  # imported inside to avoid hard dependency before module exists

    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout == f"{__version__}\n"


def test_root_invocation_prints_help():
    from ai_thesis_monitor.cli.main import app

    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    assert "Usage: ai-thesis-monitor" in result.stdout


def test_module_entrypoint_proxy_runs_version_command():
    result = subprocess.run(
        [sys.executable, "-m", "ai_thesis_monitor.cli.main", "version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == f"{__version__}\n"
