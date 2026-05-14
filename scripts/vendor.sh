#!/usr/bin/env bash
# Vendor runtime assets into src/simplex/web/static/.
#
# Pinned versions are intentional so a build is byte-for-byte reproducible.
# CI runs this before `simplex build`; locally invoke it once after clone.
#
# Usage: bash scripts/vendor.sh

set -euo pipefail

STATIC="$(cd "$(dirname "$0")/.." && pwd)/src/simplex/web/static"
mkdir -p "$STATIC"

TAILWIND_VER="3.4.4"
KATEX_VER="0.16.11"
REVEAL_VER="5.1.0"
HTMX_VER="1.9.12"

UNPKG="https://unpkg.com"

fetch() {
  local url="$1"
  local dest="$2"
  if [[ -f "$dest" ]]; then
    return
  fi
  mkdir -p "$(dirname "$dest")"
  echo "  fetch $url -> ${dest#"$STATIC/"}"
  curl --fail --silent --show-error --location --retry 3 -o "$dest" "$url"
}

echo "Vendoring into $STATIC"

# Tailwind Play CDN: a JIT runtime in a single JS file. We use this (rather
# than a prebuilt CSS) because base.html relies on arbitrary-value utilities
# (e.g. `bg-[#242424]`) that only exist when classes are compiled on demand.
fetch "https://cdn.tailwindcss.com/$TAILWIND_VER" \
      "$STATIC/tailwind.js"

# KaTeX CSS + a curated set of fonts. We do not vendor the auto-render JS
# because notes are pre-rendered to KaTeX-classed HTML during the build.
fetch "$UNPKG/katex@$KATEX_VER/dist/katex.min.css" \
      "$STATIC/katex/katex.min.css"
for f in \
  KaTeX_Main-Regular.woff2 KaTeX_Main-Bold.woff2 \
  KaTeX_Math-Italic.woff2 KaTeX_Math-BoldItalic.woff2 \
  KaTeX_AMS-Regular.woff2 KaTeX_Size1-Regular.woff2 \
  KaTeX_Size2-Regular.woff2 KaTeX_Size3-Regular.woff2 \
  KaTeX_Size4-Regular.woff2 ; do
  fetch "$UNPKG/katex@$KATEX_VER/dist/fonts/$f" \
        "$STATIC/katex/fonts/$f"
done

# RevealJS core + reset + a barebones theme. Our slides template (templates/
# revealjs.html.j2) supplies the visual tweaks on top.
fetch "$UNPKG/reveal.js@$REVEAL_VER/dist/reveal.js" \
      "$STATIC/reveal.js/reveal.js"
fetch "$UNPKG/reveal.js@$REVEAL_VER/dist/reveal.css" \
      "$STATIC/reveal.js/reveal.css"
fetch "$UNPKG/reveal.js@$REVEAL_VER/dist/reset.css" \
      "$STATIC/reveal.js/reset.css"
fetch "$UNPKG/reveal.js@$REVEAL_VER/dist/theme/black.css" \
      "$STATIC/reveal.js/theme/simplex.css"

# htmx (kept for future progressive enhancement; currently unused).
fetch "$UNPKG/htmx.org@$HTMX_VER/dist/htmx.min.js" \
      "$STATIC/htmx.min.js"

echo "Done."
