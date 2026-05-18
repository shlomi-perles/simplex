"""DarculaStyle Pygments scheme shared by the engine (videos) and the web
(notes code blocks). Kept manim-free so the web build doesn't pull manim in.
"""

import sys
import types

from pygments.style import Style
from pygments.token import Comment, Generic, Keyword, Literal, Name


def register_darcula(style_name: str = "darcula") -> None:
    """Register `DarculaStyle` under `style_name` in Pygments. Idempotent.

    Called automatically by `simplex.plugin.activate` and `engine.code.code_block`.
    Exposed so users with their own Code mobjects can opt into the same palette.
    """
    import pygments.styles

    if style_name in pygments.styles.STYLE_MAP:
        return
    cls_name = DarculaStyle.__name__
    module = types.ModuleType(style_name)
    setattr(module, cls_name, DarculaStyle)
    setattr(pygments.styles, style_name, module)
    sys.modules[f"pygments.styles.{style_name}"] = module
    style_map: dict[str, str] = pygments.styles.STYLE_MAP  # type: ignore[assignment]
    style_map[style_name] = f"{style_name}::{cls_name}"


class DarculaStyle(Style):
    """Pygments scheme inspired by JetBrains Darcula, ported from Dastimator."""

    background_color = "#111111"
    highlight_color = "#333333"

    styles = {  # noqa: RUF012 -- pygments declares `styles` as a class attribute.
        Comment.Multiline: "#808080",
        Comment.Preproc: "#808080",
        Comment.Single: "#808080",
        Comment.Special: "bold #808080",
        Comment: "#808080",
        Generic.Deleted: "#BC3F3C",
        Generic.Emph: "italic #A9B7C6",
        Generic.Heading: "bold #A9B7C6",
        Generic.Inserted: "#A5C261",
        Generic.Output: "#A9B7C6",
        Generic.Prompt: "#808080",
        Generic.Strong: "bold #A9B7C6",
        Generic.Subheading: "bold #A9B7C6",
        Generic.Traceback: "#BC3F3C",
        Keyword.Constant: "#CC7832",
        Keyword.Declaration: "#CC7832",
        Keyword.Namespace: "#CC7832",
        Keyword.Pseudo: "#CC7832",
        Keyword.Reserved: "#CC7832",
        Keyword.Type: "#CC7832",
        Keyword: "#CC7832 bold",
        Literal.Number: "#6897BB",
        Literal.String: "#6A8759",
        Literal.String.Doc: "#629755",
        Name.Attribute: "#BABABA",
        Name.Builtin.Pseudo: "#9876AA",
        Name.Builtin: "#8888C6",
        Name.Class: "#FFC66D bold",
        Name.Constant: "#9876AA",
        Name.Decorator: "#BBB529",
        Name.Entity: "#6D9CBE",
        Name.Exception: "#FFC66D bold",
        Name.Function: "#FFC66D bold",
        Name.Label: "#A9B7C6 bold",
        Name.Namespace: "#A9B7C6",
        Name.Tag: "#E8BF6A",
        Name.Variable.Class: "#9876AA",
        Name.Variable.Global: "#9876AA",
        Name.Variable.Instance: "#9876AA",
        Name.Variable: "#A9B7C6",
    }
