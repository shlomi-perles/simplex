"""Light Pygments style based on Solarized Light with Simplex tweaks."""

from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
)


class SimplexSolarizedLight(Style):
    """Warm light scheme inspired by Solarized Light."""

    background_color = "#fffce4"
    highlight_color = "#eee8d5"

    styles = {  # noqa: RUF012 -- Pygments declares `styles` as a class attribute
        Text: "#002b36",
        Error: "bold #dc322f",
        Comment: "italic #586e75",
        Comment.Multiline: "italic #586e75",
        Comment.Preproc: "italic #586e75",
        Comment.Single: "italic #586e75",
        Comment.Special: "italic bold #586e75",
        Keyword: "#db7448",
        Keyword.Constant: "#db7448",
        Keyword.Declaration: "#db7448",
        Keyword.Namespace: "#db7448",
        Keyword.Pseudo: "#db7448",
        Keyword.Reserved: "#db7448",
        Keyword.Type: "#db7448",
        Operator: "#000000",
        Operator.Word: "#db7448",
        Punctuation: "#024050",
        Name: "#024050",
        Name.Attribute: "#024050",
        Name.Builtin: "#4f66c4",
        Name.Builtin.Pseudo: "#50023B",
        Name.Class: "bold #024050",
        Name.Constant: "#50023B",
        Name.Decorator: "#db7448",
        Name.Entity: "#024050",
        Name.Exception: "bold #dc322f",
        Name.Function: "#024050",
        Name.Label: "#024050",
        Name.Namespace: "#50023B",
        Name.Other: "#024050",
        Name.Tag: "#db7448",
        Name.Variable: "#024050",
        Name.Variable.Class: "#50023B",
        Name.Variable.Global: "#50023B",
        Name.Variable.Instance: "#50023B",
        Number: "#E237BD",
        Literal: "#E237BD",
        Literal.Date: "#427925",
        String: "#427925",
        Literal.String: "#427925",
        Literal.String.Doc: "italic #427925",
        Literal.String.Escape: "#E237BD",
        Literal.Number: "#E237BD",
        Generic: "#586e75",
        Generic.Deleted: "#dc322f",
        Generic.Emph: "italic #002b36",
        Generic.Heading: "bold #002b36",
        Generic.Inserted: "#427925",
        Generic.Output: "#002b36",
        Generic.Prompt: "#586e75",
        Generic.Strong: "bold #002b36",
        Generic.Subheading: "#002b36",
        Generic.Traceback: "#dc322f",
    }
