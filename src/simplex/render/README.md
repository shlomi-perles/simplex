# render/

Manim-slides subprocess invocation, native-section reconcile, thumbnail
extraction, PDF / PowerPoint export, HTML viewer emission.

## Public surface

- `runner.render(deck, output_dir, scenes=(), write_last_frame=False)` --
  spawns `manim-slides render` with `--save_sections` (and
  `--disable_caching` when `deck.caching = False`).
- `pdf.export(deck, output_dir)` -- in-process via
  `manim_slides.convert.PDF`.
- `pptx.export(deck, output_dir)` -- in-process via
  `manim_slides.convert.PowerPoint`.
- `reconcile.build_manifest(deck, media_dir)` -> `DeckManifest`
  (a tuple of `MainSlide`, each with its own `subsections`).
- `thumbnail.generate(deck, manifest, site_deck_dir, cache_dir)` --
  ffmpeg last-frame extraction (default rule: second-to-last subsection).
- `html.render_html(deck, manifest, output_dir, static_prefix)` --
  Jinja-renders `web/templates/revealjs.html.j2` with the main/sub tree.

## Smart compilation

The Simplex plugin sets `manim.config.save_sections = True` at every
`import manim`. Combined with manim's own per-animation hash cache
(`SceneFileWriter.is_already_cached`), that means re-editing one
animation in `scenes.py` re-encodes only that animation; sections
containing only cached animations are stitched from disk.

There is **no separate Simplex render cache**. Editing a deck source
file invalidates only the affected animation hashes; everything else
is reused. To force a clean re-render: `uv run simplex clean --deck <slug>`.

## Reconcile

Two JSON sources per scene:

- `media/videos/<src_stem>/<quality>/sections/<Scene>.json` (written by
  manim when `save_sections=True`). Carries `name`, `type` (our
  `SimplexSectionType`), `video`, plus ffprobe metadata.
- `media/slides/<Scene>.json` (written by manim-slides). Used by the PDF /
  PPTX converters; not read by reconcile directly.

`build_manifest` walks each scene's sections in order: every
`type.startswith("simplex.main")` (and the auto-created first
`default.normal`) starts a new `MainSlide`; everything else attaches as
a `Subsection` of the current main.

## Don't

- Don't shell-quote (`shell=True`); always pass arg lists.
- Don't add a parallel cache stamp -- the manim per-animation cache is
  already content-addressable.
- Don't write outside `output_dir`.
- Don't read manim-slides' `PresentationConfig` JSON for hierarchy info;
  the section JSON is the source of truth.
