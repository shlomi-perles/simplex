# Notes

This deck is a starting point. Replace the contents of `slides/` and fill these notes.

Refer to a slide inline with `[slide:1]` to add a clickable jump link.

Add a sidenote with the `^[...]` syntax — it floats into the right margin on wide screens.^[Sidenotes are Tufte-style: a numbered reference inline, the body in the gutter; narrow viewports collapse to an inline reveal on click.]

Inline math: $a^2 + b^2 = c^2$. Display math:

$$
\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}
$$

Theorem / definition / lemma / remark / proof blockquotes turn into colour-coded callouts and get anchored ids automatically:

> **Theorem 1.1.** Every blockquote whose first paragraph begins with `**Theorem N.N.**` (or `Lemma`, `Definition`, `Remark`, `Proof`, …) becomes a referenceable callout.

Reference one by id with `\ref{theorem-1-1}` — the renderer resolves it to **Theorem 1.1** automatically.

Cite the bundled `refs.bib` with `\cite{key}` — the build appends a References section automatically (`\cite{KB15}` here).

Code blocks render with Pygments:

```python
print("hello, simplex")
```
