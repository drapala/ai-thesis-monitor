from typer.testing import CliRunner


def test_version_command_prints_expected_value():
    from ai_thesis_monitor.cli.main import app  # imported inside to avoid hard dependency before module exists

    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
