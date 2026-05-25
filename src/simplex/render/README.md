# render/

Manim-slides subprocess invocation, native-section reconcile, thumbnail
extraction, PDF / PowerPoint export, notes PDF export, HTML viewer emission.

## Public surface

- `runner.render(deck, output_dir, scenes=(), write_last_frame=False)` --
  spawns `manim-slides render` with `--save_sections` (and
  `--disable_caching` when `deck.caching = False`).
- `pdf.export(deck, output_dir)` -- in-process via
  `manim_slides.convert.PDF`, writing `<title>-slides.pdf`.
- `pptx.export(deck, output_dir)` -- in-process via
  `manim_slides.convert.PowerPoint`.
- `notes_pdf.export(deck, notes_path, output_dir, slide_refs=None,
  bibliography=None)` -- best-effort LaTeX PDF rendering for `notes.md`,
  writing `<title>-note.pdf`. The exporter preserves `\label{}` /
  `\autoref{}` and emits `amsthm` environments for theorem-style callouts.
- `reconcile.build_manifest(deck, media_dir)` -> `DeckManifest`
  (a tuple of `MainSlide`, each with its own `subsections`).
- `thumbnail.generate(deck, manifest, site_deck_dir, cache_dir)` --
  ffmpeg last-frame extraction (default rule: second-to-last subsection).
- `html.render_html(deck, manifest, output_dir, static_prefix)` --
  Jinja-renders `web/templates/revealjs.html.j2` with the main/sub tree.

## Smart compilation

The plugin sets `manim.config.save_sections = True`. Combined with manim's
per-animation hash cache, re-editing one animation re-encodes only that
animation; sections of only-cached animations are stitched from disk. No
separate Simplex render cache -- run `uv run simplex clean --deck <slug>`
to force a clean re-render.

## Reconcile

`build_manifest` walks each scene's
`media/videos/<src>/<q>/sections/<Scene>.json` (written by manim when
`save_sections=True`): every `type.startswith("simplex.main")` (and the
auto-created first `default.normal`) starts a new `MainSlide`; everything
else attaches as a `Subsection` of the current main. The parallel
`media/slides/<Scene>.json` is consumed only by the PDF / PPTX converters.

## Don't

- Don't shell-quote (`shell=True`); always pass arg lists.
- Don't add a parallel cache stamp -- the manim per-animation cache is
  already content-addressable.
- Don't write outside `output_dir`.
- Don't read manim-slides' `PresentationConfig` JSON for hierarchy info;
  the section JSON is the source of truth.
