# render/

Timeline-native rendering and packaging.

## Public Surface

- `runner.render(deck, output_dir, manim_args=(), scenes=())` renders Manim
  scene units directly and writes Simplex cue JSON under
  `output_dir/simplex-cues/`.
- `timeline.load_units(...)`, `timeline.rebase_cues(...)`, and
  `timeline.package_theme(...)` compose scene units into one lecture timeline
  per theme, then emit HLS/CMAF plus a progressive MP4 fallback.
- `thumbnail.generate_cue_images(...)` extracts cue posters and thumbnails
  from the composed lecture timeline.
- `pdf.export(...)` and `pptx.export(...)` rebuild exports from cue poster
  frames, so exports follow the same manifest as the web player.
- `notes_pdf.export(...)` keeps rendering `notes.md` to a notes PDF.

## Policy

Simplex records cue timing from Manim `Scene.time` and does not enable
`save_sections` for playback. Manim sections are only a user-requested debug
artifact. The browser player navigates by seeking cue timestamps inside one
active media timeline.

## Output

Public media is written under:

```text
site/decks/<deck>/
  simplex-manifest.json
  thumbs/
  posters/<theme>/
  media/<theme>/hls/master.m3u8
  media/<theme>/lecture.mp4
  exports/
```

Intermediate Manim output stays in `.simplex_cache/`.
