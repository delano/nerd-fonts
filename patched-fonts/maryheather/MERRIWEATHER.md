# Maryheather provenance webfont build

This is the static-face build used to evaluate Merriweather as a reading font.
It follows the Zilla Slab convention: a complete, proportional Nerd Font build
and a separate explicit-provenance build. The latter receives the `P+` family
marker.

Because the upstream OFL declares a Reserved Font Name, the generated family is
renamed to **Maryheather**. See "Reserved Font Name and the rename" below.

## Source and licensing

The input archive used for this build is `Merriweather-1.582`:

```text
SHA-256 329cc53c1733af4d340b9c5e42c21622378a8d09d41ee317d5d6fd9c3f9b27cf
```

Its bundled `OFL.txt` identifies the Reserved Font Name as `"Merriweather"`
and states:

> No Modified Version of the Font Software may use the Reserved Font Name(s)
> unless explicit written permission is granted by the corresponding Copyright
> Holder.

The archive README identifies the font as SIL Open Font License 1.1 and links
its upstream license at
<https://github.com/EbenSorkin/Merriweather/blob/master/OFL.txt>. When
distributing the derived webfonts, include the upstream copyright notice and
OFL 1.1 text as required by clause 2.

Georgia is only a local fallback. Do not copy macOS Georgia files into the
static-site assets without a separate webfont license that permits
redistribution and modification.

## Reserved Font Name and the rename

The patcher output is a Modified Version, and publishing it from a public repo
is redistribution. No written permission from the copyright holder is recorded
here, so the reserved name cannot appear in the generated font's name identity.

This is handled the way Nerd Fonts handles every other reserved-name source:
by substituting the family name during patching, not by qualifying it with a
suffix. Upstream ships Source Code Pro as SauceCodePro, Share Tech Mono as
ShureTechMono, and Terminus as Terminess. The `P+` suffix is unrelated - it
comes from the provenance fork and marks the provenance build, not authorship.

The substitution lives in two places, matching the existing entries for
`hermit`, `share`, `source` and the rest:

- `bin/scripts/name_parser/FontnameTools.py`, `SIL_TABLE` - the active path for
  the default `--makegroups 1`.
- `font-patcher`, `reservedFontNameReplacements` - the fallback path used when
  `--makegroups` is 0 or negative.

Do not pass `--name "Maryheather"` instead. That flag replaces the entire
naming source, so it drops the `Nerd Font Propo` and `P+` segments and the
style name along with the family.

After patching, the name records carry no reserved name in any identity field:

| Name ID | Value (Regular) |
| --- | --- |
| 1 Family | `Maryheather Nerd Font Propo P+` |
| 3 Unique ID | `Maryheather Nerd Font Propo P+ 3.5.1` |
| 4 Full name | `Maryheather Nerd Font Propo P+` |
| 6 PostScript | `MaryheatherNFPP+` |

Two records still contain the string `Merriweather`, deliberately:

- ID 0, the upstream copyright notice, which OFL clause 2 requires be retained.
- ID 7, the upstream trademark notice (`Merriweather is a trademark of Sorkin
  Type Co.`), which is a factual statement about the original font.

Neither uses the reserved name *as the name of this font*, which is what the
RFN clause restricts.

## Inputs

Use only these static TTF faces from `Merriweather-1.582/fonts/ttf/`:

| Input file | SHA-256 | CSS weight | CSS style |
| --- | --- | ---: | --- |
| `Merriweather-Regular.ttf` | `623ad474e12e7dd45793fb49f2a5b230944e03bd084664d92ed956957fe49326` | 400 | `normal` |
| `Merriweather-Italic.ttf` | `8c3208bce5c3470b64a3b38f37e38488c0c9f2922e60d8be1df09eb80b3729d2` | 400 | `italic` |
| `Merriweather-Bold.ttf` | `feb38d9411371de4d8bfe3da71177daf6224f202abb7afef0481a235c10f211a` | 700 | `normal` |
| `Merriweather-BoldItalic.ttf` | `05cf2c9ad0c4e3205e498a6ec4146fc98ea169b9a2605211e7877f2d8bc07661` | 700 | `italic` |

The input filenames keep the upstream name; only the generated font is
renamed. Place the files in `temp/merriweather/`. Do not use the variable beta
font or the Light and Black faces for this four-face webfont set.

## Patch

Run from the repository root. `--variable-width-glyphs` is the proportional
mode. Do not add `--mono`.

```sh
mkdir -p temp/merriweather/patched

for face in Regular Italic Bold BoldItalic; do
  # Plain reference for validation
  fontforge --script ./font-patcher \
    temp/merriweather/Merriweather-$face.ttf \
    --complete --variable-width-glyphs --quiet --no-progressbars \
    --outputdir temp/merriweather/patched

  # Explicit provenance face
  fontforge --script ./font-patcher \
    temp/merriweather/Merriweather-$face.ttf \
    --complete --variable-width-glyphs --provenance=explicit --quiet \
    --no-progressbars --outputdir temp/merriweather/patched
done
```

Each explicit build reports `Added provenance variants for 188 base glyphs
(explicit)`. The output filenames pick up the rename automatically:

