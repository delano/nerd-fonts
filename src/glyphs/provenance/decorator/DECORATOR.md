# Provenance decorator contract

Version 1. Depends on mapping.json version 1.

A decorator takes text containing in-band provenance marks and produces the
same text split into runs, each run carrying at most one provenance state.
A renderer turns runs into markup. The text is never altered except as stated
under PUA and `strip`.

## Input

A Unicode string. Two encodings may appear, together or alone:

- Selector encoding: a grapheme cluster followed by one of the code points in
  `mapping.json` `variation_selectors`.
- PUA encoding: one code point listed in `mapping.json` `pua`, standing for
  the base character and state given there.

Whitespace is never marked by a conforming producer. Selectors after
whitespace, or with no preceding cluster, are not marks.

## Options

| Option | Default | Effect |
| --- | --- | --- |
| `strip` | false | Remove selectors from run text. State is still reported. |
| `merge_whitespace` | true | Whitespace between two runs of the same state joins them. |

## Algorithm

1. Split the input into grapheme clusters (Unicode extended grapheme
   clusters). A selector is Grapheme_Extend, so it belongs to the cluster of
   its base.
2. Classify each cluster:
   - Last code point is a selector and the cluster has more than one code
     point: state from `variation_selectors`. Text is the cluster, minus the
     selector when `strip`.
   - The cluster is exactly one code point in `pua`: state from that entry.
     Text is the base character followed by the selector for that state, or
     the base character alone when `strip`.
   - Whitespace only: provisional state `ws`.
   - Anything else, including a lone selector: no state. Text unchanged.
3. Concatenate adjacent clusters of equal state into runs.
4. If `merge_whitespace`, a `ws` run whose neighbours both have the same
   non-null state takes that state. Every remaining `ws` run becomes no state.
5. Concatenate adjacent runs of equal state again.

Output: an ordered list of `(state, text)`. Concatenating every `text`
reproduces the input exactly unless `strip` is set or PUA input was present.

## Markup

For each run with a state, emit

```html
<span class="prov prov-STATE" data-prov="STATE">TEXT</span>
```

with `TEXT` HTML-escaped. Runs with no state are emitted as escaped text.
`data-prov` is the machine-readable contract. The classes exist for CSS.
An implementation may accept a class prefix option; `prov` is the default.

In a DOM, apply the pass to text nodes only. Skip `script`, `style`,
`textarea`, and any node already inside an element with the `prov` class.
Run server-side passes on rendered HTML text nodes, not on markdown source.

## Conformance

`fixtures.json` has the shape

```json
{ "contract_version": 1,
  "mapping_version": 1,
  "cases": [ { "name": "...", "input": "...", "options": {}, "runs": [ { "state": "ai", "text": "..." } ] } ] }
```

`state` is a string from `variation_selectors` or `null`. `options` uses the
option names in this document. An implementation conforms when, for every
case, `runs(input, options)` equals `runs` exactly, and when the two versions
it implements equal `contract_version` and `mapping_version`. Strings are
stored with ASCII escapes; compare code points, not bytes.

## Versioning

The contract version changes when the algorithm or markup changes. The
mapping version changes independently, per the rules in `../README.md`. An
implementation states both versions it implements.

## Not specified

- Visual style.
- Behaviour on text nodes inside `pre` or `code`. Implementations may skip
  them; the fixture does not cover it.
- Grapheme segmentation edge cases beyond those in the fixture. Clients using
  `Intl.Segmenter` and servers using the marker's `cluster_end` agreed on every
  case tested; they are not guaranteed to agree everywhere.
