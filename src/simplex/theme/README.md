# theme/

Frozen Pydantic tokens (colors, typography, spacing, motion, LaTeX profile, web
palette) plus a ContextVar-based active-theme registry.

## Public surface

- `Theme`, `Palette`, `Typography`, `Spacing`, `Motion`, `LatexProfile`, `WebPalette`
- `presets.SIMPLEX_DARK`, `presets.SIMPLEX_LIGHT`, `presets.get(name)`
- `active_theme(theme)` -- context manager
- `get_active_theme()` -- read the current theme (falls back to `SIMPLEX_DARK`)
- `resolve_palette(name)`, `available_palette_names()` -- resolve Manim/iTerm palette data
- `presets.get(name)`, `presets.available_names()` -- resolve built-in and repo-local themes
- `render_web_css(palette, code_style=None)` -- emits a `:root { --simplex-* }` block for the portal and deck player pages; code colors come from the Pygments style
- `studio.write_studio(...)` -- generate the packaged Theme Studio HTML
- `pygments_style.SimplexPycharm`, `pygments_style.SimplexSolarizedLight`, `register_style(...)`

Repo-local themes live in `simplex_themes/themes/*.json`. The file stem is the
theme name; JSON can include `manim_palette`, partial/full semantic `palette`,
`web_palette`, and `code_style`.

`palette` is an open semantic model. Core fields (`background`, `font`,
`accent`, `vertex`, `vertex_stroke`, `edge`, `weight`, `visited`, `label`,
`distance`) drive built-in helpers, and custom fields are preserved for scene
code through `get_active_theme().palette.<name>`.

Palette values may be true-theme switches:

```json
{
  "palette": {
    "warning": { "light": "#775500", "dark": "#FFD166" }
  }
}
```

The switch resolves from the active render variant (`SIMPLEX_THEME_VARIANT`),
not from the theme file name. Outside a true-theme render, dark is the default
fallback.

## Don't

- Don't mutate a `Theme` instance -- all models are frozen.
- Don't define presets as subclasses. They are instances so swapping themes at runtime is one assignment.
- Don't import `manim` at theme module load time; palette constants are patched only by `simplex.plugin.activate()`.
