# theme/styles

Pygments style classes used by Simplex themes.

## Rules

- Keep each style in its own module so plugin registration can expose stable
  formatter names.
- Keep classes Manim-free; these modules are imported by both scene rendering
  and web CSS generation.
