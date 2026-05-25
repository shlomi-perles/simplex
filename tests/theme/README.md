# tests/theme/

Tests for `simplex.theme`: frozen-token invariants, preset values seeded from Simplex, ContextVar push/pop.

## Don't

- Don't import `manim` here. Theme tests must stay fast and pure-Python.
- Don't assert exact color hex codes for the entire palette -- only those the plan calls out as locked-in (e.g. background `#242424`, definition env).
