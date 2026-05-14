# tests/deck/

Tests for `simplex.deck`: DeckConfig validation, discovery, scaffolder.

## Don't

- Don't touch `decks/` at the repo root. Create temp deck dirs via `tmp_path`.
- Don't rely on cwd. Pass absolute paths.
