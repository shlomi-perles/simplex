"""Render deck notes to a LaTeX-backed PDF.

The web page remains the canonical notes view; this exporter creates a
downloadable reading copy when a TeX engine is available. Markdown block
structure is parsed with markdown-it so tables, lists, paragraphs, and code
blocks survive the conversion instead of being treated as plain text.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin

from simplex.deck.config import DeckConfig
from simplex.render.filenames import pdf_name
from simplex.web import bibtex
from simplex.web.bibliography import BibEntry, Bibliography
from simplex.web.slide_ref import SlideRefMap, label_key

_CITE_RE = re.compile(r"\\cite\{([^}]+)\}")


def export(
    deck: DeckConfig,
    notes_path: Path,
    *,
    output_dir: Path,
    slide_refs: SlideRefMap | None = None,
    bibliography: Bibliography | None = None,
) -> Path:
    """Write ``<output_dir>/<title>-note.pdf`` from ``notes.md``.

    Raises ``FileNotFoundError`` when no supported TeX engine is available and
    ``subprocess.CalledProcessError`` when LaTeX rejects the generated document.
    Callers should treat both as a soft failure.
    """
    engine = _find_engine()
    if engine is None:
        raise FileNotFoundError("xelatex, lualatex, or pdflatex is required for notes PDF export")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / pdf_name(deck, "note")
    source = notes_path.read_text(encoding="utf-8")
    used_citations: list[str] = []
    body = _markdown_to_latex(source, used_citations, slide_refs or {})
    document = _document(deck, body, bibliography, tuple(used_citations))

    with tempfile.TemporaryDirectory(prefix="simplex-notes-") as tmp:
        work = Path(tmp)
        tex_path = work / "notes.tex"
        tex_path.write_text(document, encoding="utf-8")
        for _ in range(2):
            subprocess.run(
                [
                    engine,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    tex_path.name,
                ],
                cwd=work,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        shutil.copy2(work / "notes.pdf", pdf_path)
    return pdf_path


def _find_engine() -> str | None:
    for name in ("xelatex", "lualatex", "pdflatex"):
        if shutil.which(name):
            return name
    return None


def _document(
    deck: DeckConfig,
    body: str,
    bibliography: Bibliography | None,
    used_citations: tuple[str, ...],
) -> str:
    bib = _bibliography_latex(bibliography, used_citations)
    title = _escape_latex(deck.title)
    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{amsmath,amssymb}}
\usepackage{{array,booktabs,enumitem,fancyvrb,tabularx}}
\usepackage{{hyperref}}
\usepackage{{xcolor}}
\hypersetup{{colorlinks=true, linkcolor=blue, urlcolor=blue, citecolor=blue}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.65em}}
\renewcommand{{\arraystretch}}{{1.2}}
\title{{{title}}}
\date{{}}
\begin{{document}}
\maketitle
{body}
{bib}
\end{{document}}
"""


def _markdown_to_latex(
    markdown: str,
    used_citations: list[str],
    slide_refs: SlideRefMap,
) -> str:
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    md.use(dollarmath_plugin, allow_labels=True)
    tokens = md.parse(markdown)
    return "\n".join(_render_blocks(tokens, used_citations, slide_refs)).strip()


