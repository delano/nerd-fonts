# 0007. Reach variants under CoreText through a ccmp ligature

Status: accepted. Date: 2026-09-11.

## Context

CoreText ignores the format 14 cmap for these selectors: for `<A, VS>` it
returns the glyph and advance of bare `A`. This is why Safari, Orion, Zed and
Terminal.app show no marks. CoreText does run GSUB.

## Proposal

Map each selector to its own zero-width glyph in the ordinary cmap, then add a
`ccmp` ligature lookup substituting base plus selector glyph with the variant.
If CoreText honours it, iOS Safari, macOS Safari, Zed and Terminal.app are
covered by the font alone, which is criterion S3.

## Risk

CoreText may strip default-ignorable code points before GSUB runs, in which
case the ligature never sees the selector.

## Result

Tested 2026-09-11. Built a modified `AgaveNerdFontP+-Regular.ttf` in a
scratchpad: added U+E0100-E0104 to the ordinary (format 12) cmap, each to a
new zero-width, empty-outline glyph, then added a `ccmp` feature with one
ligature per (base, selector) pair read straight out of the format 14 cmap's
`uvsDict` (188 pairs each for human, ai, and unknown; edited and mixed have no
variants in this font, matching "Reserved selectors" in the README). The font
had no existing GSUB table, so this was a fresh table, not a merge.

`hb-shape` confirms the ligature fires: `<A, U+E0101>` shapes to the single
glyph `A.ai`, identical to the format 14 path and to the PUA encoding.

The CoreText probe (`render-provenance-coretext.swift`, 40pt) confirms it
too. Against the unmodified font, the selector-encoded lines (human/ai/unknown)
render as bare base glyphs and only the PUA line is marked, reproducing the
already-documented behaviour. Against the modified font, CoreText's own
glyph report shows `E.human`, `A.ai`, and `T.unknown` as the first glyph of
each corresponding line, and the ai/unknown lines render with visible marks.
The human line resolves to `E.human` but looks unmarked because that glyph's
outline is identical to `E` by build convention, not because the ligature
failed to fire.

CoreText did not strip the selector before GSUB. It ran `ccmp` against the
plain cmap encoding and produced the correct marked glyph. The stated risk
did not happen.

## Open

Productionise this in `nfprov.py`/`font-patcher`:

- Generate the five selector glyphs and the ccmp lookups at patch time from
  the uvsDict `font-patcher` already writes, instead of the one-off script
  used for this test.
- Merge into a font that may already carry a GSUB table (source `calt`
  ligatures, kerning, etc.), not just the empty-GSUB case tested here.
- Re-run "Ligatures are lost" from the README against this font: confirm the
  selector glyph is excluded from the source font's own lookups (an
  `IgnoreMarks` flag or a GDEF mark class) so it does not intrude on them.
- Re-check Safari, Orion, Zed, and Terminal.app against a real build, not
  just the CoreText probe.
- Decide whether the selector encoding or the PUA encoding is now the
  preferred interchange form, now that both work under CoreText.

No iOS probe exists yet. ADR 0001's decorator path stays the only confirmed
iOS answer until this is verified there too.
