# tests/mobjects/

Smoke construction tests for the `simplex.mobjects` package
(`Node`, `Edge`, ...).

## Conventions

- Gated on `pytest.importorskip("manim")` -- mobjects pull from the
  active theme at construction, which means a Manim runtime is required.
- Tests do not render. They check shape (submobject counts) and
  registry side effects (exit animation registration).

## Don't

- Don't test glyph layout numerically -- LaTeX font choice changes
  pixel positions between Manim versions.
