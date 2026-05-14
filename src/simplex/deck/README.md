# deck/

Per-deck configuration and discovery.

## Public surface

- `DeckConfig` -- frozen pydantic model loaded from `deck.toml`
- `discover(decks_dir)` -- returns `list[DeckConfig]` sorted by slug
- `scaffold(slug, decks_dir)` -- copies `_template/` into `decks/<slug>/`

## Don't

- Don't load `deck.toml` outside of `DeckConfig.load`.
- Don't recurse into nested deck directories -- every deck is a direct child of `decks/`.
- Don't add fields without a default. Older decks must keep validating after a config bump.
