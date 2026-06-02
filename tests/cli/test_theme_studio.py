"""`simplex theme-studio` writes the packaged editor HTML."""

from pathlib import Path

from typer.testing import CliRunner

from simplex.cli.commands import app


def test_theme_studio_writes_html(tmp_path: Path) -> None:
    output = tmp_path / "studio.html"

    result = CliRunner().invoke(app, ["theme-studio", "--no-open", "--output", str(output)])

    assert result.exit_code == 0, result.stdout
    html = output.read_text(encoding="utf-8")
    assert "Theme Studio" in html
    assert "simplex_light" in html
    assert "Belafonte Day" in html
