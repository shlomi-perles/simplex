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

_TEXT = "#A9B7C6"
_ERROR = "#960050"
_COMMENT = "#808080"
_KEYWORD = "#CC7832"
_NAME = "#C8D1DA"
_ATTRIBUTE = "#BABABA"
_BUILTIN = "#8888C6"
_PSEUDO = "#9876AA"
_CLASS = "#FFC66D"
_DECORATOR = "#BBB529"
_ENTITY = "#6D9CBE"
_OTHER = "#88BE05"
_TAG = "#E8BF6A"
_NUMBER = "#6897BB"
_STRING = "#6A8759"
_DOC_STRING = "#629755"
_DELETED = "#BC3F3C"
_INSERTED = "#A5C261"


class SimplexPycharm(Style):
    """Dark Pygments scheme inspired by PyCharm's Darcula palette."""

    background_color = "#1A1A1A"
    highlight_color = "#333333"

    styles = {  # noqa: RUF012 -- Pygments declares `styles` as a class attribute
        Text: _TEXT,
        Error: _ERROR,
        Comment: _COMMENT,
        Comment.Multiline: _COMMENT,
        Comment.Preproc: _COMMENT,
        Comment.Single: _COMMENT,
        Comment.Special: _COMMENT,
        Keyword: _KEYWORD,
        Keyword.Constant: _KEYWORD,
        Keyword.Declaration: _KEYWORD,
        Keyword.Namespace: _KEYWORD,
        Keyword.Pseudo: _KEYWORD,
        Keyword.Reserved: _KEYWORD,
        Keyword.Type: _KEYWORD,
        Operator: _TEXT,
        Operator.Word: _KEYWORD,
        Punctuation: _TEXT,
        Name: _NAME,
        Name.Attribute: _ATTRIBUTE,
        Name.Builtin: _BUILTIN,
        Name.Builtin.Pseudo: _PSEUDO,
        Name.Class: _CLASS,
        Name.Constant: _PSEUDO,
        Name.Decorator: _DECORATOR,
        Name.Entity: _ENTITY,
        Name.Exception: _CLASS,
        Name.Function: _CLASS,
        Name.Label: _NAME,
        Name.Namespace: _NAME,
        Name.Other: _OTHER,
        Name.Tag: _TAG,
        Name.Variable: _NAME,
        Name.Variable.Class: _PSEUDO,
        Name.Variable.Global: _PSEUDO,
        Name.Variable.Instance: _PSEUDO,
        Literal: _NUMBER,
        Literal.Date: _STRING,
        Literal.Number: _NUMBER,
        Literal.String: _STRING,
        Literal.String.Doc: _DOC_STRING,
        Literal.String.Escape: _NUMBER,
        Generic: _COMMENT,
        Generic.Deleted: _DELETED,
        Generic.Emph: f"italic {_TEXT}",
        Generic.Heading: _TEXT,
        Generic.Inserted: _INSERTED,
        Generic.Output: _TEXT,
        Generic.Prompt: _COMMENT,
        Generic.Strong: f"bold {_TEXT}",
        Generic.Subheading: _TEXT,
        Generic.Traceback: _DELETED,
    }
