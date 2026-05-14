# render/

Manim-slides invocation, manifest parsing, thumbnail extraction, PDF
export, HTML viewer emission, content-hash render cache.

## Public surface

- `runner.render(deck, output_dir)` -- `manim-slides render`.
- `pdf.export(deck, output_dir)` -- `manim-slides convert --to=pdf`.
- `manifest.build_manifest(deck, media_dir)` -> `DeckManifest(slides=...)`.
- `thumbnail.generate(deck, manifest, site_deck_dir, cache_dir)` -- ffmpeg.
- `html.render_html(deck, manifest, output_dir, static_prefix)` -- emits
  `slides.html` with our RevealJS template + postMessage bridge.
- `cache.is_fresh(deck, cache_dir)` / `cache.mark_fresh(...)`.

## Don't

- Don't shell-quote (`shell=True`). Always pass arg lists.
- Don't depend on a specific manim-slides JSON schema beyond the
  permissive `manifest.py` parser.
- Don't write outside of `output_dir` / the cache dir.
