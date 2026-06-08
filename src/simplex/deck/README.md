# deck/

Per-deck configuration, sectioned discovery, scaffolding.

## Public surface

- `DeckConfig` -- frozen pydantic model loaded from `deck.toml`.
- `SectionConfig` -- frozen model loaded from `decks/<dir>/_section.toml`.
- `discover(decks_dir)` -- returns a `SectionedRegistry` (sections -> decks).
- `scaffold(target, decks_dir)` -- copies `_template/` into either
  `decks/<slug>/` (featured) or `decks/<section>/<slug>/`.

## Config conventions

- `entrypoints` is the preferred ordered scene list.
- `date = "YYYY-MM-DD"` is an optional explicit publication date. When absent,
  the web builder derives a date from Git/file history.
- `[slide_themes]` owns true dark/light render theme names.
- `[web] show_notes_date = true` displays the resolved date in notes.
- Slide note labels are generated from rendered slide titles with
  `simplex.web.slide_ref.label_key`; do not add a manual notes-anchor field.
- `voiceover` is intentionally not a deck config field. Narration belongs in
  scene code through a voiceover plugin such as `manim-voiceover`.

## Don't

- Don't load `deck.toml` outside of `DeckConfig.load`.
- Don't recurse deeper than one level -- decks live at `decks/<slug>/` or
  `decks/<section>/<slug>/`, never below.
- Don't add required config fields unless every scaffolded deck is updated in
  the same change.
