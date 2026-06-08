# Palette Data

Packaged palette assets used by `simplex.theme.palettes`.

`simplex_light.json` defines the built-in light Manim palette. `iterm2.json`
is a normalized vendored snapshot of iTerm2 color schemes so palette resolution
and Theme Studio work offline and stay deterministic.

These files define Manim constants and palette bases. Project authors should
put their own exports in `simplex_themes/palette_styles/`; semantic slide
fields and custom colors belong in `simplex_themes/themes/*.json`.
