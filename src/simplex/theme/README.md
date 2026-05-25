# theme/

Frozen Pydantic tokens (colors, typography, spacing, motion, LaTeX profile, web
palette) plus a ContextVar-based active-theme registry.

## Public surface

- `Theme`, `Palette`, `Typography`, `Spacing`, `Motion`, `LatexProfile`, `WebPalette`
- `presets.SIMPLEX_DARK`, `presets.ACADEMIC_LIGHT`, `presets.get(name)`
- `active_theme(theme)` -- context manager
- `get_active_theme()` -- read the current theme (falls back to `SIMPLEX_DARK`)
- `render_web_css(palette)` -- emits a `:root { --simplex-* }` block for the portal and RevealJS pages
- `pygments_style.DarculaStyle`, `register_darcula(name="darcula")`

## Don't

- Don't mutate a `Theme` instance -- all models are frozen.
- Don't define presets as subclasses. They are instances so swapping themes at runtime is one assignment.
- Don't import `manim` at module load time; touch it only inside `LatexProfile.as_tex_template()`.
