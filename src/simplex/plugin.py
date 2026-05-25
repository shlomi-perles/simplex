"""Simplex manim plugin -- activated by manim once per render process.

Registered via ``[project.entry-points."manim.plugins"] simplex =
"simplex.plugin:activate"`` in ``pyproject.toml``. Each deck enables it by
declaring ``plugins = simplex`` in its ``manim.cfg``.

Why a plugin (not env-var pre-init): ``Scene.__init__`` constructs the
camera from ``manim.config.background_color`` during super-init, so
mutating that value in ``setup()`` is too late -- the camera locks in
the previous value. A plugin runs once at ``import manim`` time, before
any scene is constructed, which is the correct seam.

Manim 0.20.x's plugin loader (``manim.plugins.plugins_flags.get_plugins``)
resolves the ``"module:activate"`` entry-point with ``entry_point.load()``
which imports the module and returns the symbol -- but **does not call**
``activate()``. We therefore invoke ``activate()`` from module import
itself so the entry-point resolution doubles as the activation hook. The
function stays exported in case downstream code wants to re-apply
defaults after swapping themes.

Theme selection priority:
1. ``simplex.theme.context.get_active_theme()`` -- the in-process active
   theme (set by parent code that ``import simplex.plugin`` from the
   same interpreter).
2. ``SIMPLEX_THEME`` environment variable -- the deck.toml ``theme`` name
   propagated across the ``manim-slides render`` subprocess by
   ``simplex.render.runner``.
3. ``SIMPLEX_DARK`` -- the package default.
"""

from __future__ import annotations

import os


def _resolve_theme():  # type: ignore[no-untyped-def]
    """Pick the theme that should drive Manim defaults for this process."""
    from simplex.theme.context import _active
    from simplex.theme.presets import PRESETS, SIMPLEX_DARK

    # In-process context (a parent that did ``with active_theme(t): ...``)
    # wins; env-var fallback handles cross-process propagation.
    if (active := _active.get()) is not None:
        return active
    env_name = os.environ.get("SIMPLEX_THEME")
    if env_name and env_name in PRESETS:
        return PRESETS[env_name]
    return SIMPLEX_DARK


def activate() -> None:
    """Apply the resolved Simplex theme to ``manim.config`` and defaults.

    Idempotent: calling twice is harmless. Auto-invoked on module import
    because Manim 0.20.x doesn't call entry-point activate functions; see
    module docstring for the rationale.
    """
    import manim

    from simplex.engine.defaults import apply_theme_defaults
    from simplex.theme.pygments_style import register_all_builtin_styles

    theme = _resolve_theme()
    apply_theme_defaults(theme)
    manim.config.tex_template = theme.latex.as_tex_template()
    manim.config.background_color = theme.palette.background
    manim.config.save_sections = True
    register_all_builtin_styles()


# Manim's plugin loader imports this module via ``entry_point.load()`` but
# never calls ``activate()``. Run it now so the entry-point resolution itself
# applies the theme.
activate()
