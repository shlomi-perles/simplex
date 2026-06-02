"""Generate the packaged Simplex Theme Studio HTML."""

from __future__ import annotations

import importlib.util
import json
import sys
import webbrowser
from importlib import resources
from pathlib import Path
from typing import Any

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.styles import get_all_styles, get_style_by_name
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator, String, Text
from pygments.util import ClassNotFound

from simplex.theme import palettes
from simplex.theme.styles import BUILTIN_STYLES

DEFAULT_OUTPUT = Path(".simplex") / "theme-studio" / "theme_studio.html"

CODE_PREVIEW_BUILTINS: tuple[str, ...] = (
    "simplex_pycharm",
    "simplex_solarized_light",
    "default",
    "monokai",
    "dracula",
    "friendly",
    "vs",
    "solarized-light",
    "solarized-dark",
    "nord",
    "gruvbox-dark",
    "material",
    "github-dark",
    "one-dark",
)

SAMPLE_CODE = """\
from pygments import highlight
def hello_world(name="Developer"):
    # This is a high-contrast comment
    print(f"Hello, {name}! Welcome to Pygments.")
    for i in range(5):
        print(f"Count: {i}")
        c = 0
    current_style = styles.get(token, '')
    return True
def f(x):
    return x * x
"""

DEFAULT_COLORS = {
    "--bg": "#1E1E1E",
    "--fg": "#D4D4D4",
    "--comment": "#6A9955",
    "--keyword": "#C586C0",
    "--string": "#CE9178",
    "--number": "#B5CEA8",
    "--name": "#9CDCFE",
    "--function": "#1F6FE4",
    "--class": "#8A46CE",
    "--builtin": "#1C6BBB",
    "--operator": "#D4D4D4",
}


def render_html(*, repo_root: Path | None = None) -> str:
    """Return a self-contained Theme Studio HTML document."""
    code = _build_code_data(repo_root=repo_root)
    palette = palettes.studio_palette_data(repo_root=repo_root)
    replacements = {
        "__PALETTE_COLORS__": json.dumps(palette["PALETTE_COLORS"]),
        "__PALETTE_DIRECT__": json.dumps(palette["PALETTE_DIRECT"]),
        "__PALETTE_LIST__": json.dumps(palette["PALETTE_LIST"]),
        "__PALETTE_PREVIEW__": json.dumps(palette["PALETTE_PREVIEW"]),
        "__PALETTE_CUSTOM__": json.dumps(palette["PALETTE_CUSTOM"]),
        "__DEFAULT_PALETTE_THEME__": json.dumps(palette["DEFAULT_PALETTE_THEME"]),
        "__CODE_PALETTES__": json.dumps(code["CODE_PALETTES"]),
        "__CODE_LIST__": json.dumps(code["CODE_LIST"]),
        "__CODE_PREVIEW__": json.dumps(code["CODE_PREVIEW"]),
        "__CODE_CUSTOM__": json.dumps(code["CODE_CUSTOM"]),
        "__DEFAULT_CODE_THEME__": json.dumps(code["DEFAULT_CODE_THEME"]),
        "__CODE_HTML__": json.dumps(code["CODE_HTML"]),
        "__CODE_DEFAULTS__": json.dumps(code["CODE_DEFAULTS"]),
    }
    html = _template()
    for marker, value in replacements.items():
        html = html.replace(marker, value)
    return html


def write_studio(
    output: Path = DEFAULT_OUTPUT,
    *,
    repo_root: Path | None = None,
    open_browser: bool = False,
) -> Path:
    """Write Theme Studio HTML and optionally open it in the default browser."""
    output = output if output.suffix else output / "theme_studio.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(repo_root=repo_root), encoding="utf-8")
    resolved = output.resolve()
    if open_browser:
        webbrowser.open(resolved.as_uri())
    return resolved


