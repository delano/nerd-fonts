#!/usr/bin/env bash
# Subset a P+ font to a woff2 webfont for HarfBuzz browsers (ADR 0005).
#
# Keeps ASCII, Latin-1, the five provenance selectors and the PUA plane, so
# the format 14 cmap and the marked variants survive. Everything else,
# including the PfEd table that carries the fork marker, is dropped. Measured
# on Agave Nerd Font P+ Regular: 701 KB TTF to 15 KB woff2.
#
# Usage: subset-provenance-webfont.sh FONT.ttf [OUT.woff2]
# Needs fontTools with brotli; the repo .venv has both.
set -euo pipefail
in=${1:?font file}
out=${2:-${in%.*}.woff2}
here=$(cd "$(dirname "$0")" && pwd)
py="$here/../../.venv/bin/pyftsubset"
[ -x "$py" ] || py=pyftsubset
"$py" "$in" \
  --unicodes='U+0020-007E,U+00A0-00FF,U+E0100-E0104,U+100000-10FFFF' \
  --flavor=woff2 \
  --output-file="$out"
ls -l "$in" "$out"
