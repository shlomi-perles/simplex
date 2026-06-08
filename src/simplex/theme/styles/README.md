# theme/styles

Pygments style classes used by Simplex themes.

## Rules

- Keep each style in its own module so plugin registration can expose stable
  formatter names.
- Keep classes Manim-free; these modules are imported by both scene rendering
  and web CSS generation.
- Keep semantic colors out of code-style modules. Slide colors live in
  `Theme.palette`; notes/page shell colors live in `Theme.web_palette` or
  deck `[web]` overrides.
