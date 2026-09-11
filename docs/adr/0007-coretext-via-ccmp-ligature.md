# 0007. Reach variants under CoreText through a ccmp ligature

Status: proposed. Date: 2026-09-11.

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

## Open

Not tested. The test is `bin/scripts/render-provenance-coretext.swift` on a
font built this way, on macOS, before any iOS work.
