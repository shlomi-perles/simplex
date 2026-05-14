# tests/cli/

Typer CLI smoke tests via `typer.testing.CliRunner`. Exercise commands that
don't invoke `manim-slides`: `new`, `--help`. `doctor` is exercised elsewhere
because it inspects real binaries.

## Public surface

- `test_help.py` -- `simplex --help` exits 0 and lists every command.
- `test_new.py` -- `simplex new my-deck` scaffolds a loadable deck.

## Don't

- Don't invoke `simplex render` or `simplex build` here -- they shell out to manim-slides.
- Don't mutate `Path.cwd()`. Use `tmp_path` + `monkeypatch.chdir`.
