# 0001. Render provenance marks as HTML spans, independent of the font

Status: accepted. Date: 2026-09-11.

## Context

Marked text is visible only in a P+ font under a shaper that honours the
format 14 cmap. Mobile browsers do not let readers install or override fonts,
and every iOS browser shapes through CoreText, which drops the selectors.

## Decision

A decorator pass finds marked runs in the text and wraps them in
`<span class="prov prov-STATE" data-prov="STATE">`. CSS styles the spans.
The producer and the in-band encoding are unchanged. The contract is
`src/glyphs/provenance/decorator/DECORATOR.md`.

## Evidence

Chromium and WebKit 26.5, system font, no P+ font: server-side and
client-side passes produced identical runs and visible marks. Measurements in
`src/glyphs/provenance/decorator/HTML-RENDERING.md`.

## Choosing a pass

Server-side for anything published: it needs no JavaScript and survives feeds
and readers, which strip scripts. Client-side for surfaces the author does not
own. Both emit the same markup and share one stylesheet, which is where the
sawtooth-for-ai and bar-for-unknown language from the font is reproduced.

## Consequences

- iOS and mobile are covered on pages the author controls.
- A DOM or HTML rewrite is required once; CSS alone cannot select code points.
- Whitespace merging between equal states is a view default, not protocol.
- Pages the author does not control are not covered. See 0009 and the
  browser-extension note in 0006.
