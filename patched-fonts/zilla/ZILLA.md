# Zilla Slab provenance webfont build

This is the static-face build for provenance-marked headings. It uses a
complete, proportional Nerd Font build with explicit provenance marks. The
provenance family receives the `P+` marker.

## Source and licensing

The source archive available for this build is `zilla.zip`:

```text
SHA-256 62490dc19cd17e2951fe88ba3e662089ca14077634cacf1f12926374281dcf42
```

Its bundled `LICENSE` states `Copyright 2017, The Mozilla Foundation` and
licenses the font software under SIL Open Font License 1.1. The bundled license
does not declare a Reserved Font Name after the copyright notice. When
distributing the derived webfonts, include the upstream copyright notice and
OFL 1.1 text as required by clause 2.

Georgia is only a local fallback. Do not copy macOS Georgia files into the
static-site assets without a separate webfont license that permits
redistribution and modification.

## Inputs and generated faces

The existing source directory contains 12 static Zilla Slab faces, and
`patched/` contains a matching explicit-provenance TTF for each one. The normal
Zilla Slab faces use these CSS weights:

| Source / provenance output suffix | CSS weight | CSS style |
| --- | ---: | --- |
| `Light` | 300 | `normal` |
| `LightItalic` | 300 | `italic` |
| `Regular` | 400 | `normal` |
| `Italic` | 400 | `italic` |
| `Medium` | 500 | `normal` |
| `MediumItalic` | 500 | `italic` |
| `SemiBold` | 600 | `normal` |
| `SemiBoldItalic` | 600 | `italic` |
| `Bold` | 700 | `normal` |
| `BoldItalic` | 700 | `italic` |

The two additional outputs, `ZillaSlabHighNerdFontPropoP+-Light` and
`ZillaSlabHighNerdFontPropoP+-LightBold`, belong to the separate Zilla Slab
Highlight family. They are converted and staged with the standard family, but
are not part of the heading CSS below.

For the basic regular/bold pair, the input checksums are:

| Input file | SHA-256 |
| --- | --- |
| `ZillaSlab-Regular.ttf` | `41a4626844da9216b031308d4423045c765fe4231d99862d85d7d74509d37703` |
| `ZillaSlab-Italic.ttf` | `ff0cd7a2f0db59d017d51b4ed9003f58bf21ae218ab2a965aa3bc1dd894c152b` |
| `ZillaSlab-Bold.ttf` | `4ec3a04a4eef37074b42ef542e4d874e13646668cfe65256e0bf100441cf8719` |
| `ZillaSlab-BoldItalic.ttf` | `7951036c92de71e3c88ea01abe031d5bdaddf4639022a3e1cb92322f2e88d2cf` |

## Rebuild

Run from the Nerd Fonts repository root. `--variable-width-glyphs` selects
proportional mode. Do not use `--mono`.

```sh
mkdir -p temp/zilla/patched

# Build plain references first when a full metric comparison is required.
for face in temp/zilla/*.ttf; do
  fontforge --script ./font-patcher "$face" \
    --complete --variable-width-glyphs --quiet --no-progressbars \
    --outputdir temp/zilla/patched
 done

# Build explicit-provenance faces.
for face in temp/zilla/*.ttf; do
  fontforge --script ./font-patcher "$face" \
    --complete --variable-width-glyphs --provenance=explicit --quiet \
    --no-progressbars --outputdir temp/zilla/patched
 done
```

The expected standard-family filenames follow this pattern:

```text
ZillaSlabNerdFontPropoP+-<face>.ttf
```

Each explicit build should report `Added provenance variants for 188 base
glyphs (explicit)`.

## Validate and convert

Install the validator dependencies if necessary:

```sh
python3 -m pip install fonttools brotli
```

Validate a patched face, then confirm both AI encodings shape to `A.ai`:

```sh
python3 bin/scripts/test-provenance.py \
  temp/zilla/patched/ZillaSlabNerdFontPropoP+-Regular.ttf

hb-shape temp/zilla/patched/ZillaSlabNerdFontPropoP+-Regular.ttf \
  -u 0041,E0101
hb-shape temp/zilla/patched/ZillaSlabNerdFontPropoP+-Regular.ttf \
  -u 100041
```

Use `--reference` with the corresponding plain `ZillaSlabNerdFontPropo-*.ttf`
when those paired builds have been retained. That additionally verifies the
vertical metrics and unchanged name records.

Convert every provenance TTF and stage only WOFF2 assets for the static site:

```sh
for font in temp/zilla/patched/*P+*.ttf; do
  woff2_compress "$font"
 done

mkdir -p temp/zilla/webfonts
cp temp/zilla/patched/*P+*.woff2 temp/zilla/webfonts/
```

`woff2_compress` writes the compressed file beside the input TTF. The staged
files are copies of those outputs in the current workspace so both the build
workspace and deployment directory remain available for inspection.

## Heading CSS

The generated internal family is `ZillaSlab Nerd Font Propo P+`. The following
aliases its standard faces as `Zilla Slab Provenance` for heading content:

```css
@font-face {
  font-family: "Zilla Slab Provenance";
  src: url("/assets/fonts/ZillaSlabNerdFontPropoP+-Regular.woff2") format("woff2");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Zilla Slab Provenance";
  src: url("/assets/fonts/ZillaSlabNerdFontPropoP+-Italic.woff2") format("woff2");
  font-style: italic;
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Zilla Slab Provenance";
  src: url("/assets/fonts/ZillaSlabNerdFontPropoP+-Bold.woff2") format("woff2");
  font-style: normal;
  font-weight: 700;
  font-display: swap;
}

@font-face {
  font-family: "Zilla Slab Provenance";
  src: url("/assets/fonts/ZillaSlabNerdFontPropoP+-BoldItalic.woff2") format("woff2");
  font-style: italic;
  font-weight: 700;
  font-display: swap;
}

.heading--provenance {
  font-family: "Zilla Slab Provenance", Georgia, Cambria,
    "Times New Roman", Times, serif;
}
```
