#!/usr/bin/env bash
# Nerd Fonts Version: 3.5.1
# Script Version: 1.0.0
#
# Build a working example of a Nerd Font with inline typographic provenance.
#
# For each requested presentation style this script
#   1. patches the source font with `font-patcher --provenance=<style>`,
#   2. marks a short sample text with `nfprov.py` (one line per state),
#   3. renders the sample to a PNG with HarfBuzz `hb-view` (and stacks all styles into
#      all-styles.png when ImageMagick is installed),
#   4. shows with `hb-shape` that <A, VS18> and the PUA code point select the same glyph,
#   5. validates the font tables with `test-provenance.py` when fontTools is importable.
#
# Usage:
#   generate-provenance-example.sh [-f SOURCE_FONT] [-o OUTPUT_DIR] [-p PATCHER_ARGS] [STYLE ...]
#
#   STYLE         identical, subtle, or explicit (default: explicit). Several may be given.
#   SOURCE_FONT   defaults to src/unpatched-fonts/Hack/Hack-Regular.ttf
#   OUTPUT_DIR    defaults to temp/provenance-example (ignored by git)
#   PATCHER_ARGS  extra font-patcher options applied to every build, e.g. -p "--mono" or -p "--complete"
#
# Needs fontforge, python3, and hb-view/hb-shape (HarfBuzz utilities; `brew install harfbuzz`
# or `apt install libharfbuzz-bin`). Nothing is installed system wide. Generated fonts and
# images stay in OUTPUT_DIR and must not be committed.

set -e -o pipefail

sd="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
repo="${sd}/../.."

source_font="${repo}/src/unpatched-fonts/Hack/Hack-Regular.ttf"
outputdir="${repo}/temp/provenance-example"
patcher_args=""
font_size=40

usage() {
  sed -n '4,25p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while getopts "f:o:p:h" opt; do
  case "$opt" in
    f) source_font="$OPTARG" ;;
    o) outputdir="$OPTARG" ;;
    p) patcher_args="$OPTARG" ;;
    h) usage 0 ;;
    *) usage 1 ;;
  esac
done
shift $((OPTIND - 1))
styles=("$@")
[ ${#styles[@]} -eq 0 ] && styles=(explicit)

for tool in fontforge python3 hb-view hb-shape; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing required tool: $tool" >&2
    exit 1
  fi
done
if [ ! -f "$source_font" ]; then
  echo "Source font not found: $source_font" >&2
  exit 1
fi
for style in "${styles[@]}"; do
  case "$style" in
    identical|subtle|explicit) ;;
    *) echo "Unknown style '$style' (expected identical, subtle, or explicit)" >&2; exit 1 ;;
  esac
done

nfprov="${sd}/nfprov.py"
validator="${sd}/test-provenance.py"
have_fonttools=0
python3 -c "import fontTools" >/dev/null 2>&1 && have_fonttools=1

mkdir -p "$outputdir"
sample="${outputdir}/sample.txt"

# One line per provenance state. Unmarked text is "assumed human"; the other
# three lines carry a variation selector after every cluster. The fifth line is
# AI text in the PUA encoding, which CoreText renders even though it drops the
# selectors, so it shows whether a renderer loaded the font at all.
{
  printf 'Unmarked text renders as the plain base glyphs.\n'
  printf 'Explicit human text looks the same as unmarked text.\n' | python3 "$nfprov" mark --human -
  printf 'AI generated text carries the provenance mark.\n' | python3 "$nfprov" mark --ai -
  printf 'Text of unknown origin has its own variant.\n' | python3 "$nfprov" mark --unknown -
  printf 'PUA encoded AI text also carries the mark.\n' | python3 "$nfprov" mark --ai --mode=pua -
} > "$sample"

echo "Sample text: $sample"
python3 "$nfprov" inspect "$sample" | grep -E '^(characters|explicit_human|ai_vs|unknown):'

# Build the plain reference once; it is the same font without --provenance.
plaindir="${outputdir}/plain"
mkdir -p "$plaindir"
rm -f "$plaindir"/*.[ot]tf   # a stale build would be picked up by first_font()
echo "Patching reference font (no provenance) into $plaindir"
patch() {
  # Keep only the patcher's own log lines; FontForge prints a long banner even with --quiet.
  # shellcheck disable=SC2086  # patcher_args is deliberately word-split
  fontforge --script "${repo}/font-patcher" "$@" $patcher_args --quiet --no-progressbars 2>&1 \
    | grep -E 'INFO:|WARNING:|CRITICAL:|ERROR|Traceback|===>' || true
}

first_font() {
  local f
  for f in "$1"/*.[ot]tf; do
    if [ -f "$f" ]; then
      echo "$f"
      return 0
    fi
  done
  echo "font-patcher produced no font in $1" >&2
  exit 1
}

patch "$source_font" --outputdir "$plaindir"
reference=$(first_font "$plaindir")

for style in "${styles[@]}"; do
  styledir="${outputdir}/${style}"
  mkdir -p "$styledir"
  rm -f "$styledir"/*.[ot]tf
  echo
  echo "== Style: $style"
  patch "$source_font" --provenance="$style" --outputdir "$styledir"
  font=$(first_font "$styledir")
  echo "Patched font: $font"

  png="${outputdir}/${style}.png"
  hb-view --font-size="$font_size" --margin=24 --background=#FFFFFF --foreground=#000000 \
    --text-file="$sample" -o "$png" "$font"
  echo "Rendered:     $png"

  # <A, VS18> and U+100041 must both shape to the same .ai glyph.
  vs=$(hb-shape "$font" -u "0041,E0101")
  pua=$(hb-shape "$font" -u "100041")
  echo "hb-shape A+VS18: $vs"
  echo "hb-shape PUA:    $pua"
  if [ "$vs" != "$pua" ]; then
    echo "Selector and PUA encodings shape differently" >&2
    exit 1
  fi

  if [ "$have_fonttools" -eq 1 ]; then
    python3 "$validator" --reference "$reference" "$font" | grep -E '^(FAIL|All checks|FAILED)'
  else
    echo "fontTools not importable; skipping test-provenance.py (pip install fonttools)"
  fi
done

if [ ${#styles[@]} -gt 1 ]; then
  # Stack the per-style renders into one image when ImageMagick is available.
  combined="${outputdir}/all-styles.png"
  pngs=()
  for style in "${styles[@]}"; do pngs+=("${outputdir}/${style}.png"); done
  if command -v magick >/dev/null 2>&1; then
    magick "${pngs[@]}" -append "$combined" && echo "Combined:     $combined"
  elif command -v convert >/dev/null 2>&1; then
    convert "${pngs[@]}" -append "$combined" && echo "Combined:     $combined"
  else
    echo "ImageMagick not found; skipping the combined image"
  fi
fi

echo
echo "Done. Open the PNG files in $outputdir to compare styles."
