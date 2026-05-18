"""Simplex manim plugin -- activated by manim once per render process.

Registered via ``[project.entry-points."manim.plugins"] simplex =
"simplex.plugin:activate"`` in ``pyproject.toml``. Each deck enables it by
declaring ``plugins = simplex`` in its ``manim.cfg``.

Why a plugin (not env-var pre-init): ``Scene.__init__`` constructs the
camera from ``manim.config.background_color`` during super-init, so
mutating that value in ``setup()`` is too late -- the camera locks in
the previous value. A plugin runs once at ``import manim`` time, before
any scene is constructed, which is the correct seam.

The plugin pulls the *active* theme from ``simplex.theme.context``; the
per-deck CLI runner is responsible for setting it before spawning the
manim subprocess (via ``active_theme(theme)``).
"""

from __future__ import annotations


def activate() -> None:
    """Apply the active Simplex theme to ``manim.config`` and defaults.

    Idempotent: calling twice is harmless. Run at ``import manim`` time
    via the ``manim.plugins`` entry-point.
    """
    import manim

    from simplex.engine.defaults import apply_theme_defaults
    from simplex.theme.context import get_active_theme
    from simplex.theme.pygments_style import register_darcula

    theme = get_active_theme()
    apply_theme_defaults(theme)
    manim.config.tex_template = theme.latex.as_tex_template()
    manim.config.background_color = theme.palette.background
    manim.config.save_sections = True
    register_darcula()
