# tests/

Pytest suites grouped by package. Theme / region / notes / deck tests stay
stdlib-only. Tests that touch a real Manim install use
`pytest.importorskip("manim")` and live under `tests/engine/`.

## Layout

- `tests/theme/` -- palette / preamble / env values, immutability, context push/pop.
- `tests/engine/` -- `Region` math, `Remove` / `set_exit_animation`.
- `tests/deck/` -- `DeckConfig` slug validation, `discover()`, `scaffold()`.
- `tests/web/` -- markdown -> HTML, `build(render=False)` writes index + per-deck pages.
- `tests/cli/` -- Typer command smoke (`new`, `--help`).

## Don't

- Don't render real decks in the test suite -- the manim-slides subprocess is too slow.
- Don't depend on test order. syrupy snapshots may go stale; refresh with `pytest --snapshot-update`.
- Don't import Manim in `conftest.py`. Keep test discovery fast.