def _render_blocks(
    tokens: list[Token],
    used_citations: list[str],
    slide_refs: SlideRefMap,
) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "heading_open":
            inline = _next_inline(tokens, i)
            level = int(token.tag[1:]) if token.tag.startswith("h") else 1
            command = "section" if level == 1 else "subsection" if level == 2 else "subsubsection"
            out.append(rf"\{command}*{{{_inline_to_latex(inline, used_citations, slide_refs)}}}")
            i = _skip_to(tokens, i, "heading_close") + 1
        elif token.type == "paragraph_open":
            inline = _next_inline(tokens, i)
            if inline.strip():
                out.append(_inline_to_latex(inline, used_citations, slide_refs) + r"\par")
            i = _skip_to(tokens, i, "paragraph_close") + 1
        elif token.type == "bullet_list_open":
            lines, i = _render_list(tokens, i, "itemize", used_citations, slide_refs)
            out.extend(lines)
        elif token.type == "ordered_list_open":
            lines, i = _render_list(tokens, i, "enumerate", used_citations, slide_refs)
            out.extend(lines)
        elif token.type == "blockquote_open":
            end = _find_matching(tokens, i, "blockquote_open", "blockquote_close")
            body = _render_blocks(tokens[i + 1 : end], used_citations, slide_refs)
            out.extend([r"\begin{quote}", *body, r"\end{quote}"])
            i = end + 1
        elif token.type == "math_block":
            out.append("\\[\n" + token.content.strip() + "\n\\]")
            i += 1
        elif token.type in {"fence", "code_block"}:
            out.extend(
                [
                    r"\begin{Verbatim}[fontsize=\small]",
                    token.content.rstrip(),
                    r"\end{Verbatim}",
                ]
            )
            i += 1
        elif token.type == "table_open":
            lines, i = _render_table(tokens, i, used_citations, slide_refs)
            out.extend(lines)
        else:
            i += 1
    return out


def _render_list(
    tokens: list[Token],
    start: int,
    env: str,
    used_citations: list[str],
    slide_refs: SlideRefMap,
) -> tuple[list[str], int]:
    close_type = "bullet_list_close" if env == "itemize" else "ordered_list_close"
    out = [rf"\begin{{{env}}}[leftmargin=*]"]
    i = start + 1
    while i < len(tokens) and tokens[i].type != close_type:
        if tokens[i].type != "list_item_open":
            i += 1
            continue
        end = _find_matching(tokens, i, "list_item_open", "list_item_close")
        item = "\n".join(_render_blocks(tokens[i + 1 : end], used_citations, slide_refs)).strip()
        out.append(r"\item " + item)
        i = end + 1
    out.append(rf"\end{{{env}}}")
    return out, i + 1


def _render_table(
    tokens: list[Token],
    start: int,
    used_citations: list[str],
    slide_refs: SlideRefMap,
) -> tuple[list[str], int]:
    rows: list[tuple[str, list[str]]] = []
    section = "body"
    row: list[str] | None = None
    i = start + 1
    while i < len(tokens) and tokens[i].type != "table_close":
        token = tokens[i]
        if token.type == "thead_open":
            section = "head"
        elif token.type == "tbody_open":
            section = "body"
        elif token.type == "tr_open":
            row = []
        elif token.type == "inline" and row is not None:
            row.append(_inline_to_latex(token.content, used_citations, slide_refs))
        elif token.type == "tr_close" and row is not None:
            rows.append((section, row))
            row = None
        i += 1
    if not rows:
        return [], i + 1

    col_count = max(len(r) for _, r in rows)
    spec = rf"@{{}}*{{{col_count}}}{{>{{\raggedright\arraybackslash}}X}}@{{}}"
    out = [rf"\begin{{tabularx}}{{\linewidth}}{{{spec}}}", r"\toprule"]
    for idx, (kind, cells) in enumerate(rows):
        padded = [*cells, *([""] * (col_count - len(cells)))]
        out.append(" & ".join(padded) + r" \\")
        if kind == "head" and (idx == len(rows) - 1 or rows[idx + 1][0] != "head"):
            out.append(r"\midrule")
    out.extend([r"\bottomrule", r"\end{tabularx}"])
    return out, i + 1


def _next_inline(tokens: list[Token], start: int) -> str:
    if start + 1 < len(tokens) and tokens[start + 1].type == "inline":
        return tokens[start + 1].content
    return ""


def _skip_to(tokens: list[Token], start: int, close_type: str) -> int:
    for i in range(start + 1, len(tokens)):
        if tokens[i].type == close_type:
            return i
    return len(tokens) - 1


def _find_matching(tokens: list[Token], start: int, open_type: str, close_type: str) -> int:
    depth = 1
    for i in range(start + 1, len(tokens)):
        if tokens[i].type == open_type:
            depth += 1
        elif tokens[i].type == close_type:
            depth -= 1
            if depth == 0:
                return i
    return len(tokens) - 1