| CSS weight/style | Plain reference | Provenance font | WOFF2 filename |
| --- | --- | --- | --- |
| 400 normal | `MaryheatherNerdFontPropo-Regular.ttf` | `MaryheatherNerdFontPropoP+-Regular.ttf` | `MaryheatherNerdFontPropoP+-Regular.woff2` |
| 400 italic | `MaryheatherNerdFontPropo-Italic.ttf` | `MaryheatherNerdFontPropoP+-Italic.ttf` | `MaryheatherNerdFontPropoP+-Italic.woff2` |
| 700 normal | `MaryheatherNerdFontPropo-Bold.ttf` | `MaryheatherNerdFontPropoP+-Bold.ttf` | `MaryheatherNerdFontPropoP+-Bold.woff2` |
| 700 italic | `MaryheatherNerdFontPropo-BoldItalic.ttf` | `MaryheatherNerdFontPropoP+-BoldItalic.ttf` | `MaryheatherNerdFontPropoP+-BoldItalic.woff2` |

Output checksums for the build recorded here:

| File | SHA-256 |
| --- | --- |
| `MaryheatherNerdFontPropoP+-Regular.ttf` | `04c3b7c63f46a4714b427d2fa9955743ed6b9a5e0bbb2513c4e39fe523f61a25` |
| `MaryheatherNerdFontPropoP+-Italic.ttf` | `265c292e5d0e88f5f92013cf270a4523cd3992940984f64338c3afd779d75ac9` |
| `MaryheatherNerdFontPropoP+-Bold.ttf` | `1d42072670cd8ff3d41c762362b35e6e16562f25cee78b71c79be5605c855e7c` |
| `MaryheatherNerdFontPropoP+-BoldItalic.ttf` | `aedfb7c971356e01f8b31582f3ff6bb9b5c8292c6cfa750190173d57770bb123` |
| `MaryheatherNerdFontPropoP+-Regular.woff2` | `301dd0331c4b29344e8763330213489117bf2f77e2e2b68166993f7226349936` |
| `MaryheatherNerdFontPropoP+-Italic.woff2` | `302e697a80f765f762c73c9f196b1db3554a2d45738c1cc9a13f063a323b14bd` |
| `MaryheatherNerdFontPropoP+-Bold.woff2` | `f675396bff765bde61cb0a69332adafe80cda3c8a90d8cf08f397e517f20a64b` |
| `MaryheatherNerdFontPropoP+-BoldItalic.woff2` | `57868b41d9e71a5cf6b12bb7a115e5fa929f8e24743cf9a73e63c70f3b43250d` |

## Validate and convert

The repository `.venv` already carries `fontTools`; `brotli` is additionally
needed to open WOFF2:

```sh
uv pip install --python .venv/bin/python brotli
```

Validate the font tables against the plain reference, then confirm both AI
encodings shape to `A.ai`:

```sh
for face in Regular Italic Bold BoldItalic; do
  .venv/bin/python bin/scripts/test-provenance.py \
    --reference temp/merriweather/patched/MaryheatherNerdFontPropo-$face.ttf \
    temp/merriweather/patched/MaryheatherNerdFontPropoP+-$face.ttf
done

hb-shape temp/merriweather/patched/MaryheatherNerdFontPropoP+-Regular.ttf \
  -u 0041,E0101
hb-shape temp/merriweather/patched/MaryheatherNerdFontPropoP+-Regular.ttf \
  -u 100041
```

Both `hb-shape` calls return `[A.ai=0+692]`. Each validator run reports 188
bases checked, 0 absent, and `All checks passed`.

Confirm the rename landed before staging anything:

```sh
.venv/bin/python - <<'PY'
from fontTools.ttLib import TTFont
f = TTFont('temp/merriweather/patched/MaryheatherNerdFontPropoP+-Regular.ttf')
for r in f['name'].names:
    if r.platformID == 3 and r.nameID in (1, 3, 4, 6):
        assert 'Merriweather' not in r.toUnicode(), (r.nameID, r.toUnicode())
print('no reserved name in identity records')
PY
```

Convert and stage:

```sh
for font in temp/merriweather/patched/*P+*.ttf; do
  woff2_compress "$font"
done

mkdir -p temp/merriweather/webfonts
cp temp/merriweather/patched/*P+*.woff2 temp/merriweather/webfonts/
```

`woff2_compress` writes the compressed file beside the input TTF. Repeat the
validator on the `.woff2` files after compression; it opens WOFF2 directly and
checks the format 14 `cmap`, naming, provenance mappings, advance widths, and
vertical metrics.

## Site CSS

The generated internal family is `Maryheather Nerd Font Propo P+`. The
CSS-facing alias must also avoid the reserved name, so it is
`Maryheather Provenance`:

```css
@font-face {
  font-family: "Maryheather Provenance";
  src: url("/assets/fonts/MaryheatherNerdFontPropoP+-Regular.woff2") format("woff2");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Maryheather Provenance";
  src: url("/assets/fonts/MaryheatherNerdFontPropoP+-Italic.woff2") format("woff2");
  font-style: italic;
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Maryheather Provenance";
  src: url("/assets/fonts/MaryheatherNerdFontPropoP+-Bold.woff2") format("woff2");
  font-style: normal;
  font-weight: 700;
  font-display: swap;
}

@font-face {
  font-family: "Maryheather Provenance";
  src: url("/assets/fonts/MaryheatherNerdFontPropoP+-BoldItalic.woff2") format("woff2");
  font-style: italic;
  font-weight: 700;
  font-display: swap;
}

.prose--provenance {
  font-family: "Maryheather Provenance", Georgia, Cambria,
    "Times New Roman", Times, serif;
}
```

When distributing, ship the upstream OFL 1.1 text and copyright notice
alongside the webfonts.

Unmarked text can retain its existing `ui-serif, Georgia, …` stack when
avoiding a visual change is more important than consistent font loading.
