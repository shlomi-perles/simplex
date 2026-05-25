"""Pygments style inspired by JetBrains Darcula / PyCharm."""

from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Operator,
    Punctuation,
    Text,
)


class SimplexPycharm(Style):
    """Dark Pygments scheme inspired by PyCharm's Darcula palette."""

    background_color = "#111111"
    highlight_color = "#333333"

    styles = {  # noqa: RUF012 -- Pygments declares `styles` as a class attribute
        Text: "#A9B7C6",
        Error: "#960050",
        Comment: "#808080",
        Comment.Multiline: "#808080",
        Comment.Preproc: "#808080",
        Comment.Single: "#808080",
        Comment.Special: "#808080",
        Keyword: "#CC7832",
        Keyword.Constant: "#CC7832",
        Keyword.Declaration: "#CC7832",
        Keyword.Namespace: "#CC7832",
        Keyword.Pseudo: "#CC7832",
        Keyword.Reserved: "#CC7832",
        Keyword.Type: "#CC7832",
        Operator: "#A9B7C6",
        Operator.Word: "#CC7832",
        Punctuation: "#A9B7C6",
        Name: "#A9B7C6",
        Name.Attribute: "#BABABA",
        Name.Builtin: "#8888C6",
        Name.Builtin.Pseudo: "#9876AA",
        Name.Class: "#F1C829",
        Name.Constant: "#9876AA",
        Name.Decorator: "#BBB529",
        Name.Entity: "#6D9CBE",
        Name.Exception: "#F1C829",
        Name.Function: "#F1C829",
        Name.Label: "#A9B7C6",
        Name.Namespace: "#A9B7C6",
        Name.Other: "#88BE05",
        Name.Tag: "#E8BF6A",
        Name.Variable: "#A9B7C6",
        Name.Variable.Class: "#9876AA",
        Name.Variable.Global: "#9876AA",
        Name.Variable.Instance: "#9876AA",
        Literal: "#6897BB",
        Literal.Date: "#6A8759",
        Literal.Number: "#6897BB",
        Literal.String: "#6A8759",
        Literal.String.Doc: "#629755",
        Literal.String.Escape: "#6897BB",
        Generic: "#808080",
        Generic.Deleted: "#BC3F3C",
        Generic.Emph: "italic #A9B7C6",
        Generic.Heading: "#A9B7C6",
        Generic.Inserted: "#A5C261",
        Generic.Output: "#A9B7C6",
        Generic.Prompt: "#808080",
        Generic.Strong: "bold #A9B7C6",
        Generic.Subheading: "#A9B7C6",
        Generic.Traceback: "#BC3F3C",
    }
