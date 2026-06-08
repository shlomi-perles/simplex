# Notes

This deck is a starting point. Replace the contents of `slides/` and fill these notes.

Refer to a slide label inline with `[slide:a-second-slide]` to add a clickable jump link: [slide:a-second-slide].

Add a sidenote with the `^[...]` syntax — it floats into the right margin on wide screens.^[Sidenotes are Tufte-style: a numbered reference inline, the body in the gutter; narrow viewports open a bottom-sheet note on click.]

Inline math: $a^2 + b^2 = c^2$. Display math:

$$
\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}
$$

Theorem / definition / lemma / remark / proof blockquotes turn into colour-coded callouts and get anchored ids automatically:

> **Theorem.** \label{thm:first} Every blockquote whose first paragraph begins with `**Theorem.**` (or `Lemma`, `Definition`, `Remark`, `Proof`, …) becomes a referenceable callout. The renderer numbers theorem-style callouts automatically.

Reference one by label with `\ref{thm:first}` or `\autoref{thm:first}` — the renderer resolves it to \autoref{thm:first} automatically.

Cite the bundled `refs.bib` with `\cite{key}` — the build appends a References section automatically. For example, Adam is introduced in \cite{KB15}.

Code blocks render with Pygments:

```python
print("hello, simplex")
```
