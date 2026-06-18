# tests/manager/

Unit tests for the local browser manager.

## Public surface

- `test_state.py` -- manager deck state, current string entrypoint TOML edits,
  add-back scene discovery, deck defaults editing, Manim quality options, and
  cache flag selection.
- `test_jobs.py` -- render/build command assembly, job names, scene output
  lookup, open-after behavior, foreground opener guardrails, and ANSI wrapper
  routing.

## Don't

- Don't start the HTTP manager server here; test handlers and helpers directly.
- Don't run real Manim renders. Output lookup tests create tiny placeholder
  files under `.simplex_cache`.
- Don't assert a copied quality map. Quality behavior should stay derived from
  `manim.constants.QUALITIES`.
