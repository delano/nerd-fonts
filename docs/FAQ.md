# FAQ

## Why can't the provenance glyphs just be packaged like an icon or emoji set?

Because provenance glyphs are not new characters. They are variants of the
characters the source font already has, and that difference decides everything
else.

An icon set packages well because its glyphs are self-contained. Font Awesome's
`U+F0C5` is a fixed outline that looks the same whatever font it is patched
into or fallen back from: a finite repertoire, independent of the base font,
occupying code points nothing else claims. Emoji packs work the same way.

A provenance variant has none of those properties. A marked `a` must *be the
source font's* `a` — same outline, same advance width, same vertical metrics.
Nothing is copied from a separate symbol font; each variant is a reference to
the base glyph in the same font. See [Behaviour](../src/glyphs/provenance/README.md#behaviour)
and criterion M2 in [CRITERIA.md](../src/glyphs/provenance/CRITERIA.md).

Shipping the variants as a standalone font package would mean shipping outlines
for every character to be marked, drawn in some typeface chosen in advance. That
fails in three ways:

- Marked text switches typeface mid-line. Hack becomes whatever the package was
  drawn in.
- Advances stop matching the base font, so `--mono` cells misalign. This is a
  direct M2 failure.
- The repertoire is combinatorial — base characters times states, *per source
  font*. There is no fixed set to package.

Criterion M1 is unreachable by fallback in principle. A fallback font is only
consulted for code points the base font lacks, so it can never guarantee that
unmarked text shapes identically: it is not involved in unmarked text at all.

### What is packageable, and what isn't

The `ccmp` decomposition described in CRITERIA does make part of this
packageable. Split each variant into its base glyph plus a *zero-advance marker*
glyph, and the marker repertoire becomes small, fixed and font-independent —
three or five outlines, exactly icon-set shaped.

What does not package is the wiring: the format 14 `cmap` variation sequences,
GDEF mark classification, and `UseMarkFilteringSet` on the retained source
lookups. That machinery has to live inside the target font, and installing it
into an arbitrary font is the entire job of the patcher. The no-patcher routes
are already ruled out in CRITERIA — hand-authored per-font layout on M5,
post-processing a released build on M3 and M1.

A pure combining-mark package with no patcher is the one option that works on
paper: the fallback font supplies the combining mark, the base font supplies the
letter. It trades away the width control M2 requires, and it bets on terminal
combining-mark handling and on mark positioning across arbitrary fonts. The
mark-tiling work on full-width cells in issue #20 is a preview of that cost.

### Where the question does not arise

Two of the three consumer paths need no font and no patcher at all. HTML spans
([ADR 0001](adr/0001-render-marks-as-html-spans.md)) and editor decoration APIs
([ADR 0009](adr/0009-editor-decoration-apis.md)) carry provenance without
touching font binaries.

The patcher earns its keep only where provenance must be visible in a plain
text-rendering context that the author does not control. That is a narrower
claim than it first appears, and it is the honest one.

## Is patched output still Nerd Fonts-compatible?

Yes, for the output. The icon mapping is untouched and provenance variants
derive from the base font's own glyphs, so a `P+` font carries the full,
unmodified Nerd Fonts code-point mapping. Anything coded against Nerd Fonts
code points keeps working.

The patching step is a different matter. `mapping.json` is consumed by a
`--provenance`-enabled *fork* of `font-patcher`; upstream's patcher has no such
option and cannot read it. Describe the output as Nerd Fonts-compatible, not
the process.
