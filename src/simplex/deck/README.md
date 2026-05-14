# deck/

Per-deck configuration, sectioned discovery, scaffolding.

## Public surface

- `DeckConfig` -- frozen pydantic model loaded from `deck.toml`.
- `SectionConfig` -- frozen model loaded from `decks/<dir>/_section.toml`.
- `discover(decks_dir)` -- returns a `SectionedRegistry` (sections -> decks).
- `scaffold(target, decks_dir)` -- copies `_template/` into either
  `decks/<slug>/` (featured) or `decks/<section>/<slug>/`.

## Don't

- Don't load `deck.toml` outside of `DeckConfig.load`.
- Don't recurse deeper than one level -- decks live at `decks/<slug>/` or
  `decks/<section>/<slug>/`, never below.
- Don't add fields without a default. Older decks must keep validating
  after a config bump.
