# render/

Manim-slides invocation, PDF export, and a content-hash render cache.

## Public surface

- `runner.render(deck, output_dir)` -- subprocess call to `manim-slides render`
- `pdf.export(deck, output_dir)` -- `manim-slides convert --to=pdf`
- `cache.is_fresh(deck, cache_dir)` / `cache.mark_fresh(deck, cache_dir)`
- `cache.cache_key(deck)` -- sha256 over `slides.py` + `deck.toml` + theme + quality

## Don't

- Don't use `os.system` or `shell=True`. Always pass arg lists.
- Don't ship a custom quality enum -- the runner passes `deck.quality` straight to manim-slides.
- Don't write outside of `output_dir` or the cache dir.
