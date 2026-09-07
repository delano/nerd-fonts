# src/glyphs/provenance/zed-about.md

---


# Zed rendering notes

Zed on macOS shows two different behaviors with variation-selector provenance
text. They have different status and must not be conflated:

1. **Plain rendering** is understood and expected. It is the documented
   CoreText limitation.
2. **Extra spacing** in the editor is a Zed-specific display artifact. Its
   source path is identified, but the trigger has not been reproduced.

## Tested configuration

- Zed `1.18.1`, build `20260904.150309`
- macOS
- Buffer font: `Agave Nerd Font Mono P+`
- Input: `email-marked.txt`, produced with `nfprov.py mark --ai`
- AI selector: `U+E0101` (`VS18`)

The file contains each marked grapheme followed by `U+E0101`. `nfprov.py` does
not insert spaces between marked characters.

The installed `AgaveNerdFontMonoP+-Regular.ttf` contains a format 14 `cmap`
subtable with valid `<base, U+E0101> -> <base>.ai` mappings. Base and variant
glyphs have matching advances. HarfBuzz selects the `.ai` glyphs with one
advance per base character. The font is not the cause of either behavior below.

## Behavior 1: plain rendering (expected)

Zed's macOS text system uses CoreText for shaping.[^zed-coretext] A direct
CoreText test at 16 pt with `Agave Nerd Font Mono P+` produced:

- base glyphs rather than `.ai` glyphs for `base + U+E0101`;
- unchanged advances (8 px per base) and unchanged total width (72 px for
  `Nerd Font`);
- no inserted whitespace. CoreText consumed the selectors without adding
  glyphs or advances.

This matches `CRITERIA.md` S3: "CoreText currently renders marked text as
plain text, which M4 and M6 permit." Marked text stays legible and aligned; the
provenance marks are simply not visible. This is the same outcome already
recorded for Safari and Orion in the README's verified-renderers table.

Nothing here needs further investigation. It is a known CoreText limitation
shared by every CoreText host.

## Behavior 2: extra spacing in the Zed buffer (not yet explained)

The spacing and green underlines observed in the Zed buffer are **not**
produced by CoreText and are **not** generally expected. The measured CoreText
fallback in Behavior 1 adds no advance. Something in Zed's own display path
changes the text before it reaches the shaper.

### What the source establishes

Zed `1.18.1` classifies `U+E0100` through `U+E01EF` as invisible
characters.[^zed-invisibles] Its replacement function substitutes `U+2007`
FIGURE SPACE for an invisible character that is not on its preservation list.
That substitution adds a full advance, and the invisible-character path also
draws a background and underline.

The replacement is conditional. Before replacing, Zed checks whether the
invisible character is a standalone grapheme in the current highlighted text
chunk.[^zed-display-map] With Zed's exact `unicode-segmentation` version
(`1.13.3`), `<base, U+E0101>` is one extended grapheme cluster. So:

- When base and selector are in the same chunk, the selector is attached, is
  not replaced, and the original sequence goes to CoreText. Result: Behavior 1.
- When a highlighting boundary separates the selector from its base, the
  selector becomes a standalone grapheme, is replaced with `U+2007`, and gets
  the invisible-character background and underline. Result: the observed
  spacing.

The replacement changes editor display only. It does not modify the buffer or
the file.

### What remains open

The screenshot is consistent with the second case. What has not been
reproduced is **why** the plain-text buffer was chunked at those positions.
Until that trigger is identified, the spacing cannot be described as Zed's
general behavior for supplementary variation selectors, and it cannot be
attributed to ordinary missing-font fallback either.

It is therefore inaccurate to say either:

- Zed always replaces supplementary variation selectors with spaces; or
- the spacing is missing-font or CoreText fallback.

### Settings

`show_whitespaces` and `whitespace_map` control Zed's ordinary whitespace
visualization. In Zed `1.18.1`, the `highlight_invisibles` path described above
is called from editor chunk rendering without consulting `show_whitespaces`.
Setting `"show_whitespaces": "none"` is therefore not an established workaround
for supplementary variation selectors.

## PUA mode

The PUA encoding is a practical candidate for Zed on macOS:

```sh
python3 bin/scripts/nfprov.py mark --ai --mode=pua INPUT
```

In the direct CoreText test, the PUA form selected the expected `.ai` glyphs
and kept the same 8 px advances and 72 px line width. That addresses Behavior 1
at the CoreText level. Zed's invisible-character classifier does not classify
these Supplementary PUA-B code points as invisible, so Behavior 2 should not
apply. The complete Zed editor path has not been verified, so this is a
candidate workaround rather than a documented compatibility guarantee.

## Documentation status

Renderer documentation should record the two behaviors separately:

| Behavior                          | Status                                          |
| --------------------------------- | ----------------------------------------------- |
| Plain base glyphs, aligned        | Expected. CoreText limitation, permitted by S3. |
| Extra spacing, green underlines   | Zed display artifact. Path known, trigger open. |

[^zed-invisibles]: Zed `v1.18.1`, [`crates/editor/src/display_map/invisibles.rs`](https://github.com/zed-industries/zed/blob/v1.18.1/crates/editor/src/display_map/invisibles.rs#L51-L125)

[^zed-display-map]: Zed `v1.18.1`, [`HighlightedChunk::highlight_invisibles`](https://github.com/zed-industries/zed/blob/v1.18.1/crates/editor/src/display_map.rs#L1420-L1481)

[^zed-coretext]: Zed `v1.18.1`, [`crates/gpui_macos/src/text_system.rs`](https://github.com/zed-industries/zed/blob/v1.18.1/crates/gpui_macos/src/text_system.rs#L56-L57) and [`MacTextSystemState::layout_line`](https://github.com/zed-industries/zed/blob/v1.18.1/crates/gpui_macos/src/text_system.rs#L532-L576)
