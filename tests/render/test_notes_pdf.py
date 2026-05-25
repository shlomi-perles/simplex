from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from simplex.deck.config import DeckConfig
from simplex.render import notes_pdf
from simplex.web.bibliography import Bibliography


def test_notes_pdf_export_writes_latex_and_copies_pdf(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    notes = deck_dir / "notes.md"
    notes.write_text(
        r"""# Notes

See [slide:key-idea].

| Thing | Value |
|-------|-------|
| `x` | **bold** |

- First item.
- Second item.

> **Theorem.** \label{thm:first} Every finite list has a first item.

See \autoref{thm:first}.

Cite \cite{KB15}. This line has a sidenote.^[A mobile note.]
""",
        encoding="utf-8",
    )
    deck = DeckConfig(slug="demo", title="Demo Deck", path=deck_dir)
    bibliography = Bibliography.parse(
        r"""
@article{KB15,
  author = {Kingma, Diederik P. and Ba, Jimmy},
  title = {Adam: A Method for Stochastic Optimization},
  year = {2015},
}
"""
    )
    generated: list[str] = []

    def fake_run(args: list[str], *, cwd: Path, **_: object) -> subprocess.CompletedProcess[str]:
        generated.append((cwd / "notes.tex").read_text(encoding="utf-8"))
        (cwd / "notes.pdf").write_bytes(b"%PDF-1.7\n")
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(notes_pdf, "_find_engine", lambda: "fake-latex")
    monkeypatch.setattr(subprocess, "run", fake_run)

    pdf = notes_pdf.export(
        deck,
        notes,
        output_dir=tmp_path / "site" / "demo",
        slide_refs={"key-idea": (2, "Key Idea")},
        bibliography=bibliography,
    )

    assert pdf.name == "Demo Deck-note.pdf"
    assert pdf.read_bytes() == b"%PDF-1.7\n"
    assert generated
    tex = generated[-1]
    assert r"\usepackage{amsmath,amssymb,amsthm}" in tex
    assert r"\definecolor{blue}{RGB}{12,97,197}" in tex
    assert r"\definecolor{green}{RGB}{0,128,40}" in tex
    assert "bookmarksopenlevel=1" in tex
    assert "citecolor=green" in tex
    assert "anchorcolor=blue" in tex
    assert r"\newtheorem{thm}{Theorem}" in tex
    assert r"slide~2 (Key Idea)" in tex
    assert r"\begin{tabularx}" in tex
    assert r"\begin{itemize}" in tex
    assert r"\item First item.\par" in tex
    assert r"\begin{thm}" in tex
    assert r"\label{thm:first}" in tex
    assert r"\autoref{thm:first}" in tex
    assert r"\textbackslash{}label" not in tex
    assert r"\cite{KB15}" in tex
    assert r"\footnote{A mobile note.}" in tex
    assert r"\begin{thebibliography}{99}" in tex
    assert r"\bibitem[" in tex
