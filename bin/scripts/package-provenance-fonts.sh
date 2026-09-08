#!/usr/bin/env bash
# Nerd Fonts Version: 3.5.1
# Script Version: 1.0.0
#
# Package the committed provenance (P+) desktop fonts for a GitHub Release.
#
# For each family this script
#   1. copies the four text faces (Regular, Italic, Bold, BoldItalic) as TTF,
#   2. validates each TTF with `test-provenance.py`,
#   3. adds the upstream licence text and a generated README.md that records
#      the build identity (source commit, Nerd Fonts version, provenance profile),
#   4. zips the result as <family>-provenance-p-plus.zip.
#
# TTF is the desktop installation format. The WOFF2 files beside the TTFs in
# patched-fonts/*/patched/ are webfont builds for @font-face and are not packaged.
#
# Usage:
#   package-provenance-fonts.sh [-o OUTPUT_DIR] [-t TAG]
#
#   OUTPUT_DIR  defaults to temp/provenance-release (ignored by git)
#   TAG         release tag written into the READMEs (default: git describe)
#
# Publish with, for example:
#   gh release create provenance-v0.1.0 temp/provenance-release/*.zip \
#     --target <commit> --title "Provenance fonts v0.1.0" --notes-file ...
#
# Needs python3 with fontTools (for the validator) and zip.

set -e -o pipefail

sd="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
repo="$( cd -- "${sd}/../.." >/dev/null 2>&1 ; pwd -P )"
python="${PYTHON:-python3}"

out="${repo}/temp/provenance-release"
tag=""
while getopts "o:t:h" opt; do
  case "$opt" in
    o) out="$OPTARG" ;;
    t) tag="$OPTARG" ;;
    *) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  esac
done

commit="$(git -C "$repo" rev-parse HEAD)"
short="$(git -C "$repo" rev-parse --short HEAD)"
[ -n "$tag" ] || tag="$(git -C "$repo" describe --always --dirty --tags 2>/dev/null || echo "$short")"
if [ -n "$(git -C "$repo" status --porcelain -- patched-fonts/zilla patched-fonts/maryheather)" ]; then
  echo "warning: patched-fonts/ has uncommitted changes; the build id will not be reproducible" >&2
fi
built="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$python" -c 'import fontTools' 2>/dev/null || { echo "python3 with fontTools is required (pip install fonttools)" >&2; exit 1; }
command -v zip >/dev/null || { echo "zip is required" >&2; exit 1; }

faces=(Regular Italic Bold BoldItalic)

# Read name ID 5 (version string) from a TTF; it carries "NFProv <profile>" and "Nerd Fonts <ver>".
version_string() {
  "$python" - "$1" <<'EOF'
import sys
from fontTools.ttLib import TTFont
n = TTFont(sys.argv[1])["name"]
print(n.getDebugName(5) or "")
EOF
}

