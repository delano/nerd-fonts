# 0005. Serve the P+ font as a woff2 subset for HarfBuzz browsers

Status: proposed. Date: 2026-09-11.

## Context

Android Chrome, Firefox and Samsung Internet shape with HarfBuzz. A page can
load a P+ font with `@font-face`, which was verified on desktop Chrome and
Firefox. The full TTF is too large to serve casually.

## Proposal

Add a build step that subsets a P+ face to Latin-1, the selectors and the PUA
range, and writes woff2.

## Evidence so far

`pyftsubset` with `--unicodes=U+0020-007E,U+00A0-00FF,U+E0100-E0104,U+100000-10FFFF --flavor=woff2`
on Agave Nerd Font P+ Regular: 701 KB to 15 KB. The format 14 cmap with all
three selectors and the 188 PUA glyphs survive. The PfEd table is dropped,
which removes the fork marker from the webfont. The venv already has brotli.

The command is `bin/scripts/subset-provenance-webfont.sh`. Tables kept:
GDEF, OS/2, cmap, cvt, fpgm, gasp, glyf, head, hhea, hmtx, loca, maxp, name,
post, prep.

Rendering through `@font-face` was tested with headless Playwright (Chromium
1243, WebKit 2358 / WebKit 26.5), served over http since `file://` breaks
font loading. A page loaded the 15 KB subset and rendered the PUA-encoded and
selector-encoded paragraphs from `example-marked.txt` and
`example-selector.txt`, plus a canvas probe drawing `T` against `T`+VS(ai,
U+E0101) in the subset font. `document.fonts.check()` and the loaded
`FontFace`'s status confirmed the subset actually loaded in both engines,
ruling out silent fallback to a system font.

Chromium renders the marks: the canvas probe differs in 98 of 4096 pixels
between `T` and `T`+VS, and every marked character in both encodings shows
the sawtooth AI-mark underline that the unmarked control lacks. WebKit
renders no marks: the canvas probe is pixel-identical (0 of 4096 differing
pixels) between `T` and `T`+VS, and the marked paragraphs are visually
indistinguishable from the unmarked control. This confirms the ADR 0007
premise on an actual webfont: CoreText drops the format 14 selector even
when it is delivered through `@font-face`, not only in native text views.

## Open

No mobile device was tested. Whether the step belongs in `font-patcher` as
`--webfont` or stays a separate script is undecided.
