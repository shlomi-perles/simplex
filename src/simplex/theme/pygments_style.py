"""DarculaStyle Pygments scheme shared by the engine (videos) and the web
(notes code blocks). Kept manim-free so the web build doesn't pull manim in.
"""

from pygments.style import Style
from pygments.token import Comment, Generic, Keyword, Literal, Name


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
        Generic.Deleted: "#CC4040",
        Generic.Emph: "#A9B7C6",
        Generic.Heading: "#999999",
        Generic.Inserted: "#40CC40",
        Generic.Output: "#888888",
        Generic.Prompt: "#555555",
        Generic.Strong: "bold",
        Generic.Subheading: "#aaaaaa",
        Generic.Traceback: "#aa0000",
        Keyword.Constant: "#CC7832",
        Keyword.Declaration: "#CC7832",
        Keyword.Namespace: "#CC7832",
        Keyword.Pseudo: "#CC7832",
        Keyword.Reserved: "#CC7832",
        Keyword.Type: "#A9B7C6 bold",
        Keyword: "#CC7832 bold",
        Literal.Number: "#6897B3",
        Literal.String: "#008080",
        Literal.String.Doc: "#629755",
        Name.Attribute: "#800080",
        Name.Builtin.Pseudo: "#94558D",
        Name.Builtin: "#8888C6",
        Name.Class: "#A9B7C6 bold",
        Name.Constant: "#B200B2",
        Name.Decorator: "#BBB529",
        Name.Entity: "#A9B7C6",
        Name.Exception: "#A9B7C6 bold",
        Name.Function: "#A9B7C6 bold",
        Name.Label: "#A9B7C6 bold",
        Name.Namespace: "#A9B7C6",
        Name.Tag: "#A5C261 bold",
        Name.Variable.Class: "#A9B7C6 bold",
        Name.Variable.Global: "#A9B7C6 bold",
        Name.Variable.Instance: "#A9B7C6",
        Name.Variable: "#A9B7C6",
    }
