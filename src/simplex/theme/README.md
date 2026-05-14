# theme/

Frozen Pydantic tokens (colors, typography, spacing, motion, LaTeX profile) plus a ContextVar-based active-theme registry.

## Public surface

- `Theme`, `Palette`, `Typography`, `Spacing`, `Motion`, `LatexProfile`
- `presets.DASTIMATOR_DARK`, `presets.ACADEMIC_LIGHT`, `presets.get(name)`
- `active_theme(theme)` -- context manager
- `get_active_theme()` -- read the current theme (falls back to `DASTIMATOR_DARK`)

## Don't

- Don't mutate a `Theme` instance -- all models are frozen.
- Don't define presets as subclasses. They are instances so swapping themes at runtime is one assignment.
- Don't import `manim` at module load time; touch it only inside `LatexProfile.as_tex_template()`.
