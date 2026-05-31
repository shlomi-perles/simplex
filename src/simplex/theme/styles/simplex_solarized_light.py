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
    Token,
)

_TEXT = "#002b36"
_IDENTIFIER = "#024050"
_MUTED = "#586e75"
_KEYWORD = "#db7448"
_FUNCTION = "#0066CC"
_BUILTIN = "#4f66c4"
_CONSTANT = "#50023B"
_STRING = "#427925"
_NUMBER = "#E237BD"
_OPERATOR = "#000000"
_ERROR = "#dc322f"


class SimplexSolarizedLight(Style):
    """Warm light scheme inspired by Solarized Light."""

    background_color = "#fffce4"
    highlight_color = "#eee8d5"

    styles = {  # noqa: RUF012 -- Pygments declares `styles` as a class attribute
        Token: "bold",
        Text: _TEXT,
        Error: f"bold {_ERROR}",
        Comment: f"italic {_MUTED}",
        Comment.Multiline: f"italic {_MUTED}",
        Comment.Preproc: f"italic {_MUTED}",
        Comment.Single: f"italic {_MUTED}",
        Comment.Special: f"italic bold {_MUTED}",
        Keyword: _KEYWORD,
        Keyword.Constant: _KEYWORD,
        Keyword.Declaration: _KEYWORD,
        Keyword.Namespace: _KEYWORD,
        Keyword.Pseudo: _KEYWORD,
        Keyword.Reserved: _KEYWORD,
        Keyword.Type: _KEYWORD,
        Operator: _OPERATOR,
        Operator.Word: _KEYWORD,
        Punctuation: _IDENTIFIER,
        Name: _IDENTIFIER,
        Name.Attribute: _FUNCTION,
        Name.Builtin: _BUILTIN,
        Name.Builtin.Pseudo: _CONSTANT,
        Name.Class: f"bold {_FUNCTION}",
        Name.Constant: _CONSTANT,
        Name.Decorator: _KEYWORD,
        Name.Entity: _IDENTIFIER,
        Name.Exception: f"bold {_ERROR}",
        Name.Function: _FUNCTION,
        Name.Label: _IDENTIFIER,
        Name.Namespace: _CONSTANT,
        Name.Other: _IDENTIFIER,
        Name.Tag: _KEYWORD,
        Name.Variable: _IDENTIFIER,
        Name.Variable.Class: _CONSTANT,
        Name.Variable.Global: _CONSTANT,
        Name.Variable.Instance: _CONSTANT,
        Number: _NUMBER,
        Literal: _NUMBER,
        Literal.Date: _STRING,
        String: _STRING,
        Literal.String: _STRING,
        Literal.String.Doc: f"italic {_STRING}",
        Literal.String.Escape: _NUMBER,
        Literal.Number: _NUMBER,
        Generic: _MUTED,
        Generic.Deleted: _ERROR,
        Generic.Emph: f"italic {_TEXT}",
        Generic.Heading: f"bold {_TEXT}",
        Generic.Inserted: _STRING,
        Generic.Output: _TEXT,
        Generic.Prompt: _MUTED,
        Generic.Strong: f"bold {_TEXT}",
        Generic.Subheading: _TEXT,
        Generic.Traceback: _ERROR,
    }