def _build_code_data(*, repo_root: Path | None = None) -> dict[str, object]:
    custom = _load_custom_code_styles(palettes.code_styles_dir(repo_root))
    all_styles: dict[str, type[Style]] = {}
    all_styles.update(_load_pygments_styles())
    all_styles.update(BUILTIN_STYLES)
    all_styles.update(custom)

    code_palettes: dict[str, dict[str, str]] = {}
    for name, cls in all_styles.items():
        try:
            code_palettes[name] = _build_code_palette(cls)
        except (TypeError, ValueError, AttributeError):
            continue

    custom_names = sorted(custom)
    all_names = sorted(code_palettes)
    preview = list(
        dict.fromkeys(
            custom_names + [name for name in CODE_PREVIEW_BUILTINS if name in code_palettes]
        )
    )
    default_theme = "simplex_pycharm" if "simplex_pycharm" in code_palettes else all_names[0]
    code_html = highlight(
        SAMPLE_CODE,
        PythonLexer(),
        HtmlFormatter(style="default", cssclass="code-block"),
    )
    return {
        "CODE_PALETTES": code_palettes,
        "CODE_LIST": all_names,
        "CODE_PREVIEW": preview,
        "CODE_CUSTOM": custom_names,
        "DEFAULT_CODE_THEME": default_theme,
        "CODE_HTML": code_html,
        "CODE_DEFAULTS": DEFAULT_COLORS,
    }


def _load_pygments_styles() -> dict[str, type[Style]]:
    out: dict[str, type[Style]] = {}
    for name in get_all_styles():
        style: type[Style] | None = None
        try:
            style = get_style_by_name(name)
        except ClassNotFound:
            style = None
        if style is None:
            continue
        out[name] = style
    return out


def _load_custom_code_styles(directory: Path) -> dict[str, type[Style]]:
    out: dict[str, type[Style]] = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = f"_simplex_custom_code_style_{path.stem}"
        module = None
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception:
            module = None
        if module is None:
            continue
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, Style)
                and obj is not Style
                and obj.__module__ == module_name
            ):
                out[obj.__name__] = obj
    return out


def _build_code_palette(style_class: type[Style]) -> dict[str, str]:
    background = _normalize_hex(str(getattr(style_class, "background_color", "")))
    if not background:
        background = DEFAULT_COLORS["--bg"]
    return {
        "--bg": background,
        "--fg": _first_color(style_class, (Text, Name), DEFAULT_COLORS["--fg"]),
        "--comment": _first_color(
            style_class,
            (Comment, Comment.Single, Comment.Multiline, Comment.Preproc, Comment.Special),
            DEFAULT_COLORS["--comment"],
        ),
        "--keyword": _first_color(
            style_class,
            (Keyword, Keyword.Type, Keyword.Constant, Keyword.Namespace),
            DEFAULT_COLORS["--keyword"],
        ),
        "--string": _first_color(
            style_class,
            (String, Literal.String, String.Double, String.Single),
            DEFAULT_COLORS["--string"],
        ),
        "--number": _first_color(style_class, (Number, Literal.Number), DEFAULT_COLORS["--number"]),
        "--name": _first_color(
            style_class,
            (Name, Name.Attribute, Name.Namespace, Name.Variable),
            DEFAULT_COLORS["--name"],
        ),
        "--function": _first_color(
            style_class,
            (Name.Function, Name.Function.Magic),
            DEFAULT_COLORS["--function"],
        ),
        "--class": _first_color(style_class, (Name.Class,), DEFAULT_COLORS["--class"]),
        "--builtin": _first_color(
            style_class,
            (Name.Builtin, Name.Builtin.Pseudo),
            DEFAULT_COLORS["--builtin"],
        ),
        "--operator": _first_color(
            style_class,
            (Operator, Operator.Word),
            DEFAULT_COLORS["--operator"],
        ),
    }


def _first_color(style_class: type[Style], tokens: tuple[Any, ...], fallback: str) -> str:
    for token in tokens:
        style = style_class.style_for_token(token)
        if color := style.get("color"):
            return _normalize_hex(str(color))
    return fallback


def _normalize_hex(color: str) -> str:
    color = color.strip()
    if not color:
        return ""
    if color.startswith("#"):
        return color.upper()
    if len(color) in (3, 6) and all(ch in "0123456789abcdefABCDEF" for ch in color):
        return f"#{color.upper()}"
    return color


def _template() -> str:
    return (
        resources.files("simplex.theme")
        .joinpath("studio_template.html")
        .read_text(encoding="utf-8")
    )