# package <slug> <file-prefix> <menu-name> <src-dir> <licence-zip> <licence-member> <licence-name> <upstream-name> <upstream-note>
package() {
  local slug=$1 prefix=$2 menu=$3 src=$4 lzip=$5 lmember=$6 lname=$7 upstream=$8 note=$9
  local dir="${out}/${slug}-provenance-p-plus"
  rm -rf "$dir"
  mkdir -p "$dir"

  for face in "${faces[@]}"; do
    local ttf="${src}/${prefix}-${face}.ttf"
    [ -f "$ttf" ] || { echo "missing: $ttf" >&2; exit 1; }
    cp "$ttf" "$dir/"
    "$python" "${sd}/test-provenance.py" "$ttf" >/dev/null || { echo "validation failed: $ttf" >&2; exit 1; }
  done

  unzip -p "$lzip" "$lmember" > "${dir}/${lname}"

  local verstr
  verstr="$(version_string "${src}/${prefix}-Regular.ttf")"

  cat > "${dir}/README.md" <<EOF
# ${menu}

Desktop (TTF) build of ${upstream} with inline typographic provenance marks,
made with the experimental Nerd Fonts fork at
<https://github.com/delano/nerd-fonts> (see issue
<https://github.com/delano/nerd-fonts/issues/10>).

${note}

## Build

| Field | Value |
| --- | --- |
| Release tag | \`${tag}\` |
| Source commit | \`${commit}\` |
| Font version string | \`${verstr}\` |
| Packaged | ${built} |
| Packager | \`bin/scripts/package-provenance-fonts.sh\` |

The faces were produced by \`font-patcher --complete --variable-width-glyphs
--provenance=explicit\` and are committed in the fork under
\`patched-fonts/\`. Rebuild instructions are in the family's markdown file
next to them.

## Install

Install the four TTF files like any other font:

- macOS: double-click each file, or drag them into Font Book.
- Windows: select the files, right-click, Install.
- Linux: copy them to \`~/.local/share/fonts/\` and run \`fc-cache -f\`.

The family appears in font menus as **${menu}**.

## What the P+ marks are

The font contains an alternate glyph for every printable character in the
Latin-1 range. The alternate is selected by a Unicode variation selector that
follows the character in the text:

| Selector | State | Rendering |
| --- | --- | --- |
| \`U+E0100\` (VS17) | explicit human | plain glyph |
| \`U+E0101\` (VS18) | AI | glyph with a sawtooth beneath it |
| \`U+E0102\` (VS19) | unknown | glyph with a bar beneath it |

So an AI-marked character is \`<character, U+E0101>\`: the selector comes
right after the printable character it describes, and whitespace is never
marked. Unmarked text is treated as human. In a font without these tables the
selectors are ignored and the text renders normally, which is the point: the
marks travel with the words and cost nothing where they are not understood.

\`nfprov.py\` in the fork marks, inspects, converts and strips text:

\`\`\`text
echo "once." | python3 bin/scripts/nfprov.py mark --ai -
\`\`\`

## Rendering support

Marks show in renderers that honour the font's format 14 cmap subtable:
HarfBuzz (Chrome, Firefox, VS Code, most Linux applications). Applications
that shape with CoreText (Safari, Terminal.app, Zed, TextEdit) currently drop
the selectors and show plain text. For those there is a display-only PUA
encoding (\`nfprov.py mark --ai --mode=pua\`) that CoreText does render;
it falls back to missing-glyph boxes in fonts without the marks, so it is
not suitable for interchange. DirectWrite (Windows) is untested.

## Licence

${upstream} is licensed under the SIL Open Font License 1.1; the upstream
text is in \`${lname}\`. This is a Modified Version under that licence and is
distributed under the same terms. The upstream copyright and trademark
notices are retained in the font's name table.
EOF

  ( cd "$out" && rm -f "${slug}-provenance-p-plus.zip" && zip -q -r "${slug}-provenance-p-plus.zip" "${slug}-provenance-p-plus" )
  printf '%8d  %s\n' "$(stat -f %z "${out}/${slug}-provenance-p-plus.zip" 2>/dev/null || stat -c %s "${out}/${slug}-provenance-p-plus.zip")" "${slug}-provenance-p-plus.zip"
}

mkdir -p "$out"

package zilla-slab ZillaSlabNerdFontPropoP+ "ZillaSlab Nerd Font Propo P+" \
  "${repo}/patched-fonts/zilla/patched" \
  "${repo}/patched-fonts/zilla/zilla.zip" zilla-slab/LICENSE LICENSE \
  "Zilla Slab" \
  "Zilla Slab is Copyright 2017, The Mozilla Foundation. Zilla is a trademark of The Mozilla Corporation."

package maryheather MaryheatherNerdFontPropoP+ "Maryheather Nerd Font Propo P+" \
  "${repo}/patched-fonts/maryheather/patched" \
  "${repo}/patched-fonts/maryheather/merriweather.zip" Merriweather-1.582/OFL.txt OFL.txt \
  "Merriweather" \
  "Maryheather is Merriweather (Copyright 2016 The Merriweather Project Authors, <https://github.com/EbenSorkin/Merriweather>) under a different name. The Open Font License declares \"Merriweather\" a Reserved Font Name, so a Modified Version may not use it; the family, full and PostScript names in these files say Maryheather instead. The upstream copyright notice and the trademark line are unchanged."

echo "packaged in ${out} (tag ${tag}, commit ${short})"
