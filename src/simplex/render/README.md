# render/

Manim-slides invocation, manifest parsing, thumbnail extraction, PDF
export, HTML viewer emission, content-hash render cache.

## Public surface

- `runner.render(deck, output_dir, scenes=())` -- `manim-slides render`;
  passes `SIMPLEX_THEME` / `SIMPLEX_QUALITY` env vars so `BaseSlide` can
  apply the theme before the camera is constructed.
- `pdf.export(deck, output_dir)` -- `manim-slides convert --to=pdf`.
- `manifest.build_manifest(deck, media_dir)` -> `DeckManifest(slides=...)`.
- `thumbnail.generate(deck, manifest, site_deck_dir, cache_dir)` -- ffmpeg.
- `html.render_html(deck, manifest, output_dir, static_prefix)` -- emits
  `slides.html` with our RevealJS template + postMessage bridge.
- `cache.is_fresh / mark_fresh / clear` -- stamp lives at
  `.simplex_cache/<slug>.<sha>.stamp`.

## Cache & re-render

`cache_key` is a sha256 over (a) every `slides.py` / `slides/**/*.py` /
`deck.toml` byte under the deck, plus (b) the `theme` and `quality`
values. Editing any of those auto-invalidates the stamp.

Forcing a re-render or re-rendering a subset:

```bash
uv run simplex render <slug> --force                # ignore the stamp
uv run simplex render <slug> --scene CodeHelpers    # one class only
uv run simplex render <slug> --scene A --scene B    # multiple
uv run simplex build --force                        # every deck
uv run simplex build --only <slug>                  # one deck only
uv run simplex build --scene A --only <slug>        # combine
```

`--scene` implies `--force`. Unknown class names fail loudly. A partial
re-render does **not** mark the deck fresh -- instead it *clears* the
existing stamp, so the next non-partial run re-renders fully and no
stale stamp can mask scenes you didn't touch.

`simplex clean --deck <slug>` removes just that deck's
`site/decks/<slug>/`, its cache stamp, and its thumbnail cache. Bare
`simplex clean` wipes `site/`, `media/`, and `.simplex_cache/`.

## Don't

- Don't shell-quote (`shell=True`); always pass arg lists.
- Don't depend on a specific manim-slides JSON schema beyond `manifest.py`.
- Don't write outside `output_dir` / the cache dir.
- Don't call `cache.mark_fresh` after a partial render.
