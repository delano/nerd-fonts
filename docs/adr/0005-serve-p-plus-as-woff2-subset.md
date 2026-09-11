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

## Open

Rendering of the subset through `@font-face` was not tested. No mobile device
was tested. Whether the step belongs in `font-patcher` as `--webfont` or
stays a separate script is undecided.
