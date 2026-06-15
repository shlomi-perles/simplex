# cli/

Typer-based command surface exposed as `simplex` via `[project.scripts]`.

## Public surface

- `app` -- Typer application (entry point: `simplex.cli.commands:app`)
- Commands: `new`, `init`, `render`, `build`, `serve`, `clean`, `doctor`

## Don't

- Don't add business logic here. Commands are thin shells over `deck`, `render`, and `web`.
- Don't `os.chdir` outside of `serve`; that command intentionally enters `site/` to use `http.server`.
