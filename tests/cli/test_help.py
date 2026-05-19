"""`simplex --help` exits 0 and advertises every command."""

from typer.testing import CliRunner

from simplex.cli.commands import app


def test_help_exits_zero_and_lists_all_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("new", "init", "render", "build", "test", "serve", "clean", "doctor"):
        assert cmd in result.stdout
