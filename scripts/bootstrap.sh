#!/usr/bin/env bash
set -euo pipefail

echo "Installing uv (if missing)..."
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Syncing Python environment..."
uv sync

cat <<'EOM'

System dependencies (Ubuntu / Debian):
  sudo apt-get install texlive-latex-extra texlive-fonts-recommended ffmpeg \
                       libcairo2-dev libpango1.0-dev

Verify with: uv run simplex doctor
EOM