def _inline_to_latex(
    text: str,
    used_citations: list[str],
    slide_refs: SlideRefMap,
) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        if text.startswith(r"\cite{", i):
            end = text.find("}", i + 6)
            if end != -1:
                cite = text[i : end + 1]
                _record_citations(cite, used_citations)
                out.append(cite)
                i = end + 1
                continue
        if text.startswith(r"\ref{", i):
            end = text.find("}", i + 5)
            if end != -1:
                out.append(text[i : end + 1])
                i = end + 1
                continue
        if text.startswith("^[", i):
            end = text.find("]", i + 2)
            if end != -1:
                note = _inline_to_latex(text[i + 2 : end], used_citations, slide_refs)
                out.append(rf"\footnote{{{note}}}")
                i = end + 1
                continue
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end != -1:
                bold = _inline_to_latex(text[i + 2 : end], used_citations, slide_refs)
                out.append(rf"\textbf{{{bold}}}")
                i = end + 2
                continue
        if text[i] == "`":
            end = text.find("`", i + 1)
            if end != -1:
                out.append(rf"\texttt{{{_escape_latex(text[i + 1 : end])}}}")
                i = end + 1
                continue
        if text.startswith("[slide:", i):
            end = text.find("]", i + 7)
            if end != -1:
                out.append(_slide_ref_latex(text[i + 7 : end], slide_refs))
                i = end + 1
                continue
        if text[i] == "[":
            match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", text[i:])
            if match:
                label = _inline_to_latex(match.group(1), used_citations, slide_refs)
                href = _escape_latex(match.group(2))
                out.append(rf"\href{{{href}}}{{{label}}}")
                i += match.end()
                continue
        if text[i] == "$":
            end = text.find("$", i + 1)
            if end != -1:
                out.append(text[i : end + 1])
                i = end + 1
                continue
        out.append(_escape_latex(text[i]))
        i += 1
    return "".join(out)


def _slide_ref_latex(raw: str, slide_refs: SlideRefMap) -> str:
    target = slide_refs.get(label_key(raw))
    if target is None and raw.strip().isdigit():
        return rf"slide~{_escape_latex(raw.strip())}"
    if target is None:
        return _escape_latex(raw.strip())
    index, label = target
    return rf"slide~{index} ({_escape_latex(label)})"


def _record_citations(cite: str, used: list[str]) -> None:
    match = _CITE_RE.fullmatch(cite)
    if not match:
        return
    for key in match.group(1).split(","):
        clean = key.strip()
        if clean and clean not in used:
            used.append(clean)


def _bibliography_latex(bibliography: Bibliography | None, used: tuple[str, ...]) -> str:
    if bibliography is None:
        return ""
    items: list[str] = []
    for key in used:
        if not bibliography.has(key):
            continue
        entry = bibliography.get(key)
        items.append(_bibitem(entry))
    if not items:
        return ""
    return "\n".join([r"\begin{thebibliography}{99}", *items, r"\end{thebibliography}"])


def _bibitem(entry: BibEntry) -> str:
    parts: list[str] = []
    if entry.authors:
        parts.append(", ".join(_escape_latex(author.display) for author in entry.authors))
    if title := entry.fields.get("title"):
        parts.append(rf"\emph{{{_escape_latex(bibtex.unbrace(title))}}}")
    for field in ("journal", "booktitle", "publisher", "school", "institution"):
        if value := entry.fields.get(field):
            parts.append(_escape_latex(bibtex.unbrace(value)))
            break
    if entry.year is not None:
        parts.append(str(entry.year))
    if url := entry.fields.get("url"):
        parts.append(rf"\url{{{_escape_latex(bibtex.unbrace(url))}}}")
    body = ", ".join(parts) or _escape_latex(entry.key)
    return rf"\bibitem[{_escape_latex(entry.alpha_key)}]{{{_escape_latex(entry.key)}}} {body}."


_LATEX_ESCAPE = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
    "\u2014": "---",
    "\u2013": "--",
}


def _escape_latex(text: str) -> str:
    return "".join(_LATEX_ESCAPE.get(ch, ch) for ch in text)
