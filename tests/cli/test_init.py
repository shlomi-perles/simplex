"""`simplex init` creates a lectures repo from the GitHub template."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from simplex.cli import commands
from simplex.cli.commands import app


@pytest.fixture
def stub_gh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.chdir(tmp_path)

    def fake_which(name: str) -> str | None:
        if name == "gh":
            return "gh"
        if name == "git":
            return "git"
        return None

    def fake_run(args: list[str], **_kwargs: Any) -> None:
        calls.append(args)

    monkeypatch.setattr(commands.shutil, "which", fake_which)
    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    return calls


def test_init_can_create_public_repo(stub_gh: list[list[str]]) -> None:
    result = CliRunner().invoke(app, ["init", "blog", "--public"], input="\n")
    assert result.exit_code == 0, result.stdout
    assert stub_gh == [
        [
            "gh",
            "repo",
            "create",
            "blog",
            "--template",
            "shlomi-perles/simplex-lectures-template",
            "--clone",
            "--public",
        ]
    ]


def test_init_can_create_private_repo(stub_gh: list[list[str]]) -> None:
    result = CliRunner().invoke(app, ["init", "blog", "--private"], input="\n")
    assert result.exit_code == 0, result.stdout
    assert stub_gh[0][-1] == "--private"


def test_init_prompts_for_visibility_when_not_provided(stub_gh: list[list[str]]) -> None:
    result = CliRunner().invoke(app, ["init", "blog"], input="\npublic\n")
    assert result.exit_code == 0, result.stdout
    assert stub_gh[0][-1] == "--public"


def test_init_rejects_conflicting_visibility_flags(stub_gh: list[list[str]]) -> None:
    result = CliRunner().invoke(app, ["init", "blog", "--public", "--private"], input="\n")
    assert result.exit_code != 0
    assert "choose either --public or --private" in result.output
    assert stub_gh == []
