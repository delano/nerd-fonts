# Rendering provenance marks in HTML without the font

Status: prototype, not in the repository. Measured 2026-09-11 on macOS
(Darwin 27) with Playwright builds of Chromium (1243) and WebKit 26.5 (2358),
system font only, no P+ font loaded. Prototype code lived in a session
scratchpad and is described here in enough detail to be rewritten.

## Problem

Marked text depends on a font that carries the variant glyphs and on a shaper
that honours them. That excludes:

- Mobile browsers. Readers cannot install fonts or override page fonts.
- Every iOS browser, which shapes through WebKit on CoreText. CoreText drops
  the selectors (see README.md, verified renderers).
- Any page where the author controls the markup but not the reader's fonts.

## Approach

Keep the encoding in the Unicode text. Add a decorator pass that finds marked
runs and wraps them in `<span class="prov prov-STATE" data-prov="STATE">`.
CSS styles the spans. The font is not consulted. The producer is unchanged.

This is not CSS alone. CSS cannot select a code point, so a DOM or HTML
rewrite is required once. The class of library is a text decorator, the same
shape as twemoji, linkify, or a syntax highlighter: scan plain text, wrap
matches, pass everything else through byte for byte.

## Algorithm

Input: a string. Output: a list of runs `(state | null, text)`.

1. Split into grapheme clusters. Client: `Intl.Segmenter` with granularity
   `grapheme`. Server: `nfprov.cluster_end` from `bin/scripts/nfprov.py`, so
   the renderer and the marker agree on cluster boundaries.
2. Classify each cluster.
   - Ends in U+E0100..U+E0104 and has more than one code point: state from
     `mapping.json` `variation_selectors`. Keep the selector in the output text.
   - Single code point in the `mapping.json` `pua` table: state from the
     table. Replace with the base character; PUA is tofu without the font.
   - Whitespace only: provisional state `ws`.
   - Otherwise: no state.
3. Coalesce adjacent clusters with equal state.
4. A `ws` run between two runs of the same non-null state joins them.
   Remaining `ws` runs become no state. Coalesce again.
5. Emit runs with a state as spans, the rest as text.

Client-side: walk text nodes with a TreeWalker, skip `script`, `style`,
`textarea` and nodes already inside `.prov`, replace each matching text node
with the fragment from step 5. Server-side: run on the text nodes of rendered
HTML, not on markdown source.

## Verified

Input was `example-marked.txt` (PUA) and its `nfprov convert --from pua
--to vs` output. Two paragraphs, 322 selectors.

| Check | Chromium | WebKit |
| --- | --- | --- |
| Spans produced, server-side, selector input | 7 | 7 |
| Spans produced, client-side, selector input | 7 | 7 |
| Spans produced, client-side, PUA input | 7 | 7 |
| Server-side and client-side runs identical | yes | yes |
| Marks visible with system font, no P+ font | yes | yes |
| Width of `T` + U+E0101 minus width of `T`, px | 0 | 0 |
| Selectors in a selection of the server-rendered section | 322 | 322 |
| Selectors in a selection of the client-rendered section | 322 | 322 |
| Selectors in a selection of the PUA-decoded section | 0 | 0 |

The selection string is what browsers place on the plain-text clipboard. A
paste into an editor with a P+ font and a HarfBuzz shaper therefore receives
the selector encoding intact. A paste into a CoreText host receives plain
text, as it does today.

## Not verified

- A physical clipboard paste into a P+ editor. Only the selection string was
  read.
- Find-in-page with selectors retained in the DOM.
- Firefox. Its shaper is HarfBuzz; no reason to expect a difference, but it
  was not run.
- A real iOS device. WebKit 26.5 on macOS is the same engine, not the same
  platform.
- Screen reader behaviour.
- Markdown source containing selectors adjacent to syntax characters. This is
  a producer concern that exists independently of this renderer.

## Decisions that are view choices, not protocol

- Selectors are retained inside spans so copy round-trips. A `strip` option
  removes them from the visible text and keeps the state only on the
  attribute; it improves search and breaks copy round-trip. Default off.
- Whitespace between two runs of the same state is absorbed into one span.
  The producer never marks whitespace; the merge is cosmetic.
- PUA input should be decoded to base plus the matching selector, not to bare
  base, so a PUA page copies out in the selector encoding. The prototype
  decoded to bare base when measured; that is the zero in the last table
  row. Both prototypes were changed afterwards and DECORATOR.md specifies
  base plus selector.

## Where the pieces would live

- `nfprov.py render --html`: the server-side pass, next to `inspect`,
  `convert`, `strip`.
- `css/nfprov.js`, `css/nfprov.css`: the client-side pass and the shared
  styles. The styles should reproduce the font's visual language (sawtooth for
  ai, bar for unknown).
- README.md verified-renderers table: a WebKit row qualified as the span path,
  not the font path.

## Related, not done

Editors expose decoration APIs (VS Code `TextEditorDecorationType`, CodeMirror
decorations) that attach a class to a range without changing the buffer. The
same run detection would drive them. That would cover CoreText editors from an
extension, without the format 14 question. Not prototyped.
